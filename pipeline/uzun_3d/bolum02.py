#!/usr/bin/env python3
"""Bolum 2: Fisyon: cekirdek nasil bolunur?  (gercekci 3D, gercekci.py + modeller/)

Kullanim:
  WORK=/tmp/b2 python3 bolum02.py still 10 70 200     # kareler -> $WORK/kareler
  WORK=/tmp/b2 python3 bolum02.py render              # -> $WORK/sessiz.mp4
Sahne sureleri $WORK/cues.json'dan (sesler.py) gelir. Senaryo: bolum-02/senaryo.md
"""
import os, sys, json, math, re
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "modeller"))
from gercekci import *
import gercekci as G
import santral, yakit, kapan, arsiv, atom
from common3d import T, pill, blit, F_XB, F_B, F_SB, F_M, CYAN, AMBER, WHITE, MUTED, RED, GREEN, FPS
from render_kit import card, corner_tag

WORK = os.environ.get("WORK", "/tmp/b2")
CUES = json.load(open(os.path.join(WORK, "cues.json")))
STARTS, DURS = CUES["starts"], CUES["durations"]
TOTAL = CUES["duration"]
NFRAMES = int(round(TOTAL * FPS))
GAP = CUES["gap"]
TAG = "NÜKLEER ARŞİV · BÖLÜM 2"
SENARYO = os.path.join(HERE, "..", "..", "bolum-02", "senaryo.md")


# ----------------------------------------------------------------- metin zamanlamasi
def _scene_texts():
    t = open(SENARYO, encoding="utf-8").read()
    return [p.strip() for p in re.findall(r"\*\*Seslendirme:\*\*\n\n(.+?)\n\n\*\*3D görsel", t, re.S)]


TEXTS = _scene_texts()
PAUSE_CH = 12


def _clean_len(s):
    n_p = s.count("[pause]")
    return len(re.sub(r"\[[a-z]+\]\s*", "", s)) + n_p * PAUSE_CH


def at(k, phrase):
    """k. sahnede (0 tabanli) ifadenin baslangic saniyesi (sahne sesine gore, karakter orani)."""
    s = TEXTS[k]
    i = s.find(phrase)
    if i < 0:
        raise KeyError(phrase)
    return _clean_len(s[:i]) / _clean_len(s) * DURS[k]


# ----------------------------------------------------------------- yardimcilar
def clamp01(x):
    return max(0.0, min(1.0, x))


def sm(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def fade(t, a, b):
    return sm((t - a) / (b - a)) if b != a else float(t >= a)


def win(t, a, b, r=0.6):
    """a-b araliginda gorunurluk (r saniye giris/cikis)."""
    return fade(t, a, a + r) * (1 - fade(t, b - r, b))


def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def path(u, keys, **kw):
    """keys: [(zaman, goz, hedef, fov)], Catmull-Rom; uclarda sabit."""
    ts = [k[0] for k in keys]
    if u <= ts[0]:
        k = keys[0]
        return Cam(k[1], k[2], fov=k[3], **kw)
    if u >= ts[-1]:
        k = keys[-1]
        return Cam(k[1], k[2], fov=k[3], **kw)
    i = max(j for j in range(len(ts) - 1) if ts[j] <= u)
    s = sm((u - ts[i]) / (ts[i + 1] - ts[i])) * 0.35 + (u - ts[i]) / (ts[i + 1] - ts[i]) * 0.65
    P = [np.asarray(keys[max(0, min(len(keys) - 1, j))][1], float) for j in (i - 1, i, i + 1, i + 2)]
    Q = [np.asarray(keys[max(0, min(len(keys) - 1, j))][2], float) for j in (i - 1, i, i + 1, i + 2)]
    fov = keys[i][3] + (keys[i + 1][3] - keys[i][3]) * sm(s)
    return Cam(cr(*P, s), cr(*Q, s), fov=fov, **kw)


def blend(a, b, w):
    if w <= 0:
        return a
    if w >= 1:
        return b
    return cv2.addWeighted(a, 1 - w, b, w, 0)


def label(img, txt, x, y, a, size=46, col=WHITE, font=F_B, maxw=900):
    if a > 0.003:
        blit(img, T(txt, font, size, col, maxw=maxw), x, y, op=a)


def cardl(img, lines, x, y, a, size=50, amber=False, scale=1.0):
    if a > 0.003:
        blit(img, card(lines, size, amber), x, y, op=a, scale=scale)


def proj(cam, p):
    r = cam.project(p)
    return (r[0], r[1]) if r else (-999, -999)


def shots(u, lst, xf=0.8):
    """lst: [(baslangic, fn)] -> fn(u - baslangic, u) cagrilir; gecislerde capraz karisim."""
    i = max([j for j in range(len(lst)) if lst[j][0] <= u] or [0])
    img = lst[i][1](u - lst[i][0], u)
    if i + 1 < len(lst):
        nxt = lst[i + 1][0]
        if u > nxt - xf:
            w = sm((u - (nxt - xf)) / xf)
            img = blend(img, lst[i + 1][1](u - nxt, u), w)
    return img


# ----------------------------------------------------------------- ortamlar
def ortam_su(S, dens=0.35, caus=0.5, cscale=6.0):
    S.bg = (0.0, 0.025, 0.045)
    S.sun_dir = norm((0.15, 1.0, 0.25))
    S.sun_col = (0.8, 1.05, 1.2)
    S.sky_zen = (0.05, 0.2, 0.3)
    S.sky_hor = (0.03, 0.12, 0.2)
    S.gnd = (0.01, 0.04, 0.06)
    S.sun_disk = 0.0
    S.fog = (dens, 0.0, -1000, 0.93)
    S.fog_col = (0.006, 0.05, 0.08)
    S.caus = (caus * 0.35, cscale * 1.8, 0.35, 100.0)
    S.amb = 0.8
    S.env = 0.45
    S.exposure = 1.1
    S.bloom = 0.35
    S.bloom_th = 1.6


def su_kabarcik(S, t, center, R, n=60, seed=2, size=0.004, speed=0.08):
    rng = np.random.default_rng(seed)
    b = rng.uniform(-1, 1, (n, 3)) * R
    sp = rng.uniform(0.5, 1.5, n)
    for i in range(n):
        p = b[i].copy()
        p[1] = (b[i][1] + t * speed * sp[i] + R) % (2 * R) - R
        p[0] += math.sin(t * 2 + i) * R * 0.02
        S.particle(tuple(np.asarray(center) + p), size * (0.6 + sp[i] * 0.5), (0.7, 0.9, 1.0, 0.35), kind=2)


# ================================================================= SAHNE 1
D1 = DURS[0]
S1 = dict(kubbe=at(0, "Beton bir kubbenin"), kalp=at(0, "Burası reaktörün kalbi"), nrc=at(0, "Amerika Nükleer Düzenleme"),
          demet=at(0, "Bir demete yaklaşalım"), tup=at(0, "Her tüp yaklaşık"), zirk=at(0, "Tüpler zirkonyum"),
          sicak=at(0, "Normal çalışmada"), isi=at(0, "Bu ısıyı"), fisyon=at(0, "Buna fisyon"),
          gecen=at(0, "Geçen bölüm"), soru=at(0, "Sorumuz şu"))


def s1_dis(v, u):
    """gece, santral dis plan -> kubbe saydamlasir, ic gorunur."""
    S = Sahne()
    gece(S)
    S.exposure = 1.7
    cut = fade(u, S1["kubbe"] + 1.0, S1["kubbe"] + 5.0) * 0.85
    santral.plant_pwr(S, t=u, night=True, cut=cut, steam=0.03)
    if cut > 0.01:
        yakit.vessel(S, TRS((0, 6, 0), s=1.0), cut=0.0, head=True)
        S.add(CYL, TRS((0, 3, 0), s=(9, 6, 9)), santral.BETON_KOYU)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            S.add(CYL, TRS((math.cos(a) * 11, 12, math.sin(a) * 11), s=(2.2, 14, 2.2)), santral.CELIK.but(col=srgb((150, 150, 150))))
        S.light((0, 22, 0), 9, (1.0, 0.85, 0.65), 5.0 * cut)
    S.shadow_box = ((0, 20, -40), 170)
    cam = path(u, [(0, (-230, 14, 210), (0, 40, -40), 40), (S1["kubbe"], (-150, 30, 150), (0, 36, -10), 40),
                   (S1["kalp"] + 0.5, (-55, 52, 55), (0, 20, 0), 42)], far=8000, aperture=0.12)
    img = ciz(S, cam, u)
    if v < 6:
        pass
    return img


def s1_cekirdek(v, u):
    """reaktor kabinin ici: su altinda 193 demetin ust basliklari (ustten)."""
    S = Sahne()
    ortam_su(S, dens=0.28, caus=0.55, cscale=2.5)
    yakit.vessel(S, TRS((0, -5.6, 0)), cut=0.0, head=False)
    S.add(("cevre", lambda: m_lathe([(1, 0), (1, 1)], 72)), TRS((0, -5.6, 0), s=(2.0, 9.6, 2.0)), yakit.PASLANMAZ)
    yakit.core(S, TRS((0, -4.2, 0)), lod=1)
    S.add(BOX, TRS((0, -0.02, 0), s=(4.0, 0.04, 4.0)), yakit.PASLANMAZ.but(alpha=0.0))
    su_kabarcik(S, u, (0, 0.6, 0), 1.6, n=70, size=0.012, speed=0.15)
    S.light((0.3, 2.2, 0.6), 2.0, (0.55, 0.85, 1.0), 2.0)
    S.shadow_box = ((0, 0, 0), 2.6)
    S.shadow_bias = 0.002
    cam = path(v, [(0, (0.5, 3.2, 1.3), (0, -0.2, -0.2), 52), (8, (0.7, 1.9, 1.0), (0.1, -0.1, -0.1), 48),
                   (S1["demet"] - S1["kalp"], (0.35, 0.8, 0.45), (0.0, -0.1, 0.0), 42)], near=0.02, aperture=0.3)
    img = ciz(S, cam, u)
    a = win(u, S1["nrc"] + 1.0, S1["demet"] + 0.2)
    cardl(img, ["Bazı santrallerde", "193 yakıt demeti"], 430, 300, a, 52)
    return img


def s1_demet(v, u):
    """tek demet yan gorunum, asagi dogru kayan kamera; 17x17."""
    S = Sahne()
    ortam_su(S, dens=0.9, caus=0.45, cscale=14)
    S.shadow = False
    yakit.assembly(S, np.eye(4))
    for (x, z) in [(-0.217, 0), (0, -0.217), (-0.217, -0.217), (0.217, -0.217)]:
        yakit.assembly(S, TRS((x, 0, z)), lod=-1, grids=0)
    su_kabarcik(S, u, (0.05, 3.0, 0.2), 0.4, n=40, size=0.002, speed=0.05)
    S.light((0.4, 3.4, 0.7), 0.9, (0.6, 0.9, 1.0), 3.0)
    L = S1["zirk"] - S1["demet"]
    cam = path(v, [(0, (0.55, 4.05, 0.7), (0, 3.75, 0), 40), (L * 0.45, (0.5, 3.5, 0.62), (0, 3.4, 0), 40),
                   (L, (0.42, 3.0, 0.5), (0.0, 2.95, 0.0), 38)], near=0.01, aperture=0.3)
    img = ciz(S, cam, u)
    cardl(img, ["17 × 17"], 400, 260, win(u, S1["demet"] + 2.5, S1["tup"] + 0.5), 64)
    cardl(img, ["Çubuk ≈ 3,7 m (12 ft)"], 470, 260, win(u, S1["tup"] + 0.8, S1["zirk"] + 0.3), 52)
    return img


def s1_cubuk(v, u):
    """kesitli yakit cubugu: peletler, yay; sonra peletler isinir."""
    S = Sahne()
    S.bg = (0.006, 0.014, 0.022)
    S.sun_dir = norm((0.6, 0.5, 0.8))
    S.sun_col = (2.2, 2.1, 2.0)
    S.sky_zen, S.sky_hor, S.gnd = (0.12, 0.2, 0.3), (0.12, 0.18, 0.26), (0.03, 0.04, 0.05)
    S.sun_disk = 0
    S.amb, S.env = 1.0, 1.0
    S.shadow_box = ((0, 0.12, 0), 0.16)
    S.shadow_bias = 0.0004
    S.fog = (2.0, 0.0, -100, 0.6)
    S.fog_col = (0.006, 0.03, 0.05)
    g = fade(u, S1["sicak"] + 0.3, S1["sicak"] + 4.0) * 0.55
    cut = fade(v, 0.3, 2.8)
    yakit.fuel_rod_cut(S, np.eye(4), n_pel=22, cut=0.5 * cut, glow=g)
    S.light((-0.03, 0.2, 0.05), 0.12, (0.7, 0.85, 1.0), 2.5)
    if g > 0:
        S.light((0.0, 0.11, 0.012), 0.05, (1.0, 0.45, 0.12), 2.0 * g)
    L = S1["isi"] - S1["zirk"] + 1.5
    cam = path(v, [(0, (0.05, 0.25, 0.07), (0, 0.215, 0), 26), (L * 0.5, (0.045, 0.16, 0.06), (0, 0.135, 0), 26),
                   (L, (0.03, 0.11, 0.04), (0, 0.1, 0), 26)], near=0.002, aperture=0.25)
    img = ciz(S, cam, u)
    label(img, "Zirkonyum alaşımı kılıf", 1420, 300, win(u, S1["zirk"] + 1.5, S1["sicak"]), 40, CYAN, F_SB)
    label(img, "Seramik uranyum peletleri", 1420, 370, win(u, S1["zirk"] + 2.5, S1["sicak"]), 40, WHITE, F_SB)
    label(img, "İçi helyumla basınçlandırılmış", 1420, 440, win(u, S1["zirk"] + 3.5, S1["sicak"]), 34, MUTED, F_M)
    cardl(img, ["Pelet ortalaması ≈ 760 °C"], 1380, 300, win(u, S1["sicak"] + 2.0, S1["isi"] + 1.0), 52, amber=True)
    return img


LAT = None


def lattice_pts(n=7, a=3.4):
    g = np.arange(n) - (n - 1) / 2
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1) * a


def s1_kafes(v, u):
    """peletin icine dalis: duzenli atom kafesi; ortada bir uranyum cekirdegi, gelen notron."""
    S = Sahne()
    atom_ortami(S)
    S.fog = (0.012, 0.0, -1000, 0.85)
    S.fog_col = (0.01, 0.015, 0.035)
    P = lattice_pts()
    heat = 0.4
    for i, p in enumerate(P):
        if np.allclose(p, 0):
            continue
        j = 0.15 * math.sin(u * 7 + i * 1.7) * heat
        S.add(SPH_LO, TRS(tuple(p + j), s=0.55), atom.NEUTRON.but(col=srgb((120, 140, 175)), emi=(0.05, 0.07, 0.12)))
        S.particle(tuple(p + j), 1.6, (0.35, 0.55, 1.0, 0.10), kind=0, add=True)
    zoomin = fade(u, S1["gecen"] - 1.0, S1["gecen"] + 3.0)
    uc = atom.get("U235")
    sc = 0.12 + 0.0 * zoomin
    atom.draw(S, uc.P, uc.isp, (0, 0, 0), sc, R=ry(u * 0.2))
    S.particle((0, 0, 0), 2.2, (1.0, 0.55, 0.3, 0.25), kind=0, add=True)
    # notron yaklasir ve donar
    tq = fade(u, S1["gecen"] + 0.5, S1["soru"] + 0.5)
    npos = np.array([6.0 - 5.0 * tq, 0.6 - 0.45 * tq, 1.0 - 0.8 * tq])
    if u > S1["gecen"]:
        atom.neutron(S, npos, 0.12, glow=1.2, trail=[npos + np.array([0.25 * k, 0.03 * k, 0.05 * k]) for k in range(1, 10)])
    atom.dust(S, u, n=120, R=14, a=0.18)
    cam = path(v, [(0, (22, 14, 34), (0, 0, 0), 40), (S1["fisyon"] - S1["isi"], (8, 4, 13), (0, 0, 0), 40),
                   (S1["soru"] - S1["isi"], (2.2, 0.8, 2.8), (0.8, 0.2, 0.3), 36)], near=0.02, aperture=0.35)
    img = ciz(S, cam, u)
    a_f = win(u, S1["fisyon"] - 0.2, S1["gecen"] + 0.3)
    label(img, "FİSYON", 960, 470, a_f, 120, AMBER, F_XB)
    label(img, "çekirdeğin bölünmesi", 960, 580, a_f, 48, WHITE, F_SB)
    label(img, "Bir nötron çekirdeği nasıl böler?", 960, 860, fade(u, S1["soru"] + 0.3, S1["soru"] + 1.2), 60, WHITE, F_B, 1500)
    return img


def scene1(t, u):
    return shots(u, [(-2.0, s1_dis), (S1["kalp"] + 0.8, s1_cekirdek), (S1["demet"] + 0.3, s1_demet),
                     (S1["zirk"] - 0.2, s1_cubuk), (S1["isi"] + 1.2, s1_kafes)], xf=1.0)


# ================================================================= SAHNE 2
D2 = DURS[1]
S2 = dict(n32=at(1, "Amerika Enerji Bakanlığı'nın el kitabına göre ancak"), y38=at(1, "Altı yıl sonra"),
          nrc=at(1, "Bugün Nükleer Düzenleme"), neden=at(1, "Peki neden nötron"))
CARDS = [((0.08, 0.762, 0.04), 0.12), ((0.36, 0.762, 0.12), -0.1)]


def s2_arsiv(v, u):
    S = Sahne()
    ic_mekan(S)
    S.sun_dir = norm((0.2, 1.0, 0.35))
    S.sun_col = (0.35, 0.35, 0.38)
    S.exposure = 1.25
    S.shadow_box = ((0, 1.0, -0.5), 3.5)
    S.ssao_r = 0.25
    arsiv.room(S, t=u)
    a1 = fade(u, S2["n32"] - 0.5, S2["n32"] + 1.0)
    a2 = fade(u, S2["y38"], S2["y38"] + 1.5)
    if a1 > 0:
        p, r = CARDS[0]
        arsiv.card(S, TRS((p[0], p[1], p[2] + (1 - a1) * 0.3), ry(r)), glow=0.0)
        S.add(SPH, TRS((p[0] + 0.03, p[1] + 0.022 + 0.004 * math.sin(u * 2), p[2] - 0.01), s=0.02),
              atom.NEUTRON.but(emi=(0.1, 0.15, 0.3)))
    if a2 > 0:
        p, r = CARDS[1]
        arsiv.card(S, TRS((p[0] + (1 - a2) * 0.4, p[1], p[2]), ry(r)), glow=0.0)
    cam = path(u, [(-1, (2.6, 1.55, 3.6), (-0.4, 1.1, -1.5), 44), (S2["n32"] - 1.0, (1.2, 1.35, 1.6), (0.0, 0.85, -0.2), 42),
                   (S2["y38"] + 2.0, (0.62, 1.15, 0.75), (0.2, 0.77, 0.06), 40), (S2["nrc"] + 2.0, (0.6, 1.05, 0.62), (0.25, 0.77, 0.08), 38),
                   (S2["neden"] + 3.0, (0.42, 0.88, 0.25), (0.36, 0.765, 0.12), 34)], near=0.02, aperture=0.45)
    img = ciz(S, cam, u)
    if a1 > 0.05:
        x, y = proj(cam, CARDS[0][0])
        label(img, "1932", x, y - 70, a1, 64, AMBER, F_XB)
        label(img, "NÖTRON · yüksüz", x, y + 5, a1, 40, WHITE, F_SB)
    if a2 > 0.05:
        x, y = proj(cam, CARDS[1][0])
        label(img, "1938", x, y - 70, a2 * (1 - fade(u, S2["neden"] - 1.0, S2["neden"])), 64, AMBER, F_XB)
        label(img, "FİSYON", x, y + 5, a2 * (1 - fade(u, S2["neden"] - 1.0, S2["neden"])), 44, WHITE, F_B)
    an = win(u, S2["y38"] + 2.5, S2["nrc"] + 0.6)
    label(img, "Otto Hahn · Lise Meitner · Fritz Strassmann", 960, 840, an, 44, WHITE, F_SB, 1500)
    ad = win(u, S2["nrc"] + 0.6, S2["neden"] + 0.3)
    cardl(img, ["Fisyon (NRC):", "ağır çekirdek bölünür", "≥ 2 hafif çekirdek + enerji (çoğunlukla ısı)"], 560, 330, ad, 42)
    label(img, "Neden nötron?", 960, 520, fade(u, S2["neden"] + 0.2, S2["neden"] + 1.0), 84, WHITE, F_XB)
    return img


def scene2(t, u):
    return s2_arsiv(u, u)


# ================================================================= SAHNE 3
D3 = DURS[2]
S3 = dict(proton=at(2, "Şimdi çekirdeğe bir proton"), guclu=at(2, "Geçen bölümde gördüğümüz"),
          notron=at(2, "Nötron ise yüksüzdür"), ustelik=at(2, "Üstelik uranyum"), yavas=at(2, "Bu yavaş nötronlar"))


def _coulomb_path(b=3.2, k=55.0, x0=-40.0, v=9.0, n=900, dt=0.012):
    p = np.array([x0, b, 0.0])
    vel = np.array([v, 0.0, 0.0])
    out = []
    for _ in range(n):
        r = np.linalg.norm(p)
        acc = k * p / r ** 3
        vel = vel + acc * dt
        p = p + vel * dt
        out.append(p.copy())
    return np.array(out)


PPATH = _coulomb_path()


def s3_atom(v, u):
    S = Sahne()
    atom_ortami(S)
    uc = atom.get("U235")
    R = ry(u * 0.15) @ rx(0.2)
    atom.draw(S, uc.P, uc.isp, (0, 0, 0), 0.5, R=R)
    rn = np.linalg.norm(uc.P, axis=1).max() * 0.5 + 0.5
    # itme alani: soluk kirmizi-turuncu ic ice kabuklar (uzun menzil)
    af = 0.6 * fade(u, 1.0, 4.0)
    for k, rr in enumerate((3.0, 6.0, 10.0)):
        S.particle((0, 0, 0), rn * rr, (1.0, 0.42, 0.2, 0.10 * af), kind=0, add=True)
    # nukleer kuvvet menzili: ince camgobegi kabuk
    ag = win(u, S3["guclu"] + 0.5, S3["notron"] + 2.0, 1.0)
    if ag > 0:
        S.add(SPH, TRS((0, 0, 0), s=rn * 1.08), Mat((0.3, 0.9, 1.0), 0.5, emi=(0.15, 0.5, 0.7), alpha=0.18 * ag, add=True))
    # proton yolu
    up = u - S3["proton"]
    if 0 < up < S3["notron"] - S3["proton"] + 2:
        i = int(min(len(PPATH) - 1, up / 7.5 * len(PPATH)))
        pos = PPATH[i] * np.array([1, 1, 1])
        tr = [PPATH[max(0, i - k * 6)] for k in range(1, 40)]
        atom.proton(S, pos, 0.5, glow=1.0, trail=tr, alpha=1 - fade(up, 9.5, 11.0))
    un = u - S3["notron"]
    if un > 0:
        x = -40 + min(un, 6.0) * (40 - rn - 0.5) / 6.0
        pos = np.array([x, 0.8, 0.0])
        tr = [pos - np.array([0.9 * k, 0, 0]) for k in range(1, 26)]
        atom.neutron(S, pos, 0.5, glow=1.2, trail=tr)
    atom.dust(S, u, n=200, R=50, a=0.2, speed=1.0 + 6.0 * fade(u, S3["yavas"], S3["yavas"] + 2))
    cam = path(u, [(-1, (0, 6, 38), (0, 0, 0), 42), (S3["proton"], (-6, 8, 44), (-6, 0, 0), 44),
                   (S3["notron"] + 6.0, (-4, 5, 34), (-2, 0.5, 0), 40), (S3["yavas"], (-6, 2.5, 18), (-1.5, 0.5, 0), 38),
                   (D3 + 1, (-7, 2, 15), (-2.5, 0.6, 0), 36)], aperture=0.3)
    img = ciz(S, cam, u)
    label(img, "Uranyum: 92 proton", 960, 120, win(u, 1.0, S3["proton"] + 1.0), 52, WHITE, F_B)
    label(img, "Proton: itilir", 480, 170, win(u, S3["proton"] + 4.5, S3["notron"] + 0.5), 52, (255, 140, 90), F_B)
    label(img, "Nükleer kuvvet: çekirdek dışında etkisiz", 960, 830, win(u, S3["guclu"] + 1.0, S3["notron"] + 0.3), 44, CYAN, F_SB, 1500)
    label(img, "Nötron: yüksüz, itilmez", 520, 170, win(u, S3["notron"] + 1.0, S3["ustelik"] + 0.6), 52, (170, 205, 255), F_B)
    cardl(img, ["U-235: termal nötronla bölünür"], 960, 170, win(u, S3["ustelik"] + 1.5, S3["yavas"] + 0.4), 50)
    cardl(img, ["Termal nötron ≈ 2200 m/s", "(20 °C)"], 1420, 250, fade(u, S3["yavas"] + 1.0, S3["yavas"] + 2.0), 52, amber=True)
    return img


def scene3(t, u):
    return s3_atom(u, u)


# ================================================================= SAHNE 4
D4 = DURS[3]
S4 = dict(damla=at(3, "Damlayı bir arada"), nuk=at(3, "Çekirdekte bu işi"), yakal=at(3, "Nötron yakalandığında"),
          titre=at(3, "Bu enerjiyle damla"), halter=at(3, "Enerji yeterince büyükse"), kritik=at(3, "Kritik an budur"),
          itme=at(3, "İtme baskın gelince"), peki=at(3, "Peki yeterince büyük"), u238=at(3, "Uranyum iki yüz otuz sekizde"),
          tekcift=at(3, "El kitabı farkın"), dogal=at(3, "Amerika Nükleer Düzenleme Kurulu'na göre doğal"))
SPLIT = None


def split_data():
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    return SPLIT


def s4_damla(v, u):
    """studyo, havada salinan gercekci su damlasi."""
    S = Sahne()
    S.bg = (0.004, 0.006, 0.01)
    S.sun_dir = norm((-0.6, 0.7, 0.4))
    S.sun_col = (1.2, 1.25, 1.3)
    S.sky_zen, S.sky_hor, S.gnd = (0.5, 0.6, 0.75), (0.2, 0.25, 0.3), (0.02, 0.02, 0.025)
    S.sun_disk = 0
    S.shadow = False
    S.ssao = 0
    S.amb, S.env = 0.15, 1.1
    S.bloom = 0.7
    a = 0.06 * math.sin(u * 5.0) * (0.6 + 0.4 * math.sin(u * 0.7))
    sc = (1 + a, 1 - a * 0.6, 1 - a * 0.6)
    S.add(SPH, TRS((0, 0, 0), ry(u * 0.3), sc), Mat((0.03, 0.06, 0.09), 0.03, 0.0))
    S.add(SPH, TRS((0.12, -0.25, 0.3), s=(0.45, 0.35, 0.4)), Mat((0.0, 0.0, 0.0), 0.5, emi=(0.10, 0.2, 0.3), alpha=0.5, add=True))
    S.light((-2.0, 2.2, 2.5), 3, (1, 1, 1), 3.0)
    S.light((2.5, 0.5, 2.0), 3, (0.6, 0.8, 1.0), 1.5)
    S.light((0.0, -2.5, 1.0), 2, (0.3, 0.5, 0.8), 1.0)
    for k in range(40):
        ang = k * 2.4
        rr = 2.5 + (k % 5) * 0.6
        S.particle((math.cos(ang) * rr, math.sin(ang * 1.3) * 1.5, -2.5 - (k % 7)), 0.08 + 0.05 * (k % 3), (0.5, 0.7, 1.0, 0.25), add=True)
    cam = Cam((0.3 + 0.2 * math.sin(u * 0.2), 0.25, 5.2 - v * 0.05), (0, 0, 0), fov=36, aperture=0.3)
    img = ciz(S, cam, u)
    label(img, "Sıvı damlası modeli", 960, 140, win(u, 1.5, S4["nuk"] + 0.8), 58, WHITE, F_B)
    return img


def s4_cekirdek(v, u):
    """bilesik cekirdek: yakalama, salinim, halter, bolunme."""
    S = Sahne()
    atom_ortami(S)
    src, dst, grp, isp, cap = split_data()
    ty = S4["yakal"] + 2.5
    excite = fade(u, ty, ty + 1.0)
    osc_amp = 0.16 * fade(u, S4["titre"], S4["titre"] + 1.5) * (1 - fade(u, S4["halter"], S4["halter"] + 2.0))
    stretch = fade(u, S4["halter"] + 0.5, S4["kritik"] + 1.0)
    sep = fade(u, S4["itme"] + 0.2, S4["itme"] + 3.5)
    Q = src.copy()
    osc = osc_amp * math.sin((u - S4["titre"]) * 4.2)
    Q = Q * np.array([1 + osc + 0.95 * stretch, 1 - osc * 0.5 - 0.22 * stretch, 1 - osc * 0.5 - 0.22 * stretch])
    pinch = 1 - 0.62 * stretch * np.exp(-(Q[:, 0] / 2.6) ** 2)
    Q[:, 1] *= pinch
    Q[:, 2] *= pinch
    if sep > 0:
        cen = np.array([[-9.5, 0, 0], [12.5, 0, 0]])
        out = Q.copy()
        for i in range(len(Q)):
            if grp[i] < 2:
                tgt = dst[i] + cen[grp[i]] * 1.0
                out[i] = Q[i] * (1 - sm(sep * 1.4)) + tgt * sm(sep * 1.4)
                out[i] += cen[grp[i]] * sep * 0.8
            else:
                d = np.array([0.2, 1.0, 0.3]) if i % 3 == 0 else (np.array([0.1, -0.8, 0.7]) if i % 3 == 1 else np.array([-0.2, 0.3, -1.0]))
                out[i] = Q[i] + d * sep * 22
        Q = out
    s = 0.62
    Rr = ry(-0.25 + u * 0.05)
    pts = (Q @ Rr.T) * s
    # yakalanan notron
    incoming = u < ty
    for i in range(len(pts)):
        if i == cap and incoming:
            k = fade(u, S4["yakal"] - 1.0, ty)
            p0 = np.array([30.0, 3.0, 4.0])
            pos = p0 * (1 - k) + pts[i] * k
            atom.neutron(S, pos, s, glow=1.3, trail=[pos + (p0 - pos) * 0.04 * j for j in range(1, 10)] if k < 0.98 else None)
            continue
        m = atom.PROTON if isp[i] else atom.NEUTRON
        if grp[i] == 2 and sep > 0:
            atom.neutron(S, pts[i], s, glow=1.3)
            continue
        if excite > 0:
            e = excite * (0.5 + 0.25 * math.sin(u * 9 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (0.5 * e, 0.22 * e, 0.05 * e))))
        S.add(SPH, TRS(tuple(pts[i]), s=s), m)
    if excite > 0 and sep < 0.5:
        S.particle((0, 0, 0), 14 * (1 + 0.5 * stretch), (1.0, 0.6, 0.2, 0.18 * excite * (1 - sep * 2)), add=True)
    # boyun: kuvvet oklari (kritik an)
    ak = win(u, S4["kritik"] + 0.5, S4["itme"] + 1.0, 0.6)
    if ak > 0:
        for sgn in (-1, 1):
            p0 = np.array([sgn * 13.0, 0, 0]) @ Rr.T * s
            p1 = np.array([sgn * 19.0, 0, 0]) @ Rr.T * s
            S.add(CYL, align(p0, p1, 0.35), Mat((1, 0.3, 0.2), 0.4, emi=(2.5 * ak, 0.6 * ak, 0.3 * ak), alpha=ak))
            S.add(("koni", lambda: m_lathe([(1, 0), (0.0, 1.0)], 24, cap0=True)), TRS(tuple(p1), (Rr @ rz(-sgn * math.pi / 2)), (0.8, 1.6, 0.8)),
                  Mat((1, 0.3, 0.2), 0.4, emi=(2.5 * ak, 0.6 * ak, 0.3 * ak), alpha=ak))
        for k in range(5):
            y = (k - 2) * 0.9
            p = np.array([0, y, 0]) @ Rr.T * s
            S.particle(tuple(p), 1.2, (0.3, 0.9, 1.0, 0.5 * ak * (1 - fade(u, S4["kritik"] + 3.0, S4["itme"]))), add=True)
    if sep > 0:
        gw = sep * (1 - sep)
        S.particle((0, 0, 0), 30 * sep + 4, (1.0, 0.8, 0.5, 0.6 * gw * 4), add=True)
    atom.dust(S, u, n=160, R=50, a=0.18)
    cam = path(u, [(S4["nuk"] - 1, (0, 3, 28), (0, 0, 0), 40), (S4["yakal"], (4, 4, 30), (2, 0, 0), 40),
                   (S4["titre"], (0, 5, 26), (0, 0, 0), 40), (S4["kritik"], (-2, 6, 30), (0, 0, 0), 40),
                   (S4["itme"] + 4, (0, 8, 46), (1, 0, 0), 44)], aperture=0.25)
    img = ciz(S, cam, u)
    label(img, "U-235 + n → U-236*", 960, 130, win(u, ty - 0.3, S4["titre"] + 3.0), 62, AMBER, F_XB)
    label(img, "uyarılmış bileşik çekirdek", 960, 205, win(u, ty + 0.5, S4["titre"] + 3.0), 40, WHITE, F_SB)
    label(img, "Kısa menzilli çekim  ↔  uzun menzilli itme", 960, 840, win(u, S4["kritik"] + 0.8, S4["itme"] + 1.5), 48, WHITE, F_B, 1500)
    return img


def bars(S, u, x0, req, got, a, lab_col):
    sc = 0.6
    hr = req * sc * a
    hg = got * sc * a
    S.add(BOX, TRS((x0 - 0.8, hr / 2, 0), s=(1.2, max(hr, 0.01), 1.2)), Mat((0.6, 0.65, 0.7), 0.3, 0.6, emi=(0.08, 0.1, 0.12)))
    S.add(BOX, TRS((x0 + 0.8, hg / 2, 0), s=(1.2, max(hg, 0.01), 1.2)), Mat(lab_col, 0.3, 0.2, emi=tuple(c * 0.9 for c in lab_col)))
    return hr, hg


def s4_tablo(v, u):
    S = Sahne()
    atom_ortami(S)
    S.shadow = True
    S.shadow_box = ((0, 2, 0), 9)
    S.add(BOX, TRS((0, -0.05, 0), s=(30, 0.1, 14)), Mat((0.03, 0.05, 0.09), 0.25, 0.0, pat="duz"))
    a1 = fade(u, S4["peki"] + 1.0, S4["peki"] + 4.0)
    a2 = fade(u, S4["u238"] + 0.5, S4["u238"] + 3.5)
    bars(S, u, -3.2, 6.5, 6.8, a1, (0.25, 0.95, 0.55))
    if a2 > 0:
        bars(S, u, 3.2, 7.0, 5.5, a2, (1.0, 0.65, 0.2))
    cam = path(u, [(S4["peki"] - 1, (0, 4.5, 16), (0, 2.2, 0), 40), (S4["u238"] + 3, (1.5, 4.0, 15), (0.8, 2.2, 0), 40),
                   (S4["tekcift"] + 1, (0, 3.5, 14), (0, 2.2, 0), 40)], aperture=0.15)
    img = ciz(S, cam, u)
    for x0, req, got, a, nm in ((-3.2, 6.5, 6.8, a1, "U-235"), (3.2, 7.0, 5.5, a2, "U-238")):
        if a <= 0.02:
            continue
        x, y = proj(cam, (x0, -0.4, 0.8))
        label(img, nm, x, y + 40, a, 56, WHITE, F_XB)
        xr, yr = proj(cam, (x0 - 0.8, req * 0.6 * a + 0.4, 0))
        xg, yg = proj(cam, (x0 + 0.8, got * 0.6 * a + 0.4, 0))
        label(img, "gereken " + ("%.1f" % req).replace(".", ","), xr - 30, yr - 20, a, 36, MUTED, F_SB)
        label(img, "gelen " + ("%.1f" % got).replace(".", ","), xg + 30, yg - 20, a, 36, WHITE, F_SB)
    cardl(img, ["U-235: 6,8 > 6,5 MeV", "termal nötron yeter"], 460, 170, win(u, S4["peki"] + 4.5, S4["tekcift"] + 0.5), 44)
    cardl(img, ["U-238: 5,5 < 7,0 MeV", "hızlı nötron gerekir (−1,5)"], 1460, 170, win(u, S4["u238"] + 3.5, S4["tekcift"] + 0.5), 44, amber=True)
    cardl(img, ["Tek-çift etkisi", "U-235: 143 nötron + 1 = 144"], 960, 170, win(u, S4["tekcift"] + 1.0, S4["dogal"] + 0.5), 48)
    return img


ODA = np.random.default_rng(42).choice(1000, 7, replace=False)


def s4_dogal(v, u):
    S = Sahne()
    atom_ortami(S)
    g = np.arange(10) - 4.5
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1) * 1.15
    hl = fade(u, S4["dogal"] + 3.5, S4["dogal"] + 6.0)
    odd = set(int(i) for i in ODA)
    gray = Mat((0.42, 0.45, 0.5), 0.45, 0.2)
    for i, p in enumerate(P):
        if i in odd:
            S.add(SPH_LO, TRS(tuple(p), s=0.45), Mat((1.0, 0.62, 0.18), 0.3, emi=(2.0 * hl + 0.2, 1.0 * hl + 0.1, 0.2 * hl)))
            if hl > 0:
                S.particle(tuple(p), 2.2, (1.0, 0.65, 0.25, 0.35 * hl), add=True)
        else:
            S.add(SPH_LO, TRS(tuple(p), s=0.45), gray)
    ang = u * 0.08
    cam = Cam((math.sin(ang) * 22, 9, math.cos(ang) * 22), (0, 0, 0), fov=42, aperture=0.2)
    img = ciz(S, cam, u)
    a = fade(u, S4["dogal"] + 1.0, S4["dogal"] + 2.5)
    cardl(img, ["Doğal uranyum (1000 atom)"], 960, 120, a, 48)
    label(img, "993 · U-238 (%99,3)", 430, 840, a, 48, (200, 210, 225), F_B)
    label(img, "7 · U-235 (%0,7)", 1500, 840, hl, 48, AMBER, F_B)
    return img


def scene4(t, u):
    return shots(u, [(-2, s4_damla), (S4["nuk"] - 0.3, s4_cekirdek), (S4["peki"] - 0.2, s4_tablo), (S4["dogal"] - 0.2, s4_dogal)], xf=1.0)


# ================================================================= SAHNE 5
D5 = DURS[4]
S5 = dict(olasi=at(4, "Parçalar her seferinde"), kararsiz=at(4, "Parçalar kararsızdır"), nrc=at(4, "Nükleer Düzenleme Kurulu'na göre bu"),
          ort=at(4, "El kitabına göre ortalama"), enerji=at(4, "Ve enerji"), hare=at(4, "Bunun yüz altmış yedisi"),
          artı=at(4, "Bu parçalar artı yüklüdür"), pelet=at(4, "Peletlerdeki ısının"), yedi=at(4, "Enerjinin yaklaşık yüzde yedisi"),
          sure=at(4, "Bütün bunlar ne kadar"), tril=at(4, "Yani saniyenin"))


def s5_parcalar(v, u):
    S = Sahne()
    atom_ortami(S)
    rb, cs = atom.get("RB93"), atom.get("CS140")
    k = sm(v / 3.0)
    gap = 6 + 10 * k
    atom.draw(S, rb.P, rb.isp, (-gap, 0, 0), 0.6, R=ry(u * 0.3))
    atom.draw(S, cs.P, cs.isp, (gap * 1.1, 0, 0), 0.6, R=ry(-u * 0.25))
    for j, d in enumerate([(0.2, 1, 0.3), (0.1, -0.9, 0.6), (-0.3, 0.3, -1)]):
        p = np.array(d) * (4 + 14 * k)
        atom.neutron(S, p, 0.6, glow=1.3, trail=[p * (1 - 0.05 * i) for i in range(1, 12)])
    if v < 2.5:
        S.particle((0, 0, 0), 4 + 40 * k, (0.75, 0.85, 1.0, 0.5 * (1 - k)), add=True)
    beta = fade(u, S5["kararsiz"] + 0.5, S5["kararsiz"] + 1.5) * (1 - fade(u, S5["nrc"], S5["nrc"] + 1))
    if beta > 0:
        for i in range(10):
            ph = (u * 0.7 + i * 0.1) % 1.0
            for c, sgn in ((-gap, -1), (gap * 1.1, 1)):
                d = np.array([math.cos(i * 2.3) , math.sin(i * 1.7), math.sin(i * 2.9)])
                p = np.array([c, 0, 0]) + d * (4 + ph * 18)
                S.particle(tuple(p), 0.5, (0.4, 0.9, 1.0, 0.8 * beta * (1 - ph)), add=True)
    atom.dust(S, u, n=160, R=50, a=0.18)
    cam = path(v, [(0, (0, 6, 40), (0, 0, 0), 42), (12, (3, 9, 50), (2, 0, 0), 44), (40, (-2, 7, 46), (2, 0, 0), 44)], aperture=0.2)
    img = ciz(S, cam, u)
    xr, yr = proj(cam, (-gap, -7, 0))
    xc, yc = proj(cam, (gap * 1.1, -8.5, 0))
    a = fade(v, 1.0, 2.5)
    label(img, "Rb-93", xr, yr + 30, a, 52, WHITE, F_XB)
    label(img, "Cs-140", xc, yc + 30, a, 52, WHITE, F_XB)
    label(img, "U-236 → Rb-93 + Cs-140 + 3n", 960, 120, win(v, 0.5, S5["olasi"] - S5["olasi"] + 9.0) if u < S5["olasi"] + 0.01 else win(u, 0.5, S5["olasi"] + 0.5), 56, AMBER, F_XB, 1600)
    cardl(img, ["Rb-93 → Sr → Y → Zr → Nb-93", "Cs-140 → Ba → La → Ce-140"], 960, 150, win(u, S5["kararsiz"] + 2.0, S5["nrc"] + 0.4), 42)
    cardl(img, ["Gama + 2 ya da daha fazla nötron", "ortalama 2,42"], 960, 150, win(u, S5["nrc"] + 1.0, S5["enerji"] + 0.3), 46, amber=True)
    return img


def yield_curve():
    A = np.linspace(72, 162, 160)
    y = np.exp(-((A - 95) / 8.5) ** 2) + np.exp(-((A - 140) / 8.5) ** 2) + 0.0006
    yl = np.log10(y)
    yl = (yl - yl.min()) / (yl.max() - yl.min())
    return np.stack([(A - 117) * 0.12, yl * 6.0, np.zeros_like(A)], 1)


YC = yield_curve()


def s5_verim(v, u):
    S = Sahne()
    atom_ortami(S)
    S.add(("verim", lambda: m_tube(YC, 0.09, 8)), TRS((0, -3, 0)), Mat((0.3, 0.9, 1.0), 0.3, emi=(0.4, 1.4, 2.0)))
    S.add(CYL_LO, align((-6.0, -3.2, 0), (6.5, -3.2, 0), 0.03), Mat((0.5, 0.6, 0.7), 0.5, emi=(0.2, 0.25, 0.3)))
    S.add(CYL_LO, align((-6.0, -3.2, 0), (-6.0, 3.6, 0), 0.03), Mat((0.5, 0.6, 0.7), 0.5, emi=(0.2, 0.25, 0.3)))
    for Ax in (95, 140):
        x = (Ax - 117) * 0.12
        S.add(SPH, TRS((x, 3.0, 0), s=0.22), Mat((1, 0.7, 0.3), 0.3, emi=(2.5, 1.4, 0.4)))
        S.particle((x, 3.0, 0), 1.4, (1, 0.7, 0.3, 0.5), add=True)
    cam = path(v, [(0, (0, 0.5, 15), (0, 0, 0), 40), (14, (1.5, 0.8, 13.5), (0, 0.2, 0), 40)], aperture=0.1)
    img = ciz(S, cam, u)
    for Ax in (95, 140):
        x, y = proj(cam, ((Ax - 117) * 0.12, 3.6, 0))
        label(img, "≈ %d" % Ax, x, y - 20, fade(v, 1.0, 2.0), 54, AMBER, F_XB)
    x, y = proj(cam, (0.3, -3.9, 0))
    label(img, "parçanın kütle numarası", x, y + 20, fade(v, 0.5, 1.5), 38, MUTED, F_SB)
    label(img, "U-235 termal fisyonunda en olası parçalar", 960, 120, fade(v, 0.3, 1.3), 46, WHITE, F_B, 1500)
    return img


def s5_enerji(v, u):
    S = Sahne()
    atom_ortami(S)
    S.shadow = True
    S.shadow_box = ((0, 3, 0), 8)
    S.add(BOX, TRS((0, -0.05, 0), s=(24, 0.1, 12)), Mat((0.03, 0.05, 0.09), 0.25))
    k = fade(v, 0.5, 3.5)
    H = 8.0
    segs = [(167, (1.0, 0.62, 0.18), 1.4), (5, (0.45, 0.7, 1.0), 0.6), (5, (0.8, 0.85, 1.0), 0.6), (10, (0.6, 0.75, 1.0), 0.6),
            (13, (0.4, 0.95, 0.8), 0.9)]
    y = 0
    tops = []
    for i, (val, col, e) in enumerate(segs):
        h = H * val / 200 * (k if i == 0 else fade(v, 2.0 + i * 0.4, 3.0 + i * 0.4))
        if h > 0.002:
            S.add(CYL, TRS((0, y + h / 2, 0), s=(1.3, h, 1.3)), Mat(col, 0.3, 0.1, emi=tuple(c * e for c in col)))
        tops.append(y + h)
        y += h + 0.01
    S.add(CYL, TRS((0, H / 2, 0), s=(1.42, H, 1.42)), Mat((0.6, 0.8, 1.0), 0.05, 0.0, alpha=0.12))
    cam = path(v, [(0, (0, 4.5, 15), (0, 4.0, 0), 40), (20, (2.5, 5.0, 14), (0, 4.0, 0), 40)], aperture=0.15)
    img = ciz(S, cam, u)
    x, y2 = proj(cam, (1.5, H + 0.3, 0))
    label(img, "≈ 200 MeV", x + 150, y2, fade(v, 0.5, 1.5), 64, WHITE, F_XB)
    x, y2 = proj(cam, (1.5, H * 167 / 400, 0))
    cardl(img, ["167 MeV", "parçaların hareketi", "(beşte dörtten fazla)"], x + 260, y2, fade(u, S5["hare"] + 0.5, S5["hare"] + 1.5), 44, amber=True)
    x, y2 = proj(cam, (-1.5, H - 0.4, 0))
    label(img, "≈ %7 (13 MeV): sonradan", x - 280, y2, fade(u, S5["yedi"], S5["yedi"] + 1.0), 40, (130, 240, 200), F_SB)
    return img


def s5_kafes(v, u):
    """parca kafesten gecer, atomlari sarsar, elektron koparir -> isi."""
    S = Sahne()
    atom_ortami(S)
    S.fog = (0.01, 0.0, -1000, 0.8)
    S.fog_col = (0.01, 0.012, 0.03)
    P = lattice_pts(9, 3.4)
    fx = -16 + v * 3.2
    fy, fz = 0.6, 0.4
    for i, p in enumerate(P):
        d = math.hypot(p[1] - fy, p[2] - fz)
        passed = fx - p[0]
        hit = math.exp(-(d / 3.5) ** 2) * (1 if passed > 0 else 0) * math.exp(-max(passed, 0) / 30)
        heat = 0.15 + 1.6 * hit
        j = np.array([math.sin(u * 13 + i), math.sin(u * 11 + 2 * i), math.sin(u * 12 + 3 * i)]) * 0.12 * heat
        col = srgb((120, 140, 175))
        e = (0.05 + 1.2 * hit, 0.06 + 0.35 * hit, 0.12 + 0.05 * hit)
        S.add(SPH_LO, TRS(tuple(p + j), s=0.55), atom.NEUTRON.but(col=col, emi=e))
        if hit > 0.3 and passed < 6:
            for q in range(2):
                ang = i * 1.3 + q * 3.1
                r = 0.6 + passed * 0.4
                S.particle((p[0] + math.cos(ang) * r, p[1] + math.sin(ang) * r, p[2] + 0.3), 0.35, (0.4, 0.9, 1.0, 0.8 * (1 - passed / 6)), add=True)
    fp = np.array([fx, fy, fz])
    cs = atom.get("CS140")
    atom.draw(S, cs.P, cs.isp, tuple(fp), 0.18, R=ry(u))
    S.particle(tuple(fp), 3.0, (1.0, 0.6, 0.3, 0.4), add=True)
    for k in range(1, 30):
        S.particle(tuple(fp - np.array([0.6 * k, 0, 0])), 1.2 * (1 - k / 30), (1.0, 0.6, 0.3, 0.3 * (1 - k / 30)), add=True)
    cam = path(v, [(0, (-10, 7, 16), (-6, 0, 0), 44), (10, (2, 6, 17), (2, 0, 0), 44)], aperture=0.3)
    img = ciz(S, cam, u)
    label(img, "Elektronlar kopar, atomlar sarsılır → ısı", 960, 130, fade(v, 1.0, 2.0), 50, WHITE, F_B, 1600)
    return img


def s5_pelet(v, u):
    """geri cekilme: isinan pelet cubugun icinde; cubuk demette."""
    S = Sahne()
    S.bg = (0.006, 0.014, 0.022)
    S.sun_dir = norm((-0.5, 0.6, 0.7))
    S.sun_col = (1.6, 1.65, 1.7)
    S.sky_zen, S.sky_hor, S.gnd = (0.06, 0.12, 0.18), (0.08, 0.14, 0.2), (0.02, 0.03, 0.04)
    S.sun_disk = 0
    S.amb, S.env = 0.6, 0.9
    S.shadow_box = ((0, 0.12, 0), 0.25)
    S.shadow_bias = 0.0004
    S.fog = (1.0, 0.0, -100, 0.7)
    S.fog_col = (0.006, 0.03, 0.05)
    g = 0.5 * (1 - 0.3 * fade(u, S5["yedi"] + 1, S5["yedi"] + 4))
    yakit.fuel_rod_cut(S, np.eye(4), n_pel=26, cut=0.5, glow=g)
    for (x, z) in [(-0.0126, 0), (0.0126, 0), (0, -0.0126), (-0.0126, -0.0126), (0.0126, -0.0126), (0.0252, -0.0126), (-0.0252, -0.0126)]:
        S.add(CYL, TRS((x, 0.2, z - 0.0126), s=(yakit.ROD_R, 0.5, yakit.ROD_R)), yakit.ZIRK.but(emi=(0.15 * g, 0.05 * g, 0.01 * g)))
    S.light((0.0, 0.13, 0.012), 0.08, (1.0, 0.45, 0.12), 2.0 * g)
    cam = path(v, [(0, (0.018, 0.12, 0.02), (0, 0.12, 0), 36), (8, (0.07, 0.16, 0.09), (0, 0.13, 0), 38), (20, (0.12, 0.2, 0.15), (0, 0.14, 0), 40)],
               near=0.002, aperture=0.5)
    img = ciz(S, cam, u)
    cardl(img, ["Pelet ortalaması ≈ 760 °C"], 1400, 260, win(v, 1.0, S5["yedi"] - S5["pelet"] + 0.5), 48, amber=True)
    cardl(img, ["≈ %7 (13 MeV) sonradan:", "durdurulunca da ısı sürer,", "soğutma gerekir"], 1380, 300, win(u, S5["yedi"] + 0.8, S5["sure"] + 0.2), 42)
    return img


def s5_zaman(v, u):
    S = Sahne()
    atom_ortami(S)
    k = fade(v, 0.5, (S5["tril"] - S5["sure"]) + 1.0)
    exps = [0, -3, -6, -9, -12, -13]
    idx = min(int(k * (len(exps) - 1) + 1e-6), len(exps) - 1)
    for i in range(60):
        x = (i - 30) * 0.5
        h = 0.6 if i % 10 == 0 else 0.25
        S.add(BOX, TRS((x, h / 2, 0), s=(0.04, h, 0.04)), Mat((0.5, 0.7, 0.9), 0.4, emi=(0.3, 0.6, 1.0)))
    S.add(BOX, TRS((0, -0.02, 0), s=(30, 0.04, 0.04)), Mat((0.5, 0.7, 0.9), 0.4, emi=(0.3, 0.6, 1.0)))
    pulse = 0.5 + 0.5 * math.sin(u * 6)
    S.add(SPH, TRS((0, 0.9, 0), s=0.18), Mat((1, 0.7, 0.3), 0.3, emi=(3, 1.6, 0.4)))
    S.particle((0, 0.9, 0), 1.2 + 0.4 * pulse, (1, 0.7, 0.3, 0.5), add=True)
    cam = Cam((0, 2.0, 9.0 - k * 6.5), (0, 0.4, 0), fov=40, aperture=0.2)
    img = ciz(S, cam, u)
    e = exps[idx]
    txt = "1 saniye" if e == 0 else "10^%d s" % e
    sup = {"-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    if e != 0:
        txt = "10" + "".join(sup[c] for c in str(e)) + " s"
    label(img, txt, 960, 300, fade(v, 0.3, 1.0), 110 if e == -13 else 80, AMBER if e == -13 else WHITE, F_XB)
    label(img, "nötron yakalanması → fisyon → yeni nötronlar", 960, 160, fade(v, 0.5, 1.5), 44, WHITE, F_SB, 1600)
    label(img, "saniyenin on trilyonda biri", 960, 820, fade(u, S5["tril"] + 0.3, S5["tril"] + 1.2), 56, AMBER, F_B)
    return img


def scene5(t, u):
    return shots(u, [(-2, s5_parcalar), (S5["olasi"] + 3.5, s5_verim), (S5["kararsiz"] - 0.2, s5_parcalar),
                     (S5["enerji"] - 0.2, s5_enerji), (S5["artı"] - 0.2, s5_kafes), (S5["pelet"] - 0.3, s5_pelet),
                     (S5["sure"] - 0.2, s5_zaman)], xf=0.9)


# ================================================================= SAHNE 6
D6 = DURS[5]
S6 = dict(tek=at(5, "Masaya tek bir top"), birkac=at(5, "Birkaç saniye"), kapan=at(5, "Kapan bir uranyum"),
          nrc=at(5, "Nükleer Düzenleme Kurulu zincirleme"), ama=at(5, "Ama her top"), kurul=at(5, "Kurula göre zincir"),
          fark=at(5, "Bir fark daha var"), omur=at(5, "El kitabına göre su ile"))
ZN = None


def zincir():
    global ZN
    if ZN is None:
        ZN = kapan.Zincir(t0=0.0)
    return ZN


def sim_time(u):
    """sahne saniyesi -> benzetim saniyesi: once agir cekim, sonra normal, sonra yavas."""
    a = S6["tek"] + 0.8
    if u < a:
        return -1.0
    x = u - a
    if x < 3.0:
        return x * 0.25
    return 0.75 + (x - 3.0) * 0.55


def s6_kapan(v, u):
    Z = zincir()
    s = sim_time(u)
    S = Sahne()
    ic_mekan(S)
    S.sun_dir = norm((0.25, 0.5, 1.0))
    S.sun_col = (2.6, 2.4, 2.1)
    S.amb = 0.55
    S.exposure = 1.0
    S.shadow_box = ((0, 0.8, 0), 2.2)
    S.shadow_bias = 0.0006
    S.ssao_r = 0.08
    kapan.room(S)
    kapan.table(S, TRS((0, 0, 0)))
    lost_hl = fade(u, S6["ama"] + 0.5, S6["ama"] + 2.0) * (1 - fade(u, S6["fark"] - 1.0, S6["fark"]))
    lost = set(b for b, tl in Z.lost if tl <= s)
    hl_trap = fade(u, S6["kapan"] + 0.3, S6["kapan"] + 1.5) * (1 - fade(u, S6["nrc"], S6["nrc"] + 1))
    for j in range(len(Z.traps)):
        kapan.trap(S, TRS(tuple(Z.traps[j])), Z.theta(j, s), highlight=0.0)
    red = kapan.TOP.but(col=(0.9, 0.15, 0.1), emi=(1.2, 0.1, 0.05))
    for bi in list(range(len(Z.rest))) + [-1]:
        p = Z.ball_pos(bi, s) if s >= 0 or bi != -1 else None
        if bi == -1 and s < 0:
            k = fade(u, S6["tek"] - 0.5, S6["tek"] + 0.8)
            p = Z.first[1] + np.array([0, 0.6 * (1 - k), 0]) if k > 0 else None
        if p is None:
            continue
        m = red if (bi in lost and lost_hl > 0) else kapan.TOP
        if bi in lost and lost_hl > 0:
            m = kapan.TOP.but(col=tuple(a * (1 - lost_hl) + b * lost_hl for a, b in zip(kapan.TOP.col, (0.9, 0.15, 0.1))), emi=(1.2 * lost_hl, 0.1 * lost_hl, 0.05 * lost_hl))
        S.add(SPH_LO if bi >= 0 else SPH, TRS(tuple(p), s=kapan.BALL_R), m)
    cam = path(u, [(-1, (2.6, 1.6, 2.4), (0, 0.8, 0), 40), (S6["tek"] - 0.5, (1.3, 1.05, 1.1), (-0.15, 0.8, 0.05), 36),
                   (S6["tek"] + 3.5, (0.9, 0.98, 0.75), (-0.15, 0.8, 0.05), 34), (S6["birkac"] + 1, (2.3, 1.7, 2.1), (0, 0.85, 0), 42),
                   (S6["ama"], (2.0, 1.9, 2.4), (0, 0.6, 0), 44), (S6["fark"], (2.4, 2.1, 2.6), (0, 0.6, 0), 46)], aperture=0.35, near=0.02)
    img = ciz(S, cam, u)
    a = hl_trap
    if a > 0:
        j = 70
        x, y = proj(cam, Z.traps[j] + np.array([0, 0.03, 0]))
        label(img, "kapan = U-235 çekirdeği", 520, 160, a, 48, AMBER, F_B)
        label(img, "top = nötron", 520, 230, fade(u, S6["kapan"] + 1.6, S6["kapan"] + 2.5) * (1 - fade(u, S6["nrc"], S6["nrc"] + 1)), 48, WHITE, F_B)
        label(img, "kapanma = fisyon", 520, 300, fade(u, S6["kapan"] + 2.8, S6["kapan"] + 3.7) * (1 - fade(u, S6["nrc"], S6["nrc"] + 1)), 48, CYAN, F_B)
    cardl(img, ["Zincirleme tepkime:", "kendini yeniden başlatır"], 560, 200, win(u, S6["nrc"] + 1.0, S6["ama"] + 0.3), 46)
    label(img, "kaybolan toplar: masadan düşen, kapanmış kapana çarpan", 960, 150, lost_hl * (1 - fade(u, S6["kurul"], S6["kurul"] + 0.8)), 42, (255, 120, 100), F_SB, 1700)
    cardl(img, ["Kendi kendini sürdürür:", "açığa çıkan ≥ kaybedilen"], 560, 210, win(u, S6["kurul"] + 0.5, S6["fark"] + 0.3), 48, amber=True)
    n_sprung = int(np.sum(Z.ts <= s)) if s >= 0 else 0
    label(img, "kapanan: %d / %d" % (n_sprung, len(Z.traps)), 1600, 130, win(u, S6["tek"] + 1.0, S6["kapan"] + 0.2) , 40, WHITE, F_SB)
    return img


def water_mols(n=26, seed=9):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        c = rng.uniform([-14, -5, -6], [14, 5, 4])
        R = ry(rng.uniform(0, 6.28)) @ rx(rng.uniform(0, 6.28))
        out.append((c, R))
    return out


WM = water_mols()


def s6_su(v, u):
    """su molekulleri arasinda sekerek yavaslayan notron; sayac 1..19."""
    S = Sahne()
    atom_ortami(S)
    O = Mat(srgb((220, 60, 60)), 0.3, emi=(0.08, 0.01, 0.01))
    Hm = Mat(srgb((235, 235, 240)), 0.3, emi=(0.04, 0.04, 0.05))
    ang = math.radians(104.5) / 2
    for c, R in WM:
        S.add(SPH, TRS(tuple(c), s=0.9), O)
        for sgn in (-1, 1):
            d = R @ np.array([math.sin(sgn * ang), math.cos(ang), 0]) * 1.05
            S.add(SPH, TRS(tuple(c + d), s=0.55), Hm)
    # notron: kirik cizgi yol, her carpismada yavaslar
    Lk = (S6["omur"] - S6["fark"]) - 1.0
    ncol = 19
    tk = np.cumsum([0.0] + [0.35 * 1.12 ** i for i in range(ncol)])
    tk = tk / tk[-1] * Lk
    rng = np.random.default_rng(3)
    pts = [np.array([-16.0, 0.0, 0.0])]
    for i in range(ncol):
        step = rng.normal(0, 1, 3) * 2.0 + np.array([1.6, 0, 0])
        pts.append(pts[-1] + step * (1.0 - i / 26))
    pts = np.array(pts)
    pts[:, 1] = np.clip(pts[:, 1], -4, 4)
    pts[:, 2] = np.clip(pts[:, 2], -5, 3)
    i = int(np.searchsorted(tk, v) - 1)
    i = max(0, min(i, ncol - 1))
    f = clamp01((v - tk[i]) / max(tk[i + 1] - tk[i], 1e-3))
    pos = pts[i] * (1 - f) + pts[i + 1] * f
    tr = []
    for k in range(1, 18):
        vv = v - k * 0.04
        j = max(0, min(int(np.searchsorted(tk, vv) - 1), ncol - 1))
        ff = clamp01((vv - tk[j]) / max(tk[j + 1] - tk[j], 1e-3))
        tr.append(pts[j] * (1 - ff) + pts[j + 1] * ff)
    atom.neutron(S, pos, 0.5, glow=1.4, trail=tr)
    for j in range(1, min(i + 1, ncol) + 1):
        S.particle(tuple(pts[j]), 0.9, (0.5, 0.8, 1.0, 0.35 * math.exp(-(v - tk[j]) * 2) if v > tk[j] else 0), add=True)
    atom.dust(S, u, n=120, R=40, a=0.15, speed=1.0)
    cam = Cam((pos[0] * 0.6 - 2, 6, 24), (pos[0] * 0.6, 0, 0), fov=44, aperture=0.2)
    img = ciz(S, cam, u)
    ncount = min(int(np.searchsorted(tk, v)), ncol)
    label(img, "çarpışma: %d" % max(ncount - 1, 0) if ncount < ncol else "≈ 19 çarpışma", 1560, 140, fade(v, 0.5, 1.2), 54, AMBER, F_XB)
    cardl(img, ["Fisyon nötronu ≈ 2 MeV", "→ termal ≈ 0,025 eV"], 520, 170, win(v, 0.8, Lk + 0.5), 46)
    cardl(img, ["Su: soğutucu + yavaşlatıcı"], 520, 170, win(v, Lk + 0.8, (S6["omur"] - S6["fark"]) + 0.2), 48)
    cardl(img, ["Termal nötronun ömrü ≈ 10⁻⁴ s", "saniyenin on binde biri"], 700, 170, fade(u, S6["omur"] + 1.0, S6["omur"] + 2.0), 48, amber=True)
    return img


def scene6(t, u):
    return shots(u, [(-2, s6_kapan), (S6["fark"] - 0.2, s6_su)], xf=1.0)


# ================================================================= SAHNE 7
D7 = DURS[6]
S7 = dict(bir=at(6, "Bir: nötron"), iki=at(6, "İki: nötronu"), uc=at(6, "Üç: uranyum"), dort=at(6, "Dört: bir fisyon"),
          bes=at(6, "Beş: her fisyon"), fare=at(6, "Fare kapanlı masada"), reak=at(6, "Bir reaktörde ise"),
          peki=at(6, "Peki zincir nasıl"), sonraki=at(6, "Bir sonraki bölümün"), sence=at(6, "Sence masadaki"))
ITEMS = ["1 · Nötron yüksüz: itilmez", "2 · Damla titreşir, ikiye ayrılır", "3 · U-235 yavaş, U-238 hızlı nötron ister",
         "4 · ≈ 200 MeV, çoğu ısı olur", "5 · Yeni nötronlar → zincir"]


def s7_ozet(v, u):
    S = Sahne()
    ic_mekan(S)
    S.sun_dir = norm((0.2, 1.0, 0.35))
    S.sun_col = (0.35, 0.35, 0.38)
    S.exposure = 1.25
    S.shadow_box = ((0, 1.0, -0.5), 3.5)
    S.ssao_r = 0.25
    arsiv.room(S, t=u)
    ks = [S7["bir"], S7["iki"], S7["uc"], S7["dort"], S7["bes"]]
    act = [win(u, k, (ks[i + 1] if i < 4 else S7["fare"]) + 0.2, 0.4) for i, k in enumerate(ks)]
    y = 0.762
    xs = [-0.35, -0.12, 0.1, 0.3, 0.5]
    # 1: notron + kucuk cekirdek
    uc = atom.get("C12")
    atom.draw(S, uc.P, uc.isp, (xs[0], y + 0.03, 0.05), 0.011)
    S.add(SPH, TRS((xs[0] + 0.05, y + 0.03, 0.05), s=0.008), atom.NEUTRON.but(emi=(0.2 + act[0], 0.3 + act[0], 0.6 + act[0])))
    # 2: damla
    S.add(SPH, TRS((xs[1], y + 0.03, 0.05), s=(0.032 * (1 + 0.1 * math.sin(u * 5)), 0.028, 0.028)), Mat((0.55, 0.7, 0.85), 0.03, alpha=0.6,
                                                                                                     emi=(0.1 * act[1], 0.2 * act[1], 0.3 * act[1])))
    # 3: iki cubuk
    S.add(BOX, TRS((xs[2] - 0.015, y + 0.02, 0.05), s=(0.02, 0.04, 0.02)), Mat((0.25, 0.95, 0.55), 0.3, emi=(0.2 * act[2] + 0.05, 0.9 * act[2] + 0.1, 0.4 * act[2])))
    S.add(BOX, TRS((xs[2] + 0.015, y + 0.016, 0.05), s=(0.02, 0.032, 0.02)), Mat((1.0, 0.65, 0.2), 0.3, emi=(0.9 * act[2] + 0.1, 0.5 * act[2], 0.1 * act[2])))
    # 4: enerji sutunu
    S.add(CYL, TRS((xs[3], y + 0.035, 0.05), s=(0.016, 0.07, 0.016)), Mat((1.0, 0.62, 0.18), 0.3, emi=(1.0 * act[3] + 0.1, 0.5 * act[3] + 0.05, 0.1 * act[3])))
    # 5: fare kapani
    kapan.trap(S, TRS((xs[4], y, 0.05), ry(0.4)), 0.0, highlight=act[4])
    for k in (-1, 1):
        S.add(SPH, TRS((xs[4] + 0.01 * k, y + 0.035, 0.05), s=0.02), kapan.TOP.but(emi=(0.3 * act[4],) * 3))
    cam = path(u, [(-1, (0.25, 1.25, 0.95), (0.08, 0.77, 0.05), 38), (S7["fare"], (0.18, 1.05, 0.6), (0.1, 0.77, 0.05), 36)], near=0.02, aperture=0.4)
    img = ciz(S, cam, u)
    for i in range(5):
        a = fade(u, ks[i] - 0.2, ks[i] + 0.6)
        col = AMBER if act[i] > 0.5 else WHITE
        label(img, ITEMS[i], 560, 190 + i * 80, a, 44, col, F_B, 1000)
        x, yy = proj(cam, (xs[i], y + 0.09, 0.05))
        if act[i] > 0.05:
            blit(img, pill(str(i + 1), F_B, 34, WHITE, AMBER, padx=18, pady=8), x, yy - 20, op=act[i])
    return img


def s7_reaktor(v, u):
    """kontrol cubugu kumesi demetin kilavuz tuplerine iner (su alti)."""
    S = Sahne()
    ortam_su(S, dens=0.8, caus=0.45, cscale=10)
    S.shadow_box = ((0, 3.8, 0), 0.6)
    S.shadow_bias = 0.0006
    yakit.assembly(S, np.eye(4), lod=-1)
    for (x, z) in [(-0.217, 0), (0.217, 0), (0, -0.217)]:
        yakit.assembly(S, TRS((x, 0, z)), lod=1)
    ins = fade(v, 1.0, 9.0) * 0.35
    top = 3.82 + 0.45 - ins
    spider = TRS((0, top + 0.12, 0))
    S.add(CYL, spider @ TRS((0, 0, 0), s=(0.025, 0.12, 0.025)), yakit.PASLANMAZ)
    off = -8 * yakit.PITCH
    for (i, j) in yakit.GT:
        if (i, j) == (8, 8):
            continue
        x, z = off + i * yakit.PITCH, off + j * yakit.PITCH
        S.add(CYL_LO, align((0, top + 0.1, 0), (x, top + 0.07, z), 0.002), yakit.PASLANMAZ)
        S.add(CYL_LO, TRS((x, top - 0.4, z), s=(0.0045, 0.95, 0.0045)), Mat(srgb((90, 92, 96)), 0.4, 1.0))
    su_kabarcik(S, u, (0, 3.9, 0), 0.35, n=30, size=0.002, speed=0.04)
    S.light((0.3, 4.4, 0.5), 0.9, (0.6, 0.9, 1.0), 3.0)
    cam = path(v, [(0, (0.42, 4.35, 0.5), (0, 3.95, 0), 40), (12, (0.36, 4.15, 0.42), (0, 3.92, 0), 38)], near=0.01, aperture=0.45)
    img = ciz(S, cam, u)
    label(img, "Kontrol çubukları: tepkime hızını düşürür ya da artırır", 960, 140, win(u, S7["reak"] + 1.0, S7["sonraki"] + 0.2), 44, WHITE, F_B, 1700)
    return img


def s7_fare(v, u):
    Z = zincir()
    S = Sahne()
    ic_mekan(S)
    S.sun_dir = norm((0.25, 0.5, 1.0))
    S.sun_col = (2.2, 1.9, 1.5)
    S.amb = 0.5
    S.shadow_box = ((0, 0.8, 0), 2.2)
    S.shadow_bias = 0.0006
    S.ssao_r = 0.08
    kapan.room(S)
    kapan.table(S, TRS((0, 0, 0)))
    s = 99.0
    for j in range(len(Z.traps)):
        kapan.trap(S, TRS(tuple(Z.traps[j])), Z.theta(j, s))
    for bi in list(range(len(Z.rest))) + [-1]:
        p = Z.ball_pos(bi, s)
        if p is not None:
            S.add(SPH_LO, TRS(tuple(p), s=kapan.BALL_R), kapan.TOP)
    cam = path(v, [(0, (2.2, 1.4, 1.6), (0, 0.78, 0), 40), (10, (1.6, 1.2, 2.2), (-0.2, 0.78, 0), 40)], aperture=0.35, near=0.02)
    img = ciz(S, cam, u)
    label(img, "birkaç saniyede biter", 960, 140, fade(v, 0.8, 1.6), 54, WHITE, F_B)
    return img


def end_card(img, u, t0):
    q = u - t0
    a = fade(q, 0.0, 1.2)
    if a <= 0:
        return img
    dark = (img.astype(np.float32) * 0.25).astype(np.uint8)
    dark = cv2.GaussianBlur(dark, (0, 0), 12)
    img = blend(img, dark, a)
    X = 520
    label(img, "SIRADAKİ", X, 210, a * fade(q, 0.2, 0.8), 34, CYAN, F_SB)
    label(img, "BÖLÜM 3: ZİNCİRLEME TEPKİME", X, 285, a * fade(q, 0.3, 0.9), 54, AMBER, F_XB, 900)
    label(img, "VE KRİTİKLİK · YAKINDA", X, 350, a * fade(q, 0.3, 0.9), 54, AMBER, F_XB, 900)
    label(img, "Tepkime neden kontrolden çıkmadan sürer?", X, 425, a * fade(q, 0.5, 1.1), 36, WHITE, F_M, 900)
    cv2.line(img, (X - 300, 490), (X + 300, 490), tuple(int(c * 0.5 * a) for c in CYAN), 2, cv2.LINE_AA)
    label(img, "KAYNAKLAR", X, 555, a * fade(q, 0.8, 1.4), 38, CYAN, F_B)
    for i, r in enumerate(("ABD Enerji Bakanlığı (DOE)", "ABD Nükleer Düzenleme Kurulu (NRC)")):
        label(img, r, X, 620 + i * 56, a * fade(q, 1.0 + 0.2 * i, 1.6 + 0.2 * i), 34, WHITE, F_M, 900)
    label(img, "Soru: Toplardan hiçbiri kaçmasaydı ne olurdu?", X, 770, a * fade(q, 1.4, 2.0), 32, MUTED, F_SB, 900)
    blit(img, pill("ABONE OL", F_B, 34, WHITE, AMBER, padx=34, pady=14, fill=(150, 40, 30), fill_a=0.9), X, 860,
         op=a * fade(q, 2.0, 2.6), scale=1 + 0.04 * math.sin(u * 4) * fade(q, 3, 4))
    return img


def scene7(t, u):
    img = shots(u, [(-2, s7_ozet), (S7["fare"] - 0.2, s7_fare), (S7["reak"] - 0.2, s7_reaktor)], xf=1.0)
    return end_card(img, u, S7["sence"] - 0.4)


# ================================================================= kare
SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7]


def frame(t):
    bounds = [STARTS[k] - GAP / 2 for k in range(1, 7)]
    k = sum(1 for b in bounds if t >= b)
    XF = 0.55
    img = None
    for b_i, b in enumerate(bounds):
        if abs(t - b) < XF:
            w = sm((t - (b - XF)) / (2 * XF))
            a = SCENES[b_i](t, t - STARTS[b_i])
            c = SCENES[b_i + 1](t, t - STARTS[b_i + 1])
            img = blend(a, c, w)
            break
    if img is None:
        img = SCENES[k](t, t - STARTS[k])
    img = np.ascontiguousarray(img)
    corner_tag(img, TAG, fade(t, 0.3, 1.2))
    img = (img.astype(np.float32) * (1 - fade(t, TOTAL - 0.8, TOTAL) * 0.85) * fade(t, 0.0, 0.6)).astype(np.uint8)
    return img


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "still":
        import time
        os.makedirs(os.path.join(WORK, "kareler"), exist_ok=True)
        for a in sys.argv[2:]:
            t0 = time.time()
            im = frame(float(a))
            cv2.imwrite(os.path.join(WORK, "kareler", "k_%06.2f.jpg" % float(a)), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            print(a, "%.2fs" % (time.time() - t0), flush=True)
    elif mode == "zaman":
        for k, d in enumerate([S1, S2, S3, S4, S5, S6, S7]):
            print(k + 1, STARTS[k], {kk: round(STARTS[k] + vv, 1) for kk, vv in d.items()})
    elif mode == "render":
        from render_kit import render_long
        render_long("bolum02", NFRAMES, WORK, workers=int(os.environ.get("WORKERS", "4")))
