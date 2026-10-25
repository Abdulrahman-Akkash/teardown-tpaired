"""Captures the REA/Ghidra availability check for the README (docs/rea-check.png).

Opens a new, visible console that (1) runs `rea doctor` for Claude Code and shows its
Ghidra lines, then (2) runs headless Claude Code with the user-scope REA MCP server
(from ~/.claude.json) and asks whether the REA tools are available in that session.
When the console has printed both, only that window is captured with PrintWindow
(no other windows end up in the image).

Usage: python scripts/rea_check_shot.py
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tpaired.agent import claude_executable  # noqa: E402

OUT = ROOT / "docs" / "rea-check.png"
TITLE = "REA check"
QUESTION = ("REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi? "
            "inspect_analysis_settings aracını bir kez çağır ve kısa Türkçe yanıt ver: "
            "kaç REA aracı görünüyor, Ghidra sağlayıcısı tanımlı mı.")
NL = "\r\n"
DOCTOR_SUMMARY = """import json, sys
d = json.load(sys.stdin)
checks = d.get("scope_checks", []) + d.get("informational_checks", [])
print("healthy:", d.get("healthy"))
for c in checks:
    if c["name"] in ("node", "registration:claude_code") or c["name"].startswith("ghidra"):
        print(f"  {'OK ' if c['ok'] else 'ERR'} {c['name']:<28} {c.get('detail', '')}")
"""
PROMPT = "C:\\^>"  # ^ keeps cmd's echo from treating > as a redirect


def capture(hwnd: int) -> Image.Image:
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)  # PW_RENDERFULLCONTENT
    buf = ctypes.create_string_buffer(w * h * 4)
    bmi = (ctypes.c_uint32 * 10)(40, w, -h, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, bmi, 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    return img


def main() -> int:
    marker = Path(tempfile.gettempdir()) / "rea-check.done"
    marker.unlink(missing_ok=True)
    claude = claude_executable()
    # A batch file rather than `cmd /k "<string>"`: subprocess escapes inner quotes as \",
    # which cmd does not understand. Claude Code retitles the console, so the title is set
    # again before the capture.
    bat = Path(tempfile.gettempdir()) / "rea-check.cmd"
    summary = Path(tempfile.gettempdir()) / "rea-doctor-summary.py"
    summary.write_text(DOCTOR_SUMMARY, encoding="utf-8")
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        f"title {TITLE}",
        "mode con cols=150 lines=62",
        f"echo {PROMPT} rea --version",
        "call rea --version",
        f"echo {PROMPT} rea doctor --client claude_code --json  (Ghidra satırları)",
        f'call rea doctor --client claude_code --json | "{sys.executable}" "{summary}"',
        "echo.",
        f'echo {PROMPT} claude -p "{QUESTION}"',
        f'"{claude}" -p "{QUESTION}" --allowedTools mcp__rea__inspect_analysis_settings '
        "--model claude-sonnet-5-5 --no-session-persistence",
        "echo.",
        f"title {TITLE}",
        f'echo done> "{marker}"',
        "",
    ]
    bat.write_text(NL.join(lines), encoding="utf-8")
    # The REA registration carries GHIDRA_INSTALL_DIR / JAVA_HOME; doctor needs them too.
    reg = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
    env = dict(os.environ, **reg["mcpServers"]["rea"].get("env", {}),
               MCP_CONNECTION_NONBLOCKING="0", MCP_TIMEOUT="180000")
    proc = subprocess.Popen(["cmd.exe", "/k", str(bat)], env=env, cwd=str(Path.home()),
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
    deadline = time.monotonic() + 600
    while not marker.exists():
        if time.monotonic() > deadline:
            print("timed out waiting for the console", file=sys.stderr)
            return 1
        time.sleep(2)
    time.sleep(1.5)
    hwnd = ctypes.windll.user32.FindWindowW(None, TITLE)
    if not hwnd:
        print("console window not found", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    capture(hwnd).save(OUT)
    proc.terminate()
    marker.unlink(missing_ok=True)
    bat.unlink(missing_ok=True)
    summary.unlink(missing_ok=True)
    print(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
