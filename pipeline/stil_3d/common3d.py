"""Nukleer Arsiv 3D gorsel dili: ortak modul.

Katmanlar (Frame.finish sirasi):
  1. arka plan: lacivert degrade + vinyet + hacimsel isik huzmeleri + paralaksli toz (uzak/yakin
     katmanlar alan derinligi bulanikligiyla)
  2. 2D alt katman (F.img uzerine dogrudan cizilen cizgiler, dalgalar vb.)
  3. 3D katman (gl3d, moderngl/EGL): Lambert + Blinn-Phong, fresnel kenar isigi, metal, seritler;
     altina yumusak golge
  4. glow katmani (F.gl, 1/4 cozunurluk) + bloom
  5. ust katman (yazilar, etiketler, haplar) - her zaman en ustte, okunakli
  6. cok hafif film greni
"""
import sys, math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import gl3d
from gl3d import Cam, model, rot_x, rot_y, rot_z, W, H

FPS = 30
GW, GH = W // 4, H // 4

FD = os.path.expanduser("~/.fonts")
F_XB = os.path.join(FD, "Poppins-ExtraBold.ttf")
F_B = os.path.join(FD, "Poppins-Bold.ttf")
F_SB = os.path.join(FD, "Poppins-SemiBold.ttf")
F_M = os.path.join(FD, "Poppins-Medium.ttf")
F_GR = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NAVY0 = (4, 8, 26)
NAVY1 = (12, 28, 74)
CYAN = (53, 224, 255)
BLUE = (45, 168, 255)
AMBER = (255, 181, 71)
WHITE = (242, 247, 255)
MUTED = (150, 168, 202)
PEA = (124, 216, 64)
WARM = (255, 112, 60)        # proton: sicak kirmizi-turuncu
RED = (255, 84, 84)
NEUT = (140, 160, 200)       # notron: gri-mavi
GREEN = (110, 230, 140)

# ----------------------------------------------------------------- yardimcilar
def clamp01(x):
    return max(0.0, min(1.0, x))

def seg(t, a, b):
    return clamp01((t - a) / (b - a))

def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)

def smoother(x):
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)

def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3

def ease_in_out(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_out_back(x):
    x = clamp01(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def fade(t, a, b):
    return smooth(seg(t, a, b))

def scol(c, k):
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))

def c01(c, a=1.0):
    return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, a)

# ----------------------------------------------------------------- arka plan
def _make_bg():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.array(NAVY0, np.float32)[None, None, :]
    bot = np.array(NAVY1, np.float32)[None, None, :]
    g = top * (1 - y) + bot * y
    g = np.repeat(g, W, axis=1)
    xs = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    ys = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    r = np.sqrt(xs ** 2 * 0.6 + ys ** 2 * 0.35)
    v = 1 - 0.45 * np.clip(r, 0, 1.3) ** 2
    g = g * v[..., None]
    halo = np.exp(-((xs * 1.0) ** 2 + ((ys + 0.05) * 0.55) ** 2) * 3.0) * 24
    g[..., 2] += halo
    g[..., 1] += halo * 0.4
    # zemin: ufuk benzeri cok hafif alt parlaklik
    floor = np.exp(-((ys - 0.62) * 4.0) ** 2) * 10
    g[..., 2] += floor
    g[..., 1] += floor * 0.5
    return np.clip(g, 0, 255).astype(np.uint8)

BG = _make_bg()

def _make_shafts(seed):
    rr = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:GH, 0:GW].astype(np.float32)
    sx, sy = -0.15 * GW, -0.25 * GH
    ang = np.arctan2(ys - sy, xs - sx)
    dist = np.hypot(xs - sx, ys - sy)
    out = np.zeros((GH, GW), np.float32)
    for _ in range(5):
        a0 = rr.uniform(0.55, 1.25)
        wdt = rr.uniform(0.018, 0.05)
        out += np.exp(-((ang - a0) / wdt) ** 2) * rr.uniform(0.5, 1.0)
    out *= np.exp(-dist / (GH * 0.9))
    return out

SHAFT_A = _make_shafts(11)
SHAFT_B = _make_shafts(23)
SHAFT_COL = np.array((70, 140, 255), np.float32) / 255.0

_rd = np.random.default_rng(7)
ND = 260
DUST = np.stack([_rd.uniform(-500, 1580, ND), _rd.uniform(-300, 2220, ND), _rd.uniform(-2200, 900, ND)], 1)
DUST_SP = _rd.uniform(6, 22, ND)
DUST_PH = _rd.uniform(0, 6.28, ND)
DUST_SZ = _rd.uniform(1.2, 2.6, ND)
DUST_COL = [(190, 215, 255) if k % 4 else (120, 230, 255) for k in range(ND)]

def background(t, cam):
    img = BG.copy()
    far = np.zeros((GH, GW, 3), np.float32)
    # isik huzmeleri
    k1 = 0.55 + 0.45 * math.sin(t * 0.35)
    k2 = 0.55 + 0.45 * math.sin(t * 0.27 + 2.0)
    sh = (SHAFT_A * k1 + SHAFT_B * k2) * 26.0
    far += sh[..., None] * SHAFT_COL[None, None, :]
    # toz: 3D noktalar, yavas yukselis + salinim
    p = DUST.copy()
    p[:, 1] = (p[:, 1] - t * DUST_SP + 300) % 2520 - 300
    p[:, 0] += 18 * np.sin(t * 0.4 + DUST_PH)
    sx, sy, sc, dep = cam.project(p)
    near_l = np.zeros((GH, GW, 3), np.float32)
    for i in range(ND):
        z = DUST[i, 2]
        tw = 0.55 + 0.45 * math.sin(t * 1.3 + DUST_PH[i] * 3)
        c = DUST_COL[i]
        x, y, s = sx[i], sy[i], sc[i]
        if not (-60 < x < W + 60 and -60 < y < H + 60):
            continue
        if z < -600:          # uzak: bulanik, sonuk
            cv2.circle(far, (int(x / 4), int(y / 4)), max(1, int(DUST_SZ[i] * s * 0.9)),
                       scol(c, 0.55 * tw), -1, cv2.LINE_AA)
        elif z > 420:         # cok yakin: buyuk bokeh
            cv2.circle(near_l, (int(x / 4), int(y / 4)), max(2, int(DUST_SZ[i] * s * 2.6)),
                       scol(c, 0.22 * tw), -1, cv2.LINE_AA)
        else:                 # odakta: keskin kucuk nokta
            r = max(1, int(round(DUST_SZ[i] * s * 0.8)))
            cv2.circle(img, (int(x), int(y)), r, scol(c, 0.75 * tw), -1, cv2.LINE_AA)
    far = cv2.GaussianBlur(far, (0, 0), 1.6) + cv2.GaussianBlur(near_l, (0, 0), 3.5)
    up = cv2.resize(np.clip(far, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
    cv2.add(img, up, dst=img)
    return img

# ----------------------------------------------------------------- grenler
_GR = None

def grain(img, t):
    global _GR
    if _GR is None:
        rg = np.random.default_rng(99)
        _GR = [cv2.resize(np.clip(rg.normal(0, 1.7, (H // 3, W // 3)), -5, 5).astype(np.float32), (W, H),
                          interpolation=cv2.INTER_LINEAR) for _ in range(6)]
    g = _GR[int(t * FPS) % 6]
    out = img.astype(np.float32) + g[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

# ----------------------------------------------------------------- sprite'lar
_cache = {}

def T(txt, fontpath, size, color, maxw=960):
    """Golgeli, premultiplied metin sprite'i; maxw'ye sigmasi icin kuculur."""
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
    pad = 30
    w = int(bbox[2] - bbox[0]) + 2 * pad
    h = int(bbox[3] - bbox[1]) + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - bbox[0], pad - bbox[1]), txt, font=font, fill=tuple(color) + (255,))
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    # okunurluk: siki koyu kontur + genis yumusak golge
    tight = cv2.GaussianBlur(cv2.dilate(a, np.ones((3, 3), np.uint8)), (0, 0), 2.0)
    soft = cv2.GaussianBlur(a, (0, 0), max(4, s * 0.12))
    sh = np.clip(tight * 0.85 + soft * 0.75, 0, 1)
    out_a = np.clip(a + sh * (1 - a), 0, 1)
    rgb = arr[..., :3] * a[..., None]
    spr = (rgb.astype(np.float32), out_a.astype(np.float32))
    _cache[key] = spr
    return spr

def pill(txt, fontpath, size, color, border, padx=34, pady=18, fill=(8, 16, 40), fill_a=0.85):
    key = ("pill", txt, fontpath, size, color, border, padx, pady, fill_a)
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
    ex = min(w, img.shape[1] - x0)
    ey = min(h, img.shape[0] - y0)
    if ex <= sx0 or ey <= sy0:
        return
    region = img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32)
    aa = (a[sy0:ey, sx0:ex] * op)[..., None]
    region = region * (1 - aa) + rgb[sy0:ey, sx0:ex] * op
    img[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = np.clip(region, 0, 255).astype(np.uint8)

def arrow2d(img, p0, p1, color, th=8, tip=0.28):
    cv2.arrowedLine(img, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), color, th, cv2.LINE_AA, tipLength=tip)

# ----------------------------------------------------------------- mesh anahtarlari
SPHERE = ("sphere", lambda: gl3d.mesh_sphere())
SPHERE_LO = ("sphere_lo", lambda: gl3d.mesh_sphere(20, 12))
CYL = ("cyl", lambda: gl3d.mesh_cylinder())
CYL_LO = ("cyl_lo", lambda: gl3d.mesh_cylinder(20, True, 0.0))
CONE = ("cone", lambda: gl3d.mesh_cone())
BOX = ("box", lambda: gl3d.mesh_rbox(1, 1, 1, 0))

def rbox_key(w, h, d, r):
    k = ("dyn", "rbox", round(w, 0), round(h, 0), round(d, 0), round(r, 0))
    return (k, lambda: gl3d.mesh_rbox(max(1, k[2]), max(1, k[3]), max(1, k[4]), k[5]))

def torus_key(ratio):
    k = ("torus", round(ratio, 3))
    return (k, lambda: gl3d.mesh_torus(k[1]))

# malzemeler: (spec, shin/100, rim, emis), (bant frekansi, bant koyulugu, metal, ao)
MAT_PLASTIC = ((0.55, 0.45, 0.8, 0.0), (0, 0, 0, 1))
MAT_GLOSS = ((0.9, 0.9, 0.9, 0.0), (0, 0, 0, 1))
MAT_METAL = ((1.0, 0.6, 0.6, 0.0), (0, 0, 0.8, 1))
MAT_MATTE = ((0.12, 0.1, 0.35, 0.0), (0, 0, 0, 1))
MAT_GLOW = ((0.6, 0.6, 1.0, 0.9), (0, 0, 0, 1))

# ----------------------------------------------------------------- kare
class Frame:
    def __init__(self, t, cam=None):
        self.t = t
        self.cam = cam or Cam()
        self.img = background(t, self.cam)
        self.gl = np.zeros((GH, GW, 3), np.uint8)
        self.items = []
        self.ops = []
        self.shadow = 0.5

    # --- 3D nesneler
    def add(self, mesh, M, col, mat=MAT_PLASTIC, alpha=1.0, trans=None, ext=None):
        if alpha <= 0.004:
            return
        m, e = mat
        if ext is not None:
            e = ext
        tr = (alpha < 0.999) if trans is None else trans
        self.items.append((mesh[0], mesh[1], M, c01(col, alpha), m, e, tr))

    def sphere(self, x, y, z, r, col, mat=MAT_PLASTIC, alpha=1.0, glow=0.0, glow_col=None, lo=False, ao=1.0):
        if r <= 0.3 or alpha <= 0.004:
            return
        m, e = mat
        e = (e[0], e[1], e[2], ao)
        self.add(SPHERE_LO if lo else SPHERE, model((x, y, z), r), col, (m, e), alpha)
        if glow > 0:
            self.glow3(x, y, z, r * 1.9, glow_col or col, glow * alpha)

    def box(self, x, y, z, w, h, d, col, mat=MAT_PLASTIC, alpha=1.0, R=None, r=None, ext=None):
        if w < 0.5 or h < 0.5 or d < 0.5:
            return
        rr = min(w, h, d) * 0.12 if r is None else r
        self.add(rbox_key(w, h, d, rr), model((x, y, z), 1, R), col, mat, alpha, ext=ext)

    def cyl(self, x, y, z, rad, hgt, col, mat=MAT_PLASTIC, alpha=1.0, R=None, ext=None, lo=False):
        if rad <= 0.3 or hgt <= 0.3:
            return
        self.add(CYL_LO if lo else CYL, model((x, y, z), (rad, hgt, rad), R), col, mat, alpha, ext=ext)

    def rod(self, p0, p1, rad, col, mat=MAT_PLASTIC, alpha=1.0, lo=True):
        """p0 -> p1 arasi silindir (bag, ok govdesi)."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        L = np.linalg.norm(d)
        if L < 1e-3:
            return
        R = _align_y(d / L)
        self.add(CYL_LO if lo else CYL, model((p0 + p1) / 2, (rad, L, rad), R), col, mat, alpha)

    def arrow3(self, p0, p1, rad, col, mat=MAT_GLOW, alpha=1.0, head=2.6, head_len=None):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        L = np.linalg.norm(d)
        if L < 1:
            return
        u = d / L
        hl = head_len or rad * 5
        self.rod(p0, p1 - u * hl, rad, col, mat, alpha)
        self.add(CONE, model(p1 - u * hl / 2, (rad * head, hl, rad * head), _align_y(u)), col, mat, alpha)

    def torus(self, x, y, z, R0, ratio, col, Rm=None, mat=MAT_GLOW, alpha=1.0):
        self.add(torus_key(ratio), model((x, y, z), R0, Rm), col, mat, alpha)

    def plus(self, x, y, z, r, op=1.0):
        """Protonun on yuzune kameraya bakan '+' isareti (3D, derinlik testli)."""
        e = self.cam.eye
        c = np.array([x, y, z], float)
        v = e - c
        v /= np.linalg.norm(v)
        Rb = _billboard(v)
        p = c + v * r * 0.98
        a = r * 0.42
        th = max(2.0, r * 0.12)
        self.add(BOX, model(p, (2 * a, th, th * 0.6), Rb), WHITE, MAT_GLOW, op)
        self.add(BOX, model(p, (th, 2 * a, th * 0.6), Rb), WHITE, MAT_GLOW, op)

    # --- glow / 2D
    def glow(self, cx, cy, r, color, k=1.0, thick=-1):
        if k <= 0:
            return
        cv2.circle(self.gl, (int(cx / 4), int(cy / 4)), max(1, int(r / 4)), scol(color, min(1.5, k)), thick, cv2.LINE_AA)

    def glow3(self, x, y, z, r, color, k=1.0):
        sx, sy, s = self.cam.p2(x, y, z)
        self.glow(sx, sy, r * s, color, k)

    def p2(self, x, y, z=0.0):
        return self.cam.p2(x, y, z)

    def over(self, fn):
        """Ust katmana ertelenmis cizim: fn(img) -> None ya da yeni img."""
        self.ops.append(fn)

    def spr(self, s, cx, cy, op=1.0, scale=1.0):
        if op <= 0.003:
            return
        self.ops.append(lambda img: blit(img, s, cx, cy, op, scale))

    def text(self, txt, font, size, color, cx, cy, op=1.0, scale=1.0, maxw=960):
        self.spr(T(txt, font, size, color, maxw), cx, cy, op, scale)

    def text_in(self, txt, font, size, color, cx, cy, t0, dur=0.6, rise=36, maxw=960, op=1.0):
        p = ease_out(seg(self.t, t0, t0 + dur))
        if p <= 0 or op <= 0:
            return
        self.spr(T(txt, font, size, color, maxw), cx, cy + (1 - p) * rise, op=p * op)

    def caption(self, lines, t0, t1, y0=330, size=84, gap=None):
        t = self.t
        ex = 1 - fade(t, t1 - 0.35, t1)
        if ex <= 0 or t < t0:
            return
        gap = gap or int(size * 1.12)
        for i, (txt, col) in enumerate(lines):
            self.text_in(txt, F_B, size, col, 540, y0 + i * gap, t0 + 0.12 * i, op=ex)

    def series_tag(self):
        self.spr(pill("NÜKLEER ARŞİV", F_SB, 30, CYAN, CYAN, padx=30, pady=12, fill_a=0.55), 540, 212,
                 op=fade(self.t, 0.1, 0.7))

    # --- birlestir
    def finish(self, grain_on=True):
        img = self.img
        if self.items:
            arr = gl3d.get().render(self.cam, self.items)
            if arr is not None:
                a = arr[..., 3]
                ys, xs = np.nonzero(a[::8, ::8])
                if len(ys):
                    # yumusak golge (1/4 cozunurlukte)
                    sa = cv2.resize(a, (GW, GH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
                    sa = cv2.GaussianBlur(sa, (0, 0), 7)
                    M = np.float32([[1, 0, 7], [0, 1, 11]])
                    sa = cv2.warpAffine(sa, M, (GW, GH))
                    sa = cv2.resize(sa, (W, H), interpolation=cv2.INTER_LINEAR)
                    k = 1 - self.shadow * sa
                    y0, y1 = max(0, ys.min() * 8 - 120), min(H, ys.max() * 8 + 200)
                    x0, x1 = max(0, xs.min() * 8 - 120), min(W, xs.max() * 8 + 200)
                    reg = img[y0:y1, x0:x1].astype(np.float32) * k[y0:y1, x0:x1, None]
                    af = a[y0:y1, x0:x1, None].astype(np.float32) / 255.0
                    reg = reg * (1 - af) + arr[y0:y1, x0:x1, :3].astype(np.float32)
                    img[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
        # glow + bloom
        g = cv2.GaussianBlur(self.gl, (0, 0), 9)
        small = cv2.resize(img, (GW, GH), interpolation=cv2.INTER_AREA)
        br = cv2.subtract(small, (165, 165, 165, 0))
        bl = cv2.addWeighted(cv2.GaussianBlur(br, (0, 0), 3), 0.9, cv2.GaussianBlur(br, (0, 0), 12), 1.1, 0)
        g = cv2.add(g, bl)
        cv2.add(img, cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR), dst=img)
        for fn in self.ops:
            r = fn(img)
            if r is not None:
                img = r
        if grain_on:
            img = grain(img, self.t)
        return img


def _align_y(u):
    """Birim y eksenini u yonune ceviren donus."""
    y = np.array([0, 1.0, 0])
    v = np.cross(y, u)
    s = np.linalg.norm(v)
    c = float(np.dot(y, u))
    if s < 1e-8:
        return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)

def _billboard(v):
    """z eksenini v'ye (kameraya) ceviren, ekranda dik kalan donus."""
    z = v / np.linalg.norm(v)
    up = np.array([0, -1.0, 0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, -y, z], 1)

def mix(a, b, w):
    return cv2.addWeighted(a, 1 - w, b, w, 0)

# ----------------------------------------------------------------- kaynak karti
def source_card(F, t0, rows, extra=(), footer="DEVAMI KANALDA · BÖLÜM 1", y_title=640):
    """Ust katmanda: kare temiz arka plana gecer, kaynaklar ve alt yazi."""
    t = F.t
    ec = fade(t, t0, t0 + 0.6)
    if ec <= 0:
        return
    cam = F.cam

    def op(img):
        clean = background(t, cam)
        img = cv2.addWeighted(clean, ec, img, 1 - ec, 0)
        blit(img, T("KAYNAKLAR", F_B, 56, CYAN), 540, y_title, op=ec)
        cv2.line(img, (380, y_title + 52), (700, y_title + 52), scol(CYAN, 0.6 * ec), 2, cv2.LINE_AA)
        y = y_title + 110
        for i, r in enumerate(rows):
            blit(img, T(r, F_M, 34, WHITE, maxw=990), 540, y, op=fade(t, t0 + 0.2 + 0.1 * i, t0 + 0.8 + 0.1 * i))
            y += 58
        y += 30
        for i, r in enumerate(extra):
            blit(img, T(r, F_SB, 29, MUTED, maxw=990), 540, y, op=fade(t, t0 + 0.6, t0 + 1.2))
            y += 52
        blit(img, T(footer, F_B, 54, AMBER, maxw=980), 540, y + 90, op=fade(t, t0 + 0.9, t0 + 1.5))
        blit(img, pill("NÜKLEER ARŞİV", F_SB, 30, CYAN, CYAN, padx=30, pady=12, fill_a=0.55), 540, 212, op=1.0)
        return img
    F.over(op)

# ----------------------------------------------------------------- render surucusu
def _worker(args):
    mod, i0, i1, path = args
    os.environ.setdefault("LP_NUM_THREADS", "2")
    import importlib
    m = importlib.import_module(mod)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", "60", "-threads", "2", path + ".tmp.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(np.ascontiguousarray(m.frame(i / FPS)).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg hata")
    os.rename(path + ".tmp.mp4", path)
    return path

def render_video(mod, nframes, audio, out, work, workers=4, nchunks=16):
    import multiprocessing as mp
    os.makedirs(work, exist_ok=True)
    bounds = [round(nframes * k / nchunks) for k in range(nchunks + 1)]
    jobs = [(mod, bounds[k], bounds[k + 1], os.path.join(work, "c%03d.mp4" % k)) for k in range(nchunks)]
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers) as pool:
        paths = pool.map(_worker, jobs, chunksize=1)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write("file '%s'\n" % p)
    silent = os.path.join(work, "sessiz.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-c", "copy", silent])
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio,
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
                           "-movflags", "+faststart", out])
    return out

def cli(mod, frame, nframes, name):
    """render_x_3d.py still 1.0 2.5 ... | render"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    work = os.environ.get("WORK", "/tmp/r3d/" + name)
    os.makedirs(work, exist_ok=True)
    if mode == "still":
        for a in sys.argv[2:]:
            Image.fromarray(frame(float(a))).save(os.path.join(work, "still_%05.2f.png" % float(a)))
    elif mode == "render":
        audio = os.environ.get("AUDIO", "/tmp/ses/%s.m4a" % name)
        out = os.environ.get("OUTMP4", os.path.join(work, name + ".mp4"))
        render_video(mod, nframes, audio, out, work, workers=int(os.environ.get("WORKERS", "4")))
        print(out)
