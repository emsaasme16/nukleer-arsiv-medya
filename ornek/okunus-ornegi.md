# Örnek: Türkçe okunuş videosu

Tek seferlik örnek. Hiçbir platforma yüklenmedi.

- Dosya: `ornek/okunus-ornegi.mp4` — 1080x1920, 30 fps, 26,23 sn (ses 25,23 sn + 1 sn), H.264/yuv420p, AAC 192k, faststart
- Ses: ElevenLabs `eleven_v4`, ses Can Seçkin, 1 üretim — 385 kredi. Transkript (eleven_scribe_v1) için 0 kredi harcandı.
- Ses yüksekliği: loudnorm hedefi -14 LUFS; ölçülen değer -14,9 LUFS (sondaki 1 sn sessizlik dahil)
- Kural: ekrandaki yazı ve altyazı normal yazımla kaldı, Türkçe okunuş yalnızca ses metninde var.

## Karşılaştırma

| # | Ekran / altyazı (normal yazım) | Ses metni (ElevenLabs'e giden) | Transkript (scribe) | Zaman (sn) |
|---|---|---|---|---|
| 1 | Doğal uranyumun ne kadarı reaktörde bölünür? | Doğal uranyumun ne kadarı reaktörde bölünür? | Doğal uranyumun ne kadarı reaktörde bölünür? | 0,16–2,67 |
| 2 | ABD Nükleer Düzenleme Kurulu'na (NRC) göre doğal uranyumun %99,3'ü U-238. | A-Be-De Nükleer Düzenleme Kurulu'na göre doğal uranyumun yüzde doksan dokuz virgül üçü uranyum iki yüz otuz sekiz. | A-Be-De Nükleer Düzenleme Kurulu'na göre doğal uranyumun yüzde doksan dokuz virgül üçü uranyum iki yüz otuz sekiz. | 3,84–10,92 |
| 3 | Bölünebilen U-235 ise yalnızca %0,7. | Bölünebilen uranyum iki yüz otuz beş ise yalnızca yüzde sıfır virgül yedi. | Bölünebilen uranyum iki yüz otuz beş ise yalnızca yüzde sıfır virgül yedi. | 11,76–16,36 |
| 4 | Tek bir bölünme ≈ 200 MeV enerji verir. | Tek bir bölünme yaklaşık iki yüz mega elektronvolt enerji verir. | Tek bir bölünme yaklaşık iki yüz mega elektronvolt enerji verir. | 16,84–20,51 |
| 5 | Three Mile Island kazası: 1979. | Ve Tri Mayl Ayland kazası 1979'da yaşandı. | Ve Tri Mayl Ayland kazası 1979'da yaşandı. | 21,28–25,28 |

Ortadaki anahtar yazılar sırasıyla şunlar: `?`, `ABD · NRC / %99,3 U-238`, `U-235 / %0,7`, `≈ 200 MeV`, `Three Mile Island / · 1979 ·`.

## Kontrol sonucu

- **Ekran kuralı: tamam.** Ekranda ABD, NRC, %99,3, %0,7, U-235, U-238, ≈ 200 MeV ve Three Mile Island normal yazımla görünüyor. Ses metni hiçbir yerde ekrana çıkmıyor. Kontrol için 4 kareye bakıldı.
- **Transkript ses metniyle birebir aynı.** "A-Be-De" tirelerle yazılmış, [curious], [pause] ve [warmly] etiketleri de transkriptte geçiyor. Gerçek bir konuşma tanıma bu etiketleri yazmaz. Bu yüzden scribe sesi bağımsız dinlememiş, bilinen metni sese hizalamış görünüyor.
  - **Kesin olan:** kelime zamanları altyazı zamanlaması için güvenilir.
  - **Kanıtlanmayan:** "ABD'nin abede okunması", sayıların Türkçe okunması ve "Tri Mayl Ayland" bu transkriptle doğrulanamaz.
- Bağımsız ikinci kontrol olarak yerelde Whisper denendi. Model indirme adresi (Hugging Face) ağ politikası tarafından engellendiği için çalıştırılamadı.
- **Dikkat — 1979:** ses metninde rakamla "1979'da" yazıyor. Kurala göre bu "bin dokuz yüz yetmiş dokuzda" diye yazılmalıydı. Modelin bunu Türkçe okuyup okumadığını kulakla kontrol edin. Hizalamaya göre bu kelime 1,28 sn sürüyor, bu da uzun bir Türkçe okunuşla uyumlu, ama kesin kanıt değil. Talimat gereği yeniden üretilmedi.
- **Öneri:** okunuşu kesin doğrulamak için videoyu bir kez kulakla dinleyin. İleride ses metnindeki yılları da yazıyla yazın.
