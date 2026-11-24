import numpy as np, subprocess, re, os
from scipy.io import wavfile
OUT = "/home/claude/short1/out"
V = "/home/claude/short1/voice"
SR = 44100
SH = 0.8
DUR = 39.0 - SH
# -1 yarim ton perde (kalinlastirma), tempo ayni
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", V + "/take4_raw.wav", "-af", "rubberband=pitch=0.943874", V + "/take4_pitch.wav"], check=True)
sr, x = wavfile.read(V + "/take4_pitch.wav")
assert sr == SR
x = x.astype(np.float64) / 32768
# (dosyada kesim baslangici, kesim bitisi, dosyada konusma baslangici, videoda konusma baslangici)
raw_cuts = [(0.0, 6.15, 0.40), (6.25, 11.95, 8.50), (12.15, 22.25, 15.70), (22.40, 30.84, 26.90)]
w = int(0.01 * SR)
envx = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same"))
segs = []
for cs, ce, vo in raw_cuts:
    i0 = int(cs * SR)
    k = np.nonzero(envx[i0:i0 + int(1.2 * SR)] > 0.01)[0][0]
    fo = cs + k / SR
    print("kesim %.2f-%.2f, konusma basi dosyada %.3f" % (cs, ce, fo))
    segs.append((cs, ce, fo, vo))
out = np.zeros(int(DUR * SR))
fd = int(0.015 * SR)
for cs, ce, fo, vo in segs:
    seg = x[int(cs * SR):int(ce * SR)].copy()
    seg[:fd] *= np.linspace(0, 1, fd)
    seg[-fd:] *= np.linspace(1, 0, fd)
    start = int(round((vo - (fo - cs)) * SR))
    out[start:start + len(seg)] += seg
    print("parca: video %.2f-%.2f sn" % (start / SR + 0, (start + len(seg)) / SR))
wavfile.write(V + "/voice4_placed.wav", SR, (out * 32767).astype(np.int16))

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1500:])
    return r.stderr

chain = ("highpass=f=70,equalizer=f=200:t=q:w=1.0:g=1.5,equalizer=f=3200:t=q:w=1.0:g=2.0,"
         "deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=0.08:ratio=2.5:attack=12:release=180:makeup=2,"
         "aecho=0.9:0.88:28|53:0.10|0.06")
run(["ffmpeg", "-y", "-loglevel", "error", "-i", V + "/voice4_placed.wav", "-af", chain, V + "/voice4_chain.wav"])
e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", V + "/voice4_chain.wav", "-af", "ebur128=peak=true", "-f", "null", "-"])
lufs = float(re.findall(r"I:\s+(-?\d+\.\d+) LUFS", e)[-1])
gain = -17.0 - lufs
print("ses (zincirden sonra) %.1f LUFS -> kazanc %+.1f dB" % (lufs, gain))
run(["ffmpeg", "-y", "-loglevel", "error", "-i", V + "/voice4_chain.wav", "-af",
     "volume=%.2fdB,alimiter=limit=0.89:level=false,pan=stereo|c0=c0|c1=c0" % gain, V + "/voice4_final.wav"])

fc = ("[0:a]asplit=2[v][vk];"
      "[1:a][vk]sidechaincompress=threshold=0.04:ratio=3:attack=40:release=500:makeup=1[pd];"
      "[pd]volume=0.55[p];[2:a]volume=0.55[s];"
      "[v][p][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=9[m]")
run(["ffmpeg", "-y", "-loglevel", "error", "-i", V + "/voice4_final.wav", "-i", OUT + "/v3_pad.wav", "-i", OUT + "/v3_sfx.wav",
     "-filter_complex", fc, "-map", "[m]", "-ar", "44100", OUT + "/v4_mix.wav"])
e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", OUT + "/v4_mix.wav", "-af", "ebur128=peak=true", "-f", "null", "-"])
print([l.strip() for l in e.splitlines() if re.search(r"^\s+(I|LRA|Peak):", l)][-3:])
