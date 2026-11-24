# Short 2 ve 3: "Çekirdek neden dağılmıyor?" ve "Muz radyoaktif mi?"

Şablon `short1_atomun_kutlesi`'den türetildi. Fark: tl3 zaman eşlemesi yok. Ses kesilmeden 0,5 sn kaydırılır,
sahne zamanları doğrudan video saniyesidir (ses + 0,5). Cümle sınırları `silencedetect=n=-38dB:d=0.18` ile bulundu.

Kurulum: `/home/claude/s2/{code,v1,v2}`. Yazı tipleri: Poppins Bold/SemiBold/Medium
(`raw.githubusercontent.com/google/fonts/main/ofl/poppins/`), `/usr/share/fonts/truetype/google-fonts/`.
`pip install scipy opencv-python-headless`.

1. Ses: take'i `vN/raw.wav` olarak koy (44,1 kHz mono).
2. `python3 render_kuvvet.py still 2.5 8.4 ...` ile kare kontrolü, sonra
   `printf "0 9.2\n9.2 18.4\n18.4 27.6\n27.6 36.5\n" | xargs -P 4 -L 1 python3 render_kuvvet.py chunk`
3. `python3 sound_mix.py kuvvet`: pad + efekt + ses zinciri (build4 ile aynı) + iki geçişli loudnorm.
   Sonuç: -14,0 LUFS, tepe -1,5 dBFS, müzik sesin ≈14 dB altında.
4. concat `-c copy` ve `-c:a aac -b:a 192k -movflags +faststart`. AAC tepeyi ~0,1 dB yükseltebilir, gerekirse `-af volume=-0.2dB`.

ElevenLabs: flow R1oNTZxGXmR6t9f6mmr5 (kuvvet, 29,28 sn), flow JvIN6VMK8IfrClS1glOZ (muz, 29,36 sn); eleven_v4, Cem.
