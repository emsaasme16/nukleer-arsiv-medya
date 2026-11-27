"""Kelime kelime yakılmış altyazı (dikey Shorts, 1080x1920) — 2026-11-27.

Zamanlama bağımsız transkriptin (ElevenLabs eleven_scribe_v1, ayrı flow'a yüklenen mp3) kelime zamanlarından gelir.
Altyazı NORMAL yazımla çizilir (ABD, U-235, %0,7, 16 km); ses metnindeki Türkçe okunuş ekrana çıkmaz. Sesteki
"on altı kilometre" gibi kelime dizileri `DEGISTIR` ile tek bir ekran kelimesine ("16 km") birleştirilir.

Yerleşim: alttan ~%28 yükseklikte (y merkezi ≈ 1380), sağda ~140 px boşluk (Shorts düğmeleri), 1-3 kelimelik
gruplar, Poppins ExtraBold 72 px beyaz + ince koyu kontur + yarı saydam koyu şerit. Her cümlenin en önemli
kelimesi camgöbeği #3fd0ff ya da amber #ffb547 kutuda (koyu yazı).

Kullanım:
    from altyazi_kelime import Altyazi
    AY = Altyazi("words.json", ofset=1.0, vurgu=["bulut", "duman", ...], degistir={("on","altı","kilometre"): "16 km"})
    AY.ciz(img, t)              # her karede, en son (yazılar en üstte)
    AY.kutular(t)               # o anki yazı kutularının dikdörtgenleri (parlama ölçümünde dışarıda bırakmak için)

`vurgu`: cümle başına bir kelime (küçük harf, noktalamasız; cümle sırasıyla). Boş dize ("") o cümlede vurgu yok.
Renk sırayla camgöbeği / amber değişir; `renkler` ile verilebilir.
"""
import json
import re
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

CAMGOBEGI = (63, 208, 255)      # #3fd0ff
AMBER_K = (255, 181, 71)        # #ffb547
KOYU = (8, 16, 38)
W, H = 1080, 1920
SAG_BOSLUK = 140
SOL_BOSLUK = 60
ORTA_X = (SOL_BOSLUK + (W - SAG_BOSLUK)) // 2      # 500
Y_MERKEZ = int(H * (1 - 0.28))                      # 1382 (alttan %28)
MAKS_GEN = W - SAG_BOSLUK - SOL_BOSLUK - 40        # 840 px

import os
_FD = os.path.expanduser("~/.fonts")
F_XB = os.path.join(_FD, "Poppins-ExtraBold.ttf")
_TR_LOWER = str.maketrans("IİÇĞÖŞÜ", "ıiçğöşü")


def _norm(w):
    w = w.translate(_TR_LOWER).lower()
    return re.sub(r"[^\wçğıöşü']", "", w).split("'")[0]


class Altyazi:
    def __init__(self, words_json, ofset=0.0, vurgu=(), degistir=None, renkler=None, boyut=72, maks_kelime=3,
                 maks_kar=16, bosluk_esik=0.28, y=Y_MERKEZ, son=None):
        d = json.load(open(words_json, encoding="utf-8"))
        ws = [w for w in (d["words"] if isinstance(d, dict) else d) if w.get("type", "word") == "word"]
        ws = [dict(text=w["text"], s=w["start"] + ofset, e=w["end"] + ofset) for w in ws]
        ws = self._birlestir(ws, degistir or {})
        self.boyut, self.y = boyut, y
        self.font = ImageFont.truetype(F_XB, boyut)
        # cümlelere böl, vurgu ata
        cumleler, cur = [], []
        for w in ws:
            cur.append(w)
            if re.search(r"[.!?]$", w["text"]):
                cumleler.append(cur)
                cur = []
        if cur:
            cumleler.append(cur)
        renkler = renkler or [CAMGOBEGI, AMBER_K]
        ci = 0
        for i, c in enumerate(cumleler):
            hedef = vurgu[i] if i < len(vurgu) else ""
            for w in c:
                w["vurgu"] = None
            if hedef:
                for w in c:
                    if _norm(w["text"]) == _norm(hedef) or w["text"].rstrip(".,;:!?") == hedef:
                        w["vurgu"] = renkler[ci % len(renkler)]
                        ci += 1
                        break
                else:
                    raise ValueError("vurgu bulunamadı: cümle %d '%s'" % (i, hedef))
        self.cumleler = cumleler
        # gruplar: 1-3 kelime, cümle sonunda / virgülde / uzun duraklamada kır
        self.gruplar = []
        for c in cumleler:
            g = []
            for k, w in enumerate(c):
                if g:
                    onc = g[-1]
                    metin = " ".join(x["text"] for x in g + [w])
                    if (len(g) >= maks_kelime or len(metin) > maks_kar or w["s"] - onc["e"] > bosluk_esik
                            or re.search(r"[,;:]$", onc["text"])):
                        self.gruplar.append(g)
                        g = []
                g.append(w)
            if g:
                self.gruplar.append(g)
        for i, g in enumerate(self.gruplar):
            bas = g[0]["s"] - 0.06
            nxt = self.gruplar[i + 1][0]["s"] - 0.06 if i + 1 < len(self.gruplar) else g[-1]["e"] + 0.5
            bit = min(nxt, g[-1]["e"] + 0.6)
            self.gruplar[i] = dict(kel=g, bas=bas, bit=bit)
        self.son = son
        self._cache = {}

    @staticmethod
    def _birlestir(ws, degistir):
        out, i = [], 0
        anahtarlar = sorted(degistir.items(), key=lambda kv: -len(kv[0]))
        while i < len(ws):
            for seq, rep in anahtarlar:
                n = len(seq)
                if i + n <= len(ws) and all(_norm(ws[i + k]["text"]) == _norm(seq[k]) for k in range(n)):
                    son = ws[i + n - 1]["text"]
                    m = re.search(r"[.,;:!?]+$", son)
                    out.append(dict(text=rep + (m.group(0) if m else ""), s=ws[i]["s"], e=ws[i + n - 1]["e"]))
                    i += n
                    break
            else:
                out.append(ws[i])
                i += 1
        return out

    # ------------------------------------------------------------------ çizim
    def _sprite(self, txt, renk, kutu):
        key = (txt, renk, kutu)
        if key in self._cache:
            return self._cache[key]
        f = self.font
        bb = f.getbbox(txt)
        tw, th = bb[2] - bb[0], self.boyut
        px, py = (18, 10) if kutu else (6, 6)
        w, h = int(tw + 2 * px + 12), int(th * 1.18 + 2 * py + 12)
        S = 2
        im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if kutu:
            d.rounded_rectangle((6 * S, 6 * S, (w - 6) * S, (h - 6) * S), radius=16 * S, fill=tuple(kutu) + (255,))
        fs = ImageFont.truetype(F_XB, self.boyut * S)
        bbs = fs.getbbox(txt)
        x = (w * S - (bbs[2] - bbs[0])) / 2 - bbs[0]
        y = (h * S - fs.getbbox("Hg")[3]) / 2 + S * 2
        if not kutu:
            d.text((x, y), txt, font=fs, fill=tuple(renk) + (255,), stroke_width=4 * S, stroke_fill=KOYU + (230,))
        else:
            d.text((x, y), txt, font=fs, fill=tuple(renk) + (255,))
        im = im.resize((w, h), Image.LANCZOS)
        arr = np.array(im).astype(np.float32)
        a = arr[..., 3] / 255.0
        spr = ((arr[..., :3] * a[..., None]).astype(np.float32), a.astype(np.float32))
        self._cache[key] = spr
        return spr

    def _aktif(self, t):
        if self.son is not None and t >= self.son:
            return None
        for g in self.gruplar:
            if g["bas"] <= t < g["bit"]:
                return g
        return None

    def _yerlesim(self, g):
        spr = []
        for w in g["kel"]:
            kutu = w["vurgu"]
            spr.append(self._sprite(w["text"], KOYU if kutu else (255, 255, 255), kutu))
        gap = 14
        tot = sum(s[1].shape[1] for s in spr) + gap * (len(spr) - 1)
        scale = min(1.0, MAKS_GEN / max(tot, 1))
        x = ORTA_X - tot * scale / 2
        pos = []
        for s in spr:
            wpx = s[1].shape[1] * scale
            pos.append((x + wpx / 2, wpx, s[1].shape[0] * scale))
            x += wpx + gap * scale
        return spr, pos, tot * scale, scale

    def kutular(self, t):
        g = self._aktif(t)
        if g is None:
            return []
        _, pos, tot, sc = self._yerlesim(g)
        hh = max(p[2] for p in pos)
        return [(int(ORTA_X - tot / 2 - 30), int(self.y - hh / 2 - 14), int(ORTA_X + tot / 2 + 30), int(self.y + hh / 2 + 14))]

    def ciz(self, img, t):
        g = self._aktif(t)
        if g is None:
            return img
        a_g = min(1.0, (t - g["bas"]) / 0.08, (g["bit"] - t) / 0.08)
        spr, pos, tot, sc = self._yerlesim(g)
        # yarı saydam koyu şerit
        hh = max(p[2] for p in pos)
        x0, x1 = int(ORTA_X - tot / 2 - 26), int(ORTA_X + tot / 2 + 26)
        y0, y1 = int(self.y - hh / 2 - 8), int(self.y + hh / 2 + 8)
        reg = img[y0:y1, x0:x1].astype(np.float32)
        mask = np.zeros(reg.shape[:2], np.float32)
        cv2.rectangle(mask, (0, 0), (x1 - x0 - 1, y1 - y0 - 1), 1.0, -1)
        k = 0.45 * a_g
        img[y0:y1, x0:x1] = np.clip(reg * (1 - k * mask[..., None]) + np.array(KOYU, np.float32) * k * mask[..., None],
                                    0, 255).astype(np.uint8)
        for w, s, (cx, wpx, hpx) in zip(g["kel"], spr, pos):
            soylendi = t >= w["s"] - 0.03
            op = a_g * (1.0 if soylendi else 0.42)
            if w["vurgu"] and not soylendi:
                s = self._sprite(w["text"], (255, 255, 255), None)
            pop = 1.0
            if soylendi and t < w["s"] + 0.14:
                pop = 1.0 + 0.10 * (1 - (t - w["s"] + 0.03) / 0.17)
            _blit(img, s, cx, self.y, op, sc * pop)
        return img


def _blit(img, spr, cx, cy, op=1.0, scale=1.0):
    rgb, a = spr
    if abs(scale - 1.0) > 1e-3:
        nw, nh = max(1, int(rgb.shape[1] * scale)), max(1, int(rgb.shape[0] * scale))
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
        a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_LINEAR)
    h, w = a.shape
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(w, img.shape[1] - x0), min(h, img.shape[0] - y0)
    if ex <= sx0 or ey <= sy0:
        return
    reg = img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32)
    aa = (a[sy0:ey, sx0:ex] * op)[..., None]
    img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = np.clip(reg * (1 - aa) + rgb[sy0:ey, sx0:ex] * op, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    A = Altyazi(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.0)
    for g in A.gruplar:
        print("%6.2f-%6.2f  %s" % (g["bas"], g["bit"], " ".join(w["text"] for w in g["kel"])))
