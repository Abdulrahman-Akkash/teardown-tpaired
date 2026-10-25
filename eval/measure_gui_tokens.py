"""Measures what one G*Power screenshot costs a model, for the MCP-vs-GUI comparison.

Two headless `claude -p` runs with the same instruction: one reads a real G*Power
screenshot (oracle/screenshots/GP-001.png) with the Read tool, the other reads the same
information as a one-line JSON text file. The difference in input tokens is the
measured cost of one screenshot. A GUI agent needs one screenshot per action to see
the result; for this test one question takes at least SCREENSHOTS_PER_QUESTION of them
(see STEPS). The GUI-path estimate is therefore: measured unit × steps.

This cannot measure GUI-path accuracy or wall time, because computer use was not
available in this environment; the report says so.

Usage: python eval/measure_gui_tokens.py [--model claude-sonnet-5-5]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from tpaired.agent import claude_executable  # noqa: E402
SHOT = ROOT / "oracle" / "screenshots" / "GP-001.png"

# Actions a GUI agent performs for one a priori question, each followed by a screenshot.
STEPS = [
    "initial screenshot (find the window)",
    "select test family 't tests'",
    "select statistical test 'matched pairs'",
    "select type of power analysis",
    "select tails",
    "type effect size dz",
    "type alpha",
    "type power",
    "click Calculate and read the output",
]
SCREENSHOTS_PER_QUESTION = len(STEPS)

PROMPT = ("Read the file {path} and reply with only the value shown for 'Total sample size' "
          "and 'Actual power', as JSON.")


def run(prompt: str, model: str, workdir: str) -> dict:
    claude = claude_executable()
    cmd = [claude, "-p", prompt, "--model", model, "--output-format", "json",
           "--tools", "Read", "--allowedTools", "Read", "--add-dir", workdir,
           "--no-session-persistence", "--setting-sources", ""]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       cwd=workdir, timeout=600)
    out = json.loads(p.stdout)
    u = out.get("usage", {})
    total_in = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                + u.get("cache_creation_input_tokens", 0))
    return {"input_tokens_total": total_in, "output_tokens": u.get("output_tokens", 0),
            "cost_usd": out.get("total_cost_usd"), "duration_s": out.get("duration_ms", 0) / 1000,
            "result": out.get("result"), "is_error": out.get("is_error")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "gpower.png"
        img.write_bytes(SHOT.read_bytes())
        txt = Path(tmp) / "gpower.json"
        txt.write_text('{"Total sample size": 54, "Actual power": 0.9502120}', encoding="utf-8")
        with_image = run(PROMPT.format(path=img), args.model, tmp)
        text_only = run(PROMPT.format(path=txt), args.model, tmp)
    unit = with_image["input_tokens_total"] - text_only["input_tokens_total"]
    result = {"model": args.model, "screenshot": SHOT.relative_to(ROOT).as_posix(),
              "with_image": with_image, "text_only": text_only,
              "tokens_per_screenshot": unit, "screenshots_per_question": SCREENSHOTS_PER_QUESTION,
              "steps": STEPS,
              "gui_estimate_tokens_per_question": unit * SCREENSHOTS_PER_QUESTION}
    (HERE / "gui_tokens.json").write_text(json.dumps(result, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("tokens_per_screenshot", "screenshots_per_question",
                                              "gui_estimate_tokens_per_question")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
