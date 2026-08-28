"""
AQUAFIX — hero "Firul de apa"

O picatura cade intr-o teava, iar camera o urmareste prin traseu, prin perete,
pana iese la robinet. Teava e taiata pe lungime, ca sa se vada ce curge prin ea:
mesajul de vanzare al unui instalator e fix asta — "vedem ce se intampla in
peretele tau fara sa-l spargem".

    blender -b -P blender/scene/instalator.py -- --still-only --studio --still 46
    blender -b -P blender/scene/instalator.py -a -- --studio --res 1024 --samples 48
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hero_kit as K

K.wipe()

# ------------------------------------------------------------------ materiale
CUPRU  = K.mat("Cupru",  (0.62, 0.26, 0.11), 0.95, 0.30)
CROM   = K.mat("Crom",   (0.78, 0.80, 0.84), 1.00, 0.08)
APA    = K.mat("Apa",    (0.06, 0.24, 0.46), 0.0, 0.02,
                emit=(0.02, 0.16, 0.42), emit_power=1.4,
                transmission=1.0, ior=1.33)
PERETE = K.mat("Perete", (0.15, 0.155, 0.17), 0.0, 0.85)
GRESIE = K.mat("Gresie", (0.20, 0.225, 0.26), 0.05, 0.22)
GARNIT = K.mat("Garnitura", (0.02, 0.02, 0.022), 0.0, 0.75)

# ------------------------------------------------------------------- traseul
# Coboara din tavan, trece orizontal, intra in perete, si urca la robinet.
TRASEU = [
    (-6.4, 0.0,  2.90),
    (-6.4, 0.0,  0.55),
    (-3.10, 0.0, 0.55),
    (-3.10, 0.0, -0.95),
    ( 2.35, 0.0, -0.95),
    ( 2.35, 0.0,  0.85),
    ( 3.15, 0.0,  0.85),
]
R = 0.30

K.pipe_run(TRASEU, R, CUPRU, order=0, cutaway=True, open_dir=(0, -1, 0))

# coliere de prindere pe portiunile lungi
for x in (-5.2, -0.6, 1.4):
    z = 0.55 if x < -3.10 else -0.95
    K.torus(f"Colier.{x}", (x, 0, z), R + 0.05, 0.045, CROM, 0,
            rot=(0, math.radians(90), 0))

# ---------------------------------------------------------------- peretele
# Doua straturi: zidaria, si un strat de gresie decalat, ca sa se citeasca
# sectiunea prin perete si nu doar o placa.
K.cube("Zidarie", (-0.3, 1.15, -0.20), (11.5, 0.55, 5.2), PERETE, 0)
K.cube("Gresie",  (-0.3, 0.84, -0.20), (11.5, 0.10, 5.2), GRESIE, 0)
K.cube("PardosealaSectiune", (-0.3, 0.6, -2.05), (11.5, 1.6, 0.28), GRESIE, 0)

# ---------------------------------------------------------------- robinetul
K.cylinder("CorpRobinet", (3.15, 0.0, 1.28), 0.26, 0.86, CROM, 0)
K.cylinder("GatRobinet",  (3.15, 0.0, 1.76), 0.13, 0.30, CROM, 0)
K.torus("CotRobinet", (3.15, -0.30, 1.90), 0.30, 0.115, CROM, 0,
        rot=(0, math.radians(90), 0))
K.cylinder("PipaRobinet", (3.15, -0.60, 1.62), 0.115, 0.60, CROM, 0)
K.cylinder("AeratorRobinet", (3.15, -0.60, 1.30), 0.135, 0.09, CROM, 0)
K.cylinder("Maneta", (3.15, 0.0, 1.80), 0.055, 0.52, CROM, 0,
           rot=(math.radians(90), 0, 0))
K.sphere("CapManeta", (3.15, 0.26, 1.80), 0.085, CROM, 0)
K.torus("GarnituraBaza", (3.15, 0.0, 0.90), 0.27, 0.035, GARNIT, 0)

# ------------------------------------------------------------------ picatura
# Picatura principala e urmarita de camera. Merge pe traseu pana la 86% din
# durata, apoi cade din aerator — finalul e "apa ajunge la tine".
PICATURA = K.sphere("Picatura", TRASEU[0], 0.185, APA, 0, segs=40)
CADERE = [
    (3.15, -0.60, 1.22),
    (3.15, -0.60, 0.30),
    (3.15, -0.60, -1.10),
]
f_end = int(K.TOTAL * 0.86)
K.animate_along(PICATURA, TRASEU, frames=(1, f_end), ease_mode="EASE_IN_OUT")
for fr in range(f_end, K.TOTAL + 1):
    t = (fr - f_end) / max(1, K.TOTAL - f_end)
    PICATURA.location = K.sample_path(CADERE, t * t)   # accelereaza, e cadere libera
    PICATURA.keyframe_insert("location", frame=fr)

# firicel de picaturi in urma, decalate pe traseu
for i in range(1, 7):
    lag = i * 0.055
    d = K.sphere(f"Picatura.{i}", TRASEU[0], 0.185 - i * 0.014, APA, 0, segs=24)
    for fr in range(1, K.TOTAL + 1):
        t = (fr - 1) / (K.TOTAL - 1) - lag
        d.location = K.sample_path(TRASEU, max(0.0, t))
        d.keyframe_insert("location", frame=fr)
    K.ease(d, "EASE_IN_OUT", "LINEAR")

# ------------------------------------------------------------ lumini si lume
# Scena de teava e de ~5 ori mai lata decat un motor, deci lampile stau de 2.6
# ori mai departe si au nevoie de ~7 ori mai multa putere.
K.three_point(rim_color=(0.22, 0.52, 1.00), key=1500, fill=380, rim=1100,
              scale=2.6, center=(-1.4, 0, 0))
# licarire albastra chiar in teava, ca traseul sa se citeasca in intuneric
K.light("Interior", (-1.4, -2.0, -0.4), 2400, (0.30, 0.60, 1.0), 8.0,
        (math.radians(90), 0, 0))
K.world(color=(0.020, 0.026, 0.038), strength=0.85)

# --------------------------------------------------------------- camera
# Merge paralel cu teava, decalata catre privitor, si tine ochii pe picatura.
if K.flag("--debug-cam"):
    K.debug_camera(dist=16.0, height=4.0, target=(-1.4, 0, 0.0))
else:
    # Decalajul se masoara in unitatile scenei: la un traseu de ~10 unitati,
    # 4.6 inseamna nasul in teava. Mai departe si mai sus, cu un obiectiv mai
    # larg, ca sa se vada si traseul, si unde se duce picatura.
    K.camera_along(TRASEU, PICATURA, lens=32, fstop=4.0, offset=(1.6, -10.5, 2.6))

K.setup_render(studio=K.flag("--studio"))
if K.flag("--studio"):
    K.floor(z=-2.30, size=60, rgb=(0.014, 0.016, 0.020), rough=0.42)
K.finish()
