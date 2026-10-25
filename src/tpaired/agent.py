"""AI agent layer: answers a clinician's question in natural language over MCP.

The agent is headless Claude Code (`claude -p`) restricted to exactly one tool,
the `t_paired_power` MCP tool. The model only chooses the test family, its
confidence and the parameters; every number (N, power, critical t, df, ncp)
comes from the engine through the MCP server. This module computes nothing.

Usage:
    python -m tpaired.agent "Tansiyon ilacı öncesi ve sonrası ... kaç hasta gerekir?"
    python -m tpaired.agent --json "..."      # machine-readable result
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LABELS = ("t2-indep", "t-paired", "anova-oneway", "chi2-contingency", "multireg-r2",
          "ambiguous", "unsupported")
CONFIDENCE_THRESHOLD = 0.75
TOOL = "mcp__tpaired-power__t_paired_power"
DEFAULT_MODEL = "claude-sonnet-5-5"
ROOT = Path(__file__).resolve().parents[2]

SYSTEM_PROMPT = f"""Sen klinik araştırmacılara güç analizi konusunda yardım eden bir asistansın.

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
3. YALNIZCA etiket t-paired VE güven >= {CONFIDENCE_THRESHOLD} ise `t_paired_power` aracını çağır:
   - "kaç denek/çift/hasta gerekir" → mode "a-priori" ve power; "gücü nedir" → mode "post-hoc" ve n.
   - Kuyruk belirtilmemişse tails 2; alfa belirtilmemişse 0.05.
   - dz soruda sayı olarak ya da Cohen'in etiketiyle (küçük 0.2, orta 0.5, büyük 0.8) verilmelidir.
     dz verilmemişse ya da ham ortalama/SD'den hesaplanması gerekiyorsa aracı ÇAĞIRMA, etiketi
     ambiguous yap ve araştırmacıdan dz'yi iste.
4. Hiçbir sayıyı kendin hesaplama, tahmin etme ya da yuvarlama. N, güç, kritik t, df ve ncp
   yalnızca araçtan gelir. Aracı çağırmadıysan bu alanları null bırak.
5. Etiket t-paired değilse ya da güven düşükse kararı araştırmacıya bırak: ne eksik ya da neden
   desteklenmediğini kısa Türkçe bir soruyla belirt.

Yanıtının SON satırı tek satır JSON olmalı, başka hiçbir şey içermemeli:
{{"label": "...", "confidence": 0.0, "params": {{"mode": ..., "tails": ..., "dz": ..., "alpha": ..., "power": ..., "n": ...}} ya da null, "tool_result": <aracın döndürdüğü JSON ya da null>, "answer_tr": "araştırmacıya kısa Türkçe cevap ya da soru"}}
"""


def claude_executable() -> str:
    """Path to the real claude executable.

    On Windows npm installs a `claude.cmd` batch shim; batch files mangle arguments that
    contain newlines or are empty (the system prompt, `--tools ""`), which silently drops
    the tool restriction. Call the binary behind the shim instead.
    """
    found = shutil.which("claude")
    if found is None:
        raise RuntimeError("claude CLI not found on PATH")
    if found.lower().endswith((".cmd", ".bat", ".ps1")):
        exe = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.exists():
            return str(exe)
    return found


def _mcp_config() -> str:
    cfg = {"mcpServers": {"tpaired-power": {
        "command": sys.executable,
        "args": ["-m", "tpaired.mcp_server"],
        "env": {"PYTHONPATH": str(ROOT / "src")},
    }}}
    fd, path = tempfile.mkstemp(prefix="tpaired-mcp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return path


def _parse_final_json(text: str) -> dict | None:
    for line in reversed([ln.strip() for ln in text.strip().splitlines() if ln.strip()]):
        if line.startswith("```"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and "label" in obj:
            return obj
    return None


def ask(question: str, model: str = DEFAULT_MODEL, log_path: Path | None = None) -> dict:
    """Run one question through the agent. Returns the parsed decision plus run metrics."""
    claude = claude_executable()
    cfg = _mcp_config()
    fd, prompt_file = tempfile.mkstemp(prefix="tpaired-sys-", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(SYSTEM_PROMPT)
    cmd = [claude, "-p", question,
           "--system-prompt-file", prompt_file,
           "--mcp-config", cfg, "--strict-mcp-config",
           "--tools", "",
           "--allowedTools", TOOL,
           "--model", model,
           "--output-format", "stream-json", "--verbose",
           "--no-session-persistence",
           "--setting-sources", ""]
    # Wait for the MCP server before the first model turn; otherwise headless mode starts
    # with the server still "pending", the model sees no tool and writes the call as text.
    env = dict(os.environ, MCP_CONNECTION_NONBLOCKING="0", MCP_TIMEOUT="60000")
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              cwd=tempfile.gettempdir(), env=env, timeout=600)
    finally:
        os.remove(cfg)
        os.remove(prompt_file)
    wall = time.monotonic() - start

    events = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    tool_calls = []
    for ev in events:
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append({"name": block.get("name"), "input": block.get("input")})
    final = next((ev for ev in reversed(events) if ev.get("type") == "result"), {})
    decision = _parse_final_json(final.get("result", "")) or {}
    usage = final.get("usage", {}) or {}
    return {
        "decision": decision,
        "tool_calls": tool_calls,
        "text": final.get("result", ""),
        "is_error": final.get("is_error", proc.returncode != 0),
        "stderr": proc.stderr[-2000:] if proc.returncode else "",
        "metrics": {
            "input_tokens": usage.get("input_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": final.get("total_cost_usd"),
            "duration_s": round(final.get("duration_ms", wall * 1000) / 1000, 2),
            "num_turns": final.get("num_turns"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tpaired-agent",
                                description="Klinik soruyu MCP aracı üzerinden yanıtlayan ajan.")
    p.add_argument("question")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--json", action="store_true", help="tam sonucu JSON olarak yaz")
    p.add_argument("--log", type=Path, help="araç çağrı kaydını (stream-json) bu dosyaya yaz")
    args = p.parse_args(argv)
    out = ask(args.question, model=args.model, log_path=args.log)
    if args.json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(out["decision"].get("answer_tr") or out["text"])
    return 1 if out["is_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
