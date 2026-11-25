# Uzun bölüm üretimi (pipeline/uzun_3d) · 16:9, 1920×1080, 30 fps

Bölüm 1 (`bolum-01/bolum-01-atomun-icinde-ne-sakli.mp4`) bu klasörle üretildi (2026-11-25).
Sonraki bölümler için şablon: `bolum01.py` kopyalanıp sahne fonksiyonları değiştirilir; geri kalan her şey ortaktır.

## Dosyalar

- `gl3d.py`, `common3d.py`: `pipeline/stil_3d/` modüllerinin 16:9 kopyası (yalnızca W/H = 1920/1080, kamera
  merkezi ve toz alanı değişti; `T()` ok işaretlerini → ← ↔ DejaVu Sans Bold ile çizer, Poppins'te yok).
  Görsel dil aynı: perspektif kamera, Lambert + Blinn-Phong, fresnel kenar ışığı, bloom, alan derinliği, parçacıklar.
- `render_kit.py`: yeniden kullanılabilir parçalar. Paketlenmiş gerçek nükleon sayılı çekirdekler (`NUC`: N12, C, FE,
  U, RB, CS), atom (elektron bulutu), terazi, yay, Ay, Güneş, cırt cırt, arşiv rafı kartları, açık renkli rakam
  kartı (`card`), rozet, sol üst etiket (`corner_tag`), bitiş kartı (`end_card`: sol yarı dolu, sağ yarı YouTube
  bitiş ekranı için boş), çok süreçli dilimli render (`render_long`).
- `bolum01.py`: 7 sahne. Her sahne `sceneN(t, u, D)`; `u` sahnenin ses başlangıcından itibaren saniye, `D` sesin
  gerçek süresi. Senaryodaki "+0:12" ipuçları plan saniyesidir: `p = u * PLAN[k] / D` ile sese esnetilir.
  Sahne sınırlarında 1,1 sn çapraz geçiş; her sahne hafif kamera dolly'siyle açılır.
- `sesler.py`: ses zinciri + birleştirme + `cues.json` + müzik (D majör pad, seyrek arpej) + geçiş whoosh'ları + miks.
- `altyazi.py`: senaryodaki seslendirme metninden (etiketsiz) SRT; satır ≤ 42 karakter, en çok 2 satır.
- `kucuk_resim.py`: iki küçük resim (1280×720 PNG).

## Kurulum

```
python3 -m pip install numpy scipy opencv-python-headless moderngl fonttools
python3 -m pip install --ignore-installed pillow
apt-get update && apt-get install -y libegl1 libosmesa6 libgl1-mesa-dri    # önce apt-get update şart
# Poppins (Regular, Medium, SemiBold, Bold, ExtraBold, Light) ~/.fonts altına, sonra fc-cache -f
```

## Çalıştırma (Bölüm 1)

```
# 1) Ses: sahne mp3'leri /tmp/bolum1/ses/sahne_01.mp3 ... (ElevenLabs, her sahne ayrı çağrı, tek take)
python3 sesler.py /tmp/bolum1                 # -> cues.json, ses_final.wav, mix.wav (-14 LUFS, tepe -1,5)
# 2) Kare kontrolü
WORK=/tmp/bolum1 python3 bolum01.py still 10 70 200
# 3) Tam render (4 süreç, ~40 dilim, libx264 crf 22, maxrate 1100k; yarım kalan dilimler atlanmaz, bitmişler atlanır)
WORK=/tmp/bolum1 python3 bolum01.py render    # -> /tmp/bolum1/sessiz.mp4
# 4) Birleştir
ffmpeg -i /tmp/bolum1/sessiz.mp4 -i /tmp/bolum1/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
       -movflags +faststart bolum-01/bolum-01-atomun-icinde-ne-sakli.mp4
# 5) Ek dosyalar
python3 altyazi.py ../../bolum-01/senaryo.md /tmp/bolum1/cues.json ../../bolum-01/altyazi-tr.srt
python3 kucuk_resim.py ../../bolum-01
```

## Ses ayarları

- Ses: Can Seçkin (voice_id `rSuyucEH95GpZEfLV0AM`), `eleven_v4`, perde kaydırma YOK.
- Zincir: `highpass=70`, `equalizer=3000 Hz +1,5 dB`, hafif `deesser`, `acompressor` oran 2:1, yankı yok.
- Sahneler arası 0,8 sn sessizlik, başta 1,0 sn, sonda 6 sn (bitiş kartı).
- Müzik sese göre 14 dB altta (sidechain; `sesler.py` farkı ölçüp müzik kazancını ayarlar).
- Final: iki geçişli `loudnorm` (-14 LUFS, linear) + `alimiter level=false`; AAC sonrası ölçüm: -14 LUFS, tepe ≤ -1,5 dBFS.

## Kurallar (yeni bölüm için)

- Ekranda yalnızca senaryonun "Ekran yazısı" metinleri ve rakam/etiketler; tam altyazı yakılmaz; alt kenarda yazı yok.
- Sol üstte küçük `NÜKLEER ARŞİV · BÖLÜM N`. "ANİMASYON · ŞEMATİK" notu yok.
- Son 15-20 sn: kaynaklar (kurum adları) + "BÖLÜM N+1: ... · YAKINDA"; sağ yarı boş.
- Dosya GitHub için < 95 MB: 10 dakikada crf 22 + maxrate 1100k yeterli; büyükse maxrate'i düşür.
- Grafikte eksen sayıları yok; yalnızca senaryodaki değerler etiketlenir (eğri şekli şematik, işaretli noktalar
  senaryodaki değerlerdir).
