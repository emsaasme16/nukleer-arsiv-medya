# Nükleer Arşiv: üretim notları

Bu depo iki iş yapar: (1) yayınlanacak videoları ve marka görsellerini herkese açık bir adreste tutar, böylece Instagram ve tarayıcı üzerinden YouTube yüklemesi bu adresten video alabilir; (2) yeni bir oturumun işi sıfırdan öğrenmeden sürdürebilmesi için üretim kodunu ve çalışma kurallarını saklar.

Kanal: **Nükleer Arşiv** (YouTube + Instagram `nukleer.arsiv`). Anlatım nesnel, kaynaklı, jargonsuz. Her sayı için kaynak sayfası açılıp okunur. Kaynak yoksa yayın yok.

Plan belgesi (Claude Docs): "Sezon 1: Atomdan Santrale – Nükleer Mühendislik İçerik Planı". Bölüm listesi, Shorts formatları, kaynak protokolü ve ses profili orada.

## Klasörler

- `atomun-kutlesi-nerede.mp4`: yayınlanmış ilk Short (herkese açık adres).
- `brand/`: profil resmi, banner ve video filigranı.
- `pipeline/short1_atomun_kutlesi/`: ilk Short'u üreten kod.
- `pipeline/short2_cekirdek_ve_muz/`: 2. ve 3. Short'lar. Ortak yardımcılar `common.py`, ses/müzik/miks tek betikte (`sound_mix.py`). Yeni Short'lar için şablon olarak bunu kullan (`NOTLAR.md`).
- `yayin-kaydi.md`: yayın kaydı.

## Yeni oturumda kurulum

1. `git clone https://github.com/emsaasme16/nukleer-arsiv-medya` (bu depo bağlı olmalı).
2. Çalışma klasörlerini aç: `mkdir -p /home/claude/short1/{code,out,voice}`.
3. Kodu kopyala: `cp pipeline/short1_atomun_kutlesi/* /home/claude/short1/code/`.
4. Yazı tipi: Poppins sistemde kurulu olmalı (`fc-list | grep -i poppins`). Kod `render3.py` içinde font yollarını arar.
5. Kullanılan araçlar: Python (numpy, scipy, cv2, PIL), ffmpeg (libx264, rubberband, sidechaincompress, loudnorm).

## Ağ ortamı

Cloud ortamı `nukleer-arsiv-medya` bu depo için kayıtlı. İzinli alan adları: elevenlabsusercontent.com, www.energy.gov, www.epa.gov, www.nrc.gov, hps.org (Cloudflare engelliyor), hyperphysics.phy-astr.gsu.edu ve www.physics.isu.edu (DNS çözülmedi), raw.githubusercontent.com (Poppins yazı tipi). Yeni bir kaynak sitesi gerekiyorsa ortamın ağ ayarına eklenmeli. Varsayılan ortamda kaynak sayfaları açılmaz.

## Video üretim akışı (Short, yaklaşık 38 saniye, 1080×1920, 30 fps)

1. **Senaryo ve kaynaklar.** Plan belgesindeki kaynak protokolüne göre rakamlar doğrulanır. Ekranda alt not yok. Son kartta kaynak adları ve DEVAMI KANALDA · BÖLÜM 1 yazar. Görseller pipeline/stil_3d/ ile 3D üretilir.
2. **Ses.** ElevenLabs bağlayıcısı ile `creative_generate_speech`: model `eleven_v4`, ses `mScWJwY9Ty24PwwvyNcA` (Cem), Türkçe, yönerge etiketleri `[curious] [softly] [slowly] [warmly] [pause]`. Sayılar metinde okunuşuna yakın yazılır ("Yüzde 99'undan"). Tek take yeter (`generations_count: 1`), 1 kredi ≈ 1 karakter.
   - Uzun bölümler (2026-11-25'ten itibaren): Can Seçkin, voice_id rSuyucEH95GpZEfLV0AM, perde kaydırma yok.
   - Shorts (2026-11-26'dan itibaren): Can Seçkin, voice_id rSuyucEH95GpZEfLV0AM, perde kaydırma yok; videoda uyarı cümlesi yok, yapay ses bilgisi yalnızca açıklamada.
3. **Ses dosyasını almak.** `creative_get_generations` imzalı bir `elevenlabsusercontent.com` adresi döner. Çalışma ortamının ağ ayarında bu alan adı izinliyse `curl -o take.mp3 "<adres>"` ile inilir. İzinli değilse bu adım çalışmaz ve kullanıcının mp3'ü indirip sohbete yüklemesi gerekir. Her oturumda önce `curl -sI` ile erişimi dene.
4. **Ses işleme.** `build4.py`: perde −1 yarım ton (`rubberband=pitch=0.943874`), 70 Hz yüksek geçiren, 200 Hz +1,5 dB, 3,2 kHz +2 dB, de-esser, hafif sıkıştırma, çok hafif oda yankısı, ses −17 LUFS. Müzik sese göre yaklaşık 14 dB altında (sidechain), final −14 LUFS ve tepe −1,5 dBFS. `alimiter` için `level=false` kullan.
5. **Animasyon.** `render3.py` sahneleri çizer, `tl3.py` sahne sürelerini sesin gerçek süresine uydurur (ses hızlandırılmaz, animasyon sese uydurulur). Parçalar 8 saniyelik dilimlerle iki üç süreçte kodlanır (`run_v5.sh`), `concat` ile `-c copy` birleştirilir. Önce birkaç kareyi çizip bak, tam render'ı bir kez yap.
6. **Müzik ve efektler.** `sound3.py` sentezler (pad, vuruşlar, whoosh). Sahne geçişleriyle `tl3.fwd` üzerinden eşlenir.
7. **Birleştirme.** `ffmpeg -i sessiz.mp4 -i karisim.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart`.

## Yayın akışı

1. Videoyu bu depoya yükle (`git push`, Claude GitHub uygulamasının bu depoya yazma izni var). Herkese açık adres:
   `https://raw.githubusercontent.com/emsaasme16/nukleer-arsiv-medya/main/<dosya>.mp4`
2. **Instagram:** Windsor bağlayıcısı, `instagram` bağlantısı, `create_video_post` (`video_url` = yukarıdaki adres, `caption`). Hesap kimliği `get_connectors` ile alınır.
3. **YouTube:** Windsor `upload_video` üç denemede de "hız sınırı" hatası verdi. Çalışan yol tarayıcıdır: Claude in Chrome ile YouTube Studio'da "Video yükle" penceresini aç, sayfada JavaScript ile `fetch` + `DataTransfer` kullanarak `raw.githubusercontent.com` adresinden dosyayı gizli `input[type=file]`'a ver ve `change` olayını tetikle. Başlık, açıklama, "çocuklara özel değil", "ücretli tanıtım yok" doldurulur ve yayınlanır.
4. YouTube'daki **"yapay zekâ kullanımı"** sorusunu tarayıcı güvenlik katmanı benim yerime işaretlememe izin vermiyor. Bu soru kullanıcıya bırakılır.

## Başlık, açıklama ve etiket kalıbı

- Başlık: kısa soru + `#Shorts` (YouTube).
- Açıklama: tek paragraf özet, "Animasyon şematiktir, ölçekli değildir. Seslendirme yapay ses ile yapılmıştır.", kaynak listesi bağlantılarıyla, "Devamı kanalda: Bölüm N."
- Etiketler: `#NükleerArşiv #nükleer #atom #fizik #bilim #shorts`.
- Instagram'da bağlantı tıklanmaz, kaynaklar adıyla yazılır ve "Bağlantılar YouTube açıklamasında" notu eklenir.

## Bilinen sınırlar

- Windsor hesabı deneme sürümünde olabilir, yükleme ve veri sınırları değişebilir.
- Claude ayar sayfaları (Settings, Capabilities) tarayıcıdan açılamaz, ağ ve ortam ayarları kullanıcı tarafından yapılır.
- API anahtarı ve parola gibi gizli bilgiler hiçbir forma girilmez.
- İlk Short'ta rakam kaynakları: proton/elektron kütle oranı 1836,152 673 426(32) (NIST CODATA 2022); kütlenin %99'undan fazlası çekirdekte ve bezelye-stadyum ölçeği (Windows to the Universe, UCAR).
