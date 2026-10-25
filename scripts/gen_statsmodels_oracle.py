"""Ölçek kâhini: statsmodels ile eşleştirilmiş t vektörleri üretir.

Eşleştirilmiş t, farklar üzerinde tek örneklem t testidir; statsmodels'ta TTestPower.
statsmodels N'yi kesirli verir (n_frac). G*Power ile karşılaştırma için ceil(n_frac)
da yazılır; bu ikisinin farkı ve G*Power'ın gerçek yuvarlama kuralı LEDGER'da [REA]
ile kanıtlanmalıdır. Bu dosya motor DEĞİLDİR, yalnızca test/kâhin üretir.
"""
import csv
import itertools
import math
import random
import sys
from pathlib import Path

from statsmodels.stats.power import TTestPower

OUT = Path(__file__).resolve().parent.parent / "oracle" / "statsmodels_vectors.csv"
FIELDS = ["id", "mode", "tails", "dz", "alpha", "power_in", "n_in",
          "n_frac", "n_ceil", "power_out", "note"]

analysis = TTestPower()


def alternative(tails):
    return "two-sided" if tails == 2 else "larger"


def a_priori(tails, dz, alpha, power):
    n = analysis.solve_power(effect_size=dz, alpha=alpha, power=power,
                             alternative=alternative(tails))
    n = float(n)
    if math.isnan(n):
        raise ValueError("cozum yakinsamadi (NaN)")
    return n, math.ceil(n)


def post_hoc(tails, dz, alpha, n):
    return float(analysis.power(effect_size=dz, nobs=n, alpha=alpha,
                                alternative=alternative(tails)))


def main():
    rng = random.Random(301)
    rows = []

    # Izgara: tipik klinik değerler
    grid_dz = [0.2, 0.3, 0.5, 0.8, 1.0, 1.2]
    grid_alpha = [0.01, 0.05, 0.10]
    grid_power = [0.80, 0.90, 0.95]
    for tails, dz, alpha, power in itertools.product((1, 2), grid_dz, grid_alpha, grid_power):
        rows.append(("a-priori", tails, dz, alpha, power, None, "grid"))

    # Rastgele: ölçek için
    while len(rows) < 450:
        rows.append(("a-priori", rng.choice((1, 2)), round(rng.uniform(0.15, 1.5), 3),
                     rng.choice((0.01, 0.025, 0.05, 0.1)), round(rng.uniform(0.6, 0.99), 3),
                     None, "random"))
    for _ in range(120):
        rows.append(("post-hoc", rng.choice((1, 2)), round(rng.uniform(0.1, 1.5), 3),
                     rng.choice((0.01, 0.05, 0.1)), None, rng.randint(2, 300), "random"))

    # Sınır değerler (statsmodels'ın bunlara tepkisi G*Power'dan farklı olabilir)
    boundary = [
        ("a-priori", 2, 0.01, 0.05, 0.80, None, "dz cok kucuk"),
        ("a-priori", 2, 5.0, 0.05, 0.95, None, "dz cok buyuk"),
        ("a-priori", 2, 0.5, 0.05, 0.05, None, "guc = alfa"),
        ("a-priori", 2, 0.5, 0.05, 0.03, None, "guc < alfa"),
        ("a-priori", 1, 0.5, 0.05, 0.05, None, "guc = alfa tek kuyruk"),
        ("post-hoc", 2, 0.5, 0.05, None, 2, "en kucuk N"),
        ("post-hoc", 2, 0.0, 0.05, None, 30, "dz = 0"),
    ]
    rows.extend(boundary)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, (mode, tails, dz, alpha, power, n, note) in enumerate(rows, 1):
            rec = dict(id=f"SM-{i:04d}", mode=mode, tails=tails, dz=dz, alpha=alpha,
                       power_in=power, n_in=n, note=note)
            try:
                if mode == "a-priori":
                    rec["n_frac"], rec["n_ceil"] = a_priori(tails, dz, alpha, power)
                else:
                    rec["power_out"] = post_hoc(tails, dz, alpha, n)
            except Exception as e:  # sınırlarda statsmodels hata verebilir; kayda geçir
                rec["note"] = f"{note}; statsmodels hata: {type(e).__name__}: {e}"
            w.writerow(rec)

    print(f"{len(rows)} vektor -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
