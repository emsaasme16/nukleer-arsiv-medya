#!/usr/bin/env python3
"""Seslendirme metninden (yonerge etiketleri cikarilmis) Turkce SRT.
Zaman: her sahne cues.json'daki gercek baslangic/sureye yayilir; sahne icinde cumle zamani karakter
oranindan, her [pause] etiketi ~PAUSE_CH karakterlik sure sayilarak hesaplanir.
Satir <= 42 karakter, altyazi basina en cok 2 satir.
Kullanim: python3 altyazi.py senaryo.md cues.json cikti.srt"""
import re, sys, json

PAUSE_CH = 12
MAXL = 42


def scenes(md):
    t = open(md, encoding="utf-8").read()
    return [p.strip() for p in re.findall(r"\*\*Seslendirme:\*\*\n\n(.+?)\n\n\*\*3D görsel", t, re.S)]


def wrap(words):
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= MAXL:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def chunks(sentence):
    """Cumleyi <= 2 satirlik parcalara bol."""
    lines = wrap(sentence.split())
    out = []
    for i in range(0, len(lines), 2):
        out.append(lines[i:i + 2])
    return out


def ts(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def main(md, cues, out):
    C = json.load(open(cues))
    cues_out = []
    for k, txt in enumerate(scenes(md)):
        # birimler: (metin parcasi | None=pause)
        toks = re.split(r"(\[[a-z ]+\])", txt)
        items = []
        for tk in toks:
            if not tk.strip():
                continue
            if tk.startswith("["):
                if tk == "[pause]":
                    items.append((None, PAUSE_CH))
                continue
            for s in re.findall(r"[^.?!:;]+[.?!:;]*", tk):
                s = " ".join(s.split())
                if s:
                    for ch in chunks(s):
                        L = sum(len(l) for l in ch)
                        items.append((ch, L))
        total = sum(u for _, u in items)
        t0, D = C["starts"][k], C["durations"][k]
        acc = 0
        for ch, u in items:
            a = t0 + D * acc / total
            acc += u
            b = t0 + D * acc / total
            if ch is not None:
                cues_out.append((a, b - 0.05, ch))
    with open(out, "w", encoding="utf-8") as f:
        for i, (a, b, ch) in enumerate(cues_out, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), "\n".join(ch)))
    print(len(cues_out), "altyazi", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
