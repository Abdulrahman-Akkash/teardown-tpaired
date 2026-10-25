# SPEC — t testi, eşleştirilmiş ortalama (t-paired)

Bu dosya Oturum 1 (inceleme) çıktısıdır. Oturum 2 (yazım) yalnızca bunu, `docs/CONTRACT-notes.md`'yi
ve `oracle/` altındaki CSV'leri kullanır. Her kural bir LEDGER satırına (`L-xxx`) bağlıdır.

## 1. Kapsam

- Test: eşleştirilmiş iki ortalama farkı (N çift; farklar üzerinde tek örneklem t testi).
- Modlar: `a-priori` (N hesapla) ve `post-hoc` (güç hesapla). Diğer modlar kapsam dışı.

## 2. Tanımlar

| Sembol | Tanım | Kaynak |
|---|---|---|
| N | Çift sayısı (ekrandaki "Total sample size") | L-040 |
| df | N − 1 | L-040 |
| δ (ncp) | dz · √N | L-040 |
| kritik t | Merkezi t(df) dağılımının quantile'ı: iki kuyrukta 1 − α/2, tek kuyrukta 1 − α. dz < 0 ise işareti negatif raporlanır. | L-042 |
| güç (iki kuyruk) | P(T > t_c) + P(T < −t_c), T ~ merkezi olmayan t(df, \|δ\|), t_c = \|kritik t\| | L-042, L-043 |
| güç (tek kuyruk) | P(T > t_c), T ~ merkezi olmayan t(df, \|δ\|) | L-042, L-044 |

Güç yalnızca |dz|'ye bağlıdır: dz ve −dz aynı N'yi ve gücü verir; yalnızca δ ve kritik t'nin
işareti dz'nin işaretini izler (L-042, L-044).

## 3. Girdi doğrulama (hesaptan önce, bu sırayla)

| Kural | Mod | Kaynak |
|---|---|---|
| dz sayıya çevrilemezse 0 kabul edilir (sonra aşağıdaki kurallar uygulanır) | ikisi | L-024 |
| −20 ≤ dz ≤ 20, değilse hata | ikisi | L-023 |
| a priori'de \|dz\| < 1e-5 ise hata (tam 1e-5 geçerli) | a-priori | L-022 |
| 1e-7 ≤ α ≤ 0.9999999, değilse hata | ikisi | L-020 |
| 1e-7 ≤ güç ≤ 0.9999999, değilse hata | a-priori | L-021 |
| α ≤ güç, değilse hata (güç = α geçerli) | a-priori | L-013 |
| Post hoc N: önce en yakın tamsayıya yuvarla (yarım yukarı: 2.5 → 3), sonra 3 ≤ N ≤ 2 147 483 646, değilse hata | post-hoc | L-011, L-025 |
| A priori'de bulunan N için üst sınır YOK (int sınırını aşabilir) | a-priori | L-010, L-034 |

## 4. A priori N çözücü

1. f(N) = güç(N) − hedef_güç, N sürekli kabul edilir (df = N − 1, δ = dz·√N kesirli N ile).
2. Kökü Brent tipi bir yöntemle bul: başlangıç aralığı [2, 100]; kök bu aralıkta değilse üst sınırı
   genişlet. Tolerans 1e-10, en fazla 300 iterasyon (L-030, L-031).
3. Yuvarlama: N_kesirli'yi önce 10 ondalık basamağa yuvarla, sonra yukarı yuvarla (ceil) (L-032).
4. Sonuç 2'den küçükse N = 2 (L-033).
5. `actual_power`, `critical`, `df`, `ncp` bu **tamsayı N** ile hesaplanır (L-033).

Not: kütüphaneler (pwr, statsmodels) N'yi kesirli verir; G*Power ceil(round(N, 10)) kullanır.
Doğrudan `ceil` ile fark yalnızca N_kesirli bir tamsayıya 1e-10'dan yakın olduğunda ortaya çıkar.

## 5. CLI sözleşmesi

```
gpower-clone --test t-paired --mode a-priori --tails {1|2} --dz <x> --alpha <x> --power <x>
gpower-clone --test t-paired --mode post-hoc --tails {1|2} --dz <x> --alpha <x> --n <x>
```

Çıktı tek satır JSON (alan adları `docs/CONTRACT-notes.md`'deki varsayıma göre; CONTRACT.md gelince
güncellenecek):

- a priori: `{"n_total":54,"actual_power":0.9502,"critical":2.0057,"df":53,"ncp":3.6742}`
- post hoc: `{"n_total":30,"power":0.754,"critical":2.0452,"df":29,"ncp":2.7386}`

Ondalıklı alanlar 4 basamağa yuvarlanır (sözleşme örneği gibi); motor tam hassasiyeti saklar.
Geçersiz girdide `{"error":"<açıklama>"}` ve çıkış kodu ≠ 0.

## 6. Kabul kriterleri

```gherkin
Feature: Eşleştirilmiş t testi için örneklem büyüklüğü ve güç

  Background:
    Given test ailesi "t-paired"

  # L-040, L-050 — kılavuz s.48 örneği, GP-038
  Scenario: Kılavuzdaki post hoc örneği
    Given mod "post-hoc", kuyruk 2, dz 0.421637, alfa 0.05, N 50
    When hesaplanır
    Then df 49 olur
    And ncp 2.9814238'e, kritik t 2.0095752'ye, güç 0.8321145'e 1e-7 içinde eşittir

  # L-030, L-032 — GP-001
  Scenario: Tipik a priori hesap
    Given mod "a-priori", kuyruk 2, dz 0.5, alfa 0.05, güç 0.95
    When hesaplanır
    Then N 54 olur
    And actual_power 0.9502120, kritik t 2.0057460, df 53, ncp 3.6742346

  # L-032 — GP-012 (kılavuz s.50: 1492)
  Scenario: Büyük N yukarı yuvarlanır
    Given mod "a-priori", kuyruk 2, dz 0.1, alfa 0.01, güç 0.90
    Then N 1492 ve actual_power 0.9001687 olur

  # L-031, L-033, L-013 — GP-020
  Scenario: Güç alfaya eşitse N alt sınıra (2) çekilir
    Given mod "a-priori", kuyruk 2, dz 0.5, alfa 0.05, güç 0.05
    Then N 2, df 1 ve actual_power 0.0619486 olur

  # L-013 — GP-021
  Scenario: Güç alfadan küçükse hata
    Given mod "a-priori", kuyruk 2, dz 0.5, alfa 0.05, güç 0.03
    Then hata "Power must be greater than or equal to alpha" döner ve çıkış kodu sıfırdan farklıdır

  # L-010, L-034 — GP-057
  Scenario: A priori N int sınırını aşabilir
    Given mod "a-priori", kuyruk 2, dz 0.00002, alfa 0.05, güç 0.80
    Then N 19622220504 olur ve hata dönmez

  # L-022 — GP-025, GP-071
  Scenario Outline: A priori etki büyüklüğü alt eşiği
    Given mod "a-priori", kuyruk 2, dz <dz>, alfa 0.05, güç 0.80
    Then sonuç <sonuç>
    Examples:
      | dz      | sonuç                    |
      | 0       | hata                     |
      | 0.00001 | N 78488272181            |

  # L-023 — GP-067..GP-070
  Scenario Outline: Etki büyüklüğü aralığı
    Given mod "<mod>", kuyruk 2, dz <dz>, alfa 0.05, <üçüncü>
    Then sonuç <sonuç>
    Examples:
      | mod      | dz    | üçüncü    | sonuç        |
      | post-hoc | 20    | N 10      | güç 1.0000000 |
      | post-hoc | 20.5  | N 10      | hata         |
      | post-hoc | -20.5 | N 10      | hata         |
      | a-priori | 25    | güç 0.80  | hata         |

  # L-020, L-021 — GP-028..GP-031, GP-059
  Scenario Outline: Alfa ve güç aralıkları
    Given mod "a-priori", kuyruk 2, dz 0.5, alfa <alfa>, güç <güç>
    Then sonuç <sonuç>
    Examples:
      | alfa      | güç  | sonuç  |
      | 0         | 0.80 | hata   |
      | 1         | 0.80 | hata   |
      | 0.0000001 | 0.80 | N 167  |
      | 0.05      | 1    | hata   |
      | 0.05      | 0    | hata   |

  # L-011, L-025 — GP-041..GP-044, GP-062..GP-065, GP-072
  Scenario Outline: Post hoc N yuvarlama ve aralık
    Given mod "post-hoc", kuyruk 2, dz 0.5, alfa 0.05, N <n>
    Then sonuç <sonuç>
    Examples:
      | n      | sonuç      |
      | 0      | hata       |
      | 1      | hata       |
      | 2      | hata       |
      | 2.4    | hata       |
      | 2.5    | df 2       |
      | 3      | df 2       |
      | 3.4999 | df 2       |
      | 3.5    | df 3       |
      | 4.5    | df 4       |

  # L-042, L-043, L-044 — GP-045..GP-048
  Scenario: Negatif dz aynı gücü verir, işaretler döner
    Given mod "post-hoc", kuyruk 2, dz -0.5, alfa 0.05, N 30
    Then güç 0.7539647 olur
    And ncp -2.7386128 ve kritik t -2.0452296 olur

  Scenario: dz sıfırken güç alfaya eşittir
    Given mod "post-hoc", kuyruk 2, dz 0, alfa 0.05, N 30
    Then güç 0.0500000 olur

  # L-024 — GP-032
  Scenario: Sayı olmayan dz sıfır sayılır
    Given mod "a-priori", kuyruk 2, dz "abc", alfa 0.05, güç 0.80
    Then dz = 0 hatası döner

  # Diferansiyel test
  Scenario: Kâhin vektörleri
    Given oracle/gpower_vectors.csv içindeki her satır
    When CLI aynı girdiyle çalıştırılır
    Then hata satırlarında CLI hata döner
    And diğer satırlarda N tam eşleşir ve ondalıklı alanlar 1e-7 içinde eşleşir
```

## 7. Bilinen sapma

N > 10¹⁰ olan vektörlerde (GP-057, GP-058, GP-071; dz ≤ 0.00002) güç eğrisi neredeyse düzdür ve
merkezi olmayan t'nin sayısal hesabındaki çok küçük farklar N'yi ~%0.001 kaydırır. Oturum 1'in
scipy ile yaptığı kontrolde bu üç satır dışında tüm hesaplanabilir GUI vektörleri tam eşleşti
(52/55). Bu üç satır diferansiyel raporda "bilinen sapma" olarak ayrı sayılır; N eşleşmesi beklenmez.

## 8. Diferansiyel test için kaynaklar

- `oracle/gpower_vectors.csv` — G*Power GUI'den 72 vektör (her biri `oracle/screenshots/` altında
  ekran görüntüsüyle), 7 basamak.
- `oracle/statsmodels_vectors.csv` — 577 ölçek vektörü (kesirli N; `n_ceil` sütunu).
  Beklenen fark: G*Power ceil(round(N,10)) kullanır; statsmodels güç ≤ α'da NaN verir, G*Power N = 2 verir.

## AÇIK SORULAR (Oturum 2 — yazım)

Yazım sırasında SPEC'in tanımlamadığı ya da kendi içinde çeliştiği noktalar. Uygulanan geçici karar
parantez içinde; Oturum 1 / CONTRACT.md ile netleştirilmeli.

1. **AÇIK SORU — sayı olmayan α, güç, N, kuyruk.** §3 yalnızca dz için "sayı değilse 0" kuralını veriyor.
   (Geçici: girdi hatası `"<alan> is not a number: ..."`.)
2. **AÇIK SORU — aralık genişletme adımı.** §4.2 "üst sınırı genişlet" diyor, nasıl genişletileceğini
   söylemiyor. (Geçici: f(üst) ≥ 0 olana dek üst sınır ikiye katlanır; alt sınır 2'de kalır. Kök aynı
   olduğu için sonucu etkilemez.) Tolerans 1e-10 mutlak alınmıştır; N ~ 10¹⁰'da bu, kayan nokta
   aralığının altında kaldığından fiilen göreli kayan nokta sınırı (scipy `brentq` rtol) geçerlidir.
3. **AÇIK SORU — §5 ile §6 "Kâhin vektörleri" çelişkisi.** §5 CLI'ın 4 basamak basmasını, §6 ise
   "CLI aynı girdiyle çalıştırılır … ondalıklı alanlar 1e-7 içinde eşleşir" diyor; 4 basamaklı çıktı
   1e-7'yi sağlayamaz. (Geçici: 1e-7 karşılaştırması CLI'ın biçimlendirdiği motor sonucu üzerinde,
   CLI çıktısı ise 4 basamakta test edilir. Bir `--precision` bayrağı eklenmedi.)
4. **AÇIK SORU — §6 senaryo ile §7 bilinen sapma çelişkisi.** "A priori N int sınırını aşabilir"
   senaryosu N = 19622220504 bekliyor; §7 aynı satır (GP-057) için N eşleşmesi beklenmediğini söylüyor
   (dz 0.00001 / GP-071 için de aynı). (Geçici: test "hata yok + göreli fark < 1e-4" ister; tam N
   `xfail`.)
5. **AÇIK SORU — hata metinleri.** SPEC yalnızca "Power must be greater than or equal to alpha" metnini
   veriyor. (Geçici: diğer metinler `oracle/gpower_vectors.csv` `error` sütunundan, `[Input error] `
   öneki atılarak alındı.)
6. **AÇIK SORU — kullanım hataları ve çıkış kodları.** Eksik bayrak, `--dz` ile `--d`'nin birlikte
   verilmesi, `--test` ≠ `t-paired`, desteklenmeyen mod için metin/kod tanımlı değil. (Geçici: hepsi
   tek satır `{"error": ...}`; argüman hatası çıkış kodu 2, girdi doğrulama hatası 1.)
7. **AÇIK SORU — `--tails` 1/2 dışı.** §3'te kural yok, CLI sözleşmesi `{1|2}` diyor. (Geçici: hata
   `"tails must be 1 or 2"`.)
