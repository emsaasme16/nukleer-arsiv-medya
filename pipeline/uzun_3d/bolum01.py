#!/usr/bin/env python3
"""Nukleer Arsiv - Bolum 1: Atomun icinde ne sakli? (uzun video, 1920x1080, 30 fps)

Zaman: sahne baslangiclari ve sureleri $WORK/cues.json'dan (sesler.py uretir). Her sahnenin
senaryodaki '+0:12' gibi gorsel ipuclari PLAN saniyesidir; gercek ses suresine oranla esnetilir
(animasyon sese uyar, ses hizlandirilmaz).

Kullanim:
  WORK=/tmp/bolum1 python3 bolum01.py still 10 30 ...      # kare kontrolu (PNG)
  WORK=/tmp/bolum1 python3 bolum01.py render                # tam video (cok surecli dilimler)
"""
import json
from common3d import *
from common3d import _align_y
from render_kit import *

WORK = os.environ.get("WORK", "/tmp/bolum1")
CUES = json.load(open(os.path.join(WORK, "cues.json")))
STARTS = CUES["starts"]
DURS = CUES["durations"]
TOTAL = CUES["duration"]
GAP = CUES["gap"]
PLAN = [72, 93, 83, 99, 122, 78, 68]       # senaryodaki tahmini sahne sureleri (gorsel ipuclari bu olcekte)
NFRAMES = int(round(TOTAL * FPS))
TAG = "NÜKLEER ARŞİV · BÖLÜM 1"


# ============================================================== SAHNE 1: Kanca
COAL = []
_r1 = np.random.default_rng(5)
for i in range(150):
    # yigin: yarim elipsoid
    while True:
        x, y, z = _r1.uniform(-1, 1, 3)
        if x * x + y * y + z * z < 1 and y > -0.05:
            break
    COAL.append((x, y, z, _r1.uniform(0.55, 1.0), _r1.uniform(0, 6.28, 3)))


def coal_heap(F, cx, cy, s, op=1.0, grow=1.0):
    n = int(len(COAL) * clamp01(grow))
    for i in range(n):
        x, y, z, k, a = COAL[i]
        R = rot_x(a[0]) @ rot_y(a[1]) @ rot_z(a[2])
        sz = 46 * s * k
        F.add(BOX, model((cx + x * 230 * s, cy - y * 150 * s, z * 120 * s), (sz, sz * 0.8, sz * 0.9), R),
              (52 + int(18 * k), 54 + int(16 * k), 62 + int(18 * k)), MAT_MATTE, op)


def pellet(F, x, y, z, rad, hgt, R, op=1.0, glow=0.6):
    F.cyl(x, y, z, rad, hgt, (150, 158, 176), MAT_METAL, alpha=op, R=R)
    if glow > 0:
        F.glow3(x, y, z, rad * 1.5, scol(AMBER, 0.7), glow * op * 0.45)


def lattice(F, t, cx, cy, depth, op):
    """Kristal doku: kameraya dogru akan atom izgarasi."""
    for i in range(-5, 6):
        for j in range(-3, 4):
            for k in range(6):
                z = -2400 + k * 520 + depth
                z = (z + 3000) % 3120 - 3000
                fo = op * clamp01((z + 3000) / 800) * clamp01((700 - z) / 400)
                if fo <= 0.02:
                    continue
                F.sphere(cx + i * 220, cy + j * 220, z, 16, (120, 150, 190), MAT_GLOSS, alpha=fo, lo=True)


def scene1(t, u, D):
    p = u * PLAN[0] / D
    # kamera: 0-12 alttan yaklasma; 12-45 genis; 45-72 dalis
    pitch = -0.30 * (1 - smooth(seg(p, 0, 12))) + 0.04 * math.sin(p * 0.2)
    dolly = 1.15 - 0.35 * smooth(seg(p, 0, 11)) + 0.35 * smooth(seg(p, 10.5, 14))
    F = Frame(t, Cam(yaw=0.08 * math.sin(p * 0.15), pitch=pitch, dolly=dolly))
    a_split = smooth(seg(p, 11.5, 14.5))
    a_dive = smooth(seg(p, 44, 50))
    # --- pelet (0-50)
    R = rot_y(p * 0.6) @ rot_x(0.35 + 0.1 * math.sin(p * 0.4))
    px = 960 + (-470) * a_split
    py = 520 + 0 * a_split
    if p < 52:
        po = fade(p, 0.0, 1.6) * (1 - fade(p, 48, 51))
        if a_split > 0:
            # terazi (14 g pelet <-> 1 t komur), dengede
            bo = a_split * (1 - a_dive)
            tilt = 0.0
            balance(F, 960, 300, 470, tilt, bo, wobble=0.02 * math.sin(p * 1.3) * (1 - smooth(seg(p, 14, 20))))
            pellet(F, px, 300 + 245 - 52, 0, 46, 92, rot_y(p * 0.5), po)
            coal_heap(F, 960 + 470, 300 + 245 - 20, 0.62, bo, grow=smooth(seg(p, 12, 18)))
        else:
            pellet(F, 960, 520, 0, 120, 230, R, po, glow=0.8)
    # --- etiketler ve sayac
    lab = fade(p, 16, 17) * (1 - fade(p, 43, 45))
    F.text("1 pelet (< 14 g)", F_SB, 40, WHITE, 490, 760, op=lab)
    F.text("≈ 1 ton kömür", F_SB, 40, WHITE, 1430, 760, op=lab)
    ttl = fade(p, 17, 18) * (1 - fade(p, 43, 45))
    F.text("1 pelet (< 14 g) ≈ 1 ton kömür", F_B, 60, WHITE, 960, 150, op=ttl)
    c = fade(p, 30, 31) * (1 - fade(p, 44, 46))
    if c > 0:
        k1 = ease_out(seg(p, 30, 32.5))
        F.spr(card(["%d g" % round(14 * k1)], 64), 560, 880, op=c)
        F.text("÷", F_B, 72, CYAN, 760, 880, op=fade(p, 31, 32) * c)
        F.spr(card(["1 t"], 64), 940, 880, op=fade(p, 31.5, 32.5) * c)
        F.text("=", F_B, 72, CYAN, 1100, 880, op=fade(p, 34, 35) * c)
    r = fade(p, 34, 35) * (1 - fade(p, 44, 46))
    if r > 0:
        F.spr(card(["> " + tr_int(70000 * ease_out(seg(p, 34, 37))) + "×"], 64, amber=True), 1340, 880, op=r)
        F.text("Gram başına > 70.000 kat", F_B, 56, AMBER, 960, 235, op=fade(p, 37, 38) * r)
    # --- dalis: kristal doku -> tek atom
    if p > 44:
        lo = fade(p, 46, 48) * (1 - fade(p, 52, 55))
        lattice(F, t, 960, 540, (p - 44) * 420, lo)
        ao = fade(p, 51, 54)
        atom(F, t, 960, 560, 1.0 + 0.15 * smooth(seg(p, 51, 60)), ao)
        q = fade(p, 56, 57.5)
        F.spr(card(["Çekirdek enerjiyi nasıl saklar?"], 58), 960, 150, op=q)
    return F


# ============================================================== SAHNE 2: Atomun haritasi
def stadium(F, cx, cy, s, op, baseball=False):
    if op <= 0.01:
        return
    if not baseball:
        F.box(cx, cy, -4, 620 * s, 390 * s, 6, (40, 120, 70), MAT_MATTE, op)
        n = 44
        for i in range(n):
            a = 2 * math.pi * i / n
            for ring in range(3):
                rx, ry = (370 + ring * 46) * s, (250 + ring * 40) * s
                x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
                F.box(x, y, (10 + ring * 22) * s, 44 * s, 40 * s, (20 + ring * 22) * s,
                      (70 + ring * 14, 86 + ring * 14, 120 + ring * 16), MAT_PLASTIC, op, R=rot_z(a))
    else:
        # stilize beyzbol stadyumu: elmas saha + yelpaze tribun
        F.box(cx, cy + 40 * s, -4, 300 * s, 300 * s, 6, (40, 120, 70), MAT_MATTE, op, R=rot_z(math.pi / 4))
        F.box(cx, cy + 40 * s, 0, 150 * s, 150 * s, 6, (150, 110, 70), MAT_MATTE, op, R=rot_z(math.pi / 4))
        n = 22
        for i in range(n):
            a = math.pi * (1.1 + 0.8 * i / (n - 1))
            for ring in range(3):
                rr = (300 + ring * 44) * s
                x, y = cx + rr * math.cos(a), cy + 120 * s + rr * math.sin(a)
                F.box(x, y, (10 + ring * 20) * s, 44 * s, 40 * s, (20 + ring * 20) * s,
                      (70 + ring * 14, 86 + ring * 14, 120 + ring * 16), MAT_PLASTIC, op, R=rot_z(a))


def scene2(t, u, D):
    p = u * PLAN[1] / D
    # 0-20 stadyum + bezelye; 20-40 bezelye -> cekirdek; 40-55 terazi; 55-70 cubuklar; 70-83 Ay; 83- kimya/nukleer
    pitch = 0.42 * (1 - smooth(seg(p, 14, 20))) * (1 - 0) + 0.0
    dolly = 1.25 - 0.25 * smooth(seg(p, 0, 6)) - 0.55 * smooth(seg(p, 15, 21)) + 0.55 * smooth(seg(p, 21, 22))
    F = Frame(t, Cam(yaw=0.06 * math.sin(p * 0.2), pitch=pitch if p < 21 else 0.05 * math.sin(p * 0.3),
                     dolly=dolly if p < 21 else 1.0 - 0.04 * math.sin(p * 0.2)))
    # stadyum (0-21)
    if p < 22:
        so = fade(p, 0, 2) * (1 - fade(p, 20, 21.5))
        stadium(F, 960, 560, 1.0, so)
        pr = 9 + 18 * smooth(seg(p, 15, 21))
        F.sphere(960, 560, 14, pr, PEA, MAT_GLOSS, alpha=so, glow=0.9, glow_col=AMBER)
        if p < 3:
            atom(F, t, 960, 560, 1.0 + p * 0.3, 1 - fade(p, 0, 2.5))
        F.spr(badge("Benzetme · ölçekli değil"), 1660, 150, op=fade(p, 2, 3) * (1 - fade(p, 19, 20)))
    # cekirdek (21-40)
    if 20 < p < 41:
        co = fade(p, 20.5, 22.5) * (1 - fade(p, 39, 40.5))
        nucleus(F, t, "N12", 960, 560, 1.6, co, plus=True, spin=0.35)
        # elektron: kucuk camgobegi nokta yorungede
        a = t * 1.4
        ex, ey = 960 + 380 * math.cos(a), 560 + 140 * math.sin(a)
        F.sphere(ex, ey, 60 * math.sin(a), 9, CYAN, MAT_GLOW, alpha=co * fade(p, 26, 27), glow=1.0)
        F.text("Proton (+)", F_SB, 42, WARM, 520, 380, op=co * fade(p, 23, 24))
        F.text("Nötron (0)", F_SB, 42, NEUT, 1400, 380, op=co * fade(p, 24.5, 25.5))
        F.text("Elektron (−)", F_SB, 42, CYAN, 960, 820, op=co * fade(p, 26, 27))
        F.spr(card(["U-235: 235 = proton + nötron"], 52), 960, 150, op=co * fade(p, 31, 32))
    # terazi proton vs elektron (40-55)
    if 39 < p < 56:
        bo = fade(p, 40, 41.5) * (1 - fade(p, 54, 55.5))
        tilt = -0.32 * ease_out_back(seg(p, 42, 44))
        balance(F, 960, 330, 400, tilt, bo)
        lx, ly = 960 - 400 * math.cos(tilt), 330 - 400 * math.sin(tilt) + 245
        rx, ry = 960 + 400 * math.cos(tilt), 330 + 400 * math.sin(tilt) + 245
        F.sphere(lx, ly - 64 + 245 * 0 - 0, 0, 52, WARM, MAT_PLASTIC, alpha=bo, glow=0.3)
        F.plus(lx, ly - 64, 0, 52, bo)
        F.sphere(rx, ry - 82, 0, 8, CYAN, MAT_GLOW, alpha=bo, glow=1.0)
        F.text("Proton", F_SB, 40, WARM, lx, ly + 70, op=bo)
        F.text("Elektron", F_SB, 40, CYAN, rx, ry + 70, op=bo)
        F.spr(card(["Elektron = protonun 1/1837'si"], 56), 960, 150, op=bo * fade(p, 44, 45))
    # hacim / kutle cubuklari (55-70)
    if 54 < p < 71:
        bo = fade(p, 55, 56.5) * (1 - fade(p, 69, 70.5))
        g = ease_out(seg(p, 57, 60))
        hmax = 400
        F.box(720, 860 - 3, 0, 160, 3, 160, CYAN, MAT_GLOW, bo)          # hacim: neredeyse gorunmez
        F.box(1200, 860 - hmax * g / 2, 0, 160, max(1, hmax * g), 160, AMBER, MAT_PLASTIC, bo, ext=(0, 0, 0, 1))
        F.text("Hacim", F_SB, 44, CYAN, 720, 910, op=bo)
        F.text("Kütle", F_SB, 44, AMBER, 1200, 910, op=bo)
        F.text("< on trilyonda bir", F_B, 44, WHITE, 720, 780, op=bo * fade(p, 58, 59))
        F.spr(card(["%" + tr_dec(99.9 * g, 1) + "+"], 60, amber=True), 1200, 860 - hmax * g - 70, op=bo * fade(p, 58, 59))
        F.text("Hacim: < on trilyonda bir", F_B, 54, WHITE, 960, 150, op=bo * fade(p, 57, 58))
        F.text("Kütle: > %99,9", F_B, 54, AMBER, 960, 220, op=bo * fade(p, 60, 61))
    # Ay -> beyzbol stadyumu (70-84)
    if 69 < p < 85:
        mo = fade(p, 70, 71.5) * (1 - fade(p, 83, 84.5))
        k = smooth(seg(p, 72, 79))
        stadium(F, 960, 620, 0.9, mo * fade(p, 73, 75), baseball=True)
        mr = 260 * (1 - k) + 10 * k
        my = 480 * (1 - k) + 650 * k
        moon(F, 960, my, 30, mr, mo, t)
        F.text("Ay", F_SB, 44, WHITE, 960 + mr + 60, my, op=mo * (1 - k))
    # kimya / nukleer (83-)
    if p > 82:
        ko = fade(p, 83, 85)
        atom(F, t, 960, 560, 1.35, ko, cloud_k=1.0 + 0.6 * fade(p, 85, 86), nuc_k=1.0 + 1.2 * fade(p, 88, 89))
        F.text("Kimya: elektronlar", F_B, 52, CYAN, 960, 150, op=ko * fade(p, 85, 86))
        F.text("Nükleer: çekirdek", F_B, 52, AMBER, 960, 225, op=ko * fade(p, 88, 89))
    return F


# ============================================================== SAHNE 3: Itisen protonlar
def scene3(t, u, D):
    p = u * PLAN[2] / D
    F = Frame(t, Cam(yaw=0.12 * math.sin(p * 0.18), pitch=-0.04 + 0.03 * math.sin(p * 0.21),
                     dolly=1.12 - 0.12 * smooth(seg(p, 0, 3)) - 0.18 * smooth(seg(p, 29, 33)) + 0.18 * smooth(seg(p, 58, 61))))
    CY = 560
    if p < 61:
        po = fade(p, 0, 1.5) * (1 - fade(p, 59, 60.5))
        sep = 150.0
        shake = 5 * math.sin(t * 37) * (1 - smooth(seg(p, 29, 31)))
        # 45-60: biri uzaklasir, bag kopar
        pull = smooth(seg(p, 47, 52)) * (1 - smooth(seg(p, 56, 58)))
        sep += 330 * pull
        xl, xr = 960 - sep / 2 - 80 * 0 + shake, 960 + sep / 2 - shake
        F.sphere(xl, CY, 0, 66, WARM, MAT_PLASTIC, alpha=po, glow=0.3)
        F.plus(xl, CY, 0, 66, po)
        F.sphere(xr, CY, 0, 66, WARM, MAT_PLASTIC, alpha=po, glow=0.3)
        F.plus(xr, CY, 0, 66, po)
        rep = po * (1 - fade(p, 30, 32) * 0.6)
        k = 0.7 + 0.3 * math.sin(t * 9)
        L = 120 + 25 * math.sin(t * 9)
        F.arrow3((xl - 90, CY, 0), (xl - 90 - L, CY, 0), 8, RED, MAT_GLOW, alpha=rep * k, head=3.0, head_len=42)
        F.arrow3((xr + 90, CY, 0), (xr + 90 + L, CY, 0), 8, RED, MAT_GLOW, alpha=rep * k, head=3.0, head_len=42)
        F.text("Aynı yükler iter", F_B, 60, WHITE, 960, 150, op=fade(p, 2, 3) * (1 - fade(p, 14, 15)))
        # 15-30: kutle cekimi vs elektrik itmesi
        go = fade(p, 15, 16.5) * (1 - fade(p, 29, 30.5))
        if go > 0:
            gk = 1 - fade(p, 23, 24.5)
            F.arrow3((760, 820, 0), (800, 820, 0), 4, (190, 200, 230), MAT_GLOW, alpha=go * gk, head=3, head_len=14)
            F.text("kütle çekimi", F_SB, 34, MUTED, 780, 880, op=go * gk)
            if 23 < p < 25:
                F.glow(780, 820, 40, AMBER, 1.2 * (1 - seg(p, 23, 25)))
            F.arrow3((900, 820, 0), (1500, 820, 0), 14, RED, MAT_GLOW, alpha=go, head=2.6, head_len=60)
            F.text("elektrik itmesi", F_SB, 34, RED, 1200, 880, op=go)
            F.text("Kütle çekimi: ihmal edilir", F_B, 56, WHITE, 960, 150, op=go * fade(p, 24, 25))
        # 30-60: guclu kuvvet baglari
        bo = fade(p, 30, 32) * (1 - fade(p, 49.5, 50.2))
        if bo > 0:
            for dz in (-22, 0, 22):
                bond(F, (xl + 50, CY + dz * 0.6, dz), (xr - 50, CY - dz * 0.6, -dz), bo, t, rad=6)
        so = fade(p, 33, 34.5) * (1 - fade(p, 45, 46.5))
        if so > 0:
            g = ease_out(seg(p, 34, 37))
            F.box(604, 880, 0, 8, 40, 40, RED, MAT_GLOW, so)
            F.text("elektromanyetik", F_SB, 34, RED, 440, 880, op=so)
            F.box(600 + 800 * g / 2, 800, 0, max(1, 800 * g), 40, 40, CYAN, MAT_GLOW, so)
            F.text("güçlü kuvvet", F_SB, 34, CYAN, 440, 800, op=so)
            F.text("Güçlü kuvvet ≈ 100 × elektromanyetik", F_B, 56, WHITE, 960, 150, op=so * fade(p, 35, 36))
        ro = fade(p, 46, 47) * (1 - fade(p, 58, 59.5))
        if ro > 0:
            # mesafe cetveli
            y0 = 760
            F.over(lambda img, a=ro, x0=xl, x1=xr: ruler(img, x0, x1, y0, a))
            if p > 50:
                F.glow(960, CY, 80, CYAN, 0.8 * (1 - seg(p, 50, 52)))
            F.text("Menzil ≈ atom çapının 1/100.000'i", F_B, 56, WHITE, 960, 150, op=ro * fade(p, 47, 48))
    # 60-70: cirt cirtli bant
    if 59 < p < 71:
        vo = fade(p, 60, 61.5) * (1 - fade(p, 69.5, 70.8))
        open_k = smooth(seg(p, 64, 66.5))
        velcro(F, t, 960, 560, open_k, vo)
        F.spr(badge("Benzetme"), 1700, 150, op=vo)
        F.text("yakın: sıkı", F_SB, 40, CYAN, 620, 820, op=vo * (1 - fade(p, 64, 65)))
        F.text("uzak: serbest", F_SB, 40, MUTED, 1300, 820, op=vo * fade(p, 66, 67))
    # 70-: cekirdek dengede
    if p > 69.5:
        no = fade(p, 70, 72)
        nucleus(F, t, "N12", 960, 560, 1.9, no, plus=True, spin=0.3, bonds=True, arrows=True, n_glow=True)
        F.text("İtme ↔ çekim dengesi", F_B, 60, WHITE, 960, 150, op=no * fade(p, 73, 74))
    return F


# ============================================================== SAHNE 4: Eksik kutle
def scene4(t, u, D):
    p = u * PLAN[3] / D
    F = Frame(t, Cam(yaw=0.25 * math.sin(p * 0.12) if p < 20 else 0.07 * math.sin(p * 0.2),
                     pitch=0.04 * math.sin(p * 0.17), dolly=1.1 - 0.1 * smooth(seg(p, 0, 3))))
    if p < 21:
        o = fade(p, 0, 1.5) * (1 - fade(p, 19.5, 21))
        apart = smooth(seg(p, 6, 16))
        nucleus(F, t, "N12", 960, 610, 1.4, o, plus=True, spin=0.25, explode=apart * 0.65)
        # disaridan iceri amber enerji akisi
        if p > 4:
            fo = o * fade(p, 4, 6)
            for i in range(28):
                a = i * 2.39996
                ph = (t * 0.45 + i * 0.137) % 1.0
                rr = 620 * (1 - ph)
                x, y = 960 + rr * math.cos(a), 580 + rr * 0.6 * math.sin(a)
                F.glow(x, y, 22, AMBER, 1.2 * fo * math.sin(ph * math.pi))
                F.sphere(x, y, 0, 5, AMBER, MAT_GLOW, alpha=fo * math.sin(ph * math.pi))
        F.text("Bağlanma enerjisi:", F_B, 56, AMBER, 960, 130, op=o * fade(p, 8, 9))
        F.text("çekirdeği parçalarına ayırmak için gereken en az enerji", F_SB, 44, WHITE, 960, 200, op=o * fade(p, 8.5, 9.5), maxw=1500)
    if 19 < p < 41:
        o = fade(p, 20, 21.5) * (1 - fade(p, 39.5, 41))
        tilt = -0.12 * ease_out_back(seg(p, 26, 28))       # sag kefe hafif yukari
        balance(F, 960, 300, 470, tilt, o)
        lx, ly = 960 - 470 * math.cos(tilt), 300 - 470 * math.sin(tilt) + 245
        rx, ry = 960 + 470 * math.cos(tilt), 300 + 470 * math.sin(tilt) + 245
        # sol: tek tek dizili parcalar
        for i in range(12):
            r_, c_ = divmod(i, 6)
            F.sphere(lx - 150 + c_ * 60, ly - 36 - r_ * 58, 0, 27, WARM if CLN12[i] else NEUT, MAT_PLASTIC, alpha=o, lo=True)
        nucleus(F, t, "N12", rx, ry - 92, 0.62, o, plus=False, spin=0.4)
        F.text("parçalar", F_SB, 40, WHITE, lx, ly + 70, op=o)
        F.text("çekirdek", F_SB, 40, WHITE, rx, ry + 70, op=o)
        F.text("Çekirdek < parçalarının toplamı", F_B, 58, WHITE, 960, 150, op=o * fade(p, 27, 28))
        do = o * fade(p, 29, 30)
        if do > 0:
            F.over(lambda img, a=do, y0=ly - 40, y1=ry - 40: dashed_gap(img, 1640, y0, y1, a))
            F.text("kütle eksiği", F_SB, 40, CYAN, 1640, (ly + ry) / 2 - 120, op=do)
    if 39 < p < 56:
        o = fade(p, 40, 41.5) * (1 - fade(p, 54.5, 56))
        nucleus(F, t, "N12", 960, 580, 1.5, o, plus=True, spin=0.3)
        k = smooth(seg(p, 41, 45))
        # kayip kutle: kucuk parilti -> amber halka
        sx, sy = 960 + 420 * (1 - k), 580 - 220 * (1 - k)
        F.glow(sx, sy, 40 + 30 * k, AMBER, o * (1 - fade(p, 45, 46)) * 1.4)
        ro = o * fade(p, 44, 46)
        F.torus(960, 580, 0, 330, 0.045, AMBER, rot_x(math.pi / 2 - 0.35) @ rot_y(t * 0.4), MAT_GLOW, ro)
        F.text("Eksik kütle = bağlanma enerjisi", F_B, 58, AMBER, 960, 150, op=o * fade(p, 46, 47))
    if 54 < p < 81:
        o = fade(p, 55, 56.5) * (1 - fade(p, 80, 81))
        F.over(lambda img, a=o, pp=p: emc2(img, a, pp))
        co = fade(p, 70, 71.5)
        F.spr(card(["1 u ≈ 931 MeV"], 72, amber=True), 960, 760, op=o * co)
        F.text("u: atomik kütle birimi", F_SB, 38, MUTED, 960, 870, op=o * co)
    if p > 79:
        o = fade(p, 80, 82)
        nucleus(F, t, "N12", 960, 600, 1.3, o, plus=True, spin=0.3)
        spring(F, t, 960, 600, 1.0 + 0.04 * math.sin(t * 7), o)
        F.spr(badge("Benzetme"), 1700, 150, op=o)
        F.text("Sıkıştırılmış yay", F_B, 56, AMBER, 960, 150, op=o * fade(p, 81, 82))
    return F


# ============================================================== SAHNE 5: Kararlilik egrisi
CH_X0, CH_X1, CH_Y0, CH_Y1 = 260, 1660, 940, 330     # grafik kutusu (A 0..240, BE/A 0..9.5)


def bea(A):
    A = np.asarray(A, float)
    rise = 8.79 * (1 - np.exp(-A / 11.0)) ** 2.2 / (1 - math.exp(-56 / 11.0)) ** 2.2
    d = A - 56
    fall = 8.79 - 0.00287 * d - 2.11e-5 * d * d
    return np.where(A < 56, rise, fall)


def chart_xy(A, v):
    return (CH_X0 + (CH_X1 - CH_X0) * A / 240.0, CH_Y0 - (CH_Y0 - CH_Y1) * v / 9.5)


def scene5(t, u, D):
    p = u * PLAN[4] / D
    F = Frame(t, Cam(yaw=0.05 * math.sin(p * 0.15), pitch=0.02 * math.sin(p * 0.2), dolly=1.05 - 0.05 * smooth(seg(p, 0, 4))))
    co = fade(p, 0, 1.5)
    grow = smooth(seg(p, 2, 14))
    F.over(lambda img, cam=F.cam, a=co, g=grow, pp=p: draw_chart(img, cam, a, g, pp))
    F.text("Kütle numarası (A)", F_SB, 36, CYAN, (CH_X0 + CH_X1) / 2, CH_Y0 + 50, op=co * fade(p, 1, 2))
    F.text("Parçacık başına bağlanma enerjisi (MeV)", F_SB, 34, CYAN, CH_X0 + 330, CH_Y1 - 45, op=co * fade(p, 1.5, 2.5) * (1 - fade(p, 52, 54)), maxw=800)
    # tepe: demir
    fe = fade(p, 20, 21.5) * (1 - fade(p, 54, 56))
    x, y = chart_xy(56, 8.79)
    if fe > 0:
        F.glow(x, y, 40, AMBER, 1.2 * fe)
        nucleus(F, t, "FE", x + 30, y + 190, 0.55, fe, plus=False, spin=0.4)
        F.spr(card([tr_dec(8.79 * ease_out(seg(p, 21, 23)), 2)], 46, amber=True), x + 230, y + 190, op=fe)
        F.text("Tepe: A = 56 (demir) ≈ 8,79 MeV", F_B, 54, AMBER, 960, 150, op=fe * (1 - fade(p, 34, 35)))
    # U-235 (sag uc)
    ux, uy = chart_xy(235, 7.6)
    uo = fade(p, 35, 36.5) * (1 - fade(p, 56, 57))
    if uo > 0:
        nucleus(F, t, "U", ux - 60, uy + 250, 0.62, uo, plus=False, spin=0.25, arrows=p > 44,
                wobble=0.03 + 0.04 * fade(p, 44, 46), stretch=smooth(seg(p, 54, 57)))
        F.glow(ux, uy, 30, CYAN, uo)
        F.spr(card(["≈ 7,6"], 46), ux + 60, uy - 60, op=uo)
        F.text("U-235 ≈ 7,6 MeV", F_B, 54, WHITE, 960, 150, op=uo * fade(p, 37, 38))
    # bolunme: Rb-93, Cs-140
    if p > 55:
        k = smooth(seg(p, 56.5, 62))
        fo = fade(p, 56, 57) * (1 - fade(p, 96, 98))
        rbx, rby = chart_xy(93, float(bea(93)))
        csx, csy = chart_xy(140, float(bea(140)))
        sx0, sy0 = ux - 60, uy + 250
        F.glow(sx0, sy0, 160 * (1 - k) + 20, AMBER, 1.6 * fo * (1 - smooth(seg(p, 57, 61))))
        nucleus(F, t, "RB", sx0 + (rbx - sx0) * k, sy0 + (rby + 190 - sy0) * k, 0.5, fo, plus=False, spin=0.35)
        nucleus(F, t, "CS", sx0 + (csx - sx0) * k, sy0 + (csy + 215 - sy0) * k, 0.5, fo, plus=False, spin=0.3)
        lo = fade(p, 61, 62) * (1 - fade(p, 96, 97.5))
        F.glow(rbx, rby, 26, CYAN, lo)
        F.glow(csx, csy, 26, CYAN, lo)
        F.spr(card(["Rb-93 · 8,7"], 38), rbx - 50, rby - 60, op=lo)
        F.spr(card(["Cs-140 · 8,4"], 38), csx + 50, csy - 60, op=lo)
    # hesap tablosu
    to = fade(p, 75, 76) * (1 - fade(p, 97, 98.5))
    if to > 0:
        rows = [("U-235: 7,6 × 235 = 1786 MeV", 76), ("Rb-93: 8,7 × 93 = 809 MeV", 78),
                ("Cs-140: 8,4 × 140 = 1176 MeV", 80), ("809 + 1176 − 1786 = 199 MeV", 83)]
        F.over(lambda img, a=to, pp=p, rows=rows: table(img, a, pp, rows))
    ao = fade(p, 88, 89) * (1 - fade(p, 97, 98.5))
    F.spr(card(["Ortalama bir fisyon ≈ 200 MeV"], 54, amber=True), 960, 150, op=ao)
    mo = fade(p, 92, 93) * (1 - fade(p, 98, 99.5))
    F.text("Kütle kaybı < %0,1", F_B, 50, WHITE, 960, 225, op=mo)
    # fuzyon (sol) + gunes
    if p > 97:
        fo = fade(p, 98, 100)
        k = smooth(seg(p, 101, 106))
        a1 = chart_xy(4, float(bea(4)))
        a1 = (a1[0] + 110, a1[1] + 120)
        F.sphere(a1[0] - 60 + 60 * k, a1[1] - 120, 0, 28, WARM, MAT_PLASTIC, alpha=fo * (1 - k * 0.5), glow=0.4)
        F.sphere(a1[0] + 60 - 60 * k, a1[1] - 120, 0, 28, NEUT, MAT_PLASTIC, alpha=fo * (1 - k * 0.5), glow=0.4)
        if k > 0.95:
            F.glow(a1[0], a1[1] - 120, 50, AMBER, 1.3 * (1 - seg(p, 106, 108)))
        sun(F, t, 1730, 250, 80, fo * 0.9)
        ar = fade(p, 108, 110)
        fx, fy = chart_xy(56, 8.79)
        F.over(lambda img, a=ar: fis_fus_arrows(img, a))
        F.text("Fisyon →  ← Füzyon", F_B, 56, WHITE, 960, 150, op=ar)
    return F


# ============================================================== SAHNE 6: Kimyasal ve nukleer
def scene6(t, u, D):
    p = u * PLAN[5] / D
    pan = smooth(seg(p, 23, 31)) * (1 - smooth(seg(p, 38, 41)))
    F = Frame(t, Cam(yaw=0.05 * math.sin(p * 0.2), dolly=1.08 - 0.08 * smooth(seg(p, 0, 3)), shift=(0, -90 * pan)))
    if p < 21:
        o = fade(p, 0, 1.5) * (1 - fade(p, 19.5, 21))
        atom(F, t, 500, 560, 1.05, o, nuc="C", cloud_k=1.2)
        if 6 < p < 9:
            F.glow(500 + 180, 520, 30, AMBER, 1.4 * math.sin(math.pi * seg(p, 6, 9)))
        nucleus(F, t, "U", 1420, 560, 0.75, o, plus=False, spin=0.25)
        if p > 9:
            b = (p - 9) % 4.0
            F.glow(1420, 560, 90 + b * 60, AMBER, o * 1.6 * math.exp(-b * 1.2))
        F.text("kimyasal", F_B, 50, CYAN, 500, 880, op=o)
        F.text("nükleer", F_B, 50, AMBER, 1420, 880, op=o)
    if 19 < p < 62:
        o = fade(p, 20, 21.5) * (1 - fade(p, 61, 62))
        g = ease_out(seg(p, 21, 30))
        base = 860
        F.box(1150, base - 2, 0, 180, 4, 110, CYAN, MAT_GLOW, o)
        hb = 1500 * g
        F.box(1640, base - hb / 2, 0, 180, max(1, hb), 110, AMBER, MAT_PLASTIC, o, ext=(0, 0, 0, 1))
        F.text("birkaç eV", F_B, 44, CYAN, 1150, base + 50, op=o)
        F.text("200.000.000 eV", F_B, 44, AMBER, 1640, base + 50, op=o)
        do = fade(p, 41, 42) * o
        F.text("Kimyasal: atom başına birkaç eV", F_B, 48, CYAN, 680, 300, op=o * fade(p, 21, 22) * (1 - do), maxw=1000)
        F.text("Fisyon: ≈ 200 MeV = 200.000.000 eV", F_B, 48, AMBER, 680, 380, op=o * fade(p, 26, 27) * (1 - do), maxw=1000)
        F.spr(card(["200.000.000 ÷ 10 = 20.000.000"], 58), 680, 560, op=do)
        F.text("Tepkime başına ≥ 20.000.000 kat", F_B, 52, WHITE, 680, 300, op=do * fade(p, 44, 45), maxw=1000)
    if p > 60:
        o = fade(p, 61, 62.5)
        # kucuk pencere: pelet + komur (gram basina)
        F.over(lambda img, a=o: window_frame(img, 330, 560, 520, 420, a))
        pellet(F, 200, 590, 0, 30, 60, rot_y(t * 0.5) @ rot_x(0.4), o, glow=0.4)
        coal_heap(F, 450, 620, 0.42, o)
        F.text("gram başına", F_B, 44, WHITE, 330, 820, op=o)
        # cubuklar: tepkime basina
        F.box(1180, 700 - 2, 0, 120, 4, 80, CYAN, MAT_GLOW, o)
        F.box(1460, 700 - 220, 0, 120, 440, 80, AMBER, MAT_PLASTIC, o, ext=(0, 0, 0, 1))
        F.text("tepkime başına", F_B, 44, WHITE, 1320, 760, op=o)
        F.text("Tepkime başına ≠ gram başına", F_B, 58, WHITE, 960, 150, op=o * fade(p, 63, 64))
        F.spr(badge("Bölüm 4: Yakıt"), 1320, 880, op=o * fade(p, 72, 73))
    return F


# ============================================================== SAHNE 7: Ozet ve kapanis
ITEMS = ["1 · Kütle çekirdekte", "2 · Güçlü kuvvet itmeyi yener", "3 · Eksik kütle = bağlanma enerjisi",
         "4 · Zirve: demir; bölünme enerji verir", "5 · Tepkime başına on milyonlarca kat"]
ITEM_T = [3, 8, 14, 20, 29]          # plan saniyesi (madde soylendiginde)


def scene7(t, u, D):
    p = u * PLAN[6] / D
    end0 = (TOTAL - 18.0 - STARTS[6]) * PLAN[6] / D     # son ~18 sn: bitis karti
    F = Frame(t, Cam(yaw=0.10 * math.sin(p * 0.12) - 0.06, pitch=-0.03, dolly=1.05 - 0.05 * smooth(seg(p, 0, 4)),
                     shift=(-120 + 240 * smooth(seg(p, 0, 34)), 0)))
    if p < 37:
        o = fade(p, 0, 1.5) * (1 - fade(p, 35.5, 37))
        for i in range(5):
            cx = 960 + (i - 2) * 350
            act = fade(p, ITEM_T[i], ITEM_T[i] + 0.8) * (1 - fade(p, (ITEM_T + [34])[i + 1] - 0.3, (ITEM_T + [34])[i + 1] + 0.5))
            lift = -40 * act
            shelf_card(F, t, i, cx, 560 + lift, o, act)
            F.text(ITEMS[i].split(" · ")[0], F_B, 40, CYAN if act > 0.5 else MUTED, cx, 800, op=o)
        F.box(960, 760, -40, 1800, 18, 160, (40, 56, 96), MAT_MATTE, o)        # raf
        for i in range(5):
            a = fade(p, ITEM_T[i], ITEM_T[i] + 0.6) * (1 - fade(p, (ITEM_T + [34])[i + 1] - 0.4, (ITEM_T + [34])[i + 1]))
            F.text(ITEMS[i], F_B, 58, WHITE, 960, 160, op=o * a, maxw=1500)
    if 35 < p < 47:
        o = fade(p, 36, 37.5) * (1 - fade(p, 46, 47))
        nucleus(F, t, "N12", 960, 600, 1.3, o, plus=True, spin=0.3)
        spring(F, t, 960, 600, 1.0 + 0.04 * math.sin(t * 7), o, bright=1.6)
        F.spr(badge("Benzetme"), 1700, 150, op=o)
        F.text("Bağlarda saklı enerji", F_B, 60, AMBER, 960, 150, op=o * fade(p, 37, 38))
    if 45.5 < p < end0 + 1:
        o = fade(p, 46, 47.5) * (1 - fade(p, end0, end0 + 0.8))
        k = smooth(seg(p, 47, 51.5))      # notron yaklasir; carpmadan once donar
        nucleus(F, t if p < 51.5 else STARTS[6] + 51.5 * D / PLAN[6], "U", 1100, 560, 0.85, o, plus=False, spin=0.2)
        nx = 200 + (1100 - 330 - 200) * k
        F.sphere(nx, 560, 0, 30, NEUT, MAT_PLASTIC, alpha=o, glow=0.5, glow_col=CYAN)
        F.spr(card(["Soru: Demir neden önemli?"], 54), 960, 150, op=o * fade(p, end0 - 9, end0 - 8))
    if p > end0 - 0.5:
        end_card(F, t, fade(p, end0, end0 + 1.0), p - end0)
    return F


def draw_chart(img, cam, a, g, p):
    draw_chart_base(img, cam, a, g, bea, chart_xy, CH_X0, CH_X1, CH_Y0, CH_Y1)


def table(img, a, p, rows):
    table_panel(img, a, p, rows, cy=560)


def fis_fus_arrows(img, a):
    if a <= 0:
        return
    ov = img.copy()
    for A0, A1, col in ((230, 70, AMBER), (6, 48, CYAN)):
        As = np.linspace(A0, A1, 60)
        pts = np.array([chart_xy(A, float(bea(A)) + 0.9) for A in As], np.int32)
        cv2.polylines(ov, [pts[:-4]], False, col, 6, cv2.LINE_AA)
        cv2.arrowedLine(ov, tuple(int(v) for v in pts[-8]), tuple(int(v) for v in pts[-1]), col, 6, cv2.LINE_AA, tipLength=0.9)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)
    blit(img, T("fisyon", F_SB, 40, AMBER), chart_xy(170, 9.3)[0], chart_xy(170, 9.3)[1] - 20, op=a)
    blit(img, T("füzyon", F_SB, 40, CYAN), chart_xy(16, 9.3)[0], chart_xy(16, 9.3)[1] - 40, op=a)


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7]


def frame(t):
    # sahne pencereleri: sinirlar = sonraki sahnenin baslangici - GAP/2
    bounds = [STARTS[k] - GAP / 2 for k in range(1, 7)]
    k = sum(1 for b in bounds if t >= b)
    XF = 0.55
    img = None
    for b_i, b in enumerate(bounds):
        if abs(t - b) < XF:
            w = smooth((t - (b - XF)) / (2 * XF))
            a = finish(SCENES[b_i](t, t - STARTS[b_i], DURS[b_i]))
            c = finish(SCENES[b_i + 1](t, t - STARTS[b_i + 1], DURS[b_i + 1]))
            img = mix(a, c, w)
            break
    if img is None:
        img = finish(SCENES[k](t, t - STARTS[k], DURS[k]))
    corner_tag(img, TAG, fade(t, 0.3, 1.2) * (1 - fade(t, TOTAL - 18.5, TOTAL - 17.5) * 0.0))
    # bitis
    img = (img.astype(np.float32) * (1 - fade(t, TOTAL - 0.8, TOTAL) * 0.85)).astype(np.uint8)
    return img


def finish(F):
    return F.finish(grain_on=False)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "still":
        os.makedirs(os.path.join(WORK, "kareler"), exist_ok=True)
        for a in sys.argv[2:]:
            Image.fromarray(frame(float(a))).save(os.path.join(WORK, "kareler", "k_%06.2f.png" % float(a)))
    elif mode == "render":
        render_long("bolum01", NFRAMES, WORK, workers=int(os.environ.get("WORKERS", "4")))
