# ============================================================================
#  MOTORLINE — hero "Explozia inversa"
#  Un motor in patru cilindri, desfacut in ~120 de piese suspendate, care se
#  asambleaza la loc pe masura ce vizitatorul deruleaza pagina.
#
#  RULARE (headless, fara sa deschizi Blender):
#      blender -b -P blender/service-auto_engine.py
#      blender -b -P blender/service-auto_engine.py -- --out /cale/catre/frames --frames 90
#
#  Sau deschide Blender gol, Scripting > Open > ruleaza. Scena se construieste
#  din zero de fiecare data, deci poti rula de cate ori vrei fara sa strici nimic.
#
#  IESIRE: secventa PNG cu alpha (fundal transparent), 1600x1000.
#  Fundalul il pune site-ul din CSS, ca sa putem schimba culoarea fara re-render.
#
#  DE CE ASA:
#  - Fara motion blur. Cadrele sunt scrubuite inainte si inapoi cu degetul;
#    un cadru cu blur arata gresit cand stai pe el.
#  - Fara denoise temporal si fara sampling variabil. Orice diferenta de
#    zgomot intre doua cadre vecine se vede ca palpaire la scroll lent.
#  - Camera nu se roteste in jurul obiectului mai mult de ~25 de grade. Peste
#    atat, creierul citeste "video" in loc de "controlez eu miscarea".
# ============================================================================

import bpy
import math
import random
import sys
from mathutils import Vector

# ---------------------------------------------------------------- parametri
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def arg(name, default):
    if name in ARGS:
        return ARGS[ARGS.index(name) + 1]
    return default

OUT_DIR    = arg("--out", "//render/service-auto/")
TOTAL      = int(arg("--frames", 90))     # 90 = ~3 MB in webp, sweet spot
RES_X, RES_Y = 1600, 1000
SEED       = 20260828

# Fereastra in care sosesc piesele (restul e asezare + rotatie lenta).
ARRIVE_FIRST = 4
ARRIVE_LAST  = int(TOTAL * 0.86)

random.seed(SEED)

# ---------------------------------------------------------------- curatenie
def wipe():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.objects):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)

wipe()

# ---------------------------------------------------------------- materiale
def metal(name, rgb, metalness, roughness, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metalness
    bsdf.inputs["Roughness"].default_value = roughness
    if emit:
        # numele intrarii difera intre 3.x si 4.x
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = (*emit, 1.0)
                break
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 2.0
    return m

MAT = {
    "iron":    metal("Fonta bloc",     (0.055, 0.058, 0.065), 0.80, 0.52),
    "alu":     metal("Aluminiu chiul", (0.290, 0.310, 0.340), 0.95, 0.26),
    "steel":   metal("Otel arbore",    (0.480, 0.500, 0.530), 1.00, 0.17),
    "exhaust": metal("Evacuare arsa",  (0.130, 0.085, 0.060), 0.85, 0.42),
    "rubber":  metal("Cauciuc curea",  (0.020, 0.020, 0.022), 0.00, 0.85),
    "accent":  metal("Rosu Motorline", (0.620, 0.110, 0.045), 0.45, 0.30,
                     emit=(0.160, 0.030, 0.012)),
}

# ---------------------------------------------------------------- geometrie
PARTS = []   # (obiect, indice_de_asamblare)

def add(kind, name, loc, rot=(0, 0, 0), size=(1, 1, 1),
        mat="iron", order=0, radius=0.5, depth=1.0, verts=32):
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                            vertices=verts, location=loc)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth,
                                         major_segments=28, minor_segments=14,
                                         location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    ob.rotation_euler = rot
    ob.data.materials.append(MAT[mat])
    # tesitura pe muchii: fara ea, primitivele arata ca un desen de scoala
    if kind in ("cube", "cyl"):
        bev = ob.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.012
        bev.segments = 2
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(38)
    bpy.ops.object.shade_smooth()
    if kind == "cube":
        ob.data.use_auto_smooth = True if hasattr(ob.data, "use_auto_smooth") else False
    PARTS.append((ob, order))
    return ob

R90 = math.radians(90)
CYL_X = [-0.75, -0.25, 0.25, 0.75]     # axele celor patru cilindri

# --- 0. arbore cotit -------------------------------------------------------
add("cyl", "Arbore", (0, 0, -0.70), rot=(0, R90, 0),
    radius=0.085, depth=2.30, mat="steel", order=0)
for i, x in enumerate(CYL_X):
    add("cyl", f"Contragreutate.{i}", (x, 0, -0.70), rot=(0, R90, 0),
        radius=0.235, depth=0.10, mat="steel", order=0)
add("cyl", "Volanta", (1.28, 0, -0.70), rot=(0, R90, 0),
    radius=0.40, depth=0.11, mat="steel", order=0)

# --- 1. pistoane si biele --------------------------------------------------
for i, x in enumerate(CYL_X):
    add("cyl", f"Piston.{i}", (x, 0, 0.30), radius=0.215, depth=0.34,
        mat="alu", order=1)
    add("cube", f"Biela.{i}", (x, 0, -0.20), size=(0.075, 0.11, 0.52),
        mat="steel", order=1)
    for s in (-1, 1):
        add("cyl", f"Segment.{i}.{s}", (x, 0, 0.30 + s * 0.10),
            radius=0.222, depth=0.022, mat="steel", order=1)

# --- 2. blocul motor -------------------------------------------------------
add("cube", "BlocMotor", (0, 0, 0.05), size=(2.30, 1.40, 1.15),
    mat="iron", order=2)
for i, x in enumerate(CYL_X):
    add("cyl", f"Camasa.{i}", (x, 0, 0.22), radius=0.245, depth=0.92,
        mat="steel", order=2)

# --- 3. chiulasa -----------------------------------------------------------
add("cube", "Chiulasa", (0, 0, 0.83), size=(2.30, 1.40, 0.42),
    mat="alu", order=3)
for i, x in enumerate(CYL_X):
    for s in (-1, 1):
        add("cyl", f"Supapa.{i}.{s}", (x, s * 0.22, 0.78), radius=0.055,
            depth=0.44, mat="steel", order=3)
for s in (-1, 1):
    add("cyl", f"AxCame.{s}", (0, s * 0.30, 1.00), rot=(0, R90, 0),
        radius=0.075, depth=2.10, mat="steel", order=3)
    for i, x in enumerate(CYL_X):
        add("cyl", f"Cama.{i}.{s}", (x, s * 0.30, 1.00), rot=(0, R90, 0),
            radius=0.125, depth=0.09, mat="steel", order=3)

# --- 4. capac culbutori (piesa cu logo) ------------------------------------
add("cube", "CapacCulbutori", (0, 0, 1.14), size=(2.10, 1.22, 0.20),
    mat="accent", order=4)
add("cyl", "BusonUlei", (0.80, 0.36, 1.26), radius=0.13, depth=0.10,
    mat="alu", order=4)

# --- 5. baie de ulei -------------------------------------------------------
add("cube", "BaieUlei", (0, 0, -1.02), size=(2.05, 1.22, 0.42),
    mat="iron", order=5)
add("cyl", "BusonGolire", (0.70, 0, -1.24), radius=0.075, depth=0.09,
    mat="steel", order=5)

# --- 6. galerie de admisie -------------------------------------------------
add("cube", "Plenum", (0, 1.12, 0.86), size=(1.95, 0.46, 0.44),
    mat="alu", order=6)
for i, x in enumerate(CYL_X):
    add("cyl", f"Runner.{i}", (x, 0.86, 0.86), rot=(R90, 0, 0),
        radius=0.105, depth=0.62, mat="alu", order=6)
add("cyl", "ClapetaAdmisie", (-1.10, 1.12, 0.86), rot=(0, R90, 0),
    radius=0.19, depth=0.22, mat="alu", order=6)

# --- 7. galerie de evacuare ------------------------------------------------
for i, x in enumerate(CYL_X):
    add("torus", f"Primar.{i}", (x, -0.92, 0.72), rot=(0, 0, 0),
        radius=0.26, depth=0.062, mat="exhaust", order=7)
add("cyl", "Colector", (0, -1.22, 0.34), rot=(0, R90, 0),
    radius=0.13, depth=1.90, mat="exhaust", order=7)

# --- 8. turbo --------------------------------------------------------------
add("cyl", "CarcasaTurbina", (-1.18, -1.36, 0.10), rot=(R90, 0, 0),
    radius=0.36, depth=0.30, mat="exhaust", order=8)
add("cyl", "CarcasaCompresor", (-1.18, -1.36, -0.42), rot=(R90, 0, 0),
    radius=0.30, depth=0.26, mat="alu", order=8)
add("cyl", "AxTurbo", (-1.18, -1.36, -0.16), radius=0.055, depth=0.60,
    mat="steel", order=8)

# --- 9. distributie fata ---------------------------------------------------
add("cyl", "FulieVibrochen", (-1.32, 0, -0.70), rot=(0, R90, 0),
    radius=0.30, depth=0.13, mat="steel", order=9)
add("cyl", "FulieAlternator", (-1.32, 0.52, 0.30), rot=(0, R90, 0),
    radius=0.18, depth=0.11, mat="steel", order=9)
add("cyl", "FuliePompaApa", (-1.32, -0.48, 0.34), rot=(0, R90, 0),
    radius=0.16, depth=0.11, mat="steel", order=9)
add("torus", "CureaAccesorii", (-1.36, 0.02, -0.16), rot=(0, R90, 0),
    radius=0.56, depth=0.035, mat="rubber", order=9)

# --- 10. suruburi (ultimele, in rafala) ------------------------------------
bolt_spots = []
for x in (-1.02, -0.50, 0.0, 0.50, 1.02):
    for y in (-0.62, 0.62):
        bolt_spots.append((x, y, 1.04))          # chiulasa
        bolt_spots.append((x, y, -0.82))         # baie ulei
for i, (x, y, z) in enumerate(bolt_spots):
    add("cyl", f"Surub.{i}", (x, y, z), radius=0.048, depth=0.11,
        mat="steel", order=10)

print(f"[motorline] {len(PARTS)} piese construite")

# ------------------------------------------------------- grup + rotatie lenta
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
RIG = bpy.context.active_object
RIG.name = "RIG_Motor"
for ob, _ in PARTS:
    ob.parent = RIG
    ob.matrix_parent_inverse = RIG.matrix_world.inverted()

# Rotatia intregului ansamblu: 22 de grade pe toata durata. Suficient cat sa
# se schimbe unghiul luminii pe metal, prea putin cat sa ameteasca.
RIG.rotation_euler = (0, 0, math.radians(-11))
RIG.keyframe_insert("rotation_euler", frame=1)
RIG.rotation_euler = (0, 0, math.radians(11))
RIG.keyframe_insert("rotation_euler", frame=TOTAL)

# ------------------------------------------------------------- asamblarea
MAX_ORDER = max(o for _, o in PARTS)

def ease_curve(ob, frame_field):
    """Cubic ease-out pe toate curbele obiectului: piesa intra repede si se
    aseaza moale, in loc sa alunece liniar ca un slide de PowerPoint."""
    if not ob.animation_data or not ob.animation_data.action:
        return
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CUBIC"
            kp.easing = "EASE_OUT"

span = ARRIVE_LAST - ARRIVE_FIRST

for ob, order in PARTS:
    # fereastra de sosire a grupului, plus un decalaj mic per piesa
    t0 = ARRIVE_FIRST + span * (order / (MAX_ORDER + 1))
    t0 += random.uniform(0, span * 0.05)
    t1 = t0 + span * 0.30
    t0, t1 = int(round(t0)), int(round(min(t1, TOTAL)))

    target_loc = ob.location.copy()
    target_rot = ob.rotation_euler.copy()

    # directie de imprastiere: dominant lateral, ca sa nu se suprapuna toate
    # peste centrul cadrului si sa se citeasca fiecare piesa separat
    d = Vector((random.uniform(-1, 1) * 1.8,
                random.uniform(-1, 1) * 1.2,
                random.uniform(-1, 1) * 1.0)).normalized()
    dist = random.uniform(5.5, 13.0)

    ob.location = target_loc + d * dist
    ob.rotation_euler = (target_rot[0] + random.uniform(-2.6, 2.6),
                         target_rot[1] + random.uniform(-2.6, 2.6),
                         target_rot[2] + random.uniform(-2.6, 2.6))
    ob.keyframe_insert("location", frame=1)
    ob.keyframe_insert("rotation_euler", frame=1)
    ob.keyframe_insert("location", frame=t0)
    ob.keyframe_insert("rotation_euler", frame=t0)

    ob.location = target_loc
    ob.rotation_euler = target_rot
    ob.keyframe_insert("location", frame=t1)
    ob.keyframe_insert("rotation_euler", frame=t1)

    ease_curve(ob, None)

# --------------------------------------------------------------- iluminare
def light(name, kind, loc, energy, color, size=2.0, rot=(0, 0, 0)):
    data = bpy.data.lights.new(name, type=kind)
    data.energy = energy
    data.color = color
    if kind == "AREA":
        data.size = size
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob

# cheie: sus-dreapta-fata, mare si moale, ca sa curga pe aluminiu
light("Key", "AREA", (4.6, -4.2, 5.0), 1400, (1.0, 0.96, 0.92), size=6.0,
      rot=(math.radians(42), 0, math.radians(46)))
# umplere rece din stanga, tine umbrele citibile fara sa le stearga
light("Fill", "AREA", (-5.4, -2.2, 1.6), 320, (0.62, 0.72, 1.0), size=7.0,
      rot=(math.radians(78), 0, math.radians(-60)))
# contur rosu Motorline din spate — semnatura de brand pe metal
light("RimRosu", "AREA", (-2.4, 4.6, 1.4), 900, (1.0, 0.30, 0.18), size=4.0,
      rot=(math.radians(96), 0, math.radians(196)))
# licarire calda de jos, ca sa nu moara baia de ulei in negru
light("Kick", "AREA", (2.0, 2.6, -2.6), 260, (1.0, 0.74, 0.50), size=3.0,
      rot=(math.radians(-58), 0, math.radians(150)))

# lume neagra: fundalul vine din CSS, aici tinem doar reflexiile
world = bpy.data.worlds.new("Studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.025, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
bpy.context.scene.world = world

# ----------------------------------------------------------------- camera
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0.12))
LOOK = bpy.context.active_object
LOOK.name = "CAM_Target"

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 52                      # ~50mm: fara distorsiune de wide
cam_data.dof.use_dof = True
cam_data.dof.focus_object = LOOK
cam_data.dof.aperture_fstop = 3.2       # fundalul se topeste, piesa e clara
CAM = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(CAM)
bpy.context.scene.camera = CAM

track = CAM.constraints.new("TRACK_TO")
track.target = LOOK
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"

# Un singur travelling: de departe si de sus, la aproape si la nivelul motorului.
CAM.location = (6.9, -8.4, 4.1)
CAM.keyframe_insert("location", frame=1)
CAM.location = (4.4, -5.6, 1.9)
CAM.keyframe_insert("location", frame=TOTAL)
for fc in CAM.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "SINE"       # miscare constanta, fara acceleratie
        kp.easing = "EASE_IN_OUT"

# ------------------------------------------------------------- randare
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL

engines = [e.identifier for e in
           bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
scene.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines
                       else "BLENDER_EEVEE")

ee = scene.eevee
ee.taa_render_samples = 64              # fix, niciodata adaptiv: adaptivul palpaie
if hasattr(ee, "use_gtao"):
    ee.use_gtao = True
if hasattr(ee, "use_bloom"):
    ee.use_bloom = True
    ee.bloom_intensity = 0.035
if hasattr(ee, "use_ssr"):
    ee.use_ssr = True
    ee.use_ssr_refraction = True
if hasattr(ee, "use_raytracing"):       # EEVEE Next
    ee.use_raytracing = True

scene.render.use_motion_blur = False    # OBLIGATORIU: cadrele se scrubuiesc
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.film_transparent = True    # alpha: fundalul il pune CSS-ul
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.compression = 15
scene.render.filepath = OUT_DIR

scene.view_settings.view_transform = "AgX" if "AgX" in [
    t.name for t in scene.view_settings.bl_rna.properties["view_transform"].enum_items
] else "Filmic"
scene.view_settings.look = "AgX - Medium High Contrast" if scene.view_settings.view_transform == "AgX" else "Medium High Contrast"

print(f"[motorline] gata. {TOTAL} cadre -> {OUT_DIR}")
print("[motorline] randezi cu:  blender -b fisier.blend -a")
print("[motorline] sau direct:  blender -b -P blender/service-auto_engine.py -a")
