# Diferansiyel test raporu — eşleştirilmiş t testi

Bu dosya `python tests/make_report.py` ile üretilir; aynı karşılaştırmalar
`pytest` içinde de doğrulanır (`tests/test_oracle_gpower.py`, `tests/test_oracle_statsmodels.py`).
Ortam: Python 3.12.10, scipy 1.14.1, statsmodels 0.15.0.

## 1. GUI kâhin vektörleri (`oracle/gpower_vectors.csv`)

72 satır = 17 hata satırı + 55 hesaplanabilir satır (52 normal + 3 SPEC §7 bilinen sapma).

| Ölçüt | Sonuç |
|---|---|
| Hata satırlarında CLI hata döner (çıkış kodu ≠ 0) | 17/17 (%100.0) |
| Hata metni kâhindekiyle aynı (`[Input error] ` öneki hariç) | 17/17 (%100.0) |
| **N tam eşleşme** (bilinen sapma hariç) | **52/52 (%100.0)** |
| df tam eşleşme | 52/52 (%100.0) |
| ncp 7 basamak (\|fark\| ≤ 1e-7) | 52/52 (%100.0) — en büyük fark 4.7e-08 |
| kritik t 7 basamak | 52/52 (%100.0) — en büyük fark 4.6e-08 |
| güç / actual_power 7 basamak | 52/52 (%100.0) — en büyük fark 4.8e-08 |
| Satırın tüm alanları eşleşir | 52/52 (%100.0) |
| N tam eşleşme, bilinen sapma dahil | 52/55 (%94.5) |

Not: CLI sözleşme gereği 4 basamak basar (SPEC §5); 7 basamak karşılaştırması CLI'ın
biçimlendirdiği motor sonucu üzerinde yapılır, CLI çıktısı ayrıca 4 basamakta kontrol edilir
(`tests/test_oracle_gpower.py`).

### Uyuşmazlıklar

Bilinen sapma dışında uyuşmazlık yok.

### Bilinen sapma (SPEC §7, ayrı sayılır)

| id | dz | kâhin N | bizim N | fark | göreli fark | güç (kâhin) |
|---|---|---|---|---|---|---|
| GP-057 | 0.00002 | 19622220504 | 19622151276 | -69228 | 3.53e-06 | 0.8000000 (0.8000000) |
| GP-058 | 0.000011 | 64865593767 | 64866615782 | +1022015 | 1.58e-05 | 0.8000000 (0.8000049) |
| GP-071 | 0.00001 | 78488272181 | 78488605096 | +332915 | 4.24e-06 | 0.8000000 (0.8000265) |

N > 10¹⁰ bölgesinde güç eğrisi N'ye göre neredeyse düzdür (dz ≤ 2·10⁻⁵): gücün 1e-7'lik
değişimi N'de 10⁵ mertebesinde kayma demektir. Merkezi olmayan t'nin sayısal hesabındaki
(scipy/Boost ile referans aracın kendi rutini arasındaki) çok küçük farklar bu yüzden N'de
görünür. Testler bu satırlarda hata dönmemesini ve N'nin göreli olarak 1e-4 içinde olmasını
ister; tam N eşleşmesi `xfail` olarak işaretlidir (SPEC §7).

## 2. statsmodels ölçek vektörleri (`oracle/statsmodels_vectors.csv`)

577 vektör: 455 a priori, 122 post hoc.

### A priori: kesirli N ve bizim N

statsmodels `solve_power` N'yi **kesirli** verir (`n_frac`, örn. 253.6138…). Referans araç ve
bu yeniden yazım N'yi tamsayı raporlar: `N = max(2, ceil(round(N_kesirli, 10)))` (SPEC §4.3–4.4).
Dolayısıyla doğrudan `n_frac` ile eşitlik beklenmez; karşılaştırma iki adımlıdır:

| Ölçüt | Sonuç |
|---|---|
| Bizim tamsayı N = `n_ceil` (= ceil(round(n_frac,10))) | 452/452 (%100.0) |
| Bizim kesirli kök ile `n_frac` arasındaki en büyük göreli fark | 5.0e-07 |
| `n_frac` tamsayı değil (yani bizim N > statsmodels N) | 452/452 (%100.0) |

Yani her satırda bizim N, statsmodels'in kesirli N'sinin yukarı yuvarlanmışıdır; fark her zaman
(0, 1) aralığındadır ve tamamen raporlama kuralından gelir, hesaptan değil.

statsmodels'in NaN verdiği satırlar (SPEC §8'de beklenen fark):

| id | kuyruk | α | hedef güç | statsmodels | bizim |
|---|---|---|---|---|---|
| SM-0573 | 2 | 0.05 | 0.05 | NaN | N = 2, güç 0.0619486 |
| SM-0574 | 2 | 0.05 | 0.03 | NaN | hata: Power must be greater than or equal to alpha. |
| SM-0575 | 1 | 0.05 | 0.05 | NaN | N = 2, güç 0.1058229 |

Güç = α'da kök N = 2'nin altında kalır (N = 2'de güç zaten α'yı aşar), SPEC §4.4 N'yi 2'ye çeker;
güç < α ise SPEC §3 girdi hatası verir. statsmodels her iki durumda da çözümsüz kalır.

### Post hoc: güç

| Ölçüt | Sonuç |
|---|---|
| \|fark\| ≤ 1e-7 | 112/121 (%92.6) — bu satırlarda en büyük fark 4.1e-08 |
| \|fark\| > 1e-7 (bağımsız mpmath integrali hakem) | 9 |
| N < 3 olduğu için bizim hata verdiğimiz satır | 1 |

1e-7'yi aşan satırların hepsi güç ≈ 1 bölgesindedir. Hakem olarak gücü 40 basamak
hassasiyetle doğrudan integral ile hesapladık (`tests/helpers.py::mp_power`,
P(Z + δ > t_c·√(V/df)), V ~ χ²(df)). Her satırda bizim değerimiz hakemle 1e-12 içinde
aynıdır; sapan statsmodels'tir (güç 1'e yakınken hassasiyet kaybı). CSV'deki değerler
statsmodels 0.15.0 `ttest_power` ile doğrudan yeniden üretilebilir (örn. SM-0464 → 1.0):

| id | kuyruk | dz | α | N | statsmodels | bizim | mpmath hakem |
|---|---|---|---|---|---|---|---|
| SM-0464 | 2 | 0.449 | 0.01 | 224 | 1.0000000000 | 0.9999787835 | 0.9999787835 |
| SM-0465 | 1 | 0.53 | 0.05 | 125 | 0.9999999984 | 0.9999892187 | 0.9999892187 |
| SM-0470 | 2 | 0.628 | 0.1 | 100 | 1.0000000000 | 0.9999978011 | 0.9999978011 |
| SM-0482 | 1 | 0.304 | 0.1 | 288 | 0.9999998759 | 0.9999456030 | 0.9999456030 |
| SM-0486 | 2 | 0.762 | 0.01 | 90 | 1.0000000000 | 0.9999968424 | 0.9999968424 |
| SM-0502 | 2 | 0.786 | 0.05 | 81 | 1.0000000000 | 0.9999997513 | 0.9999997513 |
| SM-0511 | 1 | 0.514 | 0.05 | 143 | 0.9999999996 | 0.9999961278 | 0.9999961278 |
| SM-0549 | 2 | 1.029 | 0.1 | 38 | 1.0000000000 | 0.9999976528 | 0.9999976528 |
| SM-0560 | 1 | 0.394 | 0.05 | 295 | 1.0000000000 | 0.9999998361 | 0.9999998361 |

`SM-0576` (N = 2): statsmodels güç 0.0619486 verir; SPEC §3 post hoc N'yi [3, 2147483646] dışında reddeder (kâhin GP-041 ile aynı davranış).

