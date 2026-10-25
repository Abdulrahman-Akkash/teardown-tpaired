"""Calculation engine for the paired-samples t test (SPEC §2–§4).

This is the only module that computes anything. The CLI and the MCP server
call `solve()` and format its `Result`; they never do arithmetic themselves.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import optimize, stats

MODES = ("a-priori", "post-hoc")
TAILS = (1, 2)

DZ_LIMIT = 20.0               # SPEC §3, L-023
DZ_A_PRIORI_MIN = 1e-5        # SPEC §3, L-022
PROB_MIN, PROB_MAX = 1e-7, 0.9999999   # SPEC §3, L-020 / L-021
N_MIN, N_MAX = 3, 2_147_483_646        # SPEC §3, L-025 (post hoc only)

BRACKET_LOW, BRACKET_HIGH = 2.0, 100.0  # SPEC §4.2
XTOL, MAXITER = 1e-10, 300              # SPEC §4.2
N_FLOOR = 2                             # SPEC §4.4

# Error texts follow the reference tool's messages as recorded in the oracle CSV.
ERR_DZ_RANGE = "Effect size d is outside the admissible range (-20, 20)."
ERR_DZ_A_PRIORI = ("In an a priori analysis, the absolute value of the effect size "
                   "be greater than 0.00001.")
ERR_ALPHA_RANGE = "Alpha is outside the admissible range (1e-07, 1)."
ERR_POWER_RANGE = "Power is outside the admissible range (1e-07, 1)."
ERR_POWER_LT_ALPHA = "Power must be greater than or equal to alpha."
ERR_N_RANGE = "Total sample size is outside the admissible range (3, 2147483646)"


class InputError(ValueError):
    """Invalid input; the message is what callers report as {"error": ...}."""


@dataclass(frozen=True)
class Result:
    mode: str
    tails: int
    dz: float
    alpha: float
    n_total: int
    df: int
    ncp: float
    critical: float
    power: float                        # achieved power at the integer N
    target_power: float | None = None   # a priori only
    n_fractional: float | None = None   # a priori only: root of power(N) = target


def _parse_dz(value) -> float:
    """SPEC §3, L-024: a dz that cannot be read as a number counts as 0."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_number(value, name: str) -> float:
    # AÇIK SORU 1: SPEC only defines the non-numeric rule for dz.
    try:
        return float(value)
    except (TypeError, ValueError):
        raise InputError(f"{name} is not a number: {value!r}") from None


def _in_range(x: float, lo: float, hi: float) -> bool:
    return lo <= x <= hi   # False for NaN


def critical_t(df: float, alpha: float, tails: int) -> float:
    """Upper critical value of the central t(df) (unsigned)."""
    return float(stats.t.ppf(1.0 - alpha / tails, df))


def power_at(abs_dz: float, n: float, alpha: float, tails: int) -> float:
    """Power for |dz| at (possibly fractional) N pairs, SPEC §2."""
    df = n - 1.0
    delta = abs_dz * math.sqrt(n)
    tc = critical_t(df, alpha, tails)
    if delta == 0.0:
        upper = float(stats.t.sf(tc, df))
        lower = float(stats.t.cdf(-tc, df)) if tails == 2 else 0.0
    else:
        upper = float(stats.nct.sf(tc, df, delta))
        lower = float(stats.nct.cdf(-tc, df, delta)) if tails == 2 else 0.0
    return upper + lower


def _solve_n(abs_dz: float, alpha: float, target: float, tails: int) -> float:
    """Fractional N with power(N) = target (SPEC §4.1–4.2); N_FLOOR if already reached."""
    def f(n: float) -> float:
        return power_at(abs_dz, n, alpha, tails) - target

    lo, hi = BRACKET_LOW, BRACKET_HIGH
    if f(lo) >= 0.0:
        return lo
    # AÇIK SORU 2: SPEC says "widen the upper bound" without a factor; doubling is used.
    while f(hi) < 0.0:
        hi *= 2.0
    root, _ = optimize.brentq(f, lo, hi, xtol=XTOL, maxiter=MAXITER,
                              full_output=True, disp=False)
    return float(root)


def _round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def solve(mode: str, tails, dz, alpha, power=None, n=None) -> Result:
    """Validate (SPEC §3, in order) and compute one analysis."""
    if mode not in MODES:
        raise InputError(f"mode must be one of {', '.join(MODES)}")
    tails = _parse_number(tails, "tails")
    if tails not in TAILS:
        raise InputError("tails must be 1 or 2")
    tails = int(tails)

    dz = _parse_dz(dz)
    if not _in_range(dz, -DZ_LIMIT, DZ_LIMIT):
        raise InputError(ERR_DZ_RANGE)
    if mode == "a-priori" and abs(dz) < DZ_A_PRIORI_MIN:
        raise InputError(ERR_DZ_A_PRIORI)

    alpha = _parse_number(alpha, "alpha")
    if not _in_range(alpha, PROB_MIN, PROB_MAX):
        raise InputError(ERR_ALPHA_RANGE)

    abs_dz = abs(dz)
    if mode == "a-priori":
        if power is None:
            raise InputError("power is required in a priori mode")
        target = _parse_number(power, "power")
        if not _in_range(target, PROB_MIN, PROB_MAX):
            raise InputError(ERR_POWER_RANGE)
        if alpha > target:
            raise InputError(ERR_POWER_LT_ALPHA)
        n_frac = _solve_n(abs_dz, alpha, target, tails)
        n_int = max(N_FLOOR, math.ceil(round(n_frac, 10)))   # SPEC §4.3–4.4
    else:
        if n is None:
            raise InputError("n is required in post hoc mode")
        target = n_frac = None
        n_int = _round_half_up(_parse_number(n, "n"))       # SPEC §3, L-011
        if not _in_range(n_int, N_MIN, N_MAX):
            raise InputError(ERR_N_RANGE)

    # SPEC §4.5: reported values use the integer N.
    sign = -1.0 if dz < 0 else 1.0
    df = n_int - 1
    return Result(
        mode=mode, tails=tails, dz=dz, alpha=alpha, n_total=n_int, df=df,
        ncp=dz * math.sqrt(n_int),
        critical=sign * critical_t(df, alpha, tails),
        power=power_at(abs_dz, n_int, alpha, tails),
        target_power=target, n_fractional=n_frac,
    )
