#!/usr/bin/env python3
"""Bolum 1 kucuk resimleri (1280x720 PNG): senaryodaki iki oneri.
Kullanim: python3 kucuk_resim.py <cikti_klasoru>"""
import sys, math, os
from common3d import *
from render_kit import *


def big_text(img, lines, x, y, size, cols, font=F_XB, stroke=10, gap=1.02, anchor="l"):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for i, (txt, col) in enumerate(zip(lines, cols)):
        f = ImageFont.truetype(font, size)
        w = f.getlength(txt)
        xx = x if anchor == "l" else x - w / 2
        d.text((xx, y + i * size * gap), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=(6, 12, 32))
    return np.array(im)


def thumb1(t=3.0):
    F = Frame(t, Cam(yaw=0.0, pitch=-0.05, dolly=1.0))
    pellet_R = rot_y(0.6) @ rot_x(0.45)
    F.cyl(430, 640, 0, 120, 220, (165, 172, 190), MAT_METAL, alpha=1.0, R=pellet_R)
    F.glow(430, 640, 300, AMBER, 1.1)
    F.glow(430, 640, 190, AMBER, 0.8)
    # komur yigini (sag, ekrani dolduran)
    rng = np.random.default_rng(5)
    for i in range(260):
        while True:
            x, y, z = rng.uniform(-1, 1, 3)
            if x * x + y * y + z * z < 1 and y > -0.05:
                break
        k = rng.uniform(0.55, 1.0)
        a = rng.uniform(0, 6.28, 3)
        sz = 70 * k
        F.add(BOX, model((1450 + x * 520, 1000 - y * 420, z * 200), (sz, sz * 0.8, sz * 0.9),
                         rot_x(a[0]) @ rot_y(a[1]) @ rot_z(a[2])),
              (52 + int(22 * k), 54 + int(20 * k), 64 + int(22 * k)), MAT_MATTE, 1.0)
    # kosede kucuk cekirdek
    nucleus(F, t, "N12", 1760, 170, 0.75, 1.0, plus=False, spin=0.3)
    img = F.finish(grain_on=False)
    cv2.line(img, (520, 560), (1690, 200), scol(CYAN, 0.9), 4, cv2.LINE_AA)
    img = big_text(img, ["14 GRAM", "= 1 TON"], 960, 40, 190, [WHITE, AMBER], anchor="c")
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_SB, 46)
    d.text((60, 990), "kömür eşdeğeri · kaynak: ABD DOE", font=f, fill=MUTED, stroke_width=4, stroke_fill=(6, 12, 32))
    return np.array(im)


def thumb2(t=2.0):
    F = Frame(t, Cam(yaw=0.0, pitch=0.0, dolly=1.0))
    nucleus(F, t, "N12", 1300, 560, 2.6, 1.0, plus=True, spin=0.3, bonds=True, arrows=True)
    F.torus(1300, 560, 0, 470, 0.035, AMBER, rot_x(math.pi / 2 - 0.35) @ rot_y(0.4), MAT_GLOW, 1.0)
    F.glow(1300, 560, 480, AMBER, 0.35, thick=40)
    img = F.finish(grain_on=False)
    img = big_text(img, ["ÇEKİRDEK", "NEDEN", "DAĞILMIYOR?"], 70, 150, 170, [WHITE, WHITE, CYAN])
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_B, 50)
    d.rounded_rectangle((1560, 950, 1860, 1030), radius=40, fill=(8, 16, 40), outline=AMBER, width=4)
    d.text((1607, 960), "Bölüm 1", font=f, fill=AMBER)
    f2 = ImageFont.truetype(F_SB, 32)
    d.text((1580, 900), "şematik", font=f2, fill=MUTED)
    return np.array(im)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for i, fn in enumerate((thumb1, thumb2), 1):
        img = cv2.resize(fn(), (1280, 720), interpolation=cv2.INTER_AREA)
        p = os.path.join(out, "kucuk-resim-%d.png" % i)
        Image.fromarray(img).save(p, optimize=True)
        print(p, os.path.getsize(p))
