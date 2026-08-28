"""
Generator de cadre de TEST pentru heroul Motorline.

NU e arta finala. Randeaza aceeasi coregrafie ca service-auto_engine.py
(aceleasi piese, acelasi timing, aceeasi camera) cu un rasterizator minimal,
ca sa poti verifica scroll-ul, incadrarea si greutatea paginii inainte sa
pornesti Blender. Cand ai randarile reale, suprascrii pur si simplu folderul.

    python3 blender/_testframes.py
"""
import math, os, random
from PIL import Image, ImageDraw

W, H, N = 1200, 750, 90
OUT = "service-auto/hero/frames"
random.seed(20260828)

# --------------------------------------------------------------- mesh utils
def box(cx, cy, cz, sx, sy, sz):
    x, y, z = sx / 2, sy / 2, sz / 2
    v = [(cx-x,cy-y,cz-z),(cx+x,cy-y,cz-z),(cx+x,cy+y,cz-z),(cx-x,cy+y,cz-z),
         (cx-x,cy-y,cz+z),(cx+x,cy-y,cz+z),(cx+x,cy+y,cz+z),(cx-x,cy+y,cz+z)]
    f = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(0,3,7,4)]
    return v, f

def cyl(cx, cy, cz, r, h, axis="z", seg=14):
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a) * r, math.sin(a) * r
        if axis == "z":   p0, p1 = (cx+c, cy+s, cz-h/2), (cx+c, cy+s, cz+h/2)
        elif axis == "x": p0, p1 = (cx-h/2, cy+c, cz+s), (cx+h/2, cy+c, cz+s)
        else:             p0, p1 = (cx+c, cy-h/2, cz+s), (cx+c, cy+h/2, cz+s)
        v += [p0, p1]
    for i in range(seg):
        a, b = 2*i, 2*((i+1) % seg)
        f.append((a, b, b+1, a+1))
    f.append(tuple(range(0, 2*seg, 2)))
    f.append(tuple(range(1, 2*seg, 2)))
    return v, f

# ----------------------------------------------------------------- piesele
COL = {"iron":(74,78,86),"alu":(150,158,170),"steel":(184,190,200),
       "exhaust":(112,74,56),"rubber":(34,34,38),"accent":(255,77,46)}
PARTS = []
def add(mesh, mat, order):
    PARTS.append({"v":mesh[0],"f":mesh[1],"c":COL[mat],"o":order})

CX = [-0.75,-0.25,0.25,0.75]
add(cyl(0,0,-0.70,0.085,2.30,"x"), "steel", 0)
for x in CX: add(cyl(x,0,-0.70,0.235,0.10,"x"), "steel", 0)
add(cyl(1.28,0,-0.70,0.40,0.11,"x"), "steel", 0)
for x in CX:
    add(cyl(x,0,0.30,0.215,0.34), "alu", 1)
    add(box(x,0,-0.20,0.075,0.11,0.52), "steel", 1)
add(box(0,0,0.05,2.30,1.40,1.15), "iron", 2)
add(box(0,0,0.83,2.30,1.40,0.42), "alu", 3)
for s in (-1,1):
    add(cyl(0,s*0.30,1.00,0.075,2.10,"x"), "steel", 3)
    for x in CX: add(cyl(x,s*0.30,1.00,0.125,0.09,"x"), "steel", 3)
add(box(0,0,1.14,2.10,1.22,0.20), "accent", 4)
add(box(0,0,-1.02,2.05,1.22,0.42), "iron", 5)
add(box(0,1.12,0.86,1.95,0.46,0.44), "alu", 6)
for x in CX: add(cyl(x,0.86,0.86,0.105,0.62,"y"), "alu", 6)
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
    dist = random.uniform(5.5, 13.0)
    p["off"] = [c/L*dist for c in d]
    p["spin"] = [random.uniform(-2.6,2.6) for _ in range(3)]

# ------------------------------------------------------------------ camera
def rot(v, rx, ry, rz):
    x,y,z = v
    y,z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
    x,z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
    x,y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
    return [x,y,z]

def look(eye, tgt):
    f = [tgt[i]-eye[i] for i in range(3)]
    L = math.sqrt(sum(c*c for c in f)); f = [c/L for c in f]
    up = [0,0,1]
    r = [f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]]
    L = math.sqrt(sum(c*c for c in r)) or 1; r = [c/L for c in r]
    u = [r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], r[0]*f[1]-r[1]*f[0]]
    return r, u, f

def ease_out(t): return 1-(1-t)**3

LIGHT = [0.55,-0.42,0.72]
Ll = math.sqrt(sum(c*c for c in LIGHT)); LIGHT=[c/Ll for c in LIGHT]

os.makedirs(OUT, exist_ok=True)
for fr in range(1, N+1):
    g = (fr-1)/(N-1)
    img = Image.new("RGBA", (W,H), (0,0,0,0))
    dr = ImageDraw.Draw(img, "RGBA")
    eye = [6.9+(4.4-6.9)*g, -8.4+(-5.6+8.4)*g, 4.1+(1.9-4.1)*g]
    R,U,F = look(eye, [0,0,0.12])
    rig = math.radians(-11 + 22*g)
    faces = []
    for p in PARTS:
        t = 0 if fr<=p["t0"] else (1 if fr>=p["t1"] else ease_out((fr-p["t0"])/(p["t1"]-p["t0"])))
        off = [c*(1-t) for c in p["off"]]
        spin = [c*(1-t) for c in p["spin"]]
        cen = [sum(v[i] for v in p["v"])/len(p["v"]) for i in range(3)]
        pts = []
        for v in p["v"]:
            q = rot([v[i]-cen[i] for i in range(3)], *spin)
            q = [q[i]+cen[i]+off[i] for i in range(3)]
            q = rot(q, 0, 0, rig)
            d = [q[i]-eye[i] for i in range(3)]
            cam = [sum(d[i]*R[i] for i in range(3)),
                   sum(d[i]*U[i] for i in range(3)),
                   sum(d[i]*F[i] for i in range(3))]
            if cam[2] < 0.05: cam[2] = 0.05
            fl = 1.55
            pts.append((W/2 + cam[0]/cam[2]*fl*W/2, H/2 - cam[1]/cam[2]*fl*W/2, cam[2]))
        for face in p["f"]:
            poly = [pts[i] for i in face]
            zc = sum(q[2] for q in poly)/len(poly)
            a,b,c = [p["v"][i] for i in face[:3]]
            n = [(b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),
                 (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
                 (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])]
            nl = math.sqrt(sum(v*v for v in n)) or 1
            n = rot([v/nl for v in n], *spin)
            n = rot(n, 0, 0, rig)
            lam = max(0.0, sum(n[i]*LIGHT[i] for i in range(3)))
            rim = max(0.0, -n[1]) ** 3
            sh = 0.20 + 0.85*lam
            col = tuple(min(255, int(p["c"][i]*sh + (255,60,40)[i]*rim*0.55)) for i in range(3))
            faces.append((zc, [(q[0],q[1]) for q in poly], col))
    faces.sort(key=lambda f: -f[0])
    for _, poly, col in faces:
        dr.polygon(poly, fill=col+(255,), outline=(min(255,col[0]+26), min(255,col[1]+26), min(255,col[2]+30), 255))
    img.save(f"{OUT}/motor_{fr:04d}.webp", "WEBP", quality=74, method=4)
    if fr % 15 == 0: print("  cadru", fr)

tot = sum(os.path.getsize(f"{OUT}/{f}") for f in os.listdir(OUT))
print(f"gata: {N} cadre, {tot/1024/1024:.2f} MB total")
