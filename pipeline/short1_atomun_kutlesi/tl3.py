"""Zaman cizelgesi: eski animasyon zamani <-> yeni (ses'e gore) zaman. Parcali dogrusal."""
SH = 0.8          # 1. gecis erken: nefes boslugu kisaltma
DUR = 39.0 - SH
# (eski_mutlak, yeni_mutlak)
FWD_AB = [(0, 0), (5.0, 3.0), (12.4, 7.2), (14.0, 9.0 - SH)]
FWD_C = [(14.0, 9.0 - SH), (16.4, 11.5 - SH), (20.2, 13.4 - SH), (24.0, 16.4 - SH)]
FWD_D = [(24.0, 16.4 - SH), (25.3, 17.7 - SH), (27.0, 18.5 - SH), (31.0, 20.3 - SH), (33.0, 25.4 - SH)]
E0 = 25.4 - SH          # E sahnesi dogrudan yeni zamanla calisir
XF = [(9.0 - SH, 0.5), (16.4 - SH, 0.5), (25.4 - SH, 0.5)]   # gecis merkezleri, yari genislik

def pw(x, pts):
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        if x <= a1:
            return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    (a0, b0), (a1, b1) = pts[-2], pts[-1]
    return b1 + (x - a1) * (b1 - b0) / (a1 - a0)

def inv(pts):
    return [(b, a) for a, b in pts]

def fwd(t_old):
    if t_old < 14.0:
        return pw(t_old, FWD_AB)
    if t_old < 24.0:
        return pw(t_old, FWD_C)
    return pw(t_old, FWD_D)

INV_AB, INV_C, INV_D = inv(FWD_AB), inv(FWD_C), inv(FWD_D)
