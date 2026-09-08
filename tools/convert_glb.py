import sys
from pathlib import Path

from gltf import GltfSettings
from gltf._converter import Converter
from gltf.parseutils import parse_gltf_file

from panda3d.core import Filename


def main():
    if len(sys.argv) < 2:
        print("Использование: ./venv/bin/python tools/convert_glb.py tools/models_glb/{name}.glb")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Файл не найден: {src}")
        sys.exit(1)

    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".bam")
    print(f"Конвертация: {src} -> {dst}")

    src_fname = Filename.from_os_specific(str(src))
    src_fname.make_absolute()
    dst_fname = Filename.from_os_specific(str(dst))
    dst_fname.make_absolute()

    converter = Converter(src_fname, settings=GltfSettings())
    gltf_data = parse_gltf_file(src_fname)
    converter.update(gltf_data)
    converter.active_scene.write_bam_file(dst_fname)
    print("Готово!")


if __name__ == "__main__":
    main()