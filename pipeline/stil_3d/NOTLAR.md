# 3D görsel dil (pipeline/stil_3d)

Beş Short'un görüntüsü bu klasörle yeniden üretildi (2026-11-25). Ses, metin, rakamlar ve sahne
zamanları eski koddakiyle aynıdır; yalnızca görsel dil değişti. Ekranda alt not yoktur; son kartta
kaynak adları ve `DEVAMI KANALDA · BÖLÜM 1` yazar.

## Dosyalar

- `gl3d.py`: gerçek 3D katman. moderngl + EGL (başsız, Mesa llvmpipe). Küre, yuvarlak kenarlı kutu,
  silindir, simit (torus), koni ve boru (muz) mesh'leri; örnekli (instanced) çizim; Lambert +
  Blinn-Phong, fresnel kenar ışığı, metal, şerit/bant deseni, 4x MSAA. Dünya koordinatı piksel
  uzayıdır (x sağa, y aşağı); kamera düzken z=0 düzlemi ekranla 1:1 örtüşür, böylece eski 2D sahne
  koordinatları doğrudan kullanılır. `Cam(yaw, pitch, dolly, pivot, shift)` yörünge/dolly verir.
- `common3d.py`: ortak modül. `Frame` katman sırası: arka plan (lacivert degrade, vinyet, hacimsel
  ışık huzmeleri, paralakslı toz: uzak/yakın katmanlar bulanık = alan derinliği) → 2D alt katman →
  3D katman + yumuşak gölge → glow + bloom → yazılar (her zaman en üstte, koyu konturlu) → hafif gren.
  `source_card()` son kart, `render_video()` çok süreçli dilimli kodlama + `concat -c copy` + ses.
- `render_atom_3d.py` (atomun-kutlesi-nerede, zaman çizelgesi `../short1_atomun_kutlesi/tl3.py`)
- `render_kuvvet_3d.py` (cekirdek-neden-dagilmiyor), `render_muz_3d.py` (muz-radyoaktif-mi)
- `render_kalkan_3d.py` (radyasyon-neyle-durur), `render_yakit_3d.py` (kullanilmis-yakit-ne-kadar-yer-kaplar)

## Kurulum

```
python3 -m pip install numpy scipy opencv-python-headless moderngl
python3 -m pip install --ignore-installed pillow
apt-get install -y libegl1 libosmesa6 libgl1-mesa-dri
# Poppins (Regular, Medium, SemiBold, Bold, ExtraBold, Light) ~/.fonts altına, sonra fc-cache -f
```

## Çalıştırma

Ses yeniden üretilmez; mevcut videodan alınır:

```
mkdir -p /tmp/ses
ffmpeg -i ../../muz-radyoaktif-mi.mp4 -vn -c:a copy /tmp/ses/muz-radyoaktif-mi.m4a
cd pipeline/stil_3d
WORK=/tmp/r3d/muz python3 render_muz_3d.py still 1.5 10.5 33     # kare kontrolü (PNG)
WORK=/tmp/r3d/muz python3 render_muz_3d.py render                 # tam video
```

`render` 4 süreçte 16 dilim kodlar (libx264, crf 18, yuv420p, preset medium), `concat -c copy` ile
birleştirir, sesi `-c:a copy` ile ekler ve `-movflags +faststart` yazar. Çıktı:
`$WORK/<video-adi>.mp4` (ortam değişkenleri: `WORK`, `AUDIO`, `OUTMP4`, `WORKERS`).
Kare sayıları orijinal videolarla aynıdır (1146, 1095, 1095, 1575, 1680). 4 çekirdekte bir video
yaklaşık 2-4 dakika sürer. EGL açılmazsa `libegl1` / Mesa paketleri eksiktir.

## Gerçekçi dikey 3D Shorts (2026-11-26'dan itibaren)

Kullanıcı kararı: tesis, cihaz ve olaylar gerçekçi sinematik 3D ile; soyut küre yalnızca atom altı ölçekte. Videoda
uyarı/alt not yok ("canlandırma", "şematik", "yapay ses" vb.); yapay ses bilgisi yalnızca platform açıklamasında.

- `dikey_kit.py`: `../uzun_3d/gercekci.py` motorunu (PBR, gölge, SSAO, sis, alan derinliği, bloom) ve
  `../uzun_3d/modeller/` modellerini 1080×1920'ye uyarlar (yüklenirken `gercekci.W, H = 1080, 1920`). Yazılar bu
  klasördeki `common3d.py` (T / pill / blit) ile. Yardımcılar: `path` (Catmull-Rom kamera; anahtarlar çok farklı
  uzaklıktaysa aşar, makro çekimlerde açık yörünge kullan), `shots` (çapraz geçiş), `lines` (üst başlıklar, y 380-620),
  `cardl` (rakam kartı), `stamp` (MİT / GERÇEK damgası), `end_card` (kaynaklar + `DEVAMI KANALDA · BÖLÜM N`),
  `m_rock` (kömür/taş parçası), `render` (24 dilim, 4 süreç, crf 19, `mix.wav` ile AAC 192k).
- Ses: tek mp3 `$WORK/ses/sahne_01.mp3` → `TAIL=5.5 python3 ../uzun_3d/sesler.py $WORK` (doğal zincir, perde kaydırma
  yok, -14 LUFS). Metin zamanları `ffmpeg -af silencedetect=n=-36dB:d=0.16` sınırlarından elle `Z` sözlüğüne yazılır.
- Konu betikleri: `render_uranyum_komur_3d.py` (uranyum-komurun-milyonlarca-kati-enerji-verir-mi),
  `render_kayip_kutle_3d.py` (kayip-kutle-nereye-gider), `render_uranyum_bolunur_3d.py` (uranyumun-hepsi-bolunur-mu).
- Çalıştırma: `WORK=/tmp/s1 python3 render_uranyum_komur_3d.py still 1 9 20` (kare kontrolü), sonra `... render`
  → `$WORK/<ad>.mp4`. 4 çekirdekte bir video ≈ 15-25 dk.

- Zemin/yer düzlemleri mat: speküler düşük, bloom zemine uygulanmaz — kullanıcı 2026-11-27 parlama şikayeti.
  `dikey_kit.ZEMIN_MAT` (koyu ton, pürüzlülük 1.0, metal 0) yer düzlemlerinde varsayılan; açık gri beton döşeme
  kullanma. `shadow_box` yarıçapı zemin döşemesini tamamen kapsamalı, yoksa gölge haritası sınırında keskin
  aydınlık takozlar oluşur (ay-bir-stadyuma-sigar-mi v2: 160 → 300).
