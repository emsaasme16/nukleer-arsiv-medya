#!/usr/bin/env python3
"""Gercekci 3D Short: 60 saniyede: Reaktoru yoneten gec notronlar (reaktoru-yoneten-gec-notronlar.mp4),
1080x1920, 30 fps. 2026-11-28 gunluk Shorts gorevi (Bolum 3: zincirleme tepkime ve kritiklik).

Ses: $WORK/mix.wav (../uzun_3d/sesler.py, TAIL=4.8). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn):
metinler/reaktoru-yoneten-gec-notronlar.words.json (kapanis kelimeleri eklenen kapanis kaydindan, sessizlik sinirlari).
Kaynak: ABD DOE, DOE-HDBK-1019/1-93 Reactor Theory (Neutron Characteristics), "Prompt and Delayed Neutrons" s. 29-32:
- "The great majority (over 99%) of the neutrons produced in fission are released within about 10-13 seconds of the
  actual fission event. These are called prompt neutrons."
- "The delayed neutrons are emitted immediately following the first beta decay of a fission fragment known as a
  delayed neutron precursor."  Yari omurler: "from fractions of a second to almost a minute" (Tablo 3: 0,23-55,7 s).
- uranium-235 delayed neutron fraction 0.0065 (1.000 notronda 6,5).
- Ornek: prompt generation time 5 x 10-5 s (= 1/20.000 s) -> delayed ile 0.0813 s (hesap: ~1.626 kat).
- "control would not be possible without the dependence upon delayed neutrons to slow down the rate of the reaction."
Gorsel: santral dis planlari render_sogutma_kulesi_3d.py'nin mat sahnesi; su alti yakit demeti ve atom olcegi
zincirleri render_reaktor_kritik_3d.py'den; gecikmis notron: parcanin beta bozunmasi (elektron), sonra notron.
Kullanim: WORK=/tmp/gn python3 render_gec_notron_3d.py still 0 3 6 ... | render | olc
"""
import os
from dikey_kit import *
import render_sogutma_kulesi_3d as sk
import render_reaktor_kritik_3d as rk
from altyazi_kelime import Altyazi

NAME = "reaktoru-yoneten-gec-notronlar"
TOTAL = 57.83
NFRAMES = int(TOTAL * FPS)
BOLUM = 3
NOTXT = os.environ.get("NOTXT") == "1"
O = 1.0                                   # transkript -> video ofseti

_W = json.load(open(os.path.join(HERE, "metinler", NAME + ".words.json")))["words"]


def zw(i):
    return _W[i]["start"] + O


# kelime zamanlari (video saniyesi)
Z = dict(reaktoru=3.22 + O, bir=5.76 + O, yuzde=8.48 + O, saniyenin=10.42 + O, bunlar=13.26 + O, birkac=15.44 + O,
         once=17.42 + O, notron=19.46 + O, bu_bekleme=21.8 + O, kesrinden=22.6 + O, dakika=24.0 + O, neden=26.56 + O,
         abd=28.02 + O, yalniz=31.44 + O, kusak=33.18 + O, yirmi=34.36 + O, geciken=35.98 + O, bin6=38.2 + O,
         gecikme=39.92 + O, guc=41.36 + O, kontrol=42.8 + O, yani=44.9 + O, en_gec=47.32 + O, devami=49.36 + O,
         takip=50.66 + O)
END0 = Z["devami"] - 0.15

WORDS = os.path.join(HERE, "metinler", NAME + ".words.json")
VURGU = ["6,5'i", "yöneten", "%99'undan", "anlık", "bekler", "bozunur", ("kesrinden", "dakikaya"), "önemli",
         ("1/20.000'i",), "1.600", ("sıçrardı", "edilemezdi"), ("dizginleyen", "geç"), "kanalda", "takip"]
AY = Altyazi(WORDS, O, VURGU, {("bin", "nötrondan"): "1.000 nötrondan", ("altı", "buçuğu"): "6,5'i",
                               ("bozulur,",): "bozunur,", ("yirmi", "binde", "biri"): "1/20.000'i",
                               ("bin", "altı", "yüz"): "1.600"}, son=END0)


# ----------------------------------------------------------------- atom olcegi: gecikmis notron (parcanin bozunmasi)
def gecikme_sahne(t, u, cam, t_beta=1.2, t_n=2.4, glow0=0.0):
    """u: olay saati. Parca cekirdek (Rb-93 paketi, genel 'bolunme parcasi') ortada; t_beta'da elektron (beta) firlar,
    t_n'de notron yavasca cikar. Etrafta bolunmeyen U-235 cekirdekleri ve derinlik tozu."""
    S = Sahne()
    atom_ortami(S)
    S.bg = (0.022, 0.04, 0.085)
    S.amb = 1.3
    S.bloom = 0.6
    S.bloom_th = 1.2
    U = atom.get("U235")
    rb, cs = rk._frag()
    for k, p in enumerate([(-70, 30, -60), (80, -40, -90), (-40, -70, -130), (95, 60, -50), (10, 85, -160)]):
        atom.draw(S, U.P, U.isp, p, rk.NS, R=ry(0.3 * t + k))
    # parca: bozunmadan once hafif amber kenar isigi (uyarilmis)
    bek = clamp01(u / max(t_beta, 1e-3))
    pul = 0.15 + 0.1 * math.sin(u * 5.0) * (u < t_n)
    atom.draw(S, rb.P, rb.isp, (0, 0, 0), 0.55, R=ry(0.2 * t) @ rx(0.1 * t), glow=glow0 + pul * bek)
    # beta: elektron (kucuk, beyaz-amber) hizla uzaklasir
    if u >= t_beta:
        v = u - t_beta
        d = np.array(norm((-0.6, 0.55, 0.3)))
        pos = d * (8 + v * 60)
        a = 1.0 - fade(v, 0.8, 1.3)
        if a > 0.02:
            S.add(SPH, TRS(tuple(pos), s=0.45), Mat((1.0, 0.85, 0.5), 0.3, 0.0, emi=(2.2, 1.5, 0.6)).but(alpha=a))
            for i in range(1, 10):
                q = d * (8 + max(0.0, v - 0.025 * i) * 60)
                S.particle(tuple(q), 0.9 * (1 - i / 10), (1.0, 0.8, 0.45, 0.3 * a * (1 - i / 10)), kind=0, add=True)
        if v < 0.35:
            S.particle((0, 0, 0), 10 + 30 * v, (1.0, 0.8, 0.5, 0.35 * (1 - v / 0.35)), kind=0, add=True)
    # notron: bozunmadan sonra yavasca cikar
    if u >= t_n:
        v = u - t_n
        d = np.array(norm((0.75, -0.25, 0.35)))
        pos = d * (7 + 26 * sm(min(1.0, v / 1.4)) + v * 6)
        tr = [d * (7 + 26 * sm(min(1.0, max(0.0, v - 0.04 * i) / 1.4)) + max(0.0, v - 0.04 * i) * 6) for i in range(1, 9)]
        atom.neutron(S, pos, 0.9, glow=1.6, trail=tr)
    atom.dust(S, t, n=90, R=70, a=0.1)
    return ciz(S, cam, t)


def gcam(u, d0, d1, yaw0, dyaw, pitch=0.12, fov=44, tgt=(0, 0, 0), dur=2.6):
    k = sm(u / dur) * 0.6 + (u / dur) * 0.4
    d = d0 + (d1 - d0) * k
    yaw = yaw0 + dyaw * k
    c = np.array(tgt, float)
    eye = c + np.array([math.sin(yaw) * d, math.sin(pitch) * d, math.cos(yaw) * d])
    return Cam(tuple(eye), tuple(c), fov=fov, aperture=0.12)


# ----------------------------------------------------------------- planlar (her biri <= 3 sn)
T_P = -0.6               # acilis zinciri: ilk fisyon hemen


def sh_k1(u, t):         # acilis: fisyon ve anlik notronlar, yakin
    return rk.zincir_sahne(t, t - T_P, "denge", lambda ev, uu: rk.zcam(ev, uu, 90, 0.4 + 0.06 * u, 0.12))


def sh_k2(u, t):         # gec doğan notron: parca yakin
    return gecikme_sahne(t, u + 0.3, gcam(u, 60, 48, -0.5, 0.25), t_beta=0.6, t_n=1.3)


def sh_s1(u, t):         # "reaktoru yoneten": santral genis
    return sk.dis_sahne(t, sk.orbit(u, 0.95, 0.07, 520, 480, 30, 40, (0, 40, -60), 50), poz=0.8)


def sh_s2(u, t):         # koruma kabi yakin
    return sk.dis_sahne(t, sk.cam_at((70 - 20 * sm(u / 2.5), 14, 95), (0, 34, 0), 48), poz=0.85)


def sh_d1(u, t):         # "bir uranyum cekirdegi": yakit demeti
    k = sm(u / 3.0)
    eye = np.array((0.95, 1.15, 0.3)) * (1 - k) + np.array((0.8, 1.3, 0.45)) * k
    return rk.demet_sahne(t, Cam(tuple(eye), (0, 2.4, 0), fov=38, near=0.01, aperture=0.25), notron=0.6, y0=2.0)


T_B = Z["bir"] + 1.3      # anlik notron patlamasi: fisyon "bolundugunde" ile


def sh_b1(u, t):
    return rk.zincir_sahne(t, t - T_B, "denge", lambda ev, uu: rk.zcam(ev, uu, 80, -0.3 + 0.05 * u, 0.1))


def sh_b2(u, t):
    return rk.zincir_sahne(t, t - T_B, "denge", lambda ev, uu: rk.zcam(ev, uu, 120, 0.9 + 0.05 * u, 0.25))


def sh_b3(u, t):
    return rk.zincir_sahne(t, t - T_B, "denge", lambda ev, uu: rk.zcam(ev, uu, 160, -0.8 + 0.05 * u, 0.35, 50, 0.2))


T_G = Z["birkac"] - 0.2   # gecikmis notron olayi


def sh_g1(u, t):          # "birkac tanesi ise bekler": parca, sakin
    return gecikme_sahne(t, t - T_G, gcam(u, 75, 62, 0.3, 0.2), t_beta=Z["once"] + 1.1 - T_G,
                         t_n=Z["notron"] + 0.3 - T_G)


def sh_g2(u, t):          # beta bozunmasi, yakin
    return gecikme_sahne(t, t - T_G, gcam(u, 52, 46, -0.6, 0.25, 0.2), t_beta=Z["once"] + 1.1 - T_G,
                         t_n=Z["notron"] + 0.3 - T_G)


def sh_g3(u, t):          # notron cikar, yan aci
    return gecikme_sahne(t, t - T_G, gcam(u, 70, 64, 0.9, 0.2, 0.05, tgt=(10, -3, 5)), t_beta=Z["once"] + 1.1 - T_G,
                         t_n=Z["notron"] + 0.3 - T_G)


T_G2 = Z["bu_bekleme"] - 0.2   # ikinci olay: bekleme suresi (yavas)


def sh_w1(u, t):
    return gecikme_sahne(t, t - T_G2, gcam(u, 90, 70, -0.2, 0.3, 0.25), t_beta=1.6, t_n=2.6)


def sh_w2(u, t):
    return gecikme_sahne(t, t - T_G2, gcam(u, 64, 56, 1.2, 0.2, -0.05), t_beta=1.6, t_n=2.6)


def sh_n1(u, t):          # "bu neden onemli?": santral, kabin
    return sk.dis_sahne(t, sk.orbit(u, -0.4, 0.06, 260, 245, 70, 76, (0, 40, 0), 34), poz=0.9)


def sh_d2(u, t):          # DOE el kitabi: demet, notron isiklari
    k = sm(u / 3.0)
    eye = np.array((0.3, 0.9, 0.35)) * (1 - k) + np.array((0.36, 1.0, 0.25)) * k
    return rk.demet_sahne(t, Cam(tuple(eye), (0.05, 1.7, 0), fov=56, near=0.01, aperture=0.25), notron=1.0, y0=1.4)


def sh_d3(u, t):
    k = sm(u / 3.0)
    eye = np.array((0.55, 3.6, 0.7)) * (1 - k) + np.array((0.5, 3.4, 0.6)) * k
    return rk.demet_sahne(t, Cam(tuple(eye), (0, 3.3, 0), fov=40, near=0.01, aperture=0.25), notron=1.0, y0=3.3)


T_H = Z["yalniz"] - 0.3   # hizli zincir: yalniz anlik notronlar (saat 2,5 kat hizli)


def sh_h1(u, t):
    return rk.zincir_sahne(t, (t - T_H) * 2.5, "denge", lambda ev, uu: rk.zcam(ev, uu, 140, -0.2 + 0.05 * u, 0.15, 48, 0.8))


def sh_h2(u, t):
    return rk.zincir_sahne(t, (t - T_H) * 2.5, "denge", lambda ev, uu: rk.zcam(ev, uu, 170, 0.9 + 0.05 * u, 0.3, 50, 0.8))


T_Y = Z["geciken"] - 0.2  # yavas zincir: gecikmis notronlarla (saat 0,35 kat)


def sh_y1(u, t):
    return rk.zincir_sahne(t, 0.6 + (t - T_Y) * 0.35, "denge", lambda ev, uu: rk.zcam(ev, uu, 100, 0.2 + 0.05 * u, 0.1))


def sh_y2(u, t):
    return rk.zincir_sahne(t, 0.6 + (t - T_Y) * 0.35, "denge", lambda ev, uu: rk.zcam(ev, uu, 130, -0.9 + 0.05 * u, 0.3, 48))


def sh_s3(u, t):          # "bu gecikme olmasaydi": santral genis
    return sk.dis_sahne(t, sk.orbit(u, 0.55, 0.06, 760, 720, 60, 70, (-30, 120, -150), 50), poz=0.8)


T_U = Z["guc"] - 0.3


def sh_u1(u, t):          # "guc cok hizli sicrardi": kritik ustu zincir
    return rk.zincir_sahne(t, (t - T_U) * 1.6, "ust", lambda ev, uu: rk.zcam(ev, uu, 160 + 40 * u, 0.4, 0.15, 50, 0.0))


def sh_s4(u, t):          # "kontrol edilemezdi": kabin yakini, alcak
    return sk.dis_sahne(t, sk.cam_at((-60 + 15 * sm(u / 2.5), 6, 110), (0, 30, 0), 52), poz=0.85)


T_D = Z["yani"] - 0.2


def sh_z1(u, t):          # "zincirleme tepkimeyi dizginleyen": denge zinciri, genis
    return rk.zincir_sahne(t, t - T_D, "denge", lambda ev, uu: rk.zcam(ev, uu, 150, 0.2 + 0.05 * u, 0.3, 48, 0.3))


def sh_g4(u, t):          # "en gec gelen notronlardir": gecikmis notron yakin
    return gecikme_sahne(t, t - (Z["en_gec"] - 0.5), gcam(u, 58, 46, 0.5, 0.2, 0.1), t_beta=0.25, t_n=0.8)


def sh_son1(u, t):
    return sk.dis_sahne(t, sk.orbit(u, 0.4, 0.08, 800, 760, 120, 130, (-40, 160, -230), 46), poz=0.8)


def sh_son2(u, t):
    return sk.dis_sahne(t, sk.orbit(u, 1.1, 0.06, 700, 680, 60, 70, (-40, 150, -230), 48), poz=0.8)


def sh_son3(u, t):
    return sk.dis_sahne(t, sk.orbit(u, -0.2, 0.06, 620, 600, 180, 190, (-40, 170, -230), 44), poz=0.8)


SHOTS = [(-1.0, sh_k1), (2.4, sh_k2), (Z["reaktoru"] - 0.1, sh_s1), (Z["bir"] - 0.4, sh_s2), (Z["bir"] + 0.9, sh_d1),
         (Z["yuzde"] - 0.1, sh_b1), (Z["saniyenin"] - 0.1, sh_b2), (Z["bunlar"] - 0.1, sh_b3),
         (T_G, sh_g1), (Z["once"] + 0.6, sh_g2), (Z["notron"] - 0.1, sh_g3), (T_G2, sh_w1), (Z["dakika"] - 0.1, sh_w2),
         (Z["neden"] - 0.2, sh_n1), (Z["abd"] - 0.1, sh_d2), (Z["abd"] + 1.9, sh_d3), (T_H, sh_h1),
         (Z["yirmi"] - 0.9, sh_h2), (T_Y, sh_y1), (Z["bin6"] - 0.5, sh_y2), (Z["gecikme"] - 0.1, sh_s3),
         (T_U, sh_u1), (Z["kontrol"] - 0.1, sh_s4), (T_D, sh_z1), (Z["en_gec"] - 0.5, sh_g4),
         (END0, sh_son1), (END0 + 2.6, sh_son2), (END0 + 5.2, sh_son3)]


# ----------------------------------------------------------------- ekran yazilari (ust bolge, y 360-800)
def yazilar(img, t):
    a = 1.0 - fade(t, Z["reaktoru"] - 0.3, Z["reaktoru"])
    lines(img, [("1.000 NÖTRONDAN", WHITE), ("6,5'İ GEÇ DOĞAR", AMBER)], 430, a, 92)
    lines(img, [("REAKTÖRÜ", WHITE), ("ONLAR YÖNETİR", CYAN)], 430, win(t, Z["reaktoru"], Z["bir"] - 0.1, 0.25), 92)
    label(img, "BİR U-235 ÇEKİRDEĞİ BÖLÜNÜR", 540, 430, win(t, Z["bir"] + 0.1, Z["yuzde"] - 0.15, 0.25), 58, WHITE, F_XB)
    cardl(img, ["%99'dan fazlası"], 540, 440, win(t, Z["yuzde"], Z["bunlar"] - 0.15, 0.25), 72, amber=True)
    cardl(img, ["saniyenin", "10 trilyonda biri içinde"], 540, 610, win(t, Z["saniyenin"] + 0.4, Z["bunlar"] - 0.15, 0.25), 60)
    lines(img, [("ANLIK", CYAN), ("NÖTRONLAR", WHITE)], 420, win(t, Z["bunlar"], Z["birkac"] - 0.15, 0.25), 100)
    lines(img, [("BİRKAÇI", WHITE), ("BEKLER", AMBER)], 420, win(t, Z["birkac"], Z["once"] - 0.1, 0.25), 100)
    label(img, "1) BÖLÜNME PARÇASI BOZUNUR", 540, 410, win(t, Z["once"], Z["bu_bekleme"] - 0.15, 0.25), 54, AMBER, F_XB)
    label(img, "2) SONRA NÖTRON ÇIKAR", 540, 490, win(t, Z["notron"], Z["bu_bekleme"] - 0.15, 0.25), 54, CYAN, F_XB)
    lines(img, [("GECİKMİŞ NÖTRON", AMBER)], 420, win(t, Z["bu_bekleme"], Z["neden"] - 0.15, 0.25), 84)
    cardl(img, ["Bekleme: saniyenin kesrinden", "neredeyse 1 dakikaya"], 540, 580,
          win(t, Z["kesrinden"], Z["neden"] - 0.15, 0.3), 50)
    lines(img, [("BU NEDEN", WHITE), ("ÖNEMLİ?", AMBER)], 430, win(t, Z["neden"], Z["abd"] - 0.1, 0.25), 100)
    label(img, "ABD ENERJİ BAKANLIĞI (DOE)", 540, 380, win(t, Z["abd"], Z["geciken"] - 0.15, 0.3), 46, CYAN, F_B)
    label(img, "EL KİTABI ÖRNEĞİ", 540, 440, win(t, Z["abd"] + 0.2, Z["geciken"] - 0.15, 0.3), 40, MUTED, F_B)
    lines(img, [("YALNIZ ANLIK NÖTRONLAR:", WHITE)], 540, win(t, Z["yalniz"], Z["geciken"] - 0.15, 0.25), 56)
    cardl(img, ["1 kuşak = 1/20.000 s"], 540, 650, win(t, Z["kusak"] + 0.3, Z["geciken"] - 0.15, 0.25), 66)
    lines(img, [("GECİKMİŞ NÖTRONLARLA:", WHITE)], 540, win(t, Z["geciken"], Z["bin6"] - 0.2, 0.25), 56)
    cardl(img, ["1 kuşak ≈ 0,08 s"], 540, 650, win(t, Z["geciken"] + 0.4, Z["bin6"] - 0.2, 0.25), 66, amber=True)
    lines(img, [("≈ 1.600 KAT", AMBER), ("UZUN", WHITE)], 460, win(t, Z["bin6"] - 0.1, Z["gecikme"] - 0.15, 0.25), 104)
    lines(img, [("GECİKME", WHITE), ("OLMASAYDI…", AMBER)], 430, win(t, Z["gecikme"], Z["guc"] - 0.1, 0.25), 96)
    lines(img, [("GÜÇ ÇOK HIZLI", WHITE), ("SIÇRARDI", AMBER)], 430, win(t, Z["guc"], Z["kontrol"] - 0.1, 0.25), 92)
    lines(img, [("KONTROL", WHITE), ("MÜMKÜN OLMAZDI", AMBER)], 430, win(t, Z["kontrol"] + 0.1, Z["yani"] - 0.1, 0.25), 88)
    lines(img, [("ZİNCİRİ DİZGİNLEYEN:", WHITE)], 430, win(t, Z["yani"] + 0.1, END0, 0.25), 70)
    lines(img, [("EN GEÇ GELENLER", AMBER)], 530, win(t, Z["en_gec"], END0, 0.25), 92)


def kapanis(img, t):
    ec = clamp01((t - END0) / 4.0)          # yavas karartma (0,5 sn'de parlaklik sicramasi < %20)
    if ec <= 0:
        return img
    dark = (img.astype(np.float32) * 0.36 + np.array([6, 12, 30], np.float32) * 0.64).astype(np.uint8)
    img = blend(img, cv2.GaussianBlur(dark, (0, 0), 3), ec)
    if NOTXT:
        return img
    label(img, "KAYNAK", 540, 500, fade(t, END0 + 0.1, END0 + 0.6), 50, CYAN, F_B)
    rows = ["ABD Enerji Bakanlığı (DOE),", "DOE-HDBK-1019/1-93 Reactor Theory:", "Prompt and Delayed Neutrons"]
    for i, r in enumerate(rows):
        label(img, r, 540, 590 + i * 60, fade(t, END0 + 0.2 + 0.1 * i, END0 + 0.8 + 0.1 * i), 40,
              WHITE, F_SB if i == 0 else F_M, 990)
    k = fade(t, Z["takip"] - 0.3, Z["takip"] + 0.1)
    pulse = 1.0 + 0.04 * math.sin(max(0.0, t - Z["takip"]) * 4.0)
    blit(img, pill("TAKİP ET", F_XB, 120, NAVYTXT, AMBER, padx=70, pady=30, fill=AMBER, fill_a=1.0), 540, 1040,
         op=k, scale=pulse * (1.0 + 0.25 * (1 - k)))
    label(img, "DEVAMI KANALDA · BÖLÜM %d" % BOLUM, 540, 1660, fade(t, Z["devami"], Z["devami"] + 0.5), 52, AMBER, F_B, 900)
    return img


# ----------------------------------------------------------------- parlaklik esitleme (PARLAMA YOK kurali)
NORM = os.environ.get("NORM", "1") == "1"
HEDEF = None             # NORM=0 ... olc ile ham olcum -> hedef_hesapla()


def esitle(img, t):
    if HEDEF is None or not NORM:
        return img
    rk.HEDEF = HEDEF
    return rk.esitle(img, t)


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
    json.dump(res, open(os.path.join(os.environ.get("WORK", "/tmp/gn"), "parlama%s.json" % ("" if NORM else "_ham")), "w"))
    if not NORM:
        print("HEDEF =", rk.hedef_hesapla([r[2] for r in res]))
    print("EN KOTU: oran %.3f%%, sicrama %.1f%%" % (max(r[1] for r in res) * 100, max(r[3] for r in res) * 100))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "olc":
        olc()
    else:
        cli("render_gec_notron_3d", frame, NFRAMES, NAME)
