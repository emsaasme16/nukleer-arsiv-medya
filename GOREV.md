# Görev: Nükleer Arşiv için video üret ve yayınla

Önce `README.md` dosyasını oku (kurulum, ses, işleme, yayın adımları orada). Bu dosya görevin kendisini ve kuralları anlatır.

## Kimlik ve kurallar

- Kanal: **Nükleer Arşiv** (YouTube + Instagram `nukleer.arsiv`). Kitle: meraklı genel izleyici. Anlatım **nesnel**: yorum, övgü, korkutma yok.
- **Kaynak kuralı:** Videoya giren her sayı ve iddia için kurumsal ya da hakemli bir kaynak sayfası (IAEA, OECD-NEA, UNSCEAR, ABD NRC ve DOE, EPA, üniversite ders kitapları) açılıp okunmalı. Arama özeti kaynak sayılmaz. Sektör kuruluşlarının (WNA gibi) rakamı bağımsız bir kamu kaynağıyla doğrulanmalı. Doğrulanamayan bilgi videoya girmez. "Hafızadan" bilgi yayına girmez.
- Ekranda "ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL" notu, son kartta kaynak adları, açıklamada kaynak bağlantıları olur. Seslendirmenin yapay ses olduğu açıklamaya yazılır.
- Ton ve ses profili: README'deki ses bölümü. Her videoda aynı ses (Cem, eleven_v4) ve aynı işleme zinciri.
- Görsel dil: koyu lacivert zemin, camgöbeği ve amber vurgu, büyük kalın altyazı, üst ve alt kenarda yazı yok, 1080×1920, 30 fps, 35-45 saniye.

## Yapılmayacaklar

- Hesap ayarı değiştirme, ödeme, şifre ya da API anahtarı girme.
- YouTube'daki "yapay zekâ kullanımı" sorusunu işaretleme (güvenlik katmanı izin vermiyor, kullanıcıya bırakılır).
- Kaynağı doğrulanamayan videoyu yayınlama. Takılırsan nedenini `yayin-kaydi.md` içine yaz ve dur.
- Aynı üretim çağrısını tekrar etme (kredi harcar). Bir ses take'i yeter (`generations_count: 1`).

## İlk görev: iki video

1. **Çekirdek neden dağılmıyor?** (Bölüm 1, Short 1). Hazır taslak aşağıda. Güçlü nükleer kuvvetin kısa menzili ve protonların itişmesi için bir kaynak sayfası aç ve oku (ör. kurumsal bir fizik sayfası). Taslaktaki "cırt cırtlı bant" benzetmesi benzetme olarak kalır, kuvvetin gerçek özelliği olarak sunulmaz.
2. **Mit mi, gerçek mi? Muz radyoaktif midir?** Kaynakları kendin bul (ör. ABD EPA, NRC, IAEA ya da bir üniversite radyasyon güvenliği sayfası). Muzdaki potasyum-40 ve doz karşılaştırması için rakamları sayfadan oku. İki bağımsız kaynakla doğrula.

Her video için: kaynak listesi, senaryo (45-60 saniye okunacak kadar kısa), ElevenLabs takesi, animasyon (`pipeline/short1_atomun_kutlesi/` şablon), ses ve müzik miksajı, birkaç karenin kontrolü, ses seviyesi ölçümü (final -14 LUFS, tepe -1,5 dBFS), videoyu depoya yükleme, Instagram ve YouTube yayını (README'deki akış).

### Short 1 taslağı (seslendirme)

Çekirdekte protonlar var ve hepsi artı yüklü. Aynı yükler birbirini iter, yani çekirdek anında dağılmalı. Ama dağılmıyor. Neden? Çünkü doğada güçlü nükleer kuvvet diye bir kuvvet var. Çok şiddetli, ama menzili çok kısa: yalnızca çekirdek boyutunda etkili. Cırt cırtlı bant gibi düşün: yakınken sıkı tutar, uzaktayken hiçbir şey yapmaz. Çekirdeği bir arada tutan şey işte bu.

Görsel: iki proton, kırmızı itme okları, sonra mavi bağlar. Yazı: "İter mi? Evet. Dağılır mı? Hayır."

## Yayın kaydı

Yayınlanan her video için `yayin-kaydi.md` dosyasına bir satır ekle: tarih, başlık, YouTube bağlantısı, Instagram medya kimliği, kullanılan kaynaklar. Yayın başarısızsa nedenini de yaz.

## Günlük düzen (hedef)

Günde 2 video. Haftalık toplu üretim, YouTube'da `upload_video` için `publish_at` (özel yükle, zamanla), Instagram'da yayın gününde. YouTube Windsor yüklemesi üç denemede hız sınırına takıldı, ilk çağrıda tekrar dene. Çalışmazsa tarayıcı yolu (README) yalnızca kullanıcının Chrome'u bağlıysa kullanılır.
