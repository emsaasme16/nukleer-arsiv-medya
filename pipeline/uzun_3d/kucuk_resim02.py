#!/usr/bin/env python3
"""Bolum 2 kucuk resimleri (1280x720 PNG, < 2 MB): gercekci 3D sahneden, en cok 4 kelime.
Kullanim: WORK=/tmp/b2 python3 kucuk_resim02.py <cikti_klasoru>"""
import sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import bolum02 as b
from common3d import F_XB

b.label = lambda *a, **k: None          # sahne yazilari olmadan
b.cardl = lambda *a, **k: None


def big(img, lines, x, y, size, cols):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(zip(lines, cols)):
        f = ImageFont.truetype(F_XB, size)
        d.text((x, y + i * size * 1.05), t, font=f, fill=c, stroke_width=10, stroke_fill=(6, 12, 32))
    return np.array(im)


out = sys.argv[1]
# 1: halter bicimindeki cekirdek (bolunmeden hemen once)
u = b.S4["itme"] - 0.6
img = b.s4_cekirdek(u, u)
img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_AREA)
img = big(img, ["ÇEKİRDEK", "İKİYE BÖLÜNÜYOR"], 50, 470, 92, [(255, 255, 255), (255, 181, 71)])
Image.fromarray(img).save(os.path.join(out, "kucuk-resim-1.png"), optimize=True)
# 2: bolunme ani: Rb-93, Cs-140 ve 3 notron
img = b.s5_parcalar(1.2, 1.2)
img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_AREA)
img = big(img, ["1 NÖTRON,", "200 MeV"], 50, 470, 100, [(255, 255, 255), (255, 181, 71)])
Image.fromarray(img).save(os.path.join(out, "kucuk-resim-2.png"), optimize=True)
