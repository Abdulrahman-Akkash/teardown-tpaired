# GUI yolu değerlendirmesi (claude-sonnet-5-5)

`python eval/run_gui_eval.py` ile üretildi. Ajan G*Power'ı yalnızca ekran görüntüsüyle görür (`eval/gpower_gui_mcp.py`); N ve gücü görüntüden okur. Doğru = etiket doğru VE (t-paired ise) parametreler doğru, Calculate'e basıldı ve ekrandan okunan N/güç beklenen değerle aynı; (diğerleri için) G*Power'a dokunulmadı.

## Dil: tr

- Doğru seçim (uçtan uca): **10/10**; t-paired sorularında 5/5
- Soru başına ortalama token: 19224 (t-paired: 35349)
- Toplam maliyet: $0.2853; toplam süre 117.8 sn

| ID | Beklenen | Etiket | Ekrandan okunan | Ekran görüntüsü | Araç çağrısı | Doğru | Token | Süre (sn) | Maliyet |
|---|---|---|---|---|---|---|---|---|---|
| Q01 | t-paired | t-paired | `{"n_total": 54, "actual_power": 0.950212, "power": null}` | 3 | 10 | ✓ | 33909 | 16.96 | $0.0418 |
| Q02 | t-paired | t-paired | `{"n_total": 27, "actual_power": 0.8118316, "power": null}` | 4 | 13 | ✓ | 44864 | 19.15 | $0.0586 |
| Q03 | t-paired | t-paired | `{"n_total": 30, "actual_power": null, "power": 0.5628136}` | 3 | 11 | ✓ | 36805 | 19.06 | $0.0508 |
| Q04 | t-paired | t-paired | `{"n_total": 376, "actual_power": 0.9006277, "power": null}` | 3 | 9 | ✓ | 30137 | 17.2 | $0.0429 |
| Q05 | t-paired | t-paired | `{"n_total": 19, "actual_power": 0.909207, "power": null}` | 3 | 10 | ✓ | 31031 | 16.27 | $0.0465 |
| Q06 | ambiguous | ambiguous | `—` | 0 | 0 | ✓ | 3410 | 6.93 | $0.0135 |
| Q07 | t2-indep | t2-indep | `—` | 0 | 0 | ✓ | 3023 | 4.82 | $0.0079 |
| Q08 | anova-oneway | anova-oneway | `—` | 0 | 0 | ✓ | 3035 | 4.67 | $0.0080 |
| Q09 | chi2-contingency | chi2-contingency | `—` | 0 | 0 | ✓ | 3050 | 6.49 | $0.0084 |
| Q10 | multireg-r2 | multireg-r2 | `—` | 0 | 0 | ✓ | 2972 | 6.24 | $0.0070 |

## Dil: en

- Doğru seçim (uçtan uca): **10/10**; t-paired sorularında 5/5
- Soru başına ortalama token: 17776 (t-paired: 32337)
- Toplam maliyet: $0.2891; toplam süre 119.3 sn

| ID | Beklenen | Etiket | Ekrandan okunan | Ekran görüntüsü | Araç çağrısı | Doğru | Token | Süre (sn) | Maliyet |
|---|---|---|---|---|---|---|---|---|---|
| Q01 | t-paired | t-paired | `{"n_total": 54, "actual_power": 0.950212, "power": null}` | 3 | 11 | ✓ | 35632 | 17.19 | $0.0487 |
| Q02 | t-paired | t-paired | `{"n_total": 27, "actual_power": 0.8118316, "power": null}` | 3 | 10 | ✓ | 30325 | 15.97 | $0.0448 |
| Q03 | t-paired | t-paired | `{"n_total": 30, "actual_power": null, "power": 0.5628136}` | 3 | 10 | ✓ | 30569 | 16.79 | $0.0450 |
| Q04 | t-paired | t-paired | `{"n_total": 376, "actual_power": 0.9006277, "power": null}` | 3 | 10 | ✓ | 31174 | 16.91 | $0.0481 |
| Q05 | t-paired | t-paired | `{"n_total": 19, "actual_power": 0.909207, "power": null}` | 3 | 10 | ✓ | 33986 | 17.68 | $0.0473 |
| Q06 | ambiguous | ambiguous | `—` | 0 | 0 | ✓ | 3522 | 8.01 | $0.0155 |
| Q07 | t2-indep | t2-indep | `—` | 0 | 0 | ✓ | 3103 | 5.79 | $0.0095 |
| Q08 | anova-oneway | anova-oneway | `—` | 0 | 0 | ✓ | 3162 | 6.31 | $0.0103 |
| Q09 | chi2-contingency | chi2-contingency | `—` | 0 | 0 | ✓ | 3160 | 7.61 | $0.0103 |
| Q10 | multireg-r2 | multireg-r2 | `—` | 0 | 0 | ✓ | 3130 | 7.05 | $0.0097 |
