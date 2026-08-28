"""
MOTORLINE — hero "Scanare X-ray"

Caroseria devine transparenta si se aprind, pe rand, circuitele masinii:
combustibilul de la buson pana la motor, apoi racirea si uleiul, apoi lichidul
de frana catre cele patru etriere.

De ce asa: un service auto nu traieste din motoare, ci din frane, suspensii,
distributie, clima si electronica. Un motor care se asambleaza spune "ne
pricepem la motoare" si pierde clientul care are o problema de frana. Un traseu
care se aprinde pe fiecare sistem in parte spune "orice ai, ne ocupam".

    blender -b -P blender/scene/service_auto.py -- --still-only --studio --fast --still 52
    blender -b -P blender/scene/service_auto.py -a -- --studio --res 1024 --samples 64
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hero_kit as K

K.wipe()
T = K.TOTAL

# ------------------------------------------------------------------ materiale
SHELL   = K.xray_mat("Caroserie", (0.34, 0.58, 0.92), alpha=0.045, rim=0.55)
WIRE    = K.mat("Muchii", (0.35, 0.65, 1.0), 0.0, 0.4,
                emit=(0.20, 0.48, 0.95), emit_power=5.5)
FONTA   = K.mat("Fonta",   (0.115, 0.120, 0.135), 0.85, 0.45)
OTEL    = K.mat("Otel",    (0.34, 0.36, 0.40), 1.00, 0.26)
CAUCIUC = K.mat("Cauciuc", (0.012, 0.012, 0.014), 0.0, 0.85)
DISC    = K.mat("Disc",    (0.30, 0.31, 0.34), 1.00, 0.22)

# Fiecare circuit are culoarea lui, ca sa se citeasca instant ca sisteme
# diferite, nu ca acelasi lucru de trei ori.
BENZINA = K.mat("Benzina", (0.95, 0.55, 0.10), 0.0, 0.15,
                emit=(1.00, 0.42, 0.04), emit_power=9.0)
RACIRE  = K.mat("Racire",  (0.10, 0.70, 0.95), 0.0, 0.15,
                emit=(0.05, 0.62, 1.00), emit_power=9.0)
FRANA   = K.mat("Frana",   (1.00, 0.22, 0.14), 0.0, 0.15,
                emit=(1.00, 0.16, 0.08), emit_power=10.0)

# ------------------------------------------------------------------ caroseria
# Trei volume simple: capota, habitaclul, portbagajul. Nu ne trebuie o masina
# frumoasa, ne trebuie o silueta pe care ochiul o citeste ca masina in 0.2 sec.
# Proportii de berlina, nu de buggy: lungime 8.4, latime 2.9, inaltime ~2.
# Prima varianta avea caroseria inalta si ingusta, cu rotile scoase in afara —
# creierul o citea ca vehicul de jucarie si pierdea tot mesajul.
# O berlina are un singur volum lung si jos, cu habitaclul ridicat intre capota
# si portbagaj. Varianta anterioara punea cabina PESTE o cutie inalta, si iesea
# camioneta. Linia de centura (unde incep geamurile) sta la z=0.95, acoperisul
# la 1.78, podeaua la -0.30.
CAROSERIE = [
    ("Corp",       ( 0.00, 0, 0.32), (8.20, 2.74), (7.90, 2.92), 1.25),
    ("Habitaclu",  ( 0.35, 0, 1.36), (3.60, 2.52), (2.45, 1.92), 0.84),
]
for nume, loc, jos, sus, h in CAROSERIE:
    K.prism(nume, loc, jos, sus, h, SHELL, 0)
    K.wire_over(nume + ".Wire",
                lambda n, l=loc, j=jos, s_=sus, hh=h: K.prism(n, l, j, s_, hh, SHELL, 0),
                WIRE, thickness=0.016)

# ------------------------------------------------------------------- roti
# Rotile stau sub caroserie, nu langa ea: axul la z=-0.20, raza 0.72,
# deci solul cade la -0.92.
ROTI = [(-2.55, -1.38), (-2.55, 1.38), (2.55, -1.38), (2.55, 1.38)]
Z_AX = -0.20
for i, (x, y) in enumerate(ROTI):
    K.torus(f"Anvelopa.{i}", (x, y, Z_AX), 0.56, 0.19, CAUCIUC, 0,
            rot=(0, math.radians(90), 0))
    K.cylinder(f"Janta.{i}", (x, y, Z_AX), 0.40, 0.22, OTEL, 0,
               rot=(0, math.radians(90), 0))
    # discul si etrierul: piesele pe care le vinde cel mai des un service
    K.cylinder(f"Disc.{i}", (x, y * 0.90, Z_AX), 0.36, 0.05, DISC, 0,
               rot=(0, math.radians(90), 0))
    K.cube(f"Etrier.{i}", (x - 0.26, y * 0.90, Z_AX + 0.20),
           (0.20, 0.30, 0.26), OTEL, 0)

# ------------------------------------------------------- ce e sub caroserie
K.cube("Motor",     (-2.85, 0, 0.48), (1.35, 1.00, 0.80), FONTA, 0)
K.cube("Chiulasa",  (-2.85, 0, 0.96), (1.30, 0.95, 0.20), OTEL, 0)
K.cylinder("Cutie", (-1.65, 0, 0.22), 0.30, 1.00, OTEL, 0, rot=(0, math.radians(90), 0))
K.cylinder("Cardan",( 0.55, 0, 0.02), 0.070, 3.20, OTEL, 0, rot=(0, math.radians(90), 0))
K.sphere("Diferential", (2.45, 0, -0.02), 0.28, OTEL, 0)
K.cube("Radiator",  (-3.92, 0, 0.52), (0.14, 1.55, 0.78), OTEL, 0)
K.prism("Rezervor", (2.55, 0, 0.05), (1.25, 1.45), (1.45, 1.60), 0.44, OTEL, 0)
K.cube("Baterie",   (-3.50, 0.80, 0.82), (0.50, 0.32, 0.30), OTEL, 0)
K.cube("Calculator",(-3.50, -0.80, 0.82), (0.40, 0.26, 0.13), OTEL, 0)
K.cylinder("Compresor", (-3.25, -0.62, 0.28), 0.18, 0.32, OTEL, 0,
           rot=(0, math.radians(90), 0))

# esapamentul: de la motor, pe sub podea, pana in spate
K.pipe_run([(-2.20, -0.30, 0.10), (-1.30, -0.32, -0.10), (1.00, -0.32, -0.12),
            (2.20, -0.32, -0.08), (3.80, -0.46, 0.00)],
           0.080, OTEL, 0)
K.cube("Tobă", (3.05, -0.46, -0.04), (0.90, 0.40, 0.26), OTEL, 0)

# ============================================================== circuitele
# Ferestrele in care se aprinde fiecare, potrivite cu textele din pagina.
W_BENZINA = (int(T * 0.06), int(T * 0.40))
W_RACIRE  = (int(T * 0.38), int(T * 0.68))
W_FRANA   = (int(T * 0.64), int(T * 0.94))

def circuit(nume, traseu, material, fereastra, r=0.055, picaturi=5, viteza=1.0):
    """Un traseu luminos plus picaturi care il parcurg. Traseul e desenat tot
    timpul cat e activa fereastra; picaturile ii dau directia."""
    tuburi = K.pipe_run(traseu, r, material, 0, joint_scale=1.15)
    f0, f1 = fereastra
    for ob in tuburi:
        if ob:
            K.show_between(ob, f0, f1)
    for i in range(picaturi):
        d = K.sphere(f"{nume}.Picatura.{i}", traseu[0], r * 2.3, material, 0, segs=20)
        lag = i * 0.13
        for fr in range(f0, f1 + 1):
            t = ((fr - f0) / max(1, f1 - f0)) * viteza - lag
            d.location = K.sample_path(traseu, max(0.0, min(1.0, t)))
            d.keyframe_insert("location", frame=fr)
        K.ease(d, "EASE_IN_OUT", "LINEAR")
        K.show_between(d, f0, f1)

# --- benzina: de la busonul din spate-dreapta, pe sub prag, pana la motor ----
circuit("Benzina", [
    ( 3.55,  1.18,  0.72),
    ( 3.20,  1.10,  0.28),
    ( 2.70,  0.72,  0.02),
    ( 0.40,  0.66, -0.02),
    (-1.70,  0.60,  0.08),
    (-2.50,  0.40,  0.40),
    (-2.80,  0.12,  0.72),
], BENZINA, W_BENZINA)

# --- racire: motor -> radiator -> inapoi, bucla inchisa ---------------------
circuit("Racire", [
    (-2.82, -0.34,  0.80),
    (-3.35, -0.60,  0.70),
    (-3.86, -0.55,  0.62),
    (-3.86,  0.55,  0.36),
    (-3.35,  0.60,  0.28),
    (-2.82,  0.34,  0.36),
], RACIRE, W_RACIRE, picaturi=6)

# --- frana: de la pompa centrala catre fiecare roata ------------------------
POMPA = (-2.20, -0.66, 0.92)
for i, (x, y) in enumerate(ROTI):
    circuit(f"Frana.{i}", [
        POMPA,
        (-2.20, y * 0.42, 0.62),
        (x * 0.60 + (-0.8), y * 0.78, 0.24),
        (x - 0.26, y * 0.90, Z_AX + 0.18),
    ], FRANA, W_FRANA, r=0.042, picaturi=3)

# ------------------------------------------------------------ bara de scanare
# O dunga de lumina care trece prin masina: fara ea, transparenta se citeste ca
# "obiect din sticla", nu ca "scanare".
bpy.ops.mesh.primitive_plane_add(size=1, location=(-4.6, 0, 0.4))
BARA = bpy.context.active_object
BARA.name = "BaraScanare"
# Planul se naste in XY. Ca sa devina o felie perpendiculara pe directia de
# deplasare, il rotim 90 de grade in jurul lui Y si il scalam in planul lui,
# nu pe grosime — altfel iese o dunga, cum a iesit prima data.
BARA.scale = (2.6, 3.6, 1.0)
BARA.rotation_euler = (0, math.radians(90), 0)
BARA.data.materials.append(
    K.mat("Scan", (0.4, 0.8, 1.0), 0.0, 0.2, emit=(0.35, 0.75, 1.0),
          emit_power=2.2, alpha=0.16))
for fr, x in ((1, -5.1), (T, 4.9)):
    BARA.location.x = x
    BARA.keyframe_insert("location", frame=fr)
K.ease(BARA, "EASE_IN_OUT", "SINE")

# ------------------------------------------------------------ lumini si lume
K.three_point(rim_color=(1.0, 0.32, 0.18), key=900, fill=520, rim=700,
              scale=2.2, center=(0, 0, 0.2))
# Lumina din interior: sub o caroserie transparenta, piesele nu primesc nimic
# de la lampile de afara si raman siluete negre.
K.light("Interior", (-1.0, -0.2, 0.55), 260, (0.75, 0.85, 1.0), 3.0,
        (math.radians(90), 0, 0))
K.light("InteriorSpate", (2.2, -0.2, 0.35), 160, (1.0, 0.80, 0.62), 2.6,
        (math.radians(90), 0, 0))
K.world(color=(0.008, 0.010, 0.016), strength=0.55)

# --------------------------------------------------------------- camera
if K.flag("--debug-cam"):
    K.debug_camera(dist=15.0, height=4.0, target=(0, 0, 0.2))
else:
    # Pleaca de langa motor si se retrage pana se vede masina intreaga:
    # deschiderea spune "ne uitam in detaliu", finalul spune "la tot".
    K.camera_travel(start=(-4.80, -4.90, 1.60), end=(3.10, -12.80, 4.10),
                    target_start=(-2.85, 0, 0.60), target_end=(0.10, 0, 0.35),
                    lens=(46, 33), fstop=5.0)

K.setup_render(studio=K.flag("--studio"))
if K.flag("--studio"):
    K.floor(z=-0.93, size=70, rgb=(0.010, 0.012, 0.016), rough=0.30)
K.finish()
