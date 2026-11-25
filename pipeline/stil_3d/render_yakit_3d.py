#!/usr/bin/env python3
"""3D: Kullanilmis nukleer yakit ne kadar yer kaplar? (kullanilmis-yakit-ne-kadar-yer-kaplar.mp4)
1080x1920, 30 fps, 56 sn. Zaman cizelgesi short3_stok/render_yakit.py ile birebir ayni.
Kullanim: python3 render_yakit_3d.py still 3 10 ... | render"""
import math
from common3d import *

NAME = "kullanilmis-yakit-ne-kadar-yer-kaplar"
NFRAMES = 1680
FIELD = (40, 140, 70)
FIELD2 = (52, 162, 84)
WATER = (40, 130, 220)
STEEL = (150, 162, 180)
CER = (70, 74, 82)
CONC = (118, 122, 130)

MAT_CER = ((0.35, 0.3, 0.55, 0.0), (0, 0, 0, 1))
MAT_STEEL = ((1.0, 0.7, 0.7, 0.0), (0, 0, 0.75, 1))
MAT_CONC = ((0.12, 0.1, 0.35, 0.0), (0, 0, 0, 1))
MAT_WATER = ((1.2, 1.2, 1.4, 0.15), (0, 0, 0, 1))

CAMK = [(0, 0.0, 0.10, 1.0), (5.2, 0.12, 0.16, 0.95), (5.6, 0.0, 0.12, 1.0), (15.2, 0.10, 0.18, 0.95),
        (15.6, 0.0, 0.0, 1.0), (24.4, 0.0, 0.0, 0.96), (25.0, 0.0, 0.0, 1.0), (30.2, 0.10, 0.0, 0.98),
        (30.8, -0.10, 0.12, 1.0), (38.4, 0.10, 0.12, 0.96), (38.9, 0.0, 0.0, 1.0), (46.8, 0.0, 0.0, 0.97),
        (47.3, 0.0, 0.0, 1.0), (60, 0.0, 0.0, 0.94)]


def cam_at(t):
    if 24.6 <= t < 30.4:      # futbol sahasi: yukaridan bakan kamera
        return Cam(yaw=0.16 * math.sin(t * 0.3) - 0.06, pitch=0.55, dolly=1.0 - 0.04 * smooth(seg(t, 24.6, 30.4)),
                   pivot=(540, GY, (FZ0 + FZ1) / 2), shift=(0, 150))
    for (t0, y0, p0, d0), (t1, y1, p1, d1) in zip(CAMK, CAMK[1:]):
        if t <= t1:
            u = ease_in_out(seg(t, t0, t1))
            yaw, pit, dol = y0 + (y1 - y0) * u, p0 + (p1 - p0) * u, d0 + (d1 - d0) * u
            break
    yaw += 0.03 * math.sin(t * 0.37)
    pit += 0.015 * math.sin(t * 0.29)
    return Cam(yaw=yaw, pitch=pit, dolly=dol, pivot=(540, 980, 0))


# ----------------------------------------------------------------- cizimler
def pellet(F, cx, cy, w, h, op, glow=0.0, R=None, z=0.0):
    if op <= 0:
        return
    F.cyl(cx, cy, z, w / 2, h, CER, MAT_CER, alpha=op, R=R)
    if glow > 0:
        F.glow3(cx, cy, z, max(w, h) * 1.2, AMBER, glow * op)


def rod(F, cx, y0, y1, w, op, glow=0.4, z=0.0):
    if op <= 0:
        return
    F.cyl(cx, (y0 + y1) / 2, z, w / 2, y1 - y0, STEEL, MAT_STEEL, alpha=op, lo=True,
          ext=(10.0, 0.25, 0.75, 1.0))
    for y in range(int(y0), int(y1), 48):
        F.glow3(cx, y, z, w * 0.9, AMBER, 0.12 * op * glow)


def frame_box(F, x0, y0, x1, y1, d, col, op, rad=2.5):
    """Tel cerceve kutu (12 kenar)."""
    if op <= 0:
        return
    zs = (-d / 2, d / 2)
    P = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in zs]
    for i in range(8):
        for j in range(i + 1, 8):
            a, b = P[i], P[j]
            if sum(1 for k in range(3) if a[k] != b[k]) == 1:
                F.rod(a, b, rad, col, MAT_GLOW, alpha=op)


def counter_text(v):
    return "{:,}".format(int(v)).replace(",", ".")


# futbol sahasi: yatay duzlem (y = GY), x 90..990, z -720..0
GY = 1170
FX0, FX1, FZ0, FZ1 = 110, 970, -760, 0


def field(F, t, op, block_h):
    if op <= 0:
        return
    n = 10
    dz = (FZ1 - FZ0) / n
    for k in range(n):
        F.box(540, GY + 6, FZ0 + dz * (k + 0.5), FX1 - FX0, 12, dz, FIELD if k % 2 else FIELD2, MAT_MATTE,
              alpha=op, r=0)
    lc = (230, 245, 235)
    lm = ((0.2, 0.2, 0.3, 0.35), (0, 0, 0, 1))
    for (a, b) in [((FX0, FZ0), (FX1, FZ0)), ((FX1, FZ0), (FX1, FZ1)), ((FX1, FZ1), (FX0, FZ1)), ((FX0, FZ1), (FX0, FZ0)),
                   ((FX0, (FZ0 + FZ1) / 2), (FX1, (FZ0 + FZ1) / 2))]:
        F.rod((a[0], GY - 1, a[1]), (b[0], GY - 1, b[1]), 3.5, lc, lm, alpha=op)
    if block_h > 1:
        F.box(540, GY - block_h / 2, (FZ0 + FZ1) / 2, FX1 - FX0 - 30, block_h, FZ1 - FZ0 - 30, (96, 104, 122),
              ((0.4, 0.3, 0.7, 0.0), (0, 0, 0.2, 1)), alpha=0.72 * op, r=4)
        x, z = FX1 + 40, FZ1 - 20
        F.rod((x, GY, z), (x, GY - block_h, z), 3.5, AMBER, MAT_GLOW, alpha=op)
        F.add(CONE, model((x, GY - block_h + 9, z), (10, 18, 10)), AMBER, MAT_GLOW, op)
        F.add(CONE, model((x, GY - 9, z), (10, 18, 10), np.diag([1, -1, -1.0])), AMBER, MAT_GLOW, op)
        return F.p2(x, GY - block_h, z)
    return None


def pool(F, t, cx, cy, op):
    if op <= 0:
        return
    w, h, d = 400, 330, 260
    # beton havuz: taban + 4 duvar (on duvar alcak)
    F.box(cx, cy + h / 2 + 9, 0, w + 36, 18, d + 36, CONC, MAT_CONC, alpha=op, r=4)
    F.box(cx - w / 2 - 9, cy, 0, 18, h, d + 36, CONC, MAT_CONC, alpha=op, r=4)
    F.box(cx + w / 2 + 9, cy, 0, 18, h, d + 36, CONC, MAT_CONC, alpha=op, r=4)
    F.box(cx, cy, -d / 2 - 9, w, h, 18, CONC, MAT_CONC, alpha=op, r=4)
    for k in range(6):
        x = cx - 150 + k * 60
        rod(F, x, cy - 40, cy + h // 2 - 20, 30, op, glow=0.6)
        F.glow3(x, cy + 40, 0, 50, (90, 170, 255), 0.25 * op)
    wy = cy + 15 + 4 * math.sin(t * 2)
    F.box(cx, (wy + cy + h / 2) / 2, 0, w, cy + h / 2 - wy, d, WATER, MAT_WATER, alpha=0.42 * op, r=2)
    F.box(cx, cy + h / 2 + 2, d / 2 + 9, w + 36, h * 0.0 + 18, 18, CONC, MAT_CONC, alpha=op, r=4)


def cask(F, cx, cy, op, s=1.0):
    if op <= 0:
        return
    w, h = 150 * s, 300 * s
    F.cyl(cx, cy, 0, w / 2, h, (128, 136, 150), ((0.6, 0.45, 0.6, 0.0), (0, 0, 0.4, 1)), alpha=op,
          ext=(4.0, 0.45, 0.4, 1.0))
    F.cyl(cx, cy - h / 2 - 6 * s, 0, w / 2 * 0.92, 12 * s, (175, 184, 198), MAT_STEEL, alpha=op)


def bar(F, t, t0, cx, cy, w, h, frac, col, op):
    if op <= 0:
        return
    p = smooth(seg(t, t0, t0 + 1.6)) * frac
    F.box(cx, cy, 0, w, h, h, (60, 90, 150), MAT_GLOSS, alpha=0.22 * op, r=14)
    ww = (w - 12) * p
    if ww > 2:
        x1 = cx - w / 2 + 6 + ww
        F.box(cx - w / 2 + 6 + ww / 2, cy, 0, ww, h - 12, h - 12, col, ((0.8, 0.8, 0.8, 0.45), (0, 0, 0, 1)), alpha=op, r=10)
        F.glow3(x1, cy, 0, h * 0.9, col, 0.6 * op)


def recycle(F, t, cx, cy, op):
    if op <= 0:
        return
    r = 150
    Rt = rot_x(0.35) @ rot_y(0.25 * math.sin(t * 0.8))
    for k in range(3):
        a0 = math.radians(k * 120 + t * 40)
        a1 = a0 + math.radians(95)
        pts = []
        for i in range(13):
            a = a0 + (a1 - a0) * i / 12
            v = Rt @ np.array([r * math.cos(a), r * math.sin(a), 0])
            pts.append((cx + v[0], cy + v[1], v[2]))
        for p, q in zip(pts, pts[1:]):
            F.rod(p, q, 7, GREEN, MAT_GLOW, alpha=op)
        tg = np.array(pts[-1]) - np.array(pts[-2])
        tg /= np.linalg.norm(tg)
        tip = np.array(pts[-1]) + tg * 18
        F.add(CONE, model(tip, (22, 40, 22), gl3d_align(tg)), GREEN, MAT_GLOW, op)
    F.glow(cx, cy, r * 1.3, GREEN, 0.35 * op)
    pellet(F, cx, cy, 70, 84, op, glow=0.5, R=rot_x(0.4) @ rot_z(0.3 * math.sin(t)))


def gl3d_align(u):
    from common3d import _align_y
    return _align_y(u)


# ----------------------------------------------------------------- kare
def frame_F(t):
    F = Frame(t, cam_at(t))

    # S0 soru (0 - 5.4)
    F.caption([("KULLANILMIŞ NÜKLEER YAKIT", WHITE), ("NE KADAR YER KAPLAR?", AMBER)], 0.3, 5.4, y0=360, size=70)
    o0 = fade(t, 0.5, 1.1) * (1 - fade(t, 5.0, 5.4))
    if o0 > 0:
        for k in range(9):
            x = 540 + (k - 4) * 44
            rod(F, x, 760, 1240, 30, o0 * fade(t, 0.5 + 0.05 * k, 1.0 + 0.05 * k), glow=0.9)
        F.glow(540, 1000, 300, AMBER, 0.35 * o0)
        frame_box(F, 340, 740, 740, 1260, 60, STEEL, o0)
    if t > 4.1:
        F.text_in("CEVAP ŞAŞIRTABİLİR", F_B, 72, CYAN, 540, 1400, 4.1, op=1 - fade(t, 5.0, 5.4))

    # S1 pelet -> cubuk -> demet (5.4 - 15.4)
    if 5.2 < t < 15.6:
        so = fade(t, 5.4, 5.9) * (1 - fade(t, 15.0, 15.4))
        F.caption([("YAKIT: SERAMİK PELET", WHITE)], 5.5, 10.6, y0=360, size=76)
        F.text_in("düşük zenginleştirilmiş uranyum oksit", F_M, 40, MUTED, 540, 460, 6.6,
                  op=so * (1 - fade(t, 10.2, 10.6)))
        po = so * (1 - fade(t, 10.4, 10.9))
        sc = ease_out_back(seg(t, 5.6, 6.4))
        pellet(F, 540, 960, 220 * max(sc, 0.01), 260 * max(sc, 0.01), po * min(1, sc), glow=0.4,
               R=rot_x(0.45 + 0.1 * math.sin(t * 0.7)) @ rot_z(0.18 * math.sin(t * 0.5)))
        if t > 10.6:
            F.caption([("PELETLER ÇUBUĞA,", WHITE), ("ÇUBUKLAR DEMETE", AMBER)], 10.8, 15.4, y0=360, size=70)
            p = smooth(seg(t, 10.8, 12.2))
            for k in range(12):
                tgt_y = 760 + k * 40
                y = 960 + (tgt_y - 960) * p
                pellet(F, 540, y, 56, 34, so * fade(t, 10.6 + 0.03 * k, 11.0 + 0.03 * k))
            ro = so * fade(t, 12.0, 12.6)
            if ro > 0:
                F.cyl(540, 985, 0, 36, 510, STEEL, ((1.2, 0.8, 1.0, 0.0), (0, 0, 0.6, 1)), alpha=0.28 * ro)
            bo = so * fade(t, 12.8, 13.6)
            if bo > 0:
                for i in range(-4, 5):
                    if i == 0:
                        continue
                    rod(F, 540 + i * 62, 730, 1240, 40, bo * fade(t, 12.8 + 0.06 * abs(i), 13.4 + 0.06 * abs(i)))
                frame_box(F, 275, 710, 805, 1260, 70, WHITE, 0.6 * bo)

    # S2 sayac (15.4 - 24.6)
    if 15.2 < t < 24.8:
        so = fade(t, 15.4, 15.9) * (1 - fade(t, 24.2, 24.6))
        F.caption([("ABD TİCARİ REAKTÖRLERİ", WHITE), ("1950'LERDEN BU YANA", MUTED)], 15.5, 24.6, y0=360, size=64)
        v = 90000 * ease_out(seg(t, 17.5, 22.5))
        if t > 17.3:
            F.text("≈ " + counter_text(v), F_B, 170, AMBER, 540, 900, op=so * fade(t, 17.3, 17.8))
            F.text("METRİK TON", F_B, 80, WHITE, 540, 1060, op=so * fade(t, 17.6, 18.1))
            F.glow(540, 960, 380, AMBER, 0.25 * so)
        F.text_in("kullanılmış yakıt", F_M, 46, MUTED, 540, 1160, 22.0, op=so)

    # S3 futbol sahasi (24.6 - 30.4)
    if 24.4 < t < 30.6:
        so = fade(t, 24.6, 25.1) * (1 - fade(t, 30.0, 30.4))
        F.caption([("HEPSİ BİR ARADA:", WHITE), ("TEK BİR FUTBOL SAHASI", AMBER)], 24.7, 30.4, y0=360, size=70)
        bh = 150 * smooth(seg(t, 26.2, 27.8))
        top = field(F, t, so, bh)
        if top is not None and bh > 10:
            F.text_in("9 m'den az", F_B, 56, AMBER, min(top[0] - 60, 900), int(top[1] - 70), 27.8, op=so)
        F.text_in("yükseklikte bir yığın", F_M, 44, MUTED, 540, 1340, 28.3, op=so)

    # S4 havuz -> kuru kap (30.4 - 38.6)
    if 30.2 < t < 38.8:
        so = fade(t, 30.4, 30.9) * (1 - fade(t, 38.2, 38.6))
        F.caption([("NASIL SAKLANIYOR?", WHITE)], 30.5, 38.6, y0=360, size=76)
        o1 = so * fade(t, 30.6, 31.2)
        pool(F, t, 540, 740, o1 * (1 - 0.55 * fade(t, 34.6, 35.2)))
        F.text_in("1 · SU DOLU HAVUZ", F_B, 50, CYAN, 540, 975, 31.0, op=so)
        F.text_in("çelik kaplı beton", F_M, 36, MUTED, 540, 1030, 31.6, op=so)
        o2 = so * fade(t, 34.6, 35.2)
        for i, x in enumerate([370, 540, 710]):
            cask(F, x, 1215, o2 * fade(t, 34.6 + 0.2 * i, 35.2 + 0.2 * i), s=0.62)
        F.text_in("2 · KURU DEPOLAMA KABI", F_B, 50, AMBER, 540, 1375, 35.0, op=so)
        F.text_in("çelik ve beton", F_M, 36, MUTED, 540, 1430, 35.6, op=so)

    # S5 %90 enerji (38.6 - 47.0)
    if 38.4 < t < 47.2:
        so = fade(t, 38.6, 39.1) * (1 - fade(t, 46.6, 47.0))
        F.caption([("REAKTÖRDE 5 YIL SONRA BİLE", WHITE)], 39.6, 47.0, y0=360, size=64)
        if t > 41.0:
            F.text("%90+", F_B, 200, AMBER, 540, 820, op=so * fade(t, 41.0, 41.6))
        bar(F, t, 41.4, 540, 1010, 820, 70, 0.92, AMBER, so * fade(t, 41.2, 41.7))
        F.text_in("POTANSİYEL ENERJİ HÂLÂ İÇİNDE", F_B, 52, WHITE, 540, 1140, 43.0, op=so)

    # S6 geri donusum (47.0 - 50.3)
    if 46.8 < t < 50.5:
        so = fade(t, 47.0, 47.5) * (1 - fade(t, 49.9, 50.3))
        F.caption([("GERİ DÖNÜŞTÜRÜLEBİLİR", GREEN)], 47.1, 50.3, y0=360, size=80)
        recycle(F, t, 540, 930, so)
        F.text_in("örneğin Fransa", F_SB, 50, WHITE, 540, 1200, 48.2, op=so)

    F.series_tag()
    if t >= 50.3:
        source_card(F, 50.3, [
            "ABD Enerji Bakanlığı (DOE) · 5 Fast Facts",
            "about Spent Nuclear Fuel",
            "DOE · Nuclear 101: How Does a Nuclear Reactor Work?",
        ], ["Seslendirme yapay ses ile yapılmıştır."])
    return F


def frame(t):
    return frame_F(t).finish()


if __name__ == "__main__":
    cli("render_yakit_3d", frame, NFRAMES, NAME)
