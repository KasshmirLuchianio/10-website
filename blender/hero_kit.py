"""
hero_kit — partea comuna a tuturor scenelor de hero.

Fiecare nisa are propriul fisier in blender/scene/, care descrie DOAR geometria
si miscarea. Camera, luminile, studioul, straturile de control si setarile de
randare vin de aici, ca sa fie identice pe toate cele zece site-uri.

Se importa din scena:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import hero_kit as K
"""
import bpy, math, os, random, sys
from mathutils import Vector

# ------------------------------------------------------------------ argumente
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default

def flag(name):
    return name in ARGS

TOTAL   = int(arg("--frames", 90))
RES_X   = int(arg("--res", 1600))
# Rotunjit la par: h264 refuza sa encodeze o inaltime impara, iar 760x475
# opreste tot lantul abia la ffmpeg, dupa 40 de minute de randare.
RES_Y   = int(RES_X * 0.625) // 2 * 2
SAMPLES = int(arg("--samples", 64))
STILL   = int(arg("--still", 62))
OUT_DIR = arg("--out", "//render/")
ENGINE  = (arg("--engine", "cycles")).lower()
HDRI    = arg("--hdri", "")

PARTS = []          # (obiect, indice_de_asamblare) — folosit doar de scenele cu asamblare

# ------------------------------------------------------------------ curatenie
def wipe():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.curves, bpy.data.objects):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)

# ------------------------------------------------------------------ materiale
def _set(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return True
    return False

def mat(name, rgb, metallic=0.0, roughness=0.5, emit=None, emit_power=2.0,
        transmission=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    _set(b, ["Base Color"], (*rgb, 1.0))
    _set(b, ["Metallic"], metallic)
    _set(b, ["Roughness"], roughness)
    _set(b, ["IOR"], ior)
    if transmission:
        _set(b, ["Transmission Weight", "Transmission"], transmission)
    if alpha < 1.0:
        _set(b, ["Alpha"], alpha)
        m.blend_method = "BLEND"
    if emit:
        _set(b, ["Emission Color", "Emission"], (*emit, 1.0))
        _set(b, ["Emission Strength"], emit_power)
    return m

# ------------------------------------------------------------------ primitive
def _finish(ob, material, order, bevel=0.014):
    ob.data.materials.append(material)
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL")
        bv.width = bevel; bv.segments = 3
        bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(38)
    bpy.ops.object.shade_smooth()
    PARTS.append((ob, order))
    return ob

def cube(name, loc, size, material, order=0, rot=(0, 0, 0), bevel=0.014):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name; ob.scale = size; ob.rotation_euler = rot
    return _finish(ob, material, order, bevel)

def cylinder(name, loc, r, h, material, order=0, rot=(0, 0, 0), verts=32, bevel=0.010):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    ob = bpy.context.active_object
    ob.name = name; ob.rotation_euler = rot
    return _finish(ob, material, order, bevel)

def sphere(name, loc, r, material, order=0, segs=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segs, ring_count=segs//2,
                                         location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, material, order, bevel=0)

def torus(name, loc, major, minor, material, order=0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=36, minor_segments=18,
                                     location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, material, order, bevel=0)

def prism(name, loc, bottom, top, height, material, order=0):
    """Cutie cu fata de jos diferita de cea de sus."""
    bx, by = bottom; tx, ty = top; h = height / 2
    v = [(-bx/2,-by/2,-h),(bx/2,-by/2,-h),(bx/2,by/2,-h),(-bx/2,by/2,-h),
         (-tx/2,-ty/2, h),(tx/2,-ty/2, h),(tx/2,ty/2, h),(-tx/2,ty/2, h)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(0,4,7,3)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    ob = bpy.data.objects.new(name, me); ob.location = loc
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    return _finish(ob, material, order)

# ------------------------------------------------- teava taiata pe lungime
def half_tube(name, p0, p1, r, material, order=0, open_dir=(0, -1, 0),
              open_angle=125, thickness=0.035, segs=40):
    """Tronson de teava din care lipseste o felie, ca sa se vada ce curge prin ea.
    Deschiderea e orientata catre `open_dir` — de obicei catre camera."""
    a = Vector(p0); b = Vector(p1)
    axis = (b - a); L = axis.length
    if L < 1e-6:
        return None
    axis.normalize()
    tmp = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    u = axis.cross(tmp).normalized()
    w = axis.cross(u).normalized()
    od = Vector(open_dir).normalized()
    verts, faces = [], []
    half = math.radians(open_angle) / 2
    keep = []
    for i in range(segs + 1):
        ang = -math.pi + 2 * math.pi * i / segs
        d = u * math.cos(ang) + w * math.sin(ang)
        keep.append(d.angle(od) > half)
        verts.append(a + d * r)
        verts.append(b + d * r)
    for i in range(segs):
        if keep[i] and keep[i + 1]:
            faces.append((2*i, 2*i+1, 2*i+3, 2*i+2))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = thickness; sol.offset = 1
    return _finish(ob, material, order, bevel=0.006)

# ------------------------------------------------------------------- trasee
def sample_path(points, t):
    """Pozitia la fractiunea t (0..1) de-a lungul unei polilinii, dupa lungime."""
    pts = [Vector(p) for p in points]
    segs = [(pts[i], pts[i+1], (pts[i+1]-pts[i]).length) for i in range(len(pts)-1)]
    total = sum(s[2] for s in segs)
    d = max(0.0, min(1.0, t)) * total
    for a, b, L in segs:
        if d <= L or L == 0:
            return a + (b - a) * (d / L if L else 0)
        d -= L
    return pts[-1]

def pipe_run(points, r, material, order=0, cutaway=False, joint_scale=1.22,
             open_dir=(0, -1, 0)):
    """Traseu de teava: tronsoane drepte plus fitinguri sferice la coturi."""
    out = []
    for i in range(len(points) - 1):
        if cutaway:
            out.append(half_tube(f"Teava.{i}", points[i], points[i+1], r,
                                 material, order, open_dir=open_dir))
        else:
            a, b = Vector(points[i]), Vector(points[i+1])
            mid = (a + b) / 2
            v = b - a
            rot = v.to_track_quat("Z", "Y").to_euler()
            out.append(cylinder(f"Teava.{i}", tuple(mid), r, v.length, material,
                                order, rot=tuple(rot)))
    for i, p in enumerate(points[1:-1], start=1):
        out.append(sphere(f"Fiting.{i}", p, r * joint_scale, material, order))
    return out

# ------------------------------------------------------------------ asamblare
def scatter_and_assemble(seed=20260828, first=4, last_frac=0.86,
                         window=0.30, dist=(5.5, 13.0)):
    """Imprastie piesele si le aduce la loc, decalat pe grupe."""
    random.seed(seed)
    if not PARTS:
        return
    maxo = max(o for _, o in PARTS)
    last = int(TOTAL * last_frac); span = last - first
    for ob, order in PARTS:
        t0 = first + span * (order / (maxo + 1)) + random.uniform(0, span * 0.05)
        t1 = min(t0 + span * window, TOTAL)
        loc, rot = ob.location.copy(), ob.rotation_euler.copy()
        d = Vector((random.uniform(-1,1)*1.8, random.uniform(-1,1)*1.2,
                    random.uniform(-1,1)*1.0)).normalized()
        ob.location = loc + d * random.uniform(*dist)
        ob.rotation_euler = tuple(rot[i] + random.uniform(-2.6, 2.6) for i in range(3))
        ob.keyframe_insert("location", frame=1)
        ob.keyframe_insert("rotation_euler", frame=1)
        ob.keyframe_insert("location", frame=int(t0))
        ob.keyframe_insert("rotation_euler", frame=int(t0))
        ob.location, ob.rotation_euler = loc, rot
        ob.keyframe_insert("location", frame=int(t1))
        ob.keyframe_insert("rotation_euler", frame=int(t1))
        ease(ob)

def ease(ob, mode="EASE_OUT", interp="CUBIC"):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp
                kp.easing = mode

def animate_along(ob, points, frames=None, ease_mode="EASE_IN_OUT"):
    """Muta un obiect de-a lungul unei polilinii, cadru cu cadru."""
    f0, f1 = frames or (1, TOTAL)
    for fr in range(f0, f1 + 1):
        t = (fr - f0) / max(1, (f1 - f0))
        ob.location = sample_path(points, t)
        ob.keyframe_insert("location", frame=fr)
    ease(ob, ease_mode, "LINEAR")

# ------------------------------------------------------------------- lumini
def light(name, loc, energy, color, size=4.0, rot=(0, 0, 0), kind="AREA"):
    d = bpy.data.lights.new(name, type=kind)
    d.energy = energy; d.color = color
    if kind == "AREA":
        d.size = size
    ob = bpy.data.objects.new(name, d)
    ob.location = loc; ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob

def three_point(rim_color=(1.0, 0.30, 0.18), key=1400, fill=320, rim=900,
                scale=1.0, center=(0, 0, 0)):
    """Trei lumini de suprafata in jurul scenei.

    `scale` e cat de mare e scena fata de un obiect de ~2 unitati. Lumina scade
    cu patratul distantei, deci daca departezi lampile de doua ori, ai nevoie de
    patru ori mai multa putere. Fara asta, o scena mare randeaza complet neagra —
    exact ce s-a intamplat prima data la traseul de teava."""
    c = Vector(center)
    p = scale * scale
    light("Key",  tuple(c + Vector((4.6, -4.2, 5.0)) * scale), key * p,
          (1.0, 0.96, 0.92), 6.0 * scale, (math.radians(42), 0, math.radians(46)))
    light("Fill", tuple(c + Vector((-5.4, -2.2, 1.6)) * scale), fill * p,
          (0.62, 0.72, 1.0), 7.0 * scale, (math.radians(78), 0, math.radians(-60)))
    light("Rim",  tuple(c + Vector((-2.4, 4.6, 1.4)) * scale), rim * p,
          rim_color, 4.0 * scale, (math.radians(96), 0, math.radians(196)))

def world(color=(0.02, 0.02, 0.025), strength=0.35):
    w = bpy.data.worlds.new("World"); w.use_nodes = True
    bpy.context.scene.world = w
    n, l = w.node_tree.nodes, w.node_tree.links
    if HDRI and os.path.exists(bpy.path.abspath(HDRI)):
        env = n.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(bpy.path.abspath(HDRI))
        l.new(env.outputs["Color"], n["Background"].inputs[0])
        n["Background"].inputs[1].default_value = 0.9
    else:
        n["Background"].inputs[0].default_value = (*color, 1)
        n["Background"].inputs[1].default_value = strength
    return w

def floor(z=-1.34, size=40, rgb=(0.020, 0.021, 0.024), rough=0.36):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    ob = bpy.context.active_object; ob.name = "Podea"
    ob.data.materials.append(mat("Podea", rgb, 0.10, rough))
    return ob

# ------------------------------------------------------------------- camera
def camera(start, end, target=(0, 0, 0), lens=52, fstop=3.2, track_object=None):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=target)
    look = bpy.context.active_object; look.name = "CAM_Target"
    cd = bpy.data.cameras.new("Camera")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.focus_object = track_object or look
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Camera", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    t = cam.constraints.new("TRACK_TO")
    t.target = track_object or look
    t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    cam.location = start; cam.keyframe_insert("location", frame=1)
    cam.location = end;   cam.keyframe_insert("location", frame=TOTAL)
    ease(cam, "EASE_IN_OUT", "SINE")
    return cam, look


# ------------------------------------------------------------- look de X-ray
def xray_mat(name, rgb=(0.32, 0.62, 0.95), alpha=0.055, rim=0.9):
    """Invelis aproape invizibil, care se aprinde pe muchii. Nu e sticla: sticla
    refracta si ascunde ce e inauntru, exact invers decat vrem la un X-ray."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    _set(b, ["Base Color"], (*rgb, 1.0))
    _set(b, ["Roughness"], 0.25)
    _set(b, ["Metallic"], 0.0)
    _set(b, ["Alpha"], alpha)
    _set(b, ["Emission Color", "Emission"], (*rgb, 1.0))
    _set(b, ["Emission Strength"], rim)
    m.blend_method = "BLEND"
    m.show_transparent_back = False
    return m

def wire_over(name, build_fn, material, thickness=0.012):
    """Deseneaza acelasi volum inca o data, doar ca muchii luminoase.
    Asta e ce transforma o forma transparenta in 'scanare', nu in geam murdar."""
    ob = build_fn(name)
    ob.data.materials.clear()
    ob.data.materials.append(material)
    w = ob.modifiers.new("Wireframe", "WIREFRAME")
    w.thickness = thickness
    w.use_replace = True
    w.use_even_offset = False
    for m in list(ob.modifiers):
        if m.type == "BEVEL":
            ob.modifiers.remove(m)
    return ob

def show_between(ob, f_in, f_out, fade=3):
    """Obiectul exista doar intre doua cadre. Folosit ca sa se aprinda pe rand
    fiecare circuit, in loc sa fie toate aprinse tot timpul."""
    for f, vis in ((1, True), (max(1, f_in - fade), True),
                   (f_in, False), (f_out, False),
                   (min(TOTAL, f_out + fade), True)):
        ob.hide_render = vis
        ob.hide_viewport = vis
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"

def camera_travel(start, end, target_start, target_end, lens=(50, 34),
                  fstop=3.2, ease_mode="EASE_IN_OUT"):
    """Camera care se retrage: pleaca de langa un detaliu si ajunge la ansamblu.

    Se misca si tinta, nu doar camera — altfel, cand te departezi, subiectul de
    la inceput ramane lipit in centru si restul intra strambat in cadru. Si
    focala se largeste pe drum: tine detaliul mare la inceput fara sa taie
    ansamblul la final."""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=target_start)
    look = bpy.context.active_object; look.name = "CAM_Target"
    look.keyframe_insert("location", frame=1)
    look.location = target_end
    look.keyframe_insert("location", frame=TOTAL)
    ease(look, ease_mode, "SINE")

    cd = bpy.data.cameras.new("Camera")
    cd.lens = lens[0]
    cd.dof.use_dof = True
    cd.dof.focus_object = look
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Camera", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    t = cam.constraints.new("TRACK_TO")
    t.target = look; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    cam.location = start; cam.keyframe_insert("location", frame=1)
    cam.location = end;   cam.keyframe_insert("location", frame=TOTAL)
    ease(cam, ease_mode, "SINE")
    cd.lens = lens[0]; cd.keyframe_insert("lens", frame=1)
    cd.lens = lens[1]; cd.keyframe_insert("lens", frame=TOTAL)
    if cd.animation_data and cd.animation_data.action:
        for fc in cd.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "SINE"; kp.easing = ease_mode
    return cam, look

def camera_along(points, target_object, lens=40, fstop=2.8, offset=(0, 0, 0)):
    """Camera merge paralel cu un traseu si tine ochii pe un obiect."""
    cd = bpy.data.cameras.new("Camera")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.focus_object = target_object
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Camera", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    t = cam.constraints.new("TRACK_TO")
    t.target = target_object
    t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    off = Vector(offset)
    for fr in range(1, TOTAL + 1):
        cam.location = sample_path(points, (fr - 1) / (TOTAL - 1)) + off
        cam.keyframe_insert("location", frame=fr)
    ease(cam, "EASE_IN_OUT", "LINEAR")
    return cam

# ------------------------------------------------------------------- randare
def setup_render(studio=False, passes=True):
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, TOTAL
    engines = [e.identifier for e in
               bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    if ENGINE.startswith("cyc"):
        sc.render.engine = "CYCLES"
        sc.cycles.samples = SAMPLES
        dn = [d.identifier for d in sc.cycles.bl_rna.properties["denoiser"].enum_items]
        have = [d for d in ("OPENIMAGEDENOISE", "OPTIX") if d in dn]
        if have and not flag("--no-denoise"):
            sc.cycles.use_denoising = True; sc.cycles.denoiser = have[0]
        else:
            # Fara denoiser, zgomotul difera de la un cadru la altul — adica exact
            # palpaiala care strica un hero scrubuit — asa ca il inecam in
            # sample-uri. Exceptie: --fast, pentru verificat cadrarea, unde nu ne
            # intereseaza zgomotul si vrem raspuns in zeci de secunde.
            sc.cycles.use_denoising = False
            if not flag("--fast"):
                sc.cycles.samples = max(SAMPLES, 192)
            print(f"[kit] fara denoiser in build — {sc.cycles.samples} sample-uri")
        if hasattr(sc.cycles, "use_adaptive_sampling"):
            sc.cycles.use_adaptive_sampling = False
        try:
            pr = bpy.context.preferences.addons["cycles"].preferences
            pr.get_devices()
            for dt in ("OPTIX", "CUDA", "HIP", "METAL"):
                try:
                    pr.compute_device_type = dt
                except Exception:
                    continue
                pr.get_devices()
                # a accepta numele tipului nu inseamna ca exista placa: fara
                # verificarea asta, Cycles porneste pe "GPU" si randeaza gol
                gpus = [d for d in pr.devices if d.type == dt]
                if gpus:
                    for d in pr.devices:
                        d.use = (d.type == dt)
                    sc.cycles.device = "GPU"
                    print(f"[kit] GPU: {dt} ({len(gpus)})")
                    break
            else:
                sc.cycles.device = "CPU"
                print("[kit] Cycles pe CPU")
        except Exception:
            pass
    else:
        sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines
                            else "BLENDER_EEVEE")
        for f, v in (("taa_render_samples", 64), ("use_gtao", True), ("use_ssr", True),
                     ("use_ssr_refraction", True), ("use_raytracing", True)):
            if hasattr(sc.eevee, f):
                setattr(sc.eevee, f, v)

    sc.render.use_motion_blur = False       # cadrele se scrubuiesc
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = not studio
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = OUT_DIR + "beauty/"
    vt = [t.identifier for t in
          sc.view_settings.bl_rna.properties["view_transform"].enum_items]
    sc.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
    try:
        sc.view_settings.look = ("AgX - Medium High Contrast"
                                 if sc.view_settings.view_transform == "AgX"
                                 else "Medium High Contrast")
    except Exception:
        pass

    if passes:
        vl = sc.view_layers[0]
        vl.use_pass_z = True; vl.use_pass_normal = True
        sc.use_nodes = True
        nt = sc.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        rl = nt.nodes.new("CompositorNodeRLayers")
        cp = nt.nodes.new("CompositorNodeComposite")
        nt.links.new(rl.outputs["Image"], cp.inputs["Image"])
        if "Alpha" in rl.outputs and "Alpha" in cp.inputs:
            nt.links.new(rl.outputs["Alpha"], cp.inputs["Alpha"])
        nz = nt.nodes.new("CompositorNodeNormalize")
        iv = nt.nodes.new("CompositorNodeInvert")
        nt.links.new(rl.outputs["Depth"], nz.inputs[0])
        nt.links.new(nz.outputs[0], iv.inputs["Color"])
        fd = nt.nodes.new("CompositorNodeOutputFile")
        fd.base_path = OUT_DIR + "depth/"; fd.format.color_mode = "BW"
        nt.links.new(iv.outputs["Color"], fd.inputs[0])
        fn = nt.nodes.new("CompositorNodeOutputFile")
        fn.base_path = OUT_DIR + "normal/"; fn.format.color_mode = "RGB"
        nt.links.new(rl.outputs["Normal"], fn.inputs[0])
        globals()["_FILE_OUTS"] = (fd, fn)
    return sc

def render_still(mult=2):
    if flag("--fast"):
        mult = 1
    sc = bpy.context.scene
    sc.frame_set(min(max(STILL, 1), TOTAL))
    sc.render.resolution_x = RES_X * mult
    sc.render.resolution_y = RES_Y * mult
    sc.render.filepath = OUT_DIR + f"ancora_frame{STILL:04d}.png"
    for fo in globals().get("_FILE_OUTS", ()):
        fo.mute = True
    bpy.ops.render.render(write_still=True)
    for fo in globals().get("_FILE_OUTS", ()):
        fo.mute = False
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.filepath = OUT_DIR + "beauty/"
    print(f"[kit] cadru-ancora scris ({RES_X*mult}x{RES_Y*mult})")

def finish():
    """Se cheama la finalul fiecarei scene."""
    if flag("--still-only"):
        render_still()
    elif flag("--with-still"):
        render_still()
    print(f"[kit] {len(PARTS)} obiecte, {TOTAL} cadre, {bpy.context.scene.render.engine}")
    print(f"[kit] iese in: {OUT_DIR}")

def debug_camera(dist=14.0, height=5.0, target=(0, 0, 0)):
    """Camera statica, fara profunzime de camp, pentru verificat scena.
    Se activeaza cu --debug-cam si ignora camera scenei."""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=target)
    look = bpy.context.active_object; look.name = "DBG_Target"
    cd = bpy.data.cameras.new("DebugCam"); cd.lens = 35
    cam = bpy.data.objects.new("DebugCam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (dist * 0.35, -dist, height)
    t = cam.constraints.new("TRACK_TO")
    t.target = look; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return cam
