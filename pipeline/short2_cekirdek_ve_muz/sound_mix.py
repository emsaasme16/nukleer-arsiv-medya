#!/usr/bin/env python3
"""Muzik yatagi + efekt sentezi + ses zinciri + miks (sound3.py ve build4.py'den uyarlandi).
Kullanim: sound_mix.py kuvvet|muz"""
import sys, re, json, subprocess
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
DUR = 36.5
VOFF = 0.5
N = int(SR * DUR)
tt = np.arange(N) / SR
rng = np.random.default_rng(11)

CUES = {
    # (tur, zaman, kazanc)
    "kuvvet": [("pop", 0.35, .25), ("pop", 0.55, .22), ("whoosh", 3.4, .16), ("boom", 3.8, .35),
               ("whoosh_dn", 5.4, .18), ("boom", 7.8, .55), ("shimmer", 7.9, .12), ("pop", 8.95, .2),
               ("whoosh", 9.25, .16), ("boom", 9.7, .5), ("shimmer", 10.3, .12), ("rise", 13.4, .1),
               ("boom", 14.5, .45), ("shimmer", 14.5, .14), ("whoosh", 15.7, .14), ("shimmer", 17.6, .1),
               ("pop", 20.3, .16), ("whoosh", 22.4, .14), ("click", 24.6, .5), ("whoosh_dn", 25.7, .14),
               ("whoosh", 27.15, .14), ("boom", 27.5, .6), ("shimmer", 27.5, .16), ("shimmer", 30.2, .1)],
    "muz": [("pop", 0.4, .25), ("shimmer", 0.5, .1), ("pop", 2.2, .18), ("boom", 4.85, .45),
            ("shimmer", 4.9, .12), ("whoosh", 6.25, .14), ("ticks", 7.2, .04), ("shimmer", 9.0, .14),
            ("geiger", 9.0, .06), ("pop", 11.3, .18), ("whoosh", 12.2, .14), ("rise", 13.6, .1),
            ("boom", 15.2, .4), ("whoosh", 16.5, .14), ("ticks100", 17.4, .05), ("boom", 20.0, .45),
            ("shimmer", 20.0, .12), ("whoosh", 21.55, .14), ("rise", 22.2, .1), ("boom", 24.0, .5),
            ("whoosh", 24.7, .14), ("pop", 27.4, .2), ("shimmer", 27.4, .14), ("shimmer", 30.2, .1)],
}

def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr))
    return e

def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)

def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)

def glide(f0, f1, dur):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def bandpass_sweep(noise, f0, f1, q=2.2, blocks=60):
    n = len(noise)
    out = np.zeros(n)
    edges = np.linspace(0, n, blocks + 1).astype(int)
    zi = None
    for k in range(blocks):
        fc = f0 * (f1 / f0) ** ((k + 0.5) / blocks)
        b, a = signal.butter(2, [max(20, fc / q) / (SR / 2), min(0.45, fc * 1.3 / (SR / 2))], "band")
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        seg, zi = signal.lfilter(b, a, noise[edges[k]:edges[k + 1]], zi=zi)
        out[edges[k]:edges[k + 1]] = seg
    return out

def pop(f=640, dur=0.22):
    s = glide(f * 1.6, f, dur) * np.exp(-np.arange(int(dur * SR)) / SR * 18)
    return s * env_ar(len(s), 0.002, 0.05)

def tick(f, dur=0.035):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90)

def boom(dur=1.8, f0=100, f1=38):
    t = np.arange(int(dur * SR)) / SR
    s = glide(f0, f1, dur) * np.exp(-t * 2.6)
    n = lowpass(rng.standard_normal(len(t)), 600) * np.exp(-t * 9) * 0.5
    return (s + n) * env_ar(len(s), 0.003, 0.2)

def shimmer(f=1318.5, dur=1.8):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for k, (m, g) in enumerate([(1, 1.0), (2.0, 0.5), (3.01, 0.28), (4.2, 0.15)]):
        s += g * np.sin(2 * np.pi * f * m * t + k) * np.exp(-t * (1.6 + k * 0.8))
    return s * env_ar(len(s), 0.004, 0.3)

def whoosh(dur, f0, f1):
    s = bandpass_sweep(rng.standard_normal(int(dur * SR)), f0, f1)
    s = s * np.sin(np.pi * np.linspace(0, 1, len(s))) ** 2
    return s / (np.max(np.abs(s)) + 1e-9)

def click():
    t = np.arange(int(0.25 * SR)) / SR
    n = highpass(rng.standard_normal(len(t)), 1500) * np.exp(-t * 40)
    return n / np.max(np.abs(n)) + 0.6 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)

def build(name):
    L = np.zeros(N); R = np.zeros(N); PL = np.zeros(N); PR = np.zeros(N)

    def add(sig, t0, gain=1.0, pan=0.0):
        i0 = int(t0 * SR)
        if i0 >= N:
            return
        seg = sig[: N - i0]
        L[i0:i0 + len(seg)] += seg * gain * (1 - 0.5 * max(0, pan))
        R[i0:i0 + len(seg)] += seg * gain * (1 - 0.5 * max(0, -pan))

    # pad: muz icin daha aydinlik akor (C majör), kuvvet icin A minor (sablon)
    if name == "kuvvet":
        freqs, gains = [55.0, 82.41, 110.0, 130.81, 164.81, 246.94], [0.9, 0.5, 0.5, 0.28, 0.22, 0.10]
    else:
        freqs, gains = [65.41, 98.0, 130.81, 164.81, 196.0, 293.66], [0.9, 0.5, 0.5, 0.26, 0.22, 0.10]
    pad = np.zeros(N)
    for f, g in zip(freqs, gains):
        for d in (-0.003, 0.003):
            pad += g * signal.sawtooth(2 * np.pi * f * (1 + d) * tt + rng.uniform(0, 6.28))
    pad = lowpass(pad, 900, 2)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0 - 1.2)
    vol = (0.55 + 0.25 * lfo) * (1 + 0.3 * np.clip((tt - 24) / 4, 0, 1) * (tt < 30.5))
    fade_io = np.clip(tt / 1.5, 0, 1) * np.clip((DUR - tt) / 2.0, 0, 1)
    pad = pad * vol * fade_io
    pad /= np.max(np.abs(pad)) + 1e-9
    PL += pad * 0.20
    PR += np.roll(pad, int(0.012 * SR)) * 0.20
    bpm = 1.0 if name == "kuvvet" else 0.8
    k = 0
    while k * bpm < DUR - 1.5:
        b = np.sin(2 * np.pi * 52 * np.arange(int(0.35 * SR)) / SR) * np.exp(-np.arange(int(0.35 * SR)) / SR * 11)
        g = 0.085 * (0.5 + 0.5 * min(1, k / 5.0))
        i0 = int(k * bpm * SR)
        seg = b[: N - i0]
        PL[i0:i0 + len(seg)] += seg * g
        PR[i0:i0 + len(seg)] += seg * g
        k += 1
    hum = lowpass(rng.standard_normal(N), 130, 2)
    hum = hum / (np.max(np.abs(hum)) + 1e-9) * (0.65 + 0.35 * np.sin(2 * np.pi * tt / 11.0)) * fade_io
    PL += hum * 0.06
    PR += np.roll(hum, int(0.008 * SR)) * 0.06

    for kind, t0, g in CUES[name]:
        if kind == "pop":
            add(pop(560 + 200 * rng.uniform()), t0, g)
        elif kind == "whoosh":
            add(whoosh(0.9, 400, 5000), t0 - 0.6, g)
        elif kind == "whoosh_dn":
            add(whoosh(1.4, 4000, 300), t0, g)
        elif kind == "boom":
            add(boom(), t0, g)
        elif kind == "shimmer":
            add(shimmer(rng.choice([880, 1174.7, 1318.5])), t0, g)
        elif kind == "rise":
            add(whoosh(1.5, 300, 2800), t0, g)
        elif kind == "click":
            add(click(), t0, g)
        elif kind == "ticks":
            for i in range(30):
                add(tick(1500 + 40 * i, 0.04), t0 + i * 0.04, g, pan=((i % 3) - 1) * 0.5)
        elif kind == "ticks100":
            for i in range(100):
                p = i / 100
                x = 3 * p * p - 2 * p ** 3
                add(tick(900 + 900 * p, 0.03), t0 + 2.6 * x, g)
        elif kind == "geiger":
            tc = t0
            while tc < t0 + 3.0:
                add(highpass(rng.standard_normal(int(0.004 * SR)), 2000), tc, g * 3, pan=rng.uniform(-0.5, 0.5))
                tc += rng.exponential(0.18)

    def finish(a, b, fn):
        mix = np.stack([a, b], axis=1)
        for d, gg in [(0.083, 0.22), (0.151, 0.14), (0.239, 0.08)]:
            kk = int(d * SR)
            wet = np.zeros_like(mix)
            wet[kk:] = mix[:-kk] * gg
            mix = mix + wet[:, ::-1]
        mix = highpass(mix.T, 28, 2).T
        mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.8
        mix *= (np.clip((DUR - tt) / 1.0, 0, 1) * np.clip(tt / 0.2, 0, 1))[:, None]
        wavfile.write(fn, SR, (mix * 32767).astype(np.int16))

    D = "/home/claude/s2/" + ("v1" if name == "kuvvet" else "v2")
    finish(PL, PR, D + "/pad.wav")
    finish(L, R, D + "/sfx.wav")
    return D

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1500:])
    return r.stderr

def lufs(fn):
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", fn, "-af", "ebur128=peak=true", "-f", "null", "-"])
    I = float(re.findall(r"I:\s+(-?\d+\.\d+) LUFS", e)[-1])
    P = float(re.findall(r"Peak:\s+(-?\d+\.\d+) dBFS", e)[-1])
    return I, P

if __name__ == "__main__":
    name = sys.argv[1]
    D = build(name)
    # ses: -1 yarim ton, zincir, -17 LUFS, 0.5 sn kaydir
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/raw.wav", "-af", "rubberband=pitch=0.943874", D + "/pitch.wav"])
    chain = ("adelay=%d,apad=whole_dur=%g,highpass=f=70,equalizer=f=200:t=q:w=1.0:g=1.5,equalizer=f=3200:t=q:w=1.0:g=2.0,"
             "deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=0.08:ratio=2.5:attack=12:release=180:makeup=2,"
             "aecho=0.9:0.88:28|53:0.10|0.06" % (int(VOFF * 1000), DUR))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/pitch.wav", "-af", chain, "-t", str(DUR), D + "/vchain.wav"])
    I, _ = lufs(D + "/vchain.wav")
    gain = -17.0 - I
    print("ses zinciri %.1f LUFS -> %+.1f dB" % (I, gain))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/vchain.wav", "-af",
         "volume=%.2fdB,alimiter=limit=0.89:level=false,pan=stereo|c0=c0|c1=c0" % gain, D + "/vfinal.wav"])
    fc = ("[0:a]asplit=2[v][vk];"
          "[1:a][vk]sidechaincompress=threshold=0.04:ratio=3:attack=40:release=500:makeup=1[pd];"
          "[pd]volume=0.42[p];[2:a]volume=0.55[s];"
          "[v][p][s]amix=inputs=3:normalize=0:duration=longest[m]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/vfinal.wav", "-i", D + "/pad.wav", "-i", D + "/sfx.wav",
         "-filter_complex", fc, "-map", "[m]", "-ar", "44100", D + "/premix.wav"])
    # iki gecisli loudnorm (dogrusal) + guvenlik limiter
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", D + "/premix.wav", "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
    ln = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/premix.wav", "-af",
         ln + ",aresample=44100,alimiter=limit=0.841:level=false:attack=1:release=50", "-ar", "44100", D + "/mix.wav"])
    print("final", lufs(D + "/mix.wav"))
    # ses / muzik farki
    Iv, _ = lufs(D + "/vfinal.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + "/vfinal.wav", "-i", D + "/pad.wav", "-filter_complex",
         "[1:a][0:a]sidechaincompress=threshold=0.04:ratio=3:attack=40:release=500:makeup=1,volume=0.42[p]",
         "-map", "[p]", D + "/pad_ducked.wav"])
    Ip, _ = lufs(D + "/pad_ducked.wav")
    print("ses %.1f LUFS, muzik %.1f LUFS, fark %.1f dB" % (Iv, Ip, Iv - Ip))
