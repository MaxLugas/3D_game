import bpy
import os
import sys

SRC = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/models_glb"
DST = "/home/lugovskiy_maksim/PycharmProjects/ursina_test/tools/model_converted"
LOD_LEVELS = [
    ("LOD0", 1.0),
    ("LOD1", 0.5),
    ("LOD2", 0.25),
]

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


def duplicate_mesh_obj(src_obj, new_name):
    new_mesh = src_obj.data.copy()
    new_mesh.name = new_name + "_mesh"
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
    armature = next((obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE'), None)

    if not source_mesh_objects:
        print(f"  WARNING: no mesh objects found in {filename}")
        return

    for src_obj in source_mesh_objects:
        src_obj.select_set(False)

    for lod_name, ratio in LOD_LEVELS:
        print(f"  {lod_name}: ratio={ratio}", end="", flush=True)

        if ratio >= 1.0:
            for src_obj in source_mesh_objects:
                new_obj = duplicate_mesh_obj(src_obj, f"{base_name}_{lod_name}")
                new_obj.select_set(False)
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
                print(f" [{len(new_obj.data.polygons)} polys]", end="", flush=True)

        print()

    out_path = os.path.join(DST, filename)
    bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')

    total_polys = sum(len(obj.data.polygons) for obj in bpy.context.scene.objects if obj.type == 'MESH')
    return base_name, total_polys


glb_files = sorted([f for f in os.listdir(SRC) if f.endswith('.glb')])
results = []

for f in glb_files:
    print(f"\n=== {f} ===", flush=True)
    try:
        result = process_file(f)
        if result:
            results.append(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append((f.replace(".glb", ""), 0))

print("\n\n=== SUMMARY ===")
for name, total in results:
    print(f"  {name}: {total} total polys in LOD file")
print(f"\nAll files saved to: {DST}")
