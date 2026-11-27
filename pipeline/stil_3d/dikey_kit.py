"""Dikey (1080x1920) gercekci 3D Shorts icin ortak parcalar (2026-11-26).

Gercekci motor `../uzun_3d/gercekci.py` (PBR, golge, SSAO, sis, alan derinligi, bloom) ve `../uzun_3d/modeller/`
dikey kadraja uyarlanir: modul yuklenirken gercekci.W/H = 1080x1920 yapilir. Yazilar `common3d.py`'deki (bu klasor)
T / pill / blit ile cizilir. Ekranda alt not ve uyari yazisi yok; son kartta kaynak adlari ve
`DEVAMI KANALDA · BOLUM N`.

Kullanim (konu betigi):  from dikey_kit import *   ->  frame(t) yaz, sonra cli(__name__dosya, frame, ...)
"""
import os, sys, math, json, subprocess
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UZ = os.path.abspath(os.path.join(HERE, "..", "uzun_3d"))
sys.path.insert(0, HERE)
sys.path.append(UZ)
sys.path.append(os.path.join(UZ, "modeller"))

import gercekci as G
G.W, G.H = 1080, 1920
from gercekci import *          # noqa  (W, H artik 1080x1920)
import yakit, atom, kapan        # noqa
from common3d import T, pill, blit, F_XB, F_B, F_SB, F_M, F_GR, CYAN, AMBER, WHITE, MUTED, RED, GREEN, FPS  # noqa

W, H = 1080, 1920
NAVYTXT = (10, 22, 56)
# Zemin/yer duzlemleri icin varsayilan mat malzeme (kullanici 2026-11-27 parlama sikayeti): koyu ton, tam purluzlu,
# metal yok. Yer duzlemine acik gri/parlak beton koyma; bloom zemine ulasmasin diye zemin HDR'de esigin altinda kalir.
ZEMIN_MAT = Mat(srgb((56, 56, 58)), 1.0, 0.0, pat="beton", scale=0.35)
_cache = {}


# ----------------------------------------------------------------- zaman yardimcilari
def clamp01(x):
    return max(0.0, min(1.0, x))


def sm(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def fade(t, a, b):
    return sm((t - a) / (b - a)) if b != a else float(t >= a)


def win(t, a, b, r=0.5):
    return fade(t, a, a + r) * (1 - fade(t, b - r, b))


def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def path(u, keys, **kw):
    """keys: [(zaman, goz, hedef, fov)], Catmull-Rom; uclarda sabit."""
    ts = [k[0] for k in keys]
    if u <= ts[0]:
        k = keys[0]
        return Cam(k[1], k[2], fov=k[3], **kw)
    if u >= ts[-1]:
        k = keys[-1]
        return Cam(k[1], k[2], fov=k[3], **kw)
    i = max(j for j in range(len(ts) - 1) if ts[j] <= u)
    s = (u - ts[i]) / (ts[i + 1] - ts[i])
    s = sm(s) * 0.5 + s * 0.5
    P = [np.asarray(keys[max(0, min(len(keys) - 1, j))][1], float) for j in (i - 1, i, i + 1, i + 2)]
    Q = [np.asarray(keys[max(0, min(len(keys) - 1, j))][2], float) for j in (i - 1, i, i + 1, i + 2)]
    fov = keys[i][3] + (keys[i + 1][3] - keys[i][3]) * sm(s)
    return Cam(_cr(*P, s), _cr(*Q, s), fov=fov, **kw)


def blend(a, b, w):
    if w <= 0:
        return a
    if w >= 1:
        return b
    return cv2.addWeighted(a, 1 - w, b, w, 0)


def shots(t, lst, xf=0.7):
    """lst: [(baslangic, fn)] -> fn(t - baslangic, t); gecislerde capraz karisim."""
    i = max([j for j in range(len(lst)) if lst[j][0] <= t] or [0])
    img = lst[i][1](t - lst[i][0], t)
    if i + 1 < len(lst):
        nxt = lst[i + 1][0]
        if t > nxt - xf:
            img = blend(img, lst[i + 1][1](t - nxt, t), sm((t - (nxt - xf)) / xf))
    return img


def proj(cam, p):
    r = cam.project(p)
    return (r[0], r[1]) if r else (-999, -999)


# ----------------------------------------------------------------- tas / komur parcasi
def m_rock(seed, n=26):
    """duzensiz, keskin yuzlu tas parcasi (rastgele noktalarin dis bukey kabugu, duz normaller)."""
    from scipy.spatial import ConvexHull
    rng = np.random.default_rng(seed)
    v = rng.normal(0, 1, (n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    v *= rng.uniform(0.75, 1.0, (n, 1))
    hull = ConvexHull(v)
    tris = []
    c0 = v.mean(0)
    for f in hull.simplices:
        a, b, c = v[f[0]], v[f[1]], v[f[2]]
        nn = np.cross(b - a, c - a)
        nn /= np.linalg.norm(nn) + 1e-9
        if np.dot(nn, a - c0) < 0:
            b, c = c, b
            nn = -nn
        for q in (a, b, c):
            tris.append((*q, *nn))
    return np.array(tris, np.float32)


ROCKS = [("tas%d" % k, (lambda k=k: m_rock(100 + k))) for k in range(6)]


# ----------------------------------------------------------------- yazilar
def label(img, txt, x, y, a, size=56, col=WHITE, font=F_B, maxw=960):
    if a > 0.003:
        blit(img, T(txt, font, size, col, maxw=maxw), x, y, op=a)


def lines(img, rows, y0, a, size=78, gap=None, t=None, t0=None):
    """rows: [(metin, renk)] ortalanmis basliklar (ust bolge, y 330-560)."""
    gap = gap or int(size * 1.15)
    for i, (txt, col) in enumerate(rows):
        k = a
        if t is not None:
            k = a * fade(t, t0 + 0.12 * i, t0 + 0.12 * i + 0.45)
        label(img, txt, 540, y0 + i * gap, k, size, col, F_XB if size >= 70 else F_B)


def card(rows, size=52, amber=False, padx=36, pady=20):
    """Rakam karti: acik renkli zemin, buyuk kalin koyu yazi."""
    from PIL import ImageDraw, ImageFont
    key = ("card", tuple(rows), size, amber, padx, pady)
    if key in _cache:
        return _cache[key]
    font = ImageFont.truetype(F_B, size)
    boxes = [font.getbbox(l) for l in rows]
    lh = int(size * 1.25)
    tw = max(b[2] - b[0] for b in boxes)
    w = int(tw + 2 * padx + 8)
    h = int(lh * len(rows) + 2 * pady + 8 - (lh - size))
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (255, 228, 176) if amber else (232, 241, 255)
    edge = AMBER if amber else CYAN
    d.rounded_rectangle((4 * S, 4 * S, (w - 4) * S, (h - 4) * S), radius=18 * S, fill=fill + (245,),
                        outline=edge + (255,), width=3 * S)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for i, (l, b) in enumerate(zip(rows, boxes)):
        x = (w - (b[2] - b[0])) / 2 - b[0]
        y = 4 + pady + i * lh - font.getbbox("Hg")[1]
        d.text((x, y), l, font=font, fill=NAVYTXT + (255,))
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    sh = cv2.GaussianBlur(a, (0, 0), 8) * 0.55
    out_a = np.clip(a + sh * (1 - a), 0, 1)
    spr = ((arr[..., :3] * a[..., None]).astype(np.float32), out_a.astype(np.float32))
    _cache[key] = spr
    return spr


def cardl(img, rows, x, y, a, size=52, amber=False, scale=1.0):
    if a > 0.003:
        blit(img, card(rows, size, amber), x, y, op=a, scale=scale)


def stamp(img, txt, x, y, a, col=AMBER, size=96, ang=-8.0, pop=0.0):
    """Mürekkep damgasi: cift cerceveli, egik, kalin yazi (MIT / GERCEK)."""
    if a <= 0.003:
        return
    from PIL import ImageDraw, ImageFont
    key = ("stamp", txt, col, size)
    if key not in _cache:
        font = ImageFont.truetype(F_XB, size)
        bb = font.getbbox(txt)
        w, h = bb[2] - bb[0] + 90, bb[3] - bb[1] + 70
        S = 2
        im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((6 * S, 6 * S, (w - 6) * S, (h - 6) * S), radius=16 * S, outline=col + (255,), width=8 * S,
                            fill=(8, 14, 34, 150))
        d.rounded_rectangle((18 * S, 18 * S, (w - 18) * S, (h - 18) * S), radius=10 * S, outline=col + (255,), width=3 * S)
        f2 = ImageFont.truetype(F_XB, size * S)
        bb2 = f2.getbbox(txt)
        d.text(((w * S - (bb2[2] - bb2[0])) / 2 - bb2[0], (h * S - (bb2[3] - bb2[1])) / 2 - bb2[1]), txt, font=f2,
               fill=col + (255,))
        im = im.resize((w, h), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
        arr = np.array(im).astype(np.float32)
        al = arr[..., 3] / 255.0
        _cache[key] = ((arr[..., :3] * al[..., None]).astype(np.float32), al.astype(np.float32))
    blit(img, _cache[key], x, y, op=a, scale=1.0 + pop)


def tag(img, t):
    blit(img, pill("NÜKLEER ARŞİV", F_SB, 30, CYAN, CYAN, padx=30, pady=12, fill_a=0.55), 540, 212,
         op=fade(t, 0.1, 0.7))


def bar(img, x0, y, w_full, k, col, h=34, a=1.0):
    """yatay cubuk (kart icin): k 0..1 uzunluk."""
    if a <= 0.003 or k <= 0:
        return
    x1 = int(x0 + w_full * k)
    over = img.copy()
    cv2.rectangle(over, (int(x0), int(y - h / 2)), (x1, int(y + h / 2)), col, -1, cv2.LINE_AA)
    cv2.addWeighted(over, a, img, 1 - a, 0, dst=img)


def end_card(img, t, t0, rows, bolum, title="KAYNAKLAR"):
    """Son kart: koyu zemin, kaynak adlari, en altta DEVAMI KANALDA · BOLUM N."""
    ec = fade(t, t0, t0 + 0.6)
    if ec <= 0:
        return img
    dark = (img.astype(np.float32) * 0.18 + np.array([6, 12, 30], np.float32) * 0.82).astype(np.uint8)
    dark = cv2.GaussianBlur(dark, (0, 0), 6)
    img = blend(img, dark, ec)
    y = 640
    label(img, title, 540, y, fade(t, t0 + 0.1, t0 + 0.6), 50, CYAN, F_B)
    y += 100
    for i, r in enumerate(rows):
        label(img, r, 540, y, fade(t, t0 + 0.2 + 0.1 * i, t0 + 0.8 + 0.1 * i), 34, WHITE, F_M, 990)
        y += 58
    label(img, "DEVAMI KANALDA · BÖLÜM %d" % bolum, 540, max(y + 150, 1420), fade(t, t0 + 0.9, t0 + 1.5), 54, AMBER, F_B, 980)
    return img


# ----------------------------------------------------------------- render surucusu
VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "9000k", "-bufsize", "18000k",
        "-pix_fmt", "yuv420p", "-g", "60"]


def _worker(args):
    mod, i0, i1, pth = args
    import importlib
    m = importlib.import_module(mod)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an"] + VENC + ["-threads", "2", pth + ".tmp.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(np.ascontiguousarray(m.frame(i / FPS)).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg hata")
    os.rename(pth + ".tmp.mp4", pth)
    return pth


def _lufs(fn):
    import re
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", fn, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?\d+\.\d+) LUFS", e)[-1]), float(re.findall(r"Peak:\s+(-?\d+\.\d+) dBFS", e)[-1])


def render(mod, nframes, work, out, workers=4, nchunks=24):
    """Dilimli cok surecli render (var olan dilimler atlanir) -> sessiz.mp4 -> mix.wav ile AAC -> out."""
    import multiprocessing as mp
    cdir = os.path.join(work, "dilimler")
    os.makedirs(cdir, exist_ok=True)
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
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", os.path.join(work, "mix.wav"),
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                           "-movflags", "+faststart", out])
    print("final", out, "LUFS/tepe", _lufs(out))
    return out


def cli(mod, frame, nframes, name):
    """python3 render_x_3d.py still 1.0 2.5 ... | render   (WORK=/tmp/sN, OUTMP4)"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    work = os.environ.get("WORK", "/tmp/" + name)
    os.makedirs(work, exist_ok=True)
    if mode == "still":
        for a in sys.argv[2:]:
            Image.fromarray(frame(float(a))).save(os.path.join(work, "still_%05.2f.png" % float(a)))
            print("kare", a, flush=True)
    else:
        out = os.environ.get("OUTMP4", os.path.join(work, name + ".mp4"))
        render(mod, nframes, work, out, workers=int(os.environ.get("WORKERS", "4")))
