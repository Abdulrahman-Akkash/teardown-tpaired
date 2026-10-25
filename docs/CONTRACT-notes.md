# CLI sözleşmesi notları (t-paired)

Yönergede örnek yalnızca `t2-indep` için verilmiş; diğer ailelerin parametre adları
`CONTRACT.md` linkinde. **O dosya henüz repoda yok — aşağıdakiler varsayımdır,
CONTRACT.md gelince düzeltilmeli.**

| Bayrak | Anlam | Varsayım durumu |
|---|---|---|
| `--test t-paired` | Test ailesi etiketi (yönergedeki Jev etiket setinden) | kesin |
| `--mode a-priori \| post-hoc` | Mod | kesin |
| `--tails 1 \| 2` | Kuyruk sayısı | kesin (t2-indep örneğinden) |
| `--alpha` | α | kesin |
| `--power` | Hedef güç (a priori) | kesin |
| `--dz` | Etki büyüklüğü dz | **VARSAYIM** (`--d` de olabilir; ikisini de kabul etmek güvenli) |
| `--n` | Çift sayısı (post hoc) | **VARSAYIM** (`--n-total` da olabilir) |

Çıktı alanları (t2-indep örneğinden uyarlama, **VARSAYIM**):

- a priori: `{"n_total":54,"actual_power":0.9502,"critical":2.0057,"df":53,"ncp":3.6742}`
- post hoc: `{"n_total":30,"power":0.754,"critical":2.0452,"df":29,"ncp":2.7386}`

Ondalıklı alanlar 4 basamak (örnekteki gibi). Hata: `{"error":"..."}` + sıfırdan farklı çıkış kodu.
