from pathlib import Path
import math
import subprocess
import sys
import threading

from panda3d.core import CardMaker, TransparencyAttrib, LVector2
from direct.task.TaskManagerGlobal import taskMgr

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
    panda_path,
)


def icon_path(model):
    return ICONS_DIR / f"{Path(model).stem}.png"


def needed_models(objects, npc_enemies, pickups):
    """Модели, для которых нужны иконки | Models that need icons"""
    models = {name for name, _ in objects}
    for enemy in npc_enemies:
        models.add(enemy.model_name)
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
            icons[model] = loader.loadTexture(panda_path(path))
    return icons


class Minimap:
    def __init__(self, render, aspect2d, loader, player_root, objects, npc_enemies, pickups):
        """
        render: корневой узел сцены | scene root node
        aspect2d: UI-узел для HUD-элементов | UI node for HUD elements
        loader: загрузчик текстур | texture loader
        player_root: корневой узел игрока | player root node
        objects: статичные объекты (name, node) | static objects (name, node)
        npc_enemies: список дроидов | list of npc_enemies
        pickups: список предметов подбора | list of pickups
        """
        self.render = render
        self.aspect2d = aspect2d
        self.loader = loader
        self.player_root = player_root
        self.objects = objects
        self.npc_enemies = npc_enemies
        self.pickups = pickups
        self.minimap_size = MINIMAP_SIZE

        self.model_icons = {}
        self.marker_meta = {}

        self.root = aspect2d.attachNewNode("minimap")
        self.background = self.create_background()
        self.markers = []

        self.create_markers()
        self.set_visible(False)

        self.start_async_icons()

    def _load_existing_icons(self, models=None):
        """Загружает только готовые иконки | Load only already-generated icons"""
        if models is None:
            models = needed_models(self.objects, self.npc_enemies, self.pickups)
        icons = load_icon_textures(self.loader, models)
        player_path = ICONS_DIR / PLAYER_ICON
        if player_path.exists():
            icons[PLAYER_ICON] = self.loader.loadTexture(panda_path(player_path))
        return icons

    def start_async_icons(self):
        """Генерирует недостающие иконки в фоне, чтобы не блокировать старт игры | Generate missing icons in the background"""
        self._icons_thread = threading.Thread(target=self._generate_icons_daemon, daemon=True)
        self._icons_thread.start()
        taskMgr.doMethodLater(0.1, self._poll_icons, "minimap_icons")

    def _generate_icons_daemon(self):
        try:
            models = needed_models(self.objects, self.npc_enemies, self.pickups)
            ensure_model_icons(models)
            ensure_player_icon()
        except Exception:
            pass

    def _poll_icons(self, task):
        """Ждёт завершения генерации и подгружает текстуры | Wait for generation and load textures"""
        if self._icons_thread.is_alive():
            return task.cont
        self.model_icons = self._load_existing_icons()
        self.apply_marker_icons()
        return task.done

    def apply_marker_icons(self):
        """Обновляет маркеры свежими текстурами | Apply freshly loaded textures to markers"""
        for marker, (icon_key, fallback) in self.marker_meta.items():
            texture = self.model_icons.get(icon_key)
            if texture is not None:
                marker.setTexture(texture)
                marker.setColor(1, 1, 1, 1)
            elif fallback is not None:
                marker.setColor(*fallback)

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

    def create_marker_with_icon(self, name, scale, icon_key, fallback_color=None):
        """Маркер с иконкой и запасным цветом | Marker with icon and fallback color"""
        texture = self.model_icons.get(icon_key)
        color = None if texture is not None else fallback_color
        marker = self.create_marker(name, scale, texture=texture, color=color)
        self.marker_meta[marker] = (icon_key, fallback_color)
        return marker

    def create_markers(self):
        player_icon = self.model_icons.get(PLAYER_ICON)
        self.player_marker = self.create_marker_with_icon(
            "player_marker", MINIMAP_PLAYER_MARKER_SCALE,
            PLAYER_ICON, (0, 1, 0, 1) if player_icon is None else None,
        )
        self.markers.append((self.player_root, self.player_marker))

        for name, node in self.objects:
            marker = self.create_marker_with_icon(
                f"obj_{id(node)}", MINIMAP_OBJECT_MARKER_SCALE,
                name, None,
            )
            self.markers.append((node, marker))

        for enemy in self.npc_enemies:
            enemy_icon = self.model_icons.get(enemy.model_name)
            marker = self.create_marker_with_icon(
                f"npc_{id(enemy)}", MINIMAP_NPC_MARKER_SCALE,
                enemy.model_name, (1, 0, 0, 1) if enemy_icon is None else None,
            )
            self.markers.append((enemy, marker))

        for pickup in self.pickups:
            pickup_icon = self.model_icons.get(pickup.model_name)
            marker = self.create_marker_with_icon(
                f"pickup_{id(pickup)}", MINIMAP_OBJECT_MARKER_SCALE,
                pickup.model_name, (1, 1, 0, 1) if pickup_icon is None else None,
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