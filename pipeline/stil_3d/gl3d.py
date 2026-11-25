"""Basliksiz (EGL) OpenGL 3D katmani: moderngl ile gercek mesh render.

Dunya koordinati "piksel uzayi"dir: x saga, y ASAGI, z izleyiciye dogru. Kamera donuk
(yaw = pitch = 0) iken z = 0 duzlemindeki (x, y) noktasi ekranda tam (x, y) pikseline duser.
Boylece eski 2D sahne koordinatlari 3D'ye dogrudan tasinir; kamera hafif yorunge / dolly
ile paralaks verir.
"""
import math
import os
import numpy as np

W, H = 1080, 1920
FOVY = math.radians(40.0)
DIST = (H / 2) / math.tan(FOVY / 2)        # z=0 duzleminin 1:1 piksel oldugu uzaklik

# ----------------------------------------------------------------- matris yardimcilari
def _norm(v):
    v = np.asarray(v, np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)

def model(pos=(0, 0, 0), scale=(1, 1, 1), R=None):
    """4x4 model matrisi: once olcek, sonra donus, sonra oteleme."""
    if np.isscalar(scale):
        scale = (scale, scale, scale)
    M = np.eye(4)
    S = np.diag(scale)
    M[:3, :3] = (R if R is not None else np.eye(3)) @ S
    M[:3, 3] = pos
    return M

def perspective(fovy, aspect, near, far):
    f = 1.0 / math.tan(fovy / 2)
    return np.array([[f / aspect, 0, 0, 0],
                     [0, f, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
                     [0, 0, -1, 0]], np.float64)

def look_at(eye, tgt, up):
    f = _norm(np.asarray(tgt) - np.asarray(eye))
    s = _norm(np.cross(f, up))
    u = np.cross(s, f)
    M = np.eye(4)
    M[0, :3], M[1, :3], M[2, :3] = s, u, -f
    M[:3, 3] = -M[:3, :3] @ np.asarray(eye)
    return M

FLIP = np.diag([1.0, -1.0, 1.0, 1.0])      # piksel uzayi (y asagi) -> GL (y yukari)


class Cam:
    """Varsayilan: ekran merkezine bakan, z=0'da 1:1 kamera. pivot etrafinda yaw/pitch,
    dolly < 1 yaklasir."""

    def __init__(self, yaw=0.0, pitch=0.0, dolly=1.0, pivot=(540, 960, 0), shift=(0, 0)):
        self.yaw, self.pitch, self.dolly = yaw, pitch, dolly
        self.pivot = np.asarray(pivot, np.float64)
        tgt = np.array([540.0 + shift[0], 960.0 + shift[1], 0.0])
        eye = tgt + np.array([0, 0, DIST * dolly])
        # dolly < 1: kamera ekran merkezine dogru yaklasir
        R = rot_y(yaw) @ rot_x(pitch)
        pv = self.pivot
        eye_p = pv + R @ (eye - pv)
        tgt_p = pv + R @ (tgt - pv)
        up = R @ np.array([0, -1.0, 0])      # piksel uzayinda yukari = -y
        self.eye = eye_p
        # GL'e gec: FLIP ile
        e_gl = FLIP[:3, :3] @ eye_p
        t_gl = FLIP[:3, :3] @ tgt_p
        u_gl = FLIP[:3, :3] @ up
        self.V = look_at(e_gl, t_gl, u_gl) @ FLIP
        self.P = perspective(FOVY, W / H, 20.0, 40000.0)
        self.VP = self.P @ self.V

    def project(self, p):
        """p: (..., 3) piksel-dunya noktalari -> (sx, sy, olcek, derinlik)."""
        p = np.asarray(p, np.float64)
        one = np.ones(p.shape[:-1] + (1,))
        c = np.concatenate([p, one], -1) @ self.VP.T
        w = c[..., 3]
        sx = (c[..., 0] / w * 0.5 + 0.5) * W
        sy = (1 - (c[..., 1] / w * 0.5 + 0.5)) * H
        vz = (np.concatenate([p, one], -1) @ self.V.T)[..., 2]
        scale = DIST / np.maximum(-vz, 1.0)
        return sx, sy, scale, -vz

    def p2(self, x, y, z=0.0):
        sx, sy, s, _ = self.project([x, y, z])
        return float(sx), float(sy), float(s)


# ----------------------------------------------------------------- mesh uretimi
def mesh_sphere(seg=48, rings=28):
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
            idx += [a, b, a + 1, a + 1, b, b + 1]
    return v[np.array(idx)]

def mesh_cylinder(seg=56, caps=True, bevel=0.06):
    """Yaricap 1, y -0.5..0.5. Kenarlarda hafif pah (yumusak yansima)."""
    tris = []
    def ring(y, r, ny_mix):
        out = []
        for j in range(seg + 1):
            a = 2 * math.pi * j / seg
            c, s = math.cos(a), math.sin(a)
            n = np.array([c * (1 - abs(ny_mix)), ny_mix, s * (1 - abs(ny_mix))])
            n = n / np.linalg.norm(n)
            out.append((r * c, y, r * s, *n))
        return out
    b = bevel
    rows = [ring(-0.5, 1 - b, -0.75), ring(-0.5 + b, 1, -0.0), ring(0.5 - b, 1, 0.0), ring(0.5, 1 - b, 0.75)]
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(seg):
            a0, a1, b0, b1 = r0[j], r0[j + 1], r1[j], r1[j + 1]
            tris += [a0, b0, a1, a1, b0, b1]
    if caps:
        for y, ny in ((-0.5, -1.0), (0.5, 1.0)):
            for j in range(seg):
                a0 = 2 * math.pi * j / seg
                a1 = 2 * math.pi * (j + 1) / seg
                r = 1 - b
                tris += [(0, y, 0, 0, ny, 0), (r * math.cos(a0), y, r * math.sin(a0), 0, ny, 0),
                         (r * math.cos(a1), y, r * math.sin(a1), 0, ny, 0)]
    return np.array(tris, np.float32)

def mesh_rbox(w, h, d, r, n=6):
    """Yuvarlak kenarli kutu (merkez 0). r: kenar yaricapi (piksel)."""
    r = max(0.5, min(r, w / 2 - 0.01, h / 2 - 0.01, d / 2 - 0.01)) if min(w, h, d) > 1.1 else 0.0
    hx, hy, hz = w / 2, h / 2, d / 2
    ix, iy, iz = hx - r, hy - r, hz - r
    tris = []
    faces = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
             ((0, 1, 0), (0, 0, 1), (1, 0, 0)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
             ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (0, 1, 0), (1, 0, 0))]
    for N, U, V in faces:
        N, U, V = np.array(N, float), np.array(U, float), np.array(V, float)
        grid = []
        for i in range(n + 1):
            row = []
            for j in range(n + 1):
                u = -1 + 2 * i / n
                v = -1 + 2 * j / n
                # kup yuzeyi noktasi (birim), kutuya olcekle
                p = N + U * u + V * v
                pb = p * np.array([hx, hy, hz])
                q = np.clip(pb, [-ix, -iy, -iz], [ix, iy, iz])
                dvec = pb - q
                dl = np.linalg.norm(dvec)
                nn = dvec / dl if dl > 1e-9 else N
                pos = q + nn * r if r > 0 else pb
                if r <= 0:
                    nn = N
                row.append((*pos, *nn))
            grid.append(row)
        for i in range(n):
            for j in range(n):
                a, b, c, d2 = grid[i][j], grid[i + 1][j], grid[i][j + 1], grid[i + 1][j + 1]
                tris += [a, b, c, c, b, d2]
    return np.array(tris, np.float32)

def mesh_torus(ratio=0.12, seg=64, sides=20):
    tris = []
    def P(i, j):
        a = 2 * math.pi * i / seg
        b = 2 * math.pi * j / sides
        cx, cz = math.cos(a), math.sin(a)
        n = np.array([math.cos(b) * cx, math.sin(b), math.cos(b) * cz])
        p = np.array([cx, 0, cz]) + n * ratio
        return (*p, *n)
    for i in range(seg):
        for j in range(sides):
            a, b, c, d = P(i, j), P(i + 1, j), P(i, j + 1), P(i + 1, j + 1)
            tris += [a, b, c, c, b, d]
    return np.array(tris, np.float32)

def mesh_cone(seg=40):
    tris = []
    k = 1 / math.sqrt(2)
    for j in range(seg):
        a0 = 2 * math.pi * j / seg
        a1 = 2 * math.pi * (j + 1) / seg
        am = (a0 + a1) / 2
        tris += [(0, 0.5, 0, math.cos(am) * k, k, math.sin(am) * k),
                 (math.cos(a0), -0.5, math.sin(a0), math.cos(a0) * k, k, math.sin(a0) * k),
                 (math.cos(a1), -0.5, math.sin(a1), math.cos(a1) * k, k, math.sin(a1) * k)]
        tris += [(0, -0.5, 0, 0, -1, 0), (math.cos(a0), -0.5, math.sin(a0), 0, -1, 0),
                 (math.cos(a1), -0.5, math.sin(a1), 0, -1, 0)]
    return np.array(tris, np.float32)

def mesh_tube(path, radii, sides=28, flat=1.0):
    """path: (N,3) eksen noktalari, radii: (N,) yaricaplar. Uclari kapali (yaricap ~0 olmali).
    flat: kesitin bir eksende basiklik orani."""
    path = np.asarray(path, float)
    N = len(path)
    rings = []
    up = np.array([0, 0, 1.0])
    for i in range(N):
        tg = path[min(i + 1, N - 1)] - path[max(i - 1, 0)]
        tg /= np.linalg.norm(tg)
        nx = np.cross(tg, up)
        nx /= np.linalg.norm(nx)
        ny = np.cross(nx, tg)
        row = []
        for j in range(sides + 1):
            a = 2 * math.pi * j / sides
            # hafif koseli (muz gibi) kesit
            rr = radii[i] * (1 + 0.06 * math.cos(5 * a))
            off = nx * math.cos(a) * rr + ny * math.sin(a) * rr * flat
            nrm = nx * math.cos(a) * flat + ny * math.sin(a)
            nrm /= np.linalg.norm(nrm)
            row.append((*(path[i] + off), *nrm))
        rings.append(row)
    tris = []
    for i in range(N - 1):
        for j in range(sides):
            a, b, c, d = rings[i][j], rings[i + 1][j], rings[i][j + 1], rings[i + 1][j + 1]
            tris += [a, b, c, c, b, d]
    return np.array(tris, np.float32)


# ----------------------------------------------------------------- golgelendirici
VS = """
#version 330
uniform mat4 VP;
in vec3 in_pos; in vec3 in_nrm;
in vec4 m0; in vec4 m1; in vec4 m2; in vec4 m3;
in vec4 i_col; in vec4 i_mat; in vec4 i_ext;
out vec3 v_w; out vec3 v_n; out vec4 v_col; out vec4 v_mat; out vec4 v_ext; out vec3 v_lp;
void main(){
  mat4 M = mat4(m0, m1, m2, m3);
  vec4 w = M * vec4(in_pos, 1.0);
  v_w = w.xyz;
  v_n = transpose(inverse(mat3(M))) * in_nrm;
  v_col = i_col; v_mat = i_mat; v_ext = i_ext; v_lp = in_pos;
  gl_Position = VP * w;
}
"""

FS = """
#version 330
uniform vec3 eye;
in vec3 v_w; in vec3 v_n; in vec4 v_col; in vec4 v_mat; in vec4 v_ext; in vec3 v_lp;
out vec4 frag;
void main(){
  vec3 N = normalize(v_n);
  vec3 V = normalize(eye - v_w);
  if (dot(N, V) < 0.0) N = -N;
  // piksel uzayi: y asagi. anahtar isik sol-ust-on, dolgu sag-alt (soguk), arka isik
  vec3 Lk = normalize(vec3(-0.55, -0.75, 0.62));
  vec3 Lf = normalize(vec3(0.8, 0.25, 0.45));
  vec3 Lb = normalize(vec3(0.2, -0.6, -0.75));
  vec3 base = v_col.rgb;
  float spec = v_mat.x, shin = v_mat.y * 100.0 + 4.0, rim = v_mat.z, emis = v_mat.w;
  float metal = v_ext.z, ao = v_ext.w;
  // seritler (yerel y ekseni boyunca): bant / pelet ek yeri
  float band = 1.0;
  if (v_ext.x > 0.0) {
    float f = fract(v_lp.y * v_ext.x + 0.5);
    band = 1.0 - v_ext.y * (smoothstep(0.0, 0.06, f) * (1.0 - smoothstep(0.06, 0.12, f)) + (1.0 - smoothstep(0.0, 0.03, f)));
  }
  float dk = max(dot(N, Lk), 0.0);
  float df = max(dot(N, Lf), 0.0);
  float hemi = 0.5 + 0.5 * (-N.y);
  vec3 amb = mix(vec3(0.05, 0.07, 0.14), vec3(0.16, 0.20, 0.32), hemi);
  vec3 diff = base * (amb * 1.4 + vec3(1.0, 0.96, 0.9) * dk * 0.95 + vec3(0.35, 0.55, 0.95) * df * 0.32);
  vec3 Hk = normalize(Lk + V);
  vec3 Hf = normalize(Lf + V);
  vec3 sc = mix(vec3(1.0), base, metal);
  vec3 sp = sc * (pow(max(dot(N, Hk), 0.0), shin) * spec * 1.25 + pow(max(dot(N, Hf), 0.0), shin * 0.6) * spec * 0.25);
  float fr = pow(1.0 - max(dot(N, V), 0.0), 3.0);
  vec3 rimc = mix(vec3(0.35, 0.85, 1.0), base * 1.3 + 0.2, 0.45) * fr * rim;
  float back = pow(max(dot(-V, Lb) * 0.5 + 0.5, 0.0), 2.0) * fr * 0.35;
  vec3 col = (diff * (1.0 - metal * 0.45) + sp) * band * ao + rimc + vec3(0.5, 0.8, 1.0) * back * rim;
  col += base * emis;
  col = col / (1.0 + col * 0.18);          // yumusak ton esleme
  float a = v_col.a;
  frag = vec4(col * a, a);
}
"""

_R = None

class GL3D:
    def __init__(self, samples=4):
        import moderngl
        self.ctx = moderngl.create_standalone_context(backend="egl")
        ctx = self.ctx
        self.prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.samples = samples
        self.ms_fbo = ctx.framebuffer(color_attachments=[ctx.renderbuffer((W, H), 4, samples=samples)],
                                      depth_attachment=ctx.depth_renderbuffer((W, H), samples=samples))
        self.fbo = ctx.framebuffer(color_attachments=[ctx.renderbuffer((W, H), 4)])
        self.meshes = {}
        self.vbos = {}
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.mgl = moderngl

    def mesh(self, key, builder):
        if key not in self.meshes:
            if len(self.meshes) > 400:
                for k in [k for k in self.meshes if isinstance(k, tuple) and k[0] == "dyn"]:
                    self.meshes[k][0].release()
                    del self.meshes[k]
            data = builder()
            vbo = self.ctx.buffer(np.ascontiguousarray(data, np.float32).tobytes())
            self.meshes[key] = (vbo, len(data))
        return self.meshes[key]

    def render(self, cam, items):
        """items: liste (mesh_key, builder, M(4x4), col(rgba 0-1), mat(4), ext(4), transparent)"""
        ctx = self.ctx
        mgl = self.mgl
        if not items:
            return None
        self.ms_fbo.use()
        ctx.clear(0, 0, 0, 0)
        self.prog["VP"].write(np.ascontiguousarray(cam.VP.T, np.float32).tobytes())
        self.prog["eye"].value = tuple(float(x) for x in cam.eye)
        opaque = [it for it in items if not it[6]]
        trans = [it for it in items if it[6]]
        if trans:
            eye = cam.eye
            trans.sort(key=lambda it: -np.linalg.norm(it[2][:3, 3] - eye))
        ctx.enable(mgl.DEPTH_TEST)
        ctx.enable(mgl.BLEND)
        ctx.blend_func = (mgl.ONE, mgl.ONE_MINUS_SRC_ALPHA, mgl.ONE, mgl.ONE_MINUS_SRC_ALPHA)
        ctx.depth_mask = True
        self._draw_groups(opaque)
        if trans:
            ctx.depth_mask = False
            for it in trans:       # sirali, tek tek
                self._draw_groups([it])
            ctx.depth_mask = True
        ctx.copy_framebuffer(self.fbo, self.ms_fbo)
        raw = self.fbo.read(components=4, alignment=1)
        arr = np.frombuffer(raw, np.uint8).reshape(H, W, 4)[::-1]
        return arr

    def _draw_groups(self, items):
        groups = {}
        for it in items:
            groups.setdefault(it[0], []).append(it)
        for key, its in groups.items():
            vbo, n = self.mesh(key, its[0][1])
            inst = np.zeros((len(its), 28), np.float32)
            for i, it in enumerate(its):
                inst[i, :16] = np.asarray(it[2], np.float32).T.reshape(-1)
                inst[i, 16:20] = it[3]
                inst[i, 20:24] = it[4]
                inst[i, 24:28] = it[5]
            ibo = self.ctx.buffer(inst.tobytes())
            vao = self.ctx.vertex_array(self.prog, [
                (vbo, "3f 3f", "in_pos", "in_nrm"),
                (ibo, "4f 4f 4f 4f 4f 4f 4f/i", "m0", "m1", "m2", "m3", "i_col", "i_mat", "i_ext")])
            vao.render(instances=len(its))
            vao.release()
            ibo.release()


def get():
    global _R
    if _R is None:
        _R = GL3D()
    return _R
