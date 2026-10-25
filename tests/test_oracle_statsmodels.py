"""Scale test against the 577 statsmodels vectors (SPEC §8).

statsmodels returns a fractional N (`n_frac`); the reference tool reports
ceil(round(N, 10)) (SPEC §4.3), which the CSV already stores as `n_ceil`.
So our integer N must equal `n_ceil` and our fractional root must agree with
`n_frac`. Expected differences (SPEC §8):
  * power == alpha: statsmodels gives NaN, we clamp N to 2 (SPEC §4.4);
  * power < alpha: statsmodels gives NaN, we return an input error (SPEC §3);
  * post hoc N < 3: statsmodels computes a power, we reject N (SPEC §3).
Post hoc power should agree within 1e-7; where it does not (power very close
to 1, where statsmodels loses precision), an independent mpmath integral
decides, and the engine must match that reference.
"""
import math

import pytest

from helpers import STATSMODELS_CSV, close, load_csv, mp_power
from tpaired.engine import InputError, solve

ROWS = load_csv(STATSMODELS_CSV)
A_PRIORI = [r for r in ROWS if r["mode"] == "a-priori"]
POST_HOC = [r for r in ROWS if r["mode"] == "post-hoc"]


def test_vector_count():
    assert len(ROWS) == 577


@pytest.mark.parametrize("row", A_PRIORI, ids=lambda r: r["id"])
def test_a_priori(row):
    dz, alpha, target = float(row["dz"]), float(row["alpha"]), float(row["power_in"])
    if not row["n_frac"]:
        if target < alpha:
            with pytest.raises(InputError):
                solve("a-priori", int(row["tails"]), dz, alpha, power=target)
        else:
            assert solve("a-priori", int(row["tails"]), dz, alpha, power=target).n_total == 2
        return
    res = solve("a-priori", int(row["tails"]), dz, alpha, power=target)
    assert res.n_total == int(row["n_ceil"])
    assert res.n_total == max(2, math.ceil(round(float(row["n_frac"]), 10)))
    assert math.isclose(res.n_fractional, float(row["n_frac"]), rel_tol=1e-6)


@pytest.mark.parametrize("row", POST_HOC, ids=lambda r: r["id"])
def test_post_hoc(row):
    n = float(row["n_in"])
    if n < 2.5:
        with pytest.raises(InputError):
            solve("post-hoc", int(row["tails"]), row["dz"], row["alpha"], n=n)
        return
    res = solve("post-hoc", int(row["tails"]), row["dz"], row["alpha"], n=n)
    if close(res.power, row["power_out"]):
        return
    reference = mp_power(row["dz"], res.n_total, res.critical, res.tails)
    assert close(res.power, reference, 1e-12)
    assert not close(float(row["power_out"]), reference)  # statsmodels is the one that is off
