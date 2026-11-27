#!/usr/bin/env python3
"""Gercekci 3D Short: 60 saniyede: Bir fisyon ne kadar surer? (bir-fisyon-ne-kadar-surer.mp4), 1080x1920, 30 fps.

Ses: /tmp/fisyon/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn).
Kaynak: DOE-HDBK-1019/1-93: "In water moderated reactors, thermal neutrons tend to exist for about 10-4 seconds before
they are absorbed. Fission and fast neutron production following neutron absorption in a fissionable nucleus occurs in
about 10-13 seconds."; "the average total energy released per fission of uranium-235 with a thermal neutron is 200 MeV";
Tablo 6 "Kinetic Energy of Fission Products 167 MeV"; "The fission fragments ... cause ionization directly as they rip
orbital electrons from the surrounding atoms ... resulting in an increase in temperature."
Modeller: ../uzun_3d/modeller/yakit.py (17x17 demet, pelet; NRC Reactor Concepts Manual tarifi), atom.py (U-235 -> Rb-93 + Cs-140 + 3n).
Kullanim: WORK=/tmp/fisyon python3 render_fisyon_sure_3d.py still 2 10 ... | render
"""
from dikey_kit import *

NAME = "bir-fisyon-ne-kadar-surer"
TOTAL = 50.34
NFRAMES = int(TOTAL * FPS)
BOLUM = 2

Z = dict(soru=1.1, cevap=4.6, suyla=8.3, binde=12.7, sonra=15.7, yakalanma=18.9, tril=23.6, enerji=26.3, mev=27.8,
         bunun=30.7, parcalar=34.3, elektron=36.1, hareket=38.2, santral=40.7, son=45.2)
S_N = 0.62


def us(img, base, ex, suf, x, y, a, size=120, col=AMBER):
    """ust simgeli sayi: base^ex + suf, ortalanmis."""
    if a <= 0.003:
        return
    sb = T(base, F_XB, size, col)
    se = T(ex, F_XB, int(size * 0.55), col)
    ss = T(suf, F_XB, size, col)
    wb, we, ws = sb[1].shape[1], se[1].shape[1], ss[1].shape[1]
    pad = int(size * 0.22)
    tot = wb + we + ws - 4 * pad
    x0 = x - tot / 2
    blit(img, sb, x0 + wb / 2, y, op=a)
    blit(img, se, x0 + wb - pad * 1.6 + we / 2, y - size * 0.36, op=a)
    blit(img, ss, x0 + wb + we - pad * 3.4 + ws / 2, y, op=a)


def demet_sahne(t, glow=0.0):
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
    return S


def sh_acilis(v, t):
    S = demet_sahne(t)
    k = sm(t / 9.0)
    eye = np.array((0.5, 3.4, 0.95)) * (1 - k) + np.array((0.45, 1.2, 0.75)) * k
    tgt = np.array((0.0, 3.1, 0.0)) * (1 - k) + np.array((0.0, 1.4, 0.0)) * k
    cam = Cam(eye, tgt, fov=44, near=0.01, aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("BİR FİSYON", WHITE), ("NE KADAR SÜRER?", AMBER)], 400, win(t, 0.2, Z["cevap"]), 86, t=t, t0=0.2)
    a = win(t, Z["cevap"], Z["suyla"] + 0.2)
    us(img, "≈ 10", "-13", "s", 540, 430, a, 130)
    label(img, "saniyenin on trilyonda biri", 540, 580, a, 52, WHITE, F_SB)
    return img


def sh_son(v, t):
    S = demet_sahne(t)
    u = t - Z["santral"]
    k = sm(u / 6)
    eye = np.array((0.55, 0.6, 1.05)) * (1 - k) + np.array((0.6, 2.0, 1.3)) * k
    tgt = np.array((0.0, 0.9, 0.0)) * (1 - k) + np.array((0.0, 1.8, 0.0)) * k
    cam = Cam(eye, tgt, fov=44, near=0.01, aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("SANTRALİN ISISI", WHITE), ("BU ANDA BAŞLAR", AMBER)], 400, fade(u, 0.1, 0.6), 82, t=u, t0=0.1)
    return img


_rng = np.random.default_rng(21)
MOL = _rng.uniform(-1, 1, (70, 3)) * np.array([26, 40, 14])
MOL_R = [ry(_rng.uniform(0, 6)) @ rx(_rng.uniform(0, 6)) for _ in range(70)]
YOL_N = np.cumsum(np.vstack([[[-14, -30, 0]], _rng.normal(0, 1, (14, 3)) * np.array([9, 6, 3])]), 0)
O_MAT = Mat(srgb((120, 130, 150)), 0.35, 0.0, emi=(0.02, 0.025, 0.04))
H_MAT = Mat(srgb((225, 228, 236)), 0.3, 0.0, emi=(0.03, 0.03, 0.035))


def yol_at(u):
    n = len(YOL_N) - 1
    x = clamp01(u) * n
    i = min(n - 1, int(x))
    f = x - i
    return YOL_N[i] * (1 - f) + YOL_N[i + 1] * f


def sh_su(v, t):
    S = Sahne()
    atom_ortami(S)
    for p, R in zip(MOL, MOL_R):
        S.add(SPH_LO, TRS(tuple(p), s=1.3), O_MAT)
        for sg in (-1, 1):
            S.add(SPH_LO, TRS(tuple(p + R @ np.array([sg * 1.25, 0.95, 0])), s=0.75), H_MAT)
    u = fade(t, Z["suyla"] - 0.3, Z["sonra"] + 0.3)
    q = yol_at(u)
    atom.neutron(S, q, 0.9, glow=1.5, trail=[yol_at(u - 0.006 * j) for j in range(1, 24)])
    atom.dust(S, t, n=80, R=50, a=0.1)
    cam = Cam((q[0] * 0.4, q[1] * 0.4 + 2, 70), (q[0] * 0.4, q[1] * 0.4, 0), fov=44, aperture=0.15)
    img = ciz(S, cam, t)
    lines(img, [("SUDA YAVAŞLAMIŞ", WHITE), ("BİR NÖTRON", CYAN)], 400, win(t, Z["suyla"], Z["sonra"]), 80, t=t, t0=Z["suyla"])
    a = win(t, Z["binde"] - 0.3, Z["sonra"])
    cardl(img, ["Yakalanmadan önce dolaşır:"], 540, 1420, a, 46)
    us(img, "≈ 10", "-4", "s", 540, 1560, a, 100, CYAN)
    label(img, "saniyenin on binde biri", 540, 1680, a, 44, WHITE, F_SB)
    return img


SPLIT = None


def split_pts(t, t0, spd=1.0):
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    src, dst, grp, isp, cap = SPLIT
    sep = fade(t, t0, t0 + 3.0 / spd)
    far = max(0.0, t - (t0 + 3.0 / spd)) * 2.4 * spd
    Q = src.copy()
    if sep > 0:
        cen = np.array([[-9.5, 0, 0], [12.5, 0, 0]])
        out = Q.copy()
        for i in range(len(Q)):
            if grp[i] < 2:
                tgt = dst[i] + cen[grp[i]]
                dirc = np.sign(cen[grp[i]][0]) * np.array([1.0, 0, 0])
                out[i] = Q[i] * (1 - sm(sep * 1.4)) + tgt * sm(sep * 1.4) + cen[grp[i]] * sep * 0.8 + dirc * far
            else:
                d = np.array([0.2, 1.0, 0.3]) if i % 3 == 0 else (np.array([0.1, -0.8, 0.7]) if i % 3 == 1 else np.array([-0.2, 0.3, -1.0]))
                out[i] = Q[i] + d * (sep * 22 + far * 3)
        Q = out
    return Q, grp, isp, cap, sep


def sh_yakalama(v, t, enerji=False):
    S = Sahne()
    atom_ortami(S)
    t0 = Z["yakalanma"] + 1.4
    Q, grp, isp, cap, sep = split_pts(t, t0)
    Rr = rz(math.pi / 2) @ ry(0.2 + t * 0.03)
    pts = (Q @ Rr.T) * S_N
    hot = fade(t, Z["yakalanma"], t0) * (1 - 0.5 * sep)
    wob = 0.05 * math.sin(t * 9) * fade(t, Z["yakalanma"], t0) * (1 - sep)
    pts = pts * (1 + np.array([wob, -wob * 0.6, -wob * 0.6]))
    for i in range(len(pts)):
        if i == cap and t < Z["yakalanma"]:
            continue
        if grp[i] == 2 and sep > 0:
            atom.neutron(S, pts[i], S_N, glow=1.3)
            continue
        m = atom.PROTON if isp[i] else atom.NEUTRON
        if hot > 0:
            e = hot * (0.6 + 0.3 * math.sin(t * 9 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (0.6 * e, 0.26 * e, 0.06 * e))))
        S.add(SPH, TRS(tuple(pts[i]), s=S_N), m)
    if t < Z["yakalanma"]:
        k = fade(t, Z["sonra"] - 0.3, Z["yakalanma"])
        q = pts[cap] + np.array([3.0, -40.0, 0]) * (1 - k)
        atom.neutron(S, q, S_N, glow=1.4, trail=[q + np.array([0.075, -1.0, 0]) * j for j in range(1, 22)])
    if sep > 0:
        S.particle((0, 0, 0), 34 * sep + 6, (1.0, 0.8, 0.5, min(1.0, 2.6 * sep * (1 - sep))), add=True)
    if enerji:
        for g in (0, 1):
            c = pts[grp == g].mean(0)
            S.particle(tuple(c), 16, (1.0, 0.7, 0.4, 0.25), add=True)
    atom.dust(S, t, n=140, R=60, a=0.16)
    if enerji:
        cam = Cam((0, 3, 92), (0, 0, 0), fov=46, aperture=0.1)
    else:
        cam = path(t, [(Z["sonra"] - 0.6, (0, -6, 46), (0, -4, 0), 42), (t0, (2, 2, 40), (0, 0, 0), 40),
                       (Z["enerji"], (0, 4, 70), (0, 0, 0), 44)], aperture=0.2)
    img = ciz(S, cam, t)
    if not enerji:
        label(img, "U-235", 540, 420, win(t, Z["sonra"] + 0.2, Z["yakalanma"]), 80, AMBER, F_XB)
        lines(img, [("YAKALANMA", WHITE), ("VE BÖLÜNME", AMBER)], 400, win(t, Z["yakalanma"], Z["enerji"]), 80, t=t, t0=Z["yakalanma"])
        a = win(t, Z["tril"] - 1.2, Z["enerji"])
        us(img, "≈ 10", "-13", "s", 540, 1500, a, 120)
        label(img, "saniyenin on trilyonda biri", 540, 1640, a, 48, WHITE, F_SB)
        label(img, "+ yeni hızlı nötronlar", 540, 1740, win(t, t0 + 0.8, Z["enerji"]), 42, CYAN, F_SB)
    else:
        a = win(t, Z["enerji"] + 0.1, Z["parcalar"])
        label(img, "BİR BÖLÜNMEDE", 540, 380, a, 64, WHITE, F_XB)
        cardl(img, ["≈ 200 MeV"], 540, 510, fade(t, Z["mev"] - 0.3, Z["mev"] + 0.2) * a, 80, amber=True)
        b = win(t, Z["bunun"], Z["parcalar"])
        label(img, "Parçaların hareketi: 167 MeV", 540, 1440, b, 50, WHITE, F_B)
        bar(img, 140, 1530, 800, 1.0, (60, 70, 90), 46, b)
        bar(img, 140, 1530, 800, 167 / 200 * fade(t, Z["bunun"] + 0.3, Z["bunun"] + 1.6), AMBER, 46, b)
        label(img, "167 / 200", 540, 1610, b, 42, AMBER, F_SB)
    return img


def sh_enerji(v, t):
    return sh_yakalama(v, t, enerji=True)


TEPSI = Mat(srgb((168, 170, 174)), 0.3, 1.0, pat="fircali")
MASA = Mat(srgb((60, 64, 70)), 0.6, 0.2, pat="boya")


def sh_isi(v, t):
    """kesitli yakit cubugu icinde peletler; isinma kizil-turuncu parlamayla."""
    S = Sahne()
    ic_mekan(S, warm=True)
    S.sun_dir = norm((-0.3, 0.9, 0.45))
    S.sun_col = (1.6, 1.5, 1.4)
    S.amb = 0.35
    S.shadow_box = ((0, 0.0, 0), 0.12)
    S.shadow_bias = 0.0004
    S.ssao_r = 0.006
    S.bloom = 0.9
    g = fade(t, Z["hareket"] - 1.0, Z["santral"])
    S.add(BOX, TRS((0, -0.004, 0), s=(0.6, 0.008, 0.4)), MASA)
    S.add(BOX, TRS((0, 0.0005, 0), s=(0.16, 0.001, 0.07)), TEPSI)
    pel = yakit.SERAMIK.but(col=srgb((70, 68, 66)), rough=0.55)
    for c in range(12):
        x = -0.066 + c * 0.0112
        e = g * (0.8 + 0.2 * math.sin(t * 2 + c))
        yakit.pellet(S, (x, 0.001 + yakit.PEL_H / 2, 0.0), mat=pel.but(emi=(2.6 * e, 0.9 * e, 0.25 * e)))
        if e > 0:
            S.particle((x, 0.006, 0.0), 0.012, (1.0, 0.55, 0.2, 0.25 * e), add=True)
    u = t - Z["parcalar"]
    k = sm(u / 7)
    eye = np.array((0.05, 0.05, 0.11)) * (1 - k) + np.array((0.012, 0.016, 0.04)) * k
    cam = Cam(eye, (0.0, 0.005, 0.0), fov=34, near=0.002, aperture=0.4)
    img = ciz(S, cam, t)
    lines(img, [("PARÇALAR ÇEVREDEKİ", WHITE), ("ATOMLARDAN", WHITE), ("ELEKTRON KOPARIR", AMBER)], 400,
          win(t, Z["parcalar"] + 0.05, Z["hareket"]), 74, t=t, t0=Z["parcalar"])
    lines(img, [("YAKIT ISINIR", AMBER)], 420, win(t, Z["hareket"], Z["santral"] + 0.2), 96, t=t, t0=Z["hareket"])
    return img


SHOTS = [(-1.0, sh_acilis), (Z["suyla"] - 0.2, sh_su), (Z["sonra"] - 0.3, sh_yakalama), (Z["enerji"] - 0.2, sh_enerji),
         (Z["parcalar"] - 0.2, sh_isi), (Z["santral"] - 0.2, sh_son)]


def frame(t):
    if t >= Z["son"] + 0.7:
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (6, 12, 30)
    else:
        img = shots(t, SHOTS, xf=0.6)
    tag(img, t)
    img = end_card(img, t, Z["son"], [
        "ABD Enerji Bakanlığı (DOE) · DOE-HDBK-1019/1-93:",
        "Nuclear Physics and Reactor Theory",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_fisyon_sure_3d", frame, NFRAMES, NAME)
