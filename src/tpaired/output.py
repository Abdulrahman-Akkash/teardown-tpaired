"""Shared presentation for CLI and MCP: engine Result -> contract JSON (SPEC §5).

Only rounding and field naming happen here; all computation is in `engine`.
"""
from __future__ import annotations

import json

from tpaired.engine import InputError, Result, solve

DECIMALS = 4  # SPEC §5


def to_contract(res: Result) -> dict:
    power_key = "actual_power" if res.mode == "a-priori" else "power"
    return {
        "n_total": res.n_total,
        power_key: round(res.power, DECIMALS),
        "critical": round(res.critical, DECIMALS),
        "df": res.df,
        "ncp": round(res.ncp, DECIMALS),
    }


def run(test: str, mode, tails, dz, alpha, power=None, n=None) -> tuple[dict, bool]:
    """Validate the family, call the engine, return (payload, ok)."""
    if test != "t-paired":
        return {"error": f"unsupported test: {test!r} (only 't-paired')"}, False
    try:
        return to_contract(solve(mode, tails, dz, alpha, power=power, n=n)), True
    except InputError as exc:
        return {"error": str(exc)}, False


def dumps(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
