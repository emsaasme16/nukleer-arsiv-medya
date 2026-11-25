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
