"""GUI path of the MCP-vs-GUI comparison: the same 10 questions, solved through G*Power's window.

Same agent loop, model, label set and 0.75 threshold as `eval/run_eval.py`, but instead of
the engine's MCP tool the agent gets `eval/gpower_gui_mcp.py`: screenshots of the real
G*Power window and tools to change its controls. N and power must be read from the
screenshot image. Before every question G*Power is reset to a neutral state (t tests,
first test in the list, a priori).

G*Power 3.1.9.7 (GPowerNT.exe) must be open. Writes eval/gui_results.json and
eval/GUI_RESULTS.md; raw logs go to eval/logs/gui-<lang>-<id>.jsonl.

Usage: python eval/run_gui_eval.py [--lang tr] [--model claude-sonnet-5-5]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from tpaired.agent import CONFIDENCE_THRESHOLD, DEFAULT_MODEL, LABELS, ask  # noqa: E402
from run_eval import _same_params  # noqa: E402
import gpower_gui_mcp  # noqa: E402

PREFIX = "mcp__gpower-gui__"
TOOLS = tuple(PREFIX + t for t in ("screenshot", "select_dropdown", "set_field", "click_calculate"))
SERVERS = {"gpower-gui": {"command": sys.executable, "args": [str(HERE / "gpower_gui_mcp.py")],
                          "env": {"PYTHONIOENCODING": "utf-8"}}}

SYSTEM_PROMPT = f"""Sen klinik araştırmacılara güç analizi konusunda yardım eden bir asistansın.
Elinde açık bir G*Power 3.1.9.7 penceresi var; onu yalnızca araçlarla görebilir ve kullanabilirsin.

Görevin:
1. Sorudaki araştırma tasarımını şu etiketlerden TAM OLARAK birine ata: {", ".join(LABELS)}.
   - t-paired: aynı deneklerde iki ölçüm (önce/sonra) ya da eşleştirilmiş çiftler, ortalama farkı.
   - t2-indep: iki bağımsız grubun ortalaması (ör. ilaç ve plasebo ayrı hastalar).
   - anova-oneway: üç ya da daha fazla bağımsız grubun ortalaması.
   - chi2-contingency: oranlar / sayımlar / olumsallık tablosu.
   - multireg-r2: çoklu regresyon, R², risk faktörleri.
   - ambiguous: tasarım ya da gerekli bir parametre (etki büyüklüğü, alfa, güç ya da N) belirsiz.
   - unsupported: güç analizi sorusu değil ya da bu etiketlerin hiçbirine uymuyor.
2. Seçimine 0 ile 1 arasında bir güven değeri ver.
3. YALNIZCA etiket t-paired VE güven >= {CONFIDENCE_THRESHOLD} ise hesabı G*Power'da yap:
   test family "t tests", statistical test "Means: Difference between two dependent means
   (matched pairs)", type of power analysis "A priori" (kaç denek/çift/hasta) ya da "Post hoc"
   (gücü nedir), tails, effect size dz, α err prob ve power ya da total sample size.
   - Kuyruk belirtilmemişse iki yönlü; alfa belirtilmemişse 0.05.
   - dz soruda sayı olarak ya da Cohen'in etiketiyle (küçük 0.2, orta 0.5, büyük 0.8) verilmelidir.
     dz verilmemişse ya da ham ortalama/SD'den hesaplanması gerekiyorsa G*Power'ı KULLANMA,
     etiketi ambiguous yap ve araştırmacıdan dz'yi iste.
   - Pencerenin durumunu yalnızca `screenshot` ile görebilirsin. Ayar yapmadan önce ve
     Calculate'ten sonra ekran görüntüsü al; sonuçları (Total sample size, Actual power ya da
     Power (1-β err prob)) ekran görüntüsünden oku.
4. Hiçbir sayıyı kendin hesaplama, tahmin etme ya da yuvarlama. N ve güç yalnızca G*Power'ın
   ekranından gelir. G*Power'ı kullanmadıysan bu alanları null bırak.
5. Etiket t-paired değilse ya da güven düşükse kararı araştırmacıya bırak: ne eksik ya da neden
   desteklenmediğini kısa Türkçe bir soruyla belirt.

Yanıtının SON satırı tek satır JSON olmalı, başka hiçbir şey içermemeli:
{{"label": "...", "confidence": 0.0, "params": {{"mode": "a-priori" ya da "post-hoc", "tails": ..., "dz": ..., "alpha": ..., "power": ..., "n": ...}} ya da null, "tool_result": {{"n_total": <ekrandaki Total sample size>, "actual_power": <a priori'de ekrandaki Actual power>, "power": <post hoc'ta ekrandaki Power>}} ya da null, "answer_tr": "araştırmacıya kısa Türkçe cevap ya da soru"}}
"""


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def gui_params(tool_calls: list[dict]) -> dict:
    """The parameters the agent actually put into G*Power (last value of each control)."""
    got: dict = {}
    for c in tool_calls:
        args = c.get("input") or {}
        if c["name"] == PREFIX + "select_dropdown":
            opt = str(args.get("option", "")).lower()
            if args.get("dropdown") == "tails":
                got["tails"] = 1 if "one" in opt else 2 if "two" in opt else opt
            elif args.get("dropdown") == "statistical_test":
                got["test"] = opt
            elif args.get("dropdown") == "type_of_power_analysis":
                got["mode"] = ("a-priori" if "priori" in opt else
                               "post-hoc" if "post" in opt else opt)
        elif c["name"] == PREFIX + "set_field":
            key = {"effect_size_dz": "dz", "alpha_err_prob": "alpha", "power": "power",
                   "total_sample_size": "n"}.get(args.get("field"))
            if key:
                got[key] = args.get("value")
    # The GUI starts in a priori mode; an agent that leaves it there has chosen a priori.
    got.setdefault("mode", "a-priori")
    # The third input field holds power in a priori mode and N in post hoc mode.
    if got["mode"] == "a-priori":
        got.pop("n", None)
    else:
        got.pop("power", None)
    return got


def score(q: dict, run: dict) -> dict:
    d = run["decision"]
    names = [c["name"] for c in run["tool_calls"]]
    shots = names.count(PREFIX + "screenshot")
    used_gui = any(n != PREFIX + "screenshot" for n in names)
    label_ok = d.get("label") == q["label"]
    if q["label"] == "t-paired":
        entered = gui_params(run["tool_calls"])
        test_ok = "dependent means" in entered.pop("test", "")
        params_ok = test_ok and _same_params(q["params"], entered)
        tr = d.get("tool_result") or {}
        n_ok = _num(tr.get("n_total")) == q["n_total"]
        if "power" in q:
            p = _num(tr.get("power"))
            n_ok = n_ok and p is not None and round(p, 4) == q["power"]
        correct = (label_ok and params_ok and n_ok and shots >= 1
                   and PREFIX + "click_calculate" in names)
    else:
        params_ok = n_ok = None
        correct = label_ok and not used_gui
    return {"label_ok": label_ok, "params_ok": params_ok, "n_ok": n_ok, "screenshots": shots,
            "tool_calls": len(names), "correct": correct}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--lang", nargs="+", default=["tr"])
    p.add_argument("--only", nargs="*", help="question ids to run (default: all)")
    args = p.parse_args()
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    if args.only:
        questions = [q for q in questions if q["id"] in args.only]

    rows = []
    for lang in args.lang:
        for q in questions:
            gpower_gui_mcp.reset()
            run = ask(q[lang], model=args.model, log_path=HERE / "logs" / f"gui-{lang}-{q['id']}.jsonl",
                      system_prompt=SYSTEM_PROMPT, servers=SERVERS, allowed_tools=TOOLS)
            s = score(q, run)
            row = {"id": q["id"], "lang": lang, "expected_label": q["label"],
                   "label": run["decision"].get("label"),
                   "confidence": run["decision"].get("confidence"),
                   "params": run["decision"].get("params"),
                   "read_from_screen": run["decision"].get("tool_result"),
                   "answer_tr": run["decision"].get("answer_tr"),
                   "is_error": run["is_error"], **s, **run["metrics"]}
            rows.append(row)
            print(f"gui {lang} {q['id']} label={row['label']} correct={row['correct']} "
                  f"shots={row['screenshots']} calls={row['tool_calls']} "
                  f"tokens_in={row['input_tokens']}+{row['cache_read_input_tokens']}"
                  f"+{row['cache_creation_input_tokens']} out={row['output_tokens']} "
                  f"{row['duration_s']}s ${row['cost_usd']}", file=sys.stderr)

    (HERE / "gui_results.json").write_text(json.dumps({"model": args.model, "rows": rows},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(args.model, rows)
    return 0


def _tok(r: dict) -> int:
    return (r["input_tokens"] + r["cache_read_input_tokens"] + r["cache_creation_input_tokens"]
            + r["output_tokens"])


def write_report(model: str, rows: list[dict]) -> None:
    lines = [f"# GUI yolu değerlendirmesi ({model})", "",
             "`python eval/run_gui_eval.py` ile üretildi. Ajan G*Power'ı yalnızca ekran görüntüsüyle "
             "görür (`eval/gpower_gui_mcp.py`); N ve gücü görüntüden okur. Doğru = etiket doğru VE "
             "(t-paired ise) parametreler doğru, Calculate'e basıldı ve ekrandan okunan N/güç beklenen "
             "değerle aynı; (diğerleri için) G*Power'a dokunulmadı.", ""]
    for lang in sorted({r["lang"] for r in rows}, reverse=True):
        sel = [r for r in rows if r["lang"] == lang]
        tp = [r for r in sel if r["expected_label"] == "t-paired"]
        lines += [f"## Dil: {lang}", "",
                  f"- Doğru seçim (uçtan uca): **{sum(r['correct'] for r in sel)}/{len(sel)}**; "
                  f"t-paired sorularında {sum(r['correct'] for r in tp)}/{len(tp)}",
                  f"- Soru başına ortalama token: {round(sum(map(_tok, sel)) / len(sel))} "
                  f"(t-paired: {round(sum(map(_tok, tp)) / max(len(tp), 1))})",
                  f"- Toplam maliyet: ${sum(r['cost_usd'] or 0 for r in sel):.4f}; "
                  f"toplam süre {sum(r['duration_s'] for r in sel):.1f} sn", "",
                  "| ID | Beklenen | Etiket | Ekrandan okunan | Ekran görüntüsü | Araç çağrısı | Doğru | Token | Süre (sn) | Maliyet |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in sel:
            read = json.dumps(r["read_from_screen"], ensure_ascii=False) if r["read_from_screen"] else "—"
            lines.append(f"| {r['id']} | {r['expected_label']} | {r['label']} | `{read}` | "
                         f"{r['screenshots']} | {r['tool_calls']} | {'✓' if r['correct'] else '✗'} | "
                         f"{_tok(r)} | {r['duration_s']} | ${(r['cost_usd'] or 0):.4f} |")
        lines.append("")
    (HERE / "GUI_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
