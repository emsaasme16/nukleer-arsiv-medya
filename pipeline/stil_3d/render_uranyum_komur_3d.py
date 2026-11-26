#!/usr/bin/env python3
"""Gercekci 3D Short: Mit mi, gercek mi? Uranyum komurun milyonlarca kati enerji verir
(uranyum-komurun-milyonlarca-kati-enerji-verir-mi.mp4), 1080x1920, 30 fps.

Ses: /tmp/s1/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar sesin sessizlik sinirlarindan (ffmpeg silencedetect).
Kaynaklar: DOE "The Harnessed Atom" (pelet < 14 g = 1 metrik ton komur), DOE "5 Reasons Nuclear Is a Good Neighbor"
(yuksuk boyunda pelet = 1 ton komur), DOE-STD-1128-98 (kimyasal tepkime atom basina birkac eV),
DOE-HDBK-1019/1-93 (U-235 fisyonu ortalama 200 MeV).
Kullanim: WORK=/tmp/s1 python3 render_uranyum_komur_3d.py still 1 9 20 | render
"""
from dikey_kit import *

NAME = "uranyum-komurun-milyonlarca-kati-enerji-verir-mi"
TOTAL = 56.1
NFRAMES = int(TOTAL * FPS)
BOLUM = 1

# seslendirme zamanlari (video saniyesi)
Z = dict(bak=1.07, yuksuk=2.65, iddia=7.12, mit=10.71, doe=12.31, ton=18.53, bolu=21.0, milyon=26.14,
         nereden=28.91, tek=31.19, kimya=32.84, fisyon=37.08, fark=42.5, yani=44.74, son=50.6)

BENCH_Y = 0.9
PEL = np.array([0.0, BENCH_Y + yakit.PEL_H / 2, 0.0])
PILE_C = np.array([0.15, 0.0, -1.55])
PILE_R, PILE_H = 0.95, 0.85

KOMUR = Mat(srgb((24, 24, 27)), 0.3, 0.0)
KOMUR2 = Mat(srgb((34, 33, 36)), 0.42, 0.0)
ZEMIN = Mat(srgb((112, 110, 104)), 0.85, 0.0, pat="beton", scale=1.5)
DUVAR = Mat(srgb((64, 70, 80)), 0.9, 0.0, pat="beton", scale=1.0)
TEZGAH = Mat(srgb((120, 84, 52)), 0.55, 0.0, pat="ahsap", scale=2.0)
CELIK = Mat(srgb((150, 152, 156)), 0.35, 1.0, pat="fircali")
PELET = yakit.SERAMIK.but(col=srgb((70, 68, 66)), rough=0.55)


def _pile():
    rng = np.random.default_rng(7)
    lumps = []
    n = 900
    for i in range(n):
        r = PILE_R * math.sqrt(rng.uniform(0, 1))
        a = rng.uniform(0, 2 * math.pi)
        h = PILE_H * (1 - (r / PILE_R) ** 1.15)
        y = h * rng.uniform(0.82, 1.0)
        s = rng.uniform(0.035, 0.085) * (1.2 if r > 0.7 else 1.0)
        R = ry(rng.uniform(0, 6.3)) @ rx(rng.uniform(-0.7, 0.7)) @ rz(rng.uniform(-0.7, 0.7))
        sc = (s * rng.uniform(0.8, 1.4), s * rng.uniform(0.55, 0.9), s * rng.uniform(0.8, 1.3))
        lumps.append(((PILE_C[0] + r * math.cos(a), y, PILE_C[2] + r * math.sin(a)), R, sc, i % 3 == 0, i % 6))
    return lumps


LUMPS = _pile()
PILE_MESH = ("komur_koni", lambda: m_lathe([(1.0, 0.0), (0.7, 0.33), (0.35, 0.72), (0.0, 0.96)], 40, cap0=True))


def depo(S):
    """beton zeminli depo: tezgah, uzerinde pelet; arkada bir ton komur yigini."""
    ic_mekan(S, warm=False)
    S.sun_dir = norm((-0.45, 0.85, 0.5))
    S.sun_col = (2.3, 2.15, 1.95)
    S.amb = 0.5
    S.exposure = 1.05
    S.shadow_box = ((0.4, 0.4, -0.7), 2.6)
    S.shadow_bias = 0.0007
    S.ssao_r = 0.12
    S.add(BOX, TRS((0, -0.01, -1.0), s=(8, 0.02, 8)), ZEMIN)
    S.add(BOX, TRS((0, 2.0, -3.2), s=(8, 4.0, 0.1)), DUVAR)
    S.add(BOX, TRS((-3.0, 2.0, -1.0), s=(0.1, 4.0, 8)), DUVAR)
    # tavan lambasi parlakligi (arka duvarda sicak bir lamba)
    S.add(BOX, TRS((1.4, 2.6, -3.13), s=(1.2, 0.08, 0.04)), Mat((1, 1, 1), 0.2, emi=(5.0, 4.6, 4.0)))
    S.light((1.4, 2.4, -2.6), 5.0, (1.0, 0.92, 0.8), 2.0)
    # tezgah
    S.add(BOX, TRS((0, BENCH_Y - 0.02, 0.05), s=(0.8, 0.04, 0.5)), TEZGAH)
    for sx in (-1, 1):
        for sz in (-1, 1):
            S.add(BOX, TRS((sx * 0.36, (BENCH_Y - 0.04) / 2, 0.05 + sz * 0.21), s=(0.035, BENCH_Y - 0.04, 0.035)), CELIK)
    # komur
    S.add(PILE_MESH, TRS(tuple(PILE_C), s=(PILE_R * 0.93, PILE_H * 0.9, PILE_R * 0.93)), KOMUR2)
    for p, R, sc, alt, k in LUMPS:
        S.add(ROCKS[k], TRS(p, R, sc), KOMUR2 if alt else KOMUR)
    # pelet
    yakit.pellet(S, tuple(PEL), mat=PELET)


def sh_pelet(v, t):
    """makro: tezgah uzerindeki pelet, yavas yorunge; sonra geri cekilip komur yigini gorunur."""
    S = Sahne()
    depo(S)
    ap = 0.55 * (1 - fade(t, 7.0, 10.5)) + 0.15
    if t < 6.6:
        an = 0.45 - 0.11 * t
        rr = 0.078 - 0.002 * t
        cam = Cam((PEL[0] + rr * math.sin(an), BENCH_Y + 0.02 + 0.0015 * t, PEL[2] + rr * math.cos(an)), tuple(PEL),
                  fov=30, near=0.005, aperture=ap)
    else:
        an = 0.45 - 0.11 * 6.6
        rr = 0.078 - 0.002 * 6.6
        e0 = (PEL[0] + rr * math.sin(an), BENCH_Y + 0.02 + 0.0015 * 6.6, PEL[2] + rr * math.cos(an))
        k = sm((t - 6.6) / 5.4)
        e1, g1 = np.array((0.05, 2.05, 1.75)), np.array((0.1, 0.55, -0.95))
        eye = np.array(e0) * (1 - k) + e1 * k
        tgt = PEL * (1 - k) + g1 * k
        cam = Cam(eye, tgt, fov=30 + 14 * k, near=0.005, aperture=ap)
    img = ciz(S, cam, t)
    a = win(t, Z["yuksuk"] + 0.3, Z["iddia"] - 0.1)
    x, y = proj(cam, PEL)
    cardl(img, ["< 14 gram"], 540, 1420, a, 60, amber=True)
    label(img, "URANYUM YAKIT PELETİ", 540, 1300, a, 48, WHITE, F_B)
    ai = win(t, Z["iddia"] + 0.1, Z["doe"] - 0.2)
    lines(img, [("“URANYUM, KÖMÜRÜN", WHITE), ("MİLYONLARCA KATI", AMBER), ("ENERJİ VERİR”", WHITE)], 400, ai, 74, t=t, t0=Z["iddia"])
    label(img, "MİT Mİ, GERÇEK Mİ?", 540, 1420, win(t, Z["mit"], Z["doe"] - 0.1), 70, CYAN, F_XB)
    return img


def sh_yigin(v, t):
    """bir ton komur ve tek pelet: genis plan, yavas kayma."""
    S = Sahne()
    depo(S)
    # pelette hafif vurgu isigi
    k = fade(t, Z["doe"] + 1.5, Z["doe"] + 3.0) * (1 - fade(t, Z["milyon"] + 1.5, Z["nereden"]))
    if k > 0:
        S.particle(tuple(PEL + np.array([0, 0.01, 0])), 0.05, (1.0, 0.7, 0.35, 0.35 * k), add=True)
    cam = path(t, [(Z["doe"] - 0.5, (0.05, 2.05, 1.75), (0.1, 0.55, -0.95), 44),
                   (Z["ton"], (0.45, 1.95, 1.65), (0.1, 0.55, -0.95), 44),
                   (Z["milyon"], (0.3, 1.5, 0.9), (0.05, 0.75, -0.6), 40),
                   (Z["nereden"] + 0.5, (0.05, 1.05, 0.35), (0.0, 0.9, -0.1), 34)], near=0.01, aperture=0.12)
    img = ciz(S, cam, t)
    a1 = win(t, Z["doe"] + 0.4, Z["milyon"] - 0.1)
    lines(img, [("1 PELET", WHITE), ("≈ 1 TON KÖMÜR", AMBER)], 400, a1, 82, t=t, t0=Z["doe"] + 0.4)
    label(img, "ABD Enerji Bakanlığı (DOE)", 540, 590, a1, 40, MUTED, F_SB)
    cardl(img, ["1 ton = 1.000.000 gram"], 540, 1300, win(t, Z["ton"] + 0.2, Z["milyon"] - 0.1), 50)
    cardl(img, ["Aynı ağırlıkta:", "> 70.000 kat"], 540, 1540, win(t, Z["bolu"] + 0.8, Z["milyon"] - 0.1), 58, amber=True)
    a2 = win(t, Z["milyon"] + 0.1, Z["nereden"] + 0.2)
    lines(img, [("70.000", AMBER), ("≠ 1.000.000", WHITE)], 420, a2, 96, t=t, t0=Z["milyon"] + 0.1)
    label(img, "Çok büyük, ama milyon değil", 540, 640, a2, 46, WHITE, F_SB)
    return img


# ----------------------------------------------------------------- atom alti
SPLIT = None


def split_data():
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    return SPLIT


def sh_kimya(v, t):
    """karbon atomu (C-12 cekirdegi + elektron bulutu) ve kucuk bir kivilcim: birkac eV."""
    S = Sahne()
    atom_ortami(S)
    c = atom.get("C12")
    R = ry(t * 0.3) @ rx(0.3)
    atom.draw(S, c.P, c.isp, (0, 0, 0), 0.55, R=R)
    rng = np.random.default_rng(3)
    for i in range(260):
        v3 = rng.normal(0, 1, 3)
        v3 /= np.linalg.norm(v3)
        rr = rng.uniform(4.5, 9.5)
        ang = t * (0.6 + 0.4 * rng.uniform()) + i
        p = (ry(ang * 0.3) @ v3) * rr
        S.particle(tuple(p), rng.uniform(0.25, 0.6), (0.4, 0.7, 1.0, 0.25), add=True)
    sp = win(t, Z["kimya"] + 1.6, Z["fisyon"] - 0.2, 0.3)
    fl = 0.6 + 0.4 * math.sin(t * 23)
    S.particle((6.5, 2.0, 1.0), 2.6, (1.0, 0.65, 0.3, 0.55 * sp * fl), add=True)
    atom.dust(S, t, n=120, R=40, a=0.15)
    cam = Cam((math.sin(t * 0.1) * 4, 3, 24 - (t - Z["tek"]) * 0.4), (0, 0, 0), fov=40, aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("TEK BİR", WHITE), ("TEPKİMEYE BAKINCA", AMBER)], 400, win(t, Z["tek"] + 0.1, Z["kimya"] + 0.3), 74, t=t, t0=Z["tek"])
    a = win(t, Z["kimya"] + 0.4, Z["fisyon"] + 0.3)
    label(img, "KİMYASAL TEPKİME", 540, 420, a, 70, WHITE, F_XB)
    cardl(img, ["Atom başına: birkaç eV"], 540, 1420, a, 56)
    return img


def sh_fisyon(v, t):
    """U-235 cekirdegi bolunur: iki parca ve notronlar, parlama."""
    S = Sahne()
    atom_ortami(S)
    src, dst, grp, isp, cap = split_data()
    t0 = Z["fisyon"] + 1.4
    sep = fade(t, t0, t0 + 3.2)
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
    Rr = ry(-0.3 + t * 0.06) @ rz(0.5)
    pts = (Q @ Rr.T) * s
    hot = fade(t, t0 - 0.8, t0) * (1 - 0.6 * sep)
    for i in range(len(pts)):
        if i == cap and t < t0 - 0.6:
            k = fade(t, Z["fisyon"] - 0.3, t0 - 0.6)
            p0 = np.array([26.0, 6.0, 6.0])
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
    atom.dust(S, t, n=140, R=50, a=0.16)
    cam = path(t, [(Z["fisyon"] - 0.6, (0, 4, 40), (0, 0, 0), 42), (t0, (3, 5, 34), (0, 0, 0), 42),
                   (Z["yani"], (0, 8, 52), (1, 0, 0), 46)], aperture=0.2)
    img = ciz(S, cam, t)
    a = win(t, Z["fisyon"] + 0.2, Z["yani"] + 0.3)
    label(img, "URANYUM-235 FİSYONU", 540, 420, a, 66, AMBER, F_XB)
    cardl(img, ["Ortalama ≈ 200.000.000 eV"], 540, 1420, fade(t, Z["fisyon"] + 2.2, Z["fisyon"] + 2.8) * a, 52, amber=True)
    ak = win(t, Z["fark"], Z["yani"] + 0.3)
    label(img, "FARK: ON MİLYONLARCA KAT", 540, 1560, ak, 52, WHITE, F_XB)
    return img


def sh_karar(v, t):
    """sonuc: pelet ve komur yeniden, damga."""
    S = Sahne()
    depo(S)
    cam = path(t, [(Z["yani"] - 0.6, (-0.45, 1.9, 1.7), (0.1, 0.5, -1.0), 44), (Z["son"] + 1, (-0.25, 1.75, 1.45), (0.1, 0.5, -1.1), 42)],
               near=0.01, aperture=0.1)
    img = ciz(S, cam, t)
    img = (img.astype(np.float32) * 0.72).astype(np.uint8)
    stamp(img, "KISMEN GERÇEK", 540, 450, fade(t, Z["yani"] + 0.1, Z["yani"] + 0.35), AMBER, 84,
          pop=0.25 * (1 - fade(t, Z["yani"] + 0.1, Z["yani"] + 0.45)))
    a1 = fade(t, Z["yani"] + 0.6, Z["yani"] + 1.1)
    label(img, "Tepkime başına", 540, 1180, a1, 46, WHITE, F_SB)
    cardl(img, ["on milyonlarca kat"], 540, 1265, a1, 58, amber=True)
    a2 = fade(t, Z["yani"] + 3.0, Z["yani"] + 3.5)
    label(img, "Aynı ağırlıkta yakıtta", 540, 1420, a2, 46, WHITE, F_SB)
    cardl(img, ["on binlerce kat"], 540, 1505, a2, 58)
    return img


SHOTS = [(-1.0, sh_pelet), (Z["doe"], sh_yigin), (Z["nereden"] + 1.9, sh_kimya), (Z["fisyon"] - 0.1, sh_fisyon),
         (Z["yani"] - 0.2, sh_karar)]


def frame(t):
    if t >= Z["son"] + 0.7:
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (6, 12, 30)
    else:
        img = shots(t, SHOTS, xf=0.6)
    tag(img, t)
    img = end_card(img, t, Z["son"], [
        "ABD Enerji Bakanlığı (DOE) · The Harnessed Atom:",
        "Nuclear Energy & Electricity",
        "DOE · 5 Reasons Nuclear Is a Good Neighbor",
        "DOE-STD-1128-98 · DOE-HDBK-1019/1-93",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_uranyum_komur_3d", frame, NFRAMES, NAME)
