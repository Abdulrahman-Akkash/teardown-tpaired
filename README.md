# YZM301 Teardown Sprint — t testi, eşleştirilmiş ortalama (t-paired)

> **Yapılan katmanlar:** ☑ CLI (temel) · ☑ MCP sunucusu (+15) · ☑ AI ajanı (+10)

Bu repo, bir güç analizi aracının **eşleştirilmiş t testi** (örnek senaryo: aynı hastada
tedavi öncesi ve sonrası tansiyon) hesabının tersine mühendislikle incelenmesini, kanıt
defterini, temiz oda yeniden yazımını ve ajan çağına taşınmasını içerir.

Bu yeniden yazım G*Power **değildir** ve onun yerine geçmez. Referans (kâhin) olarak
G*Power 3.1.9.7 kullanılmıştır.

## Atıf

- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G*Power 3: A flexible
  statistical power analysis program for the social, behavioral, and biomedical sciences.
  *Behavior Research Methods, 39*, 175–191.
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses
  using G*Power 3.1: Tests for correlation and regression analyses.
  *Behavior Research Methods, 41*, 1149–1160.

G*Power yalnızca resmi sayfasından dağıtılır: https://www.psychologie.hhu.de (G*Power sayfası).

## Sürüm bilgisi

| Öğe | Değer |
|---|---|
| İncelenen sürüm | G*Power 3.1.9.7 (Windows), `GPowerWin_3.1.9.7.zip` (resmi sayfa) |
| İkili dosya | Arşivdeki çalıştırılabilir dosyanın adı `GPowerNT.exe` (yönergedeki "GPower.exe") |
| GPowerNT.exe SHA-256 | `c63e6a133eb6372932f810c08cc33dc35a06d1ddb658f897bd6c34a754efc812` |
| Ghidra | 12.1.4 (`ghidra_12.1.4_PUBLIC_20260921.zip`, SHA-256 `ddac49f9…d2d4db` doğrulandı) |
| JDK | Eclipse Temurin 21.0.12 |
| REA (rea-agents) | 6.8.0 (npm, `github.com/morluto/rea`) |
| Node.js | 24.22.1 |

## Ortam kontrolü

Ajana sorulan soru: *"REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?"*

![REA/Ghidra kontrolü](docs/rea-check.png)

`scripts/rea_check_shot.py` ayrı bir konsol açıp `rea doctor` (Ghidra satırları) ve REA MCP'li
`claude -p` ile bu soruyu çalıştırır; görüntü yalnızca o pencereden alınır.

## Kurulum

```bash
# 1) Ortamı kontrol et (JDK 21, Ghidra, REA, Python paketleri, GPower.exe hash)
powershell -ExecutionPolicy Bypass -File scripts/check-env.ps1 -GPowerExe "C:\Program Files\G*Power\GPower.exe"

# 2) Python bağımlılıkları
python -m pip install -r requirements.txt

# 3) Paketi kur (gpower-clone ve tpaired-mcp komutları)
python -m pip install -e .
```

## Çalıştırma (CLI sözleşmesi)

Hesap mantığı yalnızca `src/tpaired/engine.py`'dedir. CLI (`src/tpaired/cli.py`) ve MCP sunucusu
(`src/tpaired/mcp_server.py`) aynı ince katmanı (`src/tpaired/output.py`: alan adları + 4 basamak
yuvarlama) çağırır; hesap yapmazlar.

```bash
gpower-clone --test t-paired --mode a-priori --tails 2 --dz 0.5 --alpha 0.05 --power 0.95
# {"n_total":54,"actual_power":0.9502,"critical":2.0057,"df":53,"ncp":3.6742}

gpower-clone --test t-paired --mode post-hoc --tails 2 --dz 0.5 --alpha 0.05 --n 30
# {"n_total":30,"power":0.754,"critical":2.0452,"df":29,"ncp":2.7386}

# Kurulum yapmadan, aynı CLI:
PYTHONPATH=src python -m tpaired --test t-paired --mode a-priori --tails 2 --dz 0.5 --alpha 0.05 --power 0.95
```

- `--dz` yerine `--d`, `--n` yerine `--n-total` da kabul edilir (`docs/CONTRACT-notes.md`; ikisi birden verilirse hata).
- Çıktı her zaman tek satır JSON. Geçersiz girdide `{"error":"..."}`; çıkış kodu girdi doğrulama
  hatasında 1, argüman hatasında 2.
- Windows'ta Microsoft Store Python'u kullanılıyorsa `gpower-clone.exe` kullanıcı `Scripts` klasörüne
  kurulur; o klasör PATH'te değilse `python -m tpaired` kullanın.

### Testler

```bash
python -m pytest            # SPEC §6 senaryoları, 72 GUI + 577 statsmodels vektörü, CLI, MCP
python tests/make_report.py # tests/REPORT.md'yi yeniden üretir
```

Uyum özeti (`tests/REPORT.md`): GUI vektörlerinde 17/17 hata satırı, 52/52 hesaplanabilir satırda N tam
ve tüm ondalıklı alanlar 1e-7 içinde; 3 satır SPEC §7 bilinen sapma (N > 10¹⁰).

## MCP sunucusu (+15)

Resmî `mcp` Python SDK'sı (2.x, `MCPServer`), stdio taşıması:

```bash
tpaired-mcp                     # ya da: PYTHONPATH=src python -m tpaired.mcp_server
```

İstemci yapılandırması örneği (Claude Desktop / Claude Code `mcpServers`):

```json
{ "mcpServers": { "tpaired-power": { "command": "python", "args": ["-m", "tpaired.mcp_server"] } } }
```

Tek araç: **`t_paired_power`** — CLI ile aynı motoru ve aynı çıktıyı kullanır (`tests/test_mcp.py`
72 GUI vektörü + statsmodels örneklemi üzerinde CLI ile birebir aynı JSON'u doğrular, ayrıca gerçek
stdio alt sürecini dener).

Girdi şeması:

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `mode` | string | evet | `"a-priori"` veya `"post-hoc"` |
| `tails` | integer | evet | `1` veya `2` |
| `dz` | number \| string | evet | Etki büyüklüğü dz, −20…20; sayı değilse 0 sayılır |
| `alpha` | number | evet | 1e-7…0.9999999 |
| `power` | number \| null | a-priori'de | Hedef güç, α…0.9999999 |
| `n` | number \| null | post-hoc'ta | Çift sayısı (yarım yukarı yuvarlanır), 3…2147483646 |

Çıktı (`structuredContent`, metin içeriği aynı JSON):

- a priori: `{"n_total", "actual_power", "critical", "df", "ncp"}`
- post hoc: `{"n_total", "power", "critical", "df", "ncp"}`
- geçersiz girdi: `{"error": "..."}`

## AI ajanı (+10)

Klinisyenin Türkçe (ya da İngilizce) sorusunu alır, test ailesini seçer, parametreleri çıkarır ve
**yalnızca** `t_paired_power` MCP aracını çağırır. N, güç, kritik t, df ve ncp hep motordan gelir;
ajan hiçbir sayı hesaplamaz.

```bash
python -m tpaired.agent "Aynı hastalarda tedavi öncesi ve sonrası tansiyon ölçeceğiz, dz = 0.5, alfa 0.05, güç 0.95, iki yönlü. Kaç hasta gerekir?"
python -m tpaired.agent --json --log run.jsonl "..."   # tam sonuç + araç çağrı kaydı
```

- Ajan headless Claude Code'dur (`claude -p`, model `claude-sonnet-5-5`). `--strict-mcp-config` ve
  `--tools ""` ile tek görünen araç `mcp__tpaired-power__t_paired_power`'dır; yerleşik araçlar
  (Bash, Read, …) kapalıdır, yani ajan hesap yapmak için kod da çalıştıramaz. Claude Code'a
  `claude /login` ile giriş yapılmış olmalıdır.
- **Etiket kümesi:** `t2-indep`, `t-paired`, `anova-oneway`, `chi2-contingency`, `multireg-r2`,
  `ambiguous`, `unsupported`. **Güven eşiği 0.75:** araç yalnızca etiket `t-paired` ve güven ≥ 0.75
  ise çağrılır. Aksi hâlde karar araştırmacıya bırakılır (eksik parametre ya da desteklenmeyen tasarım
  kısa bir Türkçe soruyla belirtilir).
- **Jev yok:** Ödevde önerilen Jev sınıflandırıcısı kullanılmadı. Sınıflandırma, sistem istemiyle
  yalnızca bu etiket kümesine kısıtlanmış bir LLM ile yapılır (`src/tpaired/agent.py`, `SYSTEM_PROMPT`).
- dz soruda sayı ya da Cohen etiketi (küçük 0.2, orta 0.5, büyük 0.8) olarak verilmelidir. Ham
  ortalama farkı ve SD verilirse ajan dz'yi kendisi hesaplamaz, `ambiguous` der ve dz'yi ister (Q06).

### Değerlendirme

`python eval/run_eval.py`: 10 soru (`eval/questions.json`; 5 t-paired, 1 belirsiz, 4 başka aile),
Türkçe ve İngilizce. Her soru için beklenen aile, parametreler ve N (ya da güç) tanımlıdır. Tam tablo
[eval/RESULTS.md](eval/RESULTS.md); her koşunun araç çağrı kaydı `eval/logs/<dil>-<id>.jsonl`.

| Dil | Doğru seçim (uçtan uca) | Etiket | Ort. token / soru | Ort. maliyet / soru | Ort. süre / soru |
|---|---|---|---|---|---|
| Türkçe | **10/10** | 10/10 | 4 267 | $0.0130 | 7.1 sn |
| İngilizce | **10/10** | 10/10 | 4 478 | $0.0141 | 7.7 sn |

"Doğru" = etiket doğru VE t-paired sorularında araç beklenen parametrelerle çağrıldı ve motorun N/gücü
beklenen değerle geldi; diğer sorularda araç hiç çağrılmadı. Token sayısı önbellekten okunanlar dahil
toplam girdi + çıktıdır; maliyet ve süre Claude Code'un raporladığı değerlerdir.

**TR ve EN karşılaştırması:** Doğrulukta fark yok (10/10 ve 10/10, aynı araç girdileri). İngilizce
koşular ortalama %5 daha fazla token kullandı. Bu fark büyük ölçüde Q09'daki tek koşudan geliyor:
model orada iki tur yaptı (4 641 + 1 043 token).

**Kalibrasyon** (20 koşu): güven 0.75–0.90 aralığında 2 koşu (ikisi de Q06 `ambiguous`, ort. 0.85,
gerçek doğruluk 1.0); 0.90–1.00 aralığında 18 koşu (ort. 0.962, doğruluk 1.0). Hiç hata olmadığı
için set kalibrasyonu sınamaya yetmez. Model biraz *az güvenli* görünüyor (doğruluk 1.0 iken güven
0.85–0.97), ama 20 koşu bunu söylemek için azdır.

### MCP yolu ile GUI ekran görüntüsü yolu

| | MCP yolu (ölçüldü) | GUI ekran görüntüsü yolu |
|---|---|---|
| Token / soru | 4 267 (TR), 4 478 (EN); t-paired sorularında ~5 540 | Yalnızca görüntüler: **≥ 5 427** (tahmin) |
| Doğruluk | 20/20 | Ölçülmedi |
| Süre / soru | 7.1–7.7 sn | Ölçülmedi |

GUI sütunu bir **tahmindir**, uçtan uca ölçüm değildir. `python eval/measure_gui_tokens.py`, bir
G*Power ekran görüntüsünün (`GP-001.png`) modele maliyetini ölçer. Aynı istem bir kez görüntüyle, bir
kez aynı bilginin tek satırlık metniyle çalıştırılır; girdi token farkı **603 token/görüntü** çıktı
(`eval/gui_tokens.json`). Bir a priori soru en az 9 eylem ister (pencereyi bul, aile, test, analiz
tipi, kuyruk, dz, α, güç, Calculate + oku) ve her eylemden sonra bir ekran görüntüsü gerekir. Bu da
yalnızca görüntüler için 9 × 603 = 5 427 token eder. Bu bir alt sınırdır: ajanın kendi istemi ve araç
tanımları hariçtir, ve her turda önceki görüntüler bağlamda kalırsa toplam girdi
603 × (1 + 2 + … + 9) ≈ 27 000 tokena çıkar. GUI yolunun doğruluğu ve süresi ölçülemedi, çünkü bu
ortamda bilgisayar kullanımı (computer use) yoktu. MCP yolu ise tek araç çağrısıyla motorun kesin
sayısını döndürür; ekrandan sayı okuma hatası riski taşımaz.

## Repo yapısı

| Yol | İçerik |
|---|---|
| `SPEC.md` | Gherkin kabul kriterleri (Oturum 1 üretir) |
| `LEDGER.md` | Kanıt defteri — [DOK] / [REA] / [AJAN] |
| `HALLUCINATIONS.md` | Ajanın yanlış çıkardığı şeyler ve yakalayan testler |
| `AGENT_COST.md` | Ajan, token, maliyet, iterasyon |
| `prompts/` | İki oturumun ilk prompt'ları |
| `oracle/` | G*Power vektörleri (CSV) + ekran görüntüleri, statsmodels ölçek vektörleri |
| `src/tpaired/` | `engine.py` (tek hesap motoru), `output.py`, `cli.py`, `mcp_server.py` — Oturum 2 yazar |
| `tests/` | SPEC senaryo testleri, diferansiyel testler, `REPORT.md` uyum raporu |
| `src/tpaired/agent.py` | AI ajanı (yalnızca MCP aracını çağırır, hesap yapmaz) |
| `eval/` | 10 soruluk değerlendirme seti, sonuçlar (`RESULTS.md`), araç çağrı kayıtları (`logs/`) |
| `docs/` | Demo videosu, REA kontrol görüntüsü, CLI sözleşmesi notları |
| `scripts/` | Ortam kontrolü, GUI kâhin toplayıcı (`collect_gpower.py`), statsmodels kâhini, demo ve REA görüntüsü üreticileri |

## Kâhin

- `oracle/gpower_vectors.csv`: G*Power arayüzünden 72 vektör (17'si geçersiz girdi), her biri
  `oracle/screenshots/<id>.png` ile. `scripts/collect_gpower.py` arayüzü Win32 UI Automation ile sürer;
  hesap yapmaz, yalnızca ekrandakini kaydeder.
- `oracle/statsmodels_vectors.csv`: 577 ölçek vektörü (kesirli N).

## Demo

56 saniyelik CLI videosu: [docs/demo.mp4](docs/demo.mp4). `scripts/make_demo.py` komutları gerçekten
çalıştırır ve gerçek çıktılarını terminal kaydı olarak çizer.
