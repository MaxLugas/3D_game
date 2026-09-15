import os
import traceback

import bpy

SRC = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb"
DST = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/model_converted"
LOD_LEVELS = [
    ("LOD0", 1.0),
    ("LOD1", 0.5),
    ("LOD2", 0.25),
]

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


def duplicate_mesh_obj(src_obj, new_name):
    new_mesh = src_obj.data.copy()
    new_mesh.name = f"{new_name}_mesh"
    new_obj = src_obj.copy()
    new_obj.data = new_mesh
    new_obj.name = new_name
    bpy.context.collection.objects.link(new_obj)
    return new_obj


def process_file(filename):
    clear_scene()

    filepath = os.path.join(SRC, filename)
    base_name = filename.replace(".glb", "")

    bpy.ops.import_scene.gltf(filepath=filepath)

    source_mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not source_mesh_objects:
        return None

    for src_obj in source_mesh_objects:
        src_obj.select_set(False)

    for lod_name, ratio in LOD_LEVELS:
        if ratio >= 1.0:
            for src_obj in source_mesh_objects:
                duplicate_mesh_obj(src_obj, f"{base_name}_{lod_name}").select_set(False)
        else:
            for src_obj in source_mesh_objects:
                new_obj = duplicate_mesh_obj(src_obj, f"{base_name}_{lod_name}")

                arm_mods = []
                for mod in list(new_obj.modifiers):
                    if mod.type == 'ARMATURE':
                        arm_mods.append((mod.name, mod.object))
                        new_obj.modifiers.remove(mod)

                bpy.context.view_layer.objects.active = new_obj
                new_obj.select_set(True)

                mod = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
                mod.ratio = ratio
                mod.use_collapse_triangulate = False
                bpy.ops.object.modifier_apply(modifier="Decimate")

                for name, arm_obj in arm_mods:
                    new_mod = new_obj.modifiers.new(name=name, type='ARMATURE')
                    new_mod.object = arm_obj

                new_obj.select_set(False)

    out_path = os.path.join(DST, filename)
    bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')

    lod_polys = {}
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        for lod_name in ("LOD0", "LOD1", "LOD2"):
            if obj.name.endswith(f"_{lod_name}"):
                lod_polys[lod_name] = lod_polys.get(lod_name, 0) + len(obj.data.polygons)
    return lod_polys


glb_files = sorted([f for f in os.listdir(SRC) if f.endswith('.glb')])
total = len(glb_files)

for i, f in enumerate(glb_files, 1):
    name = f.replace(".glb", "")
    try:
        lod_polys = process_file(f)
    except Exception:
        print(f"[{i}/{total}] {name}: ОШИБКА")
        traceback.print_exc()
        continue
    if not lod_polys:
        print(f"[{i}/{total}] {name}: нет полигонов, пропущено")
        continue
    parts = " | ".join(f"{lod}: {fmt(lod_polys.get(lod, 0))}" for lod in ("LOD0", "LOD1", "LOD2"))
    print(f"[{i}/{total}] {name}: {parts} пол.")

print(f"\nГотово. Файлы сохранены в: {DST}")
