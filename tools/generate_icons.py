import argparse
import math
import sys
from pathlib import Path

from panda3d.core import loadPrcFileData

PROJECT_ROOT = Path(__file__).resolve().parent.parent

loadPrcFileData("", "framebuffer-alpha #t")

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import (
    Filename,
    LColor,
    PNMImage,
)

sys.path.insert(0, str(PROJECT_ROOT))

from src.config import panda_path
from src.maps.model_loader import load_model_or_actor

MODELS_DIR = PROJECT_ROOT / "assets" / "models"
OUT_DIR = PROJECT_ROOT / "assets" / "icons"
ICON_SIZE = 128
FIT_MARGIN = 1.15


class IconRenderer(ShowBase):
    def __init__(self, icon_size):
        loadPrcFileData("", f"win-size {icon_size} {icon_size}")
        super().__init__(windowType="offscreen")
        self.icon_size = icon_size

        region = self.win.getDisplayRegion(0)
        region.setClearColorActive(True)
        region.setClearColor(LColor(0, 0, 0, 0))

    def fit_distance(self, node):
        """Расстояние камеры, чтобы модель целиком попала в кадр | Camera distance to fit the model"""
        lmin, lmax = node.getTightBounds(self.render)
        size = max((lmax - lmin).x, (lmax - lmin).y, (lmax - lmin).z)
        vfov = self.cam.node().getLens().getFov()[1]
        distance = (size * 0.5) / math.tan(math.radians(vfov) / 2) * FIT_MARGIN
        center = (lmin + lmax) * 0.5
        return distance, center

    def render_icon(self, model_path, out_path, heading=0, pitch=0):
        """Рендерит фронтальный вид модели и сохраняет PNG | Render model front view and save PNG"""
        node = load_model_or_actor(self.loader, panda_path(model_path))
        node.reparentTo(self.render)
        node.setH(heading)
        try:
            self.pose_actor(node)

            distance, center = self.fit_distance(node)
            node.setPos(node.getPos(self.render) - center)

            self.camera.setPos(0, -distance, 0)
            self.camera.setHpr(0, pitch, 0)
            self.camera.lookAt(0, 0, 0)

            for _ in range(3):
                self.graphicsEngine.renderFrame()

            img = PNMImage()
            self.win.getScreenshot(img)
            self.unpremultiply(img)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.write(Filename.from_os_specific(str(out_path)))
            return self.coverage(img), (img.getXSize(), img.getYSize())
        finally:
            if isinstance(node, Actor):
                node.cleanup()
            else:
                node.removeNode()

    def pose_actor(self, node):
        """Ставит актёра в позу, иначе он не рендерится | Pose the actor, otherwise it does not render"""
        if not isinstance(node, Actor):
            return
        anims = node.getAnimNames()
        preferred = "Idle" if "Idle" in anims else (anims[0] if anims else None)
        if preferred:
            node.pose(preferred, 0)

    def unpremultiply(self, img):
        """Переводит цвет из premultiplied alpha в обычный | Convert premultiplied alpha to straight alpha"""
        for y in range(img.getYSize()):
            for x in range(img.getXSize()):
                a = img.getAlpha(x, y)
                if 0 < a < 1:
                    img.setXel(x, y, img.getRed(x, y) / a, img.getGreen(x, y) / a, img.getBlue(x, y) / a)

    def coverage(self, img):
        """Доля непрозрачных пикселей | Fraction of opaque pixels"""
        covered = 0
        total = img.getXSize() * img.getYSize()
        for y in range(img.getYSize()):
            for x in range(img.getXSize()):
                if img.getAlpha(x, y) > 0.01:
                    covered += 1
        return covered / total


def main():
    parser = argparse.ArgumentParser(description="Генерация иконок из фронтального вида 3D-моделей")
    parser.add_argument("--models", nargs="*", help="Имена моделей без .bam (по умолчанию все из assets/models)")
    parser.add_argument("--out", default=str(OUT_DIR), help="Папка для иконок")
    parser.add_argument("--size", type=int, default=ICON_SIZE, help="Размер иконки в пикселях")
    parser.add_argument("--heading", type=float, default=0, help="Поворот модели вокруг Y в градусах")
    parser.add_argument("--pitch", type=float, default=0, help="Наклон камеры в градусах")
    parser.add_argument("--name", default=None, help="Имя выходного файла без .png (для одного --models) | Output file name without .png (for a single --models)")
    args = parser.parse_args()

    if args.models:
        models = [MODELS_DIR / f"{name}.bam" for name in args.models]
    else:
        models = sorted(MODELS_DIR.glob("*.bam"))

    out_dir = Path(args.out)
    renderer = IconRenderer(args.size)

    try:
        for model_path in models:
            if not model_path.exists():
                print(f"[skip] модель не найдена: {model_path.name}")
                continue
            out_path = out_dir / f"{args.name if args.name else model_path.stem}.png"
            coverage, (w, h) = renderer.render_icon(model_path, out_path, args.heading, args.pitch)
            status = "ok" if coverage > 0.01 else "WARN: пустая иконка"
            print(f"[{status}] {model_path.name} -> {out_path} ({w}x{h}, покрытие {coverage:.0%})")
    finally:
        renderer.destroy()

    print("Готово.")


if __name__ == "__main__":
    main()