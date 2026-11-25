"""Arsiv odasi: metal raflar, karton kutular, ahsap masa, masa lambasi, arsiv kartlari."""
import math
import numpy as np
from gercekci import *

RAF = Mat(srgb((92, 98, 104)), 0.45, 0.85, pat="boya", scale=2.0)
KUTU = Mat(srgb((176, 140, 98)), 0.85, 0.0, pat="karton", scale=4.0)
KUTU2 = Mat(srgb((160, 128, 90)), 0.85, 0.0, pat="karton", scale=4.0)
MASA = Mat(srgb((96, 64, 40)), 0.4, 0.0, pat="ahsap", scale=0.6)
KAGIT = Mat(srgb((238, 232, 214)), 0.7, 0.0, pat="kagit", scale=3.0)
ZEMIN = Mat(srgb((92, 90, 86)), 0.7, 0.0, pat="beton", scale=1.0)
DUVAR = Mat(srgb((150, 146, 138)), 0.9, 0.0, pat="beton", scale=1.2)


def shelf(S, T, w=2.0, h=2.4, d=0.5, levels=5, seed=0):
    rng = np.random.default_rng(seed)
    for sx in (-1, 1):
        for sz in (-1, 1):
            S.add(BOX, T @ TRS((sx * w / 2, h / 2, sz * d / 2), s=(0.035, h, 0.035)), RAF)
    for k in range(levels):
        y = 0.1 + (h - 0.2) * k / (levels - 1)
        S.add(BOX, T @ TRS((0, y, 0), s=(w, 0.02, d)), RAF)
        if k < levels - 1:
            x = -w / 2 + 0.05
            while x < w / 2 - 0.3:
                bw = rng.uniform(0.28, 0.42)
                bh = rng.uniform(0.25, 0.32)
                if rng.uniform() < 0.88:
                    S.add(BOX, T @ TRS((x + bw / 2, y + 0.01 + bh / 2, rng.uniform(-0.02, 0.03)), ry(rng.uniform(-0.04, 0.04)),
                                         (bw - 0.02, bh, d * 0.85)), KUTU if rng.uniform() < 0.6 else KUTU2)
                    S.add(BOX, T @ TRS((x + bw / 2, y + 0.01 + bh * 0.6, d * 0.43 + 0.012), s=(0.1, 0.05, 0.003)), KAGIT)
                x += bw


def desk(S, T, w=1.6, d=0.8, h=0.76):
    S.add(BOX, T @ TRS((0, h - 0.02, 0), s=(w, 0.04, d)), MASA)
    for sx in (-1, 1):
        for sz in (-1, 1):
            S.add(BOX, T @ TRS((sx * (w / 2 - 0.05), (h - 0.04) / 2, sz * (d / 2 - 0.05)), s=(0.05, h - 0.04, 0.05)), MASA)


def lamp(S, T, on=1.0):
    m = Mat(srgb((30, 60, 45)), 0.35, 0.6)
    S.add(CYL, T @ TRS((0, 0.01, 0), s=(0.08, 0.02, 0.08)), m)
    S.add(CYL_LO, T @ align((0, 0.02, 0), (0.05, 0.35, 0.0), 0.008), m)
    S.add(CYL_LO, T @ align((0.05, 0.35, 0.0), (0.22, 0.42, 0.0), 0.008), m)
    S.add(("abajur", lambda: m_lathe([(0.03, 0.06), (0.09, -0.02), (0.095, -0.03)], 32)), T @ TRS((0.24, 0.42, 0), rz(-0.5)), m)
    S.add(SPH_LO, T @ TRS((0.255, 0.39, 0), s=0.025), Mat((1, 1, 1), 0.2, emi=(8 * on, 6.5 * on, 4 * on)))
    return (T @ np.array([0.26, 0.36, 0, 1]))[:3]


def card(S, T, w=0.2, d=0.13, glow=0.0):
    S.add(BOX, T @ TRS((0, 0.001, 0), s=(w, 0.002, d)), KAGIT.but(emi=(0.3 * glow, 0.28 * glow, 0.22 * glow)))


def room(S, t=0.0, lamp_on=1.0):
    S.add(BOX, TRS((0, -0.01, 0), s=(14, 0.02, 14)), ZEMIN)
    S.add(BOX, TRS((0, 1.6, -4.0), s=(14, 3.2, 0.1)), DUVAR)
    for k in range(4):
        shelf(S, TRS((-3.5, 0, -2.6 + k * 1.25)), 2.0, 2.4, 0.5, seed=k)
        shelf(S, TRS((3.6, 0, -2.6 + k * 1.25)), 2.0, 2.4, 0.5, seed=10 + k)
    desk(S, TRS((0, 0, 0)))
    lp = lamp(S, TRS((-0.55, 0.76, -0.22)), lamp_on)
    S.light(tuple(lp), 1.2, (1.0, 0.78, 0.5), 2.2 * lamp_on)
    S.light((0, 2.8, -1.5), 5.0, (0.7, 0.75, 0.85), 1.2)
    rng = np.random.default_rng(1)
    for i in range(90):
        p = rng.uniform([-2.0, 0.6, -2.5], [2.0, 2.6, 1.5])
        p = p + np.array([math.sin(t * 0.2 + i) * 0.05, ((t * 0.03 + i * 0.13) % 1.0) * 0.2, 0])
        S.particle(tuple(p), 0.008, (1.0, 0.9, 0.7, 0.35), kind=0, add=True)
