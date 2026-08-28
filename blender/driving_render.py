"""
MOTORLINE — generator de driving render, fara Blender.

Randeaza aceeasi coregrafie ca service-auto_engine.py (aceleasi piese, acelasi
timing, aceeasi camera) cu un rasterizator scris de mana, si scoate tot ce are
nevoie pasul de AI:

  beauty/   secventa opaca, pe fundal de studio   -> driving video pentru v2v
  alpha/    aceeasi secventa cu fundal transparent -> merge direct in site
  depth/    harta de adancime (alb = aproape)      -> control de profunzime
  normal/   orientarea suprafetelor                -> impiedica AI-ul sa inventeze geometrie
  ancora_*.png  un cadru la rezolutie dubla        -> il duci in generatorul de imagini

Rulare:
    python3 blender/driving_render.py
    python3 blender/driving_render.py --w 1280 --frames 90 --still 62
"""
import math, os, sys, random, argparse
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--w", type=int, default=1280)
ap.add_argument("--frames", type=int, default=90)
ap.add_argument("--still", type=int, default=46)
ap.add_argument("--out", default="render/service-auto")
ap.add_argument("--site", default="service-auto/hero/frames")
ap.add_argument("--ss", type=int, default=2, help="supersampling")
A = ap.parse_args()

W, H, N = A.w, int(A.w * 0.625), A.frames
SS = A.ss
random.seed(20260828)

# ============================================================== geometrie
def _n(v):
    L = math.sqrt(sum(c*c for c in v)) or 1.0
    return [c/L for c in v]

def _sub(quad, res, bevel=0.30):
    """Taie un patrulater in res x res bucati si inclina normala catre exterior
    langa margini. Fara asta, o fata mare de cub are o singura culoare si arata
    a carton; cu ea apare dunga de lumina pe muchie, care e tot ce face metalul
    sa fie citit ca metal."""
    a, b, c, d = quad
    ab = lambda t: [a[i]+(b[i]-a[i])*t for i in range(3)]
    dc = lambda t: [d[i]+(c[i]-d[i])*t for i in range(3)]
    P = lambda u, v: [ab(u)[i]+(dc(u)[i]-ab(u)[i])*v for i in range(3)]
    e1 = [b[i]-a[i] for i in range(3)]
    e2 = [d[i]-a[i] for i in range(3)]
    nf = _n([e1[1]*e2[2]-e1[2]*e2[1], e1[2]*e2[0]-e1[0]*e2[2], e1[0]*e2[1]-e1[1]*e2[0]])
    t1, t2 = _n(e1), _n(e2)
    out = []
    for i in range(res):
        for j in range(res):
            u0, u1 = i/res, (i+1)/res
            v0, v1 = j/res, (j+1)/res
            um, vm = (u0+u1)/2, (v0+v1)/2
            # cat de aproape de margine, pe fiecare axa (-1 = margine "jos", 1 = "sus")
            du = 0.0 if 0.5/res < um < 1-0.5/res else (1 if um > 0.5 else -1)
            dv = 0.0 if 0.5/res < vm < 1-0.5/res else (1 if vm > 0.5 else -1)
            nn = [nf[k] + bevel*(du*t1[k] + dv*t2[k]) for k in range(3)]
            out.append({"v": [P(u0,v0), P(u1,v0), P(u1,v1), P(u0,v1)], "n": _n(nn)})
    return out

def box(cx, cy, cz, sx, sy, sz, res=4):
    x, y, z = sx/2, sy/2, sz/2
    v = [(cx-x,cy-y,cz-z),(cx+x,cy-y,cz-z),(cx+x,cy+y,cz-z),(cx-x,cy+y,cz-z),
         (cx-x,cy-y,cz+z),(cx+x,cy-y,cz+z),(cx+x,cy+y,cz+z),(cx-x,cy+y,cz+z)]
    quads = [(v[0],v[3],v[2],v[1]),(v[4],v[5],v[6],v[7]),(v[0],v[1],v[5],v[4]),
             (v[2],v[3],v[7],v[6]),(v[1],v[2],v[6],v[5]),(v[0],v[4],v[7],v[3])]
    polys = []
    # fetele mari merita subdivizate, muchiile mici nu — economisim fete
    big = max(sx, sy, sz) > 0.5
    for q in quads:
        polys += _sub(q, res if big else 1)
    return polys

def cyl(cx, cy, cz, r, h, axis="z", seg=24):
    """Cilindru cu normale netede pe lateral — asa se vede rotund, nu fatetat."""
    ring = []
    for i in range(seg):
        a = 2*math.pi*i/seg
        c, s = math.cos(a), math.sin(a)
        if axis == "z":
            p0, p1, nrm = (cx+c*r,cy+s*r,cz-h/2), (cx+c*r,cy+s*r,cz+h/2), [c,s,0]
        elif axis == "x":
            p0, p1, nrm = (cx-h/2,cy+c*r,cz+s*r), (cx+h/2,cy+c*r,cz+s*r), [0,c,s]
        else:
            p0, p1, nrm = (cx+c*r,cy-h/2,cz+s*r), (cx+c*r,cy+h/2,cz+s*r), [c,0,s]
        ring.append((p0, p1, nrm))
    polys = []
    for i in range(seg):
        a0, a1, na = ring[i]
        b0, b1, nb = ring[(i+1) % seg]
        polys.append({"v": [a0, a1, b1, b0],
                      "n": _n([(na[k]+nb[k])/2 for k in range(3)])})
    ax = {"z": [0,0,1], "x": [1,0,0], "y": [0,1,0]}[axis]
    polys.append({"v": [r[0] for r in ring][::-1], "n": [-c for c in ax]})
    polys.append({"v": [r[1] for r in ring], "n": ax})
    return polys

# culoare de baza, cat de metalic (0..1), cat de lucios (exponent)
MAT = {
    "iron":    ((0.30,0.32,0.35), 0.80, 24),
    "alu":     ((0.60,0.63,0.68), 0.95, 64),
    "steel":   ((0.72,0.75,0.79), 1.00, 110),
    "exhaust": ((0.34,0.24,0.19), 0.85, 40),
    "rubber":  ((0.09,0.09,0.10), 0.05, 12),
    "accent":  ((0.78,0.20,0.11), 0.50, 70),
}

PARTS = []
def add(polys, mat, order):
    PARTS.append({"polys": polys, "m": MAT[mat], "o": order})

CX = [-0.75, -0.25, 0.25, 0.75]
R = lambda: None
add(cyl(0,0,-0.70,0.085,2.30,"x"), "steel", 0)
for x in CX: add(cyl(x,0,-0.70,0.235,0.10,"x"), "steel", 0)
add(cyl(1.28,0,-0.70,0.40,0.11,"x"), "steel", 0)
for x in CX:
    add(cyl(x,0,0.30,0.215,0.34), "alu", 1)
    add(box(x,0,-0.20,0.075,0.11,0.52), "steel", 1)
    for s in (-1,1):
        add(cyl(x,0,0.30+s*0.10,0.222,0.022), "steel", 1)
add(box(0,0,0.05,2.30,1.40,1.15), "iron", 2)
add(box(0,0,0.83,2.30,1.40,0.42), "alu", 3)
for s in (-1,1):
    add(cyl(0,s*0.30,1.00,0.075,2.10,"x"), "steel", 3)
    for x in CX: add(cyl(x,s*0.30,1.00,0.125,0.09,"x"), "steel", 3)
    for x in CX: add(cyl(x,s*0.22,0.78,0.055,0.44), "steel", 3)
add(box(0,0,1.14,2.10,1.22,0.20), "accent", 4)
add(cyl(0.80,0.36,1.26,0.13,0.10), "alu", 4)
add(box(0,0,-1.02,2.05,1.22,0.42), "iron", 5)
add(box(0,1.12,0.86,1.95,0.46,0.44), "alu", 6)
for x in CX: add(cyl(x,0.86,0.86,0.105,0.62,"y"), "alu", 6)
add(cyl(-1.10,1.12,0.86,0.19,0.22,"x"), "alu", 6)
for x in CX: add(cyl(x,-0.92,0.72,0.10,0.52,"y"), "exhaust", 7)
add(cyl(0,-1.22,0.34,0.13,1.90,"x"), "exhaust", 7)
add(cyl(-1.18,-1.36,0.10,0.36,0.30,"y"), "exhaust", 8)
add(cyl(-1.18,-1.36,-0.42,0.30,0.26,"y"), "alu", 8)
add(cyl(-1.32,0,-0.70,0.30,0.13,"x"), "steel", 9)
add(cyl(-1.32,0.52,0.30,0.18,0.11,"x"), "steel", 9)
add(cyl(-1.32,-0.48,0.34,0.16,0.11,"x"), "steel", 9)
for x in (-1.02,-0.50,0.0,0.50,1.02):
    for y in (-0.62,0.62):
        add(cyl(x,y,1.04,0.048,0.11), "steel", 10)
        add(cyl(x,y,-0.82,0.048,0.11), "steel", 10)

MAXO = max(p["o"] for p in PARTS)
FIRST, LAST = 4, int(N*0.86)
SPAN = LAST - FIRST
for p in PARTS:
    t0 = FIRST + SPAN*(p["o"]/(MAXO+1)) + random.uniform(0, SPAN*0.05)
    p["t0"], p["t1"] = t0, min(t0 + SPAN*0.30, N)
    d = [random.uniform(-1,1)*1.8, random.uniform(-1,1)*1.2, random.uniform(-1,1)*1.0]
    L = math.sqrt(sum(c*c for c in d)) or 1
    p["off"] = [c/L*random.uniform(5.5,13.0) for c in d]
    p["spin"] = [random.uniform(-2.6,2.6) for _ in range(3)]
    pts = [v for q in p["polys"] for v in q["v"]]
    p["cen"] = [sum(v[i] for v in pts)/len(pts) for i in range(3)]

print(f"[motorline] {len(PARTS)} piese, {sum(len(p['polys']) for p in PARTS)} fete")

# ================================================================ camera
def rot(v, rx, ry, rz):
    x, y, z = v
    y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
    x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
    x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
    return [x, y, z]

def norm3(v):
    L = math.sqrt(sum(c*c for c in v)) or 1
    return [c/L for c in v]

def basis(eye, tgt):
    f = norm3([tgt[i]-eye[i] for i in range(3)])
    up = [0, 0, 1]
    r = norm3([f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]])
    u = [r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], r[0]*f[1]-r[1]*f[0]]
    return r, u, f

ease_out = lambda t: 1-(1-t)**3

# lumini in spatiul lumii: cheie calda, umplere rece, contur rosu de brand
KEY  = (norm3([0.55,-0.52,0.68]), (1.00,0.95,0.88), 1.05)
FILL = (norm3([-0.72,-0.30,0.18]), (0.55,0.68,1.00), 0.34)
RIM  = (norm3([-0.35,0.85,0.22]), (1.00,0.30,0.16), 0.95)
AMB  = (0.10,0.11,0.13)

def studio_bg(w, h):
    """fundal de atelier: gradient rece + halou rosu, ca in CSS-ul paginii"""
    bg = Image.new("RGB", (w, h), (14,16,19))
    d = ImageDraw.Draw(bg)
    for i in range(h):
        t = i/h
        d.line([(0,i),(w,i)], fill=(int(21-7*t), int(24-8*t), int(29-10*t)))
    glow = Image.new("RGB", (w, h), (0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w*0.42, -h*0.34, w*1.14, h*0.72], fill=(74,22,12))
    gd.ellipse([-w*0.24, h*0.44, w*0.44, h*1.28], fill=(14,26,52))
    glow = glow.filter(ImageFilter.GaussianBlur(w*0.09))
    return Image.blend(bg, Image.blend(bg, glow, 0.85), 0.55)

# ================================================================ randare
def frame_faces(fr, w, h):
    """intoarce fetele proiectate, sortate din spate in fata"""
    g = (fr-1)/(N-1) if N > 1 else 0
    # Mult mai aproape decat prima varianta: motorul trebuie sa umple cadrul,
    # nu sa pluteasca intr-un colt. Tinta e putin sub centrul geometric, ca
    # partea de sus (capacul rosu) sa nu iasa din cadru la final.
    eye = [4.30+(2.95-4.30)*g, -5.20+(-3.95+5.20)*g, 2.35+(1.05-2.35)*g]
    RB, UB, FB = basis(eye, [0, 0, 0.06])
    rig = math.radians(-13 + 26*g)
    fl = 1.62
    out = []
    for p in PARTS:
        t = 0 if fr <= p["t0"] else (1 if fr >= p["t1"]
             else ease_out((fr-p["t0"])/(p["t1"]-p["t0"])))
        off = [c*(1-t) for c in p["off"]]
        spin = [c*(1-t) for c in p["spin"]]
        cen = p["cen"]
        base, metal, shin = p["m"]
        for face in p["polys"]:
            poly = []
            for v in face["v"]:
                q = rot([v[i]-cen[i] for i in range(3)], *spin)
                q = rot([q[i]+cen[i]+off[i] for i in range(3)], 0, 0, rig)
                d = [q[i]-eye[i] for i in range(3)]
                cam = [sum(d[i]*RB[i] for i in range(3)),
                       sum(d[i]*UB[i] for i in range(3)),
                       max(0.05, sum(d[i]*FB[i] for i in range(3)))]
                poly.append((w/2 + cam[0]/cam[2]*fl*w/2,
                             h/2 - cam[1]/cam[2]*fl*w/2, cam[2], q))
            zc = sum(q[2] for q in poly)/len(poly)
            # normala precalculata, rotita ca piesa
            n = rot(rot(face["n"], *spin), 0, 0, rig)
            wc = [sum(q[3][i] for q in poly)/len(poly) for i in range(3)]
            view = norm3([eye[i]-wc[i] for i in range(3)])
            if sum(n[i]*view[i] for i in range(3)) < 0:      # backface
                continue
            col = [AMB[i]*base[i] for i in range(3)]
            spec = 0.0
            for Ldir, Lcol, Lint in (KEY, FILL, RIM):
                lam = max(0.0, sum(n[i]*Ldir[i] for i in range(3)))
                halfv = norm3([Ldir[i]+view[i] for i in range(3)])
                sp = max(0.0, sum(n[i]*halfv[i] for i in range(3))) ** shin
                for i in range(3):
                    col[i] += base[i]*lam*Lcol[i]*Lint
                    col[i] += sp*Lcol[i]*Lint*(0.35+0.65*metal)
                spec += sp*Lint
            fres = (1 - max(0.0, sum(n[i]*view[i] for i in range(3)))) ** 4
            for i in range(3):
                col[i] += fres * 0.20 * metal
            rgb = tuple(max(0, min(255, int((c/(c+0.9))*277))) for c in col)
            ncam = [sum(n[i]*RB[i] for i in range(3)),
                    sum(n[i]*UB[i] for i in range(3)),
                    sum(n[i]*FB[i] for i in range(3))]
            out.append({"z": zc, "p": [(q[0],q[1]) for q in poly],
                        "c": rgb, "n": ncam})
    out.sort(key=lambda f: -f["z"])
    return out

ZN, ZF = 1.8, 12.0

def render(fr, w, h, ss, passes=("beauty","alpha","depth","normal")):
    W2, H2 = w*ss, h*ss
    faces = frame_faces(fr, W2, H2)
    res = {}
    if "alpha" in passes or "beauty" in passes:
        im = Image.new("RGBA", (W2,H2), (0,0,0,0))
        d = ImageDraw.Draw(im, "RGBA")
        for f in faces:
            d.polygon(f["p"], fill=f["c"]+(255,))
        im = im.resize((w,h), Image.LANCZOS)
        res["alpha"] = im
        if "beauty" in passes:
            bg = studio_bg(w,h).convert("RGBA")
            bg.alpha_composite(im)
            res["beauty"] = bg.convert("RGB")
    if "depth" in passes:
        im = Image.new("L", (W2,H2), 0)
        d = ImageDraw.Draw(im)
        for f in faces:
            t = (f["z"]-ZN)/(ZF-ZN)
            d.polygon(f["p"], fill=max(0, min(255, int(255*(1-t)))))
        res["depth"] = im.resize((w,h), Image.LANCZOS)
    if "normal" in passes:
        im = Image.new("RGB", (W2,H2), (128,128,255))
        d = ImageDraw.Draw(im)
        for f in faces:
            n = f["n"]
            d.polygon(f["p"], fill=(int((n[0]*.5+.5)*255),
                                    int((n[1]*.5+.5)*255),
                                    int((-n[2]*.5+.5)*255)))
        res["normal"] = im.resize((w,h), Image.LANCZOS)
    return res

# ================================================================ executie
for sub in ("beauty","alpha","depth","normal"):
    os.makedirs(f"{A.out}/{sub}", exist_ok=True)
os.makedirs(A.site, exist_ok=True)

for fr in range(1, N+1):
    r = render(fr, W, H, SS)
    r["beauty"].save(f"{A.out}/beauty/{fr:04d}.png")
    r["depth"].save(f"{A.out}/depth/{fr:04d}.png")
    r["normal"].save(f"{A.out}/normal/{fr:04d}.png")
    r["alpha"].save(f"{A.out}/alpha/{fr:04d}.png")
    r["alpha"].save(f"{A.site}/motor_{fr:04d}.webp", "WEBP", quality=76, method=4)
    if fr % 15 == 0:
        print(f"  cadru {fr}/{N}")

# cadrul-ancora, la rezolutie dubla, pentru generatorul de imagini
st = render(A.still, W*2, H*2, SS)
st["beauty"].save(f"{A.out}/ancora_frame{A.still:04d}.png")
st["depth"].save(f"{A.out}/ancora_depth{A.still:04d}.png")
print(f"[motorline] ancora: {A.out}/ancora_frame{A.still:04d}.png  ({W*2}x{H*2})")

tot = sum(os.path.getsize(f"{A.site}/{f}") for f in os.listdir(A.site))
print(f"[motorline] site: {N} cadre webp, {tot/1024/1024:.2f} MB")
