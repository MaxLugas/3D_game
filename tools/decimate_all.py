import os

import bpy

SRC = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb"
DST = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb_lowpoly"
RATIO = 0.5

os.makedirs(DST, exist_ok=True)


def fmt(n):
    return f"{n:,}"


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
    return sum(len(obj.data.polygons) for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj.data)


def count_verts():
    return sum(len(obj.data.vertices) for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj.data)


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
    return out_name, orig_polys, orig_verts, new_polys, new_verts, pct


glb_files = sorted([f for f in os.listdir(SRC) if f.endswith('.glb')])
total = len(glb_files)
results = []

for i, f in enumerate(glb_files, 1):
    try:
        result = process_file(f)
    except Exception as e:
        print(f"[{i}/{total}] {f}: ОШИБКА: {e}")
        result = (f.replace('.glb', '_lowpoly.glb'), 0, 0, 0, 0, 0)
    out_name, op, ov, np_, nv, pct = result
    if np_:
        print(f"[{i}/{total}] {f}: {fmt(op)} -> {fmt(np_)} пол. ({pct}% от оригинала)")
    results.append(result)

report_path = os.path.join(DST, "polygon_counts.txt")
with open(report_path, 'w', encoding='utf-8') as fp:
    fp.write(f"Сжатие моделей (ratio={RATIO})\n\n")
    for out_name, op, ov, np_, nv, pct in results:
        if np_:
            fp.write(f"{out_name}: {fmt(op)} -> {fmt(np_)} пол. ({pct}%)\n")
        else:
            fp.write(f"{out_name}: ОШИБКА\n")

print(f"\nГотово. Отчёт: {report_path}")
