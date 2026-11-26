# Video stoku (yayına hazır)

Her video depoda hazır; herkese açık adres `https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/claude/ecstatic-thompson-hd3p6u/<dosya>.mp4`.
Yayınlanınca satırı `yayin-kaydi.md`'ye taşı. YouTube'da her video için: çocuklara özel değil, ücretli tanıtım yok, herkese açık, kategori Eğitim; "değiştirilmiş içerik" sorusu: **Evet**.

Etiketler (hepsi için): `#NükleerArşiv #nükleer #atom #fizik #bilim #shorts`

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
