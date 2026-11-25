# Yayın kaydı

| Tarih | Başlık | YouTube | Instagram medya kimliği | Kaynaklar | Not |
|---|---|---|---|---|---|
| 2026-11-24 | Çekirdek neden dağılmıyor? | Yayınlandı (2026-11-25, kullanıcı YouTube Studio'dan elle yükledi; bağlantı eklenecek) | 18132193852798937 | ABD DOE, "DOE Explains...The Strong Force" (energy.gov/science/doe-explainsthe-strong-force) | YouTube: Windsor `upload_video` üç denemede de (son deneme kullanıcı isteğiyle, birkaç dakika sonra) "YouTube rate-limited the upload" hatası verdi. Claude in Chrome bağlı değildi, tarayıcı yolu denenmedi. |
| 2026-11-24 | Mit mi, gerçek mi? Muz radyoaktif midir? | Yayınlandı (2026-11-25, kullanıcı YouTube Studio'dan elle yükledi; bağlantı eklenecek) | 18436233994149942 | ABD EPA, "Natural Radioactivity in Food" (epa.gov/radtown/natural-radioactivity-food); ABD NRC, "Doses in Our Daily Lives" (nrc.gov/about-nrc/radiation/around-us/doses-daily-lives.html); ABD EPA, "Radiation Sources and Doses" (epa.gov/radiation/radiation-sources-and-doses) | 1.000 muz = NRC göğüs röntgeni 10 mrem ÷ EPA 0,01 mrem/muz (hesap). |
| 2026-11-25 | Radyasyon neyle durur? Kâğıt, metal, kurşun | https://youtube.com/shorts/2G0pUM72VKI (2026-11-25, 3D sürüm, Claude in Chrome ile YouTube Studio'dan yüklendi; eski cFmZRxZfyQw silindi) | Henüz paylaşılmadı | ABD EPA, "Radiation Basics" (epa.gov/radiation/radiation-basics); ABD NRC, "Radiation Basics" (nrc.gov/about-nrc/radiation/health-effects/radiation-basics.html) | Herkese açık, Eğitim, çocuklara özel değil, ücretli tanıtım yok, yapay zekâ kullanımı: Evet. |
| 2026-11-25 | Kullanılmış nükleer yakıt ne kadar yer kaplar? | https://youtube.com/shorts/vWVQp42kLpo (2026-11-25, 3D sürüm, Claude in Chrome ile YouTube Studio'dan yüklendi; eski REJZtlvW_fA silindi) | Henüz paylaşılmadı | ABD DOE, "5 Fast Facts about Spent Nuclear Fuel" (energy.gov/ne/articles/5-fast-facts-about-spent-nuclear-fuel); ABD DOE, "Nuclear 101: How Does a Nuclear Reactor Work?" (energy.gov/ne/articles/nuclear-101-how-does-nuclear-reactor-work) | Herkese açık, Eğitim, çocuklara özel değil, ücretli tanıtım yok, yapay zekâ kullanımı: Evet. |

Video adresleri (herkese açık, `claude/ecstatic-thompson-hd3p6u` dalı):
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/cekirdek-neden-dagilmiyor.mp4
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/muz-radyoaktif-mi.mp4
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/radyasyon-neyle-durur.mp4
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/kullanilmis-yakit-ne-kadar-yer-kaplar.mp4

## Kaynaktan okunan rakamlar (sayfadan alıntı)

- DOE: "The strong force is about 100 times stronger than electromagnetism." / "it stops working when particles are even a tiny distance apart. How tiny? About 100,000 times smaller than the diameter of an atom." / "In an atomic nucleus, the electromagnetic force should force positively charged protons apart ... The strong force overcomes this effect."
- EPA (gıda): "Consuming one banana would deliver a total dose of 0.01 millirem (0.1 microsieverts) of radiation ... you would need to eat about 100 bananas to receive the same amount of radiation exposure as you get each day in United States from natural radiation in the environment." / "Because the amount of radiation is very small, these foods do not pose a radiation risk."
- NRC: "a chest x-ray typically gives a dose of about 0.01 rem (10 millirem)"; muzda 40K 3.520 pCi/kg; yıllık ortalama 620 mrem, yarısı doğal (310 mrem → günde ≈0,85 mrem, EPA'nın "≈100 muz/gün" ifadesiyle uyumlu).
- HyperPhysics (GSU) ve hps.org açılamadı (DNS / Cloudflare), kullanılmadı.

## YouTube yükleme denemeleri

- 2026-11-24 (2. oturum): Claude in Chrome yine bağlı değildi, kullanıcının bilgisayarı da oturuma bağlı değildi. Kullanıcının isteğiyle Windsor `upload_video` ile denendi: "Çekirdek" videosu 2 kez, "Muz" videosu 1 kez (yaklaşık 3 dakika arayla). Üçü de "YouTube rate-limited the upload" hatası verdi. Windsor `get_data` son 29 günde kanalda video göstermedi, yani denemeler çift video oluşturmamış görünüyor (veri önbellekten okundu). Bir saat sonra otomatik yeniden deneme planlandı.
- 2026-11-25 00:43 UTC: Planlı yeniden deneme. "Çekirdek" yüklemesini kullanıcı onaylamadı (çağrı reddedildi), yüklenmedi. "Muz" videosu kullanıcının isteğiyle 2 kez denendi, ikisi de hız sınırı hatası verdi. Bundan sonraki saatlik denemeler yalnızca "Muz" için yapılacak.
- 2026-11-25: Kullanıcı iki videoyu da YouTube Studio'dan kendisi yükledi. Otomatik yeniden denemeler iptal edildi. Windsor `upload_video` bu kanal için hiç çalışmadı (toplam 10'dan fazla deneme, hepsi hız sınırı); yeni videolarda doğrudan Studio yolu kullanılmalı.
- 2026-11-25: "Radyasyon neyle durur?" ve "Kullanılmış nükleer yakıt ne kadar yer kaplar?" Claude in Chrome ile YouTube Studio'dan yüklendi (README'deki yol: `fetch` + `DataTransfer` ile raw.githubusercontent.com adresinden gizli `input[type=file]`'a verildi). İkisi de ilk denemede yüklendi ve yayınlandı. "Yapay zeka kullanımı" sorusu bu kez tarayıcıdan "Evet" olarak işaretlenebildi.

## Windsor destek talebi

- 2026-11-24: YouTube `upload_video` hız sınırı hatası için Windsor.ai destek talebi açıldı. Referans numarası: **55628234** (canlı sohbet: windsor.ai, e-posta: support@windsor.ai).

## 3D yeniden üretim (2026-11-25)

Beş videonun görüntüsü `pipeline/stil_3d/` ile 3D olarak yeniden üretildi; dosya adları (ve ham adresler) aynı kaldı. Ses akışları orijinal videolardan `-c:a copy` ile alındı, değişmedi (çözülmüş ses MD5'leri eski ve yeni dosyada aynı). Metin, rakam, sahne sırası ve zamanlama aynı. "ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL" alt notu kaldırıldı; son kartta "DEVAMI KANALDA · BÖLÜM 1" yazar.

3D yöntemi: gerçek 3D, moderngl + EGL (başsız, Mesa llvmpipe), mesh tabanlı (küre, yuvarlak kutu, silindir, torus, boru), Blinn-Phong + fresnel kenar ışığı, yumuşak gölge, bloom, hacimsel ışık huzmeleri, paralakslı toz (alan derinliği), hafif gren. 1080×1920, 30 fps, libx264 crf 18.

| Video | Eski boyut | Yeni boyut | Süre |
|---|---|---|---|
| atomun-kutlesi-nerede.mp4 | 12,0 MB | 43,7 MB | 38,20 sn (aynı) |
| cekirdek-neden-dagilmiyor.mp4 | 6,7 MB | 36,4 MB | 36,50 sn (aynı) |
| muz-radyoaktif-mi.mp4 | 7,2 MB | 35,4 MB | 36,50 sn (aynı) |
| radyasyon-neyle-durur.mp4 | 8,5 MB | 48,7 MB | 52,50 sn (aynı) |
| kullanilmis-yakit-ne-kadar-yer-kaplar.mp4 | 8,6 MB | 50,7 MB | 56,00 sn (aynı) |

Önizleme kareleri: `onizleme/`. Bu yeniden üretim hiçbir platforma yüklenmedi.
