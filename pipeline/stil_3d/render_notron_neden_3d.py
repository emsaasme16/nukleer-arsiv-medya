#!/usr/bin/env python3
"""Gercekci 3D Short: 60 saniyede: Cekirdegi neden notron boler? (cekirdegi-neden-notron-boler.mp4), 1080x1920, 30 fps.

Ses: /tmp/notron/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn).
Kaynaklar: DOE-HDBK-1019/1-93 (proton artı yuklu, notron yuksuz; elektrostatik kuvvet: "Strong repulsive force between
like charged particles (protons)", menzil "Relatively long"; "Because of its lack of charge, the neutron is difficult to
stop and has a high penetrating power."; fisil U-235 her enerjide notronla bolunur), NRC sozlugu "Neutron" ("An uncharged
elementary particle"), DOE "DOE Explains...Nuclear Fission" (fisyon, elementler notronla bombardiman edilerek kesfedildi).
Atom alti olcek: gercek nukleon sayili U-235 (92 p + 143 n), ../uzun_3d/modeller/atom.py.
Kullanim: WORK=/tmp/notron python3 render_notron_neden_3d.py still 2 10 ... | render
"""
from dikey_kit import *

NAME = "cekirdegi-neden-notron-boler"
TOTAL = 51.22
NFRAMES = int(TOTAL * FPS)
BOLUM = 2

Z = dict(soru=1.1, cekirdek=5.96, protonlar=10.2, notronun=11.96, ayni=14.8, disaridan=16.7, karsi=20.0,
         notron=23.86, abd=25.9, alinti=29.1, iceri=32.1, ulasan=34.3, uranyum=36.7, bolunme=39.9, yani=41.58,
         hic=44.4, son=46.2)

S_N = 0.62          # nukleon olcegi


def nuc_pts(t, spin=0.05):
    u = atom.get("U235")
    Rr = ry(0.2 + t * spin) @ rx(0.35)
    return (u.P @ Rr.T) * S_N, u.isp


def draw_nuc(S, t, hp=0.0, hn=0.0, alpha=1.0):
    P, isp = nuc_pts(t)
    for i in range(len(P)):
        if isp[i]:
            m = atom.PROTON.but(emi=(0.1 + 1.4 * hp, 0.025 + 0.45 * hp, 0.01 + 0.12 * hp))
        else:
            m = atom.NEUTRON.but(emi=(0.02 + 0.35 * hn, 0.03 + 0.55 * hn, 0.05 + 1.1 * hn))
        if alpha < 1:
            m = m.but(alpha=alpha)
        S.add(SPH, TRS(tuple(P[i]), s=S_N), m)


R_NUC = np.linalg.norm(atom.get("U235").P, axis=1).max() * S_N


def _yorunge():
    """itici merkez (cekirdek) etrafinda proton yolu: 2B sayisal tumlev, xy duzlemi."""
    p = np.array([-46.0, 5.5])
    v = np.array([9.0, 0.0])
    k = 420.0
    dt = 0.004
    out = [p.copy()]
    for _ in range(6000):
        r = np.linalg.norm(p)
        a = k * p / r ** 3
        v = v + a * dt
        p = p + v * dt
        out.append(p.copy())
        if np.linalg.norm(p) > 60 and p[0] > 0:
            break
    return np.array(out)


YOL = _yorunge()


def proton_at(k):
    i = min(len(YOL) - 1, max(0, int(k * (len(YOL) - 1))))
    return np.array([-YOL[i, 1], YOL[i, 0], 0.0]), i


def proton_trail(i, n=26, step=12):
    return [np.array([-YOL[max(0, i - j * step), 1], YOL[max(0, i - j * step), 0], 0.0]) for j in range(1, n)]


def sh_soru(v, t):
    S = Sahne()
    atom_ortami(S)
    draw_nuc(S, t)
    k = fade(t, 0.3, 5.6)
    pp, i = proton_at(k * 0.75)
    atom.proton(S, pp, S_N, glow=1.2, trail=proton_trail(i))
    q = np.array([4.0, -46.0, 0.0]) * (1 - k) + np.array([1.0, -R_NUC - 1.0, 0]) * k
    atom.neutron(S, q, S_N, glow=1.2, trail=[q + np.array([0.07, -1.2, 0]) * j for j in range(1, 20)])
    atom.dust(S, t, n=120, R=60, a=0.14)
    cam = Cam((0, 2, 104 - 6 * sm(t / 5)), (0, -6, 0), fov=44, aperture=0.12)
    img = ciz(S, cam, t)
    lines(img, [("ÇEKİRDEĞİ NEDEN", WHITE), ("PROTON DEĞİL,", WHITE), ("NÖTRON BÖLER?", AMBER)], 400,
          win(t, 0.2, Z["cekirdek"] - 0.1), 82, t=t, t0=0.2)
    return img


def sh_parca(v, t):
    S = Sahne()
    atom_ortami(S)
    hp = win(t, Z["protonlar"] - 0.8, Z["notronun"] + 0.2, 0.4)
    hn = win(t, Z["notronun"], Z["ayni"] + 0.3, 0.4)
    draw_nuc(S, t, hp, hn)
    atom.dust(S, t, n=120, R=50, a=0.14)
    ang = 0.2 + t * 0.06
    d = 34 - 4 * sm((t - Z["cekirdek"]) / 8)
    cam = Cam((math.sin(ang) * d, 5, math.cos(ang) * d), (0, 0, 0), fov=40, aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("ÇEKİRDEKTE İKİ", WHITE), ("TÜR PARÇACIK", WHITE)], 400, win(t, Z["cekirdek"] + 0.1, Z["protonlar"] - 0.8), 80,
          t=t, t0=Z["cekirdek"])
    cardl(img, ["PROTON: + yük"], 540, 440, win(t, Z["protonlar"] - 0.8, Z["ayni"] + 0.3), 64, amber=True)
    cardl(img, ["NÖTRON: yük yok"], 540, 1500, win(t, Z["notronun"], Z["ayni"] + 0.3), 64)
    label(img, "92 proton · 143 nötron · U-235", 540, 1640, win(t, Z["cekirdek"] + 1.0, Z["ayni"] + 0.3), 40, (205, 214, 228), F_SB)
    return img


def sh_proton(v, t):
    S = Sahne()
    atom_ortami(S)
    draw_nuc(S, t, hp=0.25 * win(t, Z["karsi"], Z["notron"]))
    k = fade(t, Z["disaridan"] - 0.4, Z["notron"] + 2.5)
    pp, i = proton_at(k)
    atom.proton(S, pp, S_N, glow=1.4, trail=proton_trail(i, 40, 14))
    near = math.exp(-((np.linalg.norm(pp) - 14) / 8) ** 2) if k > 0 else 0
    if near > 0.05:
        S.particle((pp * 0.5).tolist(), 10, (1.0, 0.5, 0.3, 0.18 * near), kind=0, add=True)
    atom.dust(S, t, n=120, R=60, a=0.14)
    cam = Cam((0, 2, 108), (0, -4, 0), fov=44, aperture=0.1)
    img = ciz(S, cam, t)
    lines(img, [("AYNI YÜKLER", WHITE), ("BİRBİRİNİ İTER", AMBER)], 400, win(t, Z["ayni"] - 0.1, Z["notron"]), 84, t=t, t0=Z["ayni"])
    c = proj(cam, pp)
    label(img, "+", c[0], c[1] - 70, win(t, Z["disaridan"], Z["notron"]) * float(k > 0.02), 64, AMBER, F_XB)
    label(img, "PROTON", c[0], c[1] + 70, win(t, Z["disaridan"], Z["notron"]) * float(k > 0.02), 40, AMBER, F_B)
    cardl(img, ["Çekirdeğin itmesiyle", "yolundan sapar"], 540, 1500, win(t, Z["karsi"], Z["notron"]), 54)
    return img


def sh_notron(v, t):
    S = Sahne()
    atom_ortami(S)
    draw_nuc(S, t)
    k = fade(t, Z["notron"] + 0.2, Z["iceri"] + 1.0)
    p0 = np.array([0.6, -48.0, 0.0])
    p1 = np.array([0.6, -R_NUC - 0.6, 0.0])
    q = p0 * (1 - k) + p1 * k
    atom.neutron(S, q, S_N, glow=1.4, trail=[q + (p0 - p1) / 48 * 0.9 * j for j in range(1, 26)] if k < 1 else None)
    atom.dust(S, t, n=120, R=60, a=0.14)
    cam = Cam((0, 2, 108), (0, -4, 0), fov=44, aperture=0.1)
    img = ciz(S, cam, t)
    lines(img, [("NÖTRON BU İTMEYE", WHITE), ("TAKILMAZ", CYAN)], 400, win(t, Z["notron"] - 0.1, Z["abd"] + 0.3), 82, t=t, t0=Z["notron"])
    label(img, "ABD ENERJİ BAKANLIĞI EL KİTABI:", 540, 380, win(t, Z["abd"] + 0.3, Z["ulasan"]), 42, CYAN, F_B)
    cardl(img, ["“Yükü olmadığı için", "nötronu durdurmak zordur,", "içeri işleme gücü yüksektir.”"], 540, 520,
          win(t, Z["alinti"] - 0.4, Z["ulasan"]), 46)
    c = proj(cam, q)
    label(img, "NÖTRON · 0", c[0], c[1] + 70, win(t, Z["notron"] + 0.2, Z["ulasan"]), 40, CYAN, F_B)
    return img


SPLIT = None


def split_pts(t, t0):
    global SPLIT
    if SPLIT is None:
        SPLIT = atom.compound_split()
    src, dst, grp, isp, cap = SPLIT
    sep = fade(t, t0, t0 + 3.0)
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
    return Q, grp, isp, cap, sep


def sh_bolunme(v, t):
    S = Sahne()
    atom_ortami(S)
    t0 = Z["bolunme"] - 0.3
    Q, grp, isp, cap, sep = split_pts(t, t0)
    Rr = ry(0.2 + t * 0.05) @ rz(0.6)
    pts = (Q @ Rr.T) * S_N
    hot = fade(t, Z["uranyum"], t0) * (1 - 0.5 * sep)
    wob = 0.05 * math.sin(t * 8) * fade(t, Z["ulasan"] + 0.8, t0) * (1 - sep)
    pts = pts * (1 + np.array([wob, -wob * 0.6, -wob * 0.6]))
    for i in range(len(pts)):
        if i == cap and t < Z["ulasan"] + 0.6:
            continue
        if grp[i] == 2 and sep > 0:
            atom.neutron(S, pts[i], S_N, glow=1.3)
            continue
        m = atom.PROTON if isp[i] else atom.NEUTRON
        if hot > 0:
            e = hot * (0.6 + 0.3 * math.sin(t * 9 + i))
            m = m.but(emi=tuple(x + y for x, y in zip(m.emi, (0.6 * e, 0.26 * e, 0.06 * e))))
        S.add(SPH, TRS(tuple(pts[i]), s=S_N), m)
    if t < Z["ulasan"] + 0.6:
        k = fade(t, Z["ulasan"] - 0.4, Z["ulasan"] + 0.6)
        tgt = pts[cap]
        q = tgt + np.array([-12.0, 2.0, 0]) * (1 - k)
        atom.neutron(S, q, S_N, glow=1.4)
    if sep > 0:
        S.particle((0, 0, 0), 34 * sep + 6, (1.0, 0.8, 0.5, min(1.0, 2.6 * sep * (1 - sep))), add=True)
    atom.dust(S, t, n=140, R=50, a=0.16)
    cam = path(t, [(Z["ulasan"] - 0.6, (0, 3, 44), (0, 0, 0), 40), (t0, (2, 4, 38), (0, 0, 0), 40),
                   (Z["yani"], (0, 6, 52), (1, 0, 0), 44)], aperture=0.2)
    img = ciz(S, cam, t)
    lines(img, [("NÖTRON YAKALANIR", WHITE)], 400, win(t, Z["ulasan"] + 0.1, Z["uranyum"] + 0.2), 78, t=t, t0=Z["ulasan"])
    label(img, "U-235 + NÖTRON", 540, 420, win(t, Z["uranyum"] + 0.2, Z["yani"]), 72, AMBER, F_XB)
    label(img, "BÖLÜNME BAŞLAR", 540, 1560, win(t, t0 + 0.2, Z["yani"]), 70, WHITE, F_XB)
    return img


def sh_son(v, t):
    S = Sahne()
    atom_ortami(S)
    p = np.array([math.sin(t * 0.4) * 2, 0.0, 0.0])
    atom.neutron(S, p, 2.2, glow=1.5)
    atom.dust(S, t, n=160, R=40, a=0.18)
    cam = Cam((0, 2, 26 - 2 * sm((t - Z["yani"]) / 5)), (0, -1.5, 0), fov=40, aperture=0.25)
    img = ciz(S, cam, t)
    lines(img, [("NÖTRONUN GÜCÜ", WHITE)], 400, fade(t, Z["yani"] + 0.1, Z["yani"] + 0.6), 82, t=t, t0=Z["yani"])
    cardl(img, ["Yükü değil:", "hiç yükü olmaması"], 540, 1480, fade(t, Z["hic"] - 0.6, Z["hic"]), 60, amber=True)
    return img


SHOTS = [(-1.0, sh_soru), (Z["cekirdek"] - 0.2, sh_parca), (Z["ayni"] - 0.2, sh_proton), (Z["notron"] - 0.2, sh_notron),
         (Z["ulasan"] - 0.2, sh_bolunme), (Z["yani"] - 0.2, sh_son)]


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
        "ABD NRC sözlüğü · Neutron",
        "DOE · DOE Explains...Nuclear Fission",
    ], BOLUM)
    return img


if __name__ == "__main__":
    cli("render_notron_neden_3d", frame, NFRAMES, NAME)
