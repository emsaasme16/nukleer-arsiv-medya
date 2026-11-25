#!/usr/bin/env python3
"""Short: Kullanilmis nukleer yakit ne kadar yer kaplar? 1080x1920, 30 fps.
Ses +0.5 sn kaydirildi; sahne zamanlari video saniyesidir.
Kullanim: render_yakit.py still 3 10 ... | chunk BAS SON"""
import math, os
from common import *

OUT = os.environ.get("OUT", "/home/claude/s3/b")
DUR = 56.0
GREEN = (110, 230, 140)
FIELD = (40, 140, 70)
WATER = (40, 130, 220)
STEEL = (150, 162, 180)
CER = (70, 74, 82)          # pelet (koyu seramik)

# ----------------------------------------------------------------- cizimler
def pellet(img, gl, cx, cy, w, h, op, glow=0.0):
    if op <= 0:
        return
    ov = img.copy()
    ew = max(2, int(h * 0.18))
    cv2.rectangle(ov, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), CER, -1)
    cv2.ellipse(ov, (int(cx), int(cy - h / 2)), (int(w / 2), ew), 0, 0, 360, (110, 116, 128), -1, cv2.LINE_AA)
    cv2.ellipse(ov, (int(cx), int(cy + h / 2)), (int(w / 2), ew), 0, 0, 180, CER, -1, cv2.LINE_AA)
    cv2.line(ov, (int(cx - w / 2 + w * 0.18), int(cy - h / 2 + ew)), (int(cx - w / 2 + w * 0.18), int(cy + h / 2)),
             (120, 126, 138), max(1, int(w * 0.06)), cv2.LINE_AA)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
    if glow > 0:
        gcircle(gl, cx, cy, max(w, h) * 1.2, AMBER, glow * op)

def rod(img, gl, cx, y0, y1, w, op, glow=0.4):
    if op <= 0:
        return
    ov = img.copy()
    cv2.rectangle(ov, (int(cx - w / 2), int(y0)), (int(cx + w / 2), int(y1)), STEEL, -1)
    cv2.rectangle(ov, (int(cx - w / 2 + w * 0.15), int(y0)), (int(cx - w / 2 + w * 0.3), int(y1)), (205, 214, 228), -1)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
    for y in range(int(y0), int(y1), 24):
        gcircle(gl, cx, y, w * 0.9, AMBER, 0.12 * op * glow)

def counter_text(v):
    return "{:,}".format(int(v)).replace(",", ".")

def field(img, gl, t, op, block_h):
    """Perspektif futbol sahasi + uzerinde yigin."""
    if op <= 0:
        return
    tl, tr = (300, 820), (780, 820)
    bl, br = (90, 1240), (990, 1240)
    ov = img.copy()
    cv2.fillPoly(ov, [np.array([tl, tr, br, bl], np.int32)], FIELD, cv2.LINE_AA)
    for k in range(1, 10):
        u = k / 10
        y = int(820 + (1240 - 820) * u)
        xl = int(tl[0] + (bl[0] - tl[0]) * u)
        xr = int(tr[0] + (br[0] - tr[0]) * u)
        cv2.line(ov, (xl, y), (xr, y), (60, 170, 95), 2, cv2.LINE_AA)
    cv2.polylines(ov, [np.array([tl, tr, br, bl], np.int32)], True, (230, 245, 235), 4, cv2.LINE_AA)
    cv2.line(ov, ((tl[0] + bl[0]) // 2 + 0, 1030), ((tr[0] + br[0]) // 2, 1030), (230, 245, 235), 3, cv2.LINE_AA)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
    if block_h > 1:
        # saha boyunca yigin (on yuz + ust yuz)
        ov = img.copy()
        fl, fr = (110, 1230), (970, 1230)
        bl2, br2 = (305, 830), (775, 830)
        top_f = [(fl[0], fl[1] - block_h), (fr[0], fr[1] - block_h)]
        top_b = [(br2[0], br2[1] - block_h * 0.45), (bl2[0], bl2[1] - block_h * 0.45)]
        cv2.fillPoly(ov, [np.array([fl, fr, top_f[1], top_f[0]], np.int32)], (90, 98, 116), cv2.LINE_AA)
        cv2.fillPoly(ov, [np.array([top_f[0], top_f[1], top_b[0], top_b[1]], np.int32)], (140, 150, 170), cv2.LINE_AA)
        cv2.addWeighted(ov, 0.75 * op, img, 1 - 0.75 * op, 0, dst=img)
        cv2.polylines(img, [np.array([fl, fr, top_f[1], top_b[0], top_b[1], top_f[0]], np.int32)], True,
                      scol(WHITE, 0.6 * op), 2, cv2.LINE_AA)
        # yukseklik oku
        x = 1010
        cv2.arrowedLine(img, (x, 1230), (x, int(1230 - block_h)), scol(AMBER, op), 5, cv2.LINE_AA, tipLength=0.08)
        cv2.arrowedLine(img, (x, int(1230 - block_h)), (x, 1230), scol(AMBER, op), 5, cv2.LINE_AA, tipLength=0.08)

def pool(img, gl, t, cx, cy, op):
    if op <= 0:
        return
    w, h = 400, 330
    ov = img.copy()
    cv2.rectangle(ov, (cx - w // 2 - 18, cy - h // 2), (cx + w // 2 + 18, cy + h // 2 + 18), (120, 126, 140), -1)
    cv2.rectangle(ov, (cx - w // 2, cy - h // 2 + 30), (cx + w // 2, cy + h // 2), WATER, -1)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
    pts = [(x, int(cy - h // 2 + 30 + 6 * math.sin(x / 22 + t * 3))) for x in range(cx - w // 2, cx + w // 2, 6)]
    cv2.polylines(img, [np.array(pts, np.int32)], False, scol((180, 225, 255), op), 3, cv2.LINE_AA)
    for k in range(6):
        x = cx - 150 + k * 60
        rod(img, gl, x, cy - 40, cy + h // 2 - 20, 30, op, glow=0.6)
        gcircle(gl, x, cy + 40, 50, (90, 170, 255), 0.25 * op)

def cask(img, gl, cx, cy, op, s=1.0):
    if op <= 0:
        return
    w, h = int(150 * s), int(300 * s)
    ov = img.copy()
    cv2.rectangle(ov, (cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2), (128, 136, 150), -1)
    cv2.ellipse(ov, (cx, cy - h // 2), (w // 2, int(22 * s)), 0, 0, 360, (175, 184, 198), -1, cv2.LINE_AA)
    cv2.ellipse(ov, (cx, cy + h // 2), (w // 2, int(22 * s)), 0, 0, 180, (128, 136, 150), -1, cv2.LINE_AA)
    cv2.rectangle(ov, (cx - w // 2 + int(18 * s), cy - h // 2), (cx - w // 2 + int(34 * s), cy + h // 2), (170, 178, 192), -1)
    for k in range(3):
        y = cy - h // 2 + int((k + 1) * h / 4)
        cv2.line(ov, (cx - w // 2, y), (cx + w // 2, y), (100, 108, 122), 3, cv2.LINE_AA)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)

def bar(img, gl, t, t0, cx, cy, w, h, frac, col, op):
    if op <= 0:
        return
    p = smooth(seg(t, t0, t0 + 1.6)) * frac
    cv2.rectangle(img, (cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2), scol(MUTED, 0.6 * op), 3, cv2.LINE_AA)
    x1 = int(cx - w // 2 + 6 + (w - 12) * p)
    if x1 > cx - w // 2 + 6:
        ov = img.copy()
        cv2.rectangle(ov, (cx - w // 2 + 6, cy - h // 2 + 6), (x1, cy + h // 2 - 6), col, -1)
        cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
        gcircle(gl, x1, cy, h * 0.9, col, 0.6 * op)

def recycle(img, gl, t, cx, cy, op):
    if op <= 0:
        return
    r = 150
    for k in range(3):
        a0 = k * 120 + t * 40
        cv2.ellipse(img, (cx, cy), (r, r), 0, a0, a0 + 95, scol(GREEN, op), 14, cv2.LINE_AA)
        a = math.radians(a0 + 95)
        tip = (cx + r * math.cos(a), cy + r * math.sin(a))
        d = (-math.sin(a), math.cos(a))
        n = (math.cos(a), math.sin(a))
        p1 = (tip[0] + d[0] * 34, tip[1] + d[1] * 34)
        p2 = (tip[0] + n[0] * 26 - d[0] * 6, tip[1] + n[1] * 26 - d[1] * 6)
        p3 = (tip[0] - n[0] * 26 - d[0] * 6, tip[1] - n[1] * 26 - d[1] * 6)
        cv2.fillPoly(img, [np.array([p1, p2, p3], np.int32)], scol(GREEN, op), cv2.LINE_AA)
    gcircle(gl, cx, cy, r * 1.3, GREEN, 0.35 * op)
    pellet(img, gl, cx, cy, 70, 84, op, glow=0.5)

# ----------------------------------------------------------------- kare
def frame(t):
    img = base(t)
    gl = newgl()
    series_tag(img, t)

    # S0 soru (0 - 5.4)
    caption(img, [("KULLANILMIŞ NÜKLEER YAKIT", WHITE), ("NE KADAR YER KAPLAR?", AMBER)], t, 0.3, 5.4, y0=360, size=70)
    o0 = fade(t, 0.5, 1.1) * (1 - fade(t, 5.0, 5.4))
    if o0 > 0:
        for k in range(9):
            x = 540 + (k - 4) * 44
            rod(img, gl, x, 760, 1240, 30, o0, glow=0.9)
        gcircle(gl, 540, 1000, 300, AMBER, 0.35 * o0)
        cv2.rectangle(img, (340, 740), (740, 1260), scol(STEEL, o0), 4, cv2.LINE_AA)
    if t > 4.1:
        text_in(img, "CEVAP ŞAŞIRTABİLİR", F_B, 72, CYAN, 540, 1400, t, 4.1, op=1 - fade(t, 5.0, 5.4))

    # S1 pelet -> cubuk -> demet (5.4 - 15.4)
    if 5.2 < t < 15.6:
        so = fade(t, 5.4, 5.9) * (1 - fade(t, 15.0, 15.4))
        caption(img, [("YAKIT: SERAMİK PELET", WHITE)], t, 5.5, 10.6, y0=360, size=76)
        text_in(img, "düşük zenginleştirilmiş uranyum oksit", F_M, 40, MUTED, 540, 460, t, 6.6,
                op=so * (1 - fade(t, 10.2, 10.6)))
        # tek pelet buyuk
        po = so * (1 - fade(t, 10.4, 10.9))
        pellet(img, gl, 540, 960, 220, 260, po * ease_out_back(seg(t, 5.6, 6.4)), glow=0.4)
        # cubuga dizilme
        if t > 10.6:
            caption(img, [("PELETLER ÇUBUĞA,", WHITE), ("ÇUBUKLAR DEMETE", AMBER)], t, 10.8, 15.4, y0=360, size=70)
            p = smooth(seg(t, 10.8, 12.2))
            for k in range(12):
                tgt_y = 760 + k * 40
                y = 960 + (tgt_y - 960) * p
                pellet(img, gl, 540, y, 56, 34, so * fade(t, 10.6 + 0.03 * k, 11.0 + 0.03 * k))
            ro = so * fade(t, 12.0, 12.6)
            if ro > 0:
                cv2.rectangle(img, (505, 730), (575, 1240), scol(STEEL, ro), 5, cv2.LINE_AA)
            # demet
            bo = so * fade(t, 12.8, 13.6)
            if bo > 0:
                for i in range(-4, 5):
                    if i == 0:
                        continue
                    rod(img, gl, 540 + i * 62, 730, 1240, 40, bo * fade(t, 12.8 + 0.06 * abs(i), 13.4 + 0.06 * abs(i)))
                cv2.rectangle(img, (275, 710), (805, 1260), scol(WHITE, 0.6 * bo), 3, cv2.LINE_AA)

    # S2 sayac (15.4 - 24.6)
    if 15.2 < t < 24.8:
        so = fade(t, 15.4, 15.9) * (1 - fade(t, 24.2, 24.6))
        caption(img, [("ABD TİCARİ REAKTÖRLERİ", WHITE), ("1950'LERDEN BU YANA", MUTED)], t, 15.5, 24.6, y0=360, size=64)
        v = 90000 * ease_out(seg(t, 17.5, 22.5))
        if t > 17.3:
            blit(img, T("≈ " + counter_text(v), F_B, 170, AMBER), 540, 900, op=so * fade(t, 17.3, 17.8))
            blit(img, T("METRİK TON", F_B, 80, WHITE), 540, 1060, op=so * fade(t, 17.6, 18.1))
            gcircle(gl, 540, 960, 380, AMBER, 0.25 * so)
        text_in(img, "kullanılmış yakıt", F_M, 46, MUTED, 540, 1160, t, 22.0, op=so)

    # S3 futbol sahasi (24.6 - 30.4)
    if 24.4 < t < 30.6:
        so = fade(t, 24.6, 25.1) * (1 - fade(t, 30.0, 30.4))
        caption(img, [("HEPSİ BİR ARADA:", WHITE), ("TEK BİR FUTBOL SAHASI", AMBER)], t, 24.7, 30.4, y0=360, size=70)
        bh = 150 * smooth(seg(t, 26.2, 27.8))
        field(img, gl, t, so, bh)
        if bh > 10:
            text_in(img, "9 m'den az", F_B, 56, AMBER, 790, int(1230 - bh - 90), t, 27.8, op=so)
        text_in(img, "yükseklikte bir yığın", F_M, 44, MUTED, 540, 1340, t, 28.3, op=so)

    # S4 havuz -> kuru kap (30.4 - 38.6)
    if 30.2 < t < 38.8:
        so = fade(t, 30.4, 30.9) * (1 - fade(t, 38.2, 38.6))
        caption(img, [("NASIL SAKLANIYOR?", WHITE)], t, 30.5, 38.6, y0=360, size=76)
        o1 = so * fade(t, 30.6, 31.2)
        pool(img, gl, t, 540, 740, o1 * (1 - 0.55 * fade(t, 34.6, 35.2)))
        text_in(img, "1 · SU DOLU HAVUZ", F_B, 50, CYAN, 540, 975, t, 31.0, op=so)
        text_in(img, "çelik kaplı beton", F_M, 36, MUTED, 540, 1030, t, 31.6, op=so)
        o2 = so * fade(t, 34.6, 35.2)
        for i, x in enumerate([370, 540, 710]):
            cask(img, gl, x, 1215, o2 * fade(t, 34.6 + 0.2 * i, 35.2 + 0.2 * i), s=0.62)
        text_in(img, "2 · KURU DEPOLAMA KABI", F_B, 50, AMBER, 540, 1375, t, 35.0, op=so)
        text_in(img, "çelik ve beton", F_M, 36, MUTED, 540, 1430, t, 35.6, op=so)

    # S5 %90 enerji (38.6 - 47.0)
    if 38.4 < t < 47.2:
        so = fade(t, 38.6, 39.1) * (1 - fade(t, 46.6, 47.0))
        caption(img, [("REAKTÖRDE 5 YIL SONRA BİLE", WHITE)], t, 39.6, 47.0, y0=360, size=64)
        if t > 41.0:
            blit(img, T("%90+", F_B, 200, AMBER), 540, 820, op=so * fade(t, 41.0, 41.6))
        bar(img, gl, t, 41.4, 540, 1010, 820, 70, 0.92, AMBER, so * fade(t, 41.2, 41.7))
        text_in(img, "POTANSİYEL ENERJİ HÂLÂ İÇİNDE", F_B, 52, WHITE, 540, 1140, t, 43.0, op=so)

    # S6 geri donusum (47.0 - 50.3)
    if 46.8 < t < 50.5:
        so = fade(t, 47.0, 47.5) * (1 - fade(t, 49.9, 50.3))
        caption(img, [("GERİ DÖNÜŞTÜRÜLEBİLİR", GREEN)], t, 47.1, 50.3, y0=360, size=80)
        recycle(img, gl, t, 540, 930, so)
        text_in(img, "örneğin Fransa", F_SB, 50, WHITE, 540, 1200, t, 48.2, op=so)

    note(img, t, 5.5, 50.3)
    apply_glow(img, gl)

    if t >= 50.3:
        img = source_card(img, t, 50.3, [
            "ABD Enerji Bakanlığı (DOE) · 5 Fast Facts",
            "about Spent Nuclear Fuel",
            "DOE · Nuclear 101: How Does a Nuclear Reactor Work?",
        ], ["Animasyon şematiktir, ölçekli değildir.", "Seslendirme yapay ses ile yapılmıştır."])
    return img

if __name__ == "__main__":
    main(frame, OUT, "yakit", DUR)
