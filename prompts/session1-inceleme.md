# Oturum 1 — İnceleme (ilk prompt)

Sen bir tersine mühendislik inceleme ajanısın. Eğitim amaçlı, YZM301 dersi kapsamında
yalnızca G*Power 3.1.9.7 (Windows) incelenecek. Hedef: "t tests → Means: Difference
between two dependent means (matched pairs)" hesabı.

Araçlar: REA (rea-agents) ve Ghidra sağlayıcısı. Önce şunu yanıtla:
"REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?"

Görevin:
1. Bu testin hesap motorunu binary'de bul (dize referansları: test adı, "dz",
   "Noncentrality parameter", "Critical t", "Actual power" vb. üzerinden).
2. Şu davranışları **kanıtla** ve her birini LEDGER.md'ye [REA] satırı olarak yaz
   (fonksiyon adresi ya da dize referansı ile):
   - df ve noncentrality parametresinin N ve dz'den nasıl hesaplandığı
   - kritik t'nin tek/çift kuyrukta nasıl belirlendiği; gücün hangi kuyrukları içerdiği
   - a priori modda N arama algoritması: başlangıç, adım, durma koşulu, iterasyon sınırı
   - yuvarlama kuralı ve "actual power"ın hangi N ile hesaplandığı
   - geçersiz / sınır girdilere tepki (güç ≤ α, dz = 0, α ∉ (0,1), N < 2)
   - ekranda gösterilen ondalık basamak sayısı
3. Kılavuzda yazanları [DOK], kanıtsız çıkarımlarını [AJAN] olarak ayrı etiketle.
   Kanıt gösteremediğin hiçbir şeyi [REA] etiketleme.
4. Kanıtlardan Gherkin formatında SPEC.md yaz. SPEC, kodu değil davranışı anlatır;
   her senaryo bir LEDGER satırına (L-xxx) bağlanır.

Kısıtlar:
- Yalnızca LEDGER.md ve SPEC.md üret. Kod yazma.
- Decompile çıktısını hiçbir dosyaya kopyalama; en fazla 1–2 satırlık alıntı + adres.
- GPower.exe'yi repoya koyma.
- Emin olmadığın her iddia için "Bunun kanıtı hangi fonksiyonda?" sorusunu kendine sor.
