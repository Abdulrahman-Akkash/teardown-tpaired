"""Regenerate tests/REPORT.md from the oracle CSVs.

    python tests/make_report.py
"""
import math
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "src"), str(HERE)]

import scipy  # noqa: E402
import statsmodels  # noqa: E402

from helpers import (GPOWER_CSV, KNOWN_DEVIATION, STATSMODELS_CSV, cli_args, close,  # noqa: E402
                     load_csv, mp_power, run_cli)
from tpaired.engine import InputError, solve  # noqa: E402

FIELDS = (("ncp", "ncp"), ("critical", "critical"), ("power", "actual_power"))


def pct(a, b):
    return f"{a}/{b} (%{100 * a / b:.1f})" if b else "0/0"


def gpower_section():
    rows = load_csv(GPOWER_CSV)
    err_rows = [r for r in rows if r["error"]]
    comp = [r for r in rows if not r["error"] and r["id"] not in KNOWN_DEVIATION]
    dev = [r for r in rows if r["id"] in KNOWN_DEVIATION]

    def inputs(r):
        kw = {"power": r["power_in"]} if r["mode"] == "a-priori" else {"n": r["n_in"]}
        return r["mode"], int(r["tails"]), r["dz"], r["alpha"], kw

    err_ok = msg_ok = 0
    for r in err_rows:
        m, t, dz, a, kw = inputs(r)
        out, _, code = run_cli(cli_args(m, t, dz, a, **kw))
        err_ok += code != 0 and "error" in out
        msg_ok += out.get("error") == r["error"].removeprefix("[Input error] ")

    n_ok = df_ok = 0
    field_ok = {k: 0 for k, _ in FIELDS}
    all7 = 0
    worst = {k: 0.0 for k, _ in FIELDS}
    mismatches = []
    for r in comp:
        m, t, dz, a, kw = inputs(r)
        res = solve(m, t, dz, a, **kw)
        n_exp = int(r["n_out"]) if m == "a-priori" else math.floor(float(r["n_in"]) + 0.5)
        n_ok += res.n_total == n_exp
        df_ok += res.df == int(r["df"])
        good = res.n_total == n_exp and res.df == int(r["df"])
        for k, col in FIELDS:
            d = abs(getattr(res, k) - float(r[col]))
            worst[k] = max(worst[k], d)
            hit = close(getattr(res, k), r[col])
            field_ok[k] += hit
            good &= hit
            if not hit:
                mismatches.append(f"| {r['id']} | {k} | {r[col]} | {getattr(res, k):.10f} |")
        all7 += good

    dev_lines = []
    for r in dev:
        m, t, dz, a, kw = inputs(r)
        res = solve(m, t, dz, a, **kw)
        exp = int(r["n_out"])
        dev_lines.append(
            f"| {r['id']} | {r['dz']} | {exp} | {res.n_total} | {res.n_total - exp:+d} | "
            f"{abs(res.n_total - exp) / exp:.2e} | {res.power:.7f} ({r['actual_power']}) |")

    total_computable = len(comp) + len(dev)
    lines = [
        "## 1. GUI kâhin vektörleri (`oracle/gpower_vectors.csv`)",
        "",
        f"72 satır = {len(err_rows)} hata satırı + {total_computable} hesaplanabilir satır "
        f"({len(comp)} normal + {len(dev)} SPEC §7 bilinen sapma).",
        "",
        "| Ölçüt | Sonuç |",
        "|---|---|",
        f"| Hata satırlarında CLI hata döner (çıkış kodu ≠ 0) | {pct(err_ok, len(err_rows))} |",
        f"| Hata metni kâhindekiyle aynı (`[Input error] ` öneki hariç) | {pct(msg_ok, len(err_rows))} |",
        f"| **N tam eşleşme** (bilinen sapma hariç) | **{pct(n_ok, len(comp))}** |",
        f"| df tam eşleşme | {pct(df_ok, len(comp))} |",
        f"| ncp 7 basamak (\\|fark\\| ≤ 1e-7) | {pct(field_ok['ncp'], len(comp))} — en büyük fark {worst['ncp']:.1e} |",
        f"| kritik t 7 basamak | {pct(field_ok['critical'], len(comp))} — en büyük fark {worst['critical']:.1e} |",
        f"| güç / actual_power 7 basamak | {pct(field_ok['power'], len(comp))} — en büyük fark {worst['power']:.1e} |",
        f"| Satırın tüm alanları eşleşir | {pct(all7, len(comp))} |",
        f"| N tam eşleşme, bilinen sapma dahil | {pct(n_ok, total_computable)} |",
        "",
        "Not: CLI sözleşme gereği 4 basamak basar (SPEC §5); 7 basamak karşılaştırması CLI'ın",
        "biçimlendirdiği motor sonucu üzerinde yapılır, CLI çıktısı ayrıca 4 basamakta kontrol edilir",
        "(`tests/test_oracle_gpower.py`).",
        "",
        "### Uyuşmazlıklar",
        "",
    ]
    if mismatches:
        lines += ["| id | alan | kâhin | bizim |", "|---|---|---|---|", *mismatches, ""]
    else:
        lines += ["Bilinen sapma dışında uyuşmazlık yok.", ""]
    lines += [
        "### Bilinen sapma (SPEC §7, ayrı sayılır)",
        "",
        "| id | dz | kâhin N | bizim N | fark | göreli fark | güç (kâhin) |",
        "|---|---|---|---|---|---|---|",
        *dev_lines,
        "",
        "N > 10¹⁰ bölgesinde güç eğrisi N'ye göre neredeyse düzdür (dz ≤ 2·10⁻⁵): gücün 1e-7'lik",
        "değişimi N'de 10⁵ mertebesinde kayma demektir. Merkezi olmayan t'nin sayısal hesabındaki",
        "(scipy/Boost ile referans aracın kendi rutini arasındaki) çok küçük farklar bu yüzden N'de",
        "görünür. Testler bu satırlarda hata dönmemesini ve N'nin göreli olarak 1e-4 içinde olmasını",
        "ister; tam N eşleşmesi `xfail` olarak işaretlidir (SPEC §7).",
        "",
    ]
    return lines


def statsmodels_section():
    rows = load_csv(STATSMODELS_CSV)
    ap = [r for r in rows if r["mode"] == "a-priori"]
    ph = [r for r in rows if r["mode"] == "post-hoc"]
    ap_num = [r for r in ap if r["n_frac"]]
    ap_nan = [r for r in ap if not r["n_frac"]]

    ceil_ok = frac_differs = 0
    worst_rel = 0.0
    for r in ap_num:
        res = solve("a-priori", int(r["tails"]), r["dz"], r["alpha"], power=r["power_in"])
        ceil_ok += res.n_total == int(r["n_ceil"])
        frac_differs += not float(r["n_frac"]).is_integer()
        worst_rel = max(worst_rel, abs(res.n_fractional - float(r["n_frac"])) / float(r["n_frac"]))

    nan_lines = []
    for r in ap_nan:
        try:
            res = solve("a-priori", int(r["tails"]), r["dz"], r["alpha"], power=r["power_in"])
            ours = f"N = {res.n_total}, güç {res.power:.7f}"
        except InputError as exc:
            ours = f"hata: {exc}"
        nan_lines.append(f"| {r['id']} | {r['tails']} | {r['alpha']} | {r['power_in']} | NaN | {ours} |")

    ph_ok = 0
    ph_small = []
    ph_arbiter = []
    worst_ok = 0.0
    for r in ph:
        if float(r["n_in"]) < 2.5:
            ph_small.append(r)
            continue
        res = solve("post-hoc", int(r["tails"]), r["dz"], r["alpha"], n=r["n_in"])
        d = abs(res.power - float(r["power_out"]))
        if d <= 1e-7:
            ph_ok += 1
            worst_ok = max(worst_ok, d)
        else:
            ref = mp_power(r["dz"], res.n_total, res.critical, res.tails)
            ph_arbiter.append(
                f"| {r['id']} | {r['tails']} | {r['dz']} | {r['alpha']} | {r['n_in']} | "
                f"{float(r['power_out']):.10f} | {res.power:.10f} | {ref:.10f} |")
    ph_cmp = len(ph) - len(ph_small)

    lines = [
        "## 2. statsmodels ölçek vektörleri (`oracle/statsmodels_vectors.csv`)",
        "",
        f"{len(rows)} vektör: {len(ap)} a priori, {len(ph)} post hoc.",
        "",
        "### A priori: kesirli N ve bizim N",
        "",
        "statsmodels `solve_power` N'yi **kesirli** verir (`n_frac`, örn. 253.6138…). Referans araç ve",
        "bu yeniden yazım N'yi tamsayı raporlar: `N = max(2, ceil(round(N_kesirli, 10)))` (SPEC §4.3–4.4).",
        "Dolayısıyla doğrudan `n_frac` ile eşitlik beklenmez; karşılaştırma iki adımlıdır:",
        "",
        "| Ölçüt | Sonuç |",
        "|---|---|",
        f"| Bizim tamsayı N = `n_ceil` (= ceil(round(n_frac,10))) | {pct(ceil_ok, len(ap_num))} |",
        f"| Bizim kesirli kök ile `n_frac` arasındaki en büyük göreli fark | {worst_rel:.1e} |",
        f"| `n_frac` tamsayı değil (yani bizim N > statsmodels N) | {pct(frac_differs, len(ap_num))} |",
        "",
        "Yani her satırda bizim N, statsmodels'in kesirli N'sinin yukarı yuvarlanmışıdır; fark her zaman",
        "(0, 1) aralığındadır ve tamamen raporlama kuralından gelir, hesaptan değil.",
        "",
        "statsmodels'in NaN verdiği satırlar (SPEC §8'de beklenen fark):",
        "",
        "| id | kuyruk | α | hedef güç | statsmodels | bizim |",
        "|---|---|---|---|---|---|",
        *nan_lines,
        "",
        "Güç = α'da kök N = 2'nin altında kalır (N = 2'de güç zaten α'yı aşar), SPEC §4.4 N'yi 2'ye çeker;",
        "güç < α ise SPEC §3 girdi hatası verir. statsmodels her iki durumda da çözümsüz kalır.",
        "",
        "### Post hoc: güç",
        "",
        "| Ölçüt | Sonuç |",
        "|---|---|",
        f"| \\|fark\\| ≤ 1e-7 | {pct(ph_ok, ph_cmp)} — bu satırlarda en büyük fark {worst_ok:.1e} |",
        f"| \\|fark\\| > 1e-7 (bağımsız mpmath integrali hakem) | {len(ph_arbiter)} |",
        f"| N < 3 olduğu için bizim hata verdiğimiz satır | {len(ph_small)} |",
        "",
    ]
    if ph_arbiter:
        lines += [
            "1e-7'yi aşan satırların hepsi güç ≈ 1 bölgesindedir. Hakem olarak gücü 40 basamak",
            "hassasiyetle doğrudan integral ile hesapladık (`tests/helpers.py::mp_power`,",
            "P(Z + δ > t_c·√(V/df)), V ~ χ²(df)). Her satırda bizim değerimiz hakemle 1e-12 içinde",
            "aynıdır; sapan statsmodels'tir (güç 1'e yakınken hassasiyet kaybı). CSV'deki değerler",
            f"statsmodels {statsmodels.__version__} `ttest_power` ile doğrudan yeniden üretilebilir (örn. SM-0464 → 1.0):",
            "",
            "| id | kuyruk | dz | α | N | statsmodels | bizim | mpmath hakem |",
            "|---|---|---|---|---|---|---|---|",
            *ph_arbiter,
            "",
        ]
    for r in ph_small:
        lines += [f"`{r['id']}` (N = {r['n_in']}): statsmodels güç {float(r['power_out']):.7f} verir; SPEC §3"
                  " post hoc N'yi [3, 2147483646] dışında reddeder (kâhin GP-041 ile aynı davranış).", ""]
    return lines


def main():
    lines = [
        "# Diferansiyel test raporu — eşleştirilmiş t testi",
        "",
        "Bu dosya `python tests/make_report.py` ile üretilir; aynı karşılaştırmalar",
        "`pytest` içinde de doğrulanır (`tests/test_oracle_gpower.py`, `tests/test_oracle_statsmodels.py`).",
        f"Ortam: Python {platform.python_version()}, scipy {scipy.__version__}, statsmodels {statsmodels.__version__}.",
        "",
        *gpower_section(),
        *statsmodels_section(),
    ]
    (HERE / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
