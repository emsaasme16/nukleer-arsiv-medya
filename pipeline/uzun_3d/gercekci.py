"""Gercekci 3D motor (moderngl, EGL, yazilim GL'de de calisir). Bolum 2 ile eklendi.

Dunya koordinati METRE, y YUKARI. Kamera look-at. Ozellikler:
  - PBR benzeri malzeme (GGX speküler + Lambert, metal/purluluk), prosedurel dokular (beton, ahsap,
    fircalanmis metal, boyali panel, toprak/cim, seramik, su), emisyon
  - analitik gokyuzu (gunduz/alacakaranlik/gece; gunes, ay, yildiz, bulut), yarim kure ortam isigi,
    gokyuzunden spekuler yansima
  - yonlu isik golge haritasi (PCF), 4 nokta isik
  - ustel yukseklik sisi, su alti kostik deseni
  - SSAO (yarim cozunurluk), alan derinligi, bloom, ACES ton esleme, vinyet, gren (cv2 ile)
  - yumusak parcaciklar (buhar, duman, toz, kabarcik, isik noktalari)
Kullanim: S = Sahne(); S.add(mesh, M, Mat(...)); S.particles(...); img = render(S, cam)
"""
import math
import numpy as np
import cv2

W, H = 1920, 1080
SHADOW = 2048

# ----------------------------------------------------------------- matematik
def norm(v):
    v = np.asarray(v, np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


def TRS(pos=(0, 0, 0), R=None, s=1.0):
    if np.isscalar(s):
        s = (s, s, s)
    M = np.eye(4)
    M[:3, :3] = (R if R is not None else np.eye(3)) @ np.diag(s)
    M[:3, 3] = pos
    return M


def align(a, b, r):
    """a'dan b'ye uzanan, yaricapi r olan (birim silindir y -0.5..0.5) icin model matrisi."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    y = d / max(L, 1e-9)
    t = np.array([1.0, 0, 0]) if abs(y[0]) < 0.9 else np.array([0, 0, 1.0])
    x = norm(np.cross(y, t))
    z = np.cross(x, y)
    R = np.stack([x, y, z], 1)
    return TRS((a + b) / 2, R, (r, L, r))


def perspective(fovy, aspect, near, far):
    f = 1.0 / math.tan(fovy / 2)
    return np.array([[f / aspect, 0, 0, 0], [0, f, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
                     [0, 0, -1, 0]], np.float64)


def ortho(l, r, b, t, n, f):
    return np.array([[2 / (r - l), 0, 0, -(r + l) / (r - l)], [0, 2 / (t - b), 0, -(t + b) / (t - b)],
                     [0, 0, -2 / (f - n), -(f + n) / (f - n)], [0, 0, 0, 1]], np.float64)


def look_at(eye, tgt, up=(0, 1, 0)):
    f = norm(np.asarray(tgt, float) - np.asarray(eye, float))
    s = norm(np.cross(f, up))
    u = np.cross(s, f)
    M = np.eye(4)
    M[0, :3], M[1, :3], M[2, :3] = s, u, -f
    M[:3, 3] = -M[:3, :3] @ np.asarray(eye, float)
    return M


class Cam:
    def __init__(self, eye, tgt, fov=40.0, near=0.05, far=5000.0, up=(0, 1, 0), roll=0.0,
                 focus=None, aperture=0.0):
        self.eye = np.asarray(eye, np.float64)
        self.tgt = np.asarray(tgt, np.float64)
        up = np.asarray(up, float)
        if roll:
            f = norm(self.tgt - self.eye)
            c, s = math.cos(roll), math.sin(roll)
            up = up * c + np.cross(f, up) * s
        self.fov = math.radians(fov)
        self.near, self.far = near, far
        self.V = look_at(self.eye, self.tgt, up)
        self.P = perspective(self.fov, W / H, near, far)
        self.VP = self.P @ self.V
        self.focus = focus if focus is not None else float(np.linalg.norm(self.tgt - self.eye))
        self.aperture = aperture          # 0: keskin; 1: belirgin alan derinligi
        self.right = self.V[0, :3].copy()
        self.upv = self.V[1, :3].copy()
        self.fwd = -self.V[2, :3].copy()

    def project(self, p):
        p = np.asarray(p, np.float64)
        c = self.VP @ np.append(p, 1.0)
        if c[3] <= 1e-6:
            return None
        return ((c[0] / c[3] * 0.5 + 0.5) * W, (1 - (c[1] / c[3] * 0.5 + 0.5)) * H, c[3])


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def cam_lerp(c0, c1, t, **kw):
    """iki kamera arasinda (goz/hedef) yumusak gecis."""
    return Cam(lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), fov=c0[2] * (1 - t) + c1[2] * t, **kw)


# ----------------------------------------------------------------- malzeme
PAT = {"duz": 0, "beton": 1, "ahsap": 2, "fircali": 3, "su": 4, "boya": 5, "toprak": 6, "seramik": 7,
       "kafes": 8, "cim": 9, "asfalt": 10, "plastik": 11, "kagit": 12, "karton": 13}


class Mat:
    __slots__ = ("col", "rough", "metal", "pat", "scale", "emi", "alpha", "add", "cast")

    def __init__(self, col=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, pat="duz", scale=1.0, emi=(0, 0, 0),
                 alpha=1.0, add=False, cast=True):
        self.col = tuple(col)
        self.rough, self.metal = rough, metal
        self.pat = PAT[pat] if isinstance(pat, str) else pat
        self.scale = scale
        self.emi = tuple(emi)
        self.alpha = alpha
        self.add = add
        self.cast = cast

    def but(self, **kw):
        m = Mat(self.col, self.rough, self.metal, self.pat, self.scale, self.emi, self.alpha, self.add, self.cast)
        for k, v in kw.items():
            if k == "pat" and isinstance(v, str):
                v = PAT[v]
            setattr(m, k, v)
        return m


def srgb(c):
    """0-255 sRGB -> dogrusal 0-1"""
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


# ----------------------------------------------------------------- mesh uretimi (konum + normal)
def m_box():
    tris = []
    for ax in range(3):
        for sgn in (-1, 1):
            n = np.zeros(3)
            n[ax] = sgn
            u = np.zeros(3)
            u[(ax + 1) % 3] = 1
            v = np.cross(n, u)
            c = n * 0.5
            p = [c + (-u - v) * 0.5, c + (u - v) * 0.5, c + (u + v) * 0.5, c + (-u + v) * 0.5]
            for i in (0, 1, 2, 0, 2, 3):
                tris.append((*p[i], *n))
    return np.array(tris, np.float32)


def m_sphere(seg=32, rings=18):
    v = []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(seg + 1):
            ph = 2 * math.pi * j / seg
            n = (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
            v.append(n + n)
    v = np.array(v, np.float32)
    idx = []
    for i in range(rings):
        for j in range(seg):
            a = i * (seg + 1) + j
            b = a + seg + 1
            idx += [a, a + 1, b, a + 1, b + 1, b]
    return v[np.array(idx)]


def m_lathe(profile, seg=48, smooth=True, cap0=False, cap1=False):
    """profile: [(r, y), ...] alttan uste. y ekseni etrafinda dondurulmus yuzey."""
    pr = np.asarray(profile, float)
    n = len(pr)
    # profil normalleri (2D)
    nr = np.zeros((n, 2))
    for i in range(n):
        a = pr[max(i - 1, 0)]
        b = pr[min(i + 1, n - 1)]
        d = b - a
        nn = np.array([d[1], -d[0]])
        nr[i] = nn / (np.linalg.norm(nn) + 1e-12)
    tris = []
    for j in range(seg):
        a0 = 2 * math.pi * j / seg
        a1 = 2 * math.pi * (j + 1) / seg
        for i in range(n - 1):
            quad = []
            for (ii, aa) in ((i, a0), (i, a1), (i + 1, a1), (i + 1, a0)):
                r, y = pr[ii]
                if smooth:
                    nx, ny = nr[ii]
                else:
                    d = pr[i + 1] - pr[i]
                    nn = np.array([d[1], -d[0]])
                    nn /= np.linalg.norm(nn) + 1e-12
                    nx, ny = nn
                c, s = math.cos(aa), math.sin(aa)
                quad.append((r * c, y, r * s, nx * c, ny, nx * s))
            for k in (0, 2, 1, 0, 3, 2):
                tris.append(quad[k])
        for cap, (r, y), ny in ((cap0, pr[0], -1.0), (cap1, pr[-1], 1.0)):
            if cap and r > 0:
                p0 = (0, y, 0, 0, ny, 0)
                p1 = (r * math.cos(a0), y, r * math.sin(a0), 0, ny, 0)
                p2 = (r * math.cos(a1), y, r * math.sin(a1), 0, ny, 0)
                tris += [p0, p1, p2] if ny > 0 else [p0, p2, p1]
    return np.array(tris, np.float32)


def m_cyl(seg=32, cap=True):
    return m_lathe([(1, -0.5), (1, 0.5)], seg, smooth=True, cap0=cap, cap1=cap)


def m_torus(R=1.0, r=0.2, seg=48, sides=16):
    tris = []

    def P(i, j):
        a = 2 * math.pi * i / seg
        b = 2 * math.pi * j / sides
        cx, cz = math.cos(a), math.sin(a)
        n = np.array([math.cos(b) * cx, math.sin(b), math.cos(b) * cz])
        p = np.array([cx * R, 0, cz * R]) + n * r
        return (*p, *n)
    for i in range(seg):
        for j in range(sides):
            a, b, c, d = P(i, j), P(i + 1, j), P(i, j + 1), P(i + 1, j + 1)
            tris += [a, c, b, b, c, d]
    return np.array(tris, np.float32)


def m_tube(path, r, sides=12):
    """path (N,3) boyunca sabit yaricapli boru (tel, yay)."""
    path = np.asarray(path, float)
    N = len(path)
    rings = []
    prev = None
    for i in range(N):
        tg = norm(path[min(i + 1, N - 1)] - path[max(i - 1, 0)])
        if prev is None:
            t = np.array([0, 1.0, 0]) if abs(tg[1]) < 0.9 else np.array([1.0, 0, 0])
            nx = norm(np.cross(tg, t))
        else:
            nx = norm(prev - tg * np.dot(prev, tg))
        prev = nx
        ny = np.cross(tg, nx)
        row = []
        for j in range(sides + 1):
            a = 2 * math.pi * j / sides
            nn = nx * math.cos(a) + ny * math.sin(a)
            row.append((*(path[i] + nn * r), *nn))
        rings.append(row)
    tris = []
    for i in range(N - 1):
        for j in range(sides):
            a, b, c, d = rings[i][j], rings[i + 1][j], rings[i][j + 1], rings[i + 1][j + 1]
            tris += [a, b, c, c, b, d]
    return np.array(tris, np.float32)


def m_plane(n=1):
    """xz duzlemi, -0.5..0.5, normal +y; n x n bolum."""
    tris = []
    for i in range(n):
        for j in range(n):
            x0, x1 = -0.5 + i / n, -0.5 + (i + 1) / n
            z0, z1 = -0.5 + j / n, -0.5 + (j + 1) / n
            p = [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)]
            for k in (0, 2, 1, 0, 3, 2):
                tris.append((*p[k], 0, 1, 0))
    return np.array(tris, np.float32)


def m_hyperboloid(r_base, r_throat, r_top, h, y_throat, seg=64, rows=40, wall=0.0):
    """dogal cekisli sogutma kulesi kabugu (dis yuzey; wall>0 ise ic yuzey de)."""
    prof = []
    for i in range(rows + 1):
        y = h * i / rows
        if y <= y_throat:
            k = y / y_throat
            r = r_throat + (r_base - r_throat) * (1 - k) ** 1.6
        else:
            k = (y - y_throat) / (h - y_throat)
            r = r_throat + (r_top - r_throat) * k ** 1.8
        prof.append((r, y))
    out = m_lathe(prof, seg)
    if wall > 0:
        inner = [(r - wall, y) for r, y in prof][::-1]
        out = np.concatenate([out, m_lathe(inner, seg)])
        # ust kenar
        rt = prof[-1][0]
        out = np.concatenate([out, m_lathe([(rt - wall, h), (rt, h)], seg)])
    return out


# ----------------------------------------------------------------- golgelendiriciler
_NOISE = """
float hash(vec3 p){ p = fract(p*0.3183099+.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float noise(vec3 x){ vec3 i=floor(x); vec3 f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hash(i+vec3(0,0,0)),hash(i+vec3(1,0,0)),f.x), mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x), mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z); }
float fbm(vec3 p){ float a=0.5, s=0.0; for(int i=0;i<4;i++){ s+=a*noise(p); p=p*2.03+vec3(1.7,9.2,3.1); a*=0.5; } return s; }
"""

_SKY = """
uniform vec3 sunDir; uniform vec3 sunCol; uniform vec3 skyZen; uniform vec3 skyHor; uniform vec3 gndCol;
uniform vec4 skyMisc;   // x: yildiz, y: bulut, z: gunes diski, w: ay
uniform vec3 moonDir;
vec3 skyColor(vec3 d, float rough){
  float h = d.y;
  vec3 c = mix(skyHor, skyZen, pow(clamp(h,0.0,1.0), 0.45));
  c = mix(c, gndCol*0.6, smoothstep(0.0,-0.12,h));
  float sd = max(dot(d, sunDir), 0.0);
  c += sunCol * (pow(sd, 8.0)*0.08 + pow(sd, 64.0)*0.25) * (1.0-rough*0.5);
  return c;
}
"""

VS_MAIN = """
#version 330
uniform mat4 VP; uniform mat4 LVP;
in vec3 in_pos; in vec3 in_nrm;
in vec4 m0; in vec4 m1; in vec4 m2; in vec4 m3;
in vec4 i_col; in vec4 i_pbr; in vec4 i_emi;
out vec3 v_w; out vec3 v_n; out vec3 v_lp; out vec4 v_col; out vec4 v_pbr; out vec4 v_emi; out vec4 v_ls; out vec3 v_ln;
void main(){
  mat4 M = mat4(m0, m1, m2, m3);
  vec4 w = M * vec4(in_pos, 1.0);
  v_w = w.xyz; v_lp = in_pos; v_ln = in_nrm;
  v_n = transpose(inverse(mat3(M))) * in_nrm;
  v_col = i_col; v_pbr = i_pbr; v_emi = i_emi;
  v_ls = LVP * w;
  gl_Position = VP * w;
}
"""

FS_MAIN = """
#version 330
uniform vec3 eye; uniform float time;
uniform sampler2DShadow shadowMap; uniform float shadowOn; uniform float shadowBias;
uniform vec4 fogP; uniform vec3 fogCol;           // fogP: yogunluk, yukseklik azalmasi, taban y, en cok
uniform vec4 caus;                                // kostik: guc, olcek, hiz, su yuzeyi y
uniform int nPL; uniform vec4 plPos[6]; uniform vec4 plCol[6];
uniform float ambK; uniform float envK;
""" + _NOISE + _SKY + """
in vec3 v_w; in vec3 v_n; in vec3 v_lp; in vec4 v_col; in vec4 v_pbr; in vec4 v_emi; in vec4 v_ls; in vec3 v_ln;
out vec4 frag;
const float PI = 3.14159265;
float D_GGX(float NoH, float a){ NoH=clamp(NoH,0.0,1.0); float a2=a*a; float d=NoH*NoH*(a2-1.0)+1.0; return a2/(PI*d*d+1e-6); }
float G_S(float NoV, float NoL, float r){ float k=(r+1.0)*(r+1.0)/8.0; return (NoV/(NoV*(1.0-k)+k))*(NoL/(NoL*(1.0-k)+k)); }
vec3 F_S(float c, vec3 F0){ return F0 + (1.0-F0)*pow(clamp(1.0-c,0.0,1.0), 5.0); }
float shadowF(vec3 N, vec3 L){
  if (shadowOn < 0.5) return 1.0;
  vec3 p = v_ls.xyz / v_ls.w * 0.5 + 0.5;
  if (p.x<0.0||p.x>1.0||p.y<0.0||p.y>1.0||p.z>1.0) return 1.0;
  float b = shadowBias * (1.0 + 2.0*(1.0-max(dot(N,L),0.0)));
  float s = 0.0; float tx = 1.0/2048.0;
  for(int i=-1;i<=1;i++) for(int j=-1;j<=1;j++) s += texture(shadowMap, vec3(p.xy+vec2(i,j)*tx*1.2, p.z-b));
  return s/9.0;
}
void main(){
  vec3 N = v_n; if (dot(N,N) < 1e-12) N = vec3(0.0,1.0,0.0); N = normalize(N);
  vec3 V = normalize(eye - v_w);
  if (dot(N, V) < 0.0) N = -N;
  vec3 base = v_col.rgb; float alpha = v_col.a;
  float rough = v_pbr.x, metal = v_pbr.y; int pat = int(v_pbr.z+0.5); float sc = v_pbr.w;
  vec3 P = v_w * sc; vec3 LP = v_lp * sc;
  float ao = 1.0;
  if (pat==1){ // beton
    float n1 = fbm(P*1.3), n2 = noise(P*9.0);
    base *= 0.78 + 0.32*n1 + 0.08*n2;
    base *= 1.0 - 0.18*smoothstep(0.55,0.8,fbm(P*0.35+vec3(0,v_w.y*0.4*sc,0)));   // lekeler
    rough = clamp(rough + 0.1*(n2-0.5), 0.05, 1.0);
  } else if (pat==2){ // ahsap (yerel x boyunca damar)
    float g = fbm(vec3(LP.x*0.6, LP.y*9.0, LP.z*9.0));
    float ring = sin((LP.y*14.0 + LP.z*6.0 + g*7.0))*0.5+0.5;
    base *= mix(0.72, 1.12, ring) * (0.9 + 0.2*noise(vec3(LP.x*30.0, LP.y*2.0, LP.z*2.0)));
    rough = clamp(rough + 0.15*(g-0.5), 0.1, 1.0);
  } else if (pat==3){ // fircalanmis metal (yerel y boyunca)
    float s = noise(vec3(LP.x*180.0, LP.y*1.5, LP.z*180.0));
    base *= 0.9 + 0.12*s; rough = clamp(rough + 0.12*(s-0.5), 0.05, 1.0);
  } else if (pat==5){ // boyali panel: yatay ek yerleri + kir
    float f = fract(LP.y*1.0);
    float seam = smoothstep(0.0,0.02,f)*(1.0-smoothstep(0.98,1.0,f));
    float fx = fract(LP.x*0.5 + LP.z*0.5);
    seam *= smoothstep(0.0,0.01,fx)*(1.0-smoothstep(0.99,1.0,fx));
    base *= (0.75 + 0.25*seam) * (0.9 + 0.15*fbm(P*0.8));
    base *= 1.0 - 0.15*smoothstep(0.5,0.9,fbm(vec3(P.x*0.3, P.y*2.0, P.z*0.3)));
  } else if (pat==6){ // toprak
    float n = fbm(P*0.7); base *= 0.7 + 0.5*n; rough = 0.95;
  } else if (pat==9){ // cim
    float n = fbm(P*0.5), m = noise(P*6.0);
    base = mix(base, base*vec3(1.25,1.1,0.6), n) * (0.8+0.3*m); rough = 0.95;
  } else if (pat==7){ // seramik (pelet): ince taneli
    float n = noise(P*400.0); base *= 0.85 + 0.3*n; rough = clamp(rough + 0.2*(n-0.5), 0.1, 1.0);
  } else if (pat==8){ // demet ust baslik: kare izgara delikleri (yerel xz)
    vec2 g = fract(LP.xz*17.0) - 0.5; float d = length(g);
    float hole = 1.0 - smoothstep(0.26, 0.32, d);
    if (abs(v_ln.y) > 0.5) { base *= 1.0 - 0.85*hole; ao *= 1.0 - 0.6*hole; }
  } else if (pat==10){ // asfalt
    float n = noise(P*30.0); base *= 0.8 + 0.4*n; rough = 0.9;
  } else if (pat==12){ // kagit
    base *= 0.95 + 0.06*noise(P*60.0);
  } else if (pat==13){ // karton
    base *= 0.85 + 0.2*fbm(P*3.0) + 0.05*noise(P*80.0);
  } else if (pat==4){ // su yuzeyi: dalgali normal
    float t = time;
    vec3 q = vec3(v_w.x, 0.0, v_w.z)*sc;
    float e = 0.02;
    float h0 = fbm(q*0.8 + vec3(t*0.15,0,t*0.11));
    float hx = fbm((q+vec3(e,0,0))*0.8 + vec3(t*0.15,0,t*0.11));
    float hz = fbm((q+vec3(0,0,e))*0.8 + vec3(t*0.15,0,t*0.11));
    N = normalize(N + vec3(-(hx-h0)/e, 0.0, -(hz-h0)/e)*0.35);
  }
  vec3 L = normalize(sunDir);
  float NoL = clamp(dot(N, L), 0.0, 1.0), NoV = clamp(dot(N, V), 1e-3, 1.0);
  vec3 Hh = normalize(L + V + vec3(0.0, 1e-5, 0.0));
  float NoH = clamp(dot(N, Hh), 0.0, 1.0), VoH = clamp(dot(V, Hh), 0.0, 1.0);
  float a = max(rough*rough, 0.002);
  vec3 F0 = mix(vec3(0.04), base, metal);
  vec3 F = F_S(VoH, F0);
  vec3 spec = D_GGX(NoH, a) * G_S(NoV, NoL, rough) * F / (4.0*NoV*max(NoL,1e-3)+1e-4);
  vec3 kd = (1.0 - F) * (1.0 - metal);
  float sh = shadowF(N, L);
  vec3 col = (kd*base/PI + spec) * sunCol * NoL * sh * PI;
  // nokta isiklar
  for (int i=0;i<6;i++){ if (i>=nPL) break;
    vec3 d = plPos[i].xyz - v_w; float dist = length(d); vec3 l = d/dist;
    float att = 1.0/(1.0 + dist*dist/(plPos[i].w*plPos[i].w));
    float nl = max(dot(N,l),0.0);
    vec3 hh = normalize(l+V+vec3(0.0,1e-5,0.0));
    vec3 sp = D_GGX(max(dot(N,hh),0.0), a)*G_S(NoV,nl,rough)*F_S(max(dot(V,hh),0.0),F0)/(4.0*NoV*max(nl,1e-3)+1e-4);
    col += (kd*base/PI + sp) * plCol[i].rgb * plCol[i].a * nl * att * PI;
  }
  // ortam: yarim kure + gokyuzu yansimasi
  float hemi = N.y*0.5+0.5;
  vec3 amb = mix(gndCol, mix(skyHor, skyZen, 0.5), hemi) * ambK;
  vec3 R = reflect(-V, N);
  vec3 Fr = F0 + (max(vec3(1.0-rough), F0) - F0) * pow(clamp(1.0-NoV,0.0,1.0), 5.0);
  vec3 env = skyColor(R, rough) * envK;
  float spAO = mix(1.0, 0.4, rough);
  col += (kd*base*amb + env*Fr*spAO) * ao;
  // su alti kostik
  if (caus.x > 0.0 && v_w.y < caus.w){
    vec3 q = v_w*caus.y + vec3(time*caus.z, 0, time*caus.z*0.7);
    float c1 = noise(q), c2 = noise(q*1.9+vec3(3.1));
    float cc = pow(clamp(1.0 - abs(c1-c2)*2.0, 0.0, 1.0), 8.0);
    col += base * cc * caus.x * max(N.y*0.6+0.4, 0.0);
  }
  col += v_emi.rgb * v_emi.a;
  // sis
  float dist = length(eye - v_w);
  float hf = exp(-max(v_w.y - fogP.z, 0.0)*fogP.y);
  float fog = clamp(1.0 - exp(-dist*fogP.x*hf), 0.0, fogP.w);
  vec3 fc = fogCol + sunCol*0.15*pow(max(dot(-V, L),0.0), 6.0);
  col = mix(col, fc, fog);
  frag = vec4(col*alpha, alpha);
}
"""

VS_SHADOW = """
#version 330
uniform mat4 LVP;
in vec3 in_pos;
in vec4 m0; in vec4 m1; in vec4 m2; in vec4 m3;
void main(){ mat4 M = mat4(m0,m1,m2,m3); gl_Position = LVP * M * vec4(in_pos,1.0); }
"""
FS_SHADOW = """
#version 330
void main(){}
"""

VS_GEO = """
#version 330
uniform mat4 VP; uniform mat4 V;
in vec3 in_pos; in vec3 in_nrm;
in vec4 m0; in vec4 m1; in vec4 m2; in vec4 m3;
out vec3 v_vn; out float v_d;
void main(){ mat4 M = mat4(m0,m1,m2,m3); vec4 w = M*vec4(in_pos,1.0);
  vec4 vp = V*w; v_d = -vp.z; v_vn = mat3(V)*(transpose(inverse(mat3(M)))*in_nrm);
  gl_Position = VP*w; }
"""
FS_GEO = """
#version 330
in vec3 v_vn; in float v_d;
out vec4 frag;
void main(){ vec3 n = normalize(v_vn); if (n.z < 0.0) n = -n; frag = vec4(n, v_d); }
"""

VS_FULL = """
#version 330
in vec2 in_xy; out vec2 uv;
void main(){ uv = in_xy*0.5+0.5; gl_Position = vec4(in_xy, 0.0, 1.0); }
"""
FS_SKY = """
#version 330
uniform mat4 invVP; uniform float time;
""" + _NOISE + _SKY + """
in vec2 uv; out vec4 frag;
void main(){
  vec4 a = invVP * vec4(uv*2.0-1.0, -1.0, 1.0); vec4 b = invVP * vec4(uv*2.0-1.0, 1.0, 1.0);
  vec3 d = normalize(b.xyz/b.w - a.xyz/a.w);
  vec3 c = skyColor(d, 0.0);
  float sd = max(dot(d, sunDir), 0.0);
  c += sunCol * smoothstep(0.9996, 0.99985, sd) * 30.0 * skyMisc.z;
  if (skyMisc.w > 0.0){
    float md = dot(d, normalize(moonDir));
    float disk = smoothstep(0.99965, 0.9998, md);
    float tex = 0.75 + 0.25*noise(d*900.0);
    c += vec3(0.9,0.92,1.0) * disk * tex * 3.0 * skyMisc.w;
    c += vec3(0.25,0.3,0.45) * pow(max(md,0.0), 400.0) * 0.5 * skyMisc.w;
  }
  if (skyMisc.x > 0.0 && d.y > 0.0){
    vec3 g = floor(d*420.0);
    float s = hash(g);
    float st = step(0.9986, s) * (0.5 + 0.5*sin(time*2.0 + s*90.0)) * smoothstep(0.0, 0.25, d.y);
    c += vec3(0.8,0.85,1.0) * st * skyMisc.x * 0.9;
  }
  if (skyMisc.y > 0.0 && d.y > 0.0){
    vec2 p = d.xz / (d.y + 0.15) * 1.2 + vec2(time*0.01, 0.0);
    float cl = smoothstep(0.45, 0.85, fbm(vec3(p*1.4, time*0.02)));
    vec3 cc = mix(skyHor*1.1, sunCol*0.25 + skyZen*0.6, 0.5);
    c = mix(c, cc, cl * skyMisc.y * smoothstep(0.0, 0.2, d.y));
  }
  frag = vec4(c, 1.0);
}
"""

FS_SSAO = """
#version 330
uniform sampler2D geo; uniform mat4 P; uniform float radius; uniform vec2 px;
in vec2 uv; out vec4 frag;
""" + _NOISE + """
vec3 viewPos(vec2 t){ vec4 g = texture(geo, t); float d = g.a; if (d <= 0.0) return vec3(0,0,-1e6);
  vec2 ndc = t*2.0-1.0; return vec3(ndc.x*d/P[0][0], ndc.y*d/P[1][1], -d); }
void main(){
  vec4 g = texture(geo, uv);
  if (g.a <= 0.0){ frag = vec4(1.0); return; }
  vec3 p = viewPos(uv); vec3 n = normalize(g.xyz);
  float occ = 0.0; float rr = radius * clamp(g.a*0.08, 0.15, 3.0);
  float ang = hash(vec3(gl_FragCoord.xy, 1.0))*6.2831;
  for (int i=0;i<12;i++){
    float fi = float(i);
    float th = ang + fi*2.39996; float rad = rr * (0.2 + 0.8*fract(fi*0.618+0.3));
    vec3 t = normalize(cross(n, vec3(0.0,0.0,1.0)+vec3(0.01,0.02,0.0)));
    vec3 bt = cross(n, t);
    vec3 dir = normalize(t*cos(th) + bt*sin(th) + n*(0.4+0.6*fract(fi*0.371)));
    vec3 s = p + dir*rad;
    vec4 c = P*vec4(s,1.0); vec2 st = c.xy/c.w*0.5+0.5;
    if (st.x<0.0||st.x>1.0||st.y<0.0||st.y>1.0) continue;
    float sd = texture(geo, st).a; if (sd <= 0.0) continue;
    float diff = (-s.z) - sd;
    occ += step(0.02*rr, diff) * smoothstep(0.0, 1.0, rr/abs(diff));
  }
  frag = vec4(vec3(1.0 - occ/12.0), 1.0);
}
"""

VS_PART = """
#version 330
uniform mat4 VP; uniform vec3 camR; uniform vec3 camU;
in vec2 in_xy;
in vec4 p_pos; in vec4 p_col; in vec4 p_par;
out vec2 v_uv; out vec4 v_col; out vec4 v_par; out vec3 v_w;
void main(){
  float s = p_pos.w; float rot = p_par.z;
  vec2 q = vec2(in_xy.x*cos(rot)-in_xy.y*sin(rot), in_xy.x*sin(rot)+in_xy.y*cos(rot));
  vec3 w = p_pos.xyz + (camR*q.x + camU*q.y)*s;
  v_uv = in_xy; v_col = p_col; v_par = p_par; v_w = w;
  gl_Position = VP*vec4(w,1.0);
}
"""
FS_PART = """
#version 330
uniform vec3 eye; uniform vec4 fogP; uniform vec3 fogCol;
""" + _NOISE + """
in vec2 v_uv; in vec4 v_col; in vec4 v_par; in vec3 v_w;
out vec4 frag;
void main(){
  float r = length(v_uv);
  if (r > 1.0) discard;
  float a;
  int kind = int(v_par.x+0.5);
  if (kind == 1){       // duman/buhar: gurultulu yumusak
    float n = fbm(vec3(v_uv*1.6 + v_par.y, v_par.y*0.3));
    a = smoothstep(1.0, 0.1, r) * (0.35 + 0.9*n);
    a = clamp(a, 0.0, 1.0);
  } else if (kind == 2){ // kabarcik: halka
    a = smoothstep(1.0, 0.85, r) * smoothstep(0.55, 0.85, r) + 0.15*smoothstep(1.0,0.0,r);
  } else {               // isik noktasi / toz
    a = pow(max(1.0 - r, 0.0), 2.2);
  }
  float dist = length(eye - v_w);
  float fog = clamp(1.0 - exp(-dist*fogP.x), 0.0, fogP.w);
  vec3 c = mix(v_col.rgb, fogCol, fog*0.7);
  float al = a * v_col.a;
  frag = vec4(c*al, v_par.w > 0.5 ? 0.0 : al);
}
"""


# ----------------------------------------------------------------- sahne
class Sahne:
    def __init__(self):
        self.items = []          # (key, builder, M, Mat)
        self.parts = []          # (pos3, size, rgba, kind, seed, rot, additive)
        self.sun_dir = norm((0.4, 0.8, 0.3))
        self.sun_col = (3.0, 2.85, 2.6)
        self.sky_zen = (0.18, 0.35, 0.75)
        self.sky_hor = (0.65, 0.75, 0.9)
        self.gnd = (0.25, 0.23, 0.2)
        self.stars = 0.0
        self.clouds = 0.0
        self.sun_disk = 1.0
        self.moon = 0.0
        self.moon_dir = norm((-0.3, 0.5, -0.8))
        self.fog = (0.0, 0.0, 0.0, 0.0)
        self.fog_col = (0.6, 0.7, 0.85)
        self.caus = (0.0, 1.0, 0.5, 0.0)
        self.lights = []         # (pos, radius, rgb, strength)
        self.amb = 1.0
        self.env = 1.0
        self.shadow = True
        self.shadow_box = ((0, 0, 0), 30.0)   # merkez, yaricap
        self.shadow_bias = 0.0015
        self.bg = None           # None: gokyuzu; aksi halde duz renk (dogrusal)
        self.exposure = 1.0
        self.ssao = 0.8
        self.ssao_r = 0.5
        self.bloom = 0.6
        self.bloom_th = 1.0
        self.vignette = 0.35
        self.grain = 1.0
        self.time = 0.0
        self.tint = None

    def add(self, mesh, M, mat):
        if mat.alpha <= 0.003:
            return
        self.items.append((mesh[0], mesh[1], M, mat))

    def particle(self, pos, size, rgba, kind=0, seed=0.0, rot=0.0, add=False):
        if rgba[3] <= 0.002:
            return
        self.parts.append((pos, size, rgba, kind, seed, rot, add))

    def light(self, pos, radius, rgb, k=1.0):
        self.lights.append((pos, radius, rgb, k))


# hazir mesh anahtarlari
BOX = ("box", m_box)
SPH = ("sph", m_sphere)
SPH_LO = ("sph_lo", lambda: m_sphere(14, 8))
CYL = ("cyl", m_cyl)
CYL_LO = ("cyl_lo", lambda: m_cyl(10))
CYL_OPEN = ("cyl_open", lambda: m_cyl(32, False))
PLANE = ("plane", m_plane)
PLANE_HI = ("plane_hi", lambda: m_plane(24))


class Renderer:
    def __init__(self, samples=4):
        import moderngl
        self.mgl = moderngl
        ctx = moderngl.create_standalone_context(backend="egl")
        self.ctx = ctx
        self.p_main = ctx.program(vertex_shader=VS_MAIN, fragment_shader=FS_MAIN)
        self.p_shadow = ctx.program(vertex_shader=VS_SHADOW, fragment_shader=FS_SHADOW)
        self.p_geo = ctx.program(vertex_shader=VS_GEO, fragment_shader=FS_GEO)
        self.p_sky = ctx.program(vertex_shader=VS_FULL, fragment_shader=FS_SKY)
        self.p_ssao = ctx.program(vertex_shader=VS_FULL, fragment_shader=FS_SSAO)
        self.p_part = ctx.program(vertex_shader=VS_PART, fragment_shader=FS_PART)
        self.ms = ctx.framebuffer(color_attachments=[ctx.renderbuffer((W, H), 4, samples=samples, dtype="f2")],
                                  depth_attachment=ctx.depth_renderbuffer((W, H), samples=samples))
        self.res = ctx.framebuffer(color_attachments=[ctx.renderbuffer((W, H), 4, dtype="f2")])
        self.shadow_tex = ctx.depth_texture((SHADOW, SHADOW))
        self.shadow_tex.compare_func = "<="
        self.shadow_tex.repeat_x = self.shadow_tex.repeat_y = False
        self.shadow_fbo = ctx.framebuffer(depth_attachment=self.shadow_tex)
        gw, gh = W // 2, H // 2
        self.gw, self.gh = gw, gh
        self.geo_tex = ctx.texture((gw, gh), 4, dtype="f4")
        self.geo_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.geo_fbo = ctx.framebuffer(color_attachments=[self.geo_tex], depth_attachment=ctx.depth_renderbuffer((gw, gh)))
        self.ao_tex = ctx.texture((gw, gh), 4, dtype="f1")
        self.ao_fbo = ctx.framebuffer(color_attachments=[self.ao_tex])
        quad = np.array([-1, -1, 3, -1, -1, 3], np.float32)
        self.full = ctx.buffer(quad.tobytes())
        self.vao_sky = ctx.vertex_array(self.p_sky, [(self.full, "2f", "in_xy")])
        self.vao_ssao = ctx.vertex_array(self.p_ssao, [(self.full, "2f", "in_xy")])
        pq = np.array([-1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1], np.float32)
        self.pquad = ctx.buffer(pq.tobytes())
        self.meshes = {}

    def mesh(self, key, builder):
        m = self.meshes.get(key)
        if m is None:
            data = np.ascontiguousarray(builder(), np.float32)
            m = (self.ctx.buffer(data.tobytes()), len(data), float(np.linalg.norm(data[:, :3], axis=1).max()))
            self.meshes[key] = m
        return m

    def _set(self, prog, name, val):
        if name in prog:
            u = prog[name]
            if isinstance(val, np.ndarray) and val.ndim == 2:
                u.write(np.ascontiguousarray(val.T, np.float32).tobytes())
            else:
                u.value = val

    def _groups(self, items):
        g = {}
        for it in items:
            g.setdefault(it[0], []).append(it)
        return g

    def _inst(self, its, full=True):
        n = len(its)
        inst = np.zeros((n, 28 if full else 16), np.float32)
        for i, it in enumerate(its):
            inst[i, :16] = np.asarray(it[2], np.float32).T.reshape(-1)
            if full:
                m = it[3]
                inst[i, 16:19] = m.col
                inst[i, 19] = m.alpha
                inst[i, 20:24] = (m.rough, m.metal, m.pat, m.scale)
                e = m.emi
                inst[i, 24:27] = e[:3]
                inst[i, 27] = 1.0
        return inst

    def _cull(self, its, bound, planes):
        Ms = np.stack([np.asarray(it[2], np.float64) for it in its])
        c = Ms[:, :3, 3]
        sc = np.sqrt((Ms[:, :3, :3] ** 2).sum(1)).max(1) * bound
        d = c @ planes[:, :3].T + planes[:, 3]
        ok = (d >= -sc[:, None]).all(1)
        return [it for it, k in zip(its, ok) if k]

    def _draw(self, prog, items, full=True, fmt_main=True, planes=None):
        for key, its in self._groups(items).items():
            vbo, n, bound = self.mesh(key, its[0][1])
            if planes is not None:
                its = self._cull(its, bound, planes)
                if not its:
                    continue
            inst = self._inst(its, full)
            ibo = self.ctx.buffer(inst.tobytes())
            if full:
                attrs = [(vbo, "3f 3f", "in_pos", "in_nrm"),
                         (ibo, "4f 4f 4f 4f 4f 4f 4f/i", "m0", "m1", "m2", "m3", "i_col", "i_pbr", "i_emi")]
            elif fmt_main:      # geo: konum + normal
                attrs = [(vbo, "3f 3f", "in_pos", "in_nrm"), (ibo, "4f 4f 4f 4f/i", "m0", "m1", "m2", "m3")]
            else:               # golge: yalniz konum
                attrs = [(vbo, "3f 12x", "in_pos"), (ibo, "4f 4f 4f 4f/i", "m0", "m1", "m2", "m3")]
            vao = self.ctx.vertex_array(prog, attrs)
            vao.render(instances=len(its))
            vao.release()
            ibo.release()

    def render(self, S, cam):
        ctx, mgl = self.ctx, self.mgl
        opaque = [it for it in S.items if it[3].alpha >= 0.999 and not it[3].add]
        trans = [it for it in S.items if not (it[3].alpha >= 0.999 and not it[3].add)]
        # --- golge
        c, r = S.shadow_box
        c = np.asarray(c, float)
        L = norm(S.sun_dir)
        LV = look_at(c + L * r * 2.0, c, (0, 1, 0) if abs(L[1]) < 0.99 else (1, 0, 0))
        LP = ortho(-r, r, -r, r, 0.1, r * 4.0)
        LVP = LP @ LV
        shadow_on = S.shadow and L[1] > 0.02
        if shadow_on:
            self.shadow_fbo.use()
            ctx.enable(mgl.DEPTH_TEST)
            ctx.disable(mgl.BLEND)
            ctx.clear(depth=1.0)
            ctx.viewport = (0, 0, SHADOW, SHADOW)
            self._set(self.p_shadow, "LVP", LVP)
            self._draw(self.p_shadow, [it for it in opaque if it[3].cast], full=False, fmt_main=False)
        # --- geometri (SSAO + alan derinligi icin, yarim cozunurluk)
        self.geo_fbo.use()
        ctx.viewport = (0, 0, self.gw, self.gh)
        ctx.enable(mgl.DEPTH_TEST)
        ctx.disable(mgl.BLEND)
        ctx.clear(0, 0, 0, 0, depth=1.0)
        self._set(self.p_geo, "VP", cam.VP)
        self._set(self.p_geo, "V", cam.V)
        VPm = cam.VP
        pl = np.array([VPm[3] + VPm[0], VPm[3] - VPm[0], VPm[3] + VPm[1], VPm[3] - VPm[1], VPm[3] + VPm[2], VPm[3] - VPm[2]])
        pl = pl / np.linalg.norm(pl[:, :3], axis=1, keepdims=True)
        self._draw(self.p_geo, opaque, full=False, fmt_main=True, planes=pl)
        geo = np.frombuffer(self.geo_tex.read(), np.float32).reshape(self.gh, self.gw, 4)[::-1].copy()
        ao = None
        if S.ssao > 0 and opaque:
            self.ao_fbo.use()
            ctx.disable(mgl.DEPTH_TEST)
            self.geo_tex.use(0)
            self._set(self.p_ssao, "geo", 0)
            self._set(self.p_ssao, "P", cam.P)
            self._set(self.p_ssao, "radius", float(S.ssao_r))
            self.vao_ssao.render(mgl.TRIANGLES, vertices=3)
            ao = np.frombuffer(self.ao_tex.read(), np.uint8).reshape(self.gh, self.gw, 4)[::-1, :, 0].astype(np.float32) / 255.0
        # --- ana gecis
        self.ms.use()
        ctx.viewport = (0, 0, W, H)
        if S.bg is None:
            ctx.disable(mgl.DEPTH_TEST)
            ctx.clear(0, 0, 0, 1, depth=1.0)
            p = self.p_sky
            self._set(p, "invVP", np.linalg.inv(cam.VP))
            self._uni_sky(p, S)
            self.vao_sky.render(mgl.TRIANGLES, vertices=3)
        else:
            ctx.clear(*S.bg, 1.0, depth=1.0)
        ctx.enable(mgl.DEPTH_TEST)
        ctx.enable(mgl.BLEND)
        ctx.blend_func = (mgl.ONE, mgl.ONE_MINUS_SRC_ALPHA)
        p = self.p_main
        self._set(p, "VP", cam.VP)
        self._set(p, "LVP", LVP)
        self._set(p, "eye", tuple(float(x) for x in cam.eye))
        self._uni_sky(p, S)
        self._set(p, "shadowOn", 1.0 if shadow_on else 0.0)
        self._set(p, "shadowBias", float(S.shadow_bias))
        self.shadow_tex.use(1)
        self._set(p, "shadowMap", 1)
        self._set(p, "fogP", tuple(float(x) for x in S.fog))
        self._set(p, "fogCol", tuple(float(x) for x in S.fog_col))
        self._set(p, "caus", tuple(float(x) for x in S.caus))
        self._set(p, "ambK", float(S.amb))
        self._set(p, "envK", float(S.env))
        nl = min(len(S.lights), 6)
        self._set(p, "nPL", nl)
        if nl:
            pp = np.zeros((6, 4), np.float32)
            pc = np.zeros((6, 4), np.float32)
            for i, (pos, rad, rgb, k) in enumerate(S.lights[:6]):
                pp[i] = (*pos, rad)
                pc[i] = (*rgb, k)
            p["plPos"].write(pp.tobytes())
            p["plCol"].write(pc.tobytes())
        ctx.depth_mask = True
        self._draw(p, opaque, planes=pl)
        if trans:
            ctx.depth_mask = False
            trans.sort(key=lambda it: -np.linalg.norm(it[2][:3, 3] - cam.eye))
            for it in trans:
                if it[3].add:
                    ctx.blend_func = (mgl.ONE, mgl.ONE)
                self._draw(p, [it])
                ctx.blend_func = (mgl.ONE, mgl.ONE_MINUS_SRC_ALPHA)
            ctx.depth_mask = True
        if S.parts:
            self._particles(S, cam)
        ctx.copy_framebuffer(self.res, self.ms)
        img = np.frombuffer(self.res.read(components=4, dtype="f2"), np.float16).reshape(H, W, 4)[::-1, :, :3].astype(np.float32)
        return img, geo, ao

    def _uni_sky(self, p, S):
        self._set(p, "sunDir", tuple(float(x) for x in norm(S.sun_dir)))
        self._set(p, "sunCol", tuple(float(x) for x in S.sun_col))
        self._set(p, "skyZen", tuple(float(x) for x in S.sky_zen))
        self._set(p, "skyHor", tuple(float(x) for x in S.sky_hor))
        self._set(p, "gndCol", tuple(float(x) for x in S.gnd))
        self._set(p, "skyMisc", (float(S.stars), float(S.clouds), float(S.sun_disk), float(S.moon)))
        self._set(p, "moonDir", tuple(float(x) for x in norm(S.moon_dir)))
        self._set(p, "time", float(S.time))

    def _particles(self, S, cam):
        ctx, mgl = self.ctx, self.mgl
        parts = sorted(S.parts, key=lambda q: -np.linalg.norm(np.asarray(q[0]) - cam.eye))
        n = len(parts)
        arr = np.zeros((n, 12), np.float32)
        for i, (pos, size, rgba, kind, seed, rot, add) in enumerate(parts):
            arr[i, 0:3] = pos
            arr[i, 3] = size
            arr[i, 4:8] = rgba
            arr[i, 8:12] = (kind, seed, rot, 1.0 if add else 0.0)
        p = self.p_part
        self._set(p, "VP", cam.VP)
        self._set(p, "camR", tuple(float(x) for x in cam.right))
        self._set(p, "camU", tuple(float(x) for x in cam.upv))
        self._set(p, "eye", tuple(float(x) for x in cam.eye))
        self._set(p, "fogP", tuple(float(x) for x in S.fog))
        self._set(p, "fogCol", tuple(float(x) for x in S.fog_col))
        ibo = ctx.buffer(arr.tobytes())
        vao = ctx.vertex_array(p, [(self.pquad, "2f", "in_xy"), (ibo, "4f 4f 4f/i", "p_pos", "p_col", "p_par")])
        ctx.depth_mask = False
        ctx.blend_func = (mgl.ONE, mgl.ONE_MINUS_SRC_ALPHA)
        vao.render(mgl.TRIANGLES, instances=n)
        ctx.depth_mask = True
        vao.release()
        ibo.release()


_R = None


def renderer():
    global _R
    if _R is None:
        _R = Renderer()
    return _R


# ----------------------------------------------------------------- son isleme (cv2)
_GRN = None


def _aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def post(S, cam, img, geo, ao, t=0.0):
    global _GRN
    hdr = np.nan_to_num(img, nan=0.0, posinf=60.0, neginf=0.0)
    hdr = np.minimum(hdr, 60.0)
    depth = geo[..., 3]
    if ao is not None and S.ssao > 0:
        a = cv2.GaussianBlur(ao, (0, 0), 1.5)
        a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
        hdr = hdr * (1 - S.ssao * (1 - a))[..., None]
    # alan derinligi
    if cam.aperture > 0:
        d = cv2.resize(depth, (W, H), interpolation=cv2.INTER_NEAREST)
        d = np.where(d <= 0, cam.far, d)
        coc = np.clip(np.abs(1.0 / np.maximum(d, 1e-3) - 1.0 / cam.focus) * cam.focus * cam.aperture, 0, 1)
        coc = cv2.GaussianBlur(coc, (0, 0), 6)
        small = cv2.resize(hdr, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        b1 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2.0), (W, H), interpolation=cv2.INTER_LINEAR)
        b2 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6.0), (W, H), interpolation=cv2.INTER_LINEAR)
        k1 = np.clip(coc * 2, 0, 1)[..., None]
        k2 = np.clip(coc * 2 - 1, 0, 1)[..., None]
        hdr = hdr * (1 - k1) + b1 * k1
        hdr = hdr * (1 - k2) + b2 * k2
    hdr = hdr * S.exposure
    if S.bloom > 0:
        q = cv2.resize(hdr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        br = np.maximum(q - S.bloom_th, 0)
        bl = cv2.GaussianBlur(br, (0, 0), 3) * 0.5 + cv2.GaussianBlur(br, (0, 0), 10) * 0.35 + \
            cv2.GaussianBlur(br, (0, 0), 28) * 0.25
        hdr = hdr + cv2.resize(bl, (W, H), interpolation=cv2.INTER_LINEAR) * S.bloom
    if S.tint is not None:
        hdr = hdr * np.asarray(S.tint, np.float32)
    out = _aces(hdr)
    out = np.power(out, 1 / 2.2)
    if S.vignette > 0:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
        out = out * (1 - S.vignette * np.clip(r - 0.3, 0, 1) ** 1.5)[..., None]
    out = out * 255.0
    if S.grain > 0:
        if _GRN is None:
            rg = np.random.default_rng(5)
            _GRN = [cv2.resize(rg.normal(0, 1.6, (H // 2, W // 2)).astype(np.float32), (W, H)) for _ in range(6)]
        out = out + _GRN[int(t * 30) % 6][..., None] * S.grain
    return np.clip(out, 0, 255).astype(np.uint8)


def ciz(S, cam, t=0.0):
    S.time = t
    R = renderer()
    img, geo, ao = R.render(S, cam)
    return post(S, cam, img, geo, ao, t)


# ----------------------------------------------------------------- ortam hazir ayarlari
def gece(S, moon=0.8):
    S.sun_dir = norm((-0.35, 0.42, -0.6))        # ay isigi yonu (golge icin)
    S.sun_col = (0.32, 0.38, 0.55)
    S.sky_zen = (0.004, 0.008, 0.025)
    S.sky_hor = (0.03, 0.045, 0.08)
    S.gnd = (0.01, 0.012, 0.018)
    S.stars = 1.0
    S.sun_disk = 0.0
    S.moon = moon
    S.moon_dir = S.sun_dir
    S.amb = 1.2
    S.env = 0.8
    S.fog = (0.0016, 0.02, 0.0, 0.75)
    S.fog_col = (0.025, 0.035, 0.06)
    S.exposure = 1.4


def gunduz(S):
    S.sun_dir = norm((0.45, 0.55, 0.35))
    S.sun_col = (3.2, 3.0, 2.7)
    S.sky_zen = (0.16, 0.32, 0.72)
    S.sky_hor = (0.62, 0.72, 0.88)
    S.gnd = (0.22, 0.2, 0.17)
    S.clouds = 0.5
    S.amb = 1.0
    S.fog = (0.0006, 0.01, 0.0, 0.6)
    S.fog_col = (0.6, 0.7, 0.85)


def ic_mekan(S, warm=True):
    S.bg = (0.01, 0.01, 0.012)
    S.sun_disk = 0.0
    S.sky_zen = (0.12, 0.11, 0.1) if warm else (0.08, 0.1, 0.14)
    S.sky_hor = (0.16, 0.14, 0.12) if warm else (0.1, 0.12, 0.16)
    S.gnd = (0.06, 0.05, 0.045)
    S.amb = 0.6
    S.env = 0.5


def atom_ortami(S):
    """atom alti olcek: koyu, derin, hafif mavi sisli bosluk."""
    S.bg = (0.006, 0.01, 0.025)
    S.sun_dir = norm((-0.5, 0.7, 0.5))
    S.sun_col = (2.2, 2.1, 2.0)
    S.sky_zen = (0.05, 0.09, 0.2)
    S.sky_hor = (0.1, 0.14, 0.26)
    S.gnd = (0.02, 0.025, 0.05)
    S.sun_disk = 0.0
    S.shadow = False
    S.amb = 0.9
    S.env = 1.0
    S.ssao = 0.0
    S.fog = (0.0, 0.0, 0.0, 0.0)
    S.bloom = 0.9
    S.bloom_th = 0.8
