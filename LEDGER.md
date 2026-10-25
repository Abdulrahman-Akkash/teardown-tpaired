# Kanıt Defteri (LEDGER) — eşleştirilmiş t testi

Hedef: `GPowerNT.exe` (G*Power 3.1.9.7, Windows, x86 PE)
SHA-256: `c63e6a133eb6372932f810c08cc33dc35a06d1ddb658f897bd6c34a754efc812`
Araçlar: REA 6.8.0 (`rea-agents`, MCP stdio) + Ghidra 12.1.4 sağlayıcısı, JDK 21.0.12.
Binary'de PDB yüklü değil; fonksiyon adları Ghidra'nın verdiği `FUN_<adres>` biçiminde.

Etiketler:
- **[DOK]** Kılavuzda ya da makalede yazıyor (kaynak + sayfa).
- **[REA]** Binary'den kanıtlandı: fonksiyon adresi + REA evidence ID. Evidence ID'ler, REA'nın
  aynı binary (aynı SHA-256) ve aynı analiz profili için ürettiği içerik özetleridir.
- **[AJAN]** Ajanın çıkarımı; kanıtı yok → diferansiyel testle sınanmalı.
- **[GUI]** G*Power arayüzünde gözlendi (`oracle/gpower_vectors.csv` satırı + ekran görüntüsü).

Kural: decompile çıktısı bu dosyaya konmaz. Yalnızca adres, sabit değer ve davranışın kendi
cümlelerimizle özeti yazılır.

## 1. Testin binary'deki yeri

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-001 | [REA] | Test adı dizesi `"Means: Difference between two dependent means (matched pairs)"` 0x5cb56c adresinde; tek referansı 0x4dcf4a (`FUN_004dcf10`, ad döndüren sanal metot). | xrefs `ev_3f66665e3119e5f0…`; `FUN_004dcf10` `ev_0de6be1decda5b01…` | — |
| L-002 | [REA] | Test bir C++ sınıfı; `FUN_004dcf10` vtable'da 0x5cacd8 yuvasında. Sınıfa özgü yuvalar: etki büyüklüğü kontrolü 0x4db990 (0x5cad64), mod dağıtıcısı 0x4dc2a0 (0x5cad28), varsayılanlar 0x4dc230 (0x5cad18). | read_bytes `ev_cd76dbde92a011e5…`, `ev_03dda6225cd08005…` | — |
| L-003 | [REA] | `"dz"` etiketi veren 0x4dd090 bu teste ait DEĞİL; aynı yuvayı paylaşan iki Wilcoxon sınıfına ait (adları 0x4dde10 "Wilcoxon signed-rank test (one sample case)", 0x4e3170 "… (matched pairs)"). | `ev_2684de372e3d762f…`, `ev_68c43da2e66490b3…`, `ev_dfb1a8bedd7edeb7…` | H-002 |

## 2. Mod dağıtıcısı (0x4dc2a0)

`FUN_004dc2a0` bir `switch(mod)` ile beş analiz türünü ayırır. İç mod numaraları GUI sırasından
farklıdır: **0 = a priori, 1 = sensitivity, 2 = post hoc, 3 = criterion, 4 = compromise**
(her dalın hangi girdileri okuduğundan çıkarıldı). Kanıt: `ev_7d8053030ee765ff…`

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-010 | [REA] | **A priori dalı N için aralık kontrolü yapmaz.** Yalnızca etki büyüklüğü, α, güç ve "güç ≥ α" kontrolleri çağrılır; çözücünün döndürdüğü N bir `double` alanına yazılır. | `FUN_004dc2a0` case 0, `ev_7d8053030ee765ff…` | GP-057 (N = 19 622 220 504), GP-058, GP-071 |
| L-011 | [REA] | Post hoc (ve sensitivity/criterion/compromise) dalları N'yi tamsayıya çevirdikten sonra `FUN_00488a10(N, 3, 0x7ffffffe)` ile **3 ≤ N ≤ 2 147 483 646** kontrol eder. Bu sabitler 0x4dc4ec, 0x4dc629, 0x4dc735, 0x4dc8af adreslerindeki `push 0x7ffffffe; push 3` dizileri. | search_bytes `ev_6faa0ba5fdbc350b…`; `FUN_00488a10` `ev_e7ba8b9fa32206a0…` | GP-041, GP-042, GP-043, GP-062 |
| L-012 | [REA]+[GUI] | **Tutarsızlık:** a priori, güç = α iken N = 2 döndürebilir (L-021), ama post hoc aynı N = 2'yi reddeder (L-011). Kılavuzda yok. | L-010, L-011 | GP-020 (N = 2), GP-041 (N = 2 hata) |
| L-013 | [REA] | "Güç ≥ α" kontrolü (`FUN_004880e0`) yalnızca a priori ve sensitivity dallarında çağrılır. Karşılaştırma `α ≤ güç`, yani **güç = α kabul edilir**. | `ev_5142d3e543b9ca02…`; çağrı yerleri `ev_7d8053030ee765ff…` | GP-020, GP-022, GP-023 kabul; GP-021 ret |
| L-014 | [REA] | Bu sınıfta kullanılmayan bir N kontrolü daha var: 0x4d9310 (alt sınır 2, kesme ile tamsayı). Vtable'da duruyor ama 0x4dc2a0'daki aktif yol alt sınır 3 kullanıyor. | `ev_2fd356a0ddb66f3e…` | H-003 |

## 3. Girdi doğrulama

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-020 | [REA] | α geçerli ⇔ **1e-7 ≤ α ≤ 0.9999999** (iki uç dahil). Hata metni `"(1e-07, 1)"` açık aralık gibi görünse de alt uç kabul edilir. | `FUN_00487460` `ev_1e11324b2744da68…`; dize xref `ev_4142c94c48266933…` | GP-059 kabul (α = 1e-7), GP-028/GP-029/GP-051/GP-052 ret |
| L-021 | [REA] | Güç geçerli ⇔ **1e-7 ≤ güç ≤ 0.9999999**; güç = 1 reddedilir. | `FUN_00488010` `ev_6b2a9eea390d27ee…`; xref `ev_1900ad648d532377…` | GP-030, GP-031 |
| L-022 | [REA] | A priori: `|dz| ≤ 1e-5` ise hata ("absolute value of the effect size be greater than 0.00001"). Karşılaştırma katı: tam 1e-5 kabul edilir. | `FUN_004db990` `ev_a639daa83de1a250…`; xref `ev_d9868e305dc2ab26…` | GP-025 (dz = 0) ret, GP-071 (dz = 1e-5) kabul |
| L-023 | [REA]+[GUI] | Tüm modlarda etki büyüklüğü **−20 ≤ dz ≤ 20** aralığında olmalı (sabitler −20.0 ve 20.0, `FUN_004db990` → `FUN_00487b70`). Hata metni "Effect size d …" der, "dz" demez. | `ev_a639daa83de1a250…` | GP-067 (20) kabul; GP-068, GP-069, GP-070 ret |
| L-024 | [GUI] | Sayı olmayan metin ("abc") hata vermez, 0 olarak okunur ve dz = 0 hatasına düşer. | — (ayrıştırıcı incelenmedi) | GP-032 |
| L-025 | [GUI] | Post hoc'ta kesirli N **en yakın tamsayıya yuvarlanır, yarım yukarı**: 2.4 → 2 (ret), 2.5 → 3, 3.4999 → 3, 3.5 → 4, 4.5 → 5. | Yuvarlama `FUN_0048ab70` → `FUN_0048b8d0` içinde; tam kural binary'de doğrulanmadı | GP-044, GP-063, GP-064, GP-065, GP-072 |

## 4. A priori N çözücü

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-030 | [REA] | A priori N, **sürekli N üzerinde kök bulma** ile çözülür: f(N) = güç(N) − hedef güç. Çözücü `FUN_004f9bb0`: Brent tipi (ikiye bölme + ters ikinci derece/sekant adımları), **tolerans 1e-10**, **en fazla 300 iterasyon**. | `FUN_00496aa0` `ev_053a6a275b6389a2…`; `FUN_004f9bb0` `ev_810f858e3431b4b9…` | GP-016, GP-056 |
| L-031 | [REA] | Başlangıç aralığı **[2, 100]** (`FUN_0049a210` → `FUN_004962d0(2.0, 100.0)`). | `ev_8bea9d4b498baedf…` | GP-020 |
| L-032 | [REA] | Kök bulunduktan sonra yuvarlama `FUN_00496a20`: önce **10 ondalık basamağa yuvarla** (x·1e10 + 0.5 → floor → /1e10), sonra **ceil**. Böylece 54.00000000001 gibi kayan nokta artıkları 55'e taşmaz. | `ev_c9d708c20f04f7ad…` | GP-001…GP-035 (N tam eşleşme) |
| L-033 | [REA] | Yuvarlanan N alt sınırdan (2) küçükse alt sınıra çekilir; ardından "actual power" bu **tamsayı N** ile yeniden hesaplanır. | `ev_053a6a275b6389a2…` | GP-020 (N = 2, actual power 0.0619486) |
| L-034 | [GUI] | Çözücü int sınırını aşan N üretebilir: dz = 1e-5 için N = 78 488 272 181. N ve df ekranda tamsayı olarak gösterilir. | L-010 | GP-057, GP-058, GP-071 |

## 5. Güç fonksiyonu

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-040 | [DOK] | H0: merkezi t(N−1); H1: merkezi olmayan t(N−1, δ), δ = dz·√N. | Kılavuz §19.5, s. 49 | GP-036…GP-055 |
| L-041 | [REA] | Güç çağrısı, iki gruplu genel bir arayüz üzerinden yapılır: N toplam, `n1 = n2 = N/2` olarak bölünür ve sınıf metodu `FUN_004d38b0` toplam N'yi `n1 + n2` olarak yeniden kurar. Eşleştirilmiş testte bu bölme sonucu değiştirmez. | `FUN_004bdee0` `ev_6d7f03123ae156e0…`; `FUN_004d38b0` `ev_e76cbe280dd1bbd1…` | — |
| L-042 | [REA] | İki kuyrukta α ikiye bölünür (kritik değer 1 − α/2 quantile'ı); tek kuyrukta α. Kritik değerin işareti etki büyüklüğünün işaretini izler: dz < 0 ise kritik t negatif raporlanır. | `FUN_004d38b0` `ev_e76cbe280dd1bbd1…` | GP-026, GP-027, GP-047, GP-048 (negatif kritik t) |
| L-043 | [REA]+[GUI] | İki kuyruklu güç **iki kuyruğu da** içerir (öteki kuyruğun küçük katkısı eklenir). dz = 0 iken güç tam α. | `FUN_004d38b0`; GP-045 = 0.0500000 | GP-045, GP-046 |
| L-044 | [GUI] | Tek kuyrukta negatif dz, alt kuyruk testi olarak ele alınır (güç pozitif dz ile aynı). | — | GP-048 = GP-037 (0.8482542) |

## 6. Çıktı biçimi

| ID | Etiket | İddia | Kanıt | Sınayan |
|---|---|---|---|---|
| L-050 | [GUI] | Ekranda δ, kritik t ve güç **7 ondalık basamakla** gösterilir (ör. 0.8321145, 2.0095752); df ve N tamsayı. | Ekran görüntüleri | Tüm vektörler |
| L-051 | [DOK] | Kılavuz aynı değerleri 6 basamakla verir (0.832114); GUI 7 basamak gösterir. | Kılavuz s. 48 | GP-038 |

## 7. SPEC doğrulaması (Oturum 1)

SPEC'teki formüller scipy ile bir karalama betiğinde (repoya konmadı) GUI vektörlerine uygulandı:
hata dışı 55 vektörün 52'sinde N tam ve güç 1e-6 içinde eşleşti. Eşleşmeyen 3 vektör N > 10¹⁰
olanlar (GP-057, GP-058, GP-071): sapma ~%0.001; sebebi merkezi olmayan t'nin sayısal hesabı ([AJAN]).

## 8. Açık sorular

- L-025'teki yuvarlama kuralı GUI ile gözlendi, binary'de satır satır doğrulanmadı ([AJAN] düzeyinde güven).
- Merkezi olmayan t dağılımının sayısal algoritması (seri/integral) incelenmedi; yeniden yazımda
  scipy kullanılacağı için doğruluk diferansiyel testle ölçülür.
