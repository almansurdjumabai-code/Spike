"""SpikeClip scroll film: sunset beach, live ocean, palms, neon skyline,
a floating phone playing a clip and a burst of gold coins.

blender -b -P vice_scene.py -- preview 1,60,150   -> stills into OUT/preview_####.png
blender -b -P vice_scene.py -- render             -> all frames into OUT/f_####.webp
"""
import math
import random
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["preview", "1"]
MODE = ARGS[0]
OUT = r"C:\Users\chipl\AppData\Local\Temp\claude\75f48fb559855b2d\e46a1d45-c501-4d1d-93e6-6bdd9a68f475\scratchpad\film"
CLIP = r"C:\Users\chipl\Desktop\clip pulse\clips-studio\frontend\src\renderer\public\media\clips\c5.mp4"
FRAMES = 150
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.fps = 30


def enum_pick(rna_owner, prop, wanted):
    items = [i.identifier for i in rna_owner.bl_rna.properties[prop].enum_items]
    for w in wanted:
        if w in items:
            return w
    return items[0]


def mat(name, color=(1, 1, 1), metal=0.0, rough=0.5, emit=None, strength=0.0, alpha=1.0, coat=0.0):
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


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


# ------------------------------------------------------------------ render
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
ee = sc.eevee
for attr, val in (("taa_render_samples", 48), ("use_raytracing", True), ("use_shadows", True),
                  ("use_volumetric_shadows", True), ("volumetric_tile_size", "8"), ("use_fast_gi", True)):
    try:
        setattr(ee, attr, val)
    except (AttributeError, TypeError):
        pass
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = enum_pick(sc.view_settings, "look", ["AgX - Punchy", "Punchy", "None"])
except TypeError:
    pass
sc.view_settings.exposure = 0.0

# ------------------------------------------------------------------ world: physical sunset sky + haze
SUN_EL = math.radians(4.0)
sun_dir = Vector((-0.28, 1.0, 0)).normalized()
sun_dir.z = math.sin(SUN_EL)
sun_dir.normalize()
w = bpy.data.worlds.new("Sky")
sc.world = w
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
N = nt.nodes.new
L = nt.links.new
tc = N("ShaderNodeTexCoord")
sep = N("ShaderNodeSeparateXYZ")
L(tc.outputs["Generated"], sep.inputs[0])
ramp = N("ShaderNodeValToRGB")  # vertical dusk gradient, sampled by view height
cr = ramp.color_ramp
cr.interpolation = "B_SPLINE"
stops = [(0.0, (0.02, 0.01, 0.05)), (0.47, (0.06, 0.02, 0.08)), (0.5, (1.0, 0.42, 0.12)), (0.515, (1.0, 0.25, 0.22)),
         (0.56, (0.62, 0.08, 0.36)), (0.66, (0.16, 0.04, 0.28)), (1.0, (0.012, 0.01, 0.05))]
cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
for pos, col in stops[1:-1]:
    e = cr.elements.new(pos)
    e.color = (*col, 1)
mr = N("ShaderNodeMapRange")  # Generated z is -1..1 for world directions
mr.inputs["From Min"].default_value = -1
mr.inputs["From Max"].default_value = 1
L(sep.outputs["Z"], mr.inputs["Value"])
L(mr.outputs["Result"], ramp.inputs["Fac"])
# Sun: a hot disc plus a wide glow, from the angle to sun_dir.
dot = N("ShaderNodeVectorMath")
dot.operation = "DOT_PRODUCT"
dot.inputs[1].default_value = sun_dir
L(tc.outputs["Generated"], dot.inputs[0])
disc = N("ShaderNodeMapRange")
disc.inputs["From Min"].default_value = 0.9988
disc.inputs["From Max"].default_value = 0.9992
L(dot.outputs["Value"], disc.inputs["Value"])
glow = N("ShaderNodeMath")
glow.operation = "POWER"
glow.inputs[1].default_value = 90
L(dot.outputs["Value"], glow.inputs[0])
gsum = N("ShaderNodeMath")
gsum.operation = "MULTIPLY_ADD"
gsum.inputs[1].default_value = 0.9
L(glow.outputs[0], gsum.inputs[0])
L(disc.outputs["Result"], gsum.inputs[2])
sunc = N("ShaderNodeMix")
sunc.data_type = "RGBA"
sunc.blend_type = "ADD"
sunc.inputs["Factor"].default_value = 1
L(ramp.outputs["Color"], sunc.inputs["A"])
sunscale = N("ShaderNodeMix")
sunscale.data_type = "RGBA"
sunscale.blend_type = "MULTIPLY"
sunscale.inputs["Factor"].default_value = 1
sunscale.inputs["A"].default_value = (9.0, 4.2, 1.4, 1)
L(gsum.outputs[0], sunscale.inputs["B"])
L(sunscale.outputs["Result"], sunc.inputs["B"])
bg = N("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
out = N("ShaderNodeOutputWorld")
L(sunc.outputs["Result"], bg.inputs[0])
L(bg.outputs[0], out.inputs["Surface"])

sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy = 2.2
sun.data.color = (1.0, 0.58, 0.32)
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (-sun_dir).to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ ocean
bpy.ops.mesh.primitive_plane_add(size=2, location=(-150, 40, 0))
ocean = bpy.context.object
ocean.name = "Ocean"
om = ocean.modifiers.new("Ocean", "OCEAN")
om.resolution = 12
om.spatial_size = 60
om.repeat_x, om.repeat_y = 6, 5
om.wave_scale = 0.9
om.choppiness = 1.1
om.wind_velocity = 9
om.use_normals = True
om.use_foam = True
om.foam_layer_name = "foam"
om.time = 1.0
om.keyframe_insert("time", frame=1)
om.time = 1.0 + FRAMES / 30 * 0.9
om.keyframe_insert("time", frame=FRAMES)
for fc in ocean.animation_data.action.fcurves if hasattr(ocean.animation_data.action, "fcurves") else []:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
m_water, b = mat("Water", (0.02, 0.05, 0.09), rough=0.04)
b.inputs["IOR"].default_value = 1.33
b.inputs["Transmission Weight"].default_value = 0.0
attr = m_water.node_tree.nodes.new("ShaderNodeAttribute")
attr.attribute_name = "foam"
mix = m_water.node_tree.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.inputs["A"].default_value = (0.02, 0.05, 0.09, 1)
mix.inputs["B"].default_value = (0.9, 0.8, 0.75, 1)
m_water.node_tree.links.new(attr.outputs["Fac"], mix.inputs["Factor"])
m_water.node_tree.links.new(mix.outputs["Result"], b.inputs["Base Color"])
ocean.data.materials.append(m_water)
smooth(ocean)

# ------------------------------------------------------------------ beach (gentle dune, rippled sand)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=140, size=1, location=(0, 0, 0))
beach = bpy.context.object
beach.name = "Beach"
beach.scale = (90, 44, 1)
bpy.ops.object.transform_apply(scale=True)
for v in beach.data.vertices:
    x, y = v.co.x, v.co.y
    shore = 15 + 3.5 * math.sin(x * 0.11) + 1.5 * math.sin(x * 0.37)  # wavy waterline
    t = max(0.0, min(1.0, (shore - y) / 22))  # 0 at shore, 1 inland
    v.co.z = -0.35 + t * 1.3 + 0.12 * math.sin(x * 0.9 + y * 0.4) * t + 0.05 * math.sin(x * 3.1) * t
smooth(beach)
m_sand, b = mat("Sand", (0.62, 0.42, 0.30), rough=0.9)
nn = m_sand.node_tree
noise = nn.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 140
bump = nn.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.35
nn.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nn.links.new(bump.outputs["Normal"], b.inputs["Normal"])
wet = nn.nodes.new("ShaderNodeTexCoord")
sep = nn.nodes.new("ShaderNodeSeparateXYZ")
nn.links.new(wet.outputs["Object"], sep.inputs[0])
ramp = nn.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (0.9, 0.9, 0.9, 1)
mr = nn.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.3
mr.inputs["From Max"].default_value = 0.25
nn.links.new(sep.outputs["Z"], mr.inputs["Value"])
nn.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nn.links.new(ramp.outputs["Color"], b.inputs["Roughness"])  # wet sand near the water is glossy
beach.data.materials.append(m_sand)


def ground_z(x, y):
    shore = 15 + 3.5 * math.sin(x * 0.11) + 1.5 * math.sin(x * 0.37)
    t = max(0.0, min(1.0, (shore - y) / 22))
    return -0.35 + t * 1.3


# ------------------------------------------------------------------ palms
m_trunk, b = mat("Trunk", (0.07, 0.045, 0.035), rough=0.85)
tn = m_trunk.node_tree
wave = tn.nodes.new("ShaderNodeTexWave")
wave.wave_type = "RINGS" if False else "BANDS"
wave.bands_direction = "Z"
wave.inputs["Scale"].default_value = 18
wave.inputs["Distortion"].default_value = 3
bp = tn.nodes.new("ShaderNodeBump")
bp.inputs["Strength"].default_value = 0.6
tn.links.new(wave.outputs["Fac"], bp.inputs["Height"])
tn.links.new(bp.outputs["Normal"], b.inputs["Normal"])
m_leaf, b = mat("Leaf", (0.05, 0.16, 0.06), rough=0.55)
b.inputs["Subsurface Weight"].default_value = 0.25
b.inputs["Subsurface Radius"].default_value = (0.2, 0.6, 0.1)
m_leaf.use_backface_culling = False


def frond(length, droop, width):
    """One palm leaf: a drooping spine with dozens of thin leaflets."""
    verts, faces = [], []
    segs = 14
    for i in range(segs + 1):
        t = i / segs
        x = t * length
        z = -droop * t * t * length
        spine = Vector((x, 0, z))
        half = width * math.sin(math.pi * min(1, t * 1.15)) * (1 - 0.3 * t)
        for side in (-1, 1):
            tip = spine + Vector((0.18 * length * 0.1, side * half, -half * 0.55))
            base = len(verts)
            verts += [spine, spine + Vector((length / segs * 0.9, 0, -droop * 0.02)), tip]
            faces.append((base, base + 1, base + 2))
    me = bpy.data.meshes.new("frond")
    me.from_pydata(verts, [], faces)
    me.materials.append(m_leaf)
    return me


FRONDS = [frond(3.6 + random.random(), 0.32 + random.random() * 0.15, 0.62) for _ in range(5)]


def palm(x, y, h, lean, sway_phase):
    z0 = ground_z(x, y)
    curve = bpy.data.curves.new("trunk", "CURVE")
    curve.dimensions = "3D"
    sp = curve.splines.new("BEZIER")
    sp.bezier_points.add(2)
    pts = [Vector((0, 0, 0)), Vector((lean * 0.35, 0, h * 0.5)), Vector((lean, 0, h))]
    for bpnt, co in zip(sp.bezier_points, pts):
        bpnt.co = co
        bpnt.handle_left_type = bpnt.handle_right_type = "AUTO"
    curve.bevel_depth = 0.22
    curve.bevel_resolution = 4
    curve.resolution_u = 24
    curve.use_fill_caps = True
    sp.bezier_points[0].radius = 1.4
    sp.bezier_points[1].radius = 1.0
    sp.bezier_points[2].radius = 0.75
    trunk = link(bpy.data.objects.new("Palm", curve))
    trunk.data.materials.append(m_trunk)
    trunk.location = (x, y, z0 - 0.2)
    trunk.rotation_euler.z = random.random() * math.tau
    crown = link(bpy.data.objects.new("Crown", None))
    crown.parent = trunk
    crown.location = (lean, 0, h)
    n = 14
    for i in range(n):
        f = link(bpy.data.objects.new("Frond", random.choice(FRONDS)))
        f.parent = crown
        a = i / n * math.tau + random.random() * 0.3
        up = random.uniform(-0.15, 0.45) if i % 2 else random.uniform(0.2, 0.6)
        f.rotation_euler = (0, -up, a)
        f.scale = (random.uniform(0.8, 1.15),) * 3
    # Wind: the crown sways on a slow loop.
    for fr in range(1, FRAMES + 1, 10):
        crown.rotation_euler = (0.06 * math.sin(fr * 0.11 + sway_phase), 0.05 * math.cos(fr * 0.09 + sway_phase), 0)
        crown.keyframe_insert("rotation_euler", frame=fr)
    return trunk


for (x, y, h, lean) in [(-7.5, 7, 9, 1.6), (-11, 1, 11, 2.2), (-4.2, -3, 7.5, -0.9), (8.5, 6, 10, -1.8),
                        (12, -1, 8.5, -1.2), (11.5, -9, 6.5, 0.8), (-16, 9, 12, 1.0), (17, 10, 11, -0.7),
                        (-24, 12, 9, 1.3), (25, 13, 10, -1.5)]:
    palm(x, y, h, lean, random.random() * 6)

# ------------------------------------------------------------------ neon skyline across the bay
m_tower, _ = mat("Tower", (0.012, 0.01, 0.02), rough=0.35, metal=0.2)
m_win_p, _ = mat("WinPink", (0, 0, 0), emit=(1.0, 0.25, 0.6), strength=14)
m_win_c, _ = mat("WinCyan", (0, 0, 0), emit=(0.2, 0.9, 1.0), strength=12)
m_win_w, _ = mat("WinWarm", (0, 0, 0), emit=(1.0, 0.75, 0.4), strength=7)
for side in (-1, 1):
    for i in range(26):
        x = side * (34 + i * 3.4 + random.uniform(-1, 1))
        y = 150 + random.uniform(-15, 25)
        hgt = random.uniform(8, 42) * (1.25 if i < 6 else 1)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, hgt / 2 - 0.5))
        t = bpy.context.object
        t.scale = (random.uniform(2.2, 4.5), random.uniform(2.2, 4.5), hgt)
        t.data.materials.append(m_tower)
        # Rows of lit windows as thin emissive strips on the face toward us.
        for r in range(int(hgt // 2.2)):
            if random.random() < 0.45:
                continue
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y - t.scale.y / 2 - 0.02, 1.2 + r * 2.2))
            s = bpy.context.object
            s.rotation_euler.x = math.pi / 2
            s.scale = (t.scale.x * random.uniform(0.3, 0.9), 0.35, 1)
            s.data.materials.append(random.choice([m_win_p, m_win_c, m_win_w, m_win_w]))
        if random.random() < 0.35:  # neon crown on the roofline
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - t.scale.y / 2, hgt - 0.6))
            c = bpy.context.object
            c.scale = (t.scale.x, 0.12, 0.25)
            c.data.materials.append(random.choice([m_win_p, m_win_c]))

# ------------------------------------------------------------------ neon sign on the beach
txt = bpy.data.curves.new("Sign", "FONT")
txt.body = "SPIKECLIP"
txt.align_x = "CENTER"
txt.extrude = 0.06
txt.bevel_depth = 0.015
sign = link(bpy.data.objects.new("Sign", txt))
sign.location = (-6.5, 12, 3.6)
sign.rotation_euler = (math.pi / 2, 0, math.radians(14))
sign.scale = (1.15,) * 3
m_neon, _ = mat("Neon", (0, 0, 0), emit=(1.0, 0.22, 0.6), strength=22)
txt.materials.append(m_neon)
bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=3.6, location=(-6.5, 12.05, ground_z(-6.5, 12) + 1.6))
bpy.context.object.data.materials.append(m_trunk)
neon_l = link(bpy.data.objects.new("SignGlow", bpy.data.lights.new("SignGlow", "POINT")))
neon_l.data.energy = 900
neon_l.data.color = (1.0, 0.25, 0.6)
neon_l.location = (-6.5, 11.2, 3.4)

# ------------------------------------------------------------------ hero phone with the clip playing
PHONE = Vector((0, 6.5, 2.4))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
phone = bpy.context.object
phone.name = "Phone"
phone.scale = (0.78, 0.09, 1.6)
bpy.ops.object.transform_apply(scale=True)
bev = phone.modifiers.new("Bevel", "BEVEL")
bev.width = 0.11
bev.segments = 10
m_body, _ = mat("Body", (0.02, 0.02, 0.025), metal=0.9, rough=0.18, coat=1.0)
phone.data.materials.append(m_body)
smooth(phone)
# Neon edge band.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
band = bpy.context.object
band.scale = (0.8, 0.06, 1.62)
bpy.ops.object.transform_apply(scale=True)
bb = band.modifiers.new("Bevel", "BEVEL")
bb.width = 0.115
bb.segments = 10
m_band, _ = mat("Band", (0, 0, 0), emit=(1.0, 0.3, 0.65), strength=9)
band.data.materials.append(m_band)
band.parent = phone
band.location = (0, 0, 0)
# Screen.
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
screen = bpy.context.object
screen.rotation_euler.x = math.pi / 2
screen.scale = (0.7, 1.5, 1)
m_scr = bpy.data.materials.new("Screen")
m_scr.use_nodes = True
sn = m_scr.node_tree
sn.nodes.clear()
img = bpy.data.images.load(CLIP)
img.source = "MOVIE"
tex = sn.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.image_user.frame_duration = 400
tex.image_user.frame_start = 1
tex.image_user.frame_offset = 60
tex.image_user.use_auto_refresh = True
tex.image_user.use_cyclic = True
tex.extension = "CLIP"
em = sn.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 1.5
gl = sn.nodes.new("ShaderNodeBsdfGlossy")
gl.inputs["Roughness"].default_value = 0.02
add = sn.nodes.new("ShaderNodeMixShader")  # mostly the picture, a hint of glass
add.inputs["Fac"].default_value = 0.05
o = sn.nodes.new("ShaderNodeOutputMaterial")
sn.links.new(tex.outputs["Color"], em.inputs["Color"])
sn.links.new(em.outputs[0], add.inputs[1])
sn.links.new(gl.outputs[0], add.inputs[2])
sn.links.new(add.outputs[0], o.inputs["Surface"])
screen.data.materials.append(m_scr)
# The clip is 9:16; the screen is 0.7 x 1.5, close enough with a slight crop.
screen.parent = phone
screen.location = (0, -0.05, 0)

phone.rotation_mode = "XYZ"
for fr, rz, rx, dz in [(1, math.radians(-38), math.radians(-6), 0.0), (60, math.radians(-18), math.radians(4), 0.25),
                       (110, math.radians(-6), math.radians(-2), 0.1), (FRAMES, 0.0, 0.0, 0.0)]:
    phone.rotation_euler = (rx, 0, rz)
    phone.location = PHONE + Vector((0, 0, dz))
    phone.keyframe_insert("rotation_euler", frame=fr)
    phone.keyframe_insert("location", frame=fr)

# Pink rim light behind the phone, cyan kicker from the side.
for name, loc, col, power in [("Rim", (0.6, 8.5, 3.6), (1.0, 0.25, 0.6), 380), ("Kick", (-3, 4.5, 2.2), (0.3, 0.8, 1.0), 250),
                              ("Key", (2.5, 3.5, 4.0), (1.0, 0.78, 0.5), 260)]:
    L = link(bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA")))
    L.data.energy = power
    L.data.color = col
    L.data.size = 2.5
    L.location = loc
    L.rotation_euler = (PHONE - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ gold coins burst out of the phone
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.16, depth=0.03)
coin_proto = bpy.context.object
cb = coin_proto.modifiers.new("Bevel", "BEVEL")
cb.width = 0.012
cb.segments = 3
m_gold, b = mat("Gold", (1.0, 0.7, 0.2), metal=1.0, rough=0.28, emit=(1.0, 0.6, 0.15), strength=0.35)
coin_proto.data.materials.append(m_gold)
try:
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
except Exception as e:  # noqa: BLE001
    print("smooth-by-angle", e)
coin_proto.hide_render = True
coin_proto.hide_viewport = True
for i in range(46):
    c = link(bpy.data.objects.new("Coin", coin_proto.data))
    a = random.random() * math.tau
    el = random.uniform(-0.6, 1.0)
    dist = random.uniform(1.2, 3.4)
    end = PHONE + Vector((math.cos(a) * dist * 1.2, abs(math.sin(a)) * dist * 0.7 + 0.2, el * dist * 0.55 + 0.3))
    start_f = 52 + int(random.random() * 22)
    spin = Vector((random.uniform(4, 9), random.uniform(2, 6), random.uniform(1, 4)))
    c.scale = (0.001,) * 3
    c.location = PHONE
    c.keyframe_insert("scale", frame=start_f)
    c.keyframe_insert("location", frame=start_f)
    c.scale = (1,) * 3
    c.location = end
    c.keyframe_insert("scale", frame=start_f + 18)
    c.keyframe_insert("location", frame=start_f + 18)
    c.location = end + Vector((0, 0, -0.5 - random.random() * 0.6))  # slow drift after the pop
    c.keyframe_insert("location", frame=FRAMES)
    c.rotation_euler = (0, 0, 0)
    c.keyframe_insert("rotation_euler", frame=start_f)
    c.rotation_euler = tuple(spin)
    c.keyframe_insert("rotation_euler", frame=FRAMES)

# ------------------------------------------------------------------ camera: aerial over the bay -> beach -> the phone
cam = link(bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")))
sc.camera = cam
cam.data.lens = 32
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.2
target = link(bpy.data.objects.new("Target", None))
tr = cam.constraints.new("TRACK_TO")
tr.target = target
tr.track_axis = "TRACK_NEGATIVE_Z"
tr.up_axis = "UP_Y"
cam.data.dof.focus_object = phone
KEYS = [
    (1, (-3, -46, 17), (0, 60, 5), 26),
    (45, (7, -20, 6.5), (0, 20, 3), 30),
    (85, (4.0, -4, 3.2), PHONE + Vector((-0.3, 0, 0.3)), 34),
    (FRAMES, (-0.75, 2.75, 2.5), PHONE + Vector((-0.72, 0, 0.05)), 40),
]
for fr, cl, tl, lens in KEYS:
    cam.location = cl
    target.location = tl
    cam.data.lens = lens
    cam.keyframe_insert("location", frame=fr)
    target.keyframe_insert("location", frame=fr)
    cam.data.keyframe_insert("lens", frame=fr)

# ------------------------------------------------------------------ bloom + vignette in the compositor (Blender 5 node-group API)
try:
    comp = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    sc.compositing_node_group = comp
    rl = comp.nodes.new("CompositorNodeRLayers")
    glare = comp.nodes.new("CompositorNodeGlare")
    for sock, val in (("Type", "Bloom"), ("Quality", "High")):
        try:
            glare.inputs[sock].default_value = val
        except Exception as e:  # noqa: BLE001
            print("glare", sock, e)
    for name, val in (("Threshold", 1.2), ("Strength", 0.35), ("Size", 0.8)):
        if name in glare.inputs:
            glare.inputs[name].default_value = val
    comp.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    go = comp.nodes.new("NodeGroupOutput")
    comp.links.new(rl.outputs["Image"], glare.inputs["Image"])
    comp.links.new(glare.outputs["Image"], go.inputs[0])
    print("COMPOSITOR ok")
except Exception as e:  # noqa: BLE001
    print("COMPOSITOR skipped:", e)

# ------------------------------------------------------------------ go
if MODE == "preview":
    frames = [int(f) for f in ARGS[1].split(",")]
    sc.render.image_settings.file_format = "PNG"
    sc.render.resolution_percentage = int(ARGS[2]) if len(ARGS) > 2 else 60
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = f"{OUT}/preview_{f:04d}.png"
        bpy.ops.render.render(write_still=True)
    print("PREVIEW done")
elif MODE == "save":
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/scene.blend")
else:
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.quality = 62
    if len(ARGS) > 1:
        sc.frame_start, sc.frame_end = (int(v) for v in ARGS[1].split("-"))
    sc.render.filepath = f"{OUT}/f_####"
    bpy.ops.render.render(animation=True)
    print("RENDER done")
