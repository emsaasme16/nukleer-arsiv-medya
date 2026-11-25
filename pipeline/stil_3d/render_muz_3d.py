#!/usr/bin/env python3
"""3D: Mit mi gercek mi? Muz radyoaktif midir? (muz-radyoaktif-mi.mp4) 1080x1920, 30 fps, 36,5 sn.
Zaman cizelgesi short2_cekirdek_ve_muz/render_muz.py ile birebir ayni.
Kullanim: python3 render_muz_3d.py still 3 8 ... | render"""
import math
from common3d import *

NAME = "muz-radyoaktif-mi"
NFRAMES = 1095
CX, CY = 540, 900
YEL = (255, 214, 64)
BAN_COL = (250, 200, 50)
STEM = (110, 96, 40)
TIPC = (70, 50, 25)
KCOL = (205, 190, 255)
ROT = math.radians(-18)


def banana_pts(n=60):
    out = []
    for i in range(n + 1):
        u = i / n
        ang = math.radians(205 + 130 * u)
        r = 0.78
        x = r * math.cos(ang)
        y = -r * math.sin(ang) - 0.45
        w = 0.20 * (math.sin(math.pi * u) ** 0.55) + 0.012
        nx, ny = math.cos(ang), -math.sin(ang)
        out.append((x, y, w, nx, ny))
    return out


BP = banana_pts()
U = 300.0          # 1 birim = 300 px (eski sprite d=600 ile ayni boyut)


def _rot2(x, y):
    return x * math.cos(ROT) - y * math.sin(ROT), x * math.sin(ROT) + y * math.cos(ROT)


def _banana_mesh(n=60, sides=28):
    pts = banana_pts(n)
    path, rad = [], []
    for x, y, w, nx, ny in pts:
        xr, yr = _rot2(x, y)
        path.append((xr * U, yr * U, 0.0))
        rad.append(w * U)
    return gl3d.mesh_tube(path, rad, sides=sides, flat=0.82)


BAN_HI = ("banana_hi", lambda: _banana_mesh(60, 28))
BAN_LO = ("banana_lo", lambda: _banana_mesh(14, 8))
MAT_BAN = ((0.45, 0.35, 0.7, 0.04), (0, 0, 0, 1))

# sap ve uc (birim koordinatta)
_x, _y, _w, _nx, _ny = BP[-1]
_tx, _ty = -_ny, _nx
STEM0 = _rot2(_x, _y)
STEM1 = _rot2(_x + _tx * 0.16 + 0.02, _y + _ty * 0.16 - 0.06)
TIP = _rot2(BP[0][0], BP[0][1])

# potasyum noktalari: muz yuzeyinde (on yuz), 3D
def _kdots():
    rr = np.random.default_rng(5)
    pts = []
    for k in range(70):
        i = int(rr.uniform(6, len(BP) - 6))
        x, y, w, nx, ny = BP[i]
        q = rr.uniform(-0.75, 0.75)
        px, py = x + nx * w * q, y + ny * w * q
        z = math.sqrt(max(0.0, 1 - q * q)) * w * 0.82 * 1.02
        xr, yr = _rot2(px, py)
        pts.append((xr * U, yr * U, z * U))
    return np.array(pts)


KDOTS = _kdots()
K40 = [7, 31, 52]


def ban_R(t, yaw_amp=0.45, ph=0.0):
    return rot_y(yaw_amp * math.sin(t * 0.55 + ph)) @ rot_x(0.12 * math.sin(t * 0.4 + ph))


def banana(F, x, y, s, op, glow=0.35, R=None, lo=False, z=0.0):
    if op <= 0.01 or s <= 0.005:
        return
    R = np.eye(3) if R is None else R
    F.add(BAN_LO if lo else BAN_HI, model((x, y, z), s, R), BAN_COL, MAT_BAN, op)
    if not lo:
        p0 = R @ np.array([STEM0[0] * U, STEM0[1] * U, 0]) * s
        p1 = R @ np.array([STEM1[0] * U, STEM1[1] * U, 0]) * s
        F.rod((x + p0[0], y + p0[1], z + p0[2]), (x + p1[0], y + p1[1], z + p1[2]), 0.025 * U * s, STEM, MAT_MATTE, op)
        F.sphere(x + p1[0], y + p1[1], z + p1[2], 0.028 * U * s, (80, 60, 30), MAT_MATTE, op, lo=True)
        tp = R @ np.array([TIP[0] * U, TIP[1] * U, 0]) * s
        F.sphere(x + tp[0], y + tp[1], z + tp[2], 0.03 * U * s, TIPC, MAT_MATTE, op, lo=True)
        F.glow3(x, y + 40 * s, z, 150 * s, YEL, glow * 0.4 * op)


# --------------------------------------------------------------- A (0 - 6.5)
def scene_A(t):
    F = Frame(t, Cam(yaw=0.10 * math.sin(t * 0.4), pitch=-0.05, dolly=1 - 0.05 * smooth(seg(t, 0, 6.5)), pivot=(CX, CY, 0)))
    bp = ease_out_back(seg(t, 0.3, 1.0))
    bob = 8 * math.sin(t * 2.0)
    banana(F, CX, CY + bob, 1.25 * bp, min(1, bp), R=ban_R(t))
    o = fade(t, 0.3, 0.8)
    F.spr(pill("MİT Mİ, GERÇEK Mİ?", F_B, 44, AMBER, AMBER, padx=34, pady=14), 540, 340, op=o)
    F.caption([("MUZ", WHITE), ("RADYOAKTİF Mİ?", YEL)], 2.15, 6.6, y0=470, size=104)
    st = ease_out_back(seg(t, 4.8, 5.2))
    if st > 0:
        F.spr(pill("EVET, AMA ÇOK AZ", F_B, 66, CYAN, CYAN, padx=40, pady=20, fill_a=0.92), 540, 1320,
              op=min(1, st), scale=1.25 - 0.25 * min(1, st))
    return F


# --------------------------------------------------------------- B (6.5 - 12.4)
def scene_B(t):
    F = Frame(t, Cam(yaw=0.08 * math.sin(t * 0.3), pitch=-0.04, pivot=(CX, CY, 0)))
    s = 1.5
    R = ban_R(t, 0.28)
    banana(F, CX, CY, s, fade(t, 6.4, 6.8), glow=0.2, R=R)
    dp = fade(t, 7.2, 8.4)
    hl = fade(t, 9.0, 9.5)
    rings = []
    for i, p in enumerate(KDOTS):
        if i * 0.012 + 7.2 > t:
            continue
        v = R @ p * s
        x, y, z = CX + v[0], CY + v[1], v[2]
        if i in K40 and hl > 0:
            pu = 0.75 + 0.25 * math.sin(t * 7 + i)
            F.sphere(x, y, z + 6, 13, AMBER, MAT_GLOW, alpha=hl, glow=1.0 * pu)
            F.glow3(x, y, z, 70 * pu, AMBER, 0.9 * hl)
            rings.append(F.p2(x, y, z))
        else:
            F.sphere(x, y, z + 3, 9, KCOL, MAT_GLOSS, alpha=dp * (1 - 0.45 * hl), lo=True)
    if rings and hl > 0:
        def rg(img, rings=rings):
            for (px, py, sc) in rings:
                for k in range(2):
                    q = ((t - 9.0) / 1.2 + k / 2.0) % 1.0
                    cv2.circle(img, (int(px), int(py)), int((16 + 60 * q) * sc), scol(AMBER, hl * (1 - q) * 0.8), 2, cv2.LINE_AA)
        F.over(rg)
    F.caption([("MUZ POTASYUM", WHITE), ("AÇISINDAN ZENGİN", YEL)], 6.7, 9.0, y0=380, size=86)
    if t > 8.9:
        F.caption([("KÜÇÜK BİR KISMI", WHITE), ("RADYOAKTİF", AMBER)], 9.0, 12.6, y0=380, size=86)
    lg = fade(t, 7.4, 8.0)
    F.spr(pill("POTASYUM", F_SB, 34, KCOL, (150, 140, 230), padx=24, pady=10), 540, 1330, op=lg)
    lk = fade(t, 11.2, 11.7)
    F.spr(pill("POTASYUM-40 (RADYOAKTİF)", F_SB, 34, AMBER, AMBER, padx=24, pady=10), 540, 1420, op=lk)
    return F


# --------------------------------------------------------------- C (12.4 - 16.7)
def scene_C(t):
    F = Frame(t, Cam(yaw=0.10 * math.sin(t * 0.35), pitch=-0.05, pivot=(CX, 900, 0)))
    bp = ease_out_back(seg(t, 12.5, 13.1))
    banana(F, CX, 700, 0.8 * bp, min(1, bp), R=ban_R(t, 0.6))
    F.caption([("1 MUZ YEMEK", WHITE)], 12.55, 16.9, y0=380, size=92)
    cp = fade(t, 13.4, 13.8)
    if cp > 0:
        v = 0.1 * ease_out(seg(t, 13.6, 15.2))
        txt = "≈ %s µSv" % ("%.2f" % v).replace(".", ",")
        if t >= 15.2:
            txt = "≈ 0,1 µSv"
        F.glow(540, 1080, 220, CYAN, 0.25 * cp)
        F.text(txt, F_B, 150, CYAN, 540, 1080, op=cp)
        F.text("(0,01 milirem) DOZ", F_SB, 44, MUTED, 540, 1210, op=fade(t, 15.0, 15.5))
    return F


# --------------------------------------------------------------- D (16.7 - 21.7)
def scene_D(t):
    F = Frame(t, Cam(yaw=0.06 * math.sin(t * 0.3), pitch=-0.22, pivot=(540, 973, 0)))
    F.caption([("ABD'DE BİR GÜNDE", WHITE), ("DOĞAL RADYASYON", CYAN)], 16.9, 21.9, y0=340, size=82)
    p = smooth(seg(t, 17.4, 20.0))
    n = int(round(100 * p))
    S = 74
    x0 = 540 - 4.5 * S
    y0 = 640
    s0 = 72 / 600.0
    dots = []
    for k in range(100):
        r, c = divmod(k, 10)
        x, y = x0 + c * S, y0 + r * S
        if k < n:
            pop = ease_out_back(clamp01((p * 100 - k) / 3.0))
            F.add(BAN_LO, model((x, y, 0), s0 * max(0.05, pop), ban_R(t, 0.5, k * 0.7)), BAN_COL, MAT_BAN, 1.0)
        else:
            dots.append(F.p2(x, y, 0))
    do = fade(t, 16.8, 17.3)
    for (px, py, sc) in dots:
        cv2.circle(F.img, (int(px), int(py)), 3, scol((70, 100, 160), do), -1, cv2.LINE_AA)
    k2 = ease_out_back(seg(t, 20.0, 20.5))
    if k2 > 0.01:
        F.glow(540, 1440, 200, YEL, 0.25 * min(1, k2))
        F.text("≈ 100 MUZ", F_B, 118, YEL, 540, 1440, op=min(1, k2), scale=0.8 + 0.2 * k2)
    return F


# --------------------------------------------------------------- E (21.7 - 24.9)
def scene_E(t):
    F = Frame(t, Cam(yaw=0.05 * math.sin(t * 0.3), pitch=-0.2, pivot=(540, 870, 0)))
    F.caption([("1 GÖĞÜS RÖNTGENİ", WHITE)], 21.95, 25.1, y0=340, size=88)
    F.text("(≈ 10 milirem)", F_SB, 40, MUTED, 540, 430, op=fade(t, 22.3, 22.8))
    p = smooth(seg(t, 22.2, 24.0))
    n = int(round(1000 * p))
    COLS, S = 40, 21
    x0 = 540 - (COLS - 1) / 2 * S
    y0 = 560
    s0 = 17.0 / 470.0
    dots = []
    Rb = rot_z(math.radians(-2))
    for k in range(1000):
        r, c = divmod(k, COLS)
        x, y = x0 + c * S, y0 + r * S
        if k < n:
            F.add(BAN_LO, model((x, y, 0), s0, Rb), BAN_COL, MAT_BAN, 1.0)
        else:
            dots.append(F.p2(x, y, 0))
    do = fade(t, 21.8, 22.2)
    for (px, py, sc) in dots:
        cv2.circle(F.img, (int(px), int(py)), 2, scol((70, 100, 160), do), -1, cv2.LINE_AA)
    k2 = ease_out_back(seg(t, 24.0, 24.4))
    if k2 > 0.01:
        F.glow(540, 1300, 200, YEL, 0.25 * min(1, k2))
        F.text("≈ 1.000 MUZ", F_B, 118, YEL, 540, 1300, op=min(1, k2), scale=0.8 + 0.2 * k2)
    return F


# --------------------------------------------------------------- F (24.9 - 30.2)
def scene_F(t):
    F = Frame(t, Cam(yaw=0.12 * math.sin(t * 0.35), pitch=-0.05, dolly=1 - 0.06 * smooth(seg(t, 24.9, 36.5)), pivot=(CX, 820, 0)))
    banana(F, CX, 820, 1.05, fade(t, 24.9, 25.4), R=ban_R(t, 0.5))
    F.caption([("RADYOAKTİF Mİ?", WHITE), ("EVET.", AMBER)], 25.05, 40, y0=330, size=92)
    r = ease_out_back(seg(t, 27.4, 27.9))
    if r > 0:
        F.text("RİSK Mİ?", F_B, 92, WHITE, 540, 1240, op=min(1, r))
        F.text("HAYIR.", F_B, 92, CYAN, 540, 1345, op=min(1, r), scale=0.85 + 0.15 * r)
    return F


SCENES = [(0.0, scene_A), (6.45, scene_B), (12.4, scene_C), (16.7, scene_D), (21.75, scene_E), (24.9, scene_F)]
XH = 0.2


def render_scene(fn, t, last=False):
    F = fn(t)
    F.series_tag()
    if last:
        source_card(F, 30.2, [
            "ABD EPA · \"Natural Radioactivity in Food\"",
            "1 muz ≈ 0,1 µSv · ≈100 muz = ABD'de 1 günlük doğal doz",
            "ABD NRC · \"Doses in Our Daily Lives\"",
            "muzda potasyum-40 · göğüs röntgeni ≈ 10 milirem",
        ], ["1.000 muz: NRC (10 mrem) ÷ EPA (0,01 mrem) hesabı"])
    return F.finish()


def frame(t):
    idx = 0
    for k, (s, _) in enumerate(SCENES):
        if t >= s - XH:
            idx = k
    s, fn = SCENES[idx]
    img = render_scene(fn, t, idx == len(SCENES) - 1)
    if idx > 0 and t < s + XH:
        prev = render_scene(SCENES[idx - 1][1], t)
        img = mix(prev, img, smooth((t - (s - XH)) / (2 * XH)))
    return img


if __name__ == "__main__":
    cli("render_muz_3d", frame, NFRAMES, NAME)
