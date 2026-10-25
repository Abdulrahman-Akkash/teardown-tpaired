# Ajan Maliyet ve Süreç Günlüğü

| Oturum | Ajan / model | Bağlam (ölçülen) | Plan kullanımı | İterasyon | Not |
|---|---|---|---|---|---|
| 0+1 — kurulum, kâhin, inceleme | Claude Code (Claude Opus 5.5), Claude desktop uygulaması | ~295 bin token bağlam (oturum sonunda %74; %55'i mesajlar) | 5 saatlik limitin %17'si, haftalığın %18'i (abonelik planı; API faturası yok) | ~75 araç çağrısı; REA/Ghidra'ya ~40 sorgu | Ölçüm: uygulamanın `get_usage` aracı, 2026-10-25 |
| 2 — yazım | Ayrı Claude Code oturumu (yalnızca SPEC.md), Claude Opus 5.5 | ~168k bağlam tokenı (oturum sonu) | Abonelik planı; ayrı ücret ölçülmedi | 6 pytest koşusu; 1 düzeltme turu (statsmodels güç≈1 sapması → mpmath hakem) | Temiz oda: LEDGER/HALLUCINATIONS/scripts/tools okunmadı |

## Süreç

1. Kurulum: JDK 21 (winget), Node LTS 24.22.1, Ghidra 12.1.4 (GitHub release, SHA-256 doğrulandı),
   `rea-agents` 6.8.0 (npm, `github.com/morluto/rea` deposuna bağlı olduğu doğrulandı), G*Power 3.1.9.7
   (yalnızca psychologie.hhu.de). İlk Ghidra seçimi (12.2) yanlıştı (H-005).
2. Kâhin: G*Power GUI'si Win32 UI Automation (pywinauto) ile sürüldü; ekran görüntüleri
   `PrintWindow` ile yalnızca G*Power penceresinden alındı. 72 vektör, 3 tur.
3. İnceleme: REA CLI her çağrıda binary'yi Ghidra'ya yeniden aktarıyordu (~2 dk/çağrı). Bunun yerine
   REA MCP sunucusuna tek bir kalıcı oturum açan küçük bir köprü kullanıldı; ilk aktarım sonrası
   sorgular saniyeler sürdü.
4. İz: hata dizeleri → xrefs → sanal metot → vtable → sınıfa özgü yuvalar → mod dağıtıcısı → çözücü.

## Neyi farklı yapardık?

- REA MCP'yi en baştan kalıcı oturumla kullanmak (CLI'yi tek tek çağırmak zaman kaybıydı).
- GUI toplayıcısında sabit bekleme yerine "çıktı alanı değişti ya da hata kutusu açıldı" koşulunu
  beklemek (H-001 bundan çıktı).
- Etki büyüklüğü kontrolünü bulmak için etikete ("dz") değil, önce sınıfın vtable'ına bakmak (H-002).
- Uzun decompile çıktılarını konuşmaya hiç dökmemek; doğrudan dosyaya yazıp yalnızca gereken
  satırları okumak (bağlamın büyük kısmı bu dökümlere gitti).
