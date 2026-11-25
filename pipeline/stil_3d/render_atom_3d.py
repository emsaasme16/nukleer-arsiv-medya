#!/usr/bin/env python3
"""3D: Atomun kutlesi nerede? (atomun-kutlesi-nerede.mp4) 1080x1920, 30 fps, 38,2 sn.
Zaman cizelgesi short1_atomun_kutlesi/tl3.py ile ayni (modul oradan okunur), sahne icerikleri
render3.py ile ayni.
Kullanim: python3 render_atom_3d.py still 1 10 ... | render"""
import math, os, sys
from common3d import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "short1_atomun_kutlesi"))
import tl3 as tl

NAME = "atomun-kutlesi-nerede"
NFRAMES = 1146
CX, CY = 540, 900

# ----------------------------------------------------------------- elektron bulutu (3D kure kabuk)
rng = np.random.default_rng(7)
NP = 1100
P_R = 28 + 68 * rng.beta(2.2, 1.6, NP)
_u = rng.uniform(-1, 1, NP)
_ph = rng.uniform(0, 2 * math.pi, NP)
P_DIR = np.stack([np.sqrt(1 - _u ** 2) * np.cos(_ph), np.sqrt(1 - _u ** 2) * np.sin(_ph), _u], 1)
P_PH = rng.uniform(0, 6.28, NP)
P_RATE = rng.uniform(0.8, 3.0, NP)
P_SZ = rng.choice([2, 2, 2, 3], NP)
P_GLOW = rng.uniform(0, 1, NP) < 0.35


def cloud_pts(t, z):
    R = rot_y(t * 0.12) @ rot_x(0.2 * math.sin(t * 0.1))
    d = P_DIR @ R.T
    return np.stack([CX + d[:, 0] * P_R * z, CY + d[:, 1] * P_R * z, d[:, 2] * P_R * z], 1)


def draw_cloud(F, t, z, op):
    if op <= 0.01:
        return
    p = cloud_pts(t, z)
    sx, sy, sc, dep = F.cam.project(p)
    al = (0.40 + 0.60 * (0.5 + 0.5 * np.sin(t * P_RATE + P_PH))) * op
    front = p[:, 2] >= 0
    vis = (sx > -6) & (sx < W + 6) & (sy > -6) & (sy < H + 6)

    def draw(img, sel, dim):
        for i in np.nonzero(sel & vis)[0]:
            k = float(al[i]) * dim
            c = scol(CYAN if i % 3 else BLUE, k)
            cv2.circle(img, (int(sx[i]), int(sy[i])), max(1, int(round(P_SZ[i] * sc[i]))), c, -1, cv2.LINE_AA)
    draw(F.img, ~front, 0.6)                    # arka yari: 3D nesnelerin arkasinda, sonuk
    for i in np.nonzero(P_GLOW & vis)[0]:
        F.glow(sx[i], sy[i], 4, CYAN, 0.8 * float(al[i]))
    F.over(lambda img: draw(img, front, 1.0))   # on yari: one cizilir


# ----------------------------------------------------------------- stadyum (3D)
MAT_STAND = ((0.35, 0.3, 0.7, 0.0), (0, 0, 0, 1))


def draw_stadium(F, z, op):
    if op <= 0.003:
        return
    th = min(6 * z, 40)
    # tribun halkasi (eliptik)
    F.add(torus_key(0.12), model((CX, CY, 0), (53.5 * z, th / 0.24, 34.5 * z), rot_x(math.pi / 2)),
          (36, 90, 176), MAT_STAND, op)
    F.add(torus_key(0.012), model((CX, CY, th * 0.4), (60 * z, 60 * z, 40 * z), rot_x(math.pi / 2)),
          CYAN, MAT_GLOW, op)
    # saha (seritli)
    n = 10
    sw = 76 * z / n
    for k in range(n):
        x = CX - 38 * z + sw * (k + 0.5)
        F.box(x, CY, -th * 0.3, sw, 42 * z, max(2, th * 0.2), (12, 80, 60) if k % 2 == 0 else (16, 96, 72), MAT_MATTE, op, r=0)
    ln = (205, 232, 238)
    lw = max(1.2, 0.07 * z)
    zl = -th * 0.3 + max(2, th * 0.2) / 2 + 0.5
    x0, x1, y0, y1 = CX - 38 * z, CX + 38 * z, CY - 21 * z, CY + 21 * z
    for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)), ((CX, y0), (CX, y1))]:
        F.rod((a[0], a[1], zl), (b[0], b[1], zl), lw, ln, MAT_MATTE, op)
    for sgn in (-1, 1):
        bx, bx2 = CX + sgn * 38 * z, CX + sgn * 28 * z
        for a, b in [((bx2, CY - 11 * z), (bx2, CY + 11 * z)), ((bx, CY - 11 * z), (bx2, CY - 11 * z)), ((bx, CY + 11 * z), (bx2, CY + 11 * z))]:
            F.rod((a[0], a[1], zl), (b[0], b[1], zl), lw, ln, MAT_MATTE, op)
    F.add(torus_key(0.03), model((CX, CY, zl), 6 * z, rot_x(math.pi / 2)), ln, MAT_MATTE, op)


# ----------------------------------------------------------------- sahne AB (eski zaman 0-14)
Z0, Z1 = 90.0, 4.4
ZT0, ZT1 = 5.0, 12.4


def zoom_z(t):
    p = smooth(seg(t, ZT0, ZT1))
    return Z0 * (Z1 / Z0) ** p


def scene_AB(t):
    tilt = 0.32 * smooth(seg(t, 5.0, 11.0))
    F = Frame(t, Cam(yaw=0.10 * math.sin(t * 0.3), pitch=0.04 + tilt, pivot=(CX, CY, 0)))
    z = zoom_z(t)
    draw_stadium(F, z, fade(t, 5.4, 8.4))
    draw_cloud(F, t, z, 1.0 if t > 5.0 else 0.0)
    if t > 9.0:
        sx, sy, sc = F.p2(CX, CY, 0)
        r = int(96 * z * sc)
        cv2.circle(F.img, (int(sx), int(sy)), r, scol((70, 130, 200), 0.55 * fade(t, 9.0, 10.5)), 2, cv2.LINE_AA)
    pop = ease_out_back(seg(t, 0.2, 0.9)) if t < 5.0 else 1.0
    bob = 6 * math.sin(t * 2.2) if t < 5.0 else 0.0
    pr = z * 1.0 * pop
    pulse = 0.8 + 0.2 * math.sin(t * 3.0)
    F.sphere(CX, CY + bob, pr * 0.2 if z < 6 else 0, max(pr, 1.5), PEA, ((0.6, 0.5, 0.9, 0.05), (0, 0, 0, 1)), alpha=1.0,
             glow=0.55 * pulse * fade(t, 0.2, 1.0), glow_col=PEA)
    ring = fade(t, 10.8, 11.6)
    if ring > 0:
        rr = 24 + 3 * math.sin(t * 5)
        F.torus(CX, CY, 0, rr, 0.08, PEA, rot_x(math.pi / 2), MAT_GLOW, alpha=ring)
    ex = 1 - fade(t, 5.0, 5.7)
    if ex > 0:
        F.text_in("ÇEKİRDEK", F_B, 128, CYAN, 540, 330, 0.15, op=ex)
        F.text_in("BİR BEZELYE", F_B, 128, WHITE, 540, 468, 0.5, op=ex)
        F.text_in("OLSAYDI…", F_B, 78, MUTED, 540, 588, 0.95, op=ex)
    tb = fade(t, 9.2, 10.0)
    if tb > 0:
        F.text("ELEKTRONLARIN ALANI", F_B, 76, CYAN, 540, 318 + (1 - tb) * 20, op=tb)
        F.text("BİR STADYUMDAN BÜYÜK", F_B, 76, WHITE, 540, 408 + (1 - tb) * 20, op=tb)
    lab = fade(t, 11.2, 12.0)
    if lab > 0:
        _, ys, _ = F.p2(CX, CY - 40 * Z1, 0)
        _, yc, _ = F.p2(CX, CY + 96 * Z1, 0)
        F.spr(pill("STADYUM", F_SB, 32, WHITE, (90, 150, 220), padx=26, pady=10), 540, int(ys - 36), op=lab)
        F.spr(pill("ELEKTRON BULUTU", F_SB, 32, CYAN, CYAN, padx=26, pady=10), 540, int(yc + 42), op=lab)
    pl = fade(t, 11.5, 12.3)
    if pl > 0:
        sx, sy, _ = F.p2(CX, CY, 0)

        def pline(img, pl=pl, sx=sx, sy=sy):
            cv2.line(img, (int(sx), int(sy + 30)), (CX, 1180), scol(PEA, pl), 2, cv2.LINE_AA)
            cv2.circle(img, (int(sx), int(sy + 30)), 4, scol(PEA, pl), -1, cv2.LINE_AA)
            blit(img, pill("ÇEKİRDEK = BEZELYE", F_B, 44, PEA, PEA, padx=34, pady=16), 540, 1222, op=pl)
        F.over(pline)
    F.series_tag()
    return F.finish()


# ----------------------------------------------------------------- sahne C (eski zaman 14-24)
BAR_X, BAR_Y, BAR_W, BAR_H = 80, 1066, 920, 110


def scene_C(t):
    lt = max(0.0, t - 14.0)
    F = Frame(t, Cam(yaw=0.10 * math.sin(t * 0.3), pitch=0.06, pivot=(540, 1000, 0)))
    bo = 1 - fade(lt, 2.3, 2.9)
    pop = ease_out_back(seg(lt, 0.4, 1.0))
    if bo > 0 and pop > 0:
        sc = 0.85 + 0.15 * pop
        F.text("PEKİ ATOMUN", F_B, 112, WHITE, 540, 790, op=min(1, pop) * bo, scale=sc)
        F.text("KÜTLESİ NEREDE?", F_B, 112, AMBER, 540, 930, op=min(1, pop) * bo, scale=sc)
        F.glow(540, 860, 300, AMBER, 0.08 * min(1, pop) * bo)
    cp = fade(lt, 2.9, 3.5)
    if cp > 0:
        F.text("ATOMUN KÜTLESİNİN", F_SB, 48, MUTED, 540, 520, op=cp)
        p = ease_out(seg(lt, 3.2, 6.2))
        n = int(round(99 * p))
        done = lt >= 6.2
        txt = "%99+" if done else "%" + str(n)
        sc = 1.0
        if done and lt < 6.7:
            sc = 1.0 + 0.10 * math.sin(math.pi * clamp01((lt - 6.2) / 0.5))
        F.glow(540, 760, 230, AMBER, 0.08 + 0.22 * p)
        F.text(txt, F_B, 330, AMBER, 540, 760, op=cp, scale=sc, maxw=900)
        cy = BAR_Y + BAR_H / 2
        F.box(540, cy, 0, BAR_W, BAR_H, 90, (40, 70, 130), MAT_GLOSS, alpha=0.30 * cp, r=28)
        fw = BAR_W * min(1.0, p) * 0.99
        if fw > 4:
            F.box(BAR_X + fw / 2, cy, 0, fw, BAR_H - 14, 76, (255, 172, 70), ((0.8, 0.7, 0.8, 0.35), (0, 0, 0, 1)),
                  alpha=cp, r=min(26, fw / 2 - 1))
        so = fade(lt, 6.8, 7.4)
        if so > 0:
            F.box(BAR_X + BAR_W * 0.995 - 2, cy, 0, 9, BAR_H - 14, 76, CYAN, MAT_GLOW, alpha=so, r=3)
        F.glow(540, cy, 120, AMBER, 0.10 + 0.25 * p)
    cc = fade(lt, 6.3, 7.0)
    if cc > 0:
        F.text("ÇEKİRDEKTE", F_B, 100, WHITE, 540, 950 + (1 - cc) * 20, op=cc)
    lb = fade(lt, 6.9, 7.6)
    if lb > 0:
        F.text("ÇEKİRDEK", F_B, 44, AMBER, 230, 1255, op=lb, maxw=420)
        F.text("%99'DAN FAZLA", F_SB, 36, WHITE, 230, 1310, op=lb, maxw=420)
        F.text("ELEKTRONLAR", F_B, 44, CYAN, 840, 1255, op=lb, maxw=420)
        F.text("%1'DEN AZ", F_SB, 36, WHITE, 840, 1310, op=lb, maxw=420)
        sx, sy, _ = F.p2(BAR_X + BAR_W - 5, BAR_Y + BAR_H, 0)
        F.over(lambda img: cv2.line(img, (int(sx), int(sy)), (int(sx), 1226), scol(CYAN, lb), 2, cv2.LINE_AA))
    F.series_tag()
    return F.finish()


# ----------------------------------------------------------------- sahne D (eski zaman 24-33)
COLS, ROWS, SP = 51, 36, 13
GX0 = 540 - (COLS - 1) * SP / 2
GY0 = 1234 - (ROWS - 1) * SP / 2
DOTS = np.array([(GX0 + c * SP, GY0 + r * SP, 0.0) for r in range(ROWS) for c in range(COLS)])
NTOT = COLS * ROWS  # 1836


def scene_D(t):
    lt = max(0.0, t - 24.0)
    F = Frame(t, Cam(yaw=0.08 * math.sin(t * 0.3), pitch=0.10, pivot=(540, 1000, 0)))
    F.text_in("1 PROTON KAÇ", F_B, 76, WHITE, 540, 318, 24.4)
    F.text_in("ELEKTRON AĞIRLIĞINDA?", F_B, 76, CYAN, 540, 410, 24.8)
    pp = ease_out_back(seg(lt, 1.3, 2.1))
    if pp > 0.02:
        pulse = 0.85 + 0.15 * math.sin(lt * 3.2)
        F.glow(540, 610, 180, WARM, 0.55 * pulse * min(1, pp))
        r = 88 * pp
        F.sphere(540, 610, 0, r, WARM, MAT_PLASTIC, alpha=min(1, pp))
        F.plus(540, 610, 0, r, min(1, pp))
        F.text("1 PROTON", F_B, 44, AMBER, 540, 722, op=min(1, pp))
    prog = smooth(seg(lt, 3.0, 7.0))
    n = int(round(NTOT * prog))
    gd = fade(lt, 2.4, 3.0)
    sx, sy, sc, _ = F.cam.project(DOTS)
    img = F.img
    for k in range(NTOT):
        if k < n:
            cv2.circle(img, (int(sx[k]), int(sy[k])), 4, CYAN, -1, cv2.LINE_AA)
        elif gd > 0:
            cv2.circle(img, (int(sx[k]), int(sy[k])), 2, scol((60, 90, 150), gd * 0.9), -1, cv2.LINE_AA)
    if 0 < n < NTOT:
        r_cur = (n - 1) // COLS
        for c in range(COLS):
            k = r_cur * COLS + c
            if k < n:
                cv2.circle(img, (int(sx[k]), int(sy[k])), 5, WHITE, -1, cv2.LINE_AA)
        F.glow(540, sy[r_cur * COLS], 90, CYAN, 0.30)
    if gd > 0:
        done = lt >= 7.0
        txt = "≈ %d" % n
        s2 = 1.0
        if done and lt < 7.5:
            s2 = 1.0 + 0.10 * math.sin(math.pi * clamp01((lt - 7.0) / 0.5))
        F.glow(540, 845, 150, CYAN, 0.10 + 0.20 * prog)
        F.text(txt, F_B, 150, CYAN, 540, 845, op=gd, scale=s2, maxw=760)
        F.text("ELEKTRON KÜTLESİ", F_SB, 40, MUTED, 540, 925, op=gd)
        F.text("HER NOKTA = 1 ELEKTRON", F_M, 30, MUTED, 540, 972, op=gd * 0.9)
    F.series_tag()
    return F.finish()


# ----------------------------------------------------------------- sahne E (yeni zaman 24.6 - 38.2)
def scene_E(t):
    lt = max(0.0, t - tl.E0)
    F = Frame(t, Cam(yaw=0.16 * math.sin(t * 0.3), pitch=0.08 * math.sin(t * 0.22), pivot=(540, 860, 0),
                     dolly=1.0 - 0.05 * smooth(seg(lt, 0, 10.8))))
    NX, NY = 540, 860
    nuc_p = ease_out_back(seg(lt, 0.2, 0.9))
    pulse = 1 + 0.06 * math.sin(lt * 4.0)
    strong = fade(lt, 8.2, 8.8)
    orbs = [(300, 110, 20), (360, 150, -35), (250, 190, 70)]
    ec = fade(lt, 10.8, 11.4)
    for i, (rx, ry, rot) in enumerate(orbs):
        o = fade(lt, 0.5 + 0.15 * i, 1.2 + 0.15 * i) * (1 - ec)
        if o <= 0:
            continue
        tilt = math.acos(ry / rx)
        R = rot_z(math.radians(rot)) @ rot_x(tilt)
        F.add(torus_key(0.006), model((NX, NY, 0), rx, R @ rot_x(math.pi / 2)), (90, 140, 210), MAT_GLOW, 0.6 * o)
        a = lt * (1.1 + 0.4 * i) + i * 2.1
        v = R @ np.array([rx * math.cos(a), rx * math.sin(a), 0])
        F.sphere(NX + v[0], NY + v[1], v[2], 11, CYAN, MAT_GLOW, alpha=o, glow=1.0, lo=True)
    if nuc_p > 0.02:
        F.glow(NX, NY, 230 * pulse, AMBER, (0.45 + 0.4 * strong) * min(1, nuc_p) * (1 - ec))
        F.sphere(NX, NY, 0, 62 * nuc_p * pulse * (1 + 0.15 * strong), AMBER, ((0.7, 0.7, 1.0, 0.25 + 0.3 * strong), (0, 0, 0, 1)),
                 alpha=min(1, nuc_p) * (1 - ec))
    RS = 8.3
    if lt > RS and ec < 1:
        rings = []
        for k in range(3):
            if lt - RS - k * 0.53 < 0:
                continue
            q = ((lt - RS) / 1.6 - k / 3.0) % 1.0
            rings.append((70 + 250 * q, (1 - q) * 0.9 * (1 - ec)))
        sx, sy, sc = F.p2(NX, NY, 0)
        for rr, op in rings:
            cv2.circle(F.img, (int(sx), int(sy)), int(rr * sc), scol(AMBER, op), 3, cv2.LINE_AA)
            F.glow(sx, sy, rr * sc, AMBER, 0.5 * op, thick=2)
    ko = 1 - fade(lt, 6.4, 6.9)
    if ko > 0:
        F.text_in("ODUN YANAR, DEMİR PASLANIR", F_B, 54, WHITE, 540, 300, tl.E0 + 2.5, op=ko)
        F.text_in("BUNLAR ELEKTRONLARIN İŞİ", F_B, 54, CYAN, 540, 372, tl.E0 + 4.6, op=ko)
    F.text_in("NÜKLEER ENERJİ", F_B, 88, AMBER, 540, 1190, tl.E0 + 6.9, op=1 - ec)
    F.text_in("ÇEKİRDEKTEN GELİR", F_B, 88, WHITE, 540, 1292, tl.E0 + 8.3, op=1 - ec)
    if ec > 0:
        cam = F.cam

        def card(img):
            clean = background(t, cam)
            img = cv2.addWeighted(clean, ec, img, 1 - ec, 0)
            blit(img, T("KAYNAKLAR", F_B, 52, CYAN), 540, 700, op=ec)
            cv2.line(img, (380, 748), (700, 748), scol(CYAN, 0.6 * ec), 2, cv2.LINE_AA)
            blit(img, T("NIST CODATA · proton/elektron kütle oranı ≈ 1836", F_M, 32, WHITE, maxw=980), 540, 800, op=fade(lt, 11.0, 11.6))
            blit(img, T("Windows to the Universe (UCAR) · kütlenin >%99'u çekirdekte", F_M, 32, WHITE, maxw=980), 540, 860, op=fade(lt, 11.2, 11.8))
            blit(img, T("Windows to the Universe · bezelye-stadyum ölçeği", F_M, 32, WHITE, maxw=980), 540, 920, op=fade(lt, 11.3, 11.9))
            blit(img, T("DEVAMI KANALDA · BÖLÜM 1", F_B, 54, AMBER, maxw=980), 540, 1090, op=fade(lt, 11.6, 12.2))
            return img
        F.over(card)
    F.series_tag()
    return F.finish()


# ----------------------------------------------------------------- birlestirme
def frame(Tt):
    a = lambda: scene_AB(tl.pw(Tt, tl.INV_AB))
    c = lambda: scene_C(tl.pw(Tt, tl.INV_C))
    d = lambda: scene_D(tl.pw(Tt, tl.INV_D))
    e = lambda: scene_E(Tt)
    (b1, h), (b2, _), (b3, _) = tl.XF
    if abs(Tt - b1) <= h:
        return mix(a(), c(), smooth((Tt - (b1 - h)) / (2 * h)))
    if abs(Tt - b2) <= h:
        return mix(c(), d(), smooth((Tt - (b2 - h)) / (2 * h)))
    if abs(Tt - b3) <= h:
        return mix(d(), e(), smooth((Tt - (b3 - h)) / (2 * h)))
    if Tt < b1:
        return a()
    if Tt < b2:
        return c()
    if Tt < b3:
        return d()
    return e()


if __name__ == "__main__":
    cli("render_atom_3d", frame, NFRAMES, NAME)
