#!/usr/bin/env python3
"""Ana sesin kapanis cumlesini referans kayittaki kapanisla degistirir (yeni ses uretmeden).

Kullanim: python3 kapanis_ekle.py ana.wav KES_ANA ref.wav KES_REF cikti.wav [ANLATIM_SON]
  KES_ANA / KES_REF: kapanis cumlesinin ("Devami") basindan hemen onceki sessiz noktalar (sn); duraklama ana sesteki
  kadar kalsin diye her ikisi de kelime basindan ayni uzaklikta secilir. 30 ms esit-guc gecis. Kapanisin RMS'i
  (konusma kareleri) anlatimin ortalamasina esitlenir; perde degistirme yok.
"""
import sys
import numpy as np
from scipy.io import wavfile

XF = 0.030


def oku(fn):
    sr, x = wavfile.read(fn)
    assert sr == 44100 and x.ndim == 1
    return sr, x.astype(np.float64) / 32768.0


def konusma_rms(x, sr, esik_db=-35.0):
    h = int(0.02 * sr)
    n = len(x) // h
    r = np.sqrt(np.mean(x[:n * h].reshape(n, h) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(r)
    m = db > (db.max() + esik_db)
    return float(np.sqrt(np.mean(r[m] ** 2)))


def main():
    ana_fn, ka, ref_fn, kr, out = sys.argv[1], float(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5]
    son = float(sys.argv[6]) if len(sys.argv) > 6 else ka
    sr, a = oku(ana_fn)
    _, r = oku(ref_fn)
    x = int(XF * sr)
    ia, ir = int(round(ka * sr)), int(round(kr * sr))
    A = a[:ia + x // 2]
    R = r[ir - x // 2:]
    g = konusma_rms(a[:int(son * sr)], sr) / konusma_rms(R, sr)
    R = R * g
    w = np.linspace(0, np.pi / 2, x)
    mid = A[-x:] * np.cos(w) + R[:x] * np.sin(w)
    y = np.concatenate([A[:-x], mid, R[x:]])
    pk = np.max(np.abs(y))
    if pk > 0.99:
        y *= 0.99 / pk
    wavfile.write(out, sr, (y * 32767).astype(np.int16))
    print("kapanis kazanci %.2f dB, sure %.3f sn" % (20 * np.log10(g), len(y) / sr))


if __name__ == "__main__":
    main()
