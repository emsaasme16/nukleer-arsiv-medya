#!/usr/bin/env python3
"""Gercekci 3D Short: Mit mi, gercek mi? Uranyumun hepsi bolunur (uranyumun-hepsi-bolunur-mu.mp4), 1080x1920, 30 fps.

Ses: /tmp/s3/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar sesin sessizlik sinirlarindan.
Kaynaklar: NRC sozlugu "Uranium" (%0,7 U-235 fisil, %99,3 U-238 hizli notronla bolunebilir), NRC "Fissile material"
(yavas/termal notronla bolunme), DOE-HDBK-1019/1-93 (Tablo 4: BEn - Ecrit U-235 +0,3 MeV, U-238 -1,5 MeV; U-238 yuksek
enerjili notron ister), DOE "The Harnessed Atom" (santraller ~%4 U-235'lik uranyum kullanir; zenginlestirme).
Demet modeli: ../uzun_3d/modeller/yakit.py (NRC Reactor Concepts Manual tarifi, 17x17).
Kullanim: WORK=/tmp/s3 python3 render_uranyum_bolunur_3d.py still 2 10 ... | render
"""
from dikey_kit import *

NAME = "uranyumun-hepsi-bolunur-mu"
TOTAL = 55.94
NFRAMES = int(TOTAL * FPS)
BOLUM = 2

Z = dict(soru=1.09, mit=5.36, damga=7.28, dogal=8.10, u235=12.91, fark=16.99, yavas=20.11, bu=25.66, u238=29.24,
         hizli=33.10, santral=36.83, zengin=42.90, yani=45.20, azinlik=47.63, son=50.5)

ODA = set(int(i) for i in np.random.default_rng(42).choice(1000, 7, replace=False))
TEPSI = Mat(srgb((168, 170, 174)), 0.3, 1.0, pat="fircali")
MASA = Mat(srgb((60, 64, 70)), 0.6, 0.2, pat="boya")
PELET = yakit.SERAMIK.but(col=srgb((70, 68, 66)), rough=0.55)


def sh_pelet(v, t):
    """celik tepside dizili yakit peletleri; kamera yaklasip tek pelete dalar."""
    S = Sahne()
    ic_mekan(S, warm=False)
    S.sun_dir = norm((-0.3, 0.9, 0.45))
    S.sun_col = (2.3, 2.2, 2.05)
    S.amb = 0.5
    S.shadow_box = ((0, 0.0, 0), 0.12)
    S.shadow_bias = 0.0004
    S.ssao_r = 0.006
    S.add(BOX, TRS((0, -0.004, 0), s=(0.6, 0.008, 0.4)), MASA)
    S.add(BOX, TRS((0, 0.0005, 0), s=(0.16, 0.001, 0.07)), TEPSI)
    for r in range(3):
        for c in range(12):
            x = -0.066 + c * 0.0112 + (r % 2) * 0.004
            z = -0.018 + r * 0.018
            yakit.pellet(S, (x, 0.001 + yakit.PEL_H / 2, z), mat=PELET)
    k = sm(t / 7.2)
    eye = np.array((0.06, 0.07, 0.13)) * (1 - k) + np.array((0.004, 0.016, 0.026)) * k
    tgt = np.array((0.0, 0.004, 0.0)) * (1 - k) + np.array((0.0, 0.006, 0.0)) * k
    cam = Cam(eye, tgt, fov=34, near=0.002, aperture=0.4)
    img = ciz(S, cam, t)
    lines(img, [("URANYUMUN", WHITE), ("HER ATOMU", WHITE), ("BÖLÜNÜR MÜ?", AMBER)], 400, win(t, 0.2, Z["mit"]), 84, t=t, t0=0.2)
    label(img, "MİT Mİ, GERÇEK Mİ?", 540, 450, win(t, Z["mit"] + 0.05, Z["damga"] + 0.6), 74, CYAN, F_XB)
    return img


def kup(S, t, hl, gray_a=1.0):
    g = np.arange(10) - 4.5
    X, Y, Zz = np.meshgrid(g, g, g, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel(), Zz.ravel()], 1) * 1.15
    gray = Mat((0.42, 0.45, 0.5), 0.45, 0.2, alpha=gray_a)
    for i, p in enumerate(P):
        if i in ODA:
            S.add(SPH_LO, TRS(tuple(p), s=0.45), Mat((1.0, 0.62, 0.18), 0.3, emi=(2.0 * hl + 0.2, 1.0 * hl + 0.1, 0.2 * hl)))
            if hl > 0:
                S.particle(tuple(p), 2.4, (1.0, 0.65, 0.25, 0.4 * hl), add=True)
        else:
            S.add(SPH_LO, TRS(tuple(p), s=0.45), gray)


def sh_kup(v, t):
    S = Sahne()
    atom_ortami(S)
    hl = fade(t, Z["u235"] + 0.2, Z["u235"] + 1.5)
    kup(S, t, hl)
    ang = 0.5 + t * 0.07
    d = 44 - 5 * sm((t - Z["dogal"]) / 9)
    cam = Cam((math.sin(ang) * d, 10, math.cos(ang) * d), (0, 0, 0), fov=40, aperture=0.15)
    img = ciz(S, cam, t)
    stamp(img, "MİT", 540, 430, fade(t, Z["damga"], Z["damga"] + 0.25) * (1 - fade(t, Z["dogal"] + 1.0, Z["dogal"] + 1.5)), RED, 130,
          pop=0.3 * (1 - fade(t, Z["damga"], Z["damga"] + 0.35)))
    cardl(img, ["Doğal uranyum", "(1000 atom)"], 540, 420, win(t, Z["dogal"] + 1.2, Z["fark"]), 52)
    label(img, "993 · U-238 · %99,3", 540, 1430, win(t, Z["dogal"] + 1.6, Z["fark"]), 58, (205, 214, 228), F_B)
    label(img, "7 · U-235 · %0,7", 540, 1530, win(t, Z["u235"] + 0.4, Z["fark"]), 58, AMBER, F_B)
    return img


SPLIT = None


def split_pts(t, t0, seed_rot=0.0):
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    src, dst, grp, isp, cap = SPLIT
    sep = fade(t, t0, t0 + 3.0)
    Q = src.copy()
    if sep > 0:
        cen = np.array([[-9.5, 0, 0], [12.5, 0, 0]])
        out = Q.copy()
        for i in range(len(Q)):
            if grp[i] < 2:
                tgt = dst[i] + cen[grp[i]]
                out[i] = Q[i] * (1 - sm(sep * 1.4)) + tgt * sm(sep * 1.4) + cen[grp[i]] * sep * 0.8
            else:
                d = np.array([0.2, 1.0, 0.3]) if i % 3 == 0 else (np.array([0.1, -0.8, 0.7]) if i % 3 == 1 else np.array([-0.2, 0.3, -1.0]))
                out[i] = Q[i] + d * sep * 22
        Q = out
    return Q, grp, isp, cap, sep


def gelen(S, t, ta, tb, p0, p1, s, fast=False):
    """ta-tb arasinda p0'dan p1'e giden notron (hizli: parlak, uzun iz)."""
    if t < ta - 0.3 or t > tb:
        return
    k = fade(t, ta, tb)
    pos = p0 * (1 - k) + p1 * k
    n = 18 if fast else 8
    step = 0.05 if fast else 0.025
    atom.neutron(S, pos, s, glow=2.2 if fast else 1.0, trail=[pos + (p0 - pos) * step * j for j in range(1, n)])


def sh_u235(v, t):
    S = Sahne()
    atom_ortami(S)
    t0 = Z["yavas"] + 2.6
    Q, grp, isp, cap, sep = split_pts(t, t0)
    s = 0.62
    Rr = ry(0.2 + t * 0.05) @ rz(0.6)
    pts = (Q @ Rr.T) * s
    hot = fade(t, t0 - 0.8, t0) * (1 - 0.5 * sep)
    for i in range(len(pts)):
        if i == cap and t < t0 - 0.6:
            continue
        if grp[i] == 2 and sep > 0:
            atom.neutron(S, pts[i], s, glow=1.3)
            continue
        m = atom.PROTON if isp[i] else atom.NEUTRON
        if hot > 0:
            e = hot * (0.6 + 0.3 * math.sin(t * 9 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (0.6 * e, 0.26 * e, 0.06 * e))))
        S.add(SPH, TRS(tuple(pts[i]), s=s), m)
    gelen(S, t, Z["yavas"] + 0.1, t0 - 0.6, np.array([20.0, 14.0, 4.0]), pts[cap], s)
    if sep > 0:
        S.particle((0, 0, 0), 34 * sep + 6, (1.0, 0.8, 0.5, min(1.0, 2.6 * sep * (1 - sep))), add=True)
    atom.dust(S, t, n=140, R=50, a=0.16)
    cam = path(t, [(Z["fark"] - 0.6, (0, 3, 40), (0, 0, 0), 40), (t0, (2, 4, 36), (0, 0, 0), 40),
                   (Z["u238"], (0, 6, 50), (1, 0, 0), 44)], aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("FARK, NÖTRON", WHITE), ("YAKALANINCA", AMBER)], 400, win(t, Z["fark"] + 0.1, Z["yavas"] + 0.2), 80, t=t, t0=Z["fark"])
    a = win(t, Z["yavas"] + 0.2, Z["u238"])
    label(img, "U-235 + YAVAŞ NÖTRON", 540, 420, a, 66, AMBER, F_XB)
    cardl(img, ["Eşik aşılır: +0,3 MeV"], 540, 1420, win(t, Z["yavas"] + 1.5, Z["u238"]), 54, amber=True)
    label(img, "BÖLÜNÜR", 540, 1560, win(t, t0 + 0.3, Z["u238"]), 70, WHITE, F_XB)
    return img


def sh_u238(v, t):
    S = Sahne()
    atom_ortami(S)
    u = atom.get("U238")
    t1 = Z["u238"] + 2.0                 # yavas notron yakalanir, bolunme yok
    t2 = Z["hizli"] + 1.8                # hizli notron: bolunme
    s = 0.62
    Rr = ry(-0.3 + t * 0.05) @ rx(0.3)
    if t < t2:
        wob = 0.06 * math.sin((t - t1) * 7) * math.exp(-max(0, t - t1) * 0.8) if t > t1 else 0.0
        P = u.P * (1 + wob)
        Q = (P @ Rr.T) * s
        for i in range(len(Q)):
            S.add(SPH, TRS(tuple(Q[i]), s=s), atom.PROTON if u.isp[i] else atom.NEUTRON)
        r_out = np.linalg.norm(u.P, axis=1).max() * s
        gelen(S, t, Z["u238"] + 0.2, t1, np.array([-20.0, 14.0, 4.0]), np.array([-r_out * 0.7, r_out * 0.5, r_out * 0.3]), s)
        if t > t1:
            atom.neutron(S, np.array([-r_out * 0.7, r_out * 0.5, r_out * 0.3]), s, glow=0.6 * (1 - fade(t, t1 + 0.3, t1 + 2)))
        gelen(S, t, Z["hizli"] + 0.6, t2, np.array([24.0, -16.0, 6.0]), np.array([r_out * 0.6, -r_out * 0.4, 0.0]), s, fast=True)
    else:
        Q, grp, isp, cap, sep = split_pts(t, t2)
        pts = (Q @ Rr.T) * s
        for i in range(len(pts)):
            if grp[i] == 2:
                atom.neutron(S, pts[i], s, glow=1.3)
                continue
            S.add(SPH, TRS(tuple(pts[i]), s=s), atom.PROTON if isp[i] else atom.NEUTRON)
        S.particle((0, 0, 0), 34 * sep + 6, (1.0, 0.8, 0.5, min(1.0, 2.6 * sep * (1 - sep))), add=True)
    atom.dust(S, t, n=140, R=50, a=0.16)
    cam = path(t, [(Z["u238"] - 0.6, (0, 3, 40), (0, 0, 0), 40), (t2, (-2, 4, 38), (0, 0, 0), 40),
                   (Z["santral"], (0, 6, 50), (1, 0, 0), 44)], aperture=0.2)
    img = ciz(S, cam, t)
    a = win(t, Z["u238"] + 0.1, Z["hizli"] + 0.2)
    label(img, "U-238 + YAVAŞ NÖTRON", 540, 420, a, 66, (205, 214, 228), F_XB)
    cardl(img, ["Eşiğin altında: -1,5 MeV"], 540, 1420, win(t, Z["u238"] + 1.2, Z["hizli"] + 0.2), 54)
    label(img, "BÖLÜNMEZ", 540, 1560, win(t, t1 + 0.4, Z["hizli"] + 0.2), 70, WHITE, F_XB)
    b = win(t, Z["hizli"] + 0.2, Z["santral"] + 0.2)
    label(img, "U-238 + HIZLI NÖTRON", 540, 420, b, 66, CYAN, F_XB)
    cardl(img, ["Yüksek enerjili nötron gerekir"], 540, 1420, b, 50)
    return img


def sh_demet(v, t):
    """ayakta duran 17x17 yakit demeti, yakit isleme salonunda; kamera alttan uste kayar."""
    S = Sahne()
    ic_mekan(S, warm=False)
    S.sun_dir = norm((-0.4, 0.8, 0.6))
    S.sun_col = (2.0, 2.0, 2.05)
    S.amb = 0.6
    S.exposure = 1.1
    S.shadow_box = ((0, 1.9, 0), 2.4)
    S.shadow_bias = 0.0008
    S.ssao_r = 0.05
    S.add(BOX, TRS((0, -0.01, 0), s=(10, 0.02, 10)), Mat(srgb((120, 124, 128)), 0.6, 0.0, pat="beton", scale=1.5))
    S.add(BOX, TRS((0, 3, -2.0), s=(10, 6, 0.1)), Mat(srgb((180, 188, 196)), 0.85, 0.0, pat="boya"))
    S.add(BOX, TRS((0, 0.05, 0), s=(0.5, 0.1, 0.5)), Mat(srgb((200, 170, 40)), 0.5, 0.0, pat="boya"))
    yakit.assembly(S, TRS((0, 0.1, 0)))
    S.light((0.8, 3.6, 1.2), 4.0, (1.0, 0.97, 0.9), 1.5)
    k = sm((t - Z["santral"]) / (Z["yani"] - Z["santral"]))
    eye = np.array((0.55, 0.6, 1.05)) * (1 - k) + np.array((0.5, 3.5, 0.95)) * k
    tgt = np.array((0.0, 0.9, 0.0)) * (1 - k) + np.array((0.0, 3.2, 0.0)) * k
    cam = Cam(eye, tgt, fov=44, near=0.01, aperture=0.2)
    img = ciz(S, cam, t)
    a = win(t, Z["santral"] + 0.1, Z["yani"])
    lines(img, [("SANTRAL YAKITI", WHITE)], 400, a, 76, t=t, t0=Z["santral"])
    cardl(img, ["U-235 ≈ %4"], 540, 540, fade(t, Z["santral"] + 1.6, Z["santral"] + 2.2) * a, 72, amber=True)
    label(img, "Doğal uranyumda %0,7", 540, 660, fade(t, Z["santral"] + 2.4, Z["santral"] + 3.0) * a, 44, WHITE, F_SB)
    label(img, "ZENGİNLEŞTİRME", 540, 1500, win(t, Z["zengin"] + 0.05, Z["yani"]), 80, AMBER, F_XB)
    return img


def sh_son(v, t):
    S = Sahne()
    atom_ortami(S)
    kup(S, t, 1.0, gray_a=0.55)
    ang = 0.9 + t * 0.07
    cam = Cam((math.sin(ang) * 40, 12, math.cos(ang) * 40), (0, 0, 0), fov=40, aperture=0.15)
    img = ciz(S, cam, t)
    stamp(img, "MİT", 540, 430, fade(t, Z["yani"] + 0.05, Z["yani"] + 0.3), RED, 130, pop=0.3 * (1 - fade(t, Z["yani"], Z["yani"] + 0.4)))
    label(img, "Uranyumun hepsi aynı değil", 540, 1400, fade(t, Z["yani"] + 0.5, Z["yani"] + 1.0), 52, WHITE, F_B)
    cardl(img, ["Yavaş nötronla bölünen:", "küçük bir azınlık"], 540, 1540, fade(t, Z["azinlik"], Z["azinlik"] + 0.6), 54, amber=True)
    return img


SHOTS = [(-1.0, sh_pelet), (Z["damga"] - 0.3, sh_kup), (Z["fark"] - 0.1, sh_u235), (Z["u238"] - 0.1, sh_u238),
         (Z["santral"] - 0.1, sh_demet), (Z["yani"] - 0.25, sh_son)]


def frame(t):
    if t >= Z["son"] + 0.7:
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (6, 12, 30)
    else:
        img = shots(t, SHOTS, xf=0.6)
    tag(img, t)
    img = end_card(img, t, Z["son"], [
        "ABD NRC sözlüğü · Uranium · Fissile material",
        "ABD Enerji Bakanlığı (DOE) · DOE-HDBK-1019/1-93:",
        "Nuclear Physics and Reactor Theory",
        "DOE · The Harnessed Atom: Nuclear Energy & Electricity",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_uranyum_bolunur_3d", frame, NFRAMES, NAME)
