import bpy
import os
import sys
from pathlib import Path

SRC = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb"
DST = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb_lowpoly"
RATIO = 0.5

os.makedirs(DST, exist_ok=True)


def clear_scene():
    for block in list(bpy.data.objects):
        bpy.data.objects.remove(block, do_unlink=True)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.armatures):
        bpy.data.armatures.remove(block)
    for block in list(bpy.data.actions):
        bpy.data.actions.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)
    for block in list(bpy.data.textures):
        bpy.data.textures.remove(block)
    for block in list(bpy.data.images):
        bpy.data.images.remove(block)


def count_polys():
    total = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data:
            total += len(obj.data.polygons)
    return total


def count_verts():
    total = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data:
            total += len(obj.data.vertices)
    return total


def process_file(filename):
    clear_scene()

    filepath = os.path.join(SRC, filename)
    bpy.ops.import_scene.gltf(filepath=filepath)

    orig_polys = count_polys()
    orig_verts = count_verts()

    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH':
            continue

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        arm_info = []
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                arm_info.append((mod.name, mod.object))
                obj.modifiers.remove(mod)

        if not obj.modifiers:
            mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
            mod.ratio = RATIO
            mod.use_collapse_triangulate = False
            bpy.ops.object.modifier_apply(modifier="Decimate")

        for name, arm_obj in arm_info:
            new_mod = obj.modifiers.new(name=name, type='ARMATURE')
            new_mod.object = arm_obj

        obj.select_set(False)

    new_polys = count_polys()
    new_verts = count_verts()

    out_name = filename.replace(".glb", "_lowpoly.glb")
    out_path = os.path.join(DST, out_name)
    bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')

    pct = round(new_polys / orig_polys * 100, 1) if orig_polys else 0
    return filename, out_name, orig_polys, orig_verts, new_polys, new_verts, pct


glb_files = sorted([f for f in os.listdir(SRC) if f.endswith('.glb')])
results = []

for f in glb_files:
    print(f"\n--- Processing: {f} ---", flush=True)
    try:
        result = process_file(f)
        results.append(result)
        print(f"  Done: {result[2]} -> {result[4]} polys ({result[6]}%)", flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        results.append((f, f.replace('.glb', '_lowpoly.glb'), 0, 0, 0, 0, 0))

report_path = os.path.join(DST, "polygon_counts.txt")
with open(report_path, 'w', encoding='utf-8') as fp:
    fp.write("=== Polygon Counts: Before and After Decimation (ratio={}) ===\n\n".format(RATIO))
    for orig_name, out_name, op, ov, np, nv, pct in results:
        fp.write(f"Model: {orig_name}\n")
        if op:
            fp.write(f"  Polygons: {op} -> {np} ({pct}%)\n")
            fp.write(f"  Vertices: {ov} -> {nv}\n")
        else:
            fp.write(f"  FAILED\n")
        fp.write(f"  Output:   {out_name}\n\n")

print(f"\n=== ALL DONE. Report saved to {report_path} ===")
for r in results:
    print(f"  {r[0]}: {r[2]} -> {r[4]} ({r[6]}%)")
