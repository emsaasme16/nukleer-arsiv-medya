#!/usr/bin/env python3
"""Gercekci 3D Short: Mit mi, gercek mi? Reaktor kritik olunca tehlike mi? (reaktor-kritik-olunca-tehlike-mi.mp4),
1080x1920, 30 fps. 2026-11-28 gunluk Shorts gorevi.

Ses: $WORK/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn):
metinler/reaktor-kritik-olunca-tehlike-mi.words.json.
Kaynaklar:
- ABD NRC Glossary "Criticality": "During normal reactor operations, nuclear fuel sustains a fission chain reaction or
  criticality. A reactor achieves criticality (and is said to be critical) when each fission event releases a
  sufficient number of neutrons to sustain an ongoing series of reactions."
- ABD NRC Glossary "Chain reaction" (notronlar baska cekirdeklerce yutulur, daha cok notron cikar) ve "Reactivity"
  (supercriticality = power increase, subcriticality = power decrease).
- ABD DOE-HDBK-1019/2-93: critical = "the neutron population is neither increasing nor decreasing" (keff = 1);
  supercritical: artar, subcritical: azalir; Sekil 1 ornegi: keff = 1 iken 1000 notron sonraki kusagi baslatir.
Gorsel: santral dis planlari render_sogutma_kulesi_3d.py'nin mat sahnesi (parlamasiz); su altinda 17x17 yakit
demeti ../uzun_3d/modeller/yakit.py; atom olcegi U-235 cekirdekleri atom.py. Kritik / kritik ustu / kritik alti
zincirleri: her fisyon 3 notron cikarir; kritikte bunlardan yalniz biri yeni fisyon yapar (gerisi yutulur/kacar),
kritik ustunde ikisi, kritik altinda zincir soner.
Kullanim: WORK=/tmp/rk python3 render_reaktor_kritik_3d.py still 0 3 6 ... | render | olc
"""
import os
from dikey_kit import *
import render_sogutma_kulesi_3d as sk
from altyazi_kelime import Altyazi

NAME = "reaktor-kritik-olunca-tehlike-mi"
TOTAL = 51.69
NFRAMES = int(TOTAL * FPS)
BOLUM = 3
NOTXT = os.environ.get("NOTXT") == "1"

# kelime zamanlari (video saniyesi = transkript + 1,0)
# 2026-11-28: kapanis kullanicinin kulakla sectigi 2 numara ([calm], flow ZMWmxdkHR2yJopH7fBR2 / V6nmZzF1KrHlova21s8g)
#   ana sese eklendi (kapanis_ekle.py, yeni ses uretilmedi); ses 45,24 sn; devami/takip birlesik sesin zamanlarindan
Z = dict(tehlike=2.7, mit=3.66, kulaga=5.34, ama=7.08, kritiklik=10.0, normal=11.26, yakit=13.0, bu=15.98,
         zincir=18.32, doe=20.1, kritik_demek=22.62, notron=24.02, kusak1=26.44, sonraki=28.32, artarsa=30.7,
         ustu=33.48, guc_y=34.58, azalirsa=35.78, alti=36.94, guc_d=37.68, yani=38.78, tehlike2=40.48, denge=41.52,
         mit2=42.86, devami=43.54, takip=44.82)
END0 = 43.3

WORDS = os.path.join(HERE, "metinler", "reaktor-kritik-olunca-tehlike-mi.words.json")
VURGU = ["kritik", "tehlike", "mit", "gerçek", ("alarm", "normal"), "nötronlar", "zincirleme", ("artar", "azalır"),
         ("1.000 nötron", "1.000 nötron"), ("üstüdür", "yükselir", "altıdır", "düşer"), "denge", "mit", "kanalda", "takip"]
AY = Altyazi(WORDS, 1.0, VURGU, {("bin", "nötron"): "1.000 nötron"}, son=END0)


# ----------------------------------------------------------------- su alti reaktor ortami (bolum02.py'den)
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
    S.bloom = 0.25
    S.bloom_th = 2.0


def su_kabarcik(S, t, center, R, n=60, seed=2, size=0.004, speed=0.08):
    rng = np.random.default_rng(seed)
    b = rng.uniform(-1, 1, (n, 3)) * R
    sp = rng.uniform(0.5, 1.5, n)
    for i in range(n):
        p = b[i].copy()
        p[1] = (b[i][1] + t * speed * sp[i] + R) % (2 * R) - R
        p[0] += math.sin(t * 2 + i) * R * 0.02
        S.particle(tuple(np.asarray(center) + p), size * (0.6 + sp[i] * 0.5), (0.7, 0.9, 1.0, 0.35), kind=2)


def demet_sahne(t, cam, notron=0.0, y0=2.0):
    S = Sahne()
    ortam_su(S, dens=0.9, caus=0.45, cscale=14)
    S.shadow = False
    yakit.assembly(S, np.eye(4))
    for (x, z) in [(-0.217, 0), (0, -0.217), (-0.217, -0.217), (0.217, -0.217), (0.217, 0)]:
        yakit.assembly(S, TRS((x, 0, z)), lod=-1, grids=0)
    su_kabarcik(S, t, (0.05, 3.0, 0.2), 0.4, n=40, size=0.002, speed=0.05)
    if notron > 0:                       # demetler arasinda suzulen notron isiklari (atom alti, kucuk)
        rng = np.random.default_rng(5)
        for k in range(int(70 * notron)):
            p0 = rng.uniform([-0.3, y0 - 1.2, -0.3], [0.35, y0 + 1.2, 0.35])
            ph = (t * rng.uniform(0.3, 0.8) + rng.uniform()) % 1.0
            d = np.array(norm(rng.normal(0, 1, 3)))
            p = p0 + d * ph * 0.06
            S.particle(tuple(p), 0.0035, (0.45, 0.7, 1.0, 0.6 * math.sin(ph * math.pi)), kind=0, add=True)
    S.light((0.4, 3.4, 0.7), 0.9, (0.6, 0.9, 1.0), 3.0)
    return ciz(S, cam, t)


# ----------------------------------------------------------------- atom olcegi zincirleme tepkime
SP = 26.0            # cekirdekler arasi uzaklik (nukleon yaricapi biriminde)
GEN = 0.85           # kusaklar arasi sure (sn; gorsel tempo)
NS = 0.42            # cekirdek olcegi


def _zincir(mod, seed):
    """olaylar: (konum, fisyon zamani, [cocuk indeksleri], [kayip yonleri]). her fisyon 3 notron."""
    rng = np.random.default_rng(seed)
    ev = []

    def yeni(p, tf):
        ev.append([np.array(p, float), tf, [], []])
        return len(ev) - 1

    def yon():
        return np.array(norm(rng.normal(0, 1, 3)))

    if mod == "denge":                           # her fisyondan tam 1 yeni fisyon
        i = yeni((0, 0, 0), 0.3)
        for g in range(1, 9):
            p = ev[i][0] + np.array([SP * (0.8 + 0.3 * rng.uniform()), rng.uniform(-1, 1) * SP * 0.7,
                                     rng.uniform(-1, 1) * SP * 0.5])
            j = yeni(p, 0.3 + g * GEN)
            ev[i][2].append(j)
            ev[i][3] += [yon(), yon()]
            i = j
    elif mod == "ust":                           # her fisyondan 2 yeni fisyon
        kus = [yeni((0, 0, 0), 0.2)]
        for g in range(1, 4):
            yeni_kus = []
            for i in kus:
                for s in (-1, 1):
                    a = rng.uniform(0, 6.28)
                    off = np.array([SP * 0.9, s * SP * (1.3 / g ** 0.3) + rng.uniform(-4, 4),
                                    math.cos(a) * SP * 0.6])
                    j = yeni(ev[i][0] + off, 0.2 + g * GEN)
                    ev[i][2].append(j)
                    yeni_kus.append(j)
                ev[i][3] += [yon()]
            kus = yeni_kus
        for i in kus:
            ev[i][3] += [yon(), yon(), yon()]
    else:                                        # alt: 4 -> 2 -> 1 -> 0
        kus = [yeni((0, s * SP * 1.1, z * SP * 0.6), 0.2) for s, z in ((-1.5, 0.3), (-0.5, -0.4), (0.5, 0.5), (1.5, -0.2))]
        for g, keep in ((1, 2), (2, 1)):
            yeni_kus = []
            for n, i in enumerate(kus):
                if n % (len(kus) // keep) == 0 and len(yeni_kus) < keep:
                    p = ev[i][0] + np.array([SP * 0.9, rng.uniform(-6, 6), rng.uniform(-6, 6)])
                    j = yeni(p, 0.2 + g * GEN)
                    ev[i][2].append(j)
                    yeni_kus.append(j)
                    ev[i][3] += [yon(), yon()]
                else:
                    ev[i][3] += [yon(), yon(), yon()]
            kus = yeni_kus
        for i in kus:
            ev[i][3] += [yon(), yon(), yon()]
    # bolunmeyen komsu cekirdekler (zemin): olaylarin cevresine
    pts = np.array([e[0] for e in ev])
    lo, hi = pts.min(0) - SP, pts.max(0) + SP
    bos = []
    for k in range(60):
        p = rng.uniform(lo, hi)
        if np.min(np.linalg.norm(pts - p, axis=1)) > SP * 0.55 and \
                (not bos or np.min(np.linalg.norm(np.array(bos) - p, axis=1)) > SP * 0.55):
            bos.append(p)
    return ev, bos[:14]


ZN = {m: _zincir(m, s) for m, s in (("denge", 4), ("ust", 6), ("alt", 9))}
_FR = {}


def _frag():
    if not _FR:
        rb, cs = atom.get("RB93"), atom.get("CS140")
        _FR["rb"], _FR["cs"] = rb, cs
    return _FR["rb"], _FR["cs"]


def zincir_sahne(t, u, mod, cam_f):
    """u: zincir saati (sn). cam_f(ev, u) -> Cam."""
    ev, bos = ZN[mod]
    S = Sahne()
    atom_ortami(S)
    S.bg = (0.022, 0.04, 0.085)          # dis planlarla parlaklik farki azalsin (gecis sicramasi)
    S.amb = 1.3
    S.bloom = 0.6
    S.bloom_th = 1.2
    U = atom.get("U235")
    rb, cs = _frag()
    for p in bos:
        atom.draw(S, U.P, U.isp, tuple(p), NS, R=ry(0.3 * t + p[0]))
    for k, (p, tf, ch, lost) in enumerate(ev):
        if u < tf:
            atom.draw(S, U.P, U.isp, tuple(p), NS, R=ry(0.25 * t + k))
            continue
        v = u - tf
        a = 1.0 - fade(v, 1.0, 1.6)
        if a > 0.02:
            d = np.array(norm((math.sin(k * 2.1), math.cos(k * 1.3), 0.4)))
            g = sm(min(1.0, v / 0.6)) * 9 + v * 2.0
            atom.draw(S, rb.P, rb.isp, tuple(p + d * g), NS, R=ry(k), alpha=a)
            atom.draw(S, cs.P, cs.isp, tuple(p - d * g * 0.8), NS, R=rx(k), alpha=a)
        if v < 0.5:
            S.particle(tuple(p), 6 + 26 * v, (1.0, 0.8, 0.5, 0.55 * (1 - v / 0.5)), kind=0, add=True)
        # cocuga giden notronlar
        for j in ch:
            q, tj = ev[j][0], ev[j][1]
            if u < tj:
                f = clamp01(v / max(tj - tf, 1e-3))
                pos = p + (q - p) * f
                tr = [p + (q - p) * max(0.0, f - 0.03 * i) for i in range(1, 10)]
                atom.neutron(S, pos, 0.9, glow=1.4, trail=tr)
        # yutulan / kacan notronlar
        for dvec in lost:
            if v < 1.1:
                pos = p + dvec * v * SP * 1.1
                tr = [p + dvec * max(0.0, v - 0.03 * i) * SP * 1.1 for i in range(1, 8)]
                atom.neutron(S, pos, 0.9, glow=1.4 * (1 - fade(v, 0.7, 1.1)), trail=tr,
                             alpha=1.0 - fade(v, 0.7, 1.1))
    atom.dust(S, t, n=90, R=70, a=0.1)
    return ciz(S, cam_f(ev, u), t)


def zcam(ev, u, dist=120.0, yaw=0.0, pitch=0.12, fov=46, lead=0.6):
    """aktif fisyonlarin agirlik merkezini izleyen kamera."""
    w, acc = 0.0, np.zeros(3)
    for p, tf, ch, lost in ev:
        k = math.exp(-((u - tf - lead) ** 2) / 0.9)
        w += k
        acc += p * k
    c = acc / w if w > 1e-6 else ev[0][0]
    eye = c + np.array([math.sin(yaw) * dist, math.sin(pitch) * dist, math.cos(yaw) * dist])
    return Cam(tuple(eye), tuple(c), fov=fov, aperture=0.12)


# ----------------------------------------------------------------- planlar (her biri <= 3 sn)
def sh_a1(u, t):        # acilis: santral, alcak genis
    return sk.dis_sahne(t, sk.orbit(u, 0.95, 0.07, 520, 480, 30, 40, (0, 40, -60), 50), poz=0.8)


def sh_a2(u, t):        # koruma kabi yakin
    return sk.dis_sahne(t, sk.cam_at((70 - 20 * sm(u / 2.5), 14, 95), (0, 34, 0), 48), poz=0.85)


def sh_kulaga(u, t):    # kabin ustu, tele
    return sk.dis_sahne(t, sk.orbit(u, -0.4, 0.06, 260, 245, 70, 76, (0, 40, 0), 34), poz=0.9)


def sh_ic1(u, t):       # yakit demeti, alttan yukari bakis
    k = sm(u / 3.0)
    eye = np.array((0.95, 1.15, 0.3)) * (1 - k) + np.array((0.8, 1.3, 0.45)) * k
    return demet_sahne(t, Cam(tuple(eye), (0, 2.4, 0), fov=38, near=0.01, aperture=0.25))


def sh_demet(u, t):     # tek demet, asagi kayan kamera
    k = sm(u / 3.0)
    eye = np.array((0.55, 4.05, 0.7)) * (1 - k) + np.array((0.5, 3.55, 0.62)) * k
    tgt = np.array((0.0, 3.75, 0.0)) * (1 - k) + np.array((0.0, 3.4, 0.0)) * k
    return demet_sahne(t, Cam(tuple(eye), tuple(tgt), fov=40, near=0.01, aperture=0.25))


T_D1 = 12.6             # denge zinciri saati baslangici


def sh_z1(u, t):        # fisyon ve notronlar (yakin)
    return zincir_sahne(t, t - T_D1, "denge", lambda ev, uu: zcam(ev, uu, 95, 0.3 + 0.05 * u, 0.1))


def sh_z2(u, t):        # zincir, yan aci
    return zincir_sahne(t, t - T_D1, "denge", lambda ev, uu: zcam(ev, uu, 130, 1.1 + 0.05 * u, 0.25))


def sh_z3(u, t):        # zincir, genis
    return zincir_sahne(t, t - T_D1, "denge", lambda ev, uu: zcam(ev, uu, 175, -0.6 + 0.05 * u, 0.35, 50, 0.2))


def sh_ic3(u, t):       # DOE: demet, notron isiklari
    k = sm(u / 3.0)
    eye = np.array((0.3, 0.9, 0.35)) * (1 - k) + np.array((0.36, 1.0, 0.25)) * k
    return demet_sahne(t, Cam(tuple(eye), (0.05, 1.7, 0), fov=56, near=0.01, aperture=0.25), notron=1.0, y0=1.4)


def sh_ic4(u, t):
    k = sm(u / 3.0)
    eye = np.array((0.55, 3.6, 0.7)) * (1 - k) + np.array((0.5, 3.4, 0.6)) * k
    return demet_sahne(t, Cam(tuple(eye), (0, 3.3, 0), fov=40, near=0.01, aperture=0.25), notron=1.0, y0=3.3)


T_D2 = 23.7             # ikinci denge zinciri (kusak anlatimi)


def sh_k1(u, t):
    return zincir_sahne(t, t - T_D2, "denge", lambda ev, uu: zcam(ev, uu, 120, -0.2 + 0.05 * u, 0.15))


def sh_k2(u, t):
    return zincir_sahne(t, t - T_D2, "denge", lambda ev, uu: zcam(ev, uu, 110, 0.9 + 0.05 * u, -0.1))


def sh_k3(u, t):
    return zincir_sahne(t, t - T_D2, "denge", lambda ev, uu: zcam(ev, uu, 150, 0.2 + 0.05 * u, 0.3, 48, 0.3))


T_U = Z["artarsa"] - 0.2


def sh_u1(u, t):        # kritik ustu: cig gibi buyur
    return zincir_sahne(t, t - T_U, "ust", lambda ev, uu: zcam(ev, uu, 150 + 30 * (t - T_U), 0.4, 0.15, 50, 0.0))


def sh_u2(u, t):
    return zincir_sahne(t, t - T_U, "ust", lambda ev, uu: zcam(ev, uu, 230, 1.0 + 0.05 * u, 0.3, 50, -0.2))


T_A = Z["azalirsa"] - 0.3


def sh_a_1(u, t):       # kritik alti: zincir soner
    return zincir_sahne(t, t - T_A, "alt", lambda ev, uu: zcam(ev, uu, 170, -0.5 + 0.05 * u, 0.2, 52, -0.3))


def sh_a_2(u, t):
    return zincir_sahne(t, t - T_A, "alt", lambda ev, uu: zcam(ev, uu, 150, 0.6 + 0.05 * u, 0.0, 52, -0.4))


def sh_s1(u, t):        # santral genis, kule ve bulut
    return sk.dis_sahne(t, sk.orbit(u, 0.55, 0.06, 760, 720, 60, 70, (-30, 120, -150), 50), poz=0.8)


def sh_s2(u, t):        # kabin yakini, alcak
    return sk.dis_sahne(t, sk.cam_at((-60 + 15 * sm(u / 2.5), 6, 110), (0, 30, 0), 52), poz=0.85)


def sh_son1(u, t):
    return sk.dis_sahne(t, sk.orbit(u, 0.4, 0.08, 800, 760, 120, 130, (-40, 160, -230), 46), poz=0.8)


def sh_son2(u, t):
    return sk.dis_sahne(t, sk.orbit(u, 1.1, 0.06, 700, 680, 60, 70, (-40, 150, -230), 48), poz=0.8)


def sh_son3(u, t):
    return sk.dis_sahne(t, sk.orbit(u, -0.2, 0.06, 620, 600, 180, 190, (-40, 170, -230), 44), poz=0.8)


SHOTS = [(-1.0, sh_a1), (2.55, sh_a2), (Z["kulaga"] - 0.1, sh_kulaga), (Z["ama"] - 0.1, sh_ic1),
         (Z["kritiklik"] - 0.1, sh_demet), (T_D1, sh_z1), (Z["bu"] - 0.1, sh_z2), (Z["zincir"] - 0.2, sh_z3),
         (Z["doe"] - 0.1, sh_ic3), (Z["kritik_demek"] - 0.1, sh_ic4), (Z["notron"] - 0.1, sh_k1),
         (Z["kusak1"] - 0.1, sh_k2), (Z["sonraki"] - 0.1, sh_k3), (T_U, sh_u1), (Z["ustu"] - 0.3, sh_u2),
         (T_A, sh_a_1), (Z["guc_d"] - 0.4, sh_a_2), (Z["yani"] - 0.1, sh_s1), (Z["tehlike2"] - 0.1, sh_s2),
         (END0, sh_son1), (46.63, sh_son2), (49.23, sh_son3)]


# ----------------------------------------------------------------- ekran yazilari (ust bolge, y 360-720)
def yazilar(img, t):
    a = 1.0 - fade(t, Z["mit"] - 0.3, Z["mit"])
    lines(img, [("REAKTÖR KRİTİK OLDU:", WHITE), ("TEHLİKE Mİ?", AMBER)], 430, a, 88)
    lines(img, [("MİT Mİ,", WHITE), ("GERÇEK Mİ?", AMBER)], 430, win(t, Z["mit"], Z["kulaga"] - 0.1, 0.25), 100)
    label(img, "KULAĞA ALARM GİBİ GELİYOR", 540, 470, win(t, Z["kulaga"] + 0.1, Z["ama"] - 0.15, 0.25), 60, WHITE, F_XB)
    lines(img, [("ABD NÜKLEER DÜZENLEME", CYAN), ("KURULU (NRC):", CYAN)], 380, win(t, Z["ama"], Z["yakit"] - 0.15, 0.3), 50)
    cardl(img, ["Kritiklik =", "normal çalışma hâli"], 540, 560, win(t, Z["kritiklik"], Z["yakit"] - 0.15, 0.3), 58,
          amber=True)
    lines(img, [("HER BÖLÜNME", WHITE), ("YENİ NÖTRONLAR FIRLATIR", CYAN)], 420, win(t, Z["yakit"] + 0.1, Z["bu"] - 0.1, 0.25), 72)
    lines(img, [("ZİNCİRLEME", AMBER), ("TEPKİME", WHITE)], 420, win(t, Z["zincir"] - 0.1, Z["doe"] - 0.15, 0.25), 96)
    label(img, "ABD ENERJİ BAKANLIĞI (DOE):", 540, 380, win(t, Z["doe"], Z["kusak1"] - 0.15, 0.3), 46, CYAN, F_B)
    cardl(img, ["Kritik:", "nötron sayısı", "ne artar ne azalır"], 540, 560, win(t, Z["kritik_demek"] + 0.2,
          Z["kusak1"] - 0.15, 0.3), 54)
    lines(img, [("1. KUŞAK", WHITE)], 400, win(t, Z["kusak1"], Z["artarsa"] - 0.15, 0.25), 70)
    cardl(img, ["1.000 nötron"], 540, 520, win(t, Z["kusak1"] + 0.2, Z["artarsa"] - 0.15, 0.25), 80, amber=True)
    lines(img, [("2. KUŞAK", WHITE)], 640, win(t, Z["sonraki"], Z["artarsa"] - 0.15, 0.25), 70)
    cardl(img, ["1.000 nötron"], 540, 760, win(t, Z["sonraki"] + 0.2, Z["artarsa"] - 0.15, 0.25), 80, amber=True)
    lines(img, [("KRİTİK ÜSTÜ", AMBER)], 420, win(t, Z["artarsa"] + 0.3, Z["azalirsa"] - 0.15, 0.25), 100)
    cardl(img, ["Nötron artar · güç yükselir"], 540, 560, win(t, Z["ustu"] + 0.2, Z["azalirsa"] - 0.15, 0.25), 52)
    lines(img, [("KRİTİK ALTI", CYAN)], 420, win(t, Z["azalirsa"] + 0.2, Z["yani"] - 0.15, 0.25), 100)
    cardl(img, ["Nötron azalır · güç düşer"], 540, 560, win(t, Z["alti"], Z["yani"] - 0.15, 0.25), 52)
    lines(img, [("KRİTİK =", WHITE), ("TEHLİKE DEĞİL", AMBER)], 420, win(t, Z["yani"] + 0.2, Z["denge"] - 0.1, 0.25), 88)
    lines(img, [("KRİTİK =", WHITE), ("DENGE", CYAN)], 420, win(t, Z["denge"], END0, 0.25), 104)
    stamp(img, "MİT", 540, 760, fade(t, Z["mit2"] - 0.1, Z["mit2"] + 0.15) * (1 - fade(t, END0, END0 + 0.3)), RED, 130,
          pop=0.3 * (1 - fade(t, Z["mit2"] - 0.1, Z["mit2"] + 0.3)))


def kapanis(img, t):
    ec = clamp01((t - END0) / 4.0)          # yavas karartma (0,5 sn'de parlaklik sicramasi < %20)
    if ec <= 0:
        return img
    dark = (img.astype(np.float32) * 0.50 + np.array([6, 12, 30], np.float32) * 0.50).astype(np.uint8)
    img = blend(img, cv2.GaussianBlur(dark, (0, 0), 3), ec)
    if NOTXT:
        return img
    label(img, "KAYNAKLAR", 540, 470, fade(t, END0 + 0.1, END0 + 0.6), 50, CYAN, F_B)
    rows = ["ABD Nükleer Düzenleme Kurulu (NRC),", "Glossary: Criticality · Chain reaction",
            "ABD Enerji Bakanlığı (DOE),", "DOE-HDBK-1019/2-93 Reactor Theory"]
    for i, r in enumerate(rows):
        label(img, r, 540, 560 + i * 56, fade(t, END0 + 0.2 + 0.1 * i, END0 + 0.8 + 0.1 * i), 36,
              WHITE if i % 2 == 0 else MUTED, F_M, 990)
    k = fade(t, Z["takip"] - 0.3, Z["takip"] + 0.1)
    pulse = 1.0 + 0.04 * math.sin(max(0.0, t - Z["takip"]) * 4.0)
    blit(img, pill("TAKİP ET", F_XB, 120, NAVYTXT, AMBER, padx=70, pady=30, fill=AMBER, fill_a=1.0), 540, 1040,
         op=k, scale=pulse * (1.0 + 0.25 * (1 - k)))
    label(img, "DEVAMI KANALDA · BÖLÜM %d" % BOLUM, 540, 1660, fade(t, Z["devami"], Z["devami"] + 0.5), 52, AMBER, F_B, 900)
    return img


# ----------------------------------------------------------------- parlaklik esitleme (PARLAMA YOK kurali)
# Sahne gecislerinde (gunduz dis plan <-> koyu atom olcegi) ortalama parlaklik 0,5 sn'de %20'den fazla sicramasin:
# ham olcumden (NORM=0 ile olc) hesaplanan yumusak hedef egrisine her kare kazanc (<1) ya da gama (>1) ile cekilir.
# Hedef: log parlaklikta ileri/geri kirpma (0,5 sn'de en cok %14) ortalamasi; bkz. hedef_hesapla().
NORM = os.environ.get("NORM", "1") == "1"
HEDEF = [111.2, 111.1, 111.0, 112.2, 127.9, 135.3, 135.9, 136.6, 138.0, 139.1, 132.0, 122.9, 115.1, 107.8, 94.6, 89.1, 84.4, 80.2, 80.9, 76.6, 67.2, 65.9, 72.6, 79.2, 76.2, 66.9, 58.7, 54.5, 54.2, 51.8, 54.7, 53.3, 51.2, 52.8, 51.5, 57.0, 51.7, 54.8, 58.5, 61.9, 70.6, 75.6, 81.1, 87.4, 89.4, 78.5, 72.8, 68.9, 60.5, 56.9, 53.8, 50.9, 53.8, 50.5, 52.3, 51.4, 51.4, 51.8, 50.8, 51.4, 50.9, 50.2, 51.3, 51.4, 52.7, 52.5, 51.3, 53.7, 50.8, 50.0, 49.0, 51.9, 55.9, 57.5, 61.7, 64.5, 68.4, 78.0, 88.9, 95.0, 101.5, 104.4, 111.5, 112.0, 112.5, 113.0, 113.2, 123.6, 111.7, 98.8, 86.8, 76.1, 70.7, 70.3, 70.4, 70.4, 70.4, 70.3, 75.7, 75.8, 75.8, 76.0]   # 2026-11-28 ham olcum (NORM=0 olc)


def hedef_hesapla(ham, d=math.log(1.14)):
    L = [math.log(max(x, 1.0)) for x in ham]
    f = [L[0]]
    for x in L[1:]:
        f.append(min(max(x, f[-1] - d), f[-1] + d))
    b = [L[-1]]
    for x in reversed(L[:-1]):
        b.append(min(max(x, b[-1] - d), b[-1] + d))
    b.reverse()
    return [round(math.exp((u + v) / 2), 1) for u, v in zip(f, b)]


def esitle(img, t):
    if HEDEF is None or not NORM:
        return img
    x = t / 0.5
    i = min(len(HEDEF) - 2, max(0, int(x)))
    f = clamp01(x - i)
    T = HEDEF[i] * (1 - f) + HEDEF[i + 1] * f
    sm_ = img[::8, ::8].astype(np.float32)
    lum = 0.2126 * sm_[..., 0] + 0.7152 * sm_[..., 1] + 0.0722 * sm_[..., 2]
    m = float(lum.mean())
    if abs(T - m) / max(m, 1.0) < 0.01:
        return img
    if T < m:
        return np.clip(img.astype(np.float32) * (T / m), 0, 255).astype(np.uint8)
    lo, hi = 0.25, 1.0                     # gama < 1 karanligi kaldirir, beyazi patlatmaz
    for _ in range(12):
        g = (lo + hi) / 2
        if float((255.0 * (lum / 255.0) ** g).mean()) > T:
            lo = g
        else:
            hi = g
    lut = (255.0 * (np.arange(256) / 255.0) ** ((lo + hi) / 2)).clip(0, 255).astype(np.uint8)
    return lut[img]


def frame(t, yazi=None):
    yazi = (not NOTXT) if yazi is None else yazi
    img = esitle(shots(t, SHOTS, xf=0.3), t)
    if not yazi:
        return kapanis(img, t)
    yazilar(img, t)
    img = kapanis(img, t)
    tag(img, t)
    AY.ciz(img, t)
    return img


def olc():
    """parlama olcumu: yazisiz karelerde >=245 piksel orani ve 0,5 sn arayla ortalama parlaklik sicramasi."""
    ts = [x * 0.5 for x in range(int(TOTAL / 0.5))]
    res, prev = [], None
    for t in ts:
        im = frame(t, yazi=False)
        lum = (0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2])
        oran = float((lum >= 245).mean())
        ort = float(lum.mean())
        sic = abs(ort - prev) / max(prev, 1.0) if prev is not None else 0.0
        prev = ort
        res.append((t, oran, ort, sic))
        print("%5.1f  >=245: %.3f%%  ort %.1f  sicrama %.1f%%" % (t, oran * 100, ort, sic * 100), flush=True)
    json.dump(res, open(os.path.join(os.environ.get("WORK", "/tmp/rk"), "parlama%s.json" % ("" if NORM else "_ham")), "w"))
    if not NORM:
        print("HEDEF =", hedef_hesapla([r[2] for r in res]))
    print("EN KOTU: oran %.3f%%, sicrama %.1f%%" % (max(r[1] for r in res) * 100, max(r[3] for r in res) * 100))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "olc":
        olc()
    else:
        cli("render_reaktor_kritik_3d", frame, NFRAMES, NAME)
