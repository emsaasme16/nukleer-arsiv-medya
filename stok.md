# Video stoku (yayına hazır)

Her video depoda hazır; herkese açık adres `https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/<dosya>.mp4`.
Yayınlanınca satırı `yayin-kaydi.md`'ye taşı. YouTube'da her video için: çocuklara özel değil, ücretli tanıtım yok, herkese açık, kategori Eğitim; "değiştirilmiş içerik" sorusu: **Evet**.

Etiketler (hepsi için): `#NükleerArşiv #nükleer #atom #fizik #bilim #shorts`

---

## 3. bir-fisyon-ne-kadar-surer.mp4 (50,33 sn)

**YouTube başlığı:** Bir fisyon ne kadar sürer? #Shorts

**YouTube açıklaması:**
60 saniyede: Bir uranyum çekirdeğinin bölünmesi yaklaşık saniyenin on trilyonda biri (≈ 10⁻¹³ s) sürer. ABD Enerji Bakanlığı'nın el kitabına göre su ile yavaşlatılan reaktörlerde termal nötronlar yakalanmadan önce yaklaşık 10⁻⁴ saniye (saniyenin on binde biri) dolaşır; nötron bölünebilir bir çekirdekçe yakalandıktan sonra fisyon ve yeni hızlı nötronların çıkışı yaklaşık 10⁻¹³ saniyede olur. Uranyum-235'in termal nötronla bir fisyonu ortalama 200 MeV enerji verir; bunun 167 MeV'i parçaların hareket enerjisidir. Parçalar çevredeki atomlardan elektron koparırken bu enerjiyi yakıta aktarır ve yakıt ısınır. Seslendirme yapay ses ile yapılmıştır.

Kaynaklar:
- ABD Enerji Bakanlığı (DOE), "DOE Fundamentals Handbook: Nuclear Physics and Reactor Theory, Volume 1" (DOE-HDBK-1019/1-93): https://www.energy.gov/documents/doe-hdbk-1019-93vol1

Devamı kanalda: Bölüm 2.

#NükleerArşiv #nükleer #atom #fizik #bilim #shorts #keşfet #keşfetbeniöneçıkar #eğitim #trending

**Instagram metni:**
60 saniyede: Bir fisyon ne kadar sürer? Nötron yakalandıktan sonra bölünme yaklaşık 10⁻¹³ saniyede, yani saniyenin on trilyonda birinde olur. 200 MeV'in 167 MeV'i parçaların hareketidir ve yakıtı ısıtır. Kaynak: ABD Enerji Bakanlığı (DOE-HDBK-1019). Bağlantılar YouTube açıklamasında. Seslendirme yapay sestir.
#NükleerArşiv #nükleer #bilim #shorts #keşfet #keşfetbeniöneçıkar #reels #eğitim

**Kaynaktan okunan cümleler:**
- DOE-HDBK-1019/1-93: "In water moderated reactors, thermal neutrons tend to exist for about 10-4 seconds before they are absorbed. Fission and fast neutron production following neutron absorption in a fissionable nucleus occurs in about 10-13 seconds."
- DOE-HDBK-1019/1-93: "the average total energy released per fission of uranium-235 with a thermal neutron is 200 MeV."
- DOE-HDBK-1019/1-93, Tablo 6: "Kinetic Energy of Fission Products 167 Mev"
- DOE-HDBK-1019/1-93: "All of the energy released, with the exception of the neutrino energy, is ultimately transformed into heat through a number of processes. The fission fragments, with their high positive charge and kinetic energy, cause ionization directly as they rip orbital electrons from the surrounding atoms. In this ionization process, kinetic energy is transferred to the surrounding atoms of the fuel material, resulting in an increase in temperature."
- Hesap: 10⁻¹³ s = saniyenin on trilyonda biri; 10⁻⁴ s = saniyenin on binde biri. Ekrandaki bölünme ürünleri el kitabının örnek tepkimesidir (U-236 → Rb-93 + Cs-140 + 3 n).

---

## Üretim notu

- Ses: ElevenLabs `eleven_v4`, Cem (`mScWJwY9Ty24PwwvyNcA`), tek take. Flow'lar: NZHOcMGWVNOweRRCQKbI (radyasyon, 46,16 sn, 774 kredi), 0vaC2x7BATDHaeOocCvP (yakıt, 49,60 sn, 887 kredi).
- Kod: `pipeline/short3_stok/` (`render_kalkan.py`, `render_yakit.py`, genelleştirilmiş `sound_mix.py <klasör> <süre> minor|major <cues.json>`).
- Ölçüm: radyasyon -14,2 LUFS / tepe -1,7 dBFS; yakıt -14,0 LUFS / tepe -2,4 dBFS (AAC sonrası `alimiter=limit=0.75` ile).
- ElevenLabs ücretsiz plan: ayda 10.000 karakter. Bu iki videodan sonra kalan ≈ 5.700 karakter (≈ 7 video).
- 2026-11-26 (günlük Shorts görevi): ses ElevenLabs `eleven_v4`, Can Seçkin (`rSuyucEH95GpZEfLV0AM`), perde kaydırma yok, tek take; görüntü `pipeline/stil_3d/dikey_kit.py` (gerçekçi dikey 3D).
  - Uranyum-kömür: flow wEs1F2D14ZuVBwAnOOhW, ses 49,63 sn, video 56,10 sn, 814 kredi, AAC sonrası -14,1 LUFS / tepe -2,3 dBFS. Kalan ElevenLabs karakteri (üç sesten sonra, hesap): 105.046.
  - Kayıp kütle: flow 27tzZyWH2dTntC9twpX0, ses 51,07 sn, video 57,53 sn, 805 kredi, AAC sonrası -14,1 LUFS / tepe -2,4 dBFS. Terazideki eğim temsilîdir; çekirdek C-12 olarak çizildi.
  - Kayıp kütle okunuş düzeltmesi (2026-11-26): "E eşittir m c kare" → "e eşittir em ce kare" (metin `pipeline/stil_3d/metinler/kayip-kutle-nereye-gider.txt`); flow 0C9FLoYEQlT0rDQCoPpP, generation eKPRTi9lGPh2NOPGKi17, ses 50,80 sn, video 57,30 sn, 807 kredi, AAC sonrası -14,2 LUFS / tepe -2,4 dBFS.
  - Uranyumun hepsi bölünür mü: flow CSJTRuJYbU3Ctj3w53YX, ses 49,48 sn, video 55,93 sn, 825 kredi, AAC sonrası -14,1 LUFS / tepe -2,3 dBFS.
  - Bu üç video toplam 2.444 kredi; kalan ElevenLabs karakteri ≈ 105.046 (126.676 limit).
- 2026-11-27 (günlük Shorts görevi): ses ElevenLabs `eleven_v4`, Can Seçkin (`rSuyucEH95GpZEfLV0AM`), perde kaydırma yok, tek take; görüntü `pipeline/stil_3d/dikey_kit.py`. Dinleme kontrolü: mp3 ayrı, yeni bir flow'a dosya olarak yüklendi ve `eleven_scribe_v1` o düğümden çalıştırıldı; transkriptlerde etiket yok, metin normalleştirilmiş ("A-Be-De" → "ABD", "Su ile" → "Suyla"), yani kontrol bağımsız; yanlış okunan kısaltma, sayı, birim ya da yabancı ad yok.
  - Ay bir stadyuma sığar mı: flow VklUlvHaaifgdPjvW32x (generation N6TbWp29sxGJuPOAWlEG), ses 46,11 sn, video 52,57 sn, 780 kredi (+253 dinleme kontrolü, flow k5EiQ0jxJ5ECdw4pjVF6), AAC sonrası -14,1 LUFS / tepe -2,4 dBFS. Metin `pipeline/stil_3d/metinler/ay-bir-stadyuma-sigar-mi.txt`, kod `pipeline/stil_3d/render_ay_stadyum_3d.py`.
  - Çekirdeği neden nötron böler: flow fPrYxnkrtBhpbp3gkcGQ (generation lQeQemeObmTLkQzWAgub), ses 44,75 sn, video 51,20 sn, 729 kredi (+246 dinleme kontrolü, flow ZQv3vc2Fo0ICYxxoF7ZD), AAC sonrası -14,1 LUFS / tepe -2,4 dBFS. Metin `pipeline/stil_3d/metinler/cekirdegi-neden-notron-boler.txt`, kod `pipeline/stil_3d/render_notron_neden_3d.py`.
  - Bir fisyon ne kadar sürer: flow HA1iagpMGeSAHdRcBGTO (generation UAr251DjYM3gnVEX8lBs), ses 43,89 sn, video 50,33 sn, 743 kredi (+241 dinleme kontrolü, flow dYhPvvruGg6QiR48Yd4H), AAC sonrası -14,1 LUFS / tepe -2,5 dBFS. Metin `pipeline/stil_3d/metinler/bir-fisyon-ne-kadar-surer.txt`, kod `pipeline/stil_3d/render_fisyon_sure_3d.py`.
  - Bu üç video: ses 2.252 + dinleme kontrolü 740 = 2.992 kredi; kalan ElevenLabs karakteri ≈ 96.737 (126.676 limit; üretimden önce hesapta kalan 99.729).
