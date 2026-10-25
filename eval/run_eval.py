"""Runs the 10-question evaluation set through the agent (Turkish and English).

For each question: was the label right, were the tool parameters right, and did
the N (or power) reported by the agent come from the engine and match the
expected value? Also records tokens, cost and wall time per run, and the
model's confidence for a calibration table. Writes eval/results.json and
eval/RESULTS.md; raw tool-call logs go to eval/logs/<lang>-<id>.jsonl.

Usage: python eval/run_eval.py [--model claude-sonnet-5-5] [--lang tr en]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from tpaired.agent import CONFIDENCE_THRESHOLD, DEFAULT_MODEL, TOOL, ask  # noqa: E402

PARAM_KEYS = ("mode", "tails", "dz", "alpha", "power", "n")


def _same_params(expected: dict, got: dict | None) -> bool:
    if not got:
        return False
    for k in PARAM_KEYS:
        e = expected.get(k)
        g = got.get(k)
        if e is None:
            if g not in (None, ""):
                return False
            continue
        try:
            if abs(float(e) - float(g)) > 1e-9:
                return False
        except (TypeError, ValueError):
            if str(e) != str(g):
                return False
    return True


def score(q: dict, run: dict) -> dict:
    d = run["decision"]
    calls = [c for c in run["tool_calls"] if c["name"] == TOOL]
    label_ok = d.get("label") == q["label"]
    if q["label"] == "t-paired":
        call_input = calls[-1]["input"] if calls else None
        params_ok = _same_params(q["params"], call_input)
        tool_result = d.get("tool_result") or {}
        n_ok = tool_result.get("n_total") == q["n_total"]
        if "power" in q:
            n_ok = n_ok and tool_result.get("power") == q["power"]
        correct = label_ok and params_ok and n_ok and len(calls) >= 1
    else:
        params_ok = n_ok = None
        correct = label_ok and not calls
    asked_researcher = (not calls) and (
        d.get("label") in ("ambiguous", "unsupported")
        or d.get("label") != "t-paired"
        or (d.get("confidence") or 0) < CONFIDENCE_THRESHOLD)
    return {"label_ok": label_ok, "params_ok": params_ok, "n_ok": n_ok,
            "tool_calls": len(calls), "asked_researcher": asked_researcher, "correct": correct}


def calibration(rows: list[dict]) -> list[dict]:
    bins = [(0.0, 0.5), (0.5, 0.75), (0.75, 0.9), (0.9, 1.01)]
    out = []
    for lo, hi in bins:
        sel = [r for r in rows if lo <= (r["confidence"] or 0) < hi]
        if sel:
            out.append({"bin": f"[{lo:.2f}, {min(hi, 1.0):.2f}]", "n": len(sel),
                        "mean_conf": round(sum(r["confidence"] or 0 for r in sel) / len(sel), 3),
                        "accuracy": round(sum(r["label_ok"] for r in sel) / len(sel), 3)})
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--lang", nargs="+", default=["tr", "en"])
    args = p.parse_args()
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

    rows = []
    for lang in args.lang:
        for q in questions:
            run = ask(q[lang], model=args.model, log_path=HERE / "logs" / f"{lang}-{q['id']}.jsonl")
            s = score(q, run)
            row = {"id": q["id"], "lang": lang, "expected_label": q["label"],
                   "label": run["decision"].get("label"),
                   "confidence": run["decision"].get("confidence"),
                   "tool_input": run["tool_calls"][-1]["input"] if run["tool_calls"] else None,
                   "tool_result": run["decision"].get("tool_result"),
                   "answer_tr": run["decision"].get("answer_tr"),
                   "is_error": run["is_error"], **s, **run["metrics"]}
            rows.append(row)
            print(f"{lang} {q['id']} label={row['label']} conf={row['confidence']} "
                  f"correct={row['correct']} tokens_in={row['input_tokens']}+{row['cache_read_input_tokens']}"
                  f"+{row['cache_creation_input_tokens']} out={row['output_tokens']} {row['duration_s']}s",
                  file=sys.stderr)

    (HERE / "results.json").write_text(json.dumps({"model": args.model, "rows": rows,
                                                   "calibration": calibration(rows)},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(args.model, rows)
    return 0


def write_report(model: str, rows: list[dict]) -> None:
    lines = [f"# Ajan değerlendirmesi ({model})", "",
             "`python eval/run_eval.py` ile üretildi. Doğru = etiket doğru VE (t-paired ise) araç doğru "
             "parametrelerle çağrıldı ve N/güç motordan beklenen değerle geldi; (diğerleri için) araç hiç "
             "çağrılmadı.", ""]
    for lang in sorted({r["lang"] for r in rows}, reverse=True):
        sel = [r for r in rows if r["lang"] == lang]
        acc = sum(r["correct"] for r in sel)
        lab = sum(r["label_ok"] for r in sel)
        tok_in = sum(r["input_tokens"] + r["cache_read_input_tokens"] + r["cache_creation_input_tokens"] for r in sel)
        tok_out = sum(r["output_tokens"] for r in sel)
        cost = sum(r["cost_usd"] or 0 for r in sel)
        dur = sum(r["duration_s"] for r in sel)
        lines += [f"## Dil: {lang}", "",
                  f"- Doğru seçim (uçtan uca): **{acc}/{len(sel)}**; etiket doğruluğu {lab}/{len(sel)}",
                  f"- Toplam token: girdi {tok_in} (önbellek dahil), çıktı {tok_out}; "
                  f"soru başına ortalama {round((tok_in + tok_out) / len(sel))}",
                  f"- Toplam maliyet (CLI'nin raporladığı): ${cost:.4f}; toplam süre {dur:.1f} sn", "",
                  "| ID | Beklenen | Etiket | Güven | Araç girdisi | Motor sonucu | Doğru | Token (g+ç) | Süre |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in sel:
            tin = r["input_tokens"] + r["cache_read_input_tokens"] + r["cache_creation_input_tokens"]
            lines.append(f"| {r['id']} | {r['expected_label']} | {r['label']} | {r['confidence']} | "
                         f"`{json.dumps(r['tool_input'], ensure_ascii=False) if r['tool_input'] else '—'}` | "
                         f"`{json.dumps(r['tool_result'], ensure_ascii=False) if r['tool_result'] else '—'}` | "
                         f"{'✓' if r['correct'] else '✗'} | {tin}+{r['output_tokens']} | {r['duration_s']} |")
        lines.append("")
    lines += ["## Kalibrasyon (iki dil birlikte)", "",
              "Modelin verdiği güven aralığına göre etiketin gerçekte doğru olma oranı.", "",
              "| Güven aralığı | Soru | Ortalama güven | Gerçek doğruluk |", "|---|---|---|---|"]
    for c in calibration(rows):
        lines.append(f"| {c['bin']} | {c['n']} | {c['mean_conf']} | {c['accuracy']} |")
    lines.append("")
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
