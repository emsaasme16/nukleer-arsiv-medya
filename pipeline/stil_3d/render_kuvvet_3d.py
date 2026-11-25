#!/usr/bin/env python3
"""3D: Cekirdek neden dagilmiyor? (cekirdek-neden-dagilmiyor.mp4) 1080x1920, 30 fps, 36,5 sn.
Zaman cizelgesi short2_cekirdek_ve_muz/render_kuvvet.py ile birebir ayni (video saniyesi).
Kullanim: python3 render_kuvvet_3d.py still 2.5 8.4 ... | render"""
import math
from common3d import *

NAME = "cekirdek-neden-dagilmiyor"
NFRAMES = 1095
CX, CY = 540, 900


def nucleon(F, x, y, z, r, proton=True, op=1.0, plus=True, ao=1.0):
    if op <= 0.01 or r <= 0.5:
        return
    col = WARM if proton else NEUT
    F.sphere(x, y, z, r, col, MAT_PLASTIC, alpha=op, glow=0.28, ao=ao)
    if proton and plus:
        F.plus(x, y, z, r, op)


def bond(F, p, q, op, t, rad=4.0):
    if op <= 0.01:
        return
    w = 0.75 + 0.25 * math.sin(t * 5 + p[0] * 0.01)
    F.rod(p, q, rad, scol(CYAN, 0.6 + 0.4 * w), MAT_GLOW, alpha=op)
    for k in (0.33, 0.66):
        m = (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k, p[2] + (q[2] - p[2]) * k)
        F.glow3(m[0], m[1], m[2], rad * 5, CYAN, 0.35 * op * w)


# cekirdek kumesi: (dx, dy, proton?) + 3D derinlik
CL = [(0, 0, 1), (-62, -30, 0), (60, -36, 1), (-8, -82, 1), (-64, 40, 1), (58, 34, 0),
      (4, 78, 1), (-112, -4, 0), (112, 4, 1), (52, -102, 0), (-58, 102, 0), (66, 104, 1)]
CLZ = []
for i, (dx, dy, p) in enumerate(CL):
    zz = math.sqrt(max(0.0, 135.0 ** 2 - dx * dx - dy * dy)) * 0.62
    CLZ.append(zz if i % 2 == 0 else -zz)
CL3 = np.array([(dx, dy, CLZ[i]) for i, (dx, dy, p) in enumerate(CL)], float)
BONDS = [(i, j) for i in range(len(CL)) for j in range(i + 1, len(CL))
         if np.linalg.norm(CL3[i] - CL3[j]) < 100]


def cluster(F, t, cx, cy, s, op, bop, spin=0.45):
    R = rot_y(t * spin) @ rot_x(0.35 * math.sin(t * 0.3))
    pts = []
    for i in range(len(CL)):
        j = 3 * math.sin(t * 6 + i * 1.7)
        v = R @ (CL3[i] + np.array([j, -j, 0]))
        pts.append((cx + v[0] * s, cy + v[1] * s, v[2] * s))
    for i, j in BONDS:
        bond(F, pts[i], pts[j], bop * op, t, rad=max(2.5, 5 * s))
    for i in range(len(CL)):
        ao = 0.78 + 0.22 * clamp01((pts[i][2] / s + 140) / 280)
        nucleon(F, pts[i][0], pts[i][1], pts[i][2], 44 * s, CL[i][2] == 1, op, plus=True, ao=ao)


# --------------------------------------------------------------- A: iki proton (0 - 9.6)
def scene_A(t):
    F = Frame(t, Cam(yaw=0.16 * math.sin(t * 0.33), pitch=-0.05 + 0.03 * math.sin(t * 0.21),
                     dolly=1.0 - 0.06 * smooth(seg(t, 0, 9.6)), pivot=(CX, CY, 0)))
    app = ease_out_back(seg(t, 0.3, 1.0))
    sep = 74.0
    shake = 0.0
    if t > 3.7:
        shake = 6 * math.sin(t * 38) * fade(t, 3.7, 4.0) * (1 - fade(t, 7.7, 7.9))
    sep += 210 * smooth(seg(t, 5.4, 7.2))
    sep -= 210 * ease_out_back(seg(t, 7.75, 8.35))
    sep = max(sep, 66)
    xl, xr = CX - sep + shake, CX + sep - shake
    rep = fade(t, 3.75, 4.2) * (1 - fade(t, 7.7, 8.0))
    if rep > 0:
        k = 0.7 + 0.3 * math.sin(t * 9)
        L = 120 + 25 * math.sin(t * 9)
        F.arrow3((xl - 80, CY, 0), (xl - 80 - L, CY, 0), 7, RED, MAT_GLOW, alpha=rep * (0.7 + 0.3 * k), head=3.0, head_len=40)
        F.arrow3((xr + 80, CY, 0), (xr + 80 + L, CY, 0), 7, RED, MAT_GLOW, alpha=rep * (0.7 + 0.3 * k), head=3.0, head_len=40)
        F.glow3(xl - 140, CY, 0, 70, RED, 0.6 * rep)
        F.glow3(xr + 140, CY, 0, 70, RED, 0.6 * rep)
    bo = fade(t, 7.85, 8.3)
    if bo > 0:
        bond(F, (xl, CY - 18, 0), (xr, CY - 18, 0), bo, t, 6)
        bond(F, (xl, CY + 18, 0), (xr, CY + 18, 0), bo, t, 6)
    nucleon(F, xl, CY, 0, 70 * app, True, min(1, app))
    nucleon(F, xr, CY, 0, 70 * app, True, min(1, app))
    lp = fade(t, 1.6, 2.2) * (1 - fade(t, 3.5, 3.8))
    if lp > 0:
        F.spr(pill("2 PROTON · İKİSİ DE ARTI (+) YÜKLÜ", F_SB, 34, WARM, WARM, padx=26, pady=10), CX, CY + 160, op=lp)
    F.caption([("ÇEKİRDEK NEDEN", WHITE), ("DAĞILMIYOR?", CYAN)], 0.2, 3.6, y0=360, size=96)
    F.caption([("İTER Mİ?", WHITE), ("EVET.", RED)], 3.75, 8.85, y0=1100, size=92)
    F.caption([("DAĞILIR MI?", WHITE), ("HAYIR.", CYAN)], 7.8, 8.85, y0=1330, size=92)
    if t > 3.75:
        F.caption([("AYNI YÜKLER", WHITE), ("BİRBİRİNİ İTER", RED)], 3.75, 7.7, y0=380, size=78)
    nd = ease_out_back(seg(t, 8.9, 9.3))
    if nd > 0:
        F.text("NEDEN?", F_B, 150, AMBER, 540, 420, op=min(1, nd), scale=0.8 + 0.2 * nd)
    return F


# --------------------------------------------------------------- B: guclu kuvvet + 100 kat (9.6 - 16)
def scene_B(t):
    F = Frame(t, Cam(yaw=0.12 * math.sin(t * 0.3), pitch=-0.08, dolly=1.0 - 0.05 * smooth(seg(t, 9.6, 16)),
                     pivot=(CX, 960, 0)))
    up = smooth(seg(t, 12.9, 13.6))
    s = (0.55 + 0.45 * ease_out_back(seg(t, 9.6, 10.4))) * (1 - 0.25 * up)
    cy = CY - 150 * up
    cluster(F, t, CX, cy, s, min(1, fade(t, 9.6, 10.0)), fade(t, 10.2, 11.0))
    F.caption([("GÜÇLÜ", CYAN), ("NÜKLEER KUVVET", WHITE)], 9.7, 16.3, y0=330, size=92)
    bp = fade(t, 13.0, 13.4)
    if bp > 0:
        x0, wmax = 110, 860
        y1, y2 = 1090, 1250
        F.text("ELEKTROMANYETİK İTME", F_SB, 34, RED, 540, y1 - 46, op=bp, maxw=860)
        F.text("GÜÇLÜ KUVVET", F_SB, 34, CYAN, 540, y2 - 46, op=bp, maxw=860)
        # 3D cubuk grafik: cam kanal + dolgu
        for yy in (y1, y2):
            F.box(x0 + wmax / 2, yy + 25, 0, wmax + 12, 62, 62, (60, 90, 150), MAT_GLOSS, alpha=0.22 * bp, r=12)
        F.box(x0 + 5, y1 + 25, 0, 10, 50, 50, RED, MAT_GLOW, alpha=bp, r=3)
        g = ease_out(seg(t, 13.4, 14.9))
        wg = max(10, wmax * g)
        F.box(x0 + wg / 2, y2 + 25, 0, wg, 50, 50, CYAN, ((0.8, 0.8, 0.8, 0.45), (0, 0, 0, 1)), alpha=bp, r=10)
        F.glow3(x0 + wg, y2 + 25, 0, 70, CYAN, 0.6 * bp)
        kp = ease_out_back(seg(t, 14.5, 15.0))
        if kp > 0:
            F.text("≈ 100 KAT GÜÇLÜ", F_B, 84, AMBER, 540, 1410, op=min(1, kp), scale=0.85 + 0.15 * kp)
    return F


# --------------------------------------------------------------- C: menzil (16 - 22.6)
RNG = np.random.default_rng(3)
EL = [(RNG.uniform(0, 6.28), RNG.uniform(0.5, 1.4), RNG.uniform(-1.2, 1.2), RNG.uniform(0, 3.1)) for _ in range(6)]


def scene_C(t):
    cam = Cam(yaw=0.18 * math.sin(t * 0.3 + 1), pitch=0.10 * math.sin(t * 0.25), pivot=(CX, CY, 0),
              dolly=1.0 - 0.05 * smooth(seg(t, 16, 22.6)))
    F = Frame(t, cam)
    ao = fade(t, 16.0, 16.6)
    R = 380
    # atom siniri: yari saydam cam kure + kesikli cember
    F.sphere(CX, CY, 0, R, (70, 120, 200), ((0.6, 0.8, 1.6, 0.0), (0, 0, 0, 1)), alpha=0.10 * ao)
    sx, sy, sc = F.p2(CX, CY, 0)
    Rs = R * sc
    for k in range(72):
        if k % 2 == 0:
            a0, a1 = 360 * k / 72, 360 * (k + 1) / 72
            cv2.ellipse(F.img, (int(sx), int(sy)), (int(Rs), int(Rs)), 0, a0, a1, scol((90, 140, 210), 0.8 * ao), 3, cv2.LINE_AA)
    for (ph, w, tilt, rot) in EL:
        a = ph + t * w
        rr = R * (0.55 + 0.4 * math.sin(ph * 3))
        v = rot_z(rot) @ rot_x(tilt) @ np.array([rr * math.cos(a), rr * math.sin(a), 0])
        F.sphere(CX + v[0], CY + v[1], v[2], 10, CYAN, MAT_GLOW, alpha=ao, glow=0.9, lo=True)
    F.sphere(CX, CY, 0, 7, AMBER, MAT_GLOW, alpha=ao, glow=1.2)
    F.glow3(CX, CY, 0, 50, AMBER, 0.8 * ao)
    rg = fade(t, 17.6, 18.2)
    if rg > 0:
        rr = 16 + 3 * math.sin(t * 6)
        F.torus(CX, CY, 0, rr, 0.12, CYAN, rot_x(math.pi / 2), MAT_GLOW, alpha=rg)

        def lab(img, rg=rg, sx=sx, sy=sy):
            cv2.line(img, (int(sx + 14), int(sy - 14)), (CX + 120, CY - 230), scol(CYAN, rg), 2, cv2.LINE_AA)
            blit(img, pill("GÜÇLÜ KUVVETİN ETKİ ALANI", F_SB, 32, CYAN, CYAN, padx=26, pady=10), CX + 120, CY - 262, op=rg)
        F.over(lab)
        dp = fade(t, 18.0, 18.6)

        def dim(img, dp=dp):
            ytop = int(sy - Rs - 40)
            cv2.line(img, (int(sx - Rs), ytop), (int(sx + Rs), ytop), scol(MUTED, dp), 2, cv2.LINE_AA)
            for xx in (sx - Rs, sx + Rs):
                cv2.line(img, (int(xx), ytop - 15), (int(xx), ytop + 15), scol(MUTED, dp), 2, cv2.LINE_AA)
            blit(img, T("ATOMUN ÇAPI", F_SB, 32, MUTED), int(sx), ytop - 40, op=dp)
        F.over(dim)
    F.caption([("MENZİLİ", WHITE), ("ÇOK KISA", CYAN)], 16.0, 17.55, y0=300, size=92)
    if t > 17.5:
        F.caption([("ATOM ÇAPININ", WHITE), ("≈ 1/100.000'İ", AMBER)], 17.6, 20.2, y0=1360, size=84)
    if t > 20.1:
        F.caption([("YALNIZCA", WHITE), ("ÇEKİRDEK BOYUTUNDA", CYAN)], 20.25, 22.8, y0=1360, size=80)
    return F


# --------------------------------------------------------------- D: cirt cirt benzetmesi (22.6 - 27.4)
def strip(F, y, hooks, op, t):
    x0, x1 = 170, 910
    col = CYAN if hooks else AMBER
    F.box((x0 + x1) / 2, y, 0, x1 - x0, 44, 70, (20, 46, 100), MAT_PLASTIC, alpha=op, r=10)
    F.box((x0 + x1) / 2, y, 0, x1 - x0 + 4, 46, 72, col, MAT_GLOW, alpha=0.18 * op, r=10)
    for k in range(20):
        x = x0 + 22 + k * 37
        for zz in (-18, 18):
            if hooks:   # alt yuzde kancalar: sap + halka
                F.rod((x, y + 22, zz), (x, y + 46, zz), 2.2, col, MAT_GLOW, alpha=op)
                F.add(torus_key(0.2), model((x + 8, y + 52, zz), (8, 8, 8), rot_x(math.pi / 2)), col, MAT_GLOW, op)
            else:       # ust yuzde ilmekler
                F.add(torus_key(0.12), model((x + 8, y - 22, zz), (12, 26, 12), rot_x(math.pi / 2)), col, MAT_GLOW, op)


def scene_D(t):
    F = Frame(t, Cam(yaw=0.22 * math.sin(t * 0.35), pitch=-0.18, pivot=(540, 960, 0)))
    o = fade(t, 22.6, 23.1)
    F.spr(pill("BENZETME", F_B, 38, AMBER, AMBER, padx=30, pady=12), 540, 320, op=o)
    close = smooth(seg(t, 24.1, 24.8)) * (1 - smooth(seg(t, 25.7, 26.6)))
    gap = 330 - 255 * close
    ya = 960 - gap / 2
    yb = 960 + gap / 2
    shake = 4 * math.sin(t * 30) * fade(t, 25.7, 25.9) * (1 - fade(t, 26.2, 26.5))
    strip(F, ya + shake, True, o, t)
    strip(F, yb, False, o, t)
    if close > 0.95:
        F.glow(540, 960, 300, CYAN, 0.12)
    F.caption([("CIRT CIRT BANT GİBİ", WHITE)], 22.7, 24.1, y0=470, size=78)
    if t > 24.0:
        F.caption([("YAKINKEN", WHITE), ("SIKI TUTAR", CYAN)], 24.15, 25.7, y0=1330, size=84)
    if t > 25.6:
        F.caption([("UZAKTAYKEN", WHITE), ("ETKİ YOK", MUTED)], 25.75, 27.7, y0=1330, size=84)
    return F


# --------------------------------------------------------------- E: kapanis (27.4 - 30.2)
def scene_E(t):
    F = Frame(t, Cam(yaw=0.14 * math.sin(t * 0.4), pitch=-0.06, dolly=1.0 - 0.08 * smooth(seg(t, 27.4, 36.5)),
                     pivot=(CX, 900, 0)))
    cluster(F, t, CX, 900, 1.05 + 0.03 * math.sin(t * 4), 1.0, 1.0, spin=0.6)
    F.caption([("ÇEKİRDEĞİ BİR ARADA", WHITE), ("TUTAN ŞEY BU", CYAN)], 27.5, 40, y0=330, size=82)
    F.text("GÜÇLÜ NÜKLEER KUVVET", F_B, 64, AMBER, 540, 1300, op=fade(t, 28.2, 28.8))
    return F


# --------------------------------------------------------------- birlestirme
SCENES = [(0.0, scene_A), (9.55, scene_B), (15.95, scene_C), (22.6, scene_D), (27.4, scene_E)]
XH = 0.22


def render_scene(fn, t, last=False):
    F = fn(t)
    F.series_tag()
    if last:
        source_card(F, 30.2, [
            "ABD Enerji Bakanlığı (DOE) · \"DOE Explains: The Strong Force\"",
            "güçlü kuvvet ≈ elektromanyetizmadan 100 kat güçlü",
            "menzil ≈ atom çapından 100.000 kat küçük",
        ], ["Cırt cırtlı bant yalnızca bir benzetmedir."])
    return F.finish()


def frame(t):
    idx = 0
    for k, (s, _) in enumerate(SCENES):
        if t >= s - XH:
            idx = k
    s, fn = SCENES[idx]
    last = idx == len(SCENES) - 1
    img = render_scene(fn, t, last)
    if idx > 0 and t < s + XH:
        prev = render_scene(SCENES[idx - 1][1], t)
        img = mix(prev, img, smooth((t - (s - XH)) / (2 * XH)))
    return img


if __name__ == "__main__":
    cli("render_kuvvet_3d", frame, NFRAMES, NAME)
