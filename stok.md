# Video stoku (yayına hazır)

Her video depoda hazır; herkese açık adres `https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/<dosya>.mp4`.
Yayınlanınca satırı `yayin-kaydi.md`'ye taşı. YouTube'da her video için: çocuklara özel değil, ücretli tanıtım yok, herkese açık, kategori Eğitim; "değiştirilmiş içerik" sorusu: **Evet**.

Etiketler (hepsi için): `#NükleerArşiv #nükleer #atom #fizik #bilim #shorts`

---

## 1. ay-bir-stadyuma-sigar-mi.mp4 (52,57 sn)

**YouTube başlığı:** Ay bir stadyuma sığar mı? #Shorts

**YouTube açıklaması:**
Mit mi, gerçek mi? "Ay, sıkıştırılsa bir stadyuma sığar." Bir düşünce deneyi olarak gerçek. ABD Enerji Bakanlığı'na göre atomun çekirdeği, atom hacminin %0,01'inden çok daha azını kaplar ama atomun kütlesinin %99,9'undan fazlasını taşır. Bütün çekirdekler yaklaşık aynı yoğunluktadır: Ay bu yoğunluğa kadar sıkıştırılsaydı, New York'taki Yankee Stadium'un içine sığardı. Kütlesi aynı kalırdı; yalnızca çekirdekler arasındaki boşluk ortadan kalkardı. Seslendirme yapay ses ile yapılmıştır.

Kaynaklar:
- ABD Enerji Bakanlığı (DOE), Office of Science, "DOE Explains...Nuclei": https://www.energy.gov/science/doe-explainsnuclei

Devamı kanalda: Bölüm 1.

#NükleerArşiv #nükleer #atom #fizik #bilim #shorts #keşfet #keşfetbeniöneçıkar #eğitim #trending

**Instagram metni:**
Mit mi, gerçek mi? Ay sıkıştırılsa bir stadyuma sığar. Düşünce deneyi olarak gerçek: bütün çekirdekler yaklaşık aynı yoğunlukta; Ay bu yoğunluğa sıkıştırılsa Yankee Stadium'a sığardı. Kaynak: ABD Enerji Bakanlığı (DOE Explains...Nuclei). Bağlantılar YouTube açıklamasında. Seslendirme yapay sestir.
#NükleerArşiv #nükleer #bilim #shorts #keşfet #keşfetbeniöneçıkar #reels #eğitim

**Kaynaktan okunan cümleler:**
- DOE Explains...Nuclei: "The nucleus makes up much less than .01% of the volume of the atom, but typically contains more than 99.9% of the mass of the atom."
- DOE Explains...Nuclei: "The nucleus accounts for more than 99.9994% of the total atomic mass, but occupies less than one ten-trillionth of the atomic volume."
- DOE Explains...Nuclei: "All nuclei have approximately the same density. If the Moon was smashed to the same density, it would fit inside Yankee Stadium."
- Ekrandaki çekirdekler (C-12, Fe-56, U-235) gerçek nükleon sayılarıyla çizildi; stadyum genel bir beyzbol stadyumudur (Yankee Stadium'un birebir modeli değildir).

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
