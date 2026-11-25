"""Santral dis yapilari. Olculer metre; tarif: NRC Reactor Concepts Manual (PWR koruma kabi, kum saati
bicimli dogal cekisli kule "several hundred feet tall"). Ayrinti kaynakta yoksa sade geometri."""
import math
import numpy as np
from gercekci import *

BETON = Mat(srgb((168, 164, 156)), 0.88, pat="beton", scale=0.35)
BETON_KOYU = Mat(srgb((128, 124, 118)), 0.9, pat="beton", scale=0.35)
PANEL = Mat(srgb((150, 158, 168)), 0.55, 0.15, pat="boya", scale=0.5)
PANEL_BEJ = Mat(srgb((196, 186, 160)), 0.6, 0.1, pat="boya", scale=0.5)
CELIK = Mat(srgb((140, 142, 146)), 0.35, 1.0, pat="fircali", scale=1.0)
CELIK_KOYU = Mat(srgb((70, 72, 76)), 0.5, 0.9)
CAM = Mat(srgb((30, 40, 50)), 0.08, 0.0)
ASFALT = Mat(srgb((48, 48, 50)), 0.9, pat="asfalt", scale=1.0)
CIM = Mat(srgb((70, 88, 48)), 0.95, pat="cim", scale=0.15)
TOPRAK = Mat(srgb((110, 96, 78)), 0.95, pat="toprak", scale=0.3)


def P(S, T, mesh, M, mat):
    S.add(mesh, T @ M, mat)


def tower_mesh(h=150.0):
    rb, rt, rtop = 0.42 * h * 0.62, 0.26 * h * 0.62, 0.29 * h * 0.62
    return ("kule_%d" % int(h), lambda: m_hyperboloid(rb, rt, rtop, h - 10.0, (h - 10.0) * 0.78, 72, 48, 0.0))


def cooling_tower(S, T, h=150.0, mat=BETON, steam=None, t=0.0, steam_col=(0.85, 0.87, 0.9), steam_a=0.5):
    """dogal cekisli kule: kabuk 10 m yukseklikte X kolonlar uzerinde baslar; tabanda su havuzu."""
    rb = 0.42 * h * 0.62
    S.add(tower_mesh(h), T @ TRS((0, 10.0, 0)), mat)
    n = 48
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        p0 = np.array([math.cos(a0) * rb, 0, math.sin(a0) * rb])
        p1 = np.array([math.cos(a1) * rb, 10.2, math.sin(a1) * rb])
        p2 = np.array([math.cos(a1) * rb, 0, math.sin(a1) * rb])
        p3 = np.array([math.cos(a0) * rb, 10.2, math.sin(a0) * rb])
        S.add(CYL_LO, T @ align(p0, p1, 0.45), mat)
        S.add(CYL_LO, T @ align(p2, p3, 0.45), mat)
    S.add(("havuz_kenar", lambda: m_lathe([(1.0, 0), (1.0, 1.0), (1.03, 1.0), (1.03, 0)], 72)),
          T @ TRS((0, 0, 0), s=(rb + 3, 1.2, rb + 3)), BETON_KOYU)
    S.add(PLANE, T @ TRS((0, 0.6, 0), s=(2 * rb + 5, 1, 2 * rb + 5)),
          Mat(srgb((40, 50, 55)), 0.15, pat="su", scale=0.3))
    if steam is not None:
        top = h
        rtop = 0.29 * h * 0.62
        rng = np.random.default_rng(7)
        N = 70
        for k in range(N):
            ph = (k / N + t * steam) % 1.0
            ang = rng.uniform(0, 6.28)
            rr = rng.uniform(0, 0.8) * rtop
            drift = np.array([1.0, 0, 0.3]) * ph * h * 0.9
            pos = np.array([math.cos(ang) * rr, top + ph * h * 0.75, math.sin(ang) * rr]) + drift
            size = rtop * (0.55 + 1.6 * ph)
            a = steam_a * (1 - ph) ** 1.3 * min(1.0, ph * 8)
            S.particle(tuple((T @ np.append(pos, 1))[:3]), size, (*steam_col, a), kind=1, seed=k * 0.71 + ph,
                       rot=k * 1.7)


def containment_pwr(S, T, r=21.0, h=48.0, mat=BETON, alpha=1.0):
    """buyuk kuru PWR koruma kabi: dikey silindir + yari kure kubbe, kubbe tabani bilezik, gergi kolonlari."""
    m = mat.but(alpha=alpha)
    S.add(("kab_govde", lambda: m_lathe([(1, 0), (1, 1)], 96)), T @ TRS((0, 0, 0), s=(r, h, r)), m)
    S.add(("kubbe", lambda: m_lathe([(math.cos(a), math.sin(a)) for a in np.linspace(0, math.pi / 2, 24)], 96)),
          T @ TRS((0, h, 0), s=(r * 1.001, r * 0.92, r * 1.001)), m)
    S.add(("bilezik", lambda: m_lathe([(1.0, 0), (1.04, 0), (1.04, 1), (1.0, 1)], 96, smooth=False)),
          T @ TRS((0, h - 1.2, 0), s=(r, 1.4, r)), m.but(col=tuple(c * 0.9 for c in mat.col)))
    for i in range(3):        # 3 gergi kolonu (buttress)
        a = 2 * math.pi * i / 3 + 0.4
        S.add(BOX, T @ TRS((math.cos(a) * (r + 0.6), h / 2, math.sin(a) * (r + 0.6)), ry(-a), (1.6, h, 2.4)), m)
    # ekipman kapagi
    S.add(CYL, T @ TRS((r * math.cos(2.3), 9, r * math.sin(2.3)), ry(-2.3) @ rz(math.pi / 2), (3.2, 1.6, 3.2)),
          CELIK_KOYU.but(alpha=alpha))


def building(S, T, w, h, d, mat=PANEL, roof=BETON_KOYU, doors=0, windows=0, t=0.0, lit=0.0):
    S.add(BOX, T @ TRS((0, h / 2, 0), s=(w, h, d)), mat)
    S.add(BOX, T @ TRS((0, h + 0.4, 0), s=(w + 0.6, 0.8, d + 0.6)), roof)
    for i in range(doors):
        x = -w / 2 + w * (i + 1) / (doors + 1)
        S.add(BOX, T @ TRS((x, 3.0, d / 2 + 0.05), s=(4.5, 6, 0.1)), Mat(srgb((110, 112, 116)), 0.5, 0.6, pat="boya", scale=3))
    for i in range(windows):
        x = -w / 2 + w * (i + 0.5) / windows
        e = (1.0, 0.8, 0.55) if (lit > 0 and (i * 7) % 3 != 0) else (0, 0, 0)
        S.add(BOX, T @ TRS((x, h * 0.72, d / 2 + 0.06), s=(w / windows * 0.6, 1.6, 0.1)),
              CAM.but(emi=tuple(c * lit for c in e)))


def lamp_post(S, T, h=9.0, on=1.0):
    S.add(CYL_LO, T @ TRS((0, h / 2, 0), s=(0.12, h, 0.12)), CELIK_KOYU)
    S.add(BOX, T @ TRS((0.6, h, 0), s=(1.4, 0.18, 0.3)), CELIK_KOYU)
    S.add(BOX, T @ TRS((1.1, h - 0.12, 0), s=(0.5, 0.06, 0.25)), Mat((1, 1, 1), 0.3, emi=(6 * on, 4.8 * on, 3.2 * on)))
    if on > 0:
        p = (T @ np.array([1.1, h - 0.4, 0, 1]))[:3]
        S.particle(tuple(p), 1.6, (1.0, 0.8, 0.55, 0.35 * on), kind=0, add=True)


def human(S, T, col=(0.75, 0.55, 0.15), helmet=(0.95, 0.95, 0.9), walk=0.0):
    """sade, oranli insan figuru (1,75 m), is kiyafeti ve baret."""
    skin = Mat(srgb((190, 150, 120)), 0.6)
    cloth = Mat(col, 0.8)
    pants = Mat(srgb((45, 55, 75)), 0.85)
    sw = math.sin(walk) * 0.35
    for s, side in ((-1, sw), (1, -sw)):
        hip = np.array([0.1 * s, 0.92, 0])
        foot = hip + np.array([0, -0.88, 0.0]) + np.array([0, 0, side * 0.5])
        S.add(CYL_LO, T @ align(hip, foot, 0.075), pants)
        S.add(BOX, T @ TRS(tuple(foot + np.array([0, 0.04, 0.06])), s=(0.11, 0.08, 0.26)), CELIK_KOYU)
    S.add(CYL_LO, T @ TRS((0, 1.2, 0), s=(0.19, 0.6, 0.13)), cloth)
    S.add(SPH_LO, T @ TRS((0, 1.5, 0), s=(0.2, 0.08, 0.13)), cloth)
    for s, side in ((-1, -sw), (1, sw)):
        sh = np.array([0.23 * s, 1.47, 0])
        hand = sh + np.array([0.04 * s, -0.62, side * 0.35])
        S.add(CYL_LO, T @ align(sh, hand, 0.055), cloth)
        S.add(SPH_LO, T @ TRS(tuple(hand), s=0.05), skin)
    S.add(SPH_LO, T @ TRS((0, 1.66, 0), s=(0.1, 0.12, 0.11)), skin)
    S.add(SPH_LO, T @ TRS((0, 1.73, 0), s=(0.125, 0.07, 0.135)), Mat(helmet, 0.35))


def car(S, T, col=(0.55, 0.05, 0.05), lights=0.0):
    paint = Mat(col, 0.25, 0.6)
    S.add(BOX, T @ TRS((0, 0.62, 0), s=(1.8, 0.62, 4.4)), paint)
    S.add(BOX, T @ TRS((0, 1.15, -0.2), s=(1.6, 0.5, 2.3)), paint)
    S.add(BOX, T @ TRS((0, 1.15, -0.2), s=(1.62, 0.42, 2.0)), CAM)
    for x in (-0.85, 0.85):
        for z in (-1.4, 1.4):
            S.add(CYL, T @ TRS((x, 0.34, z), rz(math.pi / 2), (0.34, 0.25, 0.34)), Mat((0.03, 0.03, 0.03), 0.8))
    if lights > 0:
        for x in (-0.6, 0.6):
            S.add(BOX, T @ TRS((x, 0.7, 2.21), s=(0.35, 0.12, 0.02)), Mat((1, 1, 1), 0.2, emi=(8 * lights, 7.5 * lights, 6 * lights)))
            S.add(BOX, T @ TRS((x, 0.75, -2.21), s=(0.35, 0.12, 0.02)), Mat((1, 0, 0), 0.2, emi=(4 * lights, 0.2, 0.1)))


def pylon(S, T, h=32.0):
    """iletim hatti diregi (kafes kule, sade)."""
    m = Mat(srgb((120, 124, 128)), 0.5, 0.8)
    b = 4.0
    pts = [(-b, 0, -b), (b, 0, -b), (b, 0, b), (-b, 0, b)]
    top = [(-0.8, h, -0.8), (0.8, h, -0.8), (0.8, h, 0.8), (-0.8, h, 0.8)]
    for p, q in zip(pts, top):
        S.add(CYL_LO, T @ align(p, q, 0.18), m)
    for k in range(6):
        y0, y1 = h * k / 6, h * (k + 1) / 6
        w0, w1 = b - (b - 0.8) * k / 6, b - (b - 0.8) * (k + 1) / 6
        for s in (-1, 1):
            S.add(CYL_LO, T @ align((-w0, y0, s * w0), (w1, y1, s * w1), 0.07), m)
            S.add(CYL_LO, T @ align((s * w0, y0, -w0), (s * w1, y1, w1), 0.07), m)
    for y, wdt in ((h * 0.72, 9), (h * 0.88, 7)):
        S.add(BOX, T @ TRS((0, y, 0), s=(wdt * 2, 0.4, 0.6)), m)


def tank(S, T, r=6.0, h=10.0):
    S.add(CYL, T @ TRS((0, h / 2, 0), s=(r, h, r)), Mat(srgb((200, 202, 205)), 0.45, 0.4, pat="boya", scale=0.6))


def fence(S, T, length=60.0):
    m = Mat(srgb((130, 135, 140)), 0.5, 0.8)
    n = int(length / 3)
    for i in range(n + 1):
        S.add(CYL_LO, T @ TRS((-length / 2 + i * 3, 1.2, 0), s=(0.05, 2.4, 0.05)), m)
    S.add(BOX, T @ TRS((0, 1.2, 0), s=(length, 2.2, 0.02)), m.but(alpha=0.25))


def plant_pwr(S, t=0.0, night=True, cut=0.0, steam=0.04, lit=1.0, people=True):
    """tam bir PWR santral yerlesimi (koruma kabi merkezde, 0,0)."""
    I = np.eye(4)
    S.add(PLANE_HI, TRS((0, 0, 0), s=(3000, 1, 3000)), CIM)
    S.add(BOX, TRS((10, 0.05, 40), s=(260, 0.1, 9)), ASFALT)
    S.add(BOX, TRS((-60, 0.05, 0), s=(9, 0.1, 160)), ASFALT)
    S.add(BOX, TRS((15, 0.04, 0), s=(150, 0.08, 90)), Mat(srgb((120, 118, 112)), 0.9, pat="beton", scale=0.2))
    containment_pwr(S, I, alpha=1.0 - cut)
    building(S, TRS((52, 0, -2)), 58, 34, 38, PANEL, doors=2, windows=6, lit=lit * (0.6 if night else 0))
    building(S, TRS((0, 0, -34)), 40, 22, 24, PANEL_BEJ, windows=5, lit=lit * (0.5 if night else 0))
    building(S, TRS((-36, 0, 6)), 22, 18, 30, BETON, windows=3, lit=lit * (0.4 if night else 0))
    cooling_tower(S, TRS((-40, 0, -190)), 150, steam=steam, t=t,
                  steam_col=(0.32, 0.34, 0.4) if night else (0.92, 0.93, 0.95), steam_a=0.55 if night else 0.6)
    tank(S, TRS((95, 0, 30)), 7, 12)
    tank(S, TRS((95, 0, 52)), 7, 12)
    for i, x in enumerate((-20, 20, 60, 100)):
        lamp_post(S, TRS((x, 0, 46), ry(math.pi / 2)), on=1.0 if night else 0.0)
    for k in range(4):
        pylon(S, TRS((160 + k * 70, 0, -40 - k * 12)), 34)
    fence(S, TRS((20, 0, 52)), 200)
    if people:
        human(S, TRS((30, 0, 42), ry(0.4)), walk=t * 3.0)
        human(S, TRS((33, 0, 43.5), ry(0.6)), col=(0.2, 0.45, 0.8), walk=t * 3.0 + 1.0)
    car(S, TRS((-5 + (t * 4.0) % 80, 0, 38), ry(math.pi / 2)), lights=1.0 if night else 0.0)
    car(S, TRS((70, 0, 44)), col=(0.75, 0.75, 0.78))
    car(S, TRS((74, 0, 44)), col=(0.08, 0.1, 0.2))
