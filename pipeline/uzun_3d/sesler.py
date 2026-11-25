#!/usr/bin/env python3
"""Uzun bolum sesi: sahne mp3'leri -> dogal ses zinciri -> birlestirme -> cues.json -> muzik/whoosh -> miks.

Kullanim:  python3 sesler.py /tmp/bolum1
Girdi:     <DIR>/ses/sahne_01.mp3 ... sahne_NN.mp3  (senaryodaki sirayla)
Cikti:     <DIR>/cues.json, <DIR>/ses_final.wav (ses yalniz), <DIR>/mix.wav (final, -14 LUFS, tepe <= -1.5 dBFS)

Ses zinciri (dogal sesi korur): PERDE KAYDIRMA YOK. 70 Hz yuksek geciren, 3 kHz +1,5 dB, hafif de-esser,
cok hafif sikistirma (2:1), yanki yok. Sahneler arasi GAP saniye sessizlik.
Muzik: sound_mix/sound3 tarzinda sakin, major tonda uzun pad (D major), sahne gecislerinde hafif whoosh;
sidechain ile muzik sese gore ~14 dB altta.
"""
import sys, os, re, json, glob, subprocess
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
LEAD = 1.0      # ilk sesten once
GAP = 0.8       # sahneler arasi sessizlik
TAIL = 6.0      # son sesten sonra (bitis karti)
rng = np.random.default_rng(11)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-2000:])
    return r.stderr


def lufs(fn):
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", fn, "-af", "ebur128=peak=true", "-f", "null", "-"])
    I = float(re.findall(r"I:\s+(-?\d+\.\d+) LUFS", e)[-1])
    P = float(re.findall(r"Peak:\s+(-?\d+\.\d+) dBFS", e)[-1])
    return I, P


def dur(fn):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", fn]).decode().strip())


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


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
        s, zi = signal.lfilter(b, a, noise[edges[k]:edges[k + 1]], zi=zi)
        out[edges[k]:edges[k + 1]] = s
    return out


def whoosh(d, f0, f1):
    s = bandpass_sweep(rng.standard_normal(int(d * SR)), f0, f1)
    s = s * np.sin(np.pi * np.linspace(0, 1, len(s))) ** 2
    return s / (np.max(np.abs(s)) + 1e-9)


def shimmer(f, d=2.4):
    t = np.arange(int(d * SR)) / SR
    s = np.zeros_like(t)
    for k, (m, g) in enumerate([(1, 1.0), (2.0, 0.45), (3.01, 0.22)]):
        s += g * np.sin(2 * np.pi * f * m * t + k) * np.exp(-t * (1.4 + k * 0.8))
    return s


def music(DUR, starts):
    N = int(DUR * SR)
    tt = np.arange(N) / SR
    # akor dizisi (major, yavas): D - G - Bm - A , her biri 12 sn, yumusak gecis
    chords = [[73.42, 110.0, 146.83, 185.0, 220.0, 293.66],     # D
              [98.0, 146.83, 196.0, 246.94, 293.66, 392.0],      # G
              [61.74, 123.47, 146.83, 185.0, 246.94, 293.66],    # Bm
              [110.0, 138.59, 164.81, 220.0, 277.18, 329.63]]    # A
    gains = [0.8, 0.5, 0.45, 0.3, 0.22, 0.10]
    CL = 12.0
    pad = np.zeros(N)
    for ci, ch in enumerate(chords):
        # bu akorun agirlik zarfi (periyodik, cross-fade)
        ph = ((tt / CL) - ci) % len(chords)
        w = np.where(ph < 1.0, 1.0, np.where(ph < 1.35, 1 - (ph - 1.0) / 0.35, np.where(ph > len(chords) - 0.35, (ph - (len(chords) - 0.35)) / 0.35, 0.0)))
        w = lowpass(w, 2.0, 1)
        sig = np.zeros(N)
        for f, g in zip(ch, gains):
            for d in (-0.0025, 0.0025):
                sig += g * signal.sawtooth(2 * np.pi * f * (1 + d) * tt + rng.uniform(0, 6.28))
        pad += sig * w
    pad = lowpass(pad, 800, 2)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 10.0 - 1.2)
    pad *= (0.7 + 0.3 * lfo)
    # cok hafif arpej parlakligi (major pentatonik, seyrek)
    arp = np.zeros(N)
    notes = [587.33, 659.25, 739.99, 880.0, 987.77]
    tc = 2.0
    while tc < DUR - 6:
        i0 = int(tc * SR)
        s = shimmer(float(rng.choice(notes)), 2.4)[: N - i0]
        arp[i0:i0 + len(s)] += s * 0.10
        tc += rng.uniform(2.6, 4.2)
    fade_io = np.clip(tt / 3.0, 0, 1) * np.clip((DUR - tt) / 4.0, 0, 1)
    pad = pad / (np.max(np.abs(pad)) + 1e-9)
    L = (pad * 0.22 + arp) * fade_io
    R = (np.roll(pad, int(0.012 * SR)) * 0.22 + np.roll(arp, int(0.02 * SR))) * fade_io
    # whoosh: sahne gecisleri (ses baslamadan hemen once)
    SL, SRr = np.zeros(N), np.zeros(N)
    for k, st in enumerate(starts[1:]):
        w = whoosh(1.3, 350, 4200)
        i0 = int((st - 1.15) * SR)
        SL[i0:i0 + len(w)] += w * 0.16 * (0.8 if k % 2 else 1.0)
        SRr[i0:i0 + len(w)] += w * 0.16 * (1.0 if k % 2 else 0.8)

    def finish(a, b, fn):
        mix = np.stack([a, b], axis=1)
        for d, gg in [(0.083, 0.22), (0.151, 0.14), (0.239, 0.08)]:
            kk = int(d * SR)
            wet = np.zeros_like(mix)
            wet[kk:] = mix[:-kk] * gg
            mix = mix + wet[:, ::-1]
        mix = highpass(mix.T, 28, 2).T
        mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.8
        wavfile.write(fn, SR, (mix * 32767).astype(np.int16))
    return finish, (L, R), (SL, SRr)


def main(D):
    files = sorted(glob.glob(os.path.join(D, "ses", "sahne_*.mp3")))
    assert files, "ses dosyasi yok"
    chain = ("highpass=f=70,equalizer=f=3000:t=q:w=1.0:g=1.5,deesser=i=0.25:m=0.5:f=0.5,"
             "acompressor=threshold=0.1:ratio=2:attack=15:release=200:makeup=1")
    starts, durs = [], []
    t = LEAD
    parts = []
    for i, f in enumerate(files):
        w = os.path.join(D, "ses", "p%02d.wav" % (i + 1))
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-af", chain, "-ar", str(SR), "-ac", "1", w])
        sr, x = wavfile.read(w)
        x = x.astype(np.float32) / 32768.0
        starts.append(round(t, 3))
        durs.append(round(len(x) / SR, 3))
        parts.append((t, x))
        t += len(x) / SR + GAP
    DUR = round(t - GAP + TAIL, 3)
    N = int(DUR * SR)
    v = np.zeros(N, np.float32)
    for t0, x in parts:
        i0 = int(round(t0 * SR))
        v[i0:i0 + len(x)] += x
    wavfile.write(os.path.join(D, "ses_ham.wav"), SR, (np.clip(v, -1, 1) * 32767).astype(np.int16))
    json.dump({"lead": LEAD, "gap": GAP, "tail": TAIL, "duration": DUR, "starts": starts, "durations": durs},
              open(os.path.join(D, "cues.json"), "w"), indent=1)
    print("sahne baslangiclari", starts, "toplam", DUR)

    I, _ = lufs(os.path.join(D, "ses_ham.wav"))
    g = -17.0 - I
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(D, "ses_ham.wav"), "-af",
         "volume=%.2fdB,alimiter=limit=0.89:level=false,pan=stereo|c0=c0|c1=c0" % g, os.path.join(D, "ses_final.wav")])

    finish, (PL, PR), (SL, SRr) = music(DUR, starts)
    finish(PL, PR, os.path.join(D, "pad.wav"))
    finish(SL, SRr, os.path.join(D, "sfx.wav"))

    def premix(padvol):
        fc = ("[0:a]asplit=2[v][vk];"
              "[1:a][vk]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=700:makeup=1[pd];"
              "[pd]volume=%.3f[p];[2:a]volume=0.5[s];"
              "[v][p][s]amix=inputs=3:normalize=0:duration=longest[m]" % padvol)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(D, "ses_final.wav"), "-i", os.path.join(D, "pad.wav"),
             "-i", os.path.join(D, "sfx.wav"), "-filter_complex", fc, "-map", "[m]", "-ar", str(SR), os.path.join(D, "premix.wav")])
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(D, "ses_final.wav"), "-i", os.path.join(D, "pad.wav"),
             "-filter_complex", "[1:a][0:a]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=700:makeup=1,volume=%.3f[p]" % padvol,
             "-map", "[p]", os.path.join(D, "pad_ducked.wav")])
        Iv, _ = lufs(os.path.join(D, "ses_final.wav"))
        Ip, _ = lufs(os.path.join(D, "pad_ducked.wav"))
        return Iv, Ip

    padvol = 0.42
    Iv, Ip = premix(padvol)
    # muzik sese gore ~14 dB altta olsun
    padvol *= 10 ** (((Iv - Ip) - 14.0) / 20)
    Iv, Ip = premix(padvol)
    print("ses %.1f LUFS, muzik %.1f LUFS, fark %.1f dB (padvol %.3f)" % (Iv, Ip, Iv - Ip, padvol))

    pm = os.path.join(D, "premix.wav")
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", pm, "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
    ln = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
          % (js["input_i"], js["input_tp"], js["input_lra"], js["input_thresh"], js["target_offset"]))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pm, "-af",
         ln + ",aresample=44100,alimiter=limit=0.79:level=false:attack=1:release=50,alimiter=limit=0.74:level=false:attack=1:release=60", "-ar", "44100",
         os.path.join(D, "mix.wav")])
    print("final (wav)", lufs(os.path.join(D, "mix.wav")))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/bolum1")
