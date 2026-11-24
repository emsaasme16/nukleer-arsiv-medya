#!/usr/bin/env python3
"""60 saniyede: Atomun kutlesi nerede? - 9:16 animasyon (1080x1920, 30 fps, 40 sn)

Kullanim:
  render.py still 0.8 3.0 ...     -> out/still_<t>.png
  render.py chunk <start> <end>   -> out/chunk_<start>_<end>.mp4
  render.py all                   -> tum parcalar + birlestirme
"""
import sys, math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
DUR = 38.2
GW, GH = W // 4, H // 4
CX, CY = 540, 900
OUT = "/home/claude/short1/out"
import tl3 as tl

F_B = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
F_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

NAVY0 = (5, 10, 30)
NAVY1 = (12, 28, 72)
CYAN = (53, 224, 255)
BLUE = (45, 168, 255)
AMBER = (255, 181, 71)
WHITE = (242, 247, 255)
MUTED = (140, 158, 192)
PEA = (124, 216, 64)
WARM = (255, 130, 70)

# ----------------------------------------------------------------- yardimcilar
def clamp01(x):
    return max(0.0, min(1.0, x))

def seg(t, a, b):
    return clamp01((t - a) / (b - a))

def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)

def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3

def ease_out_back(x):
    x = clamp01(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def fade(t, a, b):
    return smooth(seg(t, a, b))

def scol(c, k):
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))

# ----------------------------------------------------------------- arka plan
def make_bg():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.array(NAVY0, np.float32)[None, None, :]
    bot = np.array(NAVY1, np.float32)[None, None, :]
    g = top * (1 - y) + bot * y
    g = np.repeat(g, W, axis=1)
    xs = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    ys = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    r = np.sqrt(xs ** 2 * 0.6 + ys ** 2 * 0.35)
    v = 1 - 0.38 * np.clip(r, 0, 1.3) ** 2
    g = g * v[..., None]
    halo = np.exp(-((xs * 1.0) ** 2 + ((ys - 0.0) * 0.55) ** 2) * 3.2) * 20
    g[..., 2] += halo
    g[..., 1] += halo * 0.35
    return np.clip(g, 0, 255).astype(np.uint8)

BG = make_bg()
rng = np.random.default_rng(7)
STARS = [(int(rng.uniform(0, W)), int(rng.uniform(0, H)), int(rng.choice([1, 1, 2])),
          rng.uniform(0, 6.28), rng.uniform(0.6, 2.2)) for _ in range(150)]

def base(t):
    img = BG.copy()
    for (x, y, r, ph, rate) in STARS:
        a = 0.30 + 0.70 * (0.5 + 0.5 * math.sin(t * rate + ph))
        cv2.circle(img, (x, y), r, scol((190, 215, 255), a * 0.75), -1, cv2.LINE_AA)
    return img

def newgl():
    return np.zeros((GH, GW, 3), np.uint8)

def gcircle(gl, cx, cy, r, color, k=1.0, thick=-1):
    cv2.circle(gl, (int(cx / 4), int(cy / 4)), max(1, int(r / 4)), scol(color, k), thick, cv2.LINE_AA)

def apply_glow(img, gl, sigma=9, gain=1.0):
    g = cv2.GaussianBlur(gl, (0, 0), sigma)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    if gain != 1.0:
        g = cv2.convertScaleAbs(g, alpha=gain)
    cv2.add(img, g, dst=img)

# ----------------------------------------------------------------- sprite'lar
_cache = {}

def T(txt, fontpath, size, color, maxw=940):
    """Golge verilmis, premultiplied metin sprite'i; maxw'ye sigmasi icin kuculur."""
    key = (txt, fontpath, size, color, maxw)
    if key in _cache:
        return _cache[key]
    s = size
    while True:
        font = ImageFont.truetype(fontpath, s)
        if font.getlength(txt) <= maxw or s <= 20:
            break
        s -= 2
    bbox = font.getbbox(txt)
    pad = 18
    w = int(bbox[2] - bbox[0]) + 2 * pad
    h = int(bbox[3] - bbox[1]) + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - bbox[0], pad - bbox[1]), txt, font=font, fill=tuple(color) + (255,))
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    sh = cv2.GaussianBlur(a, (0, 0), 6) * 0.65
    out_a = np.clip(a + sh * (1 - a), 0, 1)
    rgb = arr[..., :3] * a[..., None]
    spr = (rgb.astype(np.float32), out_a.astype(np.float32))
    _cache[key] = spr
    return spr

def pill(txt, fontpath, size, color, border, maxw=700, padx=34, pady=18, fill=(8, 16, 40), fill_a=0.88):
    key = ("pill", txt, fontpath, size, color, border, maxw, padx, pady)
    if key in _cache:
        return _cache[key]
    font = ImageFont.truetype(fontpath, size)
    bbox = font.getbbox(txt)
    tw = int(bbox[2] - bbox[0])
    th = int(bbox[3] - bbox[1])
    w = tw + 2 * padx + 8
    h = th + 2 * pady + 8
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4 * S, 4 * S, (w - 4) * S, (h - 4) * S), radius=(h - 8) * S // 2,
                        fill=tuple(fill) + (int(255 * fill_a),), outline=tuple(border) + (255,), width=3 * S)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.text((4 + padx - bbox[0], 4 + pady - bbox[1]), txt, font=font, fill=tuple(color) + (255,))
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    rgb = arr[..., :3] * a[..., None]
    spr = (rgb.astype(np.float32), a.astype(np.float32))
    _cache[key] = spr
    return spr

def sphere_sprite(base_col, d, rim=None, spec=0.55):
    ys, xs = np.mgrid[0:d, 0:d].astype(np.float32)
    x = (xs - (d - 1) / 2) / (d / 2)
    y = (ys - (d - 1) / 2) / (d / 2)
    r2 = x * x + y * y
    inside = r2 <= 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    L = np.array([-0.45, -0.55, 0.7], np.float32)
    L /= np.linalg.norm(L)
    diff = np.clip(x * L[0] + y * L[1] + z * L[2], 0, 1)
    Hh = L + np.array([0, 0, 1], np.float32)
    Hh /= np.linalg.norm(Hh)
    sp = np.clip(x * Hh[0] + y * Hh[1] + z * Hh[2], 0, 1) ** 48
    bc = np.array(base_col, np.float32)
    col = bc[None, None, :] * (0.28 + 0.85 * diff[..., None])
    col = col + sp[..., None] * 255 * spec
    rimc = (1 - z) ** 3
    col = col + rimc[..., None] * (np.array(rim if rim else base_col, np.float32) * 0.55)
    col = np.clip(col, 0, 255)
    edge = np.clip((1 - np.sqrt(r2)) * d / 2, 0, 1)
    a = edge * inside
    rgb = col * a[..., None]
    return rgb.astype(np.float32), a.astype(np.float32)

PEA_SPR = sphere_sprite(PEA, 600, rim=(190, 255, 120))
PROTON_SPR = sphere_sprite(WARM, 400, rim=(255, 210, 120), spec=0.5)
NUC_SPR = sphere_sprite(AMBER, 400, rim=(255, 235, 150), spec=0.6)

def blit(img, spr, cx, cy, op=1.0, scale=1.0):
    if op <= 0.003:
        return
    rgb, a = spr
    if abs(scale - 1.0) > 1e-3:
        nw = max(1, int(rgb.shape[1] * scale))
        nh = max(1, int(rgb.shape[0] * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        rgb = cv2.resize(rgb, (nw, nh), interpolation=interp)
        a = cv2.resize(a, (nw, nh), interpolation=interp)
    h, w = a.shape
    x0 = int(round(cx - w / 2))
    y0 = int(round(cy - h / 2))
    sx0 = max(0, -x0)
    sy0 = max(0, -y0)
    ex = min(w, W - x0)
    ey = min(h, H - y0)
    if ex <= sx0 or ey <= sy0:
        return
    region = img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32)
    aa = (a[sy0:ey, sx0:ex] * op)[..., None]
    region = region * (1 - aa) + rgb[sy0:ey, sx0:ex] * op
    img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = np.clip(region, 0, 255).astype(np.uint8)

def text_in(img, txt, fontpath, size, color, cx, cy, t, t0, dur=0.6, rise=36, maxw=940, op=1.0):
    """Asagidan yukari kayarak belirir."""
    p = ease_out(seg(t, t0, t0 + dur))
    if p <= 0:
        return
    blit(img, T(txt, fontpath, size, color, maxw), cx, cy + (1 - p) * rise, op=p * op)

# ----------------------------------------------------------------- elektron bulutu
NP = 1100
P_R = 28 + 68 * rng.beta(2.2, 1.6, NP)
P_TH = rng.uniform(0, 2 * math.pi, NP)
P_OM = rng.uniform(0.05, 0.18, NP) * rng.choice([-1, 1], NP)
P_PH = rng.uniform(0, 6.28, NP)
P_RATE = rng.uniform(0.8, 3.0, NP)
P_SZ = rng.choice([2, 2, 2, 3], NP)
P_GLOW = rng.uniform(0, 1, NP) < 0.35

def draw_cloud(img, gl, t, z, op):
    if op <= 0.01:
        return
    ang = P_TH + P_OM * t
    px = CX + P_R * z * np.cos(ang)
    py = CY + P_R * z * np.sin(ang)
    vis = np.nonzero((px > -6) & (px < W + 6) & (py > -6) & (py < H + 6))[0]
    al = (0.40 + 0.60 * (0.5 + 0.5 * np.sin(t * P_RATE + P_PH))) * op
    for i in vis:
        k = float(al[i])
        c = scol(CYAN if i % 3 else BLUE, k)
        cv2.circle(img, (int(px[i]), int(py[i])), int(P_SZ[i]), c, -1, cv2.LINE_AA)
        if P_GLOW[i]:
            cv2.circle(gl, (int(px[i] / 4), int(py[i] / 4)), 1, scol(CYAN, 0.8 * k), -1, cv2.LINE_AA)

# ----------------------------------------------------------------- stadyum
def draw_stadium(img, gl, z, op):
    if op <= 0.003:
        return
    ov = img.copy()
    c = (CX, CY)
    th = int(np.clip(0.12 * z, 2, 8))

    def ax(a, b):
        return (max(1, int(a * z)), max(1, int(b * z)))

    cv2.ellipse(ov, c, ax(60, 40), 0, 0, 360, (18, 52, 118), -1, cv2.LINE_AA)
    for k in range(36):
        ang = 2 * math.pi * k / 36
        p1 = (int(CX + 47 * z * math.cos(ang)), int(CY + 29 * z * math.sin(ang)))
        p2 = (int(CX + 60 * z * math.cos(ang)), int(CY + 40 * z * math.sin(ang)))
        cv2.line(ov, p1, p2, (36, 90, 176), max(1, int(0.14 * z)), cv2.LINE_AA)
    cv2.ellipse(ov, c, ax(47, 29), 0, 0, 360, (8, 20, 50), -1, cv2.LINE_AA)
    # saha
    x0, x1 = int(CX - 38 * z), int(CX + 38 * z)
    y0, y1 = int(CY - 21 * z), int(CY + 21 * z)
    cv2.rectangle(ov, (x0, y0), (x1, y1), (12, 80, 60), -1)
    n = 10
    sw = (x1 - x0) / n
    for k in range(0, n, 2):
        cv2.rectangle(ov, (int(x0 + k * sw), y0), (int(x0 + (k + 1) * sw), y1), (16, 96, 72), -1)
    ln = (205, 232, 238)
    cv2.rectangle(ov, (x0, y0), (x1, y1), ln, th, cv2.LINE_AA)
    cv2.line(ov, (CX, y0), (CX, y1), ln, th, cv2.LINE_AA)
    cv2.circle(ov, c, max(1, int(6 * z)), ln, th, cv2.LINE_AA)
    for sgn in (-1, 1):
        bx = int(CX + sgn * 38 * z)
        bx2 = int(CX + sgn * 28 * z)
        cv2.rectangle(ov, (min(bx, bx2), int(CY - 11 * z)), (max(bx, bx2), int(CY + 11 * z)), ln, th, cv2.LINE_AA)
    cv2.ellipse(ov, c, ax(47, 29), 0, 0, 360, (60, 130, 200), th, cv2.LINE_AA)
    cv2.ellipse(ov, c, ax(60, 40), 0, 0, 360, CYAN, th, cv2.LINE_AA)
    cv2.addWeighted(ov, op, img, 1 - op, 0, img)
    cv2.ellipse(gl, (CX // 4, CY // 4), (max(1, int(60 * z / 4)), max(1, int(40 * z / 4))), 0, 0, 360,
                scol(CYAN, 0.55 * op), 2, cv2.LINE_AA)

# ----------------------------------------------------------------- sahne AB (0-14 sn)
Z0, Z1 = 90.0, 4.4
ZT0, ZT1 = 5.0, 12.4

def zoom_z(t):
    p = smooth(seg(t, ZT0, ZT1))
    return Z0 * (Z1 / Z0) ** p

def series_tag(img, t):
    blit(img, pill("NÜKLEER ARŞİV", F_SB, 30, CYAN, CYAN, padx=30, pady=12, fill_a=0.55), 540, 212,
         op=fade(t, 0.1, 0.7))

def scene_AB(t):
    img = base(t)
    gl = newgl()
    z = zoom_z(t)
    # stadyum ve bulut yakinlasma ile belirir
    draw_stadium(img, gl, z, fade(t, 5.4, 8.4))
    draw_cloud(img, gl, t, z, 1.0 if t > 5.0 else 0.0)
    if t > 9.0:
        # bulut siniri
        r = int(96 * z)
        cv2.ellipse(img, (CX, CY), (r, r), 0, 0, 360, scol((70, 130, 200), 0.55 * fade(t, 9.0, 10.5)), 2, cv2.LINE_AA)
    # bezelye
    pop = ease_out_back(seg(t, 0.2, 0.9)) if t < 5.0 else 1.0
    bob = 6 * math.sin(t * 2.2) if t < 5.0 else 0.0
    pr = z * 1.0
    scale = (pr / 300.0) * pop
    pea_y = CY + bob
    gr = max(pr * 1.9, 20)
    pulse = 0.8 + 0.2 * math.sin(t * 3.0)
    gcircle(gl, CX, pea_y, gr, PEA, 0.55 * pulse * (fade(t, 0.2, 1.0)))
    blit(img, PEA_SPR, CX, pea_y, op=1.0, scale=scale)
    # isaret halkasi
    ring = fade(t, 10.8, 11.6)
    if ring > 0:
        rr = 24 + 3 * math.sin(t * 5)
        cv2.circle(img, (CX, CY), int(rr), scol(PEA, ring), 3, cv2.LINE_AA)
        gcircle(gl, CX, CY, rr, PEA, 0.6 * ring, thick=2)
    # A: kanca metinleri
    ex = 1 - fade(t, 5.0, 5.7)
    if ex > 0:
        text_in(img, "ÇEKİRDEK", F_B, 128, CYAN, 540, 330, t, 0.15, op=ex)
        text_in(img, "BİR BEZELYE", F_B, 128, WHITE, 540, 468, t, 0.5, op=ex)
        text_in(img, "OLSAYDI…", F_B, 78, MUTED, 540, 588, t, 0.95, op=ex)
    # B: baslik
    tb = fade(t, 9.2, 10.0)
    if tb > 0:
        blit(img, T("ELEKTRONLARIN ALANI", F_B, 76, CYAN), 540, 318 + (1 - tb) * 20, op=tb)
        blit(img, T("BİR STADYUMDAN BÜYÜK", F_B, 76, WHITE), 540, 408 + (1 - tb) * 20, op=tb)
    # etiketler
    lab = fade(t, 11.2, 12.0)
    if lab > 0:
        blit(img, pill("STADYUM", F_SB, 32, WHITE, (90, 150, 220), padx=26, pady=10), 540, int(CY - 40 * Z1 - 36), op=lab)
        blit(img, pill("ELEKTRON BULUTU", F_SB, 32, CYAN, CYAN, padx=26, pady=10), 540, int(CY + 96 * Z1 + 42), op=lab)
    pl = fade(t, 11.5, 12.3)
    if pl > 0:
        cv2.line(img, (CX, CY + 30), (CX, 1180), scol(PEA, pl), 2, cv2.LINE_AA)
        cv2.circle(img, (CX, CY + 30), 4, scol(PEA, pl), -1, cv2.LINE_AA)
        blit(img, pill("ÇEKİRDEK = BEZELYE", F_B, 44, PEA, PEA, padx=34, pady=16), 540, 1222, op=pl)
    nt = fade(t, 12.0, 12.8)
    if nt > 0:
        blit(img, T("ŞEMATİK · ÖLÇEKLİ DEĞİL", F_M, 30, MUTED), 540, 1470, op=0.85 * nt)
    series_tag(img, t)
    apply_glow(img, gl)
    return img

# ----------------------------------------------------------------- sahne C (14-24 sn)
BAR_X, BAR_Y, BAR_W, BAR_H = 80, 1066, 920, 110

def rrect_mask(w, h, r):
    m = np.zeros((h, w), np.float32)
    S = 4
    big = np.zeros((h * S, w * S), np.uint8)
    cv2.rectangle(big, (r * S, 0), (w * S - r * S, h * S), 255, -1)
    cv2.rectangle(big, (0, r * S), (w * S, h * S - r * S), 255, -1)
    for (cx, cy) in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(big, (cx * S, cy * S), r * S, 255, -1, cv2.LINE_AA)
    m = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return m

BAR_MASK = rrect_mask(BAR_W, BAR_H, 28)
_cn, _ = cv2.findContours((BAR_MASK > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
BAR_CONTOUR = max(_cn, key=cv2.contourArea) + np.array([BAR_X, BAR_Y])
_gx = np.linspace(0, 1, BAR_W, dtype=np.float32)[None, :, None]
_gy = np.linspace(0, 1, BAR_H, dtype=np.float32)[:, None, None]
_c0 = np.array((255, 214, 120), np.float32)
_c1 = np.array((255, 150, 40), np.float32)
BAR_GRAD = (_c0 * (1 - _gx) + _c1 * _gx) * (1.12 - 0.34 * _gy)
BAR_GRAD = np.clip(BAR_GRAD, 0, 255)

def draw_bar(img, frac, sliver_op):
    y0, y1 = BAR_Y, BAR_Y + BAR_H
    x0, x1 = BAR_X, BAR_X + BAR_W
    reg = img[y0:y1, x0:x1].astype(np.float32)
    bgc = np.array((10, 24, 60), np.float32)
    m = BAR_MASK[..., None]
    reg = reg * (1 - m) + bgc * m
    fw = int(BAR_W * frac)
    if fw > 0:
        fm = np.zeros((BAR_H, BAR_W, 1), np.float32)
        fm[:, :fw] = BAR_MASK[:, :fw, None]
        reg = reg * (1 - fm) + BAR_GRAD * fm
    img[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
    # dis cizgi
    cv2.polylines(img, [BAR_CONTOUR], True, (80, 135, 205), 2, cv2.LINE_AA)
    if sliver_op > 0:
        cv2.rectangle(img, (x0 + int(BAR_W * 0.99), y0 + 6), (x1 - 6, y1 - 6), scol(CYAN, sliver_op), -1)

def scene_C(t):
    img = base(t)
    gl = newgl()
    lt = max(0.0, t - 14.0)
    # buyuk soru
    bo = 1 - fade(lt, 2.3, 2.9)
    pop = ease_out_back(seg(lt, 0.4, 1.0))
    if bo > 0 and pop > 0:
        sc = 0.85 + 0.15 * pop
        blit(img, T("PEKİ ATOMUN", F_B, 112, WHITE), 540, 790, op=min(1, pop) * bo, scale=sc)
        blit(img, T("KÜTLESİ NEREDE?", F_B, 112, AMBER), 540, 930, op=min(1, pop) * bo, scale=sc)
        gcircle(gl, 540, 860, 300, AMBER, 0.08 * min(1, pop) * bo)
    # sayac
    cp = fade(lt, 2.9, 3.5)
    if cp > 0:
        blit(img, T("ATOMUN KÜTLESİNİN", F_SB, 48, MUTED), 540, 520, op=cp)
        p = ease_out(seg(lt, 3.2, 6.2))
        n = int(round(99 * p))
        done = lt >= 6.2
        txt = "%99+" if done else "%" + str(n)
        sc = 1.0
        if done:
            sc = 1.0 + 0.10 * math.sin(math.pi * clamp01((lt - 6.2) / 0.5)) if lt < 6.7 else 1.0
        gcircle(gl, 540, 760, 230, AMBER, 0.08 + 0.22 * p)
        blit(img, T(txt, F_B, 330, AMBER, maxw=900), 540, 760, op=cp, scale=sc)
        draw_bar(img, min(1.0, p) * 0.99, fade(lt, 6.8, 7.4))
        gcircle(gl, 540, BAR_Y + BAR_H // 2, 120, AMBER, 0.10 + 0.25 * p)
    cc = fade(lt, 6.3, 7.0)
    if cc > 0:
        blit(img, T("ÇEKİRDEKTE", F_B, 100, WHITE), 540, 950 + (1 - cc) * 20, op=cc)
    lb = fade(lt, 6.9, 7.6)
    if lb > 0:
        blit(img, T("ÇEKİRDEK", F_B, 44, AMBER, maxw=420), 80 + 150, 1255, op=lb)
        blit(img, T("%99'DAN FAZLA", F_SB, 36, WHITE, maxw=420), 80 + 150, 1310, op=lb)
        blit(img, T("ELEKTRONLAR", F_B, 44, CYAN, maxw=420), 1000 - 160, 1255, op=lb)
        blit(img, T("%1'DEN AZ", F_SB, 36, WHITE, maxw=420), 1000 - 160, 1310, op=lb)
        cv2.line(img, (BAR_X + BAR_W - 5, BAR_Y + BAR_H), (BAR_X + BAR_W - 5, 1226), scol(CYAN, lb), 2, cv2.LINE_AA)
    series_tag(img, t)
    apply_glow(img, gl)
    return img

# ----------------------------------------------------------------- sahne D (24-33 sn)
COLS, ROWS, SP = 51, 36, 13
GX0 = 540 - (COLS - 1) * SP / 2
GY0 = 1234 - (ROWS - 1) * SP / 2
DOTS = [(GX0 + c * SP, GY0 + r * SP) for r in range(ROWS) for c in range(COLS)]
NTOT = COLS * ROWS  # 1836

def scene_D(t):
    img = base(t)
    gl = newgl()
    lt = max(0.0, t - 24.0)
    text_in(img, "1 PROTON KAÇ", F_B, 76, WHITE, 540, 318, lt, 0.4)
    text_in(img, "ELEKTRON AĞIRLIĞINDA?", F_B, 76, CYAN, 540, 410, lt, 0.8)
    # proton
    pp = ease_out_back(seg(lt, 1.3, 2.1))
    if pp > 0.02:
        pulse = 0.85 + 0.15 * math.sin(lt * 3.2)
        gcircle(gl, 540, 610, 180, WARM, 0.55 * pulse * min(1, pp))
        blit(img, PROTON_SPR, 540, 610, op=min(1, pp), scale=(88 / 200.0) * pp)
        cv2.line(img, (540 - 22, 610), (540 + 22, 610), scol(WHITE, min(1, pp)), 6, cv2.LINE_AA)
        cv2.line(img, (540, 610 - 22), (540, 610 + 22), scol(WHITE, min(1, pp)), 6, cv2.LINE_AA)
        blit(img, T("1 PROTON", F_B, 44, AMBER), 540, 722, op=min(1, pp))
    # elektron noktalari
    prog = smooth(seg(lt, 3.0, 7.0))
    n = int(round(NTOT * prog))
    gd = fade(lt, 2.4, 3.0)
    for k, (x, y) in enumerate(DOTS):
        if k < n:
            cv2.circle(img, (int(x), int(y)), 4, CYAN, -1, cv2.LINE_AA)
        elif gd > 0:
            cv2.circle(img, (int(x), int(y)), 2, scol((60, 90, 150), gd * 0.9), -1, cv2.LINE_AA)
    if 0 < n < NTOT:
        r_cur = (n - 1) // COLS
        for c in range(COLS):
            k = r_cur * COLS + c
            if k < n:
                x, y = DOTS[k]
                cv2.circle(img, (int(x), int(y)), 5, WHITE, -1, cv2.LINE_AA)
        gcircle(gl, 540, GY0 + r_cur * SP, 90, CYAN, 0.30)
    # sayac
    if gd > 0:
        done = lt >= 7.0
        txt = "≈ %d" % n
        sc = 1.0
        if done and lt < 7.5:
            sc = 1.0 + 0.10 * math.sin(math.pi * clamp01((lt - 7.0) / 0.5))
        gcircle(gl, 540, 845, 150, CYAN, 0.10 + 0.20 * prog)
        blit(img, T(txt, F_B, 150, CYAN, maxw=760), 540, 845, op=gd, scale=sc)
        blit(img, T("ELEKTRON KÜTLESİ", F_SB, 40, MUTED), 540, 925, op=gd)
        blit(img, T("HER NOKTA = 1 ELEKTRON", F_M, 30, MUTED), 540, 972, op=gd * 0.9)
    series_tag(img, t)
    apply_glow(img, gl)
    return img

# ----------------------------------------------------------------- sahne E (yeni zaman: 25.4 - 39.0)
def scene_E(t):
    img = base(t)
    gl = newgl()
    lt = max(0.0, t - tl.E0)
    NX, NY = 540, 860
    nuc_p = ease_out_back(seg(lt, 0.2, 0.9))
    pulse = 1 + 0.06 * math.sin(lt * 4.0)
    strong = fade(lt, 8.2, 8.8)
    orbs = [(300, 110, 20), (360, 150, -35), (250, 190, 70)]
    for i, (rx, ry, rot) in enumerate(orbs):
        o = fade(lt, 0.5 + 0.15 * i, 1.2 + 0.15 * i)
        if o <= 0:
            continue
        cv2.ellipse(img, (NX, NY), (rx, ry), rot, 0, 360, scol((70, 120, 190), 0.55 * o), 2, cv2.LINE_AA)
        a = lt * (1.1 + 0.4 * i) + i * 2.1
        ex = rx * math.cos(a)
        ey = ry * math.sin(a)
        cr = math.radians(rot)
        px = NX + ex * math.cos(cr) - ey * math.sin(cr)
        py = NY + ex * math.sin(cr) + ey * math.cos(cr)
        gcircle(gl, px, py, 46, CYAN, 0.9 * o)
        cv2.circle(img, (int(px), int(py)), 11, scol(CYAN, o), -1, cv2.LINE_AA)
    if nuc_p > 0.02:
        gcircle(gl, NX, NY, 230 * pulse, AMBER, (0.45 + 0.4 * strong) * min(1, nuc_p))
        blit(img, NUC_SPR, NX, NY, op=min(1, nuc_p), scale=(62 / 200.0) * nuc_p * pulse * (1 + 0.15 * strong))
    RS = 8.3
    if lt > RS:
        for k in range(3):
            if lt - RS - k * 0.53 < 0:
                continue
            q = ((lt - RS) / 1.6 - k / 3.0) % 1.0
            rr = 70 + 250 * q
            op = (1 - q) * 0.9
            cv2.circle(img, (NX, NY), int(rr), scol(AMBER, op), 3, cv2.LINE_AA)
            gcircle(gl, NX, NY, rr, AMBER, 0.5 * op, thick=2)
    ko = 1 - fade(lt, 6.4, 6.9)
    if ko > 0:
        text_in(img, "ODUN YANAR, DEMİR PASLANIR", F_B, 54, WHITE, 540, 300, lt, 2.5, op=ko)
        text_in(img, "BUNLAR ELEKTRONLARIN İŞİ", F_B, 54, CYAN, 540, 372, lt, 4.6, op=ko)
    text_in(img, "NÜKLEER ENERJİ", F_B, 88, AMBER, 540, 1190, lt, 6.9)
    text_in(img, "ÇEKİRDEKTEN GELİR", F_B, 88, WHITE, 540, 1292, lt, 8.3)
    ec = fade(lt, 10.8, 11.4)
    if ec > 0:
        apply_glow(img, gl)
        clean = base(t)
        img = cv2.addWeighted(clean, ec, img, 1 - ec, 0)
        gl = newgl()
        blit(img, T("KAYNAKLAR", F_B, 48, CYAN), 540, 700, op=ec)
        blit(img, T("NIST CODATA · proton/elektron kütle oranı ≈ 1836", F_M, 32, WHITE, maxw=980), 540, 790, op=fade(lt, 11.0, 11.6))
        blit(img, T("Windows to the Universe (UCAR) · kütlenin >%99'u çekirdekte", F_M, 32, WHITE, maxw=980), 540, 850, op=fade(lt, 11.2, 11.8))
        blit(img, T("Windows to the Universe · bezelye-stadyum ölçeği", F_M, 32, WHITE, maxw=980), 540, 910, op=fade(lt, 11.3, 11.9))
        blit(img, T("ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL", F_SB, 30, MUTED, maxw=980), 540, 1010, op=fade(lt, 11.4, 12.0))
        blit(img, T("DEVAMI KANALDA · BÖLÜM 1", F_B, 52, AMBER, maxw=980), 540, 1160, op=fade(lt, 11.6, 12.2))
    series_tag(img, t)
    apply_glow(img, gl)
    return img

# ----------------------------------------------------------------- birlestirme
def mix(a, b, w):
    return cv2.addWeighted(a, 1 - w, b, w, 0)

def frame(T):
    a = lambda: scene_AB(tl.pw(T, tl.INV_AB))
    c = lambda: scene_C(tl.pw(T, tl.INV_C))
    d = lambda: scene_D(tl.pw(T, tl.INV_D))
    e = lambda: scene_E(T)
    (b1, h), (b2, _), (b3, _) = tl.XF
    if abs(T - b1) <= h:
        return mix(a(), c(), smooth((T - (b1 - h)) / (2 * h)))
    if abs(T - b2) <= h:
        return mix(c(), d(), smooth((T - (b2 - h)) / (2 * h)))
    if abs(T - b3) <= h:
        return mix(d(), e(), smooth((T - (b3 - h)) / (2 * h)))
    if T < b1:
        return a()
    if T < b2:
        return c()
    if T < b3:
        return d()
    return e()

def save_png(img, path):
    Image.fromarray(img).save(path)

def render_chunk(s, e):
    i0, i1 = int(round(s * FPS)), int(round(e * FPS))
    tmp = os.path.join(OUT, "tmp_v3_chunk_%g_%g.mp4" % (s, e))
    dst = os.path.join(OUT, "v3_chunk_%g_%g.mp4" % (s, e))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", "30", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        img = frame(i / FPS)
        p.stdin.write(np.ascontiguousarray(img).tobytes())
    p.stdin.close()
    rc = p.wait()
    if rc == 0:
        os.rename(tmp, dst)
    else:
        sys.exit("ffmpeg hata kodu %d" % rc)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for a in sys.argv[2:]:
            t = float(a)
            save_png(frame(t), os.path.join(OUT, "v3still_%05.2f.png" % t))
    elif mode == "chunk":
        render_chunk(float(sys.argv[2]), float(sys.argv[3]))
