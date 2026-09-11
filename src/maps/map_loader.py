import json
import os

from panda3d.core import Point3

from src.config import SHOW_BOUNDS, MAP_FILE, PICKUP_MODELS, PLAYER_MODEL
from src.core.collision_masks import MASK_PLAYER, MASK_OBSTACLE, collide_mask
from src.core.npc_config import NPCS
from src.entities.npc_enemy import NpcEnemy
from src.entities.pickup import PickupItem
from src.maps.model_loader import load_model_or_actor, create_bounds_collider, apply_world_render


class MapLoader:
    def __init__(self, render, loader, pusher=None, collision_trav=None, npc_manager=None):
        self.render = render
        self.loader = loader
        self.pusher = pusher
        self.collision_trav = collision_trav
        self.npc_manager = npc_manager
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
                    enemy = NpcEnemy(
                        self.render, pos, self.pusher, self.collision_trav,
                        model=name, heading=heading, scale=scale, manager=self.npc_manager,
                    )
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
            into_mask=collide_mask(MASK_PLAYER, MASK_OBSTACLE),
        )
        node.attachNewNode(collision)

    def load_model(self, name):
        """Загружает статичную модель. | Load static model."""
        node = load_model_or_actor(self.loader, name)
        return apply_world_render(node, name)