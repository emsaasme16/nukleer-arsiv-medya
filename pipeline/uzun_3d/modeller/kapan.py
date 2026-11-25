"""Fare kapani ve ping-pong topu benzetmesi (plan belgesinin ana benzetmesi). Gunluk nesneler: tipik olculer
(taban ~10 x 4,5 cm ahsap, tel cene, yay, tetik; top capi 40 mm)."""
import math
import numpy as np
from gercekci import *

AHSAP = Mat(srgb((196, 160, 112)), 0.65, 0.0, pat="ahsap", scale=1.0)
MASA = Mat(srgb((120, 82, 52)), 0.45, 0.0, pat="ahsap", scale=0.35)
ZEMIN = Mat(srgb((150, 112, 78)), 0.5, 0.0, pat="ahsap", scale=0.5)
TEL = Mat(srgb((185, 188, 192)), 0.3, 1.0)
BAKIR = Mat(srgb((190, 140, 90)), 0.35, 1.0)
TOP = Mat(srgb((228, 226, 220)), 0.4, 0.0)
SIVA = Mat(srgb((214, 208, 196)), 0.9, 0.0, pat="beton", scale=1.5, cast=False)
BL, BW, BT = 0.10, 0.045, 0.008
BALL_R = 0.02


def m_bail():
    w, L = 0.017, 0.036
    pts = [(0, 0, -w)] + [(L * k / 8, 0, -w) for k in range(1, 9)] + \
          [(L + 0.004 * math.sin(a), 0, -w * math.cos(a)) for a in np.linspace(0, math.pi, 10)] + \
          [(L - L * k / 8, 0, w) for k in range(1, 9)]
    return m_tube(pts, 0.0009, 6)


def m_coil():
    pts = [(0.0045 * math.cos(a), 0.0045 * math.sin(a), a / (2 * math.pi) * 0.0022) for a in np.linspace(0, 2 * math.pi * 4, 64)]
    return m_tube(pts, 0.0007, 6)


BAIL = ("cene", m_bail)
COIL = ("yay_k", m_coil)


def trap(S, T, theta=0.0, highlight=0.0):
    """theta: cene acisi (0 kurulu, pi kapanmis)."""
    m = AHSAP if highlight <= 0 else AHSAP.but(emi=(0.6 * highlight, 0.25 * highlight, 0.05 * highlight))
    S.add(BOX, T @ TRS((0, BT / 2, 0), s=(BL, BT, BW)), m)
    hy = BT + 0.005
    S.add(BAIL, T @ TRS((0, hy, 0), rz(theta)), TEL)
    for z in (-0.012, 0.012):
        S.add(COIL, T @ TRS((0, hy, z - 0.0011)), TEL)
    S.add(BOX, T @ TRS((-0.035, BT + 0.002, 0), s=(0.022, 0.003, 0.02)), BAKIR)       # tetik plakasi
    if theta < 0.3:
        S.add(CYL_LO, T @ align((-0.03, BT + 0.004, 0), (0.033, BT + 0.006, 0), 0.0008), TEL)   # tutma kolu
    S.add(CYL_LO, T @ TRS((0, BT + 0.001, 0), rx(math.pi / 2), (0.0012, 0.04, 0.0012)), TEL)  # mil


def table(S, T, w=2.2, d=1.3, h=0.76):
    S.add(BOX, T @ TRS((0, h - 0.02, 0), s=(w, 0.04, d)), MASA)
    for sx in (-1, 1):
        for sz in (-1, 1):
            S.add(BOX, T @ TRS((sx * (w / 2 - 0.06), (h - 0.04) / 2, sz * (d / 2 - 0.06)), s=(0.06, h - 0.04, 0.06)), MASA)
    S.add(BOX, T @ TRS((0, h - 0.08, d / 2 - 0.05), s=(w - 0.15, 0.08, 0.02)), MASA)
    S.add(BOX, T @ TRS((0, h - 0.08, -d / 2 + 0.05), s=(w - 0.15, 0.08, 0.02)), MASA)


def room(S, w=7.0, d=6.0, h=2.9):
    S.add(BOX, TRS((0, -0.01, 0), s=(w, 0.02, d)), ZEMIN)
    S.add(BOX, TRS((0, h / 2, -d / 2), s=(w, h, 0.1)), SIVA)
    S.add(BOX, TRS((-w / 2, h / 2, 0), s=(0.1, h, d)), SIVA)
    S.add(BOX, TRS((w / 2, h / 2, 0), s=(0.1, h, d)), SIVA)
    S.add(BOX, TRS((0, h, 0), s=(w, 0.1, d)), SIVA.but(col=srgb((230, 228, 222))))
    # pencere (arka duvar, gun isigi giriyor)
    S.add(BOX, TRS((1.2, 1.6, -d / 2 + 0.06), s=(1.6, 1.4, 0.04)), Mat((1, 1, 1), 0.1, emi=(3.0, 3.1, 3.3)))
    for x in (0.4, 1.2, 2.0):
        S.add(BOX, TRS((x, 1.6, -d / 2 + 0.09), s=(0.05, 1.45, 0.05)), Mat(srgb((240, 240, 236)), 0.5))
    S.add(BOX, TRS((1.2, 1.6, -d / 2 + 0.09), s=(1.65, 0.05, 0.05)), Mat(srgb((240, 240, 236)), 0.5))
    S.add(BOX, TRS((0, 0.05, -d / 2 + 0.06), s=(w, 0.1, 0.03)), Mat(srgb((240, 238, 232)), 0.5))   # supurgelik


class Zincir:
    """deterministik kapan zinciri benzetimi. Zaman: benzetim saniyesi."""

    def __init__(self, cols=16, rows=10, sx=0.12, sz=0.105, h=0.76, seed=4, t0=0.0):
        self.h = h
        self.traps = []
        for r in range(rows):
            for c in range(cols):
                self.traps.append(np.array([(c - (cols - 1) / 2) * sx, h, (r - (rows - 1) / 2) * sz]))
        self.traps = np.array(self.traps)
        n = len(self.traps)
        self.ts = np.full(n, np.inf)
        rng = np.random.default_rng(seed)
        self.balls = []          # (launch_t, p0, v0) -> ucus; sonra sekmeler
        # baslangic toplari: kapan ustunde duran (iki top)
        self.rest = []
        for i in range(n):
            for k in (-1, 1):
                self.rest.append((i, np.array([0.012 * k, BT + 0.006 + BALL_R, 0.0])))
        # ilk top: yukaridan dusurulen
        tgt = int(np.argmin(np.linalg.norm(self.traps - np.array([-0.15, h, 0.05]), axis=1)))
        self.first = (t0, self.traps[tgt] + np.array([0.0, 0.9, 0.0]), np.array([0.0, 0.0, 0.0]))
        events = [(t0 + math.sqrt(2 * 0.9 / 9.81) * 0.98, tgt, -1)]
        self.paths = {}          # top indeksi -> segmentler
        self.lost = []
        self.paths[-1] = self._fly(self.first[0], self.first[1], self.first[2], rng)
        while events:
            events.sort()
            te, j, b = events.pop(0)
            if self.ts[j] < np.inf:
                continue
            self.ts[j] = te + 0.015
            for bi in (2 * j, 2 * j + 1):
                p0 = self.traps[j] + self.rest[bi][1]
                ang = rng.uniform(0, 2 * math.pi)
                hs = rng.uniform(0.25, 1.1)
                v0 = np.array([math.cos(ang) * hs, rng.uniform(2.0, 3.0), math.sin(ang) * hs])
                segs = self._fly(self.ts[j], p0, v0, rng)
                self.paths[bi] = segs
                land_t, land_p = segs[0][0] + segs[0][3], segs[0][1] + segs[0][2] * segs[0][3] + np.array([0, -0.5 * 9.81 * segs[0][3] ** 2, 0])
                d = np.linalg.norm(self.traps[:, [0, 2]] - land_p[[0, 2]], axis=1)
                k = int(np.argmin(d))
                if d[k] < 0.055 and abs(land_p[1] - (h + 0.03)) < 0.05:
                    if self.ts[k] == np.inf:
                        events.append((land_t, k, bi))
                    else:
                        self.lost.append((bi, land_t))
                else:
                    self.lost.append((bi, land_t))

    def _fly(self, t0, p0, v0, rng, bounces=3):
        """segment listesi: (t_baslangic, p0, v0, sure, zemin_y)."""
        segs = []
        p, v, t = np.array(p0, float), np.array(v0, float), t0
        for b in range(bounces + 1):
            on_table = abs(p[0]) < 1.1 and abs(p[2]) < 0.65
            floor = (self.h + 0.03) if on_table else BALL_R
            # p.y - 0.5 g T^2 + v.y T = floor
            a, bq, c = -0.5 * 9.81, v[1], p[1] - floor
            disc = bq * bq - 4 * a * c
            T = (-bq - math.sqrt(max(disc, 0))) / (2 * a)
            # masa disina cikarsa zemine kadar dussun
            pe = p + v * T + np.array([0, a * T * T, 0])
            if on_table and not (abs(pe[0]) < 1.1 and abs(pe[2]) < 0.65):
                c = p[1] - BALL_R
                T = (-bq - math.sqrt(bq * bq - 4 * a * c)) / (2 * a)
                pe = p + v * T + np.array([0, a * T * T, 0])
            segs.append((t, p.copy(), v.copy(), T))
            t += T
            p = pe
            v = np.array([v[0] * 0.6, -(v[1] - 9.81 * T) * 0.45, v[2] * 0.6])
            if v[1] < 0.15:
                break
        segs.append((t, p.copy(), np.zeros(3), 1e9))
        return segs

    def ball_pos(self, bi, s):
        if bi not in self.paths or s < self.paths[bi][0][0]:
            if bi == -1:
                return None
            j = bi // 2
            return self.traps[j] + self.rest[bi][1]
        for (t0, p0, v0, T) in self.paths[bi]:
            if s <= t0 + T:
                dt = s - t0
                return p0 + v0 * dt + np.array([0, -0.5 * 9.81 * dt * dt, 0]) * (1 if np.any(v0) else 0)
        return self.paths[bi][-1][1]

    def theta(self, j, s):
        k = (s - self.ts[j]) / 0.035
        return math.pi * min(max(k, 0), 1) ** 0.7 * 0.97
