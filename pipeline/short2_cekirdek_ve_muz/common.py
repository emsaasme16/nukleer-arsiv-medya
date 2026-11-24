"""Ortak cizim yardimcilari (render3.py'den ayrildi)."""
import sys, math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
GW, GH = W // 4, H // 4
CX, CY = 540, 900

F_B = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
F_SB = "/usr/share/fonts/truetype/google-fonts/Poppins-SemiBold.ttf"
F_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"

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


RED = (255, 84, 84)
NEUT = (150, 170, 205)

def series_tag(img, t):
    blit(img, pill("NÜKLEER ARŞİV", F_SB, 30, CYAN, CYAN, padx=30, pady=12, fill_a=0.55), 540, 212,
         op=fade(t, 0.1, 0.7))

def note(img, t, a, b):
    o = fade(t, a, a + 0.6) * (1 - fade(t, b - 0.4, b))
    if o > 0:
        blit(img, T("ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL", F_M, 28, MUTED), 540, 1580, op=0.8 * o)

def arrow(img, p0, p1, color, th=8, tip=0.28):
    cv2.arrowedLine(img, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), color, th, cv2.LINE_AA, tipLength=tip)

def caption(img, lines, t, t0, t1, y0=330, size=84, gap=None):
    """lines: [(metin, renk)], t0'da girer t1'de cikar."""
    ex = 1 - fade(t, t1 - 0.35, t1)
    if ex <= 0 or t < t0:
        return
    gap = gap or int(size * 1.12)
    for i, (txt, col) in enumerate(lines):
        text_in(img, txt, F_B, size, col, 540, y0 + i * gap, t, t0 + 0.12 * i, op=ex)

def source_card(img, t, t0, rows, extra):
    ec = fade(t, t0, t0 + 0.6)
    if ec <= 0:
        return img
    clean = base(t)
    img = cv2.addWeighted(clean, ec, img, 1 - ec, 0)
    blit(img, T("KAYNAKLAR", F_B, 52, CYAN), 540, 640, op=ec)
    y = 740
    for i, r in enumerate(rows):
        blit(img, T(r, F_M, 34, WHITE, maxw=990), 540, y, op=fade(t, t0 + 0.2 + 0.1 * i, t0 + 0.8 + 0.1 * i))
        y += 58
    y += 30
    for i, r in enumerate(extra):
        blit(img, T(r, F_SB, 29, MUTED, maxw=990), 540, y, op=fade(t, t0 + 0.6, t0 + 1.2))
        y += 52
    blit(img, T("DEVAMI KANALDA · BÖLÜM 1", F_B, 52, AMBER, maxw=980), 540, y + 90, op=fade(t, t0 + 0.9, t0 + 1.5))
    return img

def render_chunk(frame, out, tag, s, e, FPS=30):
    i0, i1 = int(round(s * FPS)), int(round(e * FPS))
    tmp = os.path.join(out, "tmp_%s_%g_%g.mp4" % (tag, s, e))
    dst = os.path.join(out, "%s_chunk_%06.2f.mp4" % (tag, s))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", "30", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg hata")
    os.rename(tmp, dst)

def main(frame, out, tag, dur):
    mode = sys.argv[1]
    if mode == "still":
        for a in sys.argv[2:]:
            Image.fromarray(frame(float(a))).save(os.path.join(out, "%s_still_%05.2f.png" % (tag, float(a))))
    elif mode == "chunk":
        render_chunk(frame, out, tag, float(sys.argv[2]), float(sys.argv[3]))
