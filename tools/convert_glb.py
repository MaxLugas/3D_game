import sys
from pathlib import Path

try:
    import panda3d_gltf
except ImportError:
    print("Установи panda3d-gltf: pip install panda3d-gltf")
    sys.exit(1)

from panda3d.core import Filename
from panda3d_gltf import convert_gltf_to_bam


def main():
    if len(sys.argv) < 2:
        print("Использование: python convert_glb.py <файл.glb>")
        '''gltf2bam assets/models/house.glb assets/models/house.bam'''

        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Файл не найден: {src}")
        sys.exit(1)

    dst = src.with_suffix(".bam")
    print(f"Конвертация: {src} -> {dst}")

    convert_gltf_to_bam(Filename(str(src)), Filename(str(dst)), None)
    print("Готово!")


if __name__ == "__main__":
    main()