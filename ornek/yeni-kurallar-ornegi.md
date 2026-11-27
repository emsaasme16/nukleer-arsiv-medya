# Örnek: yeni kurallarla Short — "Soğutma kulesinden çıkan duman mı?"

Tek seferlik örnek (2026-11-27). Hiçbir platforma yüklenmedi; `stok.md` ve `yayin-kaydi.md` değişmedi.

- Video: `sogutma-kulesi-duman-mi.mp4` (stoğa taşındı) — 1080x1920, 30 fps, 52,50 sn, düzeltme sonrası (ilk sürüm 52,97 sn; seslendirme 46,48 sn + 1,0 sn baş + 5,5 sn son kart), H.264 yuv420p, AAC 192k, faststart
- Kontak sayfası: `ornek/yeni-kurallar-kareler.jpg`
- Kod: `pipeline/stil_3d/render_sogutma_kulesi_3d.py` (sahneler), `pipeline/stil_3d/altyazi_kelime.py` (yeniden kullanılabilir kelime kelime altyazı)
- Ses metni: `pipeline/stil_3d/metinler/sogutma-kulesi-duman-mi.txt`; kelime zamanları: `pipeline/stil_3d/metinler/sogutma-kulesi-duman-mi.words.json`

## Konu ve kaynaklar

Konu `yayin-kaydi.md` ve `stok.md`'de yok. Her iddia aşağıdaki sayfalar açılıp okunarak yazıldı:

1. **ABD Enerji Bakanlığı (DOE), "The Harnessed Atom" (DOE/NE-0143), Ders 6 Atoms to Electricity** — https://www.energy.gov/sites/prod/files/2014/06/f16/Student%20Edition_2.pdf
   - "What looks like smoke coming from the top of the cooling tower is really vapor from lake water. This water has never been near the reactor. It is not radioactive."
   - Kondenser: "The water does not mix. Only the heat is transferred." (birinci, ikinci, üçüncü döngü)
   - "warm lake water from the third loop is sprayed in the air and trickles down … Some of the water evaporates. The warm, moist air rises inside the tower."
   - "Heat and moisture leave the top of the tower at about 16 km per hour (10 miles per hour) into the atmosphere."
   - "At 200 meters (656 feet) high, a cooling tower is usually the power plant's tallest structure."
2. **ABD Nükleer Düzenleme Kurulu (NRC), Reactor Concepts Manual, "Nuclear Power for Electrical Generation"** — https://www.nrc.gov/reading-rm/basic-ref/students/for-educators/01.pdf
   - "The "steam" vented from the top of a cooling tower is really lukewarm water vapor. IT IS NOT RADIOACTIVE. As the warm, wet air from inside the cooling tower contacts the cooler, dryer air above the cooling tower, the water vapor which cannot be held by the cooler air forms a visible cloud. … The released cloud of vapor will only be visible until it is dispersed and absorbed by the air."
3. Ek okuma (metne sayı girmedi): NRC sözlük "Cooling tower" — https://www.nrc.gov/reading-rm/basic-ref/glossary/cooling-tower.html

## 1. Açılış cümlesi puanlaması

Ölçütler, her biri 0-2: anlaşılırlık (≤ 12 kelime), merak boşluğu, somutluk, kaynakla doğrulanabilirlik, doğal Türkçe.

| Kalıp | Aday | Kelime | Anl. | Merak | Somut | Kaynak | Türkçe | Toplam |
|---|---|---|---|---|---|---|---|---|
| (i) ters köşe | Nükleer santralin tepesindeki o beyaz bulut, aslında göl suyu. | 9 | 2 | 2 | 2 | 2 | 2 | **10** |
| (b) Mit mi, gerçek mi? | Mit mi, gerçek mi? Soğutma kulesinden radyoaktif duman çıkar. | 9 | 2 | 1 | 1 | 2 | 2 | 8 |
| (h) doğrudan soru | Soğutma kulesinden çıkan şey gerçekten duman mı? | 7 | 2 | 1 | 1 | 2 | 2 | 8 |
| (c) somut nesne/an | Yazın buzlu bardağın terlemesi, soğutma kulesinin sırrını anlatır. | 9 | 1 | 2 | 2 | 1 | 2 | 8 |
| (g) ölçek şoku | 200 metrelik kule, santralin en yüksek yapısı ve duman çıkarmıyor. | 10 | 1 | 1 | 2 | 1 | 1 | 6 |

Notlar: (c)'de DOE buzlu bardağı kondenser için örnek veriyor, kule için değil, bu yüzden kaynak puanı 1. (g)'de iki fikir birden var, kaynak da "usually" diyor ama cümle bunu kesin söylüyor, bu yüzden kaynak puanı 1.

**Seçilen: (i), 10/10.** Seslendirmenin ilk cümlesi bu. İlk karede (t = 0) büyük ekran yazısı olarak da var: "O BEYAZ BULUT, / ASLINDA GÖL SUYU".

## Seslendirme metni (ElevenLabs'e giden, Türkçe okunuşla)

> [curious] Nükleer santralin tepesindeki o beyaz bulut, aslında göl suyu. [pause] Duman gibi görünür. Ama A-Be-De Enerji Bakanlığı'na göre kuleden çıkan şey, gölden alınan suyun buharıdır. Bu su reaktörün yanına hiç gitmez. [pause] Santralde üç ayrı su döngüsü vardır. Sular birbirine karışmaz, yalnızca ısı aktarılır. [pause] Kulenin içinde ılık su aşağı süzülür ve bir kısmı buharlaşır. Nemli sıcak hava yükselir, tepeden saatte yaklaşık on altı kilometre hızla çıkar. [pause] A-Be-De Nükleer Düzenleme Kurulu'na göre bu bulut ılık su buharıdır ve radyoaktif değildir. Soğuk hava bu nemi tutamaz, görünür bir bulut oluşur, sonra havaya karışıp kaybolur. [pause] İki yüz metre yüksekliğiyle bu kule, çoğu zaman santralin en yüksek yapısıdır. Devamı kanalda; takip et, kaçırma.

- **Okunuş taraması** (`grep -nP '\b[A-ZÇĞİÖŞÜ]{2,}\b|[%/=²³°≈×±]|\d[,.]\d|[A-Za-z]-?\d|[qwxQWX]'`, `LC_ALL=C.UTF-8` ile): eşleşme yok (düzeltmeden önce tek eşleşme `[warmly]` etiketindeki "w" idi; etiket 2026-11-27'de kaldırıldı). Metinde rakam, sembol ve kısaltma yok.
  - Not: tarama Türkçe olmayan yerel ayarda çalıştırılırsa her Türkçe harfi yanlışlıkla işaretler. `LC_ALL=C.UTF-8` ile çalıştırın.
- NRC kısaltması seste hiç geçmiyor, yalnızca "Nükleer Düzenleme Kurulu" deniyor (CLAUDE.md kuralı). Ekranda "(NRC)" normal yazımla yer alıyor.

## Dinleme kontrolü (bağımsız transkript)

mp3, ayrı bir flow'a (`xI9vsrrsTJYI24bSwgng`) dosya olarak yüklendi. Transkript `eleven_scribe_v1` ile o düğümden alındı.

> Nükleer santralin tepesindeki o beyaz bulut aslında göl suyu. Duman gibi görünür ama ABD Enerji Bakanlığı'na göre kuleden çıkan şey gölden alınan suyun buharıdır. Bu su reaktörün yanına hiç gitmez. Santralde üç ayrı su döngüsü vardır. Sular birbirine karışmaz, yalnızca ısı aktarılır. Kulenin içinde ılık su aşağı süzülür ve bir kısmı buharlaşır. Nemli sıcak hava yükselir. Tepeden saatte yaklaşık on altı kilometre hızla çıkar. ABD Nükleer Düzenleme Kurulu'na göre bu bulut ılık su buharıdır ve radyoaktif değildir. Soğuk hava bu nemi tutamaz. Görünür bir bulut oluşur, sonra havaya karışıp kaybolur. İki yüz metre yüksekliğiyle bu kule çoğu zaman santralin en yüksek yapısıdır. Devamı kanalda. Takip et, kaçırma.

- **Kelime kelime ses metniyle aynı**; yalnızca noktalama farklı.
- Önceki örnekten farklı olarak bu transkript **gerçekten bağımsız** görünüyor: yönerge etiketleri yok ve "A-Be-De" yazımı yerine kulağa göre "ABD" yazılmış. Bu, sesin "A-Be-De" diye okunduğunu doğruluyor.
- Altyazı zamanları bu transkriptin kelime zamanlarından alındı (+1,0 sn baş boşluk).

## 2. Kelime kelime altyazı

- Yardımcı: `pipeline/stil_3d/altyazi_kelime.py` (`Altyazi(words.json, ofset, vurgu, degistir)`).
- Yerleşim:
  - Konum: alttan %28 (y ≈ 1382), sağda 140 px boşluk (metin alanı x 60-940).
  - Kelime grupları: 1-3 kelime. Cümle sonunda, virgülde ve 0,28 sn'den uzun duraklamada yeni grup başlar.
  - Yazı: Poppins ExtraBold 72 px, beyaz, ince koyu kontur, %45 saydam koyu şerit.
- Okunma anı: henüz söylenmemiş kelime %42 saydamlıkta durur. Söylendiği anda tam beyaz olur ve kısa bir büyüme (%10 "pop") yapar.
- Vurgu: her cümlenin en önemli kelimesi sırayla camgöbeği #3fd0ff ve amber #ffb547 kutuda gösterilir. Vurgulanan kelimeler: göl, buharıdır, gitmez, üç, karışmaz, buharlaşır, yükselir, 16 km, radyoaktif, tutamaz, kaybolur, 200 metre, kanalda, takip.
- Normal yazım: sesteki "on altı kilometre" altyazıda "16 km", "iki yüz metre" altyazıda "200 metre" olur. Transkriptteki "ABD" olduğu gibi kalır.
- Ekranda 57 altyazı grubu var.

## 3. Tempo

- **23 kesme, 24 plan.** En uzun plan 3,90 sn (son kart, 44,7-48,6); konulu planların en uzunu 2,94 sn (37,08-40,02, bulutun dağılması). 4 sn'yi aşan durgun sahne yok. Son kartın arka planı da 48,6 ve 51,15 sn'de kesmeyle değişiyor.
- Planlar arası 0,35 sn çapraz geçiş var. Ayrıca her planın içinde kamera sürekli hareket ediyor.
- Planlar sırayla:
  1. Açılış (2 plan)
  2. Dumanın alttan görünüşü
  3. Göl (2 plan)
  4. Koruma kabı ve kule
  5. Havadan üç döngü (3 plan, döngüler sırayla çizilir)
  6. Kulenin içi (2 plan)
  7. Kule ağzı ve buhar (3 plan)
  8. NRC bölümü (3 plan; RADYOAKTİF DEĞİL damgası)
  9. Soğuk hava ve bulut (2 plan)
  10. 200 m (2 plan)
  11. Son kart (3 plan)
- Üst bölgedeki başlık ve kartlar da 1,5-3 sn'de bir değişiyor.

## 4. Kapanış

- Seslendirmenin son cümlesi: "Devamı kanalda; takip et, kaçırma."
- Son kart (44,7 sn'den sonra) şunları gösterir:
  - KAYNAKLAR: ABD Enerji Bakanlığı (DOE), The Harnessed Atom · ABD Nükleer Düzenleme Kurulu (NRC), Reactor Concepts Manual
  - Büyük amber "TAKİP ET" düğmesi; 46,08 sn'de, "Takip" kelimesiyle aynı anda büyüyerek gelir ve hafifçe nabız atar
  - En altta "DEVAMI KANALDA · BÖLÜM 2"

## 5. Parlama ölçümleri

Ölçüm `python3 render_sogutma_kulesi_3d.py olc` ile yapıldı: yazısız kareler (yazı kutuları hariç), 0,5 sn arayla 105 kare. Parlaklık Rec.709 lumadır.

| Ölçüt | Sınır | Sonuç |
|---|---|---|
| ≥ 245 piksel oranı | ≤ %2 | **en kötü %0,43** (son kart, 47,0 sn); diğer karelerin hepsi %0,00 |
| 0,5 sn'de ortalama parlaklık sıçraması | ≤ %20 | **en kötü %19,2** (12,0 sn, göl → koruma kabı) |

- **İlk ölçüm kuralı geçmedi.** Beş yerde sıçrama %20'yi aştı:
  - göl → kab: %29,7
  - havadan → kule içi: %36,5
  - kule içi → kule ağzı: %65,7
  - yerden → geniş plan: %22,8
  - son kart kararması: %38,6
- **Yapılan düzeltmeler:**
  - Kule içinin pozlaması artırıldı.
  - Kab, kule ağzı ve yerden planların pozlaması %15-20 kısıldı.
  - Son kart 0,5 sn yerine 2,4 sn'de, %50 koyuluğa kadar doğrusal kararıyor.
- Malzemeler:
  - Göl ve havuz suyu mat (pürüzlülük 0,78, spekülerlik düşük).
  - Zeminde `ZEMIN_MAT` ve çim kullanıldı (pürüzlülük 1,0); açık gri beton döşeme yok.
  - Bloom eşiği 2,5: yalnızca çok parlak küçük ışıklar parlar. Güneş diski kapalı.

## 6. Diğer teknik bilgiler

- Görüntü: gerçekçi 3D (`dikey_kit` / `gercekci.py`, PBR, gölge, SSAO, sis).
  - Kule 200 m yüksekliğinde, X kolonlu hiperbolik bir kule. Dibinde su havuzu var.
  - Sahnede PWR koruma kabı, türbin binası, göl, pompa evi, direkler, çit, insanlar ve araçlar var.
- Videoda uyarı cümlesi yok ("yapay zekâ", "şematik", "canlandırma" geçmiyor).
- Ses: ElevenLabs `eleven_v4`, Can Seçkin (`rSuyucEH95GpZEfLV0AM`), Türkçe, `generations_count` 1, tek üretim.
  - Konuşma flow'u `SbKfV1Ow0j2NpRpNlHoY`, generation `Qzy1qQ2ySSoxeQ6teK6d`.
  - Ses süresi 46,48 sn.
- Ses işleme: `TAIL=5.5 python3 ../uzun_3d/sesler.py` (doğal zincir, perde kaydırma yok; müzik sesten 14,0 dB altta).
  - Ölçüm (AAC sonrası mp4): **-14,1 LUFS, tepe -2,4 dBFS** (hedef -14 LUFS, tepe ≤ -1,5).

## Harcanan kredi

- Üretimden önce kalan: 96.737 karakter (limit 126.676). Senaryo 871 karakter (+300 = 1.171), yeterliydi.
- Ses: 785 kredi.
- Dinleme kontrolü (eleven_scribe_v1): 256 kredi.
- **Toplam: 1.041 kredi.** Hesapta kalan: 95.696 (126.676 limit; kullanılan 30.980) karakter.

## Görüntü değişimi

46,48 sn'lik seslendirme boyunca görüntü **21 kez** kesmeyle değişti. Bütün videoda (52,98 sn) **23 kesme** var. Ortalama plan süresi 2,2 sn.

## Kontrol

- Tam render'dan önce 25 kare açılıp incelendi: ilk kare, her sahne ve son kart. Bulunan hatalar düzeltildi:
  - Kule içi çekimi kulenin dışında kalıyordu.
  - NRC çekiminde kule koruma kabının arkasında kalıyordu.
  - NRC başlığı tek satıra sığmıyordu, iki satıra bölündü.
  - "3. DÖNGÜ" etiketi kartla çakışıyordu.
  - Son kartın son 4,4 sn'si tek plandı, kesme eklendi.
- Render'dan sonra mp4'ten 8 kare (0,0 · 4,2 · 8,9 · 16,6 · 21,5 · 27,6 · 33,7 · 47,0 sn) çıkarılıp incelendi: açılış yazısı ilk karede, altyazı söylenen kelimeyle eşzamanlı, vurgu kutuları, döngü çizimi, damga ve son kart doğru; parlama yok.

## Düzeltme (2026-11-27): kapanış cümlesi aynı tonla

Kullanıcı şikayeti: son cümle "Devamı kanalda; takip et, kaçırma." `[warmly]` etiketi yüzünden videonun geri kalanından farklı tonda okunmuştu.

- **Yöntem A** (yalnız son cümleyi bağlamla yeniden üretip eklemek; flow `0kbExpb7clmsgME1Msus`, 150 + 51 kredi) **reddedildi**: son cümle önceki 3 cümleye göre perde +%20,7, hız −%25,2 (eşik %8 / %12).
- **Yöntem B**: `[warmly]` silindi, tüm metin tek parça yeniden üretildi (`eleven_v4`, Can Seçkin, flow `06xDF6sWrRWOwBKlX9mx`, generation `4VLHdmZtQ1obE4NpFUAQ`, 776 kredi). Ses 46,0 sn, video 52,50 sn.
- Son cümle / önceki 3 cümle: perde 134,5 / 148,4 Hz (−%9,4; ama anlatımın tüm cümle aralığı 132-162 Hz, tüm anlatım ortalamasına göre −%2,4), eklemleme hızı −%7,3 (eski: −%13,4), RMS +1,35 dB (eski +3,20 dB).
- Dinleme kontrolü: ayrı flow `2YFyqrfN90mlvimQ3wel`, `eleven_scribe_v1` (253 kredi); transkript ses metniyle kelime kelime aynı. `words.json` bununla değişti; render zamanları (Z, END0, plan kesmeleri) yeni kelime zamanlarına kaydırıldı. "Takip" 45,74 sn, TAKİP ET düğmesi onunla eşzamanlı.
- Ses -14,1 LUFS / tepe -2,5 dBFS. Parlama: ≥245 oranı en kötü %0,00, sıçrama en kötü %19,9. En uzun plan 3,73 sn.
