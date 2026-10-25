"""Thin CLI over the engine (SPEC §5). Prints exactly one JSON line."""
from __future__ import annotations

import argparse
import sys

from tpaired.output import dumps, run


class _UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # argparse would print usage and exit 2
        raise _UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="gpower-clone",
                description="Paired-samples t test: a priori N or post hoc power.")
    p.add_argument("--test", required=True, help="test family; only 't-paired'")
    p.add_argument("--mode", required=True, help="a-priori | post-hoc")
    p.add_argument("--tails", required=True, help="1 | 2")
    p.add_argument("--dz", help="effect size dz (alias: --d)")
    p.add_argument("--d", dest="d_alias", help=argparse.SUPPRESS)
    p.add_argument("--alpha", required=True)
    p.add_argument("--power", help="target power (a-priori)")
    p.add_argument("--n", help="number of pairs (post-hoc; alias: --n-total)")
    p.add_argument("--n-total", dest="n_alias", help=argparse.SUPPRESS)
    return p


def _one_of(primary, alias, names):
    if primary is not None and alias is not None:
        raise _UsageError(f"give only one of {names}")
    return primary if primary is not None else alias


def main(argv: list[str] | None = None) -> int:
    try:
        a = build_parser().parse_args(argv)
        dz = _one_of(a.dz, a.d_alias, "--dz/--d")
        n = _one_of(a.n, a.n_alias, "--n/--n-total")
        if dz is None:
            raise _UsageError("--dz is required")
    except _UsageError as exc:
        print(dumps({"error": str(exc)}))
        return 2
    payload, ok = run(a.test, a.mode, a.tails, dz, a.alpha, power=a.power, n=n)
    print(dumps(payload))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
