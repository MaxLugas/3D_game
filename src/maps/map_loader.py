import json
import os

from panda3d.core import Point3, BitMask32

from src.config import SHOW_BOUNDS, OBSTACLE_MASK_BIT, MAP_FILE, PICKUP_MODELS, PLAYER_MODEL
from src.core.npc_config import NPCS
from src.entities.npc_enemies import Npc_Enemy
from src.entities.pickup import PickupItem
from src.maps.model_loader import load_model_or_actor, create_bounds_collider, apply_world_render


class MapLoader:
    def __init__(self, render, loader, pusher=None, collision_trav=None):
        self.render = render
        self.loader = loader
        self.pusher = pusher
        self.collision_trav = collision_trav
        self.objects = []
        self.npc_enemies = []
        self.pickups = []
        self.player_start = None

    def load_map(self, path=MAP_FILE):
        """
        Загрузка карты из JSON файла
        Load map from JSON file
        """
        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for name, items in data.get("objects", {}).items():
            for item in items:
                pos = Point3(*item.get("pos", [0, 0, 0]))
                heading = item.get("heading", 0)
                pitch = item.get("pitch", 0)
                scale = item.get("scale")

                if name == PLAYER_MODEL:
                    if self.player_start is None:
                        self.player_start = (pos, heading)
                    continue
                if name in NPCS:
                    enemy = Npc_Enemy(self.render, pos, self.pusher, self.collision_trav, model=name, heading=heading, scale=scale)
                    self.npc_enemies.append(enemy)
                elif name in PICKUP_MODELS:
                    pickup = PickupItem(self.render, self.loader, name, pos, heading=heading, scale=scale)
                    self.pickups.append(pickup)
                else:
                    node = self.load_model(name)
                    node.reparentTo(self.render)
                    node.setPos(*pos)
                    node.setH(heading)
                    if pitch:
                        node.setP(pitch)
                    node.setScale(scale if scale else 1)
                    if SHOW_BOUNDS:
                        node.showBounds()
                    self.setup_collidable_object(node)
                    self.objects.append((name, node))

    def setup_collidable_object(self, node):
        """Создаёт коллайдер для статичного объекта. | Create collider for static object."""
        collision = create_bounds_collider(
            node,
            f"static_{id(node)}",
            into_mask=BitMask32.bit(1) | BitMask32.bit(OBSTACLE_MASK_BIT),
        )
        node.attachNewNode(collision)

    def load_model(self, name):
        """Загружает статичную модель. | Load static model."""
        node = load_model_or_actor(self.loader, name)
        return apply_world_render(node, name)