"""SpikeClip scroll film, v2: dusk over the bay.

A low camera over live water, a dense lit skyline across the bay, an arched
causeway washed in pink light, palms and trees on the shore, a speedboat in
SpikeClip colours carving a wake, birds and a helicopter in a real cloudy
dusk sky, then a phone playing a clip rising out of the water in a burst of
gold coins.

Sky and the shore trees / buoy are CC0 assets from Poly Haven (see ASSETS).

blender -b --factory-startup -P bay_scene.py -- preview 1,90,180 50
blender -b --factory-startup -P bay_scene.py -- render [a-b]
"""
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["preview", "1"]
MODE = ARGS[0]
SCRATCH = Path(r"C:\Users\chipl\AppData\Local\Temp\claude\75f48fb559855b2d\e46a1d45-c501-4d1d-93e6-6bdd9a68f475\scratchpad")
OUT = SCRATCH / "film2"
ASSETS = SCRATCH / "ph"
CLIP = r"C:\Users\chipl\Desktop\clip pulse\clips-studio\frontend\src\renderer\public\media\clips\c5.mp4"
FRAMES = 180
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.fps = 30


def enum_pick(owner, prop, wanted):
    items = [i.identifier for i in owner.bl_rna.properties[prop].enum_items]
    return next((w for w in wanted if w in items), items[0])


def mat(name, color=(1, 1, 1), metal=0.0, rough=0.5, emit=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m, b


def link(obj):
    sc.collection.objects.link(obj)
    return obj


def box(name, size, loc, material=None, bevel=0.0):
    """A box built at the origin and then moved (Blender 5 bakes location on apply)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.location = loc
    if bevel:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 3
    if material:
        o.data.materials.append(material)
    return o


def keys(obj, path, frames_values, interp=None):
    for f, v in frames_values:
        setattr(obj, path, v)
        obj.keyframe_insert(path, frame=f)


# ------------------------------------------------------------------ render settings
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
for attr, val in (("taa_render_samples", 32), ("use_raytracing", True), ("use_shadows", True), ("use_fast_gi", True),
                  ("volumetric_tile_size", "8"), ("volumetric_end", 600.0), ("volumetric_samples", 48)):
    try:
        setattr(sc.eevee, attr, val)
    except (AttributeError, TypeError):
        pass
try:
    sc.eevee.ray_tracing_options.resolution_scale = "2"
except Exception:  # noqa: BLE001
    pass
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = enum_pick(sc.view_settings, "look", ["AgX - Punchy", "Punchy"])
except TypeError:
    pass
sc.view_settings.exposure = -0.9

# ------------------------------------------------------------------ sky: real dusk HDRI, graded to lavender
w = bpy.data.worlds.new("Sky")
sc.world = w
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
N, L = nt.nodes.new, nt.links.new
tc = N("ShaderNodeTexCoord")
mp = N("ShaderNodeMapping")
mp.inputs["Rotation"].default_value = (0, 0, math.radians(200))
L(tc.outputs["Generated"], mp.inputs["Vector"])
env = N("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ASSETS / "sky" / "belfast_4k.hdr"))
L(mp.outputs["Vector"], env.inputs["Vector"])
hsv = N("ShaderNodeHueSaturation")
hsv.inputs["Hue"].default_value = 0.53  # nudge toward magenta
hsv.inputs["Saturation"].default_value = 1.7
L(env.outputs["Color"], hsv.inputs["Color"])
tint = N("ShaderNodeMix")
tint.data_type = "RGBA"
tint.blend_type = "MULTIPLY"
tint.inputs["Factor"].default_value = 1
tint.inputs["B"].default_value = (0.82, 0.6, 1.2, 1)
L(hsv.outputs["Color"], tint.inputs["A"])
bg = N("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.42
L(tint.outputs["Result"], bg.inputs["Color"])
wo = N("ShaderNodeOutputWorld")
L(bg.outputs[0], wo.inputs["Surface"])

moon = link(bpy.data.objects.new("Dusk", bpy.data.lights.new("Dusk", "SUN")))
moon.data.energy = 0.9
moon.data.color = (1.0, 0.62, 0.78)
moon.data.angle = math.radians(4)
moon.rotation_euler = (math.radians(80), 0, math.radians(165))

# ------------------------------------------------------------------ water
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
ocean = bpy.context.object
ocean.name = "Ocean"
ocean.location = (-320, -60, 0)
om = ocean.modifiers.new("Ocean", "OCEAN")
om.resolution = 11
om.spatial_size = 80
om.repeat_x, om.repeat_y = 8, 4
om.wave_scale = 0.8
om.choppiness = 1.6
om.wind_velocity = 9
om.wave_scale_min = 0.01
om.use_normals = True
om.use_foam = True
om.foam_coverage = 0.25
om.foam_layer_name = "foam"
keys(om, "time", [(1, 2.0), (FRAMES, 2.0 + FRAMES / 30)])
m_water, b = mat("Water", (0.015, 0.012, 0.045), rough=0.09)
b.inputs["Specular IOR Level"].default_value = 0.6
wn = m_water.node_tree
fa = wn.nodes.new("ShaderNodeAttribute")
fa.attribute_name = "foam"
fm = wn.nodes.new("ShaderNodeMix")
fm.data_type = "RGBA"
fm.inputs["A"].default_value = (0.025, 0.02, 0.06, 1)
fm.inputs["B"].default_value = (0.75, 0.7, 0.85, 1)
fr = wn.nodes.new("ShaderNodeMapRange")
fr.inputs["From Min"].default_value = 0.35
fr.inputs["From Max"].default_value = 1.0
wn.links.new(fa.outputs["Fac"], fr.inputs["Value"])
wn.links.new(fr.outputs["Result"], fm.inputs["Factor"])
wn.links.new(fm.outputs["Result"], b.inputs["Base Color"])
ocean.data.materials.append(m_water)
for p in ocean.data.polygons:
    p.use_smooth = True

# ------------------------------------------------------------------ skyline: towers with real window grids
SHORE_Y = 330


def facade(name, lit, glass, frame, density, accent=None):
    """Window grid from a brick texture: each 'brick' is one window, lit or dark at random."""
    m, b = mat(name, frame, rough=0.4, metal=0.3)
    t = m.node_tree
    tco = t.nodes.new("ShaderNodeTexCoord")
    sep = t.nodes.new("ShaderNodeSeparateXYZ")
    t.links.new(tco.outputs["Object"], sep.inputs[0])
    uv = t.nodes.new("ShaderNodeCombineXYZ")
    add = t.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    t.links.new(sep.outputs["X"], add.inputs[0])
    t.links.new(sep.outputs["Y"], add.inputs[1])
    t.links.new(add.outputs[0], uv.inputs["X"])
    t.links.new(sep.outputs["Z"], uv.inputs["Y"])
    br = t.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Color1"].default_value = (0, 0, 0, 1)
    br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.45
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = 1.7
    br.inputs["Row Height"].default_value = 3.3
    t.links.new(uv.outputs[0], br.inputs["Vector"])
    on = t.nodes.new("ShaderNodeMath")  # lit if the brick's random value > 1 - density
    on.operation = "GREATER_THAN"
    on.inputs[1].default_value = 1 - density
    t.links.new(br.outputs["Color"], on.inputs[0])
    win = t.nodes.new("ShaderNodeMath")  # inside a window (not mortar)
    win.operation = "SUBTRACT"
    win.inputs[0].default_value = 1.0
    t.links.new(br.outputs["Fac"], win.inputs[1])
    litmask = t.nodes.new("ShaderNodeMath")
    litmask.operation = "MULTIPLY"
    t.links.new(on.outputs[0], litmask.inputs[0])
    t.links.new(win.outputs[0], litmask.inputs[1])
    # Lit windows vary in warmth/brightness from the brick value.
    tone = t.nodes.new("ShaderNodeMix")
    tone.data_type = "RGBA"
    tone.inputs["A"].default_value = (*lit, 1)
    tone.inputs["B"].default_value = (min(1, lit[0] * 1.1), lit[1] * 0.85, lit[2] * 0.7, 1)
    t.links.new(br.outputs["Color"], tone.inputs["Factor"])
    em = t.nodes.new("ShaderNodeMath")
    em.operation = "MULTIPLY"
    em.inputs[1].default_value = 5.0
    t.links.new(litmask.outputs[0], em.inputs[0])
    t.links.new(tone.outputs["Result"], b.inputs["Emission Color"])
    t.links.new(em.outputs[0], b.inputs["Emission Strength"])
    base = t.nodes.new("ShaderNodeMix")
    base.data_type = "RGBA"
    base.inputs["A"].default_value = (*frame, 1)
    base.inputs["B"].default_value = (*glass, 1)
    t.links.new(win.outputs[0], base.inputs["Factor"])
    t.links.new(base.outputs["Result"], b.inputs["Base Color"])
    rough = t.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.6
    rough.inputs["To Max"].default_value = 0.08
    t.links.new(win.outputs[0], rough.inputs["Value"])
    t.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    return m


FACADES = [
    facade("OfficeWarm", (1.0, 0.72, 0.4), (0.02, 0.025, 0.04), (0.05, 0.045, 0.06), 0.42),
    facade("OfficeCool", (0.85, 0.9, 1.0), (0.015, 0.025, 0.04), (0.04, 0.045, 0.06), 0.3),
    facade("Residential", (1.0, 0.66, 0.36), (0.03, 0.025, 0.035), (0.12, 0.1, 0.12), 0.28),
    facade("Glass", (0.95, 0.8, 0.55), (0.015, 0.02, 0.035), (0.03, 0.035, 0.05), 0.18),
]
ACCENTS = [mat(f"Accent{i}", (0, 0, 0), emit=c, strength=s)[0] for i, (c, s) in enumerate(
    [((0.3, 1.0, 0.65), 9), ((0.25, 0.9, 1.0), 9), ((1.0, 0.25, 0.65), 10), ((1.0, 0.85, 0.6), 8)])]
m_red, _ = mat("AirLight", (0, 0, 0), emit=(1, 0.05, 0.02), strength=30)

towers = []
for i in range(58):
    x = random.uniform(-330, 300)
    centre = math.exp(-((x + 20) / 110) ** 2)  # downtown in the middle, lower at the edges
    y = SHORE_Y + 25 + random.uniform(0, 140)
    h = random.uniform(18, 45) + centre * random.uniform(25, 130)
    wdt, dep = random.uniform(14, 30), random.uniform(14, 30)
    fac = random.choice(FACADES[:2] if h > 90 else FACADES)
    t = box("Tower", (wdt, dep, h), (x, y, h / 2), fac)
    towers.append(t)
    if h > 70 and random.random() < 0.7:  # set-back crown with a lit band
        ch = random.uniform(6, 16)
        box("Crown", (wdt * 0.72, dep * 0.72, ch), (x, y, h + ch / 2), fac)
        box("Band", (wdt * 0.74, dep * 0.74, 1.2), (x, y, h + ch - 0.8), random.choice(ACCENTS))
        top = h + ch
    else:
        top = h
        if random.random() < 0.35:
            box("Band", (wdt * 1.01, dep * 1.01, 1.0), (x, y, h - 1.0), random.choice(ACCENTS))
    if h > 110:  # antenna + aircraft warning light
        box("Mast", (0.6, 0.6, 18), (x, y, top + 9), mat("Mast", (0.1, 0.1, 0.1))[0])
        box("Red", (1.1, 1.1, 1.1), (x, y, top + 18.5), m_red)

# Hero tower with a SPIKECLIP rooftop sign (our brand on the skyline).
hero = box("HeroTower", (30, 26, 175), (-35, SHORE_Y + 70, 87.5), FACADES[1])
box("HeroCrown", (22, 20, 20), (-35, SHORE_Y + 70, 185), FACADES[1])
box("HeroBand", (22.4, 20.4, 1.6), (-35, SHORE_Y + 70, 194), ACCENTS[1])
sign = bpy.data.curves.new("Sign", "FONT")
sign.body = "SPIKECLIP"
sign.align_x = "CENTER"
sign.extrude = 0.3
so = link(bpy.data.objects.new("Sign", sign))
so.location = (-35, SHORE_Y + 70 - 13.2, 176)
so.rotation_euler = (math.pi / 2, 0, 0)
so.scale = (5.2,) * 3
m_neon, _ = mat("Neon", (0, 0, 0), emit=(1.0, 0.2, 0.62), strength=40)
sign.materials.append(m_neon)

# Low-rise waterfront strip with warm windows.
for i in range(40):
    x = -330 + i * 16 + random.uniform(-2, 2)
    h = random.uniform(6, 16)
    box("Low", (random.uniform(8, 12), 10, h), (x, SHORE_Y + 12, h / 2), FACADES[2])

# Shore: a seawall and a dark land strip.
box("Land", (600, 160, 2.0), (-20, SHORE_Y + 75, 0.3), mat("Land", (0.03, 0.03, 0.03), rough=0.9)[0])
box("Seawall", (600, 2, 2.2), (-20, SHORE_Y - 5, 0.4), mat("Wall", (0.35, 0.33, 0.36), rough=0.8)[0])
# Promenade lights along the seawall.
m_lamp, _ = mat("Lamp", (0, 0, 0), emit=(1.0, 0.8, 0.55), strength=40)
for i in range(60):
    x = -330 + i * 11
    box("Pole", (0.25, 0.25, 5), (x, SHORE_Y - 3, 3.5), mat("PoleM", (0.05, 0.05, 0.05))[0])
    box("Bulb", (0.7, 0.7, 0.5), (x, SHORE_Y - 3, 6.1), m_lamp)

# ------------------------------------------------------------------ palms (dense leaflets) and Poly Haven trees on the shore
m_trunk, b = mat("Trunk", (0.05, 0.035, 0.03), rough=0.85)
m_leaf, b = mat("Leaf", (0.02, 0.06, 0.025), rough=0.6)
m_leaf.use_backface_culling = False


def frond_mesh(length):
    bm = bmesh.new()
    segs = 18
    for i in range(segs):
        t0, t1 = i / segs, (i + 1) / segs
        p0 = Vector((t0 * length, 0, -0.45 * (t0 * length) ** 2 / length))
        p1 = Vector((t1 * length, 0, -0.45 * (t1 * length) ** 2 / length))
        leaf = 0.75 * math.sin(math.pi * min(1, t0 * 1.1)) + 0.1
        for side in (-1, 1):
            tip = p0 + Vector((0.35, side * leaf, -leaf * 0.7))
            v = [bm.verts.new(p0), bm.verts.new(p1), bm.verts.new(tip)]
            bm.faces.new(v)
    me = bpy.data.meshes.new("Frond")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m_leaf)
    return me


FRONDS = [frond_mesh(random.uniform(3.4, 4.6)) for _ in range(6)]


def palm(x, y, h, lean):
    cu = bpy.data.curves.new("Trunk", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co, r in zip(sp.bezier_points, [(0, 0, 0), (lean * 0.3, 0, h * 0.5), (lean, 0, h)], (1.3, 1.0, 0.8)):
        bp.co = co
        bp.radius = r
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.22
    cu.bevel_resolution = 3
    cu.materials.append(m_trunk)
    tr = link(bpy.data.objects.new("Palm", cu))
    tr.location = (x, y, 0.8)
    tr.rotation_euler.z = random.uniform(0, math.tau)
    crown = link(bpy.data.objects.new("Crown", None))
    crown.parent = tr
    crown.location = (lean, 0, h)
    for k in range(16):
        f = link(bpy.data.objects.new("Frond", random.choice(FRONDS)))
        f.parent = crown
        f.rotation_euler = (0, -random.uniform(-0.2, 0.55), k / 16 * math.tau + random.uniform(-0.15, 0.15))
    ph = random.uniform(0, 6)
    for fr in range(1, FRAMES + 1, 12):
        crown.rotation_euler = (0.05 * math.sin(fr * 0.1 + ph), 0.04 * math.cos(fr * 0.08 + ph), 0)
        crown.keyframe_insert("rotation_euler", frame=fr)


for i in range(110):
    palm(random.uniform(-330, 300), SHORE_Y + random.uniform(-2, 10), random.uniform(10, 19), random.uniform(-2.5, 2.5))

try:
    bpy.ops.import_scene.gltf(filepath=str(ASSETS / "island_tree_01" / "island_tree_01.gltf"))
    parts = [o for o in bpy.context.selected_objects]
    tree_col = bpy.data.collections.new("TreeSrc")
    for o in parts:
        for c in o.users_collection:
            c.objects.unlink(o)
        tree_col.objects.link(o)
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in parts if o.type == "MESH" for c in o.bound_box]
    tree_h = max(zs) - min(zs)
    for i in range(16):
        e = link(bpy.data.objects.new("Tree", None))
        e.instance_type = "COLLECTION"
        e.instance_collection = tree_col
        s = random.uniform(10, 16) / tree_h
        e.scale = (s, s, s)
        e.location = (random.uniform(-330, 300), SHORE_Y + random.uniform(0, 12), 0.8)
        e.rotation_euler.z = random.uniform(0, math.tau)
    print("TREES ok", round(tree_h, 2))
except Exception as ex:  # noqa: BLE001
    print("TREES skipped", ex)

# ------------------------------------------------------------------ the causeway: arches washed in pink from below
m_conc, _ = mat("Concrete", (0.55, 0.5, 0.52), rough=0.75)
m_pink, _ = mat("PinkWash", (0, 0, 0), emit=(1.0, 0.18, 0.7), strength=14)
BR_Y, BR_Z = SHORE_Y - 60, 11
bx0, bx1 = 30, 360
box("Deck", (bx1 - bx0, 12, 1.8), ((bx0 + bx1) / 2, BR_Y, BR_Z), m_conc)
box("Rail", (bx1 - bx0, 0.3, 1.0), ((bx0 + bx1) / 2, BR_Y - 6, BR_Z + 1.4), m_conc)
span = 20
for i in range(int((bx1 - bx0) / span) + 1):
    x = bx0 + i * span
    box("Pier", (2.4, 9, BR_Z), (x, BR_Y, BR_Z / 2 - 0.5), m_conc)
    box("Wash", (2.45, 0.2, BR_Z * 0.8), (x, BR_Y - 4.6, BR_Z * 0.4), m_pink)
    if i:
        cu = bpy.data.curves.new("Arch", "CURVE")
        cu.dimensions = "3D"
        spl = cu.splines.new("POLY")
        n = 16
        spl.points.add(n)
        for k in range(n + 1):
            a = math.pi * k / n
            spl.points[k].co = (-(span / 2 - 1.2) * math.cos(a), 0, (BR_Z - 3) * math.sin(a) * 0.55 + 2, 1)
        cu.bevel_depth = 0.6
        cu.materials.append(m_conc)
        ar = link(bpy.data.objects.new("Arch", cu))
        ar.location = (x - span / 2, BR_Y - 4.4, 0)
    if i % 2 == 0:
        lt = link(bpy.data.objects.new("Uplight", bpy.data.lights.new("Up", "AREA")))
        lt.data.energy = 3500
        lt.data.color = (1.0, 0.25, 0.7)
        lt.data.size = 6
        lt.location = (x, BR_Y - 9, 0.6)
        lt.rotation_euler = (math.radians(-35), 0, 0)
# Road lamps on the deck.
for i in range(15):
    box("DeckLamp", (0.5, 0.5, 0.4), (bx0 + i * 20, BR_Y - 5.5, BR_Z + 5), m_lamp)

# ------------------------------------------------------------------ channel marker buoy (Poly Haven) with a green light
try:
    bpy.ops.import_scene.gltf(filepath=str(ASSETS / "lateral_sea_marker" / "lateral_sea_marker.gltf"))
    buoy_parts = list(bpy.context.selected_objects)
    root = link(bpy.data.objects.new("Buoy", None))
    for o in buoy_parts:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in buoy_parts if o.type == "MESH" for c in o.bound_box]
    s = 4.2 / (max(zs) - min(zs))
    root.scale = (s, s, s)
    root.location = (22, 62, -0.9)
    for fr in range(1, FRAMES + 1, 15):
        root.rotation_euler = (0.06 * math.sin(fr * 0.13), 0.05 * math.cos(fr * 0.11), 0.3)
        root.location.z = -0.9 + 0.18 * math.sin(fr * 0.12)
        root.keyframe_insert("rotation_euler", frame=fr)
        root.keyframe_insert("location", frame=fr)
    gl = link(bpy.data.objects.new("BuoyLight", bpy.data.lights.new("BuoyLight", "POINT")))
    gl.data.energy = 900
    gl.data.color = (0.35, 1.0, 0.3)
    gl.parent = root
    gl.location = (0, 0, 4.6 / s)
    print("BUOY ok")
except Exception as ex:  # noqa: BLE001
    print("BUOY skipped", ex)

# ------------------------------------------------------------------ speedboat in SpikeClip colours
m_hull = bpy.data.materials.new("Hull")
m_hull.use_nodes = True
hn = m_hull.node_tree
hb = next(n for n in hn.nodes if n.type == "BSDF_PRINCIPLED")
hb.inputs["Roughness"].default_value = 0.18
hb.inputs["Coat Weight"].default_value = 1.0
hco = hn.nodes.new("ShaderNodeTexCoord")
hsep = hn.nodes.new("ShaderNodeSeparateXYZ")
hn.links.new(hco.outputs["Object"], hsep.inputs[0])
hx = hn.nodes.new("ShaderNodeMapRange")  # stern (x=-4.5) cyan -> bow (x=4.5) pink
hx.inputs["From Min"].default_value = -4.0
hx.inputs["From Max"].default_value = 4.5
hn.links.new(hsep.outputs["X"], hx.inputs["Value"])
hramp = hn.nodes.new("ShaderNodeValToRGB")
hramp.color_ramp.elements[0].color = (0.25, 0.85, 0.95, 1)
hramp.color_ramp.elements[1].color = (1.0, 0.3, 0.62, 1)
mid = hramp.color_ramp.elements.new(0.5)
mid.color = (0.82, 0.78, 0.98, 1)
hn.links.new(hx.outputs["Result"], hramp.inputs["Fac"])
# Leafy wrap pattern: voronoi cracks as pale fronds over the gradient.
vor = hn.nodes.new("ShaderNodeTexVoronoi")
vor.feature = "DISTANCE_TO_EDGE"
vor.inputs["Scale"].default_value = 3.2
hn.links.new(hco.outputs["Object"], vor.inputs["Vector"])
vr = hn.nodes.new("ShaderNodeMapRange")
vr.inputs["From Min"].default_value = 0.0
vr.inputs["From Max"].default_value = 0.035
vr.inputs["To Min"].default_value = 0.55
vr.inputs["To Max"].default_value = 0.0
hn.links.new(vor.outputs["Distance"], vr.inputs["Value"])
wrap = hn.nodes.new("ShaderNodeMix")
wrap.data_type = "RGBA"
wrap.inputs["B"].default_value = (1, 1, 1, 1)
hn.links.new(vr.outputs["Result"], wrap.inputs["Factor"])
hn.links.new(hramp.outputs["Color"], wrap.inputs["A"])
# White above the sheer stripe (z > 0.55).
hz = hn.nodes.new("ShaderNodeMapRange")
hz.inputs["From Min"].default_value = 0.93
hz.inputs["From Max"].default_value = 0.99
hn.links.new(hsep.outputs["Z"], hz.inputs["Value"])
top = hn.nodes.new("ShaderNodeMix")
top.data_type = "RGBA"
top.inputs["B"].default_value = (0.92, 0.92, 0.95, 1)
hn.links.new(hz.outputs["Result"], top.inputs["Factor"])
hn.links.new(wrap.outputs["Result"], top.inputs["A"])
hn.links.new(top.outputs["Result"], hb.inputs["Base Color"])


def hull_mesh():
    """Deep-V planing hull lofted from cross-sections, bow at +X."""
    bm = bmesh.new()
    rings = []
    n = 28
    for i in range(n + 1):
        t = i / n
        x = -4.5 + 9.0 * t
        bow = max(0.0, (t - 0.55) / 0.45)
        half = 1.35 * math.sqrt(max(0.0, 1 - bow ** 2.2)) + 0.02
        keel = -0.55 + 0.45 * bow ** 1.6
        sheer = 0.95 + 0.25 * bow ** 1.5
        chine_y = half * 0.78
        chine_z = keel + 0.32 * (1 - bow * 0.5)
        prof = [(0, keel), (chine_y * 0.5, keel + 0.12), (chine_y, chine_z), (half, chine_z + 0.12),
                (half * 1.02, 0.5), (half, sheer)]
        ring = [bm.verts.new((x, -y, z)) for y, z in reversed(prof[1:])] + [bm.verts.new((x, y, z)) for y, z in prof]
        rings.append(ring)
    for a, b2 in zip(rings, rings[1:]):
        for k in range(len(a) - 1):
            bm.faces.new((a[k], a[k + 1], b2[k + 1], b2[k]))
    bm.faces.new(list(reversed(rings[0])))  # transom
    deck = [r[0] for r in rings] + [r[-1] for r in reversed(rings)]
    bm.faces.new(deck)
    me = bpy.data.meshes.new("Hull")
    bm.to_mesh(me)
    bm.free()
    return me


boat = link(bpy.data.objects.new("Boat", None))
hull = link(bpy.data.objects.new("Hull", hull_mesh()))
hull.parent = boat
hull.data.materials.append(m_hull)
ss = hull.modifiers.new("Smooth", "SUBSURF")
ss.levels = ss.render_levels = 2
for p in hull.data.polygons:
    p.use_smooth = True
m_white, _ = mat("White", (0.9, 0.9, 0.93), rough=0.25, coat=0.6)
m_chrome, _ = mat("Chrome", (0.9, 0.9, 0.95), metal=1.0, rough=0.08)
m_glass, gb = mat("Glass", (0.05, 0.07, 0.1), rough=0.02)
gb.inputs["Transmission Weight"].default_value = 0.6
m_black, _ = mat("Rub", (0.02, 0.02, 0.02), rough=0.4)
m_teak, _ = mat("Deck", (0.75, 0.73, 0.7), rough=0.6)
# Rub rail, deck, cabin, windshield, hardtop arch, rails, outboard.
for side in (-1, 1):
    rr = box("RubRail", (7.6, 0.06, 0.08), (-0.6, side * 1.36, 0.56), m_black)
    rr.parent = boat
    port = box("Porthole", (1.4, 0.03, 0.18), (1.2, side * 1.33, 0.78), m_black, bevel=0.06)
    port.parent = boat
d = box("Cockpit", (5.0, 2.2, 0.12), (-1.7, 0, 1.0), m_teak)
d.parent = boat
cab = box("Cabin", (2.6, 1.9, 0.5), (1.5, 0, 1.22), m_white, bevel=0.25)
cab.parent = boat
ws = box("Windshield", (0.08, 2.1, 0.55), (0.15, 0, 1.6), m_glass, bevel=0.03)
ws.rotation_euler.y = math.radians(-35)
ws.parent = boat
seat = box("Helm", (0.7, 0.7, 0.6), (-0.9, -0.4, 1.35), m_white, bevel=0.12)
seat.parent = boat
for side in (-1, 1):
    leg = box("ArchLeg", (0.15, 0.15, 1.6), (-1.2, side * 1.05, 1.85), m_white, bevel=0.05)
    leg.rotation_euler.y = math.radians(-18)
    leg.parent = boat
roof = box("Hardtop", (2.2, 2.25, 0.12), (-0.55, 0, 2.62), m_white, bevel=0.1)
roof.rotation_euler.y = math.radians(-4)
roof.parent = boat
light = box("NavLight", (0.12, 0.12, 0.12), (-0.5, 0, 2.74), mat("NavL", (0, 0, 0), emit=(1, 1, 1), strength=60)[0])
light.parent = boat
for side in (-1, 1):  # bow rails
    cu = bpy.data.curves.new("Rail", "CURVE")
    cu.dimensions = "3D"
    spl = cu.splines.new("POLY")
    pts = [(0.4, side * 1.25, 1.35), (2.4, side * 1.0, 1.5), (3.9, side * 0.35, 1.62), (4.35, 0, 1.62)]
    spl.points.add(len(pts) - 1)
    for k, p in enumerate(pts):
        spl.points[k].co = (*p, 1)
    cu.bevel_depth = 0.025
    cu.materials.append(m_chrome)
    r = link(bpy.data.objects.new("Rail", cu))
    r.parent = boat
    for k in range(3):
        st = box("Stanchion", (0.03, 0.03, 0.4), (0.9 + k * 1.2, side * (1.18 - k * 0.22), 1.33), m_chrome)
        st.parent = boat
eng = box("Outboard", (0.55, 0.45, 1.0), (-4.75, 0, 0.55), m_black, bevel=0.12)
eng.parent = boat
# Name on the hull.
for side in (-1, 1):
    nm = bpy.data.curves.new("BoatName", "FONT")
    nm.body = "SPIKECLIP"
    nm.size = 0.32
    nm.extrude = 0.005
    nm.materials.append(mat("NameInk", (0.03, 0.03, 0.05), rough=0.3)[0])
    no = link(bpy.data.objects.new("BoatName", nm))
    no.parent = boat
    no.location = (-3.6 if side < 0 else -1.4, side * 1.37, 0.62)
    no.rotation_euler = (math.pi / 2, 0, 0 if side < 0 else math.pi)
# Wake: a foam trail and bow spray, built as noisy alpha planes that follow the boat.
m_foam = bpy.data.materials.new("Foam")
m_foam.use_nodes = True
fn = m_foam.node_tree
fn.nodes.clear()
fco = fn.nodes.new("ShaderNodeTexCoord")
fno = fn.nodes.new("ShaderNodeTexNoise")
fno.inputs["Scale"].default_value = 6
fno.inputs["Detail"].default_value = 12
fn.links.new(fco.outputs["Object"], fno.inputs["Vector"])
fgr = fn.nodes.new("ShaderNodeTexGradient")
fgr.gradient_type = "LINEAR"
fn.links.new(fco.outputs["UV"], fgr.inputs["Vector"])
fmul = fn.nodes.new("ShaderNodeMath")
fmul.operation = "MULTIPLY"
fn.links.new(fno.outputs["Fac"], fmul.inputs[0])
fn.links.new(fgr.outputs["Fac"], fmul.inputs[1])
fcut = fn.nodes.new("ShaderNodeMapRange")
fcut.inputs["From Min"].default_value = 0.15
fcut.inputs["From Max"].default_value = 0.45
fn.links.new(fmul.outputs[0], fcut.inputs["Value"])
fp = fn.nodes.new("ShaderNodeBsdfPrincipled")
fp.inputs["Base Color"].default_value = (0.85, 0.85, 0.95, 1)
fp.inputs["Roughness"].default_value = 0.5
fn.links.new(fcut.outputs["Result"], fp.inputs["Alpha"])
fo = fn.nodes.new("ShaderNodeOutputMaterial")
fn.links.new(fp.outputs[0], fo.inputs["Surface"])
try:
    m_foam.surface_render_method = "BLENDED"
except AttributeError:
    pass
for side in (-1, 1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    wk = bpy.context.object
    wk.name = "Wake"
    wk.scale = (24, 3.2, 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in wk.data.vertices:  # flare outwards behind the boat
        v.co.y += side * (0.5 - (v.co.x + 12) / 24) * -5
    wk.location = (-16, side * 2.2, 0.32)
    wk.rotation_euler.z = math.pi  # UV gradient strongest at the transom
    wk.data.materials.append(m_foam)
    wk.parent = boat
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
churn = bpy.context.object
churn.scale = (10, 2.6, 1)
bpy.ops.object.transform_apply(scale=True)
churn.location = (-9.5, 0, 0.34)
churn.rotation_euler.z = math.pi
churn.data.materials.append(m_foam)
churn.parent = boat

# Its own light rig so the wrap reads at dusk (dock lights / sunset bounce).
for nm_, off, col, en in (("BoatKey", (3, -7, 5), (1.0, 0.85, 0.9), 2600), ("BoatFill", (-6, -4, 2), (0.5, 0.75, 1.0), 900)):
    bl = link(bpy.data.objects.new(nm_, bpy.data.lights.new(nm_, "AREA")))
    bl.data.energy = en
    bl.data.color = col
    bl.data.size = 6
    bl.parent = boat
    bl.location = off
    bl.rotation_euler = (-Vector(off)).to_track_quat("-Z", "Y").to_euler()

# Boat run: left to right across the bay, pitching and rolling on the chop.
BOAT_PATH = [(1, (-62, 22, 0.25)), (90, (-12, 19, 0.25)), (FRAMES, (40, 17, 0.25))]
for f, loc in BOAT_PATH:
    boat.location = loc
    boat.keyframe_insert("location", frame=f)
for f in range(1, FRAMES + 1, 6):
    boat.rotation_euler = (0.035 * math.sin(f * 0.21), math.radians(-5) + 0.03 * math.sin(f * 0.17), math.radians(-3))
    boat.location.z = 0.25 + 0.09 * math.sin(f * 0.23)
    boat.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ birds and a helicopter
m_sil, _ = mat("Silhouette", (0.01, 0.01, 0.015), rough=0.8)
for i in range(6):
    bird = link(bpy.data.objects.new("Bird", None))
    for side in (-1, 1):
        bm = bmesh.new()
        v = [bm.verts.new((0, 0, 0)), bm.verts.new((0.35, side * 0.05, 0)), bm.verts.new((-0.1, side * 0.9, 0.05))]
        bm.faces.new(v)
        me = bpy.data.meshes.new("Wing")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m_sil)
        wing = link(bpy.data.objects.new("Wing", me))
        wing.parent = bird
        for f in range(1, FRAMES + 1, 3):
            wing.rotation_euler = (side * 0.6 * math.sin(f * 0.9 + i), 0, 0)
            wing.keyframe_insert("rotation_euler", frame=f)
    body = box("BirdBody", (0.5, 0.12, 0.1), (0, 0, 0), m_sil)
    body.parent = bird
    start = Vector((random.uniform(-60, 0), random.uniform(90, 140), random.uniform(28, 45)))
    bird.scale = (2.2,) * 3
    keys(bird, "location", [(1, start), (FRAMES, start + Vector((random.uniform(35, 55), random.uniform(-10, 10), random.uniform(-3, 4))))])

heli = link(bpy.data.objects.new("Heli", None))
hbody = box("HeliBody", (3.2, 1.4, 1.4), (0, 0, 0), m_sil, bevel=0.6)
hbody.parent = heli
tail = box("Tail", (4.0, 0.25, 0.3), (-3.4, 0, 0.3), m_sil)
tail.parent = heli
rotor = box("Rotor", (7.5, 0.25, 0.04), (0, 0, 0.95), m_sil)
rotor.parent = heli
for f in range(1, FRAMES + 1, 2):
    rotor.rotation_euler.z = f * 1.3
    rotor.keyframe_insert("rotation_euler", frame=f)
blink = box("Blink", (0.3, 0.3, 0.3), (0, 0, -0.8), m_red)
blink.parent = heli
for f in range(1, FRAMES + 1):
    blink.hide_render = (f // 8) % 2 == 1
    blink.keyframe_insert("hide_render", frame=f)
heli.scale = (2.5,) * 3
keys(heli, "location", [(1, Vector((40, 230, 85))), (FRAMES, Vector((-30, 220, 95)))])
heli.rotation_euler.z = math.pi

# ------------------------------------------------------------------ the phone rising out of the water + coin burst
PHONE = Vector((10, 22, 3.4))
phone = box("Phone", (0.95, 0.11, 1.95), (0, 0, 0), mat("Body", (0.02, 0.02, 0.025), metal=0.9, rough=0.15, coat=1.0)[0], bevel=0.13)
for p in phone.data.polygons:
    p.use_smooth = True
band = box("Band", (0.97, 0.07, 1.97), (0, 0, 0), mat("BandN", (0, 0, 0), emit=(1.0, 0.3, 0.65), strength=12)[0], bevel=0.135)
band.parent = phone
band.location = (0, 0, 0)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
screen = bpy.context.object
screen.rotation_euler.x = math.pi / 2
screen.scale = (0.86, 1.82, 1)
m_scr = bpy.data.materials.new("Screen")
m_scr.use_nodes = True
sn = m_scr.node_tree
sn.nodes.clear()
img = bpy.data.images.load(CLIP)
img.source = "MOVIE"
tex = sn.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.image_user.frame_duration = 400
tex.image_user.frame_offset = 40
tex.image_user.use_auto_refresh = True
tex.image_user.use_cyclic = True
tex.extension = "CLIP"
em = sn.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 1.5
so2 = sn.nodes.new("ShaderNodeOutputMaterial")
sn.links.new(tex.outputs["Color"], em.inputs["Color"])
sn.links.new(em.outputs[0], so2.inputs["Surface"])
screen.data.materials.append(m_scr)
screen.parent = phone
screen.location = (0, -0.062, 0)
phone.rotation_mode = "XYZ"
for f, z, rz in [(1, -4.0, -0.5), (100, -4.0, -0.5), (138, PHONE.z + 0.35, -0.2), (FRAMES, PHONE.z, -0.08)]:
    phone.location = (PHONE.x, PHONE.y, z)
    phone.rotation_euler = (0, 0, rz)
    phone.keyframe_insert("location", frame=f)
    phone.keyframe_insert("rotation_euler", frame=f)
rim = link(bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", "AREA")))
rim.data.energy = 500
rim.data.color = (1.0, 0.3, 0.7)
rim.data.size = 3
rim.location = PHONE + Vector((1.5, 3, 2))
rim.rotation_euler = (PHONE - rim.location).to_track_quat("-Z", "Y").to_euler()
key = link(bpy.data.objects.new("Key", bpy.data.lights.new("Key", "AREA")))
key.data.energy = 260
key.data.color = (0.75, 0.85, 1.0)
key.data.size = 3
key.location = PHONE + Vector((-3, -5, 2.5))
key.rotation_euler = (PHONE - key.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.17, depth=0.03, location=(0, 0, 0))
coin_src = bpy.context.object
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
coin_src.data.materials.append(mat("Gold", (1.0, 0.7, 0.2), metal=1.0, rough=0.25, emit=(1.0, 0.6, 0.15), strength=0.35)[0])
coin_src.hide_render = coin_src.hide_viewport = True
for i in range(60):
    c = link(bpy.data.objects.new("Coin", coin_src.data))
    a = random.uniform(0, math.tau)
    r = random.uniform(1.4, 4.2)
    end = PHONE + Vector((math.cos(a) * r, abs(math.sin(a)) * r * 0.8 + 0.3, random.uniform(-1.6, 2.6)))
    f0 = 112 + random.randint(0, 26)
    c.location = (PHONE.x, PHONE.y, 0.1)
    c.scale = (0.01,) * 3
    c.keyframe_insert("location", frame=f0)
    c.keyframe_insert("scale", frame=f0)
    c.location = end
    c.scale = (1,) * 3
    c.keyframe_insert("location", frame=f0 + 16)
    c.keyframe_insert("scale", frame=f0 + 16)
    c.location = end - Vector((0, 0, random.uniform(0.3, 0.9)))
    c.keyframe_insert("location", frame=FRAMES)
    c.rotation_euler = (0, 0, 0)
    c.keyframe_insert("rotation_euler", frame=f0)
    c.rotation_euler = (random.uniform(5, 10), random.uniform(2, 6), random.uniform(1, 3))
    c.keyframe_insert("rotation_euler", frame=FRAMES)

# ------------------------------------------------------------------ aerial perspective over the city
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
haze = bpy.context.object
haze.name = "Haze"
haze.scale = (700, 420, 160)
bpy.ops.object.transform_apply(scale=True)
haze.location = (-20, SHORE_Y + 110, 80)
m_haze = bpy.data.materials.new("Haze")
m_haze.use_nodes = True
hz_nt = m_haze.node_tree
hz_nt.nodes.clear()
pv = hz_nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.0007
pv.inputs["Color"].default_value = (0.85, 0.6, 0.95, 1)
hzo = hz_nt.nodes.new("ShaderNodeOutputMaterial")
hz_nt.links.new(pv.outputs[0], hzo.inputs["Volume"])
haze.data.materials.append(m_haze)

# ------------------------------------------------------------------ camera: skim the water beside the boat, then turn to the phone
cam = link(bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")))
sc.camera = cam
cam.data.clip_end = 3000
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 4.0
tgt = link(bpy.data.objects.new("Target", None))
tr = cam.constraints.new("TRACK_TO")
tr.target = tgt
tr.track_axis = "TRACK_NEGATIVE_Z"
tr.up_axis = "UP_Y"
focus = link(bpy.data.objects.new("Focus", None))
cam.data.dof.focus_object = focus
SHOTS = [  # frame, camera, look-at, lens, focus
    (1, (-48, -22, 4.5), (-30, 300, 45), 26, (-60, 34, 1)),
    (60, (-34, 2, 2.0), (-28, 60, 10), 30, (-34, 20, 1)),
    (100, (-10, 3, 1.8), (-4, 70, 8), 30, (-10, 19, 1)),
    (140, (4, 10, 2.6), PHONE + Vector((0, 6, 1.2)), 32, PHONE),
    (FRAMES, (8.6, 15.0, 3.2), PHONE + Vector((-0.8, 0, 0.1)), 40, PHONE),
]
for f, cl, tl, lens, fo in SHOTS:
    cam.location = cl
    tgt.location = tl
    focus.location = fo
    cam.data.lens = lens
    cam.keyframe_insert("location", frame=f)
    tgt.keyframe_insert("location", frame=f)
    focus.keyframe_insert("location", frame=f)
    cam.data.keyframe_insert("lens", frame=f)

# ------------------------------------------------------------------ compositor: soft bloom
try:
    comp = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    sc.compositing_node_group = comp
    rl = comp.nodes.new("CompositorNodeRLayers")
    glare = comp.nodes.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = "High"
    for k, v in (("Threshold", 1.0), ("Strength", 0.45), ("Size", 0.85)):
        glare.inputs[k].default_value = v
    comp.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    go = comp.nodes.new("NodeGroupOutput")
    comp.links.new(rl.outputs["Image"], glare.inputs["Image"])
    comp.links.new(glare.outputs["Image"], go.inputs[0])
except Exception as ex:  # noqa: BLE001
    print("COMP skipped", ex)

# ------------------------------------------------------------------ go
OUT.mkdir(parents=True, exist_ok=True)
if MODE == "preview":
    sc.render.image_settings.file_format = "PNG"
    sc.render.resolution_percentage = int(ARGS[2]) if len(ARGS) > 2 else 50
    for f in (int(v) for v in ARGS[1].split(",")):
        sc.frame_set(f)
        sc.render.filepath = str(OUT / f"preview_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    print("PREVIEW done")
elif MODE == "save":
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bay.blend"))
else:
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.quality = 64
    if len(ARGS) > 1:
        sc.frame_start, sc.frame_end = (int(v) for v in ARGS[1].split("-"))
    sc.render.filepath = str(OUT / "f_####")
    bpy.ops.render.render(animation=True)
    print("RENDER done")
