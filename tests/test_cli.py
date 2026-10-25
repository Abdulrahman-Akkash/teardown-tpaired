"""CLI contract (SPEC §5): real subprocesses, flag aliases, single-line JSON."""
import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from helpers import ROOT, run_cli

EXAMPLE = ["--test", "t-paired", "--mode", "a-priori", "--tails", "2",
           "--dz", "0.5", "--alpha", "0.05", "--power", "0.95"]


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    lines = proc.stdout.splitlines()
    assert len(lines) == 1, proc.stdout + proc.stderr
    return json.loads(lines[0]), proc.returncode


def test_python_dash_m():
    out, code = run([sys.executable, "-m", "tpaired", *EXAMPLE])
    assert code == 0
    assert out == {"n_total": 54, "actual_power": 0.9502, "critical": 2.0057, "df": 53, "ncp": 3.6742}


def _console_script():
    found = shutil.which("gpower-clone")
    if found:
        return found
    for scheme in (sysconfig.get_default_scheme(), f"{os.name}_user"):
        try:
            scripts = Path(sysconfig.get_path("scripts", scheme))
        except KeyError:
            continue
        for name in ("gpower-clone.exe", "gpower-clone"):
            if (scripts / name).exists():
                return str(scripts / name)
    return None


@pytest.mark.skipif(_console_script() is None, reason="console script not installed (pip install -e .)")
def test_console_script():
    out, code = run([_console_script(), *EXAMPLE])
    assert code == 0 and out["n_total"] == 54


def test_python_dash_m_error_exit_code():
    out, code = run([sys.executable, "-m", "tpaired", "--test", "t-paired", "--mode", "a-priori",
                     "--tails", "2", "--dz", "0.5", "--alpha", "0.05", "--power", "0.03"])
    assert code != 0 and set(out) == {"error"}


def test_post_hoc_contract_example():
    out, _, code = run_cli(["--test", "t-paired", "--mode", "post-hoc", "--tails", "2",
                            "--dz", "0.5", "--alpha", "0.05", "--n", "30"])
    assert code == 0
    assert out == {"n_total": 30, "power": 0.754, "critical": 2.0452, "df": 29, "ncp": 2.7386}


@pytest.mark.parametrize("dz_flag", ["--dz", "--d"])
@pytest.mark.parametrize("n_flag", ["--n", "--n-total"])
def test_flag_aliases(dz_flag, n_flag):
    out, _, code = run_cli(["--test", "t-paired", "--mode", "post-hoc", "--tails", "2",
                            dz_flag, "0.5", "--alpha", "0.05", n_flag, "30"])
    assert code == 0 and out["n_total"] == 30


@pytest.mark.parametrize("argv", [
    [],                                                                      # nothing
    ["--test", "t2-indep", "--mode", "a-priori", "--tails", "2",
     "--dz", "0.5", "--alpha", "0.05", "--power", "0.8"],                    # wrong family
    ["--test", "t-paired", "--mode", "sensitivity", "--tails", "2",
     "--dz", "0.5", "--alpha", "0.05", "--power", "0.8"],                    # unsupported mode
    ["--test", "t-paired", "--mode", "a-priori", "--tails", "3",
     "--dz", "0.5", "--alpha", "0.05", "--power", "0.8"],                    # tails
    ["--test", "t-paired", "--mode", "a-priori", "--tails", "2",
     "--dz", "0.5", "--alpha", "0.05"],                                      # missing --power
    ["--test", "t-paired", "--mode", "post-hoc", "--tails", "2",
     "--dz", "0.5", "--alpha", "0.05"],                                      # missing --n
    ["--test", "t-paired", "--mode", "post-hoc", "--tails", "2",
     "--dz", "0.5", "--d", "0.4", "--alpha", "0.05", "--n", "30"],           # both aliases
    ["--test", "t-paired", "--mode", "a-priori", "--tails", "2",
     "--dz", "0.5", "--alpha", "x", "--power", "0.8"],                       # non-numeric alpha
])
def test_usage_errors_are_json(argv):
    out, _, code = run_cli(argv)
    assert code != 0 and set(out) == {"error"}
