#!/usr/bin/env python3
"""Nükleer Arşiv test kartları: soru.jpg, cevap.jpg (1080x1350) ve tiktok.mp4 (1080x1920).

Kullanım:
    python3 pipeline/topluluk/kart.py            # sorular.json'daki tüm sorular
    python3 pipeline/topluluk/kart.py <id> ...   # yalnızca verilen id'ler
    --force : dosyalar varsa da yeniden üret
"""
import json
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SORULAR = os.path.join(ROOT, "topluluk", "sorular.json")
FONT_DIR = os.path.expanduser("~/.fonts")

CYAN = (63, 208, 255)
AMBER = (255, 181, 71)
WHITE = (255, 255, 255)
FPS = 30
SR = 48000
DUR = 12.0
T_SWITCH = 8.0

_font_cache = {}


def font(weight, size):
    key = (weight, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(FONT_DIR, f"Poppins-{weight}.ttf"), size)
    return _font_cache[key]


# ---------------------------------------------------------------- arka plan
def frame_from_video(path, tmpdir):
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip())
    out = os.path.join(tmpdir, "kare.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur / 2:.2f}", "-i", path,
                    "-frames:v", "1", out], check=True)
    return Image.open(out).convert("RGB")


def cover(img, W, H):
    s = max(W / img.width, H / img.height)
    nw, nh = int(round(img.width * s)), int(round(img.height * s))
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - W) // 2, (nh - H) // 2
    return img.crop((x, y, x + W, y + H))


def make_background(src, W, H):
    """src: PIL görüntüsü ya da None. Bulanık + karartılmış arka plan döndürür."""
    if src is not None:
        bg = cover(src, W, H).filter(ImageFilter.GaussianBlur(12))
        arr = np.asarray(bg).astype(np.float32) * 0.42  # %58 karartma
        # hafif lacivert ton ve dikey vinyet
        y = np.linspace(0, 1, H)[:, None, None]
        tint = np.array([11, 22, 48], np.float32)
        arr = arr * 0.85 + tint * 0.15
        arr *= (1.0 - 0.25 * (np.abs(y - 0.5) * 2) ** 2)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    top = np.array([0x0b, 0x16, 0x30], np.float32)
    bot = np.array([0x05, 0x0a, 0x18], np.float32)
    t = np.linspace(0, 1, H)[:, None, None]
    arr = np.broadcast_to(top * (1 - t) + bot * t, (H, W, 3)).copy()
    rng = np.random.default_rng(7)
    n = int(W * H / 2500)
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, H)
        r = rng.choice([1, 1, 1, 2])
        a = rng.uniform(0.15, 0.6)
        col = CYAN if rng.random() < 0.3 else WHITE
        cv2.circle(arr, (int(x), int(y)), int(r), tuple(float(c) * a + arr[y, x, i] * (1 - a) for i, c in enumerate(col)), -1,
                   lineType=cv2.LINE_AA)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- metin
def wrap(text, fnt, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def line_h(fnt, k=1.22):
    return int(fnt.size * k)


def draw_lines_center(d, lines, fnt, cx, y, fill, k=1.22):
    for ln in lines:
        w = fnt.getlength(ln)
        d.text((cx - w / 2, y), ln, font=fnt, fill=fill)
        y += line_h(fnt, k)
    return y


def draw_pill(d, text, cx, y, color=CYAN, size=30):
    f = font("SemiBold", size)
    w = f.getlength(text)
    padx, h = 30, int(size * 1.9)
    box = (cx - w / 2 - padx, y, cx + w / 2 + padx, y + h)
    d.rounded_rectangle(box, radius=h // 2, outline=color + (255,), width=3, fill=(5, 10, 24, 150))
    bb = f.getbbox(text)
    d.text((cx - w / 2, y + (h - (bb[3] + bb[1])) / 2), text, font=f, fill=color + (255,))
    return y + h


def draw_arrow(d, x, ycen, color, size):
    L = size * 0.9
    t = max(3, size // 9)
    d.line((x, ycen, x + L - size * 0.25, ycen), fill=color, width=t)
    d.polygon([(x + L, ycen), (x + L - size * 0.38, ycen - size * 0.26), (x + L - size * 0.38, ycen + size * 0.26)], fill=color)
    return x + L


def draw_check(d, x, ycen, size, color):
    t = max(5, size // 7)
    pts = [(x, ycen), (x + size * 0.35, ycen + size * 0.35), (x + size, ycen - size * 0.45)]
    d.line(pts, fill=color, width=t, joint="curve")
    for p in pts:
        d.ellipse((p[0] - t / 2, p[1] - t / 2, p[0] + t / 2, p[1] + t / 2), fill=color)


# ---------------------------------------------------------------- düzenler
def layout_question(q, W, H, top, bottom):
    """Şeffaf RGBA katman: soru ekranı. top/bottom: güvenli alan sınırları (y)."""
    M = 80
    maxw = W - 2 * M
    for qs in (72, 68, 64, 60):
        for os_ in (50, 48, 46, 44):
            qf, of = font("Bold", qs), font("SemiBold", os_)
            qlines = wrap(q["soru"], qf, maxw)
            if len(qlines) > 5:
                continue
            opts = []
            for i, s in enumerate(q["secenekler"]):
                lab = "ABCD"[i] + ")"
                lw = of.getlength(lab + " ")
                ol = wrap(s, of, maxw - 2 * 34 - lw)
                opts.append((lab, lw, ol))
            pill_h = int(30 * 1.9)
            foot_h = 50
            qh = len(qlines) * line_h(qf, 1.18)
            oh = sum(len(o[2]) * line_h(of, 1.2) + 40 for o in opts) + 22 * (len(opts) - 1)
            body = qh + 60 + oh
            avail = (bottom - top) - pill_h - foot_h - 2 * 50
            if body <= avail:
                break
        else:
            continue
        break
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = W / 2
    draw_pill(d, "NÜKLEER ARŞİV · TEST", cx, top)
    y0 = top + pill_h + 50 + max(0, (avail - body) / 2)
    y = draw_lines_center(d, qlines, qf, cx, y0, WHITE + (255,), 1.18) + 60
    for lab, lw, ol in opts:
        bh = len(ol) * line_h(of, 1.2) + 40
        d.rounded_rectangle((M, y, W - M, y + bh), radius=22, fill=(4, 10, 26, 175), outline=(255, 255, 255, 60), width=2)
        ty = y + 20 - of.getbbox("A")[1] + 6
        d.text((M + 34, ty), lab, font=of, fill=CYAN + (255,))
        for ln in ol:
            d.text((M + 34 + lw, ty), ln, font=of, fill=WHITE + (255,))
            ty += line_h(of, 1.2)
        y += bh + 22
    ff = font("Medium", 34)
    txt = "Cevap bir sonraki karede"
    tw = ff.getlength(txt) + 12 + 34 * 0.9
    fy = bottom - foot_h
    d.text((cx - tw / 2, fy), txt, font=ff, fill=AMBER + (255,))
    bb = ff.getbbox("Cevap")
    draw_arrow(d, cx - tw / 2 + ff.getlength(txt) + 12, fy + (bb[1] + bb[3]) / 2 + 2, AMBER + (255,), 34)
    return layer


def layout_answer(q, W, H, top, bottom):
    M = 80
    maxw = W - 2 * M
    ans = q["secenekler"][q["dogru"]]
    for asz in (62, 58, 54, 50):
        for esz in (42, 40, 38):
            af, ef = font("Bold", asz), font("Regular", esz)
            chk = int(asz * 0.8)
            alines = wrap(ans, af, maxw - 2 * 40 - chk - 26)
            elines = wrap(q["aciklama"], ef, maxw)
            if len(elines) > 6:
                continue
            kf = font("Medium", 30)
            klines = wrap("Kaynak: " + q["kaynak"], kf, maxw)
            pill_h = int(30 * 1.9)
            ah = len(alines) * line_h(af, 1.18) + 70
            eh = len(elines) * line_h(ef, 1.3)
            kh = len(klines) * line_h(kf) + 18 + line_h(font("Medium", 34))
            body = ah + 60 + eh
            avail = (bottom - top) - pill_h - kh - 2 * 50
            if body <= avail:
                break
        else:
            continue
        break
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = W / 2
    draw_pill(d, "DOĞRU CEVAP", cx, top)
    y = top + pill_h + 50 + max(0, (avail - body) / 2)
    # doğru cevap kutusu
    tw = max(af.getlength(l) for l in alines)
    bw = min(maxw, tw + chk + 26 + 2 * 50)
    bx = cx - bw / 2
    d.rounded_rectangle((bx, y, bx + bw, y + ah), radius=28, fill=(63, 208, 255, 52), outline=CYAN + (255,), width=5)
    ty = y + 35 - af.getbbox("A")[1] + 4
    first_mid = ty + (af.getbbox("Ag")[1] + af.getbbox("Ag")[3]) / 2
    draw_check(d, bx + 50, first_mid, chk, CYAN + (255,))
    for ln in alines:
        d.text((bx + 50 + chk + 26, ty), ln, font=af, fill=WHITE + (255,))
        ty += line_h(af, 1.18)
    y += ah + 60
    draw_lines_center(d, elines, ef, cx, y, (235, 242, 255, 255), 1.3)
    # alt bilgi
    am = font("Medium", 34)
    fy = bottom - line_h(am)
    ky = fy - 18 - len(klines) * line_h(kf)
    draw_lines_center(d, klines, kf, cx, ky, (200, 214, 235, 255))
    draw_lines_center(d, ["Videonun tamamı Nükleer Arşiv'de"], am, cx, fy, AMBER + (255,))
    return layer


# ---------------------------------------------------------------- ses
def make_audio(path):
    n = int(SR * DUR)
    t = np.arange(n) / SR
    out = np.zeros(n)

    def note(f):
        return 440.0 * 2 ** ((f - 69) / 12)

    chords = [(0, 4, [57, 60, 64, 45]), (4, 8, [53, 57, 60, 41]), (8, 12, [48, 55, 64, 36])]  # Am, F, C
    for a, b, ns in chords:
        env = np.zeros(n)
        i0, i1 = int(a * SR), int(b * SR)
        seg = np.arange(i1 - i0) / SR
        L = (b - a)
        att, rel = 0.8, 1.2
        e = np.minimum(1, seg / att) * np.clip((L + rel - seg) / rel, 0, 1)
        env[i0:i1] = e
        # sonraki akorla örtüşen sönüm
        tail_end = min(n, i1 + int(rel * SR))
        tl = np.arange(tail_end - i1) / SR
        env[i1:tail_end] = np.maximum(env[i1:tail_end], e[-1] * np.exp(-tl * 3))
        for k, m in enumerate(ns):
            f = note(m)
            amp = 0.11 if m >= 48 else 0.14
            for det in (-0.12, 0.12):
                ph = np.random.default_rng(k).uniform(0, 6.28)
                out += amp * env * (np.sin(2 * np.pi * (f + det) * t + ph) + 0.18 * np.sin(2 * np.pi * 2 * (f + det) * t))
    # yavaş dalgalanma
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
    # geri sayım tıkları (3,4,5,6,7 sn)
    for s in range(3, 8):
        i0 = int(s * SR)
        L = int(0.05 * SR)
        tt = np.arange(L) / SR
        click = np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 140) * 0.35
        click += np.sin(2 * np.pi * 1100 * tt) * np.exp(-tt * 90) * 0.2
        out[i0:i0 + L] += click
    # ding (8 sn)
    i0 = int(T_SWITCH * SR)
    L = n - i0
    tt = np.arange(L) / SR
    ding = np.zeros(L)
    for f, a, dec in ((1318.5, 0.32, 2.6), (1975.5, 0.16, 3.4), (2637.0, 0.08, 5.0), (659.25, 0.12, 2.0)):
        ding += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)
    ding *= np.minimum(1, tt / 0.004)
    out[i0:] += ding
    # yumuşak giriş/çıkış
    fade = np.ones(n)
    fi, fo = int(0.4 * SR), int(1.0 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    out *= fade
    out /= np.max(np.abs(out)) + 1e-9
    out *= 0.5
    stereo = np.stack([out, out], 1)
    import scipy.io.wavfile as wf
    wf.write(path, SR, (stereo * 32767).astype(np.int16))


def loudnorm_pass(wav):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    js = json.loads(txt[txt.rindex("{"):txt.rindex("}") + 1])
    return js


# ---------------------------------------------------------------- video
def ring_overlay(W, cx, cy, R, frac, num):
    """Geri sayım halkası (RGBA numpy)."""
    pad = 12
    sz = 2 * (R + pad)
    img = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = sz
    r2 = R * 2
    d.ellipse((c - r2, c - r2, c + r2, c + r2), fill=(4, 10, 26, 190))
    d.ellipse((c - r2, c - r2, c + r2, c + r2), outline=(255, 255, 255, 70), width=12)
    if frac > 0:
        d.arc((c - r2, c - r2, c + r2, c + r2), start=-90, end=-90 + 360 * frac, fill=CYAN + (255,), width=12)
    f = font("Bold", int(R * 1.15 * 2))
    s = str(num)
    bb = f.getbbox(s)
    d.text((c - (bb[0] + bb[2]) / 2, c - (bb[1] + bb[3]) / 2), s, font=f, fill=WHITE + (255,))
    img = img.resize((sz, sz), Image.LANCZOS)
    return img, (int(cx - sz / 2), int(cy - sz / 2))


def make_video(q, bg_src, out_path, tmpdir):
    W, H = 1080, 1920
    TOP, BOT = 180, H - 320
    bgW, bgH = int(W * 1.03) + 2, int(H * 1.03) + 2
    bg_big = np.asarray(make_background(bg_src, bgW, bgH)).astype(np.float32)
    qlay = np.asarray(layout_question(q, W, H, TOP + 40, BOT - 30)).astype(np.float32) / 255.0
    alay = np.asarray(layout_answer(q, W, H, TOP + 40, BOT - 30)).astype(np.float32) / 255.0

    wav = os.path.join(tmpdir, "ses.wav")
    make_audio(wav)
    m = loudnorm_pass(wav)
    af = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']},aresample=48000")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-af", af,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(DUR * FPS)
    R = 62
    rcx, rcy = W - 80 - R, TOP - 40 - R + 20  # sağ üst, TikTok güvenli alanının hemen altında
    rcy = TOP + R - 10
    for i in range(nf):
        t = i / FPS
        z = 1.0 + 0.03 * (t / DUR)
        cw, ch = W * z, H * z
        sx, sy = (bgW - cw) / 2, (bgH - ch) / 2
        M = np.array([[1 / z, 0, -sx / z], [0, 1 / z, -sy / z]], np.float32)
        # bg_big koordinatından çıktıya: out = (in - s)/z
        frame = cv2.warpAffine(bg_big, M, (W, H), flags=cv2.INTER_LINEAR)
        # metin katmanı: 7.85-8.15 arası çapraz geçiş
        a = np.clip((t - (T_SWITCH - 0.15)) / 0.3, 0, 1)
        if a <= 0:
            lay = qlay
        elif a >= 1:
            lay = alay
        else:
            lay = qlay * (1 - a) + alay * a
        alpha = lay[..., 3:4]
        frame = frame * (1 - alpha) + lay[..., :3] * 255.0 * alpha
        # geri sayım halkası
        if 3.0 <= t < T_SWITCH:
            num = 5 - int(t - 3.0)
            frac = 1 - ((t - 3.0) % 1.0)
            ring, (ox, oy) = ring_overlay(W, rcx, rcy, R, frac, num)
            ra = np.asarray(ring).astype(np.float32) / 255.0
            hh, ww = ra.shape[:2]
            reg = frame[oy:oy + hh, ox:ox + ww]
            aa = ra[..., 3:4]
            frame[oy:oy + hh, ox:ox + ww] = reg * (1 - aa) + ra[..., :3] * 255 * aa
        # yumuşak parlama
        g = np.exp(-((t - T_SWITCH) / 0.1) ** 2)
        if g > 0.01:
            frame = frame + (255 - frame) * 0.45 * g
        p.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg başarısız")


# ---------------------------------------------------------------- ana akış
def find_video(q):
    v = q.get("video_dosyasi") or ""
    if v and os.path.exists(os.path.join(ROOT, v)):
        return os.path.join(ROOT, v)
    return None


def build(q, force=False):
    od = os.path.join(ROOT, "topluluk", q["id"])
    outs = [os.path.join(od, n) for n in ("soru.jpg", "cevap.jpg", "tiktok.mp4")]
    if not force and all(os.path.exists(o) for o in outs):
        print(f"[atla] {q['id']}")
        return False
    os.makedirs(od, exist_ok=True)
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        vp = find_video(q)
        src = frame_from_video(vp, tmp) if vp else None
        W, H = 1080, 1350
        bg = make_background(src, W, H).convert("RGBA")
        for name, fn in (("soru.jpg", layout_question), ("cevap.jpg", layout_answer)):
            img = Image.alpha_composite(bg, fn(q, W, H, 80, H - 80)).convert("RGB")
            img.save(os.path.join(od, name), quality=90, optimize=True)
        make_video(q, src, outs[2], tmp)
    print(f"[tamam] {q['id']} (arka plan: {os.path.relpath(vp, ROOT) if vp else 'degrade'})")
    return True


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    qs = json.load(open(SORULAR, encoding="utf-8"))
    if args:
        qs = [q for q in qs if q["id"] in args]
    for q in qs:
        build(q, force)


if __name__ == "__main__":
    main()
