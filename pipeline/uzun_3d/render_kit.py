"""Uzun bolumler icin yeniden kullanilabilir 3D/2D parcalar (16:9).

Cekirdek (paketlenmis nukleon kumeleri), atom (elektron bulutu), terazi, yay, kartlar, kose etiketi,
bitis karti ve cok surecli dilimli render surucusu. Bolum betikleri `from render_kit import *` ile kullanir.
"""
import math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import gl3d
from common3d import *
from common3d import _align_y, _cache

NAVYTXT = (10, 22, 56)


# ----------------------------------------------------------------- sayi bicimleri (Turkce)
def tr_int(v):
    return "{:,}".format(int(round(v))).replace(",", ".")


def tr_dec(v, n):
    return ("{:.%df}" % n).format(v).replace(".", ",")


# ----------------------------------------------------------------- kartlar
def card(lines, size=56, amber=False, padx=40, pady=22):
    """Rakam karti: acik renkli zemin, buyuk kalin koyu yazi."""
    key = ("card", tuple(lines), size, amber, padx, pady)
    if key in _cache:
        return _cache[key]
    font = ImageFont.truetype(F_B, size)
    _A = "\u2190\u2192\u2194\u207b\u2074\u2075\u2076\u2077\u2078\u2079\u2070"
    _fb = ImageFont.truetype(F_GR, int(size * 0.92))
    boxes = []
    for l in lines:
        bb = font.getbbox(l)
        if any(ch in _A for ch in l):
            wl = sum((_fb if ch in _A else font).getlength(ch) for ch in l)
            bb = (0, bb[1], int(wl), bb[3])
        boxes.append(bb)
    lh = int(size * 1.25)
    tw = max(b[2] - b[0] for b in boxes)
    w = int(tw + 2 * padx + 8)
    h = int(lh * len(lines) + 2 * pady + 8 - (lh - size))
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (255, 228, 176) if amber else (232, 241, 255)
    edge = AMBER if amber else CYAN
    d.rounded_rectangle((4 * S, 4 * S, (w - 4) * S, (h - 4) * S), radius=18 * S, fill=fill + (245,),
                        outline=edge + (255,), width=3 * S)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    ARR = "\u2190\u2192\u2194\u207b\u2074\u2075\u2076\u2077\u2078\u2079\u2070"
    fb = ImageFont.truetype(F_GR, int(size * 0.92))
    for i, (l, b) in enumerate(zip(lines, boxes)):
        x = (w - (b[2] - b[0])) / 2 - b[0]
        y = 4 + pady + i * lh - font.getbbox("Hg")[1]
        if not any(ch in ARR for ch in l):
            d.text((x, y), l, font=font, fill=NAVYTXT + (255,))
            continue
        for ch in l:       # Poppins'te olmayan ok/ust simgeler DejaVu ile
            f = fb if ch in ARR else font
            d.text((x, y + (size * 0.06 if f is fb else 0)), ch, font=f, fill=NAVYTXT + (255,))
            x += f.getlength(ch)
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    # hafif dis golge
    sh = cv2.GaussianBlur(a, (0, 0), 8) * 0.55
    out_a = np.clip(a + sh * (1 - a), 0, 1)
    spr = ((arr[..., :3] * a[..., None]).astype(np.float32), out_a.astype(np.float32))
    _cache[key] = spr
    return spr


def badge(txt):
    return pill(txt, F_SB, 28, AMBER, AMBER, padx=22, pady=10, fill_a=0.6)


def corner_tag(img, txt, a):
    if a <= 0:
        return
    s = pill(txt, F_SB, 26, CYAN, CYAN, padx=22, pady=10, fill_a=0.55)
    w = s[1].shape[1]
    blit(img, s, 40 + w / 2, 52, op=a)


# ----------------------------------------------------------------- cekirdek kumeleri
def _pack(n, seed):
    rng = np.random.default_rng(seed)
    Rc = 1.02 * n ** (1 / 3)
    pts = []
    while len(pts) < n:
        v = rng.uniform(-1, 1, 3)
        if np.dot(v, v) < 1:
            pts.append(v * Rc)
    P = np.array(pts)
    for _ in range(120):
        d = P[:, None, :] - P[None, :, :]
        dist = np.linalg.norm(d, axis=-1) + np.eye(n) * 10
        push = np.clip(1.9 - dist, 0, None)[..., None] * d / dist[..., None]
        P += push.sum(1) * 0.5
        r = np.linalg.norm(P, axis=1, keepdims=True)
        P = np.where(r > Rc, P * Rc / r, P)
        P -= P.mean(0) * 0.1
    return P


def _mk(z, n, seed):
    P = _pack(z + n, seed)
    rng = np.random.default_rng(seed + 1)
    isp = np.zeros(z + n, bool)
    isp[rng.choice(z + n, z, replace=False)] = True
    return P, isp


NUC = {
    "N12": _mk(6, 6, 3),      # genel kucuk cekirdek (sematik)
    "C": _mk(6, 6, 9),
    "FE": _mk(26, 30, 4),
    "U": _mk(92, 143, 5),
    "RB": _mk(37, 56, 6),
    "CS": _mk(55, 85, 7),
}
CLN12 = [bool(x) for x in NUC["N12"][1]]
_N12B = None


def bond(F, p, q, op, t, rad=4.0):
    if op <= 0.01:
        return
    w = 0.75 + 0.25 * math.sin(t * 5 + p[0] * 0.01)
    F.rod(p, q, rad, scol(CYAN, 0.6 + 0.4 * w), MAT_GLOW, alpha=op)
    for k in (0.33, 0.66):
        m = (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k, p[2] + (q[2] - p[2]) * k)
        F.glow3(m[0], m[1], m[2], rad * 5, CYAN, 0.35 * op * w)


def nucleus(F, t, key, cx, cy, s, op, plus=True, spin=0.3, bonds=False, arrows=False, n_glow=False,
            explode=0.0, wobble=0.0, stretch=0.0, z0=0.0):
    if op <= 0.01:
        return
    P, isp = NUC[key]
    n = len(P)
    rn = 40.0 * s                      # nukleon yaricapi (piksel)
    R = rot_y(t * spin) @ rot_x(0.35 * math.sin(t * 0.3))
    Q = P @ R.T
    if explode > 0:
        dirs = P / (np.linalg.norm(P, axis=1, keepdims=True) + 1e-6)
        Q = Q + (dirs @ R.T) * explode * 6.0
    if wobble > 0:
        Q = Q * (1 + wobble * np.sin(t * 6 + np.arange(n))[:, None])
    if stretch > 0:
        Q = Q * np.array([1 + 0.7 * stretch, 1 - 0.25 * stretch, 1 - 0.25 * stretch])
        # bel: ortada incelme
        pinch = 1 - 0.35 * stretch * np.exp(-(Q[:, 0] / 2.5) ** 2)
        Q[:, 1] *= pinch
        Q[:, 2] *= pinch
    pts = np.stack([cx + Q[:, 0] * rn, cy + Q[:, 1] * rn, z0 + Q[:, 2] * rn], 1)
    lo = n > 30
    if bonds:
        for i in range(n):
            for j in range(i + 1, n):
                if np.linalg.norm(P[i] - P[j]) < 2.25:
                    bond(F, pts[i], pts[j], op, t, rad=max(2.5, 5 * s))
    zmax = np.abs(Q[:, 2]).max() + 1e-6
    for i in range(n):
        ao = 0.8 + 0.2 * clamp01((Q[i, 2] / zmax + 1) / 2)
        col = WARM if isp[i] else NEUT
        F.sphere(pts[i, 0], pts[i, 1], pts[i, 2], rn, col, MAT_PLASTIC, alpha=op, lo=lo, ao=ao,
                 glow=(0.25 if not lo else 0.0) + (0.35 if (n_glow and not isp[i]) else 0.0),
                 glow_col=CYAN if (n_glow and not isp[i]) else None)
        if plus and isp[i] and not lo:
            F.plus(pts[i, 0], pts[i, 1], pts[i, 2], rn, op)
    Rpx = (np.linalg.norm(P, axis=1).max() + 1) * rn
    if lo:
        F.glow(cx, cy, Rpx * 1.1, scol(WARM, 0.5), 0.5 * op)
    if arrows:
        k = 0.7 + 0.3 * math.sin(t * 8)
        na = 8
        for i in range(na):
            a = 2 * math.pi * i / na + t * 0.15
            d = np.array([math.cos(a), math.sin(a), 0.0])
            p0 = np.array([cx, cy, z0]) + d * (Rpx + 14)
            p1 = p0 + d * (60 + 18 * math.sin(t * 8 + i)) * max(0.6, s)
            F.arrow3(p0, p1, 5 * max(0.6, s), RED, MAT_GLOW, alpha=op * k, head=3.0, head_len=24 * max(0.6, s))


def atom(F, t, cx, cy, s, op, nuc=None, cloud_k=1.0, nuc_k=1.0):
    """Camgobegi elektron bulutu + ortada kucuk amber cekirdek (ya da kucuk kume)."""
    if op <= 0.01:
        return
    R = 270 * s
    for rr, kk in ((1.0, 0.16), (0.78, 0.18), (0.55, 0.2), (0.34, 0.16)):
        F.glow(cx, cy, R * rr, scol(CYAN, 0.55), kk * op * cloud_k)
    for i in range(6):
        a = t * (0.9 + 0.13 * i) + i * 1.7
        tilt = i * 0.55
        x = math.cos(a) * R * 0.8
        y = math.sin(a) * R * 0.32
        xr = x * math.cos(tilt) - y * math.sin(tilt)
        yr = x * math.sin(tilt) + y * math.cos(tilt)
        z = math.sin(a + i) * R * 0.4
        F.sphere(cx + xr, cy + yr, z, 6 * s, CYAN, MAT_GLOW, alpha=op, glow=0.9, lo=True)
    if nuc:
        nucleus(F, t, nuc, cx, cy, 0.42 * s, op, plus=False, spin=0.5)
    else:
        F.sphere(cx, cy, 0, 11 * s, AMBER, MAT_GLOW, alpha=op, glow=1.2 * nuc_k)
        F.glow(cx, cy, 30 * s * nuc_k, AMBER, 0.6 * op * nuc_k)


# ----------------------------------------------------------------- terazi
def balance(F, cx, cy, half, tilt, op, wobble=0.0, s=1.0):
    if op <= 0.01:
        return
    tilt = tilt + wobble
    col = (150, 170, 210)
    F.cyl(cx, cy + 220 * s, -10, 10 * s, 440 * s, col, MAT_METAL, alpha=op)
    F.box(cx, cy + 440 * s, -10, 220 * s, 22 * s, 110 * s, (60, 76, 120), MAT_PLASTIC, op)
    F.sphere(cx, cy, 0, 18 * s, AMBER, MAT_GLOSS, alpha=op)
    F.box(cx, cy, 0, 2 * half, 14 * s, 18 * s, col, MAT_METAL, op, R=rot_z(tilt))
    for sg in (-1, 1):
        ex, ey = cx + sg * half * math.cos(tilt), cy + sg * half * math.sin(tilt)
        py = ey + 245 * s
        F.cyl(ex, py, 0, 150 * s, 10 * s, (110, 130, 175), MAT_METAL, alpha=op)
        for dx in (-120, 120):
            F.rod((ex, ey, 0), (ex + dx * s, py - 5, 0), 2.2, (170, 190, 230), MAT_GLOSS, alpha=op)


# ----------------------------------------------------------------- yay (benzetme)
def _spring_mesh():
    turns, L, rad = 7.0, 560.0, 120.0
    n = 420
    th = np.linspace(0, turns * 2 * math.pi, n)
    x = np.linspace(-L / 2, L / 2, n)
    path = np.stack([x, rad * np.cos(th), rad * np.sin(th)], 1)
    radii = np.full(n, 11.0)
    radii[:3] = [0.1, 6, 9]
    radii[-3:] = [9, 6, 0.1]
    return gl3d.mesh_tube(path, radii, sides=14)


SPRING = ("spring", _spring_mesh)


def spring(F, t, cx, cy, comp, op, bright=1.0):
    if op <= 0.01:
        return
    F.add(SPRING, model((cx, cy, 40), (comp, 1, 1), rot_x(t * 0.2)), (200, 210, 230), MAT_METAL, op)
    for sg in (-1, 1):
        ex = cx + sg * 280 * comp
        F.cyl(ex, cy, 40, 135, 14, AMBER, MAT_GLOW, alpha=op, R=rot_z(math.pi / 2))
        F.glow(ex, cy, 150, AMBER, 0.7 * op * bright * (0.8 + 0.2 * math.sin(t * 6)))


# ----------------------------------------------------------------- diger nesneler
_CR = np.random.default_rng(12).normal(size=(9, 3))
_CR /= np.linalg.norm(_CR, axis=1, keepdims=True)


def moon(F, x, y, z, r, op, t):
    if op <= 0.01 or r < 1:
        return
    F.sphere(x, y, z, r, (190, 192, 200), MAT_MATTE, alpha=op)
    R = rot_y(t * 0.2)
    for c in _CR:
        v = R @ c
        if v[2] < 0.1:
            continue
        F.sphere(x + v[0] * r * 0.93, y + v[1] * r * 0.93, z + v[2] * r * 0.93, r * 0.16, (130, 134, 146), MAT_MATTE, alpha=op, lo=True)


def sun(F, t, x, y, r, op):
    if op <= 0.01:
        return
    F.sphere(x, y, -40, r, (255, 200, 90), MAT_GLOW, alpha=op, glow=1.5, glow_col=AMBER)
    F.glow(x, y, r * 2.2, scol(AMBER, 0.6), 0.6 * op * (0.85 + 0.15 * math.sin(t * 2)))


def velcro(F, t, cx, cy, open_k, op):
    if op <= 0.01:
        return
    lift = 240 * open_k
    F.box(cx, cy + 70, 0, 820, 36, 90, (60, 80, 130), MAT_MATTE, op)
    F.box(cx, cy - 70 - lift, 0, 820, 36, 90, (70, 92, 140), MAT_MATTE, op)
    for i in range(18):
        x = cx - 380 + i * 44.7
        # alt: ilmekler (kucuk halkalar)
        F.torus(x, cy + 44, 0, 15, 0.22, (140, 200, 230), rot_z(0) @ rot_x(math.pi / 2) @ rot_y(math.pi / 2) , MAT_PLASTIC, op)
        # ust: kancalar
        F.cyl(x + 10, cy - 30 - lift, 0, 4, 44, (150, 220, 255), MAT_GLOSS, alpha=op)
        F.sphere(x + 10, cy - 8 - lift, 0, 7, (150, 220, 255), MAT_GLOSS, alpha=op, lo=True)
    if open_k < 0.3:
        F.glow(cx, cy, 300, CYAN, 0.35 * op * (1 - open_k / 0.3))


def shelf_card(F, t, i, cx, cy, o, act):
    if o <= 0.01:
        return
    F.box(cx, cy, -20, 300, 230, 16, scol((34, 50, 96), 1 + 0.4 * act), MAT_PLASTIC, o)
    z = 30
    if i == 0:
        for k in range(16):
            a = 2 * math.pi * k / 16
            F.box(cx + 105 * math.cos(a), cy + 62 * math.sin(a), z, 22, 18, 22, (90, 110, 150), MAT_PLASTIC, o, R=rot_z(a))
        F.box(cx, cy, z - 8, 150, 90, 4, (40, 120, 70), MAT_MATTE, o)
        F.sphere(cx, cy, z + 4, 9, PEA, MAT_GLOSS, alpha=o, glow=0.9, glow_col=AMBER)
    elif i == 1:
        F.sphere(cx - 55, cy, z, 40, WARM, MAT_PLASTIC, alpha=o)
        F.sphere(cx + 55, cy, z, 40, WARM, MAT_PLASTIC, alpha=o)
        F.plus(cx - 55, cy, z, 40, o)
        F.plus(cx + 55, cy, z, 40, o)
        bond(F, (cx - 20, cy, z), (cx + 20, cy, z), o, t, rad=5)
    elif i == 2:
        tl = -0.15
        F.box(cx, cy - 40, z, 220, 8, 10, (150, 170, 210), MAT_METAL, o, R=rot_z(tl))
        F.cyl(cx, cy + 10, z, 5, 100, (150, 170, 210), MAT_METAL, alpha=o)
        for sg in (-1, 1):
            ex, ey = cx + sg * 110 * math.cos(tl), cy - 40 + sg * 110 * math.sin(tl)
            F.cyl(ex, ey + 50, z, 45, 6, (110, 130, 175), MAT_METAL, alpha=o)
        for k in range(4):
            F.sphere(cx - 135 + k * 18, cy - 40 + 25 + 20, z + 10, 9, WARM if k % 2 else NEUT, MAT_PLASTIC, alpha=o, lo=True)
        F.sphere(cx + 108, cy - 40 - 16 + 20, z + 10, 16, WARM, MAT_PLASTIC, alpha=o, lo=True)
    elif i == 3:
        pts = []
        for k in range(40):
            A = 4 + k * 6
            v = 8.79 * (1 - math.exp(-A / 11.0)) ** 2.2 / (1 - math.exp(-56 / 11.0)) ** 2.2 if A < 56 else 8.79 - 0.00287 * (A - 56) - 2.11e-5 * (A - 56) ** 2
            pts.append((cx - 120 + 240 * A / 240, cy + 80 - 170 * v / 9.5))
        for a_, b_ in zip(pts[:-1], pts[1:]):
            F.rod((a_[0], a_[1], z), (b_[0], b_[1], z), 4, AMBER, MAT_GLOW, alpha=o)
        F.sphere(cx - 120 + 56, cy + 80 - 170 * 8.79 / 9.5, z, 10, AMBER, MAT_GLOW, alpha=o, glow=1.0)
    elif i == 4:
        F.box(cx - 60, cy + 80 - 2, z, 60, 4, 40, CYAN, MAT_GLOW, o)
        F.box(cx + 60, cy + 80 - 90, z, 60, 180, 40, AMBER, MAT_PLASTIC, o)
    if act > 0.01:
        F.glow(cx, cy, 170, CYAN, 0.5 * act * o, thick=10)


# ----------------------------------------------------------------- ust katman cizimleri
def window_frame(img, cx, cy, w, h, a):
    if a <= 0:
        return
    ov = img.copy()
    cv2.rectangle(ov, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), CYAN, 3, cv2.LINE_AA)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)


def ruler(img, x0, x1, y0, a):
    if a <= 0:
        return
    ov = img.copy()
    cv2.line(ov, (int(x0), int(y0)), (int(x1), int(y0)), CYAN, 3, cv2.LINE_AA)
    for x in (x0, x1):
        cv2.line(ov, (int(x), int(y0 - 18)), (int(x), int(y0 + 18)), CYAN, 3, cv2.LINE_AA)
    n = 10
    for k in range(1, n):
        x = x0 + (x1 - x0) * k / n
        cv2.line(ov, (int(x), int(y0 - 8)), (int(x), int(y0 + 8)), CYAN, 2, cv2.LINE_AA)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)


def dashed_gap(img, x, y0, y1, a):
    if a <= 0:
        return
    ov = img.copy()
    ya, yb = sorted((y0, y1))
    yb = max(yb, ya + 40)
    y = ya
    while y < yb:
        cv2.line(ov, (int(x), int(y)), (int(x), int(min(yb, y + 10))), CYAN, 3, cv2.LINE_AA)
        y += 18
    for yy in (ya, yb):
        cv2.line(ov, (int(x - 30), int(yy)), (int(x + 30), int(yy)), CYAN, 3, cv2.LINE_AA)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)


def emc2(img, a, p):
    if a <= 0:
        return
    cs = 1 + 1.1 * smooth(seg(p, 59, 62)) * (1 - smooth(seg(p, 64, 66.5)))
    es = 1 + 0.45 * smooth(seg(p, 65, 67))
    E = T("E", F_XB, 170, AMBER, maxw=1800)
    EQ = T("=", F_XB, 150, WHITE, maxw=1800)
    M = T("m", F_XB, 110, WHITE, maxw=1800)
    C = T("c²", F_XB, 170, CYAN, maxw=1800)
    ws = [E[1].shape[1] * es, EQ[1].shape[1], M[1].shape[1], C[1].shape[1] * cs]
    tot = sum(ws) - 36 * 3
    x = 960 - tot / 2
    y = 430
    for spr, w, sc in zip((E, EQ, M, C), ws, (es, 1, 1, cs)):
        blit(img, spr, x + w / 2, y + (12 if spr is M else 0), op=a, scale=sc)
        x += w - 36


def draw_chart_base(img, cam, a, g, curve_fn, xy_fn, x0, x1, y0, y1):
    if a <= 0:
        return
    P = lambda x, y: tuple(int(v) for v in cam.p2(x, y, 0)[:2])
    ov = img.copy()
    cv2.line(ov, P(x0, y0), P(x1 + 30, y0), CYAN, 3, cv2.LINE_AA)
    cv2.line(ov, P(x0, y0), P(x0, y1 - 40), CYAN, 3, cv2.LINE_AA)
    cv2.arrowedLine(ov, P(x1, y0), P(x1 + 40, y0), CYAN, 3, cv2.LINE_AA, tipLength=0.5)
    cv2.arrowedLine(ov, P(x0, y1 - 20), P(x0, y1 - 60), CYAN, 3, cv2.LINE_AA, tipLength=0.5)
    As = np.linspace(1, 1 + 239 * g, max(2, int(400 * g)))
    vs = curve_fn(As)
    pts = np.array([P(*xy_fn(A, v)) for A, v in zip(As, vs)], np.int32)
    glow = np.zeros_like(img)
    cv2.polylines(glow, [pts], False, CYAN, 14, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 9)
    cv2.add(ov, glow, dst=ov)
    cv2.polylines(ov, [pts], False, WHITE, 4, cv2.LINE_AA)
    if 0 < g < 1:
        cv2.circle(ov, tuple(pts[-1]), 9, WHITE, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)


def table_panel(img, a, p, rows, cy=560):
    if a <= 0:
        return
    ov = img.copy()
    w, h = 1080, 80 * len(rows) + 60
    x0, y0 = 960 - w // 2, cy - h // 2
    cv2.rectangle(ov, (x0, y0), (x0 + w, y0 + h), (8, 16, 40), -1)
    cv2.addWeighted(ov, 0.85 * a, img, 1 - 0.85 * a, 0, dst=img)
    ov = img.copy()
    cv2.rectangle(ov, (x0, y0), (x0 + w, y0 + h), CYAN, 2, cv2.LINE_AA)
    cv2.addWeighted(ov, a, img, 1 - a, 0, dst=img)
    for i, (txt, t0) in enumerate(rows):
        last = i == len(rows) - 1
        o = a * fade(p, t0, t0 + 0.8)
        if last:
            cv2.line(img, (x0 + 60, y0 + 30 + i * 80 + 2), (x0 + w - 60, y0 + 30 + i * 80 + 2), scol(CYAN, o), 2, cv2.LINE_AA)
        blit(img, T(txt, F_B if last else F_SB, 48, AMBER if last else WHITE, maxw=1000), 960, y0 + 70 + i * 80, op=o)


# ----------------------------------------------------------------- bitis karti (sol yari dolu, sag yari bos)
def end_card(F, t, a, q, title="BÖLÜM 2: FİSYON · YAKINDA", sub="Bir nötron çekirdeği nasıl böler?",
             sources=("ABD Enerji Bakanlığı (DOE)", "ABD Nükleer Düzenleme Kurulu (NRC)"),
             question="Soru: Demir neden önemli?"):
    if a <= 0:
        return
    cam = F.cam

    def op(img):
        clean = background(t, cam)
        img = cv2.addWeighted(clean, a, img, 1 - a, 0)
        X = 560
        blit(img, T("SIRADAKİ", F_SB, 34, CYAN), X, 210, op=a * fade(q, 0.2, 0.8))
        blit(img, T(title, F_XB, 60, AMBER, maxw=860), X, 285, op=a * fade(q, 0.3, 0.9))
        blit(img, T(sub, F_M, 38, WHITE, maxw=860), X, 365, op=a * fade(q, 0.5, 1.1))
        cv2.line(img, (X - 300, 440), (X + 300, 440), scol(CYAN, 0.5 * a), 2, cv2.LINE_AA)
        blit(img, T("KAYNAKLAR", F_B, 40, CYAN), X, 510, op=a * fade(q, 0.8, 1.4))
        for i, r in enumerate(sources):
            blit(img, T(r, F_M, 36, WHITE, maxw=860), X, 580 + i * 58, op=a * fade(q, 1.0 + 0.2 * i, 1.6 + 0.2 * i))
        if question:
            blit(img, T(question, F_SB, 36, MUTED, maxw=860), X, 760, op=a * fade(q, 1.4, 2.0))
        pu = 1 + 0.04 * math.sin(t * 4) * fade(q, 3, 4)
        blit(img, pill("ABONE OL", F_B, 34, WHITE, AMBER, padx=34, pady=14, fill=(150, 40, 30), fill_a=0.9), X, 860,
             op=a * fade(q, 2.0, 2.6), scale=pu)
        return img
    F.over(op)


# ----------------------------------------------------------------- render surucusu
VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "1100k", "-bufsize", "2200k",
        "-pix_fmt", "yuv420p", "-g", "60"]


def _worker(args):
    mod, i0, i1, path = args
    import importlib
    m = importlib.import_module(mod)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an"] + VENC + ["-threads", "2", path + ".tmp.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(np.ascontiguousarray(m.frame(i / FPS)).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg hata")
    os.rename(path + ".tmp.mp4", path)
    return path


def render_long(mod, nframes, work, workers=4, nchunks=None):
    """Kareleri cok surecli dilimlerle kodlar, concat -c copy ile sessiz.mp4 yapar. Var olan dilimler atlanir."""
    import multiprocessing as mp
    cdir = os.path.join(work, "dilimler")
    os.makedirs(cdir, exist_ok=True)
    nchunks = nchunks or max(workers * 6, nframes // 450)
    bounds = [round(nframes * k / nchunks) for k in range(nchunks + 1)]
    jobs = [(mod, bounds[k], bounds[k + 1], os.path.join(cdir, "c%03d.mp4" % k)) for k in range(nchunks)]
    todo = [j for j in jobs if not os.path.exists(j[3])]
    os.environ.setdefault("LP_NUM_THREADS", "2")
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers) as pool:
        for pth in pool.imap_unordered(_worker, todo, chunksize=1):
            print("tamam", pth, flush=True)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for j in jobs:
            f.write("file '%s'\n" % j[3])
    silent = os.path.join(work, "sessiz.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-c", "copy", silent])
    return silent
