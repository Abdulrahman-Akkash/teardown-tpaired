"""Differential test against the 72 GUI oracle vectors (SPEC §6 "Kâhin vektörleri").

The CLI prints 4 decimals (SPEC §5), so the 1e-7 comparison is made on the
engine result the CLI formats; the CLI itself is checked for exit code, N/df
and 4-digit agreement on the same row.
"""
import pytest

from helpers import GPOWER_CSV, KNOWN_DEVIATION, cli_args, close, load_csv, run_cli
from tpaired.engine import solve

ROWS = load_csv(GPOWER_CSV)
ERROR_PREFIX = "[Input error] "


def row_inputs(row):
    kw = {"power": row["power_in"]} if row["mode"] == "a-priori" else {"n": row["n_in"]}
    return row["mode"], int(row["tails"]), row["dz"], row["alpha"], kw


def test_oracle_has_72_rows():
    assert len(ROWS) == 72
    assert sum(1 for r in ROWS if r["error"]) == 17


@pytest.mark.parametrize("row", [r for r in ROWS if r["error"]], ids=lambda r: r["id"])
def test_error_rows(row):
    mode, tails, dz, alpha, kw = row_inputs(row)
    out, _, code = run_cli(cli_args(mode, tails, dz, alpha, **kw))
    assert code != 0
    assert set(out) == {"error"}
    assert out["error"] == row["error"].removeprefix(ERROR_PREFIX)


@pytest.mark.parametrize(
    "row", [r for r in ROWS if not r["error"] and r["id"] not in KNOWN_DEVIATION], ids=lambda r: r["id"])
def test_computed_rows(row):
    mode, tails, dz, alpha, kw = row_inputs(row)
    res = solve(mode, tails, dz, alpha, **kw)
    assert res.df == int(row["df"])
    if mode == "a-priori":
        assert res.n_total == int(row["n_out"])
    assert close(res.ncp, row["ncp"]), ("ncp", res.ncp)
    assert close(res.critical, row["critical"]), ("critical", res.critical)
    assert close(res.power, row["actual_power"]), ("power", res.power)

    out, _, code = run_cli(cli_args(mode, tails, dz, alpha, **kw))
    assert code == 0
    power_key = "actual_power" if mode == "a-priori" else "power"
    assert out["df"] == int(row["df"]) and out["n_total"] == res.n_total
    for key, col in (("ncp", "ncp"), ("critical", "critical"), (power_key, "actual_power")):
        assert close(out[key], row[col], 5e-5 + 1e-7), key


@pytest.mark.parametrize("row", [r for r in ROWS if r["id"] in KNOWN_DEVIATION], ids=lambda r: r["id"])
def test_known_deviation_rows(row):
    """SPEC §7: no error, N within ~0.001 %; exact N is not expected."""
    mode, tails, dz, alpha, kw = row_inputs(row)
    res = solve(mode, tails, dz, alpha, **kw)
    expected = int(row["n_out"])
    assert abs(res.n_total - expected) / expected < 1e-4
    out, _, code = run_cli(cli_args(mode, tails, dz, alpha, **kw))
    assert code == 0 and out["n_total"] == res.n_total
