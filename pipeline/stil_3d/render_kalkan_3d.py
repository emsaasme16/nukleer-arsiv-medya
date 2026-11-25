#!/usr/bin/env python3
"""3D: Radyasyon neyle durur? (radyasyon-neyle-durur.mp4) 1080x1920, 30 fps, 52,5 sn.
Zaman cizelgesi short3_stok/render_kalkan.py ile birebir ayni.
Kullanim: python3 render_kalkan_3d.py still 3 10 ... | render"""
import math
from common3d import *

NAME = "radyasyon-neyle-durur"
NFRAMES = 1575
LANE_Y = 960
EX = 150
PAPER_X, METAL_X, LEAD_X = 400, 620, 850
ALPHA_C = (255, 96, 96)
BETA_C = (80, 190, 255)
GAMMA_C = (190, 120, 255)

MAT_PAPER = ((0.15, 0.1, 0.45, 0.06), (0, 0, 0, 1))
MAT_ALU = ((1.1, 0.55, 0.7, 0.0), (0, 0, 0.85, 1))
MAT_LEAD = ((0.45, 0.25, 0.5, 0.0), (0, 0, 0.5, 1))

# kamera anahtar kareleri: (t, yaw, pitch, dolly)
CAMK = [(0, 0.0, -0.04, 1.0), (4.3, 0.0, -0.04, 0.97), (4.6, 0.0, 0.0, 1.0), (7.6, 0.0, 0.0, 0.98),
        (8.3, -0.30, -0.15, 0.98), (16.6, -0.26, -0.12, 0.95), (17.2, -0.30, -0.15, 0.98), (25.6, -0.26, -0.12, 0.95),
        (26.2, -0.30, -0.15, 0.98), (34.0, -0.24, -0.12, 0.95), (34.6, 0.0, 0.0, 1.0), (41.8, 0.0, 0.0, 0.97),
        (42.4, -0.30, -0.15, 0.98), (46.8, -0.24, -0.12, 0.96), (60, -0.24, -0.12, 0.96)]


def cam_at(t):
    for (t0, y0, p0, d0), (t1, y1, p1, d1) in zip(CAMK, CAMK[1:]):
        if t <= t1:
            u = ease_in_out(seg(t, t0, t1))
            yaw, pit, dol = y0 + (y1 - y0) * u, p0 + (p1 - p0) * u, d0 + (d1 - d0) * u
            break
    yaw += 0.03 * math.sin(t * 0.4)
    pit += 0.015 * math.sin(t * 0.33)
    return Cam(yaw=yaw, pitch=pit, dolly=dol, pivot=(520, LANE_Y, 0))


def gtitle(F, t0, t1, name, sym, col):
    t = F.t
    ex = 1 - fade(t, t1 - 0.35, t1)
    p = ease_out(seg(t, t0, t0 + 0.6))
    if p <= 0 or ex <= 0:
        return
    a = T(name, F_B, 96, col)
    b = T(sym, F_GR, 96, col)
    wa, wb = a[1].shape[1], b[1].shape[1]
    x0 = 540 - (wa + wb - 60) / 2
    y = 360 + (1 - p) * 36
    F.spr(a, x0 + wa / 2, y, op=p * ex)
    F.spr(b, x0 + wa + wb / 2 - 40, y + 4, op=p * ex)


# ----------------------------------------------------------------- cizimler
def emitter(F, t, op):
    if op <= 0:
        return
    r = 46 + 4 * math.sin(t * 3)
    F.sphere(EX, LANE_Y, 0, r, AMBER, ((0.7, 0.7, 1.0, 0.35), (0, 0, 0, 1)), alpha=op, glow=0.8)
    F.glow3(EX, LANE_Y, 0, r * 2.6, AMBER, 0.5 * op)


def barrier(F, x, w, h, col, mat, label, op, sub=None, d=280):
    if op <= 0:
        return
    F.box(x, LANE_Y, 0, w, h, d, col, mat, alpha=op, r=min(4, w * 0.3))
    sx, sy, sc = F.p2(x, LANE_Y + h / 2, d / 2)
    F.text(label, F_SB, 32, WHITE, sx, sy + 50, op=op, maxw=260)
    if sub:
        F.text(sub, F_M, 26, MUTED, sx, sy + 92, op=op, maxw=260)


def barriers(F, t, t0, which=(1, 1, 1), fade_out=None):
    o = fade(t, t0, t0 + 0.6)
    if fade_out:
        o *= 1 - fade(t, fade_out - 0.4, fade_out)
    rise = 1 - ease_out(seg(t, t0, t0 + 0.7))
    if which[0]:
        barrier(F, PAPER_X, 8, 330 * (1 - 0.3 * rise), (238, 236, 226), MAT_PAPER, "KÂĞIT", o)
    if which[1]:
        barrier(F, METAL_X, 24, 330 * (1 - 0.3 * rise), (176, 186, 200), MAT_ALU, "METAL LEVHA", o, "ör. alüminyum")
    if which[2]:
        barrier(F, LEAD_X, 110, 360 * (1 - 0.3 * rise), (78, 84, 98), MAT_LEAD, "KURŞUN", o, "ya da kalın beton", d=300)


def alpha_spr(F, x, y, op, s=1.0, z=0.0):
    if op <= 0.01:
        return
    F.glow3(x, y, z, 46 * s, ALPHA_C, 0.8 * op)
    R = rot_y(F.t * 2.2 + x * 0.01) @ rot_x(F.t * 1.3)
    for (dx, dy, dz), prot in [((-1, -1, 1), 1), ((1, -1, -1), 0), ((-1, 1, -1), 0), ((1, 1, 1), 1)]:
        v = R @ np.array([dx, dy, dz]) * 8.5 * s
        F.sphere(x + v[0], y + v[1], z + v[2], 12.5 * s, WARM if prot else NEUT, MAT_PLASTIC, alpha=op, lo=True)


def beta_spr(F, x, y, op, trail=True):
    if op <= 0.01:
        return
    F.sphere(x, y, 0, 9, BETA_C, MAT_GLOW, alpha=op, glow=1.2)
    if trail:
        F.rod((x - 150, y, 0), (x - 10, y, 0), 2.5, BETA_C, MAT_GLOW, alpha=0.45 * op)
        for k in range(1, 5):
            F.glow3(x - 32 * k, y, 0, 22 - 3 * k, BETA_C, 0.5 * op * (1 - k / 5))


def gamma_wave(F, x0, x1, y, t, op, amp=22, decay_from=None):
    if op <= 0 or x1 <= x0:
        return
    pts = []
    for x in range(int(x0), int(x1), 6):
        a = amp
        if decay_from is not None and x > decay_from:
            a = amp * math.exp(-(x - decay_from) / 28)
        ph = (x - t * 900) / 18
        pts.append((x, y + a * math.sin(ph), 10 * math.cos(ph) * a / amp))
    for p, q in zip(pts, pts[1:]):
        F.rod(p, q, 3.2, GAMMA_C, MAT_GLOW, alpha=op)
    for p in pts[::4]:
        F.glow3(p[0], p[1], p[2], 16, GAMMA_C, 0.5 * op)


def flight(t, t0, x0, x1, speed):
    if t < t0:
        return None, False
    x = x0 + (t - t0) * speed
    return (min(x, x1), x >= x1)


def stop_flash(F, x, y, t, t_hit, col):
    if t_hit is None or t < t_hit:
        return
    k = 1 - seg(t, t_hit, t_hit + 0.6)
    if k > 0:
        F.glow3(x, y, 0, 90 * (1 - k) + 30, col, 1.2 * k)


def sym_card(F, cx, cy, sym, name, col, op):
    if op <= 0:
        return
    t = F.t
    F.glow(cx, cy, 150, col, 0.45 * op)
    F.torus(cx, cy, 0, 120, 0.045, col, rot_y(0.35 * math.sin(t * 1.2 + cx)) @ rot_x(math.pi / 2), MAT_GLOW, alpha=op)
    F.sphere(cx, cy, -40, 70, scol(col, 0.35), ((0.5, 0.5, 1.2, 0.2), (0, 0, 0, 1)), alpha=0.5 * op)
    F.text(sym, F_GR, 120, col, cx, cy - 4, op=op)
    F.text(name, F_B, 46, WHITE, cx, cy + 190, op=op)


def panel(F, cx, cy, col, o, tilt):
    R = rot_y(tilt)
    F.box(cx, cy + 10, -10, 440, 480, 24, (14, 24, 56), ((0.6, 0.6, 0.6, 0.0), (0, 0, 0, 1)), alpha=0.9 * o, R=R, r=10)
    corners = [R @ np.array(v) for v in [(-220, -230, 3), (220, -230, 3), (220, 250, 3), (-220, 250, 3)]]
    pts = [F.p2(cx + v[0], cy + v[1], v[2] + 2) for v in corners]

    def edge(img, pts=pts):
        arr = np.array([(int(p[0]), int(p[1])) for p in pts], np.int32)
        cv2.polylines(img, [arr], True, scol(col, o), 4, cv2.LINE_AA)
    F.over(edge)
    return F.p2(cx, cy, 2)


# ----------------------------------------------------------------- kare
def frame_F(t):
    F = Frame(t, cam_at(t))

    # S0 kanca (0 - 4.5)
    F.caption([("RADYASYON HER ŞEYİN", WHITE), ("İÇİNDEN GEÇER Mİ?", AMBER)], 0.3, 4.4, y0=360, size=74)
    o0 = fade(t, 0.4, 1.0) * (1 - fade(t, 4.0, 4.5))
    if o0 > 0:
        r0 = 70 * (1 + 0.04 * math.sin(t * 4))
        F.sphere(540, LANE_Y, 0, r0, AMBER, ((0.7, 0.7, 1.0, 0.35), (0, 0, 0, 1)), alpha=o0, glow=0.9)
        Rr = rot_x(0.5 + 0.2 * math.sin(t * 0.5)) @ rot_y(t * 0.3)
        for k in range(12):
            ang = k * 2 * math.pi / 12 + 0.2
            r = 110 + ((t * 300 + k * 53) % 380)
            fo = o0 * (1 - (r - 110) / 380)
            col = [ALPHA_C, BETA_C, GAMMA_C][k % 3]
            v = Rr @ np.array([r * math.cos(ang), r * math.sin(ang), 0]) if k % 2 else np.array([r * math.cos(ang), r * math.sin(ang), 0])
            F.sphere(540 + v[0], LANE_Y + v[1], v[2], 11, col, MAT_GLOW, alpha=fo, glow=1.2, lo=True)
    if t > 3.2:
        F.text_in("ASLINDA HAYIR.", F_B, 86, CYAN, 540, 1330, 3.2, op=1 - fade(t, 4.1, 4.5))

    # S1 uc tur (4.5 - 7.8)
    o1 = fade(t, 4.5, 5.0) * (1 - fade(t, 7.4, 7.8))
    F.caption([("ÜÇ TEMEL TÜR,", WHITE), ("ÜÇ FARKLI ENGEL", AMBER)], 4.6, 7.8, y0=360, size=74)
    for i, (sym, nm, col) in enumerate([("α", "ALFA", ALPHA_C), ("β", "BETA", BETA_C), ("γ", "GAMA", GAMMA_C)]):
        sym_card(F, 200 + 340 * i, 930, sym, nm, col, o1 * fade(t, 4.7 + 0.35 * i, 5.2 + 0.35 * i))

    # S2 alfa (7.8 - 16.8)
    if 7.6 < t < 17.0:
        so = fade(t, 7.8, 8.3) * (1 - fade(t, 16.4, 16.8))
        gtitle(F, 7.9, 16.8, "ALFA ", "α", ALPHA_C)
        F.text_in("2 PROTON + 2 NÖTRON · AĞIR", F_SB, 44, WHITE, 540, 470, 9.9, op=so)
        emitter(F, t, so)
        barriers(F, t, 7.9, (1, 0, 0), fade_out=16.8)
        for k, t0 in enumerate([9.6, 11.0, 12.4, 13.8, 15.2]):
            x, hit = flight(t, t0, EX + 50, PAPER_X - 50, 360)
            if x is not None:
                th = t0 + (PAPER_X - 50 - EX - 50) / 360
                fo = so * (1 - seg(t, th + 0.3, th + 0.9))
                alpha_spr(F, x, LANE_Y + (k - 2) * 50, fo, s=1.5)
                stop_flash(F, PAPER_X - 10, LANE_Y + (k - 2) * 50, t, th, ALPHA_C)
        F.text_in("BİR KÂĞIT YAPRAĞI DURDURUR", F_B, 56, AMBER, 540, 1330, 13.2, op=so)
        F.text_in("derinin dış katmanı da", F_M, 40, MUTED, 540, 1405, 14.6, op=so)

    # S3 beta (16.8 - 25.8)
    if 16.6 < t < 26.0:
        so = fade(t, 16.8, 17.3) * (1 - fade(t, 25.4, 25.8))
        gtitle(F, 16.9, 25.8, "BETA ", "β", BETA_C)
        F.text_in("DAHA KÜÇÜK, DAHA HIZLI", F_SB, 44, WHITE, 540, 470, 18.7, op=so)
        emitter(F, t, so)
        barriers(F, t, 16.9, (1, 1, 0), fade_out=25.8)
        for k, t0 in enumerate([18.8, 19.6, 20.4, 21.2, 22.0, 22.8, 23.6]):
            x, hit = flight(t, t0, EX + 40, METAL_X - 24, 760)
            if x is not None:
                th = t0 + (METAL_X - 24 - EX - 40) / 760
                fo = so * (1 - seg(t, th + 0.2, th + 0.7))
                yy = LANE_Y + ((k * 3) % 5 - 2) * 38
                beta_spr(F, x, yy, fo, trail=not hit)
                stop_flash(F, METAL_X - 14, yy, t, th, BETA_C)
        F.text_in("KÂĞIDI GEÇER", F_SB, 44, MUTED, 540, 1300, 20.6, op=so)
        F.text_in("İNCE METAL LEVHA DURDURUR", F_B, 56, AMBER, 540, 1380, 22.3, op=so)

    # S4 gama (25.8 - 34.2)
    if 25.6 < t < 34.4:
        so = fade(t, 25.8, 26.3) * (1 - fade(t, 33.8, 34.2))
        gtitle(F, 25.9, 34.2, "GAMA ", "γ", GAMMA_C)
        F.text_in("KÜTLESİZ · SAF ENERJİ", F_SB, 44, WHITE, 540, 470, 27.4, op=so)
        emitter(F, t, so)
        barriers(F, t, 25.9, (1, 1, 1), fade_out=34.2)
        if t > 27.6:
            front = EX + 40 + (t - 27.6) * 520
            gamma_wave(F, EX + 40, min(front, LEAD_X + 40), LANE_Y, t, so, decay_from=LEAD_X - 55)
        F.text_in("KÂĞIDI VE METALİ GEÇER", F_SB, 44, MUTED, 540, 1320, 29.6, op=so)
        F.text_in("KURŞUN YA DA KALIN BETON GEREKİR", F_B, 52, AMBER, 540, 1400, 31.0, op=so)

    # S5 alfa: icerisi / disarisi (34.2 - 42.0)
    if 34.0 < t < 42.2:
        so = fade(t, 34.2, 34.7) * (1 - fade(t, 41.6, 42.0))
        F.caption([("AMA BİR AYRINTI ÖNEMLİ", WHITE)], 34.3, 42.0, y0=360, size=70)
        cx1, cx2, cy = 290, 790, 900
        o_l = so * fade(t, 36.1, 36.6)
        o_r = so * fade(t, 38.3, 38.8)
        for cx, o, col, head, line1, line2, tilt in [
                (cx1, o_l, GREEN, "DIŞARIDAN", "deri durdurur", "pek zarar vermez", 0.12),
                (cx2, o_r, RED, "İÇERİDEN", "solunur ya da yutulursa", "ciddi hasar verebilir", -0.12)]:
            if o <= 0:
                continue
            px, py, sc = panel(F, cx, cy, col, o, tilt)
            alpha_spr(F, cx, cy - 90, o, s=1.6, z=40)
            F.text(head, F_B, 52, col, px, py + 50, op=o)
            F.text(line1, F_M, 34, WHITE, px, py + 125, op=o, maxw=410)
            F.text(line2, F_M, 34, WHITE, px, py + 175, op=o, maxw=410)

    # S6 ozet (42.0 - 46.8)
    if 41.8 < t < 47.0:
        so = fade(t, 42.0, 42.5) * (1 - fade(t, 46.4, 46.8))
        F.caption([("NE KADAR DELİCİ?", WHITE), ("NEREDEN GELİYOR?", AMBER)], 42.1, 46.8, y0=360, size=80)
        emitter(F, t, so)
        barriers(F, t, 42.1, (1, 1, 1), fade_out=46.8)
        alpha_spr(F, PAPER_X - 50, LANE_Y - 110, so, s=1.5)
        beta_spr(F, METAL_X - 40, LANE_Y, so, trail=False)
        gamma_wave(F, EX + 40, LEAD_X + 40, LANE_Y + 110, t, so, amp=16, decay_from=LEAD_X - 55)

    F.series_tag()
    if t >= 46.8:
        source_card(F, 46.8, [
            "ABD EPA · Radiation Basics",
            "ABD NRC · Radiation Basics",
        ], ["Seslendirme yapay ses ile yapılmıştır."])
    return F


def frame(t):
    return frame_F(t).finish()


if __name__ == "__main__":
    cli("render_kalkan_3d", frame, NFRAMES, NAME)
