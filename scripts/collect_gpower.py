"""Kâhin toplayıcı: G*Power arayüzünü Win32 UI Automation ile sürer.

Her vektör için girdileri GUI alanlarına yazar, Calculate'e basar, çıktı alanlarını
olduğu gibi (ekranda gösterilen basamaklarla) okur ve pencerenin ekran görüntüsünü
oracle/screenshots/ altına kaydeder. Hata kutusu açılırsa metnini kaydeder ve kapatır.

Bu dosya motor DEĞİLDİR; hiçbir hesap yapmaz, yalnızca G*Power'ın gösterdiğini kaydeder.

Kullanım: python scripts/collect_gpower.py oracle/gpower_inputs.csv oracle/gpower_vectors.csv
G*Power (GPowerNT.exe) açık olmalı.
"""
import csv
import ctypes
import os
import struct
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PIL import Image
from pywinauto import Desktop

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "oracle" / "screenshots"

TEST_NAME = "Means: Difference between two dependent means (matched pairs)"
MODES = {"a-priori": 0, "post-hoc": 3}

# Kontrol kimlikleri (pywinauto ile pencere dökümünden)
CB_FAMILY, CB_TEST, CB_MODE, CB_TAILS = 1000, 1001, 1002, 1040
IN_EDITS = (1021, 1022, 1023)          # dz, alfa, güç (a priori) ya da N (post hoc)
OUT_EDITS = (1050, 1051, 1052, 1053, 1054)
BTN_CALC = 1009

# Calculate sonrası bekleme (sn); uzun N aramaları için GPOWER_WAIT ile artırılabilir
WAIT = float(os.environ.get("GPOWER_WAIT", "0.8"))

OUT_FIELDS = ["id", "mode", "tails", "dz", "alpha", "power_in", "n_in",
              "ncp", "critical", "df", "n_out", "actual_power", "error", "screenshot", "note"]


def capture_window(hwnd):
    """Yalnızca G*Power penceresini PrintWindow ile çizer: odak çalmaz, üstteki
    başka pencereleri (bildirim, alt-tab vb.) yakalamaz."""
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)  # PW_RENDERFULLCONTENT
    buf = ctypes.create_string_buffer(w * h * 4)
    bmi = struct.pack("<IiiHHIIiiII", 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, bmi, 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)


def main_window():
    return Desktop(backend="win32").window(title_re=r"G\*Power 3\.1\.9\.7")


def ctrl(win, cls, cid):
    for c in win.descendants(class_name=cls):
        if c.control_id() == cid:
            return c
    raise LookupError(f"{cls} {cid} yok")


def visible_ctrl(win, cls, cid):
    cands = [c for c in win.descendants(class_name=cls) if c.control_id() == cid and c.is_visible()]
    return cands[-1]


def select(win, cid, text_or_index):
    cb = ctrl(win, "ComboBox", cid)
    if isinstance(text_or_index, int):
        cb.select(text_or_index)
    else:
        cb.select(cb.item_texts().index(text_or_index))
    time.sleep(0.3)


def dismiss_dialogs(pid):
    """G*Power'ın açtığı hata/uyarı kutularının metnini topla ve kapat."""
    msgs = []
    for w in Desktop(backend="win32").windows(process=pid, class_name="#32770", visible_only=True):
        if w.window_text().startswith("G*Power 3.1.9.7"):
            continue
        texts = [c.window_text() for c in w.descendants(class_name="Static") if c.window_text()]
        msgs.append(f"[{w.window_text()}] " + " | ".join(texts))
        try:
            w.close()
        except Exception:
            pass
    return "; ".join(msgs)


def run_vector(win, pid, v):
    select(win, CB_FAMILY, "t tests")
    select(win, CB_TEST, TEST_NAME)
    select(win, CB_MODE, MODES[v["mode"]])
    select(win, CB_TAILS, "Two" if str(v["tails"]) == "2" else "One")

    third = v["power_in"] if v["mode"] == "a-priori" else v["n_in"]
    for cid, val in zip(IN_EDITS, (v["dz"], v["alpha"], third)):
        ctrl(win, "Edit", cid).set_edit_text(str(val))

    # Önceki vektörün çıktısı kalmasın (gizli alanlar atlanır)
    for cid in OUT_EDITS:
        c = ctrl(win, "Edit", cid)
        if c.is_visible():
            c.set_edit_text("")

    visible_ctrl(win, "Button", BTN_CALC).click()
    time.sleep(WAIT)
    err = dismiss_dialogs(pid)
    time.sleep(0.2)

    out = [ctrl(win, "Edit", cid).window_text() for cid in OUT_EDITS]
    rec = dict(v)
    rec["ncp"], rec["critical"], rec["df"] = out[0], out[1], out[2]
    if v["mode"] == "a-priori":
        rec["n_out"], rec["actual_power"] = out[3], out[4]
    else:
        rec["actual_power"] = out[3]
    rec["error"] = err

    SHOTS.mkdir(parents=True, exist_ok=True)
    shot = SHOTS / f"{v['id']}.png"
    capture_window(win.handle).save(shot)
    rec["screenshot"] = shot.relative_to(ROOT).as_posix()
    return rec


def main(inp, outp):
    win = main_window()
    pid = win.process_id()
    with open(inp, newline="", encoding="utf-8") as f:
        vectors = list(csv.DictReader(f))
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction="ignore")
        w.writeheader()
        for v in vectors:
            rec = run_vector(win, pid, v)
            w.writerow(rec)
            f.flush()
            print(rec["id"], rec["n_out"] if "n_out" in rec else "", rec["actual_power"], rec["error"], file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
