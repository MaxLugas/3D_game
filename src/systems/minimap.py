from pathlib import Path
import math
import subprocess
import sys

from panda3d.core import CardMaker, TransparencyAttrib, LVector2

from src.config import (
    MINIMAP_SIZE,
    MINIMAP_MARGIN,
    MINIMAP_VIEW_RADIUS,
    MINIMAP_BG_ALPHA,
    MINIMAP_PLAYER_MARKER_SCALE,
    MINIMAP_NPC_MARKER_SCALE,
    MINIMAP_OBJECT_MARKER_SCALE,
    ICONS_DIR,
    GENERATOR_TOOL,
    PROJECT_ROOT,
    PLAYER_MODEL,
    PLAYER_ICON,
)
from src.core.npc_config import DROID_MODEL


def icon_path(model):
    return ICONS_DIR / f"{Path(model).stem}.png"


def needed_models(objects, droids, pickups):
    """Модели, для которых нужны иконки | Models that need icons"""
    models = {name for name, _ in objects}
    if droids:
        models.add(DROID_MODEL)
    for pickup in pickups:
        models.add(pickup.model_name)
    return models


def run_icon_generator(models, name=None):
    """Запускает генератор иконок | Run the icon generator"""
    args = [sys.executable, str(GENERATOR_TOOL), "--out", str(ICONS_DIR),
            "--models", *(Path(m).stem for m in models)]
    if name:
        args += ["--name", name]
    try:
        subprocess.run(args, cwd=str(PROJECT_ROOT), check=False, timeout=180)
    except Exception:
        pass


def ensure_model_icons(models):
    """Генерирует недостающие иконки моделей | Generate missing model icons"""
    missing = sorted(m for m in models if not icon_path(m).exists())
    if missing:
        run_icon_generator(missing)


def ensure_player_icon():
    """Генерирует player.png из модели игрока, если её нет | Generate player.png from player model if missing"""
    if (ICONS_DIR / PLAYER_ICON).exists():
        return
    run_icon_generator([PLAYER_MODEL], name=Path(PLAYER_ICON).stem)


def load_icon_textures(loader, models):
    """Загружает текстуры иконок моделей | Load model icon textures"""
    icons = {}
    for model in models:
        path = icon_path(model)
        if path.exists():
            icons[model] = loader.loadTexture(str(path))
    return icons


class Minimap:
    def __init__(self, render, aspect2d, loader, player_root, objects, droids, pickups):
        """
        render: корневой узел сцены | scene root node
        aspect2d: UI-узел для HUD-элементов | UI node for HUD elements
        loader: загрузчик текстур | texture loader
        player_root: корневой узел игрока | player root node
        objects: статичные объекты (name, node) | static objects (name, node)
        droids: список дроидов | list of droids
        pickups: список предметов подбора | list of pickups
        """
        self.render = render
        self.aspect2d = aspect2d
        self.loader = loader
        self.player_root = player_root
        self.objects = objects
        self.droids = droids
        self.pickups = pickups
        self.minimap_size = MINIMAP_SIZE

        self.model_icons = self.load_icons()

        self.root = aspect2d.attachNewNode("minimap")
        self.background = self.create_background()
        self.markers = []

        self.create_markers()
        self.set_visible(False)

    def load_icons(self):
        """Генерирует недостающие и загружает иконки из моделей | Generate missing and load model icons"""
        models = needed_models(self.objects, self.droids, self.pickups)
        ensure_model_icons(models)
        ensure_player_icon()
        icons = load_icon_textures(self.loader, models)
        player_path = ICONS_DIR / PLAYER_ICON
        if player_path.exists():
            icons[PLAYER_ICON] = self.loader.loadTexture(str(player_path))
        return icons

    def create_background(self):
        card_maker = CardMaker("minimap_bg")
        card_maker.setFrame(-0.5, 0.5, -0.5, 0.5)
        background = self.root.attachNewNode(card_maker.generate())
        background.setScale(self.minimap_size)
        background.setColor(0, 0, 0, MINIMAP_BG_ALPHA)
        background.setTransparency(TransparencyAttrib.MAlpha)
        background.setBin("fixed", 100)
        background.setDepthTest(False)
        background.setDepthWrite(False)
        self.background = background
        self.update_background_position()
        return background

    def update_background_position(self):
        """Позиционирует фон относительно текущего аспекта окна | Position background relative to current window aspect"""
        scale_x = self.aspect2d.getSx()
        self.background.setPos(
            -1 / scale_x + MINIMAP_MARGIN + self.minimap_size / 2, 0,
            1 - MINIMAP_MARGIN - self.minimap_size / 2,
        )

    def create_marker(self, name, scale, texture=None, color=None):
        card_maker = CardMaker(name)
        card_maker.setFrame(-0.5, 0.5, -0.5, 0.5)
        marker = self.root.attachNewNode(card_maker.generate())
        marker.setScale(scale)
        if texture is not None:
            marker.setTexture(texture)
        if color is not None:
            marker.setColor(*color)
        marker.setTransparency(TransparencyAttrib.MAlpha)
        marker.setBin("fixed", 100)
        marker.setDepthTest(False)
        marker.setDepthWrite(False)
        return marker

    def create_markers(self):
        player_icon = self.model_icons.get(PLAYER_ICON)
        self.player_marker = self.create_marker(
            "player_marker", MINIMAP_PLAYER_MARKER_SCALE,
            texture=player_icon, color=(0, 1, 0, 1) if player_icon is None else None,
        )
        self.markers.append((self.player_root, self.player_marker))

        for name, node in self.objects:
            icon = self.model_icons.get(name)
            marker = self.create_marker(
                f"obj_{id(node)}", MINIMAP_OBJECT_MARKER_SCALE,
                texture=icon,
            )
            self.markers.append((node, marker))

        npc_icon = self.model_icons.get(DROID_MODEL)
        for droid in self.droids:
            marker = self.create_marker(
                f"npc_{id(droid)}", MINIMAP_NPC_MARKER_SCALE,
                texture=npc_icon, color=(1, 0, 0, 1) if npc_icon is None else None,
            )
            self.markers.append((droid, marker))

        for pickup in self.pickups:
            pickup_icon = self.model_icons.get(pickup.model_name)
            marker = self.create_marker(
                f"pickup_{id(pickup)}", MINIMAP_OBJECT_MARKER_SCALE,
                texture=pickup_icon, color=(1, 1, 0, 1) if pickup_icon is None else None,
            )
            self.markers.append((pickup, marker))

    def get_source_position(self, source):
        if hasattr(source, "get_position"):
            return source.get_position()
        if hasattr(source, "actor"):
            return source.actor.getPos(self.render)
        return source.getPos(self.render)

    def is_source_dead(self, source):
        if hasattr(source, "is_alive"):
            return not source.is_alive()
        if hasattr(source, "is_available"):
            return not source.is_available()
        return source.isEmpty()

    def world_to_minimap(self, pos, player_pos):
        """Преобразует мировые координаты в позицию на миникарте относительно игрока | Convert world coords to minimap position relative to player"""
        rel_x = (pos.x - player_pos.x) / MINIMAP_VIEW_RADIUS
        rel_y = (pos.y - player_pos.y) / MINIMAP_VIEW_RADIUS
        half_size = self.minimap_size / 2
        return LVector2(
            self.background.getX() + rel_x * half_size,
            self.background.getZ() + rel_y * half_size,
        )

    def clamp_to_background(self, marker_pos):
        """Не даёт маркерам выходить за границы фона | Keep markers inside the background bounds"""
        half = self.minimap_size / 2
        return LVector2(
            max(self.background.getX() - half, min(self.background.getX() + half, marker_pos.x)),
            max(self.background.getZ() - half, min(self.background.getZ() + half, marker_pos.y)),
        )

    def set_visible(self, visible):
        if visible:
            self.root.show()
        else:
            self.root.hide()

    def update(self):
        if self.root.isHidden():
            return

        self.update_background_position()

        player_pos = self.player_root.getPos(self.render)

        # Игрок всегда в центре миникарты | Player is always at the center of the minimap
        self.player_marker.setPos(self.background.getX(), 0, self.background.getZ())

        valid_markers = []
        for source, marker in self.markers:
            if source is self.player_root:
                valid_markers.append((source, marker))
                continue

            if self.is_source_dead(source):
                marker.removeNode()
                continue

            try:
                marker_pos = self.world_to_minimap(self.get_source_position(source), player_pos)
                marker_pos = self.clamp_to_background(marker_pos)
            except Exception:
                marker.removeNode()
                continue

            marker.setPos(marker_pos.x, 0, marker_pos.y)
            valid_markers.append((source, marker))

        self.markers = valid_markers
        self.update_player_rotation()

    def update_player_rotation(self):
        """Поворачивает маркер игрока по направлению взгляда | Rotate player marker with look direction"""
        forward = self.player_root.getQuat(self.render).getForward()
        angle = math.degrees(math.atan2(forward.x, forward.y))
        self.player_marker.setR(angle)