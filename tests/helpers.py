"""Shared test helpers: run the CLI in-process and load the oracle CSVs."""
import contextlib
import csv
import io
import json
from pathlib import Path

from tpaired.cli import main as cli_main

ROOT = Path(__file__).resolve().parents[1]
GPOWER_CSV = ROOT / "oracle" / "gpower_vectors.csv"
STATSMODELS_CSV = ROOT / "oracle" / "statsmodels_vectors.csv"

# SPEC §7: N > 1e10, N match not expected.
KNOWN_DEVIATION = {"GP-057", "GP-058", "GP-071"}

TOL = 1e-7


def cli_args(mode, tails, dz, alpha, power=None, n=None):
    argv = ["--test", "t-paired", "--mode", mode, "--tails", str(tails),
            "--dz", str(dz), "--alpha", str(alpha)]
    if power is not None:
        argv += ["--power", str(power)]
    if n is not None:
        argv += ["--n", str(n)]
    return argv


def run_cli(argv):
    """Run the CLI in-process; return (parsed JSON, raw line, exit code)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(argv)
    line = buf.getvalue()
    assert line.endswith("\n") and line.count("\n") == 1, f"not a single line: {line!r}"
    return json.loads(line), line.strip(), code


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def close(a, b, tol=TOL):
    return abs(float(a) - float(b)) <= tol + 1e-12


def mp_power(dz, n, critical, tails, dps=40):
    """Independent high-precision power: integrate P(Z + delta > tc*sqrt(V/df)) over V ~ chi2(df).

    Used only as an arbiter when statsmodels and the engine disagree.
    """
    import mpmath as mp
    mp.mp.dps = dps
    df, delta, tc = mp.mpf(n - 1), abs(mp.mpf(dz)) * mp.sqrt(n), abs(mp.mpf(critical))

    def chi2_pdf(v):
        return mp.exp((df / 2 - 1) * mp.log(v) - v / 2 - (df / 2) * mp.log(2) - mp.loggamma(df / 2))

    def tail(sign):  # sign=+1: P(T > tc); sign=-1: P(T < -tc)
        if sign > 0:
            g = lambda v: mp.ncdf(delta - tc * mp.sqrt(v / df)) * chi2_pdf(v)
        else:
            g = lambda v: mp.ncdf(-tc * mp.sqrt(v / df) - delta) * chi2_pdf(v)
        return mp.quad(g, [0, df, 2 * df, mp.inf])

    p = tail(+1) + (tail(-1) if tails == 2 else 0)
    return float(p)
