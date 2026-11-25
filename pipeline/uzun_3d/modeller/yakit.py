"""PWR yakiti ve reaktor kabi. Tarif: NRC Reactor Concepts Manual bolum 1 ve 4 (17x17 kare duzen, aralik
izgaralari, alt/ust baslik, kilavuz tupler; ~12 ft cubuk, zirkonyum alasimi kilif, ustte gaz boslugu;
193 demet, ic cap 173 in). Pelet/cubuk capi ve izgara sayisi kaynakta yok: sade, tipik oranlar."""
import math
import numpy as np
from gercekci import *

ROD_R = 0.00475          # kilif dis yaricapi
PITCH = 0.0126           # cubuk araligi
ASSY = 17 * PITCH + 0.0008   # demet genisligi ~0.215 m
ROD_L = 3.66             # 12 ft
PEL_R = 0.0041
PEL_H = 0.0098
GT = {(2, 5), (2, 8), (2, 11), (3, 3), (3, 13), (5, 2), (5, 5), (5, 8), (5, 11), (5, 14), (8, 2), (8, 5), (8, 8),
      (8, 11), (8, 14), (11, 2), (11, 5), (11, 8), (11, 11), (11, 14), (13, 3), (13, 13), (14, 5), (14, 8), (14, 11)}

ZIRK = Mat(srgb((176, 178, 182)), 0.32, 1.0, pat="fircali", scale=1.0)
PASLANMAZ = Mat(srgb((160, 162, 166)), 0.38, 1.0, pat="fircali", scale=1.0)
SERAMIK = Mat(srgb((88, 86, 84)), 0.7, 0.0, pat="seramik", scale=1.0)
REAKTOR_CELIK = Mat(srgb((120, 122, 126)), 0.45, 1.0, pat="fircali", scale=0.6)
KESIT = Mat(srgb((200, 120, 60)), 0.6, 0.0)


def m_arc_tube(r_out, r_in, a0, a1, seg=32):
    """y -0.5..0.5 boyunca a0..a1 acisinda acik boru dilimi (kesit gorunumu): dis, ic yuzey ve kesit yuzleri."""
    tris = []
    angs = np.linspace(a0, a1, seg + 1)
    for (r, sgn) in ((r_out, 1), (r_in, -1)):
        for i in range(seg):
            b0, b1 = angs[i], angs[i + 1]
            q = [(r * math.cos(b0), -0.5, r * math.sin(b0), sgn * math.cos(b0), 0, sgn * math.sin(b0)),
                 (r * math.cos(b1), -0.5, r * math.sin(b1), sgn * math.cos(b1), 0, sgn * math.sin(b1)),
                 (r * math.cos(b1), 0.5, r * math.sin(b1), sgn * math.cos(b1), 0, sgn * math.sin(b1)),
                 (r * math.cos(b0), 0.5, r * math.sin(b0), sgn * math.cos(b0), 0, sgn * math.sin(b0))]
            tris += [q[0], q[2], q[1], q[0], q[3], q[2]]
    for b in (a0, a1):
        n = (-math.sin(b), 0, math.cos(b)) if b == a0 else (math.sin(b), 0, -math.cos(b))
        c, s = math.cos(b), math.sin(b)
        q = [(r_in * c, -0.5, r_in * s), (r_out * c, -0.5, r_out * s), (r_out * c, 0.5, r_out * s), (r_in * c, 0.5, r_in * s)]
        tris += [(*q[0], *n), (*q[1], *n), (*q[2], *n), (*q[0], *n), (*q[2], *n), (*q[3], *n)]
    for y, ny in ((-0.5, -1), (0.5, 1)):
        for i in range(seg):
            b0, b1 = angs[i], angs[i + 1]
            q = [(r_in * math.cos(b0), y, r_in * math.sin(b0)), (r_out * math.cos(b0), y, r_out * math.sin(b0)),
                 (r_out * math.cos(b1), y, r_out * math.sin(b1)), (r_in * math.cos(b1), y, r_in * math.sin(b1))]
            tris += [(*q[0], 0, ny, 0), (*q[1], 0, ny, 0), (*q[2], 0, ny, 0), (*q[0], 0, ny, 0), (*q[2], 0, ny, 0), (*q[3], 0, ny, 0)]
    return np.array(tris, np.float32)


def m_pellet():
    r, h, ch, dish = 1.0, 1.0, 0.06, 0.03
    prof = [(0.0, -0.5 + dish), (0.6, -0.5 + dish * 0.4), (r - ch, -0.5), (r, -0.5 + ch), (r, 0.5 - ch), (r - ch, 0.5),
            (0.6, 0.5 - dish * 0.4), (0.0, 0.5 - dish)]
    return m_lathe(prof, 40, smooth=False)


PELLET = ("pelet", m_pellet)


def pellet(S, pos, R=None, mat=SERAMIK, glow=0.0):
    m = mat if glow <= 0 else mat.but(emi=(1.0 * glow, 0.38 * glow, 0.08 * glow))
    S.add(PELLET, TRS(pos, R, (PEL_R, PEL_H, PEL_R)), m)


def m_spring(turns=30, r=0.0036, wire=0.0006, L=0.18):
    pts = [(r * math.cos(a), L * a / (2 * math.pi * turns) - L / 2, r * math.sin(a)) for a in np.linspace(0, 2 * math.pi * turns, turns * 16)]
    return m_tube(pts, wire, 6)


def fuel_rod_cut(S, T, y0=0.0, n_pel=60, cut=1.0, glow=0.0, show_spring=True, clad_alpha=1.0, face=0.95):
    """kesitli yakit cubugu: kilif yarim aciliyor (cut 0..1), icinde ust uste peletler, ustte yay ve gaz boslugu.
    T: cubugun alt ucu, y yukari. Yalnizca alt n_pel pelet ve ust plenum modellenir (yakin cekim)."""
    L = n_pel * PEL_H + 0.2
    a1 = 2 * math.pi - cut * math.pi
    S.add(("klf_%d" % int(cut * 40), lambda: m_arc_tube(ROD_R, ROD_R - 0.00057, 0, max(a1, 0.3), 48)),
          T @ TRS((0, L / 2, 0), ry(2 * math.pi - cut * math.pi / 2 - face), (1, L, 1)), ZIRK.but(alpha=clad_alpha))
    for k in range(n_pel):
        S.add(PELLET, T @ TRS((0, PEL_H * (k + 0.5) + 0.002, 0), s=(PEL_R, PEL_H, PEL_R)),
              SERAMIK if glow <= 0 else SERAMIK.but(emi=(1.0 * glow, 0.36 * glow, 0.07 * glow)))
    if show_spring:
        S.add(("yay", m_spring), T @ TRS((0, n_pel * PEL_H + 0.1, 0)), PASLANMAZ)
    S.add(CYL, T @ TRS((0, -0.004, 0), s=(ROD_R, 0.012, ROD_R)), ZIRK)          # alt tapa


def assembly(S, T, L=ROD_L, grids=8, lod=0, rod_mat=ZIRK, glow=0.0, top_only=False):
    """17x17 PWR demeti. T: demetin alt merkezi. lod 1: yalniz kutu + ust baslik (uzak gorunum)."""
    hb, ht = 0.07, 0.09
    if lod >= 1:
        S.add(BOX, T @ TRS((0, hb + L / 2, 0), s=(ASSY * 0.98, L, ASSY * 0.98)), rod_mat.but(pat="fircali"))
        S.add(BOX, T @ TRS((0, hb + L + ht / 2, 0), s=(ASSY, ht, ASSY)), PASLANMAZ.but(pat="kafes", scale=1 / ASSY))
        return
    off = -8 * PITCH
    for i in range(17):
        for j in range(17):
            x, z = off + i * PITCH, off + j * PITCH
            if (i, j) in GT:
                S.add(CYL_LO if lod < 0 else CYL, T @ TRS((x, hb + L / 2 + 0.03, z), s=(0.0061, L + 0.06, 0.0061)), PASLANMAZ)
            else:
                m = rod_mat if glow <= 0 else rod_mat.but(emi=(0.6 * glow, 0.2 * glow, 0.04 * glow))
                S.add(CYL_LO if lod < 0 else CYL, T @ TRS((x, hb + L / 2, z), s=(ROD_R, L, ROD_R)), m)
    gm = Mat(srgb((185, 186, 190)), 0.35, 1.0)
    for g in range(grids):
        y = hb + 0.12 + (L - 0.24) * g / (grids - 1)
        for k in range(18):
            c = off - PITCH / 2 + k * PITCH
            if 0 < k < 17 and lod < 0:
                continue
            S.add(BOX, T @ TRS((c, y, 0), s=(0.0005 if 0 < k < 17 else 0.0012, 0.04, ASSY)), gm)
            S.add(BOX, T @ TRS((0, y, c), s=(ASSY, 0.04, 0.0005 if 0 < k < 17 else 0.0012)), gm)
    S.add(BOX, T @ TRS((0, hb / 2, 0), s=(ASSY, hb, ASSY)), PASLANMAZ.but(pat="kafes", scale=1 / ASSY))
    S.add(BOX, T @ TRS((0, hb + L + ht / 2, 0), s=(ASSY, ht, ASSY)), PASLANMAZ.but(pat="kafes", scale=1 / ASSY))
    for sx, sz in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
        S.add(BOX, T @ TRS((sx * ASSY * 0.36, hb + L + ht + 0.015, sz * ASSY * 0.36), s=(0.03, 0.03, 0.03)), PASLANMAZ)


CORE_ROWS = [7, 11, 13, 13, 15, 15, 15, 15, 15, 15, 15, 13, 13, 11, 7]    # toplam 193


def core_positions(pitch=ASSY + 0.002):
    out = []
    for r, n in enumerate(CORE_ROWS):
        for c in range(n):
            out.append(((c - (n - 1) / 2) * pitch, (r - 7) * pitch))
    return out


def vessel(S, T, cut=0.0, alpha=1.0, head=True, head_lift=0.0):
    """reaktor kabi: ic cap 4,39 m (173 in), duvar ~0,22 m; yari kure alt baslik, cikarilabilir ust kapak,
    kapak uzerinde kontrol cubugu surucu nozullari. cut>0: on yarisi kesik (ic gorunur)."""
    ri, ro, Hc = 2.197, 2.42, 9.0
    a1 = 2 * math.pi - cut * math.pi
    m = REAKTOR_CELIK.but(alpha=alpha)
    if cut > 0:
        S.add(("kab_kes_%d" % int(cut * 20), lambda: m_arc_tube(ro, ri, 0, a1, 72)),
              T @ TRS((0, Hc / 2, 0), ry(math.pi / 2 + cut * math.pi / 2), (1, Hc, 1)), m)
    else:
        S.add(("kab", lambda: m_lathe([(1, 0), (1, 1)], 72)), T @ TRS((0, 0, 0), s=(ro, Hc, ro)), m)
    S.add(("kab_alt", lambda: m_lathe([(math.cos(a), -math.sin(a)) for a in np.linspace(0, math.pi / 2, 20)][::-1], 72)),
          T @ TRS((0, 0, 0), s=(ro, ro * 0.85, ro)), m)
    if head:
        hy = Hc + head_lift
        S.add(("kapak", lambda: m_lathe([(math.cos(a), math.sin(a)) for a in np.linspace(0, math.pi / 2, 20)], 72)),
              T @ TRS((0, hy + 0.3, 0), s=(ro, ro * 0.7, ro)), m)
        S.add(CYL, T @ TRS((0, hy + 0.15, 0), s=(ro + 0.35, 0.3, ro + 0.35)), m)          # flans
        for (x, z) in core_positions(0.4)[::3]:
            if x * x + z * z < 1.7 ** 2:
                h0 = hy + 0.3 + ro * 0.7 * math.sqrt(max(0, 1 - (x * x + z * z) / ro ** 2))
                S.add(CYL_LO, T @ TRS((x, h0 + 1.2, z), s=(0.07, 2.6, 0.07)), PASLANMAZ.but(alpha=alpha))
        for k in range(4):        # sicak/soguk bacak nozullari
            a = math.pi / 4 + k * math.pi / 2
            S.add(CYL, T @ TRS((math.cos(a) * (ro + 0.6), Hc - 1.4, math.sin(a) * (ro + 0.6)), ry(-a) @ rz(math.pi / 2), (0.45, 1.3, 0.45)), m)


def core(S, T, lod=1, glow=0.0, highlight=None, hl=0.0):
    """193 demetlik cekirdek; alt plaka y=0."""
    for k, (x, z) in enumerate(core_positions()):
        gl = glow + (hl if highlight == k else 0)
        assembly(S, T @ TRS((x, 0, z)), lod=lod, glow=gl)
