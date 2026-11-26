#!/usr/bin/env python3
"""Gercekci 3D Short: 60 saniyede: Kayip kutle nereye gider? (kayip-kutle-nereye-gider.mp4), 1080x1920, 30 fps.

Ses: /tmp/s2/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar sesin sessizlik sinirlarindan.
Seslendirme metni: metinler/kayip-kutle-nereye-gider.txt (okunus duzeltmesi 2026-11-26).
Kaynaklar: DOE-HDBK-1019/1-93 (kutle kusuru tanimi; fisyon ornegi 236,052589 -> 235,85208 amu),
DOE-HDBK-1122-99 Modul 1.04 (bag enerjisi = kutle kusurunun enerji karsiligi), DOE "DOE Explains...Fusion Energy
Science" (E=mc2), NRC sozlugu "Binding energy".
Kullanim: WORK=/tmp/s2 python3 render_kayip_kutle_3d.py still 2 10 ... | render
"""
from dikey_kit import *

NAME = "kayip-kutle-nereye-gider"
TOTAL = 57.30
NFRAMES = int(TOTAL * FPS)
BOLUM = 1

Z = dict(dusun=1.06, kefe=4.37, esit=9.19, kusur=14.13, nereye=16.69, kaybolmadi=18.66, enerji=19.65, bag=20.81,
         karsilik=25.84, einstein=29.41, fisyon=34.43, u235=36.27, fark=44.19, ama=47.21, son=51.85)

TOP = 0.76                       # masa ustu
PIV = np.array([0.0, TOP + 0.47, 0.0])
ARM = 0.19
HANG = 0.25
PIRINC = Mat(srgb((196, 158, 92)), 0.28, 1.0, pat="fircali", scale=3.0)
CELIK = Mat(srgb((170, 172, 176)), 0.3, 1.0, pat="fircali")
TAS = Mat(srgb((22, 22, 25)), 0.25, 0.0)
MASA = Mat(srgb((92, 64, 42)), 0.5, 0.0, pat="ahsap", scale=2.0)
DUVAR = Mat(srgb((40, 46, 58)), 0.9, 0.0, pat="beton", scale=1.0)
PAN = ("kefe", lambda: m_lathe([(0.0, 0.0), (0.6, 0.012), (0.9, 0.06), (1.0, 0.2)], 40, smooth=True, cap0=True))
NUC_S = 0.0085


def nucleon_pts():
    rng = np.random.default_rng(4)
    pts = []
    while len(pts) < 12:
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(0.05, 1.0)) * 0.05
        p = np.array([r * math.cos(a), 0.0, r * math.sin(a)])
        if all(np.linalg.norm(p - q) > 2.2 * NUC_S for q in pts):
            pts.append(p)
    return pts


NPTS = nucleon_pts()
C12 = None


def theta(t):
    """kiris acisi (+: sag kefe asagi). Once sol (cekirdek) asagi, parcalar eklendikce sag agir basar."""
    n = n_dropped(t)
    base = -0.16 + 0.016 * n * 1.0
    k = fade(t, Z["esit"] - 0.2, Z["esit"] + 1.4)
    tgt = base * (1 - k) + 0.07 * k
    return tgt


def drop_time(i):
    return Z["kefe"] + 0.15 + i * 0.33


def n_dropped(t):
    return sum(1 for i in range(12) if t > drop_time(i) + 0.35)


def terazi(S, t, glow=0.0):
    global C12
    if C12 is None:
        C12 = atom.get("C12")
    th = theta(t)
    # masa ve oda
    S.add(BOX, TRS((0, TOP - 0.02, 0), s=(1.6, 0.04, 0.9)), MASA)
    S.add(BOX, TRS((0, 1.5, -0.9), s=(4, 3.0, 0.1)), DUVAR)
    S.add(BOX, TRS((0, -0.01, 0), s=(4, 0.02, 4)), Mat(srgb((50, 50, 54)), 0.8, pat="beton"))
    # taban, kolon
    S.add(BOX, TRS((0, TOP + 0.02, 0), s=(0.36, 0.04, 0.16)), TAS)
    S.add(BOX, TRS((0, TOP + 0.045, 0), s=(0.3, 0.01, 0.12)), PIRINC)
    S.add(CYL, align((0, TOP + 0.05, 0), tuple(PIV - np.array([0, 0.01, 0])), 0.011), PIRINC)
    S.add(SPH, TRS(tuple(PIV), s=0.016), CELIK)
    # kiris
    R = rz(-th)
    S.add(BOX, TRS(tuple(PIV), R, (2 * ARM + 0.02, 0.012, 0.014)), PIRINC)
    S.add(BOX, TRS(tuple(PIV + R @ np.array([0, -0.09, 0])), R, (0.005, 0.17, 0.005)), CELIK)   # ibre
    ends = []
    for sgn in (-1, 1):
        e = PIV + R @ np.array([sgn * ARM, 0, 0])
        ends.append(e)
        pan_y = e[1] - HANG
        c = np.array([e[0], pan_y, 0])
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.5
            q = c + np.array([0.062 * math.cos(a), 0.012, 0.062 * math.sin(a)])
            S.add(CYL, align(tuple(e), tuple(q), 0.0012), CELIK)
        S.add(PAN, TRS(tuple(c), s=(0.07, 0.07, 0.07)), PIRINC)
    # sol kefe: cekirdek (C-12) ; sag kefe: tek tek protonlar ve notronlar
    cl = np.array([ends[0][0], ends[0][1] - HANG + 0.006 + 2.3 * NUC_S, 0])
    Rn = ry(t * 0.2)
    m_emi = glow
    for i, p in enumerate(C12.P):
        m = atom.PROTON if C12.isp[i] else atom.NEUTRON
        if m_emi > 0:
            e = m_emi * (0.7 + 0.3 * math.sin(t * 6 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (1.0 * e, 0.45 * e, 0.12 * e))))
        S.add(SPH, TRS(tuple(cl + (Rn @ p) * NUC_S), s=NUC_S), m)
    if m_emi > 0:
        S.particle(tuple(cl), 0.06, (1.0, 0.65, 0.3, 0.45 * m_emi), add=True)
    cr = np.array([ends[1][0], ends[1][1] - HANG + 0.006 + NUC_S, 0])
    for i, p in enumerate(NPTS):
        td = drop_time(i)
        if t < td:
            continue
        k = fade(t, td, td + 0.35)
        pos = cr + p + np.array([0, (1 - k) ** 2 * 0.25, 0])
        m = atom.PROTON if i % 2 == 0 else atom.NEUTRON
        S.add(SPH, TRS(tuple(pos), s=NUC_S), m)
    return cl, cr


def lab(S):
    ic_mekan(S, warm=False)
    S.sun_dir = norm((-0.35, 0.9, 0.55))
    S.sun_col = (2.4, 2.3, 2.15)
    S.amb = 0.45
    S.exposure = 1.1
    S.shadow_box = ((0, TOP + 0.25, 0), 0.7)
    S.shadow_bias = 0.0005
    S.ssao_r = 0.05
    S.light((0.4, TOP + 0.6, 0.4), 1.5, (1.0, 0.9, 0.75), 1.2)


def sh_terazi(v, t):
    S = Sahne()
    lab(S)
    glow = fade(t, Z["enerji"] - 0.3, Z["enerji"] + 0.8) * (1 - fade(t, Z["einstein"] - 0.6, Z["einstein"]))
    cl, cr = terazi(S, t, glow)
    cam = path(t, [(-1, (0.06, TOP + 0.42, 1.6), (0.0, TOP + 0.36, 0.0), 40),
                   (Z["kusur"], (-0.02, TOP + 0.4, 1.45), (0.0, TOP + 0.35, 0.0), 40),
                   (Z["enerji"], (-0.14, TOP + 0.3, 0.62), (-0.17, TOP + 0.23, 0.0), 36),
                   (Z["einstein"] + 1, (-0.2, TOP + 0.27, 0.36), (-0.19, TOP + 0.23, 0.0), 32)], near=0.01, aperture=0.3)
    img = ciz(S, cam, t)
    lines(img, [("ÇEKİRDEK", WHITE), ("TERAZİDE", AMBER)], 400, win(t, 0.3, Z["kefe"] + 0.3), 82, t=t, t0=0.3)
    x, y = proj(cam, cl)
    label(img, "Çekirdek", min(max(x, 220), 860), y + 110, win(t, 1.6, Z["esit"]), 42, WHITE, F_SB)
    x2, y2 = proj(cam, cr)
    label(img, "Protonlar + nötronlar", min(max(x2, 220), 860), y2 + 110, win(t, Z["kefe"] + 1.0, Z["esit"]), 40, WHITE, F_SB, 420)
    lines(img, [("TERAZİ", WHITE), ("EŞİT KALMAZ", AMBER)], 400, win(t, Z["esit"] + 0.1, Z["kusur"]), 82, t=t, t0=Z["esit"])
    cardl(img, ["Çekirdek < parçaların toplamı"], 540, 1450, win(t, Z["esit"] + 2.3, Z["nereye"]), 46)
    lines(img, [("KÜTLE KUSURU", AMBER)], 420, win(t, Z["kusur"] + 0.1, Z["nereye"]), 84, t=t, t0=Z["kusur"])
    lines(img, [("O KÜTLE", WHITE), ("NEREYE GİTTİ?", AMBER)], 400, win(t, Z["nereye"] + 0.1, Z["enerji"]), 82, t=t, t0=Z["nereye"])
    lines(img, [("ENERJİYE", WHITE), ("DÖNÜŞTÜ", AMBER)], 400, win(t, Z["enerji"] + 0.05, Z["bag"] + 0.2), 86, t=t, t0=Z["enerji"])
    a = win(t, Z["bag"] + 0.2, Z["einstein"])
    label(img, "BAĞ ENERJİSİ", 540, 400, a, 80, AMBER, F_XB)
    cardl(img, ["Çekirdeği parçalarına", "ayırmak için gereken", "en küçük enerji"], 540, 1440, win(t, Z["bag"] + 0.4, Z["karsilik"]), 46)
    cardl(img, ["Bağ enerjisi =", "eksik kütlenin karşılığı"], 540, 1440, win(t, Z["karsilik"] + 0.1, Z["einstein"]), 50, amber=True)
    return img


def sh_emc2(v, t):
    S = Sahne()
    atom_ortami(S)
    c = atom.get("C12")
    k = 0.6 + 0.4 * math.sin(t * 3)
    atom.draw(S, c.P, c.isp, (0, 0, 0), 0.8, R=ry(t * 0.35) @ rx(0.4), glow=0.5 * k)
    S.particle((0, 0, 0), 9, (1.0, 0.7, 0.35, 0.35 * k), add=True)
    for r in (5.0, 8.0, 12.0):
        ph = ((t * 0.6 + r * 0.1) % 1.0)
        S.particle((0, 0, 0), r * (0.6 + ph), (1.0, 0.75, 0.4, 0.12 * (1 - ph)), add=True)
    atom.dust(S, t, n=140, R=40, a=0.16)
    cam = Cam((math.sin(t * 0.15) * 3, 2.5, 22 - (t - Z["einstein"]) * 0.5), (0, -1.5, 0), fov=40, aperture=0.15)
    img = ciz(S, cam, t)
    a = fade(t, Z["einstein"] + 0.4, Z["einstein"] + 1.0)
    label(img, "E = mc²", 540, 440, a, 140, AMBER, F_XB)
    label(img, "kütle ve enerji eşdeğerdir", 540, 580, a, 50, WHITE, F_SB)
    return img


SPLIT = None


def sh_fisyon(v, t):
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    src, dst, grp, isp, cap = SPLIT
    S = Sahne()
    atom_ortami(S)
    t0 = Z["u235"] + 2.4
    sep = fade(t, t0, t0 + 3.4)
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
    s = 0.62
    Rr = ry(0.3 + t * 0.05) @ rz(-0.45)
    pts = (Q @ Rr.T) * s
    hot = fade(t, t0 - 0.8, t0) * (1 - 0.5 * sep)
    for i in range(len(pts)):
        if i == cap and t < t0 - 0.6:
            k = fade(t, Z["u235"] + 0.2, t0 - 0.6)
            p0 = np.array([-26.0, -5.0, 8.0])
            pos = p0 * (1 - k) + pts[i] * k
            atom.neutron(S, pos, s, glow=1.3, trail=[pos + (p0 - pos) * 0.04 * j for j in range(1, 10)])
            continue
        if grp[i] == 2 and sep > 0:
            atom.neutron(S, pts[i], s, glow=1.3)
            continue
        m = atom.PROTON if isp[i] else atom.NEUTRON
        if hot > 0:
            e = hot * (0.6 + 0.3 * math.sin(t * 9 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (0.6 * e, 0.26 * e, 0.06 * e))))
        S.add(SPH, TRS(tuple(pts[i]), s=s), m)
    if sep > 0:
        gw = sep * (1 - sep)
        S.particle((0, 0, 0), 34 * sep + 6, (1.0, 0.8, 0.5, min(1.0, 2.6 * gw)), add=True)
    late = fade(t, Z["ama"] - 0.3, Z["ama"] + 1.5)
    if late > 0:
        S.particle((0, 0, 0), 60, (1.0, 0.7, 0.35, 0.25 * late), add=True)
    atom.dust(S, t, n=140, R=50, a=0.16)
    cam = path(t, [(Z["fisyon"] - 0.6, (0, 4, 42), (0, 0, 0), 42), (t0, (-3, 5, 36), (0, 0, 0), 42),
                   (Z["ama"], (0, 8, 54), (1, 0, 0), 46), (Z["son"] + 1, (0, 9, 60), (1, 0, 0), 46)], aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("FİSYONDA DA", WHITE), ("AYNI HESAP", AMBER)], 400, win(t, Z["fisyon"] + 0.1, Z["u235"] + 1.5), 80, t=t, t0=Z["fisyon"])
    label(img, "U-235 + nötron", 540, 420, win(t, Z["u235"] + 1.6, Z["fark"]), 70, WHITE, F_XB)
    cardl(img, ["Önce: 236,052589 u", "Sonra: 235,85208 u"], 540, 1430, win(t, Z["u235"] + 4.5, Z["ama"]), 50)
    label(img, "DOE el kitabındaki örnek tepkime", 540, 1580, win(t, Z["u235"] + 4.8, Z["ama"]), 34, MUTED, F_SB)
    lines(img, [("FARK:", WHITE), ("BİNDE BİRDEN AZ", AMBER)], 400, win(t, Z["fark"] + 0.1, Z["ama"]), 80, t=t, t0=Z["fark"])
    a = fade(t, Z["ama"] + 0.1, Z["ama"] + 0.7)
    lines(img, [("MUAZZAM ENERJİ,", WHITE), ("O KÜÇÜCÜK", AMBER), ("FARKTAN", AMBER)], 380, a, 82, t=t, t0=Z["ama"])
    return img


SHOTS = [(-1.0, sh_terazi), (Z["einstein"] - 0.2, sh_emc2), (Z["fisyon"] - 0.1, sh_fisyon)]


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
        "DOE-HDBK-1122-99 · Module 1.04 Nuclear Physics",
        "DOE · DOE Explains...Fusion Energy Science",
        "ABD NRC sözlüğü · Binding energy",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_kayip_kutle_3d", frame, NFRAMES, NAME)
