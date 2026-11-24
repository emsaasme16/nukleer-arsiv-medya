#!/usr/bin/env python3
"""Short #2 v2: pad ve sfx ayri akimlar (sese gore yeniden zamanlandi)."""
import tl3 as tl
SH = tl.SH
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
DUR = tl.DUR
N = int(SR * DUR)
rng = np.random.default_rng(11)
tt = np.arange(N) / SR

L = np.zeros(N, np.float64)
R = np.zeros(N, np.float64)
PL = np.zeros(N, np.float64)
PR = np.zeros(N, np.float64)

def env_ar(n, a, r):
    """Kisa atak/sonum zarfi, n ornek."""
    e = np.ones(n)
    na = max(1, int(a * SR))
    nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr))
    return e

def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    seg = sig[: N - i0]
    gl = gain * (1 - 0.5 * max(0, pan)) * (1 + 0.0)
    gr = gain * (1 - 0.5 * max(0, -pan))
    L[i0:i0 + len(seg)] += seg * gl
    R[i0:i0 + len(seg)] += seg * gr

def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)

def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)

def bandpass_sweep(noise, f0, f1, q=2.0, blocks=60):
    """Gurultuyu zamanla kayan alcak geciren ile suz (yukselen/alcalan whoosh)."""
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

def sine(f, dur, phase=0.0):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * f * t + phase)

def glide(f0, f1, dur):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph)

def pop(f=640, dur=0.22):
    s = glide(f * 1.6, f, dur) * np.exp(-np.arange(int(dur * SR)) / SR * 18)
    return s * env_ar(len(s), 0.002, 0.05)

def tick(f, dur=0.035):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 90)
    return s

def boom(dur=1.6, f0=95, f1=38):
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

def whoosh(dur, f0, f1, up=True):
    n = rng.standard_normal(int(dur * SR))
    s = bandpass_sweep(n, f0, f1, q=2.2)
    t = np.linspace(0, 1, len(s))
    e = np.sin(np.pi * t) ** 2 if up else np.sin(np.pi * t) ** 1.5
    s = s * e
    return s / (np.max(np.abs(s)) + 1e-9)

# ------------------------------------------------------------------ yatak (pad)
def pad_layer(freqs, gains, det=0.003):
    out = np.zeros(N)
    for f, g in zip(freqs, gains):
        for d in (-det, det):
            ph = rng.uniform(0, 6.28)
            out += g * signal.sawtooth(2 * np.pi * f * (1 + d) * tt + ph)
    return out

pad = pad_layer([55.0, 82.41, 110.0, 130.81, 164.81, 246.94], [0.9, 0.5, 0.5, 0.28, 0.22, 0.10])
pad = lowpass(pad, 900, 2)
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0 - 1.2)
vol = 0.55 + 0.25 * lfo
vol *= 1 + 0.30 * np.clip((tt - 3.0) / 4.2, 0, 1) * (tt < 9.0 - SH)      # zoom gerilimi
vol *= 1 + 0.35 * np.clip((tt - 31.0 + SH) / 2.7, 0, 1) * (tt < 36.0 - SH)   # nukleer enerji yukselisi
fade_io = np.clip(tt / 1.5, 0, 1) * np.clip((DUR - tt) / 1.8, 0, 1)
pad = pad * vol * fade_io
pad /= np.max(np.abs(pad)) + 1e-9
PL += pad * 0.20
PR += np.roll(pad, int(0.012 * SR)) * 0.20
for k in range(int(DUR)):                                    # 60 bpm nabiz
    b = sine(52, 0.35) * np.exp(-np.arange(int(0.35 * SR)) / SR * 11) * env_ar(int(0.35 * SR), 0.004, 0.1)
    g = 0.085 * (0.5 + 0.5 * min(1, k / 5.0)) * (1 if k < DUR - 1.5 else 0)
    i0 = int(k * SR)
    seg = b[: N - i0]
    PL[i0:i0 + len(seg)] += seg * g
    PR[i0:i0 + len(seg)] += seg * g

hum = lowpass(rng.standard_normal(N), 130, 2)
hum = hum / (np.max(np.abs(hum)) + 1e-9)
hum *= (0.65 + 0.35 * np.sin(2 * np.pi * tt / 11.0)) * fade_io
PL += hum * 0.060
PR += np.roll(hum, int(0.008 * SR)) * 0.060

n = tl.fwd      # eski zaman -> yeni zaman

# ---- 0-9 sn: bezelye + stadyum (zoom yeni zamanda 3.0-7.2)
add(pop(520), 0.25, 0.30)
add(whoosh(4.2, 180, 3800), 3.0, 0.30)
add(glide(160, 760, 4.2) * np.sin(np.pi * np.linspace(0, 1, int(4.2 * SR))) ** 2, 3.0, 0.07)
for k, tk in enumerate(np.linspace(n(5.4), n(12.0), 26)):
    f = [1568, 1976, 2349, 1760, 2637][k % 5]
    add(tick(f, 0.05), tk, 0.025 * (0.4 + 0.6 * k / 26), pan=((k % 3) - 1) * 0.6)
add(pop(740, 0.18), n(10.9), 0.14)
add(pop(880, 0.18), n(11.3), 0.12)
add(pop(660, 0.22), n(11.7), 0.16)

# ---- 9-16.4: "kutlesi nerede?" ve sayac
add(whoosh(0.9, 400, 5000), 8.45 - SH, 0.18)
add(boom(1.8), n(14.4), 0.50)
add(shimmer(880, 1.4), n(14.5), 0.10)
for k in range(99):
    p = k / 99
    x = 1 - (1 - p) ** (1 / 3.0)
    add(tick(700 + 900 * p, 0.03), n(17.2 + 3.0 * x), 0.05 + 0.04 * p)
add(whoosh(1.5, 300, 2800), n(17.2), 0.10)
add(boom(2.0, 110, 42), n(20.25), 0.55)                      # %99+ (yaklasik 13.4 sn)
add(shimmer(1174.7, 2.2), n(20.25), 0.16)
add(pop(900, 0.2), n(20.9), 0.12)

# ---- 16.4-25.4: proton / elektron noktalari
add(whoosh(0.8, 500, 4500), n(24.6), 0.12)
add(pop(420, 0.28), n(25.35), 0.30)
add(shimmer(659.3, 1.2), n(25.5), 0.09)
for k in range(36):
    p = k / 36
    add(tick(900 + 1400 * p, 0.04), n(27.0 + 4.0 * p), 0.05 + 0.05 * p, pan=-0.5 + p)
add(whoosh(1.8, 250, 3200), n(27.0), 0.10)
add(boom(2.2, 120, 40), n(31.0), 0.55)                       # 1836 bitisi (yaklasik 20.3 sn)
add(shimmer(987.8, 2.0), n(31.0), 0.15)

# ---- 25.4-39: atom ve "nukleer enerji" (dogrudan yeni zaman)
E0 = tl.E0
add(whoosh(1.0, 300, 3500), E0 - 0.3, 0.14)
add(pop(500, 0.26), E0 + 0.2, 0.22)
for k, dt in enumerate([0.5, 0.65, 0.8]):
    add(pop(1100 + 220 * k, 0.1), E0 + dt, 0.07, pan=(k - 1) * 0.6)
add(whoosh(1.4, 200, 6000), E0 + 5.6, 0.14)                  # "Nukleer enerji ise..." oncesi kabarma
add(shimmer(1318.5, 2.2), E0 + 6.9, 0.10)                    # NUKLEER ENERJI yazisi
add(boom(3.2, 130, 36), E0 + 8.3, 0.80)                      # "cekirdegin icinden gelir"
add(shimmer(1318.5, 3.0), E0 + 8.3, 0.18)
add(shimmer(659.3, 3.0), E0 + 8.3, 0.12)
for k in range(4):
    add(glide(520, 150, 0.9) * np.exp(-np.arange(int(0.9 * SR)) / SR * 3.5), E0 + 8.3 + 0.53 * k, 0.12 - 0.02 * k)
add(shimmer(1760, 2.0), E0 + 10.8, 0.10)                     # kaynak karti
add(shimmer(1318.5, 2.0), E0 + 11.0, 0.07)

# ------------------------------------------------------------------ cikti (ayri akimlar)
def finish(a, b, name, gain_limit):
    mix = np.stack([a, b], axis=1)
    for d, g in [(0.083, 0.22), (0.151, 0.14), (0.239, 0.08)]:
        k = int(d * SR)
        wet = np.zeros_like(mix)
        wet[k:] = mix[:-k] * g
        mix = mix + wet[:, ::-1]
    mix = highpass(mix.T, 28, 2).T
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * gain_limit
    fo = np.clip((DUR - tt) / 1.0, 0, 1)[:, None]
    fi = np.clip(tt / 0.2, 0, 1)[:, None]
    mix = mix * fo * fi
    wavfile.write("/home/claude/short1/out/" + name, SR, (mix * 32767).astype(np.int16))
    print(name, "peak %.3f rms %.1f dBFS" % (np.max(np.abs(mix)), 20 * np.log10(np.sqrt(np.mean(mix ** 2)))))

finish(PL, PR, "v3_pad.wav", 0.8)
finish(L, R, "v3_sfx.wav", 0.8)
