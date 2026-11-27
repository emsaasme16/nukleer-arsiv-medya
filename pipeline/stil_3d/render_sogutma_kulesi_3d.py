#!/usr/bin/env python3
"""Gercekci 3D Short: Sogutma kulesinden cikan duman mi? (ornek/yeni-kurallar-ornegi.mp4), 1080x1920, 30 fps.

Yeni kurallar ornegi (2026-11-27): acilis cumlesi puanlamasi, kelime kelime altyazi (altyazi_kelime.py), 2-3 sn'de bir
goruntu degisimi, parlamasiz (mat zemin/su, bloom yalniz kucuk isiklarda), 'Devami kanalda; takip et, kacirma.' kapanisi.

Ses: $WORK/mix.wav (../uzun_3d/sesler.py, TAIL=5.5). Zamanlar bagimsiz transkriptin kelime zamanlarindan (+1,0 sn):
metinler/sogutma-kulesi-duman-mi.words.json.
Kaynaklar: ABD DOE, "The Harnessed Atom" (DOE/NE-0143) ders 6: kuleden duman gibi gorunen sey gol suyunun buhari,
reaktore hic yaklasmamis, radyoaktif degil; uc dongu, sular karismaz, yalniz isi aktarilir; ilik su asagi suzulur,
bir kismi buharlasir; isi ve nem tepeden ~16 km/sa ile cikar; 200 m ile genellikle santralin en yuksek yapisi.
ABD NRC, Reactor Concepts Manual, "Nuclear Power for Electrical Generation": kuleden cikan "buhar" ilik su buharidir,
radyoaktif degildir; soguk hava nemi tutamaz, gorunur bulut olusur, havaya karisinca kaybolur.
Kullanim: WORK=/tmp/sk python3 render_sogutma_kulesi_3d.py still 0 3 6 ... | render | olc
"""
import os
from dikey_kit import *
import santral
from altyazi_kelime import Altyazi

NAME = "yeni-kurallar-ornegi"
TOTAL = 52.98
NFRAMES = int(round(TOTAL * FPS))
BOLUM = 2
NOTXT = os.environ.get("NOTXT") == "1"      # parlama olcumu icin yazisiz kare

WORDS = os.path.join(HERE, "metinler", "sogutma-kulesi-duman-mi.words.json")
VURGU = ["göl", "buharıdır", "gitmez", "üç", "karışmaz", "buharlaşır", "yükselir", "16 km", "radyoaktif", "tutamaz",
         "kaybolur", "200 metre", "kanalda", "takip"]
AY = Altyazi(WORDS, 1.0, VURGU, {("on", "altı", "kilometre"): "16 km", ("iki", "yüz", "metre"): "200 metre"})

# cumle/ifade baslangiclari (video saniyesi = transkript + 1,0)
Z = dict(duman=5.48, ama=6.9, buharidir=11.24, bu_su=12.14, santralde=14.7, sular=17.18, yalnizca=18.74,
         kulenin=20.52, kismi=23.08, nemli=24.62, tepeden=26.2, yaklasik=27.06, nrc=29.62, radyoaktif=33.58,
         soguk=35.08, gorunur=36.78, sonra=38.22, iki_yuz=40.12, santralin=42.68, devami=44.86, takip=46.08)
END0 = 44.7

# ----------------------------------------------------------------- malzemeler (hepsi mat; parlama yok)
SU_MAT = Mat(srgb((34, 46, 54)), 0.78, 0.0, pat="su", scale=0.25)        # gol: puruzlu, spekuler dusuk
KULE_BETON = Mat(srgb((150, 146, 138)), 0.92, pat="beton", scale=0.3)
CIM_MAT = Mat(srgb((62, 78, 44)), 1.0, pat="cim", scale=0.15)
TOWER = (-40.0, 0.0, -230.0)
TH = 200.0                                 # DOE: "At 200 meters (656 feet) high"
RB, RT, RTOP = 0.40 * TH * 0.62, 0.25 * TH * 0.62, 0.28 * TH * 0.62


def m_kule():
    return m_hyperboloid(RB, RT, RTOP, TH - 12.0, (TH - 12.0) * 0.78, 80, 48, 1.2)


KULE = ("kule200", m_kule)


def ortam(S, soguk=False):
    """ogleden sonra, hafif bulutlu: gunes yumusak, gok doygun ama esigin altinda."""
    gunduz(S)
    S.sun_dir = norm((0.55, 0.42, 0.3))
    S.sun_col = (2.3, 2.1, 1.85)
    S.sky_zen = (0.10, 0.20, 0.46) if not soguk else (0.09, 0.17, 0.40)
    S.sky_hor = (0.40, 0.48, 0.60) if not soguk else (0.36, 0.43, 0.55)
    S.clouds = 0.45
    S.sun_disk = 0.0
    S.amb = 0.85
    S.exposure = 0.82
    S.bloom = 0.25
    S.bloom_th = 2.5                       # bloom yalniz cok parlak kucuk isiklarda
    S.fog = (0.0007, 0.01, 0.0, 0.55)
    S.fog_col = (0.42, 0.5, 0.62)
    S.shadow_box = ((-40, 0, -110), 340)
    S.shadow_bias = 0.002
    S.ssao_r = 1.2


def buhar(S, t, n=200, yay=1.0, gorunur=1.0, a0=0.5):
    """tepeden yukselen ilik su buhari: ruzgarla egilir, buyur, seyrelir (gorunur bulut -> havaya karisir)."""
    rng = np.random.default_rng(7)
    top = np.array(TOWER) + (0, TH - 12.0, 0)
    for k in range(n):
        ph = (k / n + t * 0.035) % 1.0
        ang = rng.uniform(0, 6.28)
        rr = rng.uniform(0, 0.85) * RTOP
        hgt = ph * TH * 0.95 * yay
        drift = np.array([1.0, 0, 0.35]) * (ph ** 1.4) * TH * 0.9 * yay
        pos = top + np.array([math.cos(ang) * rr, hgt, math.sin(ang) * rr]) + drift
        size = RTOP * (0.5 + 1.5 * ph)
        a = a0 * gorunur * (1 - ph) ** 1.5 * min(1.0, ph * 7)
        S.particle(tuple(pos), size, (0.86, 0.88, 0.9, a), kind=1, seed=k * 0.71 + ph, rot=k * 1.7)


def santral_sahne(S, t, kule_ic=False):
    I = np.eye(4)
    S.add(PLANE_HI, TRS((0, 0, 0), s=(4000, 1, 4000)), CIM_MAT)
    S.add(BOX, TRS((15, 0.04, 0), s=(150, 0.08, 90)), ZEMIN_MAT)
    S.add(BOX, TRS((10, 0.06, 40), s=(260, 0.1, 9)), ZEMIN_MAT.but(pat="asfalt", scale=1.0))
    S.add(BOX, TRS((-60, 0.06, -60), s=(9, 0.1, 200)), ZEMIN_MAT.but(pat="asfalt", scale=1.0))
    S.add(PLANE, TRS((-330, 0.25, -120), s=(420, 1, 640)), SU_MAT)                       # gol
    santral.containment_pwr(S, I)
    santral.building(S, TRS((52, 0, -2)), 58, 34, 38, santral.PANEL, doors=2, windows=6)
    santral.building(S, TRS((0, 0, -34)), 40, 22, 24, santral.PANEL_BEJ, windows=5)
    santral.building(S, TRS((-36, 0, 6)), 22, 18, 30, santral.BETON, windows=3)
    santral.building(S, TRS((-110, 0, -150)), 26, 9, 16, santral.BETON_KOYU, windows=2)   # gol suyu pompa evi
    # kule: X kolonlar + kabuk + havuz
    Tt = TRS(TOWER)
    S.add(KULE, Tt @ TRS((0, 12.0, 0)), KULE_BETON)
    for i in range(56):
        a0 = 2 * math.pi * i / 56
        a1 = 2 * math.pi * (i + 1) / 56
        p0 = np.array([math.cos(a0) * RB, 0, math.sin(a0) * RB])
        p1 = np.array([math.cos(a1) * RB, 12.2, math.sin(a1) * RB])
        p2 = np.array([math.cos(a1) * RB, 0, math.sin(a1) * RB])
        p3 = np.array([math.cos(a0) * RB, 12.2, math.sin(a0) * RB])
        S.add(CYL_LO, Tt @ align(p0, p1, 0.55), KULE_BETON)
        S.add(CYL_LO, Tt @ align(p2, p3, 0.55), KULE_BETON)
    S.add(("havuz_k", lambda: m_lathe([(1.0, 0), (1.0, 1.0), (1.03, 1.0), (1.03, 0)], 80)),
          Tt @ TRS((0, 0, 0), s=(RB + 3, 1.2, RB + 3)), santral.BETON_KOYU)
    S.add(PLANE, Tt @ TRS((0, 0.7, 0), s=(2 * RB + 5, 1, 2 * RB + 5)), SU_MAT)
    santral.tank(S, TRS((95, 0, 30)), 7, 12)
    santral.tank(S, TRS((95, 0, 52)), 7, 12)
    for k in range(4):
        santral.pylon(S, TRS((160 + k * 70, 0, -40 - k * 12)), 34)
    santral.fence(S, TRS((20, 0, 52)), 200)
    for i, x in enumerate((-20, 20, 60, 100)):
        santral.lamp_post(S, TRS((x, 0, 46), ry(math.pi / 2)), on=0.0)
    santral.human(S, TRS((-112, 0, 72), ry(2.6)), walk=t * 3.0)
    santral.human(S, TRS((-109, 0, 73.5), ry(2.8)), col=(0.2, 0.45, 0.8), walk=t * 3.0 + 1.0)
    santral.fence(S, TRS((-110, 0, 66)), 60)
    santral.car(S, TRS((-5 + (t * 4.0) % 80, 0, 38), ry(math.pi / 2)))
    santral.car(S, TRS((70, 0, 44)), col=(0.75, 0.75, 0.78))
    # uzak tepeler/agac kumeleri (ufuk)
    rng = np.random.default_rng(3)
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(700, 1400)
        S.add(SPH_LO, TRS((math.cos(a) * d, 0, math.sin(a) * d), s=(rng.uniform(60, 140), rng.uniform(25, 60), 80)),
              Mat(srgb((48, 62, 40)), 1.0, pat="cim", scale=0.05))


def cam_at(eye, tgt, fov=45, ap=0.0):
    return Cam(eye, tgt, fov=fov, near=1.0, far=8000, aperture=ap)


def orbit(u, ang0, dang, d0, d1, h0, h1, tgt, fov, dur=3.0):
    k = sm(u / dur) * 0.6 + (u / dur) * 0.4
    ang = ang0 + dang * k
    d = d0 + (d1 - d0) * k
    h = h0 + (h1 - h0) * k
    c = np.array(tgt[:3], float)
    eye = c + np.array([math.sin(ang) * d, h - c[1], math.cos(ang) * d])
    return cam_at(eye, tgt, fov)


def dis_sahne(t, cam, **kw):
    S = Sahne()
    ortam(S, soguk=kw.get("soguk", False))
    santral_sahne(S, t)
    buhar(S, t, yay=kw.get("yay", 1.0), gorunur=kw.get("gorunur", 1.0))
    S.exposure *= kw.get("poz", 1.0)
    return ciz(S, cam, t)


TOP = np.array(TOWER) + (0, TH, 0)
MID = np.array(TOWER) + (0, TH * 0.6, 0)


# ----------------------------------------------------------------- planlar (her biri <= 3 sn)
def sh_a1(u, t):        # acilis: genis, alcak; kule ve bulut
    cam = orbit(u, 0.55, 0.06, 760, 700, 60, 70, (-60, 170, -230), 52)
    return dis_sahne(t, cam)


def sh_a2(u, t):        # bulutun tepesi, tele
    cam = orbit(u, 0.25, -0.05, 620, 590, 210, 230, TOP + (40, 70, 0), 34)
    return dis_sahne(t, cam)


def sh_duman(u, t):     # alttan bulut
    cam = orbit(u, 1.25, 0.08, 330, 300, 20, 26, TOP + (30, 40, 0), 58)
    return dis_sahne(t, cam)


def sh_gol1(u, t):      # gol yuzeyi uzerinden kuleye
    eye = (-470 + 40 * sm(u / 2.5), 9, -60 - 20 * sm(u / 2.5))
    return dis_sahne(t, cam_at(eye, (-40, 120, -230), 50))


def sh_gol2(u, t):      # pompa evi ve gol, kule arkada
    eye = (-250 - 30 * sm(u / 2.5), 30, 60)
    return dis_sahne(t, cam_at(eye, (-90, 70, -200), 48))


def sh_reaktor(u, t):   # koruma kabi on planda, kule arkada
    eye = (60 - 25 * sm(u / 2.6), 26, 120)
    return dis_sahne(t, cam_at(eye, (-20, 70, -120), 50), poz=0.8)


def sh_dongu1(u, t):    # havadan
    cam = orbit(u, 0.9, 0.08, 420, 400, 330, 320, (-20, 0, -110), 48)
    return dis_sahne(t, cam)


def sh_dongu2(u, t):
    cam = orbit(u, 0.35, -0.07, 330, 310, 230, 220, (0, 0, -90), 50)
    return dis_sahne(t, cam)


def sh_dongu3(u, t):    # kondenser binasindan kuleye
    eye = (140 - 20 * sm(u / 2), 70, 60)
    return dis_sahne(t, cam_at(eye, (-30, 40, -170), 46))


def ic_sahne(t, cam, ust=False):
    S = Sahne()
    ortam(S)
    S.amb = 0.8
    S.exposure = 1.35
    santral_sahne(S, t)
    rng = np.random.default_rng(11)
    c = np.array(TOWER)
    for k in range(380):                      # asagi suzulen ilik su damlalari
        r = RB * 0.85 * math.sqrt(rng.uniform())
        a = rng.uniform(0, 6.28)
        y = 13.0 - ((rng.uniform() * 13.0 + t * 9.0) % 13.0)
        S.particle(tuple(c + (math.cos(a) * r, y + 0.4, math.sin(a) * r)), 0.22, (0.62, 0.7, 0.76, 0.55), kind=0)
    for k in range(70):                       # yukselen buhar
        ph = (k / 70 + t * 0.08) % 1.0
        r = RB * 0.7 * math.sqrt(rng.uniform())
        a = rng.uniform(0, 6.28)
        p = c + (math.cos(a) * r, 14 + ph * (TH - 30), math.sin(a) * r)
        S.particle(tuple(p), 9 + 22 * ph, (0.75, 0.78, 0.82, 0.16 * min(1, ph * 6) * (1 - ph)), kind=1, seed=k * 0.3)
    S.light(tuple(c + (0, 6, 0)), 120, (0.8, 0.85, 0.9), 0.6)
    return ciz(S, cam, t)


def sh_ic1(u, t):       # kulenin icinde, yukari bakis
    c = np.array(TOWER)
    eye = c + (35 - 4 * u, 3.0, 20)
    return ic_sahne(t, cam_at(eye, c + (-10, 150, -10), 70))


def sh_ic2(u, t):       # damlalar ve buhar, yan bakis
    c = np.array(TOWER)
    eye = c + (30 - 4 * sm(u / 2), 4 + 1.5 * u, -8)
    return ic_sahne(t, cam_at(eye, c + (-30, 26, 4), 62))


def sh_tepe1(u, t):     # kule agzi yakin
    cam = orbit(u, 0.6, 0.1, 260, 240, TH + 50, TH + 60, TOP + (0, 20, 0), 46)
    return dis_sahne(t, cam, poz=0.85)


def sh_tepe2(u, t):
    cam = orbit(u, -0.3, 0.07, 520, 500, 150, 165, TOP + (40, 40, 0), 44)
    return dis_sahne(t, cam)


def sh_tepe3(u, t):
    cam = orbit(u, 2.3, -0.07, 480, 470, TH + 160, TH + 150, TOP + (60, 60, 0), 44)
    return dis_sahne(t, cam)


def sh_nrc1(u, t):      # yerden, cit ve insanlar on planda
    eye = (-118 - 3 * u, 1.7, 92)
    return dis_sahne(t, cam_at(eye, (-45, 95, -230), 56))


def sh_nrc2(u, t):
    cam = orbit(u, 1.7, 0.08, 520, 490, 80, 95, MID + (20, 60, 0), 46)
    return dis_sahne(t, cam)


def sh_nrc3(u, t):
    cam = orbit(u, 0.0, 0.07, 450, 430, 260, 270, TOP + (60, 70, 0), 40)
    return dis_sahne(t, cam)


def sh_bulut1(u, t):    # soguk gokyuzu, bulut
    cam = orbit(u, 0.95, 0.06, 560, 540, TH + 30, TH + 40, TOP + (80, 90, 0), 42)
    return dis_sahne(t, cam, soguk=True)


def sh_bulut2(u, t):    # bulut seyrelir, kaybolur
    cam = orbit(u, 1.4, 0.07, 640, 620, TH + 120, TH + 130, TOP + (120, 120, 0), 46)
    return dis_sahne(t, cam, soguk=True, gorunur=1.0 - 0.45 * sm(u / 3.0))


def sh_boy1(u, t):      # yerden yukari: insan olcegi
    c = np.array(TOWER)
    eye = c + (RB + 32, 1.8, RB + 50 - 4 * u)
    return dis_sahne(t, cam_at(eye, c + (0, 110, 0), 66), poz=0.8)


def sh_boy2(u, t):      # genis: kule santralin en yuksek yapisi
    cam = orbit(u, 0.75, 0.05, 900, 880, 40, 45, (-10, 90, -110), 46)
    return dis_sahne(t, cam)


def sh_son1(u, t):
    cam = orbit(u, 0.4, 0.08, 800, 760, 120, 130, (-40, 160, -230), 46)
    return dis_sahne(t, cam)


def sh_son2(u, t):
    cam = orbit(u, 1.1, 0.06, 700, 680, 60, 70, (-40, 150, -230), 48)
    return dis_sahne(t, cam)


def sh_son3(u, t):
    cam = orbit(u, -0.2, 0.06, 620, 600, 180, 190, (-40, 170, -230), 44)
    return dis_sahne(t, cam)


SHOTS = [(-1.0, sh_a1), (2.7, sh_a2), (Z["duman"] - 0.15, sh_duman), (Z["ama"] + 0.6, sh_gol1), (9.9, sh_gol2),
         (Z["bu_su"] - 0.1, sh_reaktor), (Z["santralde"] - 0.1, sh_dongu1), (Z["sular"] - 0.1, sh_dongu2),
         (Z["yalnizca"] - 0.05, sh_dongu3), (Z["kulenin"] - 0.1, sh_ic1), (22.5, sh_ic2),
         (Z["nemli"] - 0.1, sh_tepe1), (Z["tepeden"] - 0.1, sh_tepe2), (28.2, sh_tepe3),
         (Z["nrc"] - 0.1, sh_nrc1), (31.7, sh_nrc2), (Z["radyoaktif"] - 0.2, sh_nrc3),
         (Z["soguk"] - 0.1, sh_bulut1), (Z["gorunur"] + 0.3, sh_bulut2), (Z["iki_yuz"] - 0.1, sh_boy1),
         (42.4, sh_boy2), (END0, sh_son1), (48.6, sh_son2), (51.15, sh_son3)]

# ----------------------------------------------------------------- dongu cizimi (2D bindirme, 3D noktalardan)
LOOPS = [
    ([(-8, 6, 0), (-8, 34, 0), (8, 34, 0), (8, 6, 0), (-8, 6, 0)], (255, 110, 90), "1"),
    ([(10, 30, 0), (44, 30, -2), (44, 8, -2), (10, 8, 0), (10, 30, 0)], AMBER, "2"),
    ([(60, 5, -2), (60, 3, -90), (-20, 3, -200), (-40, 18, -230), (-40, 3, -230), (-30, 2, -200), (52, 2, -90),
      (52, 4, -2)], CYAN, "3"),
]


def loops(img, cam, t, t0, etiket=True):
    for i, (pts, col, nm) in enumerate(LOOPS):
        k = fade(t, t0 + 0.55 * i, t0 + 0.55 * i + 0.6)
        if k <= 0:
            continue
        P = [proj(cam, p) for p in pts]
        seglen = [math.dist(P[j], P[j + 1]) for j in range(len(P) - 1)]
        L = sum(seglen) * k
        poly = [P[0]]
        for j, sl in enumerate(seglen):
            if L <= 0:
                break
            f = min(1.0, L / max(sl, 1e-6))
            poly.append((P[j][0] + (P[j + 1][0] - P[j][0]) * f, P[j][1] + (P[j + 1][1] - P[j][1]) * f))
            L -= sl
        arr = np.array(poly, np.int32).reshape(-1, 1, 2)
        cv2.polylines(img, [arr], False, (8, 16, 38), 16, cv2.LINE_AA)
        cv2.polylines(img, [arr], False, col, 9, cv2.LINE_AA)
        if etiket and k > 0.5:
            q = P[1] if i < 2 else P[2]
            blit(img, pill("%s. DÖNGÜ" % nm, F_B, 34, col, col, padx=22, pady=10, fill_a=0.7), q[0], q[1] - 50,
                 op=fade(k, 0.5, 1.0))


# ----------------------------------------------------------------- ekran yazilari
def yazilar(img, t):
    # acilis (ilk karede tam gorunur, en iyi aday): "O BEYAZ BULUT, ASLINDA GOL SUYU"
    a = 1.0 - fade(t, Z["duman"] - 0.35, Z["duman"])
    lines(img, [("O BEYAZ BULUT,", WHITE), ("ASLINDA GÖL SUYU", AMBER)], 430, a, 92)
    label(img, "DUMAN MI?", 540, 470, win(t, Z["duman"], Z["ama"] + 0.55, 0.25), 110, WHITE, F_XB)
    label(img, "ABD ENERJİ BAKANLIĞI (DOE):", 540, 380, win(t, Z["ama"] + 0.6, Z["bu_su"] - 0.1, 0.3), 46, CYAN, F_B)
    cardl(img, ["Kuleden çıkan:", "göl suyunun buharı"], 540, 520, win(t, 8.6, Z["bu_su"] - 0.1, 0.3), 58, amber=True)
    lines(img, [("REAKTÖRE", WHITE), ("HİÇ YAKLAŞMAZ", AMBER)], 430, win(t, Z["bu_su"] + 0.3, Z["santralde"] - 0.1, 0.3), 88)
    lines(img, [("3 AYRI", AMBER), ("SU DÖNGÜSÜ", WHITE)], 420, win(t, Z["santralde"] + 0.2, Z["sular"] - 0.1, 0.3), 92)
    cardl(img, ["Sular karışmaz"], 540, 420, win(t, Z["sular"] + 0.5, Z["kulenin"] - 0.1, 0.3), 62)
    cardl(img, ["Yalnızca ısı aktarılır"], 540, 560, win(t, Z["yalnizca"] + 0.2, Z["kulenin"] - 0.1, 0.3), 56, amber=True)
    lines(img, [("KULENİN İÇİ", WHITE)], 420, win(t, Z["kulenin"] + 0.1, Z["kismi"] - 0.2, 0.3), 92)
    cardl(img, ["Ilık su aşağı süzülür,", "bir kısmı buharlaşır"], 540, 470, win(t, Z["kismi"] - 0.4, Z["nemli"] - 0.1, 0.3), 54)
    lines(img, [("NEMLİ SICAK HAVA", WHITE), ("YÜKSELİR", AMBER)], 430, win(t, Z["nemli"] + 0.1, Z["tepeden"] - 0.1, 0.3), 86)
    cardl(img, ["≈ 16 km/sa"], 540, 470, win(t, Z["yaklasik"], Z["nrc"] - 0.1, 0.3), 96, amber=True)
    lines(img, [("ABD NÜKLEER DÜZENLEME", CYAN), ("KURULU (NRC):", CYAN)], 360, win(t, Z["nrc"] + 0.1, Z["soguk"] - 0.1, 0.3), 50)
    cardl(img, ["Ilık su buharı"], 540, 540, win(t, 31.0, Z["soguk"] - 0.1, 0.3), 70)
    stamp(img, "RADYOAKTİF DEĞİL", 540, 700, fade(t, Z["radyoaktif"] - 0.1, Z["radyoaktif"] + 0.15) *
          (1 - fade(t, Z["soguk"] - 0.3, Z["soguk"] - 0.05)), GREEN, 76,
          pop=0.3 * (1 - fade(t, Z["radyoaktif"] - 0.1, Z["radyoaktif"] + 0.3)))
    lines(img, [("SOĞUK HAVA", WHITE), ("BU NEMİ TUTAMAZ", CYAN)], 430, win(t, Z["soguk"] + 0.1, Z["gorunur"] + 0.25, 0.25), 86)
    lines(img, [("GÖRÜNÜR BULUT,", WHITE), ("SONRA KAYBOLUR", AMBER)], 430, win(t, Z["gorunur"] + 0.35, Z["iki_yuz"] - 0.1, 0.3), 86)
    cardl(img, ["200 m"], 540, 470, win(t, Z["iki_yuz"] + 0.1, END0, 0.3), 120, amber=True)
    label(img, "SANTRALİN EN YÜKSEK YAPISI", 540, 640, win(t, Z["santralin"] - 0.2, END0, 0.3), 54, WHITE, F_XB)


def kapanis(img, t):
    ec = clamp01((t - END0) / 2.4)          # yavas karartma: 0,5 sn'de parlaklik %20'den fazla dusmesin
    if ec <= 0:
        return img
    dark = (img.astype(np.float32) * 0.50 + np.array([6, 12, 30], np.float32) * 0.50).astype(np.uint8)
    img = blend(img, cv2.GaussianBlur(dark, (0, 0), 3), ec)
    if NOTXT:
        return img
    label(img, "KAYNAKLAR", 540, 470, fade(t, END0 + 0.1, END0 + 0.6), 50, CYAN, F_B)
    rows = ["ABD Enerji Bakanlığı (DOE),", "The Harnessed Atom", "ABD Nükleer Düzenleme Kurulu (NRC),",
            "Reactor Concepts Manual"]
    for i, r in enumerate(rows):
        label(img, r, 540, 560 + i * 56, fade(t, END0 + 0.2 + 0.1 * i, END0 + 0.8 + 0.1 * i), 36,
              WHITE if i % 2 == 0 else MUTED, F_M, 990)
    k = fade(t, Z["takip"] - 0.3, Z["takip"] + 0.1)
    pulse = 1.0 + 0.04 * math.sin(max(0.0, t - Z["takip"]) * 4.0)
    blit(img, pill("TAKİP ET", F_XB, 120, NAVYTXT, AMBER, padx=70, pady=30, fill=AMBER, fill_a=1.0), 540, 1040,
         op=k, scale=pulse * (1.0 + 0.25 * (1 - k)))
    label(img, "DEVAMI KANALDA · BÖLÜM %d" % BOLUM, 540, 1660, fade(t, Z["devami"], Z["devami"] + 0.5), 52, AMBER, F_B, 900)
    return img


def frame(t, yazi=None):
    yazi = (not NOTXT) if yazi is None else yazi
    img = shots(t, SHOTS, xf=0.35)
    if t < 14.7 + 0.1 or t > 20.6:
        pass
    else:
        # dongu planlari: kamera her karede yeniden kuruluyor, ayni kamerayi bindirme icin tekrar hesapla
        i = max(j for j in range(len(SHOTS)) if SHOTS[j][0] <= t)
        fn = SHOTS[i][1]
        u = t - SHOTS[i][0]
        cam = {sh_dongu1: lambda: orbit(u, 0.9, 0.08, 420, 400, 330, 320, (-20, 0, -110), 48),
               sh_dongu2: lambda: orbit(u, 0.35, -0.07, 330, 310, 230, 220, (0, 0, -90), 50),
               sh_dongu3: lambda: cam_at((140 - 20 * sm(u / 2), 70, 60), (-30, 40, -170), 46)}.get(fn)
        if cam is not None:
            loops(img, cam(), t, max(Z["santralde"], SHOTS[i][0]) if fn is sh_dongu1 else SHOTS[i][0] - 2.0,
                  etiket=yazi)
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
    res = []
    prev = None
    for t in ts:
        im = frame(t, yazi=False)
        lum = (0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2])
        oran = float((lum >= 245).mean())
        ort = float(lum.mean())
        sic = abs(ort - prev) / max(prev, 1.0) if prev is not None else 0.0
        prev = ort
        res.append((t, oran, ort, sic))
        print("%5.1f  >=245: %.3f%%  ort %.1f  sicrama %.1f%%" % (t, oran * 100, ort, sic * 100), flush=True)
    json.dump(res, open(os.path.join(os.environ.get("WORK", "/tmp/sk"), "parlama.json"), "w"))
    print("EN KOTU: oran %.3f%%, sicrama %.1f%%" % (max(r[1] for r in res) * 100, max(r[3] for r in res) * 100))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "olc":
        olc()
    else:
        cli("render_sogutma_kulesi_3d", frame, NFRAMES, NAME)
