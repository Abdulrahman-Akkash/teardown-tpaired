# Oturum 2 — Yazım (ilk prompt)

Temiz oda yazım oturumusun. Elindeki TEK kaynak `SPEC.md` (ve CLI sözleşmesi
`docs/CONTRACT-notes.md`). Ghidra/REA çıktısını, LEDGER.md'deki alıntıları ya da
herhangi bir decompile içeriğini görmeyeceksin ve istemeyeceksin.

Görevin:
1. `src/` altında Python ile tek bir hesap motoru yaz (eşleştirilmiş t testi,
   a priori ve post hoc). Dağılım fonksiyonları için scipy serbest.
2. Motoru çağıran ince bir CLI yaz: `gpower-clone --test t-paired ...`
   Çıktı tek satır JSON; geçersiz girdide `{"error":"..."}` ve sıfırdan farklı çıkış kodu.
3. SPEC.md'deki her Gherkin senaryosunu `tests/` altında bir teste çevir; önce testleri
   yaz, sonra motoru.
4. `oracle/gpower_vectors.csv` ve `oracle/statsmodels_vectors.csv` ile diferansiyel test
   yaz; uyum oranını ve her uyuşmazlığın açıklamasını `tests/REPORT.md`'ye yaz.

Kısıtlar:
- Hesap mantığı yalnızca motorda olur. CLI (ve ileride MCP/ajan) motoru çağırır, hesap yapmaz.
- SPEC'te olmayan bir davranışa ihtiyaç duyarsan uydurma: SPEC'e "AÇIK SORU" olarak not düş.
- Yeniden yazıma "G*Power" adını verme.
