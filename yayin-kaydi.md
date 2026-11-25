# Yayın kaydı

| Tarih | Başlık | YouTube | Instagram medya kimliği | Kaynaklar | Not |
|---|---|---|---|---|---|
| 2026-11-24 | Çekirdek neden dağılmıyor? | **Yayınlanmadı** | 18132193852798937 | ABD DOE, "DOE Explains...The Strong Force" (energy.gov/science/doe-explainsthe-strong-force) | YouTube: Windsor `upload_video` üç denemede de (son deneme kullanıcı isteğiyle, birkaç dakika sonra) "YouTube rate-limited the upload" hatası verdi. Claude in Chrome bağlı değildi, tarayıcı yolu denenmedi. |
| 2026-11-24 | Mit mi, gerçek mi? Muz radyoaktif midir? | **Yayınlanmadı** (deneme yapılmadı, aynı hız sınırı) | 18436233994149942 | ABD EPA, "Natural Radioactivity in Food" (epa.gov/radtown/natural-radioactivity-food); ABD NRC, "Doses in Our Daily Lives" (nrc.gov/about-nrc/radiation/around-us/doses-daily-lives.html); ABD EPA, "Radiation Sources and Doses" (epa.gov/radiation/radiation-sources-and-doses) | 1.000 muz = NRC göğüs röntgeni 10 mrem ÷ EPA 0,01 mrem/muz (hesap). |

Video adresleri (herkese açık, `claude/ecstatic-thompson-hd3p6u` dalı):
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/cekirdek-neden-dagilmiyor.mp4
- https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/muz-radyoaktif-mi.mp4

## Kaynaktan okunan rakamlar (sayfadan alıntı)

- DOE: "The strong force is about 100 times stronger than electromagnetism." / "it stops working when particles are even a tiny distance apart. How tiny? About 100,000 times smaller than the diameter of an atom." / "In an atomic nucleus, the electromagnetic force should force positively charged protons apart ... The strong force overcomes this effect."
- EPA (gıda): "Consuming one banana would deliver a total dose of 0.01 millirem (0.1 microsieverts) of radiation ... you would need to eat about 100 bananas to receive the same amount of radiation exposure as you get each day in United States from natural radiation in the environment." / "Because the amount of radiation is very small, these foods do not pose a radiation risk."
- NRC: "a chest x-ray typically gives a dose of about 0.01 rem (10 millirem)"; muzda 40K 3.520 pCi/kg; yıllık ortalama 620 mrem, yarısı doğal (310 mrem → günde ≈0,85 mrem, EPA'nın "≈100 muz/gün" ifadesiyle uyumlu).
- HyperPhysics (GSU) ve hps.org açılamadı (DNS / Cloudflare), kullanılmadı.

## YouTube yükleme denemeleri

- 2026-11-24 (2. oturum): Claude in Chrome yine bağlı değildi, kullanıcının bilgisayarı da oturuma bağlı değildi. Kullanıcının isteğiyle Windsor `upload_video` ile denendi: "Çekirdek" videosu 2 kez, "Muz" videosu 1 kez (yaklaşık 3 dakika arayla). Üçü de "YouTube rate-limited the upload" hatası verdi. Windsor `get_data` son 29 günde kanalda video göstermedi, yani denemeler çift video oluşturmamış görünüyor (veri önbellekten okundu). Bir saat sonra otomatik yeniden deneme planlandı.
- 2026-11-25 00:43 UTC: Planlı yeniden deneme. "Çekirdek" yüklemesini kullanıcı onaylamadı (çağrı reddedildi), yüklenmedi. "Muz" videosu kullanıcının isteğiyle 2 kez denendi, ikisi de hız sınırı hatası verdi. Bundan sonraki saatlik denemeler yalnızca "Muz" için yapılacak.

## Windsor destek talebi

- 2026-11-24: YouTube `upload_video` hız sınırı hatası için Windsor.ai destek talebi açıldı. Referans numarası: **55628234** (canlı sohbet: windsor.ai, e-posta: support@windsor.ai).
