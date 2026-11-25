"""Atom alti olcek: gercek nukleon sayili paketlenmis cekirdekler (birim: nukleon yaricapi = 1)."""
import math
import numpy as np
from gercekci import *

PROTON = Mat(srgb((236, 92, 52)), 0.32, 0.0, emi=(0.10, 0.025, 0.01))
NEUTRON = Mat(srgb((150, 168, 200)), 0.3, 0.0, emi=(0.02, 0.03, 0.05))
NEUTRON_GLOW = Mat(srgb((170, 200, 240)), 0.25, 0.0, emi=(0.6, 0.9, 1.6))
PROTON_GLOW = Mat(srgb((255, 120, 70)), 0.25, 0.0, emi=(1.6, 0.5, 0.2))


def pack(n, seed):
    """n kureyi yaricap ~1.02 n^(1/3) icinde gevsek paketle (itme ile)."""
    rng = np.random.default_rng(seed)
    Rc = 1.0 * n ** (1 / 3)
    P = []
    while len(P) < n:
        v = rng.uniform(-1, 1, 3)
        if v @ v < 1:
            P.append(v * Rc)
    P = np.array(P)
    for _ in range(90):
        d = P[:, None, :] - P[None, :, :]
        r = np.linalg.norm(d, axis=2) + np.eye(n) * 9
        f = np.clip(2.0 - r, 0, None)[..., None] * d / r[..., None]
        P += 0.25 * f.sum(1)
        rr = np.linalg.norm(P, axis=1, keepdims=True)
        P = np.where(rr > Rc, P / rr * Rc, P)
        P -= P.mean(0) * 0.2
    return P


def types(n, z, seed):
    rng = np.random.default_rng(seed + 100)
    t = np.zeros(n, bool)
    t[rng.choice(n, z, replace=False)] = True
    return t


class Cekirdek:
    def __init__(self, z, n, seed):
        self.A = z + n
        self.P = pack(self.A, seed)
        self.isp = types(self.A, z, seed)


_CACHE = {}


def get(key):
    if key not in _CACHE:
        spec = {"U235": (92, 143, 5), "U238": (92, 146, 8), "RB93": (37, 56, 6), "CS140": (55, 85, 7),
                "FE56": (26, 30, 4), "C12": (6, 6, 9)}[key]
        _CACHE[key] = Cekirdek(*spec)
    return _CACHE[key]


def draw(S, P, isp, center, scale=1.0, R=None, alpha=1.0, glow=0.0, emi_boost=None):
    R = np.eye(3) if R is None else R
    Q = (P @ R.T) * scale + np.asarray(center)
    for i in range(len(P)):
        m = PROTON if isp[i] else NEUTRON
        if glow > 0:
            m = m.but(emi=tuple(e + g for e, g in zip(m.emi, (1.2 * glow, 0.45 * glow, 0.12 * glow))))
        if alpha < 1:
            m = m.but(alpha=alpha)
        S.add(SPH, TRS(tuple(Q[i]), s=scale * 1.0), m)


def neutron(S, pos, s=1.0, glow=1.0, trail=None, alpha=1.0):
    m = NEUTRON.but(emi=(0.25 * glow, 0.38 * glow, 0.7 * glow), alpha=alpha)
    S.add(SPH, TRS(tuple(pos), s=s), m)
    S.particle(tuple(pos), 3.2 * s, (0.45, 0.65, 1.0, 0.35 * glow * alpha), kind=0, add=True)
    if trail is not None:
        for k, p in enumerate(trail):
            a = (1 - k / len(trail)) * 0.25 * alpha
            S.particle(tuple(p), 1.2 * s * (1 - 0.6 * k / len(trail)), (0.45, 0.7, 1.0, a), kind=0, add=True)


def proton(S, pos, s=1.0, glow=1.0, trail=None, alpha=1.0):
    m = PROTON.but(emi=(0.8 * glow, 0.25 * glow, 0.08 * glow), alpha=alpha)
    S.add(SPH, TRS(tuple(pos), s=s), m)
    S.particle(tuple(pos), 3.2 * s, (1.0, 0.5, 0.25, 0.3 * glow * alpha), kind=0, add=True)
    if trail is not None:
        for k, p in enumerate(trail):
            a = (1 - k / len(trail)) * 0.25 * alpha
            S.particle(tuple(p), 1.2 * s * (1 - 0.6 * k / len(trail)), (1.0, 0.55, 0.3, a), kind=0, add=True)


def dust(S, t, center=(0, 0, 0), n=160, R=60.0, seed=3, col=(0.5, 0.7, 1.0), a=0.25, speed=1.0):
    """atom olcegi derinlik tozu (yavas suzulen isik noktalari)."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(-1, 1, (n, 3)) * R
    vel = rng.normal(0, 1, (n, 3)) * 0.6
    sz = rng.uniform(0.15, 0.5, n)
    for i in range(n):
        p = base[i] + vel[i] * t * speed
        p = (p + R) % (2 * R) - R + np.asarray(center)
        tw = 0.6 + 0.4 * math.sin(t * 1.3 + i)
        S.particle(tuple(p), sz[i], (*col, a * tw), kind=0, add=True)


def compound_split(seed=11):
    """U-236 bileşik cekirdek konumlari ve Rb-93 / Cs-140 / 3n eslesmesi."""
    rb, cs = get("RB93"), get("CS140")
    C = pack(236, seed)
    order = np.argsort(C[:, 0])
    left = order[:93]
    right = order[-140:]
    mid = order[93:96]
    # her parcanin kendi paketinde x'e gore sirala, eslestir
    rb_o = np.argsort(rb.P[:, 0])
    cs_o = np.argsort(cs.P[:, 0])
    src = np.zeros((236, 3))
    dst_local = np.zeros((236, 3))
    grp = np.zeros(236, int)       # 0: rb, 1: cs, 2: notron
    isp = np.zeros(236, bool)
    k = 0
    for ci, li in zip(left, rb_o):
        src[k] = C[ci]; dst_local[k] = rb.P[li]; grp[k] = 0; isp[k] = rb.isp[li]; k += 1
    for ci, li in zip(right, cs_o):
        src[k] = C[ci]; dst_local[k] = cs.P[li]; grp[k] = 1; isp[k] = cs.isp[li]; k += 1
    for ci in mid:
        src[k] = C[ci]; dst_local[k] = 0; grp[k] = 2; isp[k] = False; k += 1
    # yakalanan notron: +x yuzeyine en yakin notron (gelen notron bunun yerine oturur)
    cand = [i for i in range(236) if not isp[i]]
    cap = max(cand, key=lambda i: src[i, 0] * 0.3 - abs(src[i, 1]) - abs(src[i, 2]) + np.linalg.norm(src[i]))
    return src, dst_local, grp, isp, cap
