#!/usr/bin/env python3
"""Short: Cekirdek neden dagilmiyor? 1080x1920, 30 fps. Zamanlar video saniyesi (ses +0.5 sn kaydirildi)."""
import math
from common import *

OUT = "/home/claude/s2/v1"
DUR = 36.5
CX, CY = 540, 900

# --------------------------------------------------------------- sprite'lar
P_SPR = sphere_sprite(WARM, 300, rim=(255, 210, 120), spec=0.5)
N_SPR = sphere_sprite(NEUT, 300, rim=(200, 215, 240), spec=0.45)

def nucleon(img, gl, x, y, r, proton=True, op=1.0, plus=True):
    if op <= 0.01:
        return
    gcircle(gl, x, y, r * 1.9, WARM if proton else NEUT, 0.35 * op)
    blit(img, P_SPR if proton else N_SPR, x, y, op=op, scale=2 * r / 300.0)
    if proton and plus:
        k = max(2, int(r * 0.11))
        a = int(r * 0.42)
        cv2.line(img, (int(x - a), int(y)), (int(x + a), int(y)), scol(WHITE, op), k, cv2.LINE_AA)
        cv2.line(img, (int(x), int(y - a)), (int(x), int(y + a)), scol(WHITE, op), k, cv2.LINE_AA)

def bond(img, gl, p, q, op, t, th=7):
    if op <= 0.01:
        return
    w = 0.75 + 0.25 * math.sin(t * 5 + p[0] * 0.01)
    cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), scol(BLUE, op * w), th, cv2.LINE_AA)
    cv2.line(gl, (int(p[0] / 4), int(p[1] / 4)), (int(q[0] / 4), int(q[1] / 4)), scol(CYAN, op), 2, cv2.LINE_AA)

# cekirdek kumesi: (dx, dy, proton?)
CL = [(0, 0, 1), (-62, -30, 0), (60, -36, 1), (-8, -82, 1), (-64, 40, 1), (58, 34, 0),
      (4, 78, 1), (-112, -4, 0), (112, 4, 1), (52, -102, 0), (-58, 102, 0), (66, 104, 1)]
BONDS = [(i, j) for i in range(len(CL)) for j in range(i + 1, len(CL))
         if math.hypot(CL[i][0] - CL[j][0], CL[i][1] - CL[j][1]) < 92]

def cluster(img, gl, t, cx, cy, s, op, bop):
    pts = []
    for i, (dx, dy, p) in enumerate(CL):
        j = 3 * math.sin(t * 6 + i * 1.7)
        pts.append((cx + (dx + j) * s, cy + (dy - j) * s))
    for i, j in BONDS:
        bond(img, gl, pts[i], pts[j], bop * op, t, th=max(3, int(7 * s)))
    order = sorted(range(len(CL)), key=lambda i: CL[i][1])
    for i in order:
        nucleon(img, gl, pts[i][0], pts[i][1], 44 * s, CL[i][2] == 1, op, plus=True)

# --------------------------------------------------------------- A: iki proton (0 - 9.6)
def scene_A(t):
    img = base(t)
    gl = newgl()
    app = ease_out_back(seg(t, 0.3, 1.0))
    sep = 74.0
    shake = 0.0
    if t > 3.7:
        shake = 6 * math.sin(t * 38) * fade(t, 3.7, 4.0) * (1 - fade(t, 7.7, 7.9))
    sep += 210 * smooth(seg(t, 5.4, 7.2))                       # "dagilmali"
    sep -= 210 * ease_out_back(seg(t, 7.75, 8.35))             # "ama dagilmiyor"
    sep = max(sep, 66)
    xl, xr = CX - sep + shake, CX + sep - shake
    rep = fade(t, 3.75, 4.2) * (1 - fade(t, 7.7, 8.0))
    if rep > 0:
        k = 0.7 + 0.3 * math.sin(t * 9)
        L = 120 + 25 * math.sin(t * 9)
        arrow(img, (xl - 80, CY), (xl - 80 - L, CY), scol(RED, rep * k), 12, 0.35)
        arrow(img, (xr + 80, CY), (xr + 80 + L, CY), scol(RED, rep * k), 12, 0.35)
        gcircle(gl, xl - 140, CY, 60, RED, 0.5 * rep)
        gcircle(gl, xr + 140, CY, 60, RED, 0.5 * rep)
    bo = fade(t, 7.85, 8.3)
    if bo > 0:
        bond(img, gl, (xl, CY - 18), (xr, CY - 18), bo, t, 9)
        bond(img, gl, (xl, CY + 18), (xr, CY + 18), bo, t, 9)
    nucleon(img, gl, xl, CY, 70 * app, True, min(1, app))
    nucleon(img, gl, xr, CY, 70 * app, True, min(1, app))
    lp = fade(t, 1.6, 2.2) * (1 - fade(t, 3.5, 3.8))
    if lp > 0:
        blit(img, pill("2 PROTON · İKİSİ DE ARTI (+) YÜKLÜ", F_SB, 34, WARM, WARM, padx=26, pady=10), CX, CY + 160, op=lp)
    caption(img, [("ÇEKİRDEK NEDEN", WHITE), ("DAĞILMIYOR?", CYAN)], t, 0.2, 3.6, y0=360, size=96)
    caption(img, [("İTER Mİ?", WHITE), ("EVET.", RED)], t, 3.75, 8.85, y0=1100, size=92)
    caption(img, [("DAĞILIR MI?", WHITE), ("HAYIR.", CYAN)], t, 7.8, 8.85, y0=1330, size=92)
    if t > 3.75:
        caption(img, [("AYNI YÜKLER", WHITE), ("BİRBİRİNİ İTER", RED)], t, 3.75, 7.7, y0=380, size=78)
    nd = ease_out_back(seg(t, 8.9, 9.3))
    if nd > 0:
        blit(img, T("NEDEN?", F_B, 150, AMBER), 540, 420, op=min(1, nd), scale=0.8 + 0.2 * nd)
    return img, gl

# --------------------------------------------------------------- B: guclu kuvvet + 100 kat (9.6 - 16)
def scene_B(t):
    img = base(t)
    gl = newgl()
    up = smooth(seg(t, 12.9, 13.6))
    s = (0.55 + 0.45 * ease_out_back(seg(t, 9.6, 10.4))) * (1 - 0.25 * up)
    cy = CY - 150 * up
    cluster(img, gl, t, CX, cy, s, min(1, fade(t, 9.6, 10.0)), fade(t, 10.2, 11.0))
    caption(img, [("GÜÇLÜ", CYAN), ("NÜKLEER KUVVET", WHITE)], t, 9.7, 16.3, y0=330, size=92)
    bp = fade(t, 13.0, 13.4)
    if bp > 0:
        x0, wmax = 110, 860
        y1, y2 = 1090, 1250
        blit(img, T("ELEKTROMANYETİK İTME", F_SB, 34, RED, maxw=860), 540, y1 - 46, op=bp)
        cv2.rectangle(img, (x0, y1), (x0 + wmax, y1 + 50), scol((30, 50, 90), bp), 2, cv2.LINE_AA)
        cv2.rectangle(img, (x0, y1), (x0 + int(wmax / 100), y1 + 50), scol(RED, bp), -1)
        blit(img, T("GÜÇLÜ KUVVET", F_SB, 34, CYAN, maxw=860), 540, y2 - 46, op=bp)
        g = ease_out(seg(t, 13.4, 14.9))
        cv2.rectangle(img, (x0, y2), (x0 + wmax, y2 + 50), scol((30, 50, 90), bp), 2, cv2.LINE_AA)
        cv2.rectangle(img, (x0, y2), (x0 + max(int(wmax / 100), int(wmax * g)), y2 + 50), scol(CYAN, bp), -1)
        gcircle(gl, x0 + wmax * g, y2 + 25, 70, CYAN, 0.6 * bp)
        kp = ease_out_back(seg(t, 14.5, 15.0))
        if kp > 0:
            blit(img, T("≈ 100 KAT GÜÇLÜ", F_B, 84, AMBER), 540, 1410, op=min(1, kp), scale=0.85 + 0.15 * kp)
    return img, gl

# --------------------------------------------------------------- C: menzil (16 - 22.6)
RNG = np.random.default_rng(3)
EL = [(RNG.uniform(0, 6.28), RNG.uniform(0.5, 1.4)) for _ in range(6)]

def scene_C(t):
    img = base(t)
    gl = newgl()
    ao = fade(t, 16.0, 16.6)
    R = 380
    for k in range(72):                                         # kesikli atom siniri
        if k % 2 == 0:
            a0, a1 = 360 * k / 72, 360 * (k + 1) / 72
            cv2.ellipse(img, (CX, CY), (R, R), 0, a0, a1, scol((90, 140, 210), 0.8 * ao), 3, cv2.LINE_AA)
    for (ph, w) in EL:
        a = ph + t * w
        rr = R * (0.55 + 0.4 * math.sin(ph * 3))
        px, py = CX + rr * math.cos(a), CY + rr * math.sin(a)
        cv2.circle(img, (int(px), int(py)), 9, scol(CYAN, ao), -1, cv2.LINE_AA)
        gcircle(gl, px, py, 34, CYAN, 0.7 * ao)
    gcircle(gl, CX, CY, 40, AMBER, 0.9 * ao)
    cv2.circle(img, (CX, CY), 5, scol(AMBER, ao), -1, cv2.LINE_AA)
    rg = fade(t, 17.6, 18.2)
    if rg > 0:
        rr = 16 + 3 * math.sin(t * 6)
        cv2.circle(img, (CX, CY), int(rr), scol(CYAN, rg), 3, cv2.LINE_AA)
        cv2.line(img, (CX + 14, CY - 14), (CX + 120, CY - 230), scol(CYAN, rg), 2, cv2.LINE_AA)
        blit(img, pill("GÜÇLÜ KUVVETİN ETKİ ALANI", F_SB, 32, CYAN, CYAN, padx=26, pady=10), CX + 120, CY - 262, op=rg)
        dp = fade(t, 18.0, 18.6)
        cv2.line(img, (CX - R, CY - R - 40), (CX + R, CY - R - 40), scol(MUTED, dp), 2, cv2.LINE_AA)
        for sx in (CX - R, CX + R):
            cv2.line(img, (sx, CY - R - 55), (sx, CY - R - 25), scol(MUTED, dp), 2, cv2.LINE_AA)
        blit(img, T("ATOMUN ÇAPI", F_SB, 32, MUTED), CX, CY - R - 80, op=dp)
    caption(img, [("MENZİLİ", WHITE), ("ÇOK KISA", CYAN)], t, 16.0, 17.55, y0=300, size=92)
    if t > 17.5:
        caption(img, [("ATOM ÇAPININ", WHITE), ("≈ 1/100.000'İ", AMBER)], t, 17.6, 20.2, y0=1360, size=84)
    if t > 20.1:
        caption(img, [("YALNIZCA", WHITE), ("ÇEKİRDEK BOYUTUNDA", CYAN)], t, 20.25, 22.8, y0=1360, size=80)
    return img, gl

# --------------------------------------------------------------- D: cirt cirt benzetmesi (22.6 - 27.4)
def strip(img, gl, y, hooks, op, t):
    x0, x1 = 170, 910
    col = CYAN if hooks else AMBER
    cv2.rectangle(img, (x0, int(y) - 22), (x1, int(y) + 22), scol((14, 34, 80), op), -1)
    cv2.rectangle(img, (x0, int(y) - 22), (x1, int(y) + 22), scol(col, op), 3, cv2.LINE_AA)
    for k in range(20):
        x = x0 + 22 + k * 37
        if hooks:   # alt yuzde kancalar
            cv2.line(img, (x, int(y) + 22), (x, int(y) + 52), scol(col, op), 3, cv2.LINE_AA)
            cv2.ellipse(img, (x + 8, int(y) + 52), (8, 8), 0, 0, 180, scol(col, op), 3, cv2.LINE_AA)
        else:       # ust yuzde ilmekler
            cv2.ellipse(img, (x + 8, int(y) - 22), (12, 26), 0, 180, 360, scol(col, op), 3, cv2.LINE_AA)

def scene_D(t):
    img = base(t)
    gl = newgl()
    o = fade(t, 22.6, 23.1)
    blit(img, pill("BENZETME", F_B, 38, AMBER, AMBER, padx=30, pady=12), 540, 320, op=o)
    close = smooth(seg(t, 24.1, 24.8)) * (1 - smooth(seg(t, 25.7, 26.6)))
    gap = 330 - 255 * close
    ya = 960 - gap / 2
    yb = 960 + gap / 2
    shake = 4 * math.sin(t * 30) * fade(t, 25.7, 25.9) * (1 - fade(t, 26.2, 26.5))
    strip(img, gl, ya + shake, True, o, t)
    strip(img, gl, yb, False, o, t)
    if close > 0.95:
        gcircle(gl, 540, 960, 300, CYAN, 0.10)
    caption(img, [("CIRT CIRT BANT GİBİ", WHITE)], t, 22.7, 24.1, y0=470, size=78)
    if t > 24.0:
        caption(img, [("YAKINKEN", WHITE), ("SIKI TUTAR", CYAN)], t, 24.15, 25.7, y0=1330, size=84)
    if t > 25.6:
        caption(img, [("UZAKTAYKEN", WHITE), ("ETKİ YOK", MUTED)], t, 25.75, 27.7, y0=1330, size=84)
    return img, gl

# --------------------------------------------------------------- E: kapanis (27.4 - 30.2)
def scene_E(t):
    img = base(t)
    gl = newgl()
    cluster(img, gl, t, CX, 900, 1.05 + 0.03 * math.sin(t * 4), 1.0, 1.0)
    caption(img, [("ÇEKİRDEĞİ BİR ARADA", WHITE), ("TUTAN ŞEY BU", CYAN)], t, 27.5, 40, y0=330, size=82)
    blit(img, T("GÜÇLÜ NÜKLEER KUVVET", F_B, 64, AMBER), 540, 1300, op=fade(t, 28.2, 28.8))
    return img, gl

# --------------------------------------------------------------- birlestirme
SCENES = [(0.0, scene_A), (9.55, scene_B), (15.95, scene_C), (22.6, scene_D), (27.4, scene_E)]
XH = 0.22

def render_scene(fn, t):
    img, gl = fn(t)
    series_tag(img, t)
    apply_glow(img, gl)
    return img

def frame(t):
    idx = 0
    for k, (s, _) in enumerate(SCENES):
        if t >= s - XH:
            idx = k
    s, fn = SCENES[idx]
    img = render_scene(fn, t)
    if idx > 0 and t < s + XH:
        prev = render_scene(SCENES[idx - 1][1], t)
        img = cv2.addWeighted(prev, 1 - smooth((t - (s - XH)) / (2 * XH)), img, smooth((t - (s - XH)) / (2 * XH)), 0)
    note(img, t, 0.4, 30.1)
    img = source_card(img, t, 30.2, [
        "ABD Enerji Bakanlığı (DOE) · \"DOE Explains: The Strong Force\"",
        "güçlü kuvvet ≈ elektromanyetizmadan 100 kat güçlü",
        "menzil ≈ atom çapından 100.000 kat küçük",
    ], ["Cırt cırtlı bant yalnızca bir benzetmedir.", "ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL"])
    if t > 30.2:
        series_tag(img, t)
    return img

if __name__ == "__main__":
    main(frame, OUT, "kuvvet", DUR)
