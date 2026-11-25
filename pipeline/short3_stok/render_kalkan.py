#!/usr/bin/env python3
"""Short: Radyasyon neyle durur? (alfa / beta / gama ve kalkanlar). 1080x1920, 30 fps.
Ses +0.5 sn kaydirildi; sahne zamanlari video saniyesidir.
Kullanim: render_kalkan.py still 3 10 ... | chunk BAS SON"""
import math, os
from common import *

OUT = os.environ.get("OUT", "/home/claude/s3/a")
DUR = 52.5
LANE_Y = 960
EX = 150                      # kaynak (yayici) x
PAPER_X, METAL_X, LEAD_X = 400, 620, 850
ALPHA_C = (255, 96, 96)
BETA_C = (80, 190, 255)
GAMMA_C = (190, 120, 255)
GREEN = (110, 230, 140)
F_GR = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def gtitle(img, t, t0, t1, name, sym, col):
    """ALFA (α) basligi: harf DejaVu ile."""
    ex = 1 - fade(t, t1 - 0.35, t1)
    p = ease_out(seg(t, t0, t0 + 0.6))
    if p <= 0 or ex <= 0:
        return
    a = T(name, F_B, 96, col); b = T(sym, F_GR, 96, col)
    wa, wb = a[1].shape[1], b[1].shape[1]
    x0 = 540 - (wa + wb) / 2
    y = 360 + (1 - p) * 36
    blit(img, a, x0 + wa / 2, y, op=p * ex)
    blit(img, b, x0 + wa + wb / 2 - 10, y + 4, op=p * ex)

# ----------------------------------------------------------------- cizimler
def emitter(img, gl, t, op):
    if op <= 0:
        return
    r = 46 + 4 * math.sin(t * 3)
    gcircle(gl, EX, LANE_Y, r * 2.4, AMBER, 0.55 * op)
    blit(img, NUC_SPR, EX, LANE_Y, op=op, scale=r * 2 / 400)

def barrier(img, x, w, h, col, label, op, sub=None):
    if op <= 0:
        return
    y0, y1 = LANE_Y - h // 2, LANE_Y + h // 2
    ov = img.copy()
    cv2.rectangle(ov, (x - w // 2, y0), (x + w // 2, y1), col, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, op, img, 1 - op, 0, dst=img)
    cv2.rectangle(img, (x - w // 2, y0), (x + w // 2, y1), scol(WHITE, 0.55 * op), 2, cv2.LINE_AA)
    blit(img, T(label, F_SB, 32, WHITE, maxw=260), x, y1 + 50, op=op)
    if sub:
        blit(img, T(sub, F_M, 26, MUTED, maxw=260), x, y1 + 92, op=op)

def barriers(img, t, t0, which=(1, 1, 1), fade_out=None):
    o = fade(t, t0, t0 + 0.6)
    if fade_out:
        o *= 1 - fade(t, fade_out - 0.4, fade_out)
    if which[0]:
        barrier(img, PAPER_X, 10, 330, (235, 235, 225), "KÂĞIT", o)
    if which[1]:
        barrier(img, METAL_X, 24, 330, (170, 182, 196), "METAL LEVHA", o, "ör. alüminyum")
    if which[2]:
        barrier(img, LEAD_X, 110, 360, (70, 78, 92), "KURŞUN", o, "ya da kalın beton")

def alpha_spr(img, gl, x, y, op, s=1.0):
    gcircle(gl, x, y, 46 * s, ALPHA_C, 0.8 * op)
    for dx, dy, c in [(-11, -11, WARM), (11, -11, NEUT), (-11, 11, NEUT), (11, 11, WARM)]:
        blit(img, PROTON_SPR if c == WARM else NEUT_SPR, x + dx * s, y + dy * s, op=op, scale=26 * s / 400)

def beta_spr(img, gl, x, y, op):
    gcircle(gl, x, y, 26, BETA_C, 0.9 * op)
    blit(img, BETA_SPR, x, y, op=op, scale=18 / 400)

def gamma_wave(img, gl, x0, x1, y, t, op, amp=22, decay_from=None):
    if op <= 0 or x1 <= x0:
        return
    pts = []
    for x in range(int(x0), int(x1), 4):
        a = amp
        if decay_from is not None and x > decay_from:
            a = amp * math.exp(-(x - decay_from) / 28)
        pts.append((x, int(y + a * math.sin((x - t * 900) / 18))))
    if len(pts) > 1:
        arr = np.array(pts, np.int32)
        cv2.polylines(img, [arr], False, scol(GAMMA_C, op), 6, cv2.LINE_AA)
        for p in pts[::3]:
            gcircle(gl, p[0], p[1], 14, GAMMA_C, 0.5 * op)

def flight(t, t0, x0, x1, speed):
    """t0'da x0'dan cikar, x1'de durur. (x, durdu_mu)"""
    if t < t0:
        return None, False
    x = x0 + (t - t0) * speed
    return (min(x, x1), x >= x1)

def stop_flash(gl, x, y, t, t_hit, col):
    if t_hit is None or t < t_hit:
        return
    k = 1 - seg(t, t_hit, t_hit + 0.6)
    if k > 0:
        gcircle(gl, x, y, 90 * (1 - k) + 30, col, 1.2 * k)

NEUT_SPR = sphere_sprite(NEUT, 400, rim=(220, 230, 255), spec=0.5)
BETA_SPR = sphere_sprite(BETA_C, 400, rim=(200, 240, 255), spec=0.7)

def sym_card(img, gl, cx, cy, sym, name, col, op):
    if op <= 0:
        return
    gcircle(gl, cx, cy, 150, col, 0.45 * op)
    cv2.circle(img, (cx, cy), 120, scol(col, op), 5, cv2.LINE_AA)
    blit(img, T(sym, F_GR, 120, col), cx, cy - 4, op=op)
    blit(img, T(name, F_B, 46, WHITE), cx, cy + 190, op=op)

# ----------------------------------------------------------------- kare
def frame(t):
    img = base(t)
    gl = newgl()
    series_tag(img, t)

    # S0 kanca (0 - 4.5)
    caption(img, [("RADYASYON HER ŞEYİN", WHITE), ("İÇİNDEN GEÇER Mİ?", AMBER)], t, 0.3, 4.4, y0=360, size=74)
    o0 = fade(t, 0.4, 1.0) * (1 - fade(t, 4.0, 4.5))
    if o0 > 0:
        r0 = 70 * (1 + 0.04 * math.sin(t * 4))
        gcircle(gl, 540, LANE_Y, r0 * 2.6, AMBER, 0.6 * o0)
        blit(img, NUC_SPR, 540, LANE_Y, op=o0, scale=r0 * 2 / 400)
        for k in range(12):
            ang = k * 2 * math.pi / 12 + 0.2
            r = 110 + ((t * 300 + k * 53) % 380)
            fo = o0 * (1 - (r - 110) / 380)
            col = [ALPHA_C, BETA_C, GAMMA_C][k % 3]
            gcircle(gl, 540 + r * math.cos(ang), LANE_Y + r * math.sin(ang), 26, col, 1.2 * fo)
            cv2.circle(img, (int(540 + r * math.cos(ang)), int(LANE_Y + r * math.sin(ang))), 11, scol(col, fo), -1, cv2.LINE_AA)
    if t > 3.2:
        text_in(img, "ASLINDA HAYIR.", F_B, 86, CYAN, 540, 1330, t, 3.2, op=1 - fade(t, 4.1, 4.5))

    # S1 uc tur (4.5 - 7.8)
    o1 = fade(t, 4.5, 5.0) * (1 - fade(t, 7.4, 7.8))
    caption(img, [("ÜÇ TEMEL TÜR,", WHITE), ("ÜÇ FARKLI ENGEL", AMBER)], t, 4.6, 7.8, y0=360, size=74)
    for i, (sym, nm, col) in enumerate([("α", "ALFA", ALPHA_C), ("β", "BETA", BETA_C), ("γ", "GAMA", GAMMA_C)]):
        sym_card(img, gl, 200 + 340 * i, 930, sym, nm, col, o1 * fade(t, 4.7 + 0.35 * i, 5.2 + 0.35 * i))

    # S2 alfa (7.8 - 16.8)
    if 7.6 < t < 17.0:
        so = fade(t, 7.8, 8.3) * (1 - fade(t, 16.4, 16.8))
        gtitle(img, t, 7.9, 16.8, "ALFA ", "α", ALPHA_C)
        text_in(img, "2 PROTON + 2 NÖTRON · AĞIR", F_SB, 44, WHITE, 540, 470, t, 9.9, op=so)
        emitter(img, gl, t, so)
        barriers(img, t, 7.9, (1, 0, 0), fade_out=16.8)
        for k, t0 in enumerate([9.6, 11.0, 12.4, 13.8, 15.2]):
            x, hit = flight(t, t0, EX + 50, PAPER_X - 50, 360)
            if x is not None:
                th = t0 + (PAPER_X - 50 - EX - 50) / 360
                fo = so * (1 - seg(t, th + 0.3, th + 0.9))
                alpha_spr(img, gl, x, LANE_Y + (k - 2) * 50, fo, s=1.5)
                stop_flash(gl, PAPER_X - 10, LANE_Y + (k - 2) * 50, t, th, ALPHA_C)
        text_in(img, "BİR KÂĞIT YAPRAĞI DURDURUR", F_B, 56, AMBER, 540, 1330, t, 13.2, op=so)
        text_in(img, "derinin dış katmanı da", F_M, 40, MUTED, 540, 1405, t, 14.6, op=so)

    # S3 beta (16.8 - 25.8)
    if 16.6 < t < 26.0:
        so = fade(t, 16.8, 17.3) * (1 - fade(t, 25.4, 25.8))
        gtitle(img, t, 16.9, 25.8, "BETA ", "β", BETA_C)
        text_in(img, "DAHA KÜÇÜK, DAHA HIZLI", F_SB, 44, WHITE, 540, 470, t, 18.7, op=so)
        emitter(img, gl, t, so)
        barriers(img, t, 16.9, (1, 1, 0), fade_out=25.8)
        for k, t0 in enumerate([18.8, 19.6, 20.4, 21.2, 22.0, 22.8, 23.6]):
            x, hit = flight(t, t0, EX + 40, METAL_X - 24, 760)
            if x is not None:
                th = t0 + (METAL_X - 24 - EX - 40) / 760
                fo = so * (1 - seg(t, th + 0.2, th + 0.7))
                beta_spr(img, gl, x, LANE_Y + ((k * 3) % 5 - 2) * 38, fo)
                stop_flash(gl, METAL_X - 14, LANE_Y + ((k * 3) % 5 - 2) * 38, t, th, BETA_C)
        text_in(img, "KÂĞIDI GEÇER", F_SB, 44, MUTED, 540, 1300, t, 20.6, op=so)
        text_in(img, "İNCE METAL LEVHA DURDURUR", F_B, 56, AMBER, 540, 1380, t, 22.3, op=so)

    # S4 gama (25.8 - 34.2)
    if 25.6 < t < 34.4:
        so = fade(t, 25.8, 26.3) * (1 - fade(t, 33.8, 34.2))
        gtitle(img, t, 25.9, 34.2, "GAMA ", "γ", GAMMA_C)
        text_in(img, "KÜTLESİZ · SAF ENERJİ", F_SB, 44, WHITE, 540, 470, t, 27.4, op=so)
        emitter(img, gl, t, so)
        barriers(img, t, 25.9, (1, 1, 1), fade_out=34.2)
        if t > 27.6:
            front = EX + 40 + (t - 27.6) * 520
            gamma_wave(img, gl, EX + 40, min(front, LEAD_X + 40), LANE_Y, t, so, decay_from=LEAD_X - 55)
        text_in(img, "KÂĞIDI VE METALİ GEÇER", F_SB, 44, MUTED, 540, 1320, t, 29.6, op=so)
        text_in(img, "KURŞUN YA DA KALIN BETON GEREKİR", F_B, 52, AMBER, 540, 1400, t, 31.0, op=so)

    # S5 alfa: icerisi / disarisi (34.2 - 42.0)
    if 34.0 < t < 42.2:
        so = fade(t, 34.2, 34.7) * (1 - fade(t, 41.6, 42.0))
        caption(img, [("AMA BİR AYRINTI ÖNEMLİ", WHITE)], t, 34.3, 42.0, y0=360, size=70)
        # sol: disarida
        cx1, cx2, cy = 290, 790, 900
        o_l = so * fade(t, 36.1, 36.6)
        o_r = so * fade(t, 38.3, 38.8)
        for cx, o, col, head, line1, line2 in [
            (cx1, o_l, GREEN, "DIŞARIDAN", "deri durdurur", "pek zarar vermez"),
            (cx2, o_r, RED, "İÇERİDEN", "solunur ya da yutulursa", "ciddi hasar verebilir")]:
            if o <= 0:
                continue
            ov = img.copy()
            cv2.rectangle(ov, (cx - 220, cy - 230), (cx + 220, cy + 250), (10, 18, 44), -1)
            cv2.addWeighted(ov, 0.85 * o, img, 1 - 0.85 * o, 0, dst=img)
            cv2.rectangle(img, (cx - 220, cy - 230), (cx + 220, cy + 250), scol(col, o), 4, cv2.LINE_AA)
            alpha_spr(img, gl, cx, cy - 90, o, s=1.6)
            blit(img, T(head, F_B, 52, col), cx, cy + 50, op=o)
            blit(img, T(line1, F_M, 34, WHITE, maxw=410), cx, cy + 125, op=o)
            blit(img, T(line2, F_M, 34, WHITE, maxw=410), cx, cy + 175, op=o)

    # S6 ozet (42.0 - 46.8)
    if 41.8 < t < 47.0:
        so = fade(t, 42.0, 42.5) * (1 - fade(t, 46.4, 46.8))
        caption(img, [("NE KADAR DELİCİ?", WHITE), ("NEREDEN GELİYOR?", AMBER)], t, 42.1, 46.8, y0=360, size=80)
        emitter(img, gl, t, so)
        barriers(img, t, 42.1, (1, 1, 1), fade_out=46.8)
        alpha_spr(img, gl, PAPER_X - 50, LANE_Y - 110, so, s=1.5)
        beta_spr(img, gl, METAL_X - 40, LANE_Y, so)
        gamma_wave(img, gl, EX + 40, LEAD_X + 40, LANE_Y + 110, t, so, amp=16, decay_from=LEAD_X - 55)

    note(img, t, 7.9, 46.8)
    apply_glow(img, gl)

    if t >= 46.8:
        img = source_card(img, t, 46.8, [
            "ABD EPA · Radiation Basics",
            "ABD NRC · Radiation Basics",
        ], ["Animasyon şematiktir, ölçekli değildir.", "Seslendirme yapay ses ile yapılmıştır."])
    return img

if __name__ == "__main__":
    main(frame, OUT, "kalkan", DUR)
