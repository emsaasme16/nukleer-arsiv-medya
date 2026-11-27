#!/usr/bin/env python3
"""Gercekci 3D Short: Mit mi, gercek mi? Ay bir stadyuma sigar mi? (ay-bir-stadyuma-sigar-mi.mp4), 1080x1920, 30 fps.

Ses: /tmp/ay/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn).
Kaynak: ABD DOE (Office of Science), "DOE Explains...Nuclei": cekirdek atom hacminin %0,01'inden cok azini kaplar,
kutlenin %99,9'undan fazlasini tasir; butun cekirdekler yaklasik ayni yogunlukta; Ay bu yogunluga sikistirilsa
Yankee Stadium'a sigardi.
Stadyum: genel bir acik beyzbol stadyumu (oval tribun, cim saha, toprak ic saha, isik kuleleri); Ay: kraterli gri kure.
Kullanim: WORK=/tmp/ay python3 render_ay_stadyum_3d.py still 2 12 30 ... | render
"""
from dikey_kit import *
import santral

NAME = "ay-bir-stadyuma-sigar-mi"
TOTAL = 52.58
NFRAMES = int(TOTAL * FPS)
BOLUM = 1

Z = dict(soru=1.1, mit=5.6, deney=7.8, gercek=9.4, sir=10.6, kutle=13.6, hacim=16.6, nokta=21.3, ustelik=24.9,
         abd=28.5, sikis=30.8, amerika=33.1, kutlesi=36.2, bosluk=37.7, yani=41.0, madde=43.7, son=47.4)

TRIBUN = Mat(srgb((44, 74, 128)), 0.6, 0.05, pat="boya", scale=0.4)
TRIBUN_BETON = Mat(srgb((150, 146, 140)), 0.85, pat="beton", scale=0.3)
TOPRAK_S = Mat(srgb((150, 104, 70)), 0.95, pat="toprak", scale=0.4)
CIM_S = Mat(srgb((54, 104, 46)), 0.9, pat="cim", scale=0.12)
AY_MAT = Mat(srgb((112, 110, 106)), 0.95, 0.0, pat="beton", scale=0.05)
AY_KOYU = Mat(srgb((92, 92, 96)), 0.95, 0.0, pat="beton", scale=0.02)
ZEMIN_ASFALT = ZEMIN_MAT.but(col=srgb((38, 38, 40)), pat="asfalt", scale=1.0)
ZEMIN_BETON = ZEMIN_MAT.but(col=srgb((50, 50, 51)), pat="beton", scale=0.35)
SX, SZ = 1.0, 0.86          # oval olcek
BINA = [Mat(srgb((70, 74, 82)), 0.7, 0.1, pat="boya", scale=0.5), Mat(srgb((96, 90, 80)), 0.8, pat="beton", scale=0.3),
        Mat(srgb((54, 60, 70)), 0.5, 0.2, pat="boya", scale=0.5)]


def m_tribun():
    """basamakli tribun halkasi (ic yaricap 1 = 86 m varsayimi ile normalize degil, metre)."""
    pr = [(84.0, 0.0), (84.0, 3.5)]
    r, y = 84.0, 3.5
    for k in range(16):
        r += 2.0
        pr += [(r, y)]
        y += 1.6
        pr += [(r, y)]
    pr += [(r + 4, y), (r + 4, 0.0)]
    return m_lathe(pr, 96, smooth=False)


def m_dis():
    return m_lathe([(121.0, 0.0), (121.0, 30.0), (118.0, 31.0)], 96, smooth=True)


TRB = ("tribun", m_tribun)
DIS = ("stad_dis", m_dis)


def stadyum(S, night=True):
    # zemin mat (2026-11-27 parlama duzeltmesi): koyu, purluzlu, spekulersiz; eski acik gri beton parliyordu
    S.add(BOX, TRS((0, -0.5, 0), s=(3000, 1.0, 3000)), ZEMIN_ASFALT)
    S.add(BOX, TRS((0, -0.3, 0), s=(330, 0.6, 290)), ZEMIN_BETON)
    S.add(CYL, TRS((0, 0.05, 0), s=(86, 0.2, 86 * SZ)), CIM_S)
    S.add(TRB, TRS((0, 0, 0), s=(SX, 1, SZ)), TRIBUN)
    S.add(DIS, TRS((0, 0, 0), s=(SX, 1, SZ)), TRIBUN_BETON)
    # ic saha: toprak elmas + kale cizgileri
    home = np.array([0.0, 0.2, 55.0])
    S.add(BOX, TRS(tuple(home + (0, 0, -19)), R=ry(math.pi / 4), s=(27, 0.1, 27)), TOPRAK_S)
    S.add(BOX, TRS(tuple(home + (0, 0.04, -19)), R=ry(math.pi / 4), s=(21, 0.1, 21)), CIM_S)
    S.add(CYL, TRS(tuple(home + (0, 0.1, -19)), s=(3, 0.12, 3)), TOPRAK_S)
    for k in (-1, 1):
        S.add(BOX, TRS(tuple(home + (k * 40, 0.12, -40)), R=ry(-k * math.pi / 4), s=(0.25, 0.05, 115)),
              Mat((0.9, 0.9, 0.9), 0.6, emi=(0.15, 0.15, 0.15)))
    # isik kuleleri
    on = 1.0 if night else 0.0
    for i in range(6):
        a = 2 * math.pi * (i + 0.5) / 6
        p = np.array([math.cos(a) * 128 * SX, 0, math.sin(a) * 128 * SZ])
        S.add(CYL_LO, TRS(tuple(p + (0, 26, 0)), s=(1.1, 52, 1.1)), santral.CELIK_KOYU)
        R = ry(-a + math.pi / 2)
        S.add(BOX, TRS(tuple(p + (0, 53, 0)), R=R, s=(12, 5, 1.0)), santral.CELIK_KOYU)
        S.add(BOX, TRS(tuple(p + (0, 53, 0) - 0.6 * norm((p[0], 0, p[2]))), R=R, s=(11, 4.2, 0.3)),
              Mat((1, 1, 1), 0.3, emi=(9 * on, 8.6 * on, 7.8 * on)))
        if on:
            q = p + (0, 53, 0) - 2.0 * norm((p[0], 0, p[2]))
            S.particle(tuple(q), 16, (1.0, 0.95, 0.85, 0.45), kind=0, add=True)
            S.light(tuple(q * 0.7 + np.array([0, 10, 0])), 200, (1.0, 0.96, 0.9), 1.1)
    for i in range(48):                   # dis cephe kolonlari
        a = 2 * math.pi * i / 48
        p = np.array([math.cos(a) * 121.6 * SX, 15, math.sin(a) * 121.6 * SZ])
        S.add(BOX, TRS(tuple(p), R=ry(-a), s=(1.6, 30, 2.2)), santral.BETON_KOYU)
    S.add(("stad_cati", lambda: m_lathe([(104.0, 31.5), (122.0, 33.0)], 96, smooth=True)), TRS((0, 0, 0), s=(SX, 1, SZ)),
          santral.CELIK_KOYU.but(cast=False))
    # cevre binalari
    rng = np.random.default_rng(5)
    for k in range(26):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(220, 520)
        h = rng.uniform(14, 60)
        T_ = TRS((math.cos(a) * d, 0, math.sin(a) * d), R=ry(rng.uniform(0, 3)))
        santral.building(S, T_, rng.uniform(25, 50), h, rng.uniform(20, 40), mat=BINA[k % 3],
                         windows=6, lit=0.8 if night else 0.0)


def ay(S, c, r):
    S.add(SPH, TRS(tuple(c), s=r), AY_MAT)
    rng = np.random.default_rng(9)


def gece_ortam(S):
    gece(S, moon=0.0)
    S.sun_dir = norm((0.5, 0.45, 0.6))
    S.sun_col = (0.55, 0.6, 0.75)
    S.amb = 0.7
    S.exposure = 1.0
    S.shadow_box = ((0, 10, 0), 300)    # 160 zemin betonunun disini kapsamiyordu: sinirda keskin aydinlik takozlar
    S.shadow_bias = 0.002
    S.ssao_r = 1.2
    S.fog = (0.0012, 0.02, 0.0, 0.6)


_e = np.array([math.sin(0.66) * 680, 245, math.cos(0.66) * 680])
_f = norm(np.array([-40, 170, 0]) - _e)
_r = norm(np.cross(_f, (0, 1, 0)))
AY_GOK = (_e + _f * 2600 + _r * 380 + np.array([0, 520, 0]), 150.0)
AY_STAD = (np.array([0.0, 52.0, -6.0]), 52.0)
CAM_STAD = [(0.0, (380, 250, 520), (0, 60, 0), 46)]


def sh_gece(v, t, son=False):
    S = Sahne()
    gece_ortam(S)
    stadyum(S)
    ay(S, *AY_GOK)
    ang = 0.62 + 0.012 * t
    d = 700 - 40 * sm(t / 10)
    eye = (math.sin(ang) * d, 240 + 10 * t * 0.1, math.cos(ang) * d)
    cam = Cam(eye, (-40, 170, 0), fov=50, near=1.0, far=6000, aperture=0.05)
    if t < 0:
        pass
    img = ciz(S, cam, t)
    if not son:
        lines(img, [("AY, BİR STADYUMA", WHITE), ("SIĞAR MI?", AMBER)], 400, win(t, 0.2, Z["mit"]), 86, t=t, t0=0.2)
        label(img, "MİT Mİ, GERÇEK Mİ?", 540, 450, win(t, Z["mit"] + 0.05, Z["gercek"] - 0.2), 74, CYAN, F_XB)
        stamp(img, "GERÇEK", 540, 430, fade(t, Z["gercek"] - 0.2, Z["gercek"] + 0.05), GREEN, 120,
              pop=0.3 * (1 - fade(t, Z["gercek"] - 0.2, Z["gercek"] + 0.2)))
        label(img, "Bir düşünce deneyi olarak", 540, 600, fade(t, Z["gercek"] - 0.1, Z["gercek"] + 0.4), 50, WHITE, F_SB)
    return img


def sh_son(v, t):
    tt = t - Z["yani"]
    img = sh_gece(v, 14 + tt * 0.6, son=True)
    lines(img, [("AY'IN HACMİ:", WHITE), ("ÇOĞUNLUKLA", WHITE), ("BOŞLUK", AMBER)], 400, fade(tt, 0.1, 0.6), 90, t=tt, t0=0.1)
    cardl(img, ["Madde değil, çekirdekler", "arasındaki boşluk"], 540, 1500, fade(tt, Z["madde"] - Z["yani"], Z["madde"] - Z["yani"] + 0.6), 50, amber=True)
    return img


ELEK = None


def bulut(S, R, t, a=1.0):
    global ELEK
    if ELEK is None:
        rng = np.random.default_rng(4)
        v = rng.normal(0, 1, (420, 3))
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        ELEK = v * rng.uniform(0.35, 1.0, (420, 1)) ** 0.5
    for i, p in enumerate(ELEK):
        S.particle(tuple(p * R), R * 0.16, (0.35, 0.6, 1.0, 0.05 * a), kind=0, add=True)
    for k in range(6):
        ph = t * (0.9 + 0.13 * k) + k * 1.7
        ax = norm((math.sin(k * 2.1), math.cos(k * 1.3), math.sin(k * 0.7 + 1)))
        b1 = norm(np.cross(ax, (0.3, 1, 0.2)))
        b2 = np.cross(ax, b1)
        p = (b1 * math.cos(ph) + b2 * math.sin(ph)) * R * (0.6 + 0.07 * k)
        S.particle(tuple(p), R * 0.035, (0.6, 0.85, 1.0, 0.9 * a), kind=0, add=True)


def sh_atom(v, t):
    S = Sahne()
    atom_ortami(S)
    c = atom.get("C12")
    atom.draw(S, c.P, c.isp, (0, 0, 0), R=ry(t * 0.3) @ rx(0.4))
    R_at = 140.0
    bulut(S, R_at, t, a=fade(t, Z["sir"] + 2.0, Z["sir"] + 5.5))
    atom.dust(S, t, n=80, R=200, a=0.10)
    k = sm((t - Z["sir"] - 0.8) / 8.5)
    d = 10 * (1 - k) + 420 * k
    ang = 0.3 + t * 0.04
    cam = Cam((math.sin(ang) * d, d * 0.18, math.cos(ang) * d), (0, 0, 0), fov=42, near=0.3, far=4000, aperture=0.15 * (1 - k))
    img = ciz(S, cam, t)
    lines(img, [("SIR, ÇEKİRDEKTE", WHITE)], 400, win(t, Z["sir"] + 0.1, Z["kutle"]), 80, t=t, t0=Z["sir"])
    cardl(img, ["Kütlenin", "%99,9'undan fazlası"], 540, 440, win(t, Z["kutle"], Z["ustelik"] - 0.2), 56, amber=True)
    cardl(img, ["Hacmin", "%0,01'inden çok azı"], 540, 1480, win(t, Z["hacim"] + 1.2, Z["ustelik"] - 0.2), 56)
    p = proj(cam, (0, 0, 0))
    label(img, "ÇEKİRDEK", p[0], p[1] + 120, win(t, Z["nokta"], Z["ustelik"] - 0.2), 40, WHITE, F_B)
    label(img, "ELEKTRON BULUTU", 540, 1180, win(t, Z["nokta"] + 0.5, Z["ustelik"] - 0.2), 40, CYAN, F_B)
    return img


def sh_uc(v, t):
    S = Sahne()
    atom_ortami(S)
    pos = [(0, 19.0, 0), (0, 0.0, 0), (0, -20.0, 0)]
    for key, p, sd in zip(("C12", "FE56", "U235"), pos, (0.0, 1.0, 2.0)):
        c = atom.get(key)
        atom.draw(S, c.P, c.isp, p, R=ry(t * 0.3 + sd) @ rx(0.3))
    atom.dust(S, t, n=100, R=60, a=0.12)
    cam = Cam((0, 12, 132 - 6 * sm((t - Z["ustelik"]) / 4)), (7, 10, 0), fov=40, aperture=0.1)
    img = ciz(S, cam, t)
    lines(img, [("BÜTÜN ÇEKİRDEKLER", WHITE)], 420, win(t, Z["ustelik"], Z["abd"] + 0.2), 76, t=t, t0=Z["ustelik"])
    cardl(img, ["≈ aynı yoğunlukta"], 540, 560, win(t, Z["ustelik"] + 0.9, Z["abd"] + 0.2), 62, amber=True)
    for nm, p in zip(("C-12", "Fe-56", "U-235"), pos):
        q = proj(cam, (p[0] + 13, p[1], 0))
        label(img, nm, q[0] + 40, q[1], win(t, Z["ustelik"] + 0.5, Z["abd"] + 0.2), 46, WHITE, F_B)
    return img


def sh_sikis(v, t):
    S = Sahne()
    gece_ortam(S)
    stadyum(S)
    k = sm((t - (Z["sikis"] - 0.4)) / 5.2)
    c0, r0 = AY_GOK
    c1, r1 = AY_STAD
    c = c0 * (1 - k) + c1 * k
    r = math.exp(math.log(r0) * (1 - k) + math.log(r1) * k)
    ay(S, c, r)
    if k > 0.9:
        S.particle(tuple(c1 + (0, -r1 * 0.6, 0)), 160, (0.7, 0.8, 1.0, 0.10 * fade(k, 0.9, 1.0)), kind=0, add=True)
    u = t - Z["abd"]
    ang = 0.64 + 0.012 * u
    d = 660 - 140 * sm((t - Z["sikis"]) / 6)
    eye = (math.sin(ang) * d, 250 - 30 * sm((t - Z["sikis"]) / 6), math.cos(ang) * d)
    tgt = (-40 * (1 - k), 170 * (1 - k) + 40 * k, 0)
    cam = Cam(eye, tgt, fov=50, near=1.0, far=6000, aperture=0.05)
    img = ciz(S, cam, t)
    label(img, "ABD ENERJİ BAKANLIĞI (DOE):", 540, 360, win(t, Z["abd"] + 0.1, Z["kutlesi"]), 46, CYAN, F_B)
    lines(img, [("AY, ÇEKİRDEK", WHITE), ("YOĞUNLUĞUNA", WHITE), ("SIKIŞTIRILSAYDI", AMBER)], 450,
          win(t, Z["sikis"] - 0.6, Z["amerika"]), 74, t=t, t0=Z["sikis"] - 0.6)
    lines(img, [("YANKEE STADIUM'A", AMBER), ("SIĞARDI", WHITE)], 450, win(t, Z["amerika"], Z["kutlesi"]), 80, t=t, t0=Z["amerika"])
    cardl(img, ["Kütle: aynı"], 540, 470, win(t, Z["kutlesi"], Z["yani"] + 0.2), 66, amber=True)
    cardl(img, ["Çekirdekler arasındaki", "boşluk: yok"], 540, 640, win(t, Z["bosluk"], Z["yani"] + 0.2), 52)
    return img


SHOTS = [(-1.0, sh_gece), (Z["sir"] - 0.2, sh_atom), (Z["ustelik"] - 0.2, sh_uc), (Z["abd"] - 0.3, sh_sikis),
         (Z["yani"] - 0.1, sh_son)]


def frame(t):
    if t >= Z["son"] + 0.7:
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (6, 12, 30)
    else:
        img = shots(t, SHOTS, xf=0.6)
    tag(img, t)
    img = end_card(img, t, Z["son"], [
        "ABD Enerji Bakanlığı (DOE), Office of Science",
        "DOE Explains...Nuclei",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_ay_stadyum_3d", frame, NFRAMES, NAME)
