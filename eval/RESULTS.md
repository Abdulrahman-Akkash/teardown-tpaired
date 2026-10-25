# Ajan değerlendirmesi (claude-sonnet-5-5)

`python eval/run_eval.py` ile üretildi. Doğru = etiket doğru VE (t-paired ise) araç doğru parametrelerle çağrıldı ve N/güç motordan beklenen değerle geldi; (diğerleri için) araç hiç çağrılmadı.

## Dil: tr

- Doğru seçim (uçtan uca): **10/10**; etiket doğruluğu 10/10
- Toplam token: girdi 36521 (önbellek dahil), çıktı 6149; soru başına ortalama 4267
- Toplam maliyet (CLI'nin raporladığı): $0.1302; toplam süre 71.2 sn

| ID | Beklenen | Etiket | Güven | Araç girdisi | Motor sonucu | Doğru | Token (g+ç) | Süre |
|---|---|---|---|---|---|---|---|---|
| Q01 | t-paired | t-paired | 0.97 | `{"mode": "a-priori", "tails": 2, "dz": 0.5, "alpha": 0.05, "power": 0.95}` | `{"n_total": 54, "actual_power": 0.9502, "critical": 2.0057, "df": 53, "ncp": 3.6742}` | ✓ | 4949+596 | 9.12 |
| Q02 | t-paired | t-paired | 0.97 | `{"mode": "a-priori", "tails": 1, "dz": 0.5, "alpha": 0.05, "power": 0.8}` | `{"n_total": 27, "actual_power": 0.8118, "critical": 1.7056, "df": 26, "ncp": 2.5981}` | ✓ | 4961+573 | 7.36 |
| Q03 | t-paired | t-paired | 0.97 | `{"mode": "post-hoc", "tails": 2, "dz": 0.4, "alpha": 0.05, "n": 30}` | `{"n_total": 30, "power": 0.5628, "critical": 2.0452, "df": 29, "ncp": 2.1909}` | ✓ | 4891+633 | 6.92 |
| Q04 | t-paired | t-paired | 0.95 | `{"mode": "a-priori", "tails": 2, "dz": 0.2, "alpha": 0.01, "power": 0.9}` | `{"n_total": 376, "actual_power": 0.9006, "critical": 2.589, "df": 375, "ncp": 3.8781}` | ✓ | 5008+655 | 6.9 |
| Q05 | t-paired | t-paired | 0.95 | `{"mode": "a-priori", "tails": 2, "dz": 0.8, "alpha": 0.05, "power": 0.9}` | `{"n_total": 19, "actual_power": 0.9092, "critical": 2.1009, "df": 18, "ncp": 3.4871}` | ✓ | 4954+668 | 7.26 |
| Q06 | ambiguous | ambiguous | 0.85 | `—` | `—` | ✓ | 2364+725 | 7.55 |
| Q07 | t2-indep | t2-indep | 0.97 | `—` | `—` | ✓ | 2341+593 | 6.91 |
| Q08 | anova-oneway | anova-oneway | 0.97 | `—` | `—` | ✓ | 2352+532 | 6.44 |
| Q09 | chi2-contingency | chi2-contingency | 0.96 | `—` | `—` | ✓ | 2337+492 | 5.64 |
| Q10 | multireg-r2 | multireg-r2 | 0.95 | `—` | `—` | ✓ | 2364+682 | 7.14 |

## Dil: en

- Doğru seçim (uçtan uca): **10/10**; etiket doğruluğu 10/10
- Toplam token: girdi 38156 (önbellek dahil), çıktı 6620; soru başına ortalama 4478
- Toplam maliyet (CLI'nin raporladığı): $0.1407; toplam süre 77.1 sn

| ID | Beklenen | Etiket | Güven | Araç girdisi | Motor sonucu | Doğru | Token (g+ç) | Süre |
|---|---|---|---|---|---|---|---|---|
| Q01 | t-paired | t-paired | 0.97 | `{"mode": "a-priori", "tails": 2, "dz": 0.5, "alpha": 0.05, "power": 0.95}` | `{"n_total": 54, "actual_power": 0.9502, "critical": 2.0057, "df": 53, "ncp": 3.6742}` | ✓ | 4857+586 | 8.18 |
| Q02 | t-paired | t-paired | 0.97 | `{"mode": "a-priori", "tails": 1, "dz": 0.5, "alpha": 0.05, "power": 0.8}` | `{"n_total": 27, "actual_power": 0.8118, "critical": 1.7056, "df": 26, "ncp": 2.5981}` | ✓ | 4851+601 | 6.62 |
| Q03 | t-paired | t-paired | 0.97 | `{"mode": "post-hoc", "tails": 2, "dz": 0.4, "alpha": 0.05, "n": 30}` | `{"n_total": 30, "power": 0.5628, "critical": 2.0452, "df": 29, "ncp": 2.1909}` | ✓ | 4823+688 | 7.77 |
| Q04 | t-paired | t-paired | 0.95 | `{"mode": "a-priori", "tails": 2, "dz": 0.2, "alpha": 0.01, "power": 0.9}` | `{"n_total": 376, "actual_power": 0.9006, "critical": 2.589, "df": 375, "ncp": 3.8781}` | ✓ | 4860+614 | 6.99 |
| Q05 | t-paired | t-paired | 0.95 | `{"mode": "a-priori", "tails": 2, "dz": 0.8, "alpha": 0.05, "power": 0.9}` | `{"n_total": 19, "actual_power": 0.9092, "critical": 2.1009, "df": 18, "ncp": 3.4871}` | ✓ | 4853+771 | 8.61 |
| Q06 | ambiguous | ambiguous | 0.85 | `—` | `—` | ✓ | 2330+716 | 7.28 |
| Q07 | t2-indep | t2-indep | 0.97 | `—` | `—` | ✓ | 2302+656 | 7.69 |
| Q08 | anova-oneway | anova-oneway | 0.97 | `—` | `—` | ✓ | 2314+389 | 5.4 |
| Q09 | chi2-contingency | chi2-contingency | 0.95 | `—` | `—` | ✓ | 4641+1043 | 11.78 |
| Q10 | multireg-r2 | multireg-r2 | 0.95 | `—` | `—` | ✓ | 2325+556 | 6.79 |

## Kalibrasyon (iki dil birlikte)

Modelin verdiği güven aralığına göre etiketin gerçekte doğru olma oranı.

| Güven aralığı | Soru | Ortalama güven | Gerçek doğruluk |
|---|---|---|---|
| [0.75, 0.90] | 2 | 0.85 | 1.0 |
| [0.90, 1.00] | 18 | 0.962 | 1.0 |
