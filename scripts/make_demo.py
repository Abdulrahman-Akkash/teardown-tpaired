"""Builds the ~60 s CLI demo video (docs/demo.mp4).

Each command below is actually executed; its real stdout and exit code are captured
and then rendered as a terminal recording (typed command, then output). Nothing in
the video is hand-written except the command lines and the short captions.

Usage: python scripts/make_demo.py [--ffmpeg PATH]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo.mp4"
W, H, FPS = 1280, 720, 10
BG, FG, DIM, OK, BAD, CAP = (24, 26, 33), (220, 223, 228), (120, 126, 140), (120, 200, 120), (230, 110, 110), (240, 200, 90)

SCENES = [
    ("A priori: tansiyon önce/sonra, dz 0.5, güç 0.95 → kaç çift?",
     "gpower-clone --test t-paired --mode a-priori --tails 2 --dz 0.5 --alpha 0.05 --power 0.95"),
    ("Post hoc: 30 çift, dz 0.5 → güç?",
     "gpower-clone --test t-paired --mode post-hoc --tails 2 --dz 0.5 --alpha 0.05 --n 30"),
    ("Kılavuzdaki örnek (s. 48): G*Power 0.8321145",
     "gpower-clone --test t-paired --mode post-hoc --tails 2 --dz 0.421637 --alpha 0.05 --n 50"),
    ("Sınır: güç = α → G*Power da N = 2 verir [REA 0x49a210]",
     "gpower-clone --test t-paired --mode a-priori --tails 2 --dz 0.5 --alpha 0.05 --power 0.05"),
    ("Geçersiz girdi: güç < α → hata + sıfırdan farklı çıkış kodu",
     "gpower-clone --test t-paired --mode a-priori --tails 2 --dz 0.5 --alpha 0.05 --power 0.03"),
    ("Sınır: post hoc N = 2 reddedilir (3 ≤ N) [REA 0x4dc2a0]",
     "gpower-clone --test t-paired --mode post-hoc --tails 2 --dz 0.5 --alpha 0.05 --n 2"),
    ("Diferansiyel test: 72 G*Power + 577 statsmodels vektörü",
     "python -m pytest -q"),
]


def execute(cmd: str) -> tuple[str, int]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    if cmd.startswith("gpower-clone"):
        argv = [sys.executable, "-m", "tpaired", *cmd.split()[1:]]
    else:
        argv = [sys.executable, *cmd.split()[1:]]
    p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=env)
    out = p.stdout.strip().splitlines()
    if cmd.startswith("python -m pytest"):
        out = out[-1:]  # summary line only
    return "\n".join(out), p.returncode


def wrap(text: str, width: int) -> list[str]:
    lines = []
    for raw in text.splitlines() or [""]:
        while len(raw) > width:
            lines.append(raw[:width])
            raw = raw[width:]
        lines.append(raw)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = ap.parse_args()
    font = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 20)
    cap_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
    cols = 100
    results = [(cap, cmd, *execute(cmd)) for cap, cmd in SCENES]

    frames_dir = Path(tempfile.mkdtemp(prefix="demo-"))
    idx = 0

    def emit(img: Image.Image, n: int = 1) -> None:
        nonlocal idx
        for _ in range(n):
            img.save(frames_dir / f"{idx:05d}.png")
            idx += 1

    history: list[tuple[str, tuple]] = []

    def screen(caption: str, partial: list[tuple[str, tuple]]) -> Image.Image:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 64], fill=(36, 39, 48))
        d.text((24, 16), caption, font=cap_font, fill=CAP)
        y = 84
        lines = (history + partial)[-26:]
        for text, color in lines:
            d.text((24, y), text, font=font, fill=color)
            y += 24
        footer = "tpaired · temiz oda yeniden yazım"
        d.text((W - 24 - d.textlength(footer, font=font), H - 32), footer, font=font, fill=DIM)
        return img

    title = Image.new("RGB", (W, H), BG)
    td = ImageDraw.Draw(title)
    td.text((80, 260), "YZM301 Teardown Sprint — t-paired", font=ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 44), fill=FG)
    td.text((80, 330), "Eşleştirilmiş t testi için güç analizi CLI'si (G*Power 3.1.9.7 kâhin)", font=cap_font, fill=DIM)
    emit(title, 3 * FPS)

    for cap, cmd, out, rc in results:
        prompt = "$ "
        for k in range(0, len(cmd) + 1, 3):
            emit(screen(cap, [(l, FG) for l in wrap(prompt + cmd[:k], cols)]))
        history.extend((l, FG) for l in wrap(prompt + cmd, cols))
        color = OK if rc == 0 else BAD
        history.extend((l, color) for l in wrap(out, cols))
        history.append((f"(çıkış kodu {rc})", DIM))
        history.append(("", FG))
        emit(screen(cap, []), int(4.5 * FPS))

    emit(screen("Hesap tek motorda; CLI ve MCP ince katman.", []), 3 * FPS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([args.ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(frames_dir / "%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "28", str(OUT)], check=True)
    shutil.rmtree(frames_dir)
    print(f"{OUT} ({idx / FPS:.1f} s, {OUT.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
