#!/usr/bin/env python3
"""Short: Mit mi gercek mi? Muz radyoaktif midir? 1080x1920, 30 fps. Ses +0.5 sn kaydirildi."""
import math
from common import *

OUT = "/home/claude/s2/v2"
DUR = 36.5
CX, CY = 540, 900
YEL = (255, 214, 64)
GREEN = (110, 230, 140)

def banana_pts(n=60):
    """Muz merkez cizgisi ve kalinligi (birim koordinat, merkez 0,0)."""
    out = []
    for i in range(n + 1):
        u = i / n
        ang = math.radians(205 + 130 * u)
        r = 0.78
        x = r * math.cos(ang)
        y = -r * math.sin(ang) - 0.45
        w = 0.20 * (math.sin(math.pi * u) ** 0.55) + 0.012
        nx, ny = math.cos(ang), -math.sin(ang)
        out.append((x, y, w, nx, ny))
    return out

BP = banana_pts()

def banana_sprite(d):
    S = 3
    D = d * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rot = math.radians(-18)
    def P(x, y):
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        return (D / 2 + xr * D * 0.5, D / 2 + yr * D * 0.5)
    outer = [P(x + nx * w, y + ny * w) for x, y, w, nx, ny in BP]
    inner = [P(x - nx * w, y - ny * w) for x, y, w, nx, ny in BP]
    dr.polygon(outer + inner[::-1], fill=(214, 160, 28, 255))
    o2 = [P(x + nx * w * 0.15, y + ny * w * 0.15) for x, y, w, nx, ny in BP]
    i2 = [P(x - nx * w * 0.92, y - ny * w * 0.92) for x, y, w, nx, ny in BP]
    dr.polygon(o2 + i2[::-1], fill=(255, 222, 70, 255))
    o3 = [P(x - nx * w * 0.35, y - ny * w * 0.35) for x, y, w, nx, ny in BP[8:-8]]
    i3 = [P(x - nx * w * 0.70, y - ny * w * 0.70) for x, y, w, nx, ny in BP[8:-8]]
    dr.polygon(o3 + i3[::-1], fill=(255, 240, 150, 255))
    x, y, w, nx, ny = BP[0]
    c = P(x, y)
    dr.ellipse((c[0] - 0.025 * D, c[1] - 0.025 * D, c[0] + 0.025 * D, c[1] + 0.025 * D), fill=(70, 50, 25, 255))
    x, y, w, nx, ny = BP[-1]
    tx, ty = -ny, nx
    p0 = P(x, y)
    p1 = P(x + tx * 0.16 + 0.02, y + ty * 0.16 - 0.06)
    dr.line([p0, p1], fill=(120, 110, 40, 255), width=int(0.05 * D))
    dr.ellipse((p1[0] - 0.026 * D, p1[1] - 0.026 * D, p1[0] + 0.026 * D, p1[1] + 0.026 * D), fill=(80, 60, 30, 255))
    im = im.resize((d, d), Image.LANCZOS)
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3] / 255.0
    return (arr[..., :3] * a[..., None]).astype(np.float32), a.astype(np.float32)

def banana_dot_pts():
    rot = math.radians(-18)
    pts = []
    rr = np.random.default_rng(5)
    for k in range(70):
        i = int(rr.uniform(6, len(BP) - 6))
        x, y, w, nx, ny = BP[i]
        q = rr.uniform(-0.75, 0.75)
        px, py = x + nx * w * q, y + ny * w * q
        pts.append((px * math.cos(rot) - py * math.sin(rot), px * math.sin(rot) + py * math.cos(rot)))
    return pts

BAN = banana_sprite(600)
BAN_S = banana_sprite(72)

KDOTS = banana_dot_pts()
K40 = [7, 31, 52]

def banana(img, gl, x, y, s, op, glow=0.35):
    if op <= 0.01:
        return
    gcircle(gl, x, y + 40 * s, 150 * s, YEL, glow * 0.4 * op)
    blit(img, BAN, x, y, op=op, scale=s)

# --------------------------------------------------------------- A (0 - 6.5)
def scene_A(t):
    img = base(t)
    gl = newgl()
    bp = ease_out_back(seg(t, 0.3, 1.0))
    bob = 8 * math.sin(t * 2.0)
    banana(img, gl, CX, CY + bob, 1.25 * bp, min(1, bp))
    o = fade(t, 0.3, 0.8)
    blit(img, pill("MİT Mİ, GERÇEK Mİ?", F_B, 44, AMBER, AMBER, padx=34, pady=14), 540, 340, op=o)
    caption(img, [("MUZ", WHITE), ("RADYOAKTİF Mİ?", YEL)], t, 2.15, 6.6, y0=470, size=104)
    st = ease_out_back(seg(t, 4.8, 5.2))
    if st > 0:
        blit(img, pill("EVET, AMA ÇOK AZ", F_B, 66, CYAN, CYAN, padx=40, pady=20, fill_a=0.92), 540, 1320,
             op=min(1, st), scale=1.25 - 0.25 * min(1, st))
    return img, gl

# --------------------------------------------------------------- B (6.5 - 12.4)
def scene_B(t):
    img = base(t)
    gl = newgl()
    s = 1.5
    banana(img, gl, CX, CY, s, fade(t, 6.4, 6.8), glow=0.2)
    dp = fade(t, 7.2, 8.4)
    hl = fade(t, 9.0, 9.5)
    for i, (x, y) in enumerate(KDOTS):
        px, py = CX + x * 300 * s, CY + y * 300 * s
        if i * 0.012 + 7.2 > t:
            continue
        if i in K40 and hl > 0:
            pu = 0.75 + 0.25 * math.sin(t * 7 + i)
            cv2.circle(img, (int(px), int(py)), 13, scol(AMBER, hl), -1, cv2.LINE_AA)
            gcircle(gl, px, py, 70 * pu, AMBER, 0.9 * hl)
            for k in range(2):
                q = ((t - 9.0) / 1.2 + k / 2.0) % 1.0
                cv2.circle(img, (int(px), int(py)), int(16 + 60 * q), scol(AMBER, hl * (1 - q) * 0.8), 2, cv2.LINE_AA)
        else:
            cv2.circle(img, (int(px), int(py)), 9, scol((205, 190, 255), dp * (1 - 0.45 * hl)), -1, cv2.LINE_AA)
    caption(img, [("MUZ POTASYUM", WHITE), ("AÇISINDAN ZENGİN", YEL)], t, 6.7, 9.0, y0=380, size=86)
    if t > 8.9:
        caption(img, [("KÜÇÜK BİR KISMI", WHITE), ("RADYOAKTİF", AMBER)], t, 9.0, 12.6, y0=380, size=86)
    lg = fade(t, 7.4, 8.0)
    blit(img, pill("POTASYUM", F_SB, 34, (205, 190, 255), (150, 140, 230), padx=24, pady=10), 540, 1330, op=lg)
    lk = fade(t, 11.2, 11.7)
    blit(img, pill("POTASYUM-40 (RADYOAKTİF)", F_SB, 34, AMBER, AMBER, padx=24, pady=10), 540, 1420, op=lk)
    return img, gl

# --------------------------------------------------------------- C (12.4 - 16.7)
def scene_C(t):
    img = base(t)
    gl = newgl()
    bp = ease_out_back(seg(t, 12.5, 13.1))
    banana(img, gl, CX, 700, 0.8 * bp, min(1, bp))
    caption(img, [("1 MUZ YEMEK", WHITE)], t, 12.55, 16.9, y0=380, size=92)
    cp = fade(t, 13.4, 13.8)
    if cp > 0:
        v = 0.1 * ease_out(seg(t, 13.6, 15.2))
        txt = "≈ %s µSv" % ("%.2f" % v).replace(".", ",")
        if t >= 15.2:
            txt = "≈ 0,1 µSv"
        gcircle(gl, 540, 1080, 220, CYAN, 0.25 * cp)
        blit(img, T(txt, F_B, 150, CYAN, maxw=960), 540, 1080, op=cp)
        blit(img, T("(0,01 milirem) DOZ", F_SB, 44, MUTED), 540, 1210, op=fade(t, 15.0, 15.5))
    return img, gl

# --------------------------------------------------------------- D (16.7 - 21.7)
def scene_D(t):
    img = base(t)
    gl = newgl()
    caption(img, [("ABD'DE BİR GÜNDE", WHITE), ("DOĞAL RADYASYON", CYAN)], t, 16.9, 21.9, y0=340, size=82)
    p = smooth(seg(t, 17.4, 20.0))
    n = int(round(100 * p))
    S = 74
    x0 = 540 - 4.5 * S
    y0 = 640
    for k in range(100):
        r, c = divmod(k, 10)
        x, y = x0 + c * S, y0 + r * S
        if k < n:
            blit(img, BAN_S, x, y, op=1.0, scale=1.0)
        else:
            cv2.circle(img, (int(x), int(y)), 3, scol((70, 100, 160), fade(t, 16.8, 17.3)), -1, cv2.LINE_AA)
    k2 = ease_out_back(seg(t, 20.0, 20.5))
    if k2 > 0.01:
        gcircle(gl, 540, 1440, 200, YEL, 0.25 * min(1, k2))
        blit(img, T("≈ 100 MUZ", F_B, 118, YEL), 540, 1440, op=min(1, k2), scale=0.8 + 0.2 * k2)
    return img, gl

# --------------------------------------------------------------- E (21.7 - 24.9)
def scene_E(t):
    img = base(t)
    gl = newgl()
    caption(img, [("1 GÖĞÜS RÖNTGENİ", WHITE)], t, 21.95, 25.1, y0=340, size=88)
    blit(img, T("(≈ 10 milirem)", F_SB, 40, MUTED), 540, 430, op=fade(t, 22.3, 22.8))
    p = smooth(seg(t, 22.2, 24.0))
    n = int(round(1000 * p))
    COLS, S = 40, 21
    x0 = 540 - (COLS - 1) / 2 * S
    y0 = 560
    for k in range(1000):
        r, c = divmod(k, COLS)
        x, y = x0 + c * S, y0 + r * S
        if k < n:
            cv2.ellipse(img, (int(x), int(y)), (8, 4), -20, 0, 360, YEL, -1, cv2.LINE_AA)
        else:
            cv2.circle(img, (int(x), int(y)), 2, scol((70, 100, 160), fade(t, 21.8, 22.2)), -1, cv2.LINE_AA)
    k2 = ease_out_back(seg(t, 24.0, 24.4))
    if k2 > 0.01:
        gcircle(gl, 540, 1300, 200, YEL, 0.25 * min(1, k2))
        blit(img, T("≈ 1.000 MUZ", F_B, 118, YEL), 540, 1300, op=min(1, k2), scale=0.8 + 0.2 * k2)
    return img, gl

# --------------------------------------------------------------- F (24.9 - 30.2)
def scene_F(t):
    img = base(t)
    gl = newgl()
    banana(img, gl, CX, 820, 1.05, fade(t, 24.9, 25.4))
    caption(img, [("RADYOAKTİF Mİ?", WHITE), ("EVET.", AMBER)], t, 25.05, 40, y0=330, size=92)
    r = ease_out_back(seg(t, 27.4, 27.9))
    if r > 0:
        blit(img, T("RİSK Mİ?", F_B, 92, WHITE), 540, 1240, op=min(1, r))
        blit(img, T("HAYIR.", F_B, 92, CYAN), 540, 1345, op=min(1, r), scale=0.85 + 0.15 * r)
    return img, gl

SCENES = [(0.0, scene_A), (6.45, scene_B), (12.4, scene_C), (16.7, scene_D), (21.75, scene_E), (24.9, scene_F)]
XH = 0.2

def render_scene(fn, t):
    img, gl = fn(t)
    series_tag(img, t)
    apply_glow(img, gl)
    return img

def frame(t):
    idx = 0
    for k, (s, _) in enumerate(SCENES):
        if t >= s - XH:
            idx = k
    s, fn = SCENES[idx]
    img = render_scene(fn, t)
    if idx > 0 and t < s + XH:
        prev = render_scene(SCENES[idx - 1][1], t)
        w = smooth((t - (s - XH)) / (2 * XH))
        img = cv2.addWeighted(prev, 1 - w, img, w, 0)
    note(img, t, 0.4, 30.1)
    img = source_card(img, t, 30.2, [
        "ABD EPA · \"Natural Radioactivity in Food\"",
        "1 muz ≈ 0,1 µSv · ≈100 muz = ABD'de 1 günlük doğal doz",
        "ABD NRC · \"Doses in Our Daily Lives\"",
        "muzda potasyum-40 · göğüs röntgeni ≈ 10 milirem",
    ], ["1.000 muz: NRC (10 mrem) ÷ EPA (0,01 mrem) hesabı", "ANİMASYON · ŞEMATİK, ÖLÇEKLİ DEĞİL"])
    if t > 30.2:
        series_tag(img, t)
    return img

if __name__ == "__main__":
    main(frame, OUT, "muz", DUR)
