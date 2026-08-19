from pathlib import Path
import math

from panda3d.core import CardMaker, TransparencyAttrib, LColor, LVector2

from src.config import (
    MAP_SIZE,
    MINIMAP_SIZE,
    MINIMAP_MARGIN,
    MINIMAP_BG_ALPHA,
    MINIMAP_PLAYER_MARKER_SCALE,
    MINIMAP_NPC_MARKER_SCALE,
    MINIMAP_OBJECT_MARKER_SCALE,
)

ICON_NAMES = ("tree", "stone", "statue", "cottage", "fence", "target", "npc", "player_start")

MODEL_ICON_MAP = {
    "tree.bam": "tree",
    "stone.bam": "stone",
    "stone_2.bam": "stone",
    "statue.bam": "statue",
    "house.bam": "cottage",
    "fence.bam": "fence",
    "target.bam": "target",
}

MODEL_COLORS = {
    "tree.bam": (0.2, 0.8, 0.2, 1),
    "stone.bam": (0.6, 0.6, 0.6, 1),
    "stone_2.bam": (0.6, 0.6, 0.6, 1),
    "statue.bam": (1, 1, 0, 1),
    "chest.bam": (0.8, 0.5, 0.2, 1),
}


class Minimap:
    def __init__(self, render, aspect2d, loader, player_root, objects, droids, pickups, map_half_size=MAP_SIZE):
        """
        render: корневой узел сцены | scene root node
        aspect2d: UI-узел для HUD-элементов | UI node for HUD elements
        loader: загрузчик текстур | texture loader
        player_root: корневой узел игрока | player root node
        objects: статичные объекты (name, node) | static objects (name, node)
        droids: список дроидов | list of droids
        pickups: список предметов подбора | list of pickups
        map_half_size: половина размера игрового поля | half of the game field size
        """
        self.render = render
        self.aspect2d = aspect2d
        self.loader = loader
        self.player_root = player_root
        self.objects = objects
        self.droids = droids
        self.pickups = pickups
        self.map_half_size = map_half_size
        self.minimap_size = MINIMAP_SIZE

        self.icons = self._load_icons()

        self.root = aspect2d.attachNewNode("minimap")
        self.bg = self._create_background()
        self.markers = []

        self._create_markers()
        self.set_visible(False)

    def _load_icons(self):
        icons_dir = Path(__file__).resolve().parents[2] / "assets" / "icons"
        icons = {}
        for name in ICON_NAMES:
            path = icons_dir / f"{name}.png"
            if path.exists():
                icons[name] = self.loader.loadTexture(str(path))
        return icons

    def _create_background(self):
        cm = CardMaker("minimap_bg")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        bg = self.root.attachNewNode(cm.generate())
        bg.setScale(self.minimap_size)
        bg.setColor(0, 0, 0, MINIMAP_BG_ALPHA)
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setBin("fixed", 100)
        bg.setDepthTest(False)
        bg.setDepthWrite(False)
        self.bg = bg
        self._update_bg_position()
        return bg

    def _update_bg_position(self):
        """Позиционирует фон относительно текущего аспекта окна | Position background relative to current window aspect"""
        sx = self.aspect2d.getSx()
        self.bg.setPos(-1 / sx + MINIMAP_MARGIN + self.minimap_size / 2, 0, 1 - MINIMAP_MARGIN - self.minimap_size / 2)

    def _make_marker(self, name, scale, texture=None, color=None):
        cm = CardMaker(name)
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        marker = self.root.attachNewNode(cm.generate())
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

    def _create_markers(self):
        player_icon = self.icons.get("player_start")
        self.player_marker = self._make_marker(
            "player_marker", MINIMAP_PLAYER_MARKER_SCALE,
            texture=player_icon, color=(0, 1, 0, 1) if player_icon is None else None,
        )
        self.markers.append((self.player_root, self.player_marker))

        for name, node in self.objects:
            icon = self.icons.get(MODEL_ICON_MAP.get(name))
            color = MODEL_COLORS.get(name, (1, 1, 1, 1))
            marker = self._make_marker(
                f"obj_{id(node)}", MINIMAP_OBJECT_MARKER_SCALE,
                texture=icon, color=None if icon is not None else color,
            )
            self.markers.append((node, marker))

        npc_icon = self.icons.get("npc")
        for droid in self.droids:
            marker = self._make_marker(
                f"npc_{id(droid)}", MINIMAP_NPC_MARKER_SCALE,
                texture=npc_icon, color=(1, 0, 0, 1) if npc_icon is None else None,
            )
            self.markers.append((droid, marker))

        statue_icon = self.icons.get("statue")
        for pickup in self.pickups:
            marker = self._make_marker(
                f"pickup_{id(pickup)}", MINIMAP_OBJECT_MARKER_SCALE,
                texture=statue_icon, color=(1, 1, 0, 1) if statue_icon is None else None,
            )
            self.markers.append((pickup, marker))

    def _source_pos(self, source):
        if hasattr(source, "get_position"):
            return source.get_position()
        if hasattr(source, "actor"):
            return source.actor.getPos(self.render)
        return source.getPos(self.render)

    def _source_dead(self, source):
        if hasattr(source, "is_alive"):
            return not source.is_alive()
        if hasattr(source, "is_available"):
            return not source.is_available()
        return source.isEmpty()

    def _world_to_minimap(self, pos):
        nx = pos.x / self.map_half_size
        ny = pos.y / self.map_half_size
        offset = self.minimap_size / 2
        return LVector2(self.bg.getX() + nx * offset, self.bg.getZ() + ny * offset)

    def set_visible(self, visible):
        if visible:
            self.root.show()
        else:
            self.root.hide()

    def update(self):
        if self.root.isHidden():
            return

        self._update_bg_position()

        valid_markers = []
        for source, marker in self.markers:
            if self._source_dead(source):
                marker.removeNode()
                continue

            try:
                m_pos = self._world_to_minimap(self._source_pos(source))
            except Exception:
                marker.removeNode()
                continue

            marker.setPos(m_pos.x, 0, m_pos.y)
            valid_markers.append((source, marker))

        self.markers = valid_markers
        self._update_player_rotation()

    def _update_player_rotation(self):
        """Поворачивает маркер игрока по направлению взгляда | Rotate player marker with look direction"""
        forward = self.player_root.getQuat(self.render).getForward()
        angle = math.degrees(math.atan2(forward.x, forward.y))
        self.player_marker.setR(angle)