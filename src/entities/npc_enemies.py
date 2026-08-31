from math import atan2, degrees

from direct.actor.Actor import Actor
from panda3d.core import CollisionRay, CollisionNode, BitMask32, LVector3
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from src.config import (
    SHOW_BOUNDS,
    OBSTACLE_MASK_BIT,
)
from src.core.npc_config import NPC_MODELS, npc_config
from src.maps.model_loader import create_bounds_collider, apply_world_render


class Npc_Enemy:
    def __init__(self, render, pos, pusher, collision_trav, model=NPC_MODELS, heading=0, scale=1):
        """Создаёт NPC: модель, анимации, коллайдер | Create NPC: model, animations, collider"""
        self.render = render
        self.model_name = model
        self.scale = scale

        config = npc_config(model)
        self.aggro_distance = config["aggro_distance"]
        self.attack_distance = config["attack_distance"]
        self.run_speed = config["run_speed"]
        self.separation_distance = config["separation_distance"]
        self.avoid_lookahead = config["avoid_lookahead"]
        self.avoid_spacing = config["avoid_spacing"]
        self.avoid_strength = config["avoid_strength"]
        self.anims = config.get("anims", {})

        self.actor = Actor(model)
        self.actor.reparentTo(render)
        self.actor.setScale(scale)
        self.actor.setPos(pos)
        self.actor.setH(heading)
        apply_world_render(self.actor, model)
        if SHOW_BOUNDS:
            self.actor.showBounds()
        self.loop_anim("idle")

        self.berserk = False
        self.running = False
        self.attacking = False

        # === СОЗДАНИЕ КОЛЛАЙДЕРА | CREATE COLLIDER ===
        # Коллайдер из границ модели; масштаб наследуется родителем | Collider from model bounds; scale inherited from parent
        lmin, lmax = self.actor.getTightBounds(self.actor)
        self.collider_center = (lmin + lmax) * 0.5

        collider_node = create_bounds_collider(
            self.actor,
            f"enemy_{id(self)}",
            into_mask=BitMask32.bit(1),
            from_mask=BitMask32.bit(OBSTACLE_MASK_BIT),
        )
        self.collider = self.actor.attachNewNode(collider_node)

        self.pusher = pusher
        self.collision_trav = collision_trav
        self.pusher.addCollider(self.collider, self.actor)
        self.collision_trav.addCollider(self.collider, self.pusher)

        self.avoid_rays = {}
        self.avoid_nodes = {}
        # Лучи обхода препятствий (слева, по центру, справа) | Obstacle avoidance rays (left, center, right)
        for name in ("left", "center", "right"):
            ray = CollisionRay()
            avoid_node = CollisionNode(f"avoid_{name}_{id(self)}")
            avoid_node.addSolid(ray)
            avoid_node.setFromCollideMask(BitMask32.bit(OBSTACLE_MASK_BIT))
            avoid_node.setIntoCollideMask(BitMask32.allOff())
            np = self.render.attachNewNode(avoid_node)
            self.avoid_rays[name] = ray
            self.avoid_nodes[name] = np

        self.avoid_trav = CollisionTraverser()
        self.avoid_queue = CollisionHandlerQueue()
        for np in self.avoid_nodes.values():
            self.avoid_trav.addCollider(np, self.avoid_queue)

    def anim(self, key):
        """Имя анимации по ключу с запасным вариантом | Anim name by key with fallback"""
        name = self.anims.get(key)
        if name is not None and name in self.actor.getAnimNames():
            return name
        anims = self.actor.getAnimNames()
        return anims[0] if anims else None

    def play_anim(self, key):
        """Однократное воспроизведение анимации по ключу | Play one-shot animation by key"""
        name = self.anim(key)
        if name is not None:
            self.actor.play(name)

    def loop_anim(self, key):
        """Зацикленная анимация по ключу | Loop animation by key"""
        name = self.anim(key)
        if name is not None:
            self.actor.loop(name)

    def is_alive(self):
        """Жив ли NPC | Check if NPC is alive"""
        return not self.actor.isEmpty()

    def die(self):
        """Удаляет NPC и его коллайдеры | Remove NPC and its colliders"""
        self.pusher.removeCollider(self.collider)
        self.collision_trav.removeCollider(self.collider)
        for np in self.avoid_nodes.values():
            np.removeNode()
        self.actor.cleanup()

    def update(self, player_pos, dt, others=()):
        """Обновление состояния NPC каждый кадр | Update NPC state every frame"""
        dist = (self.actor.getPos(self.render) - player_pos).length()

        # Логика состояний | State machine
        if not self.berserk and dist < self.aggro_distance:
            self.berserk = True
            self.running = False
            self.attacking = False
            self.actor.stop()
            self.play_anim("aggro")
        elif self.berserk and not self.running and not self.attacking:
            ctrl = self.actor.getAnimControl(self.anim("aggro"))
            if not ctrl or not ctrl.isPlaying():
                self.running = True
                self.actor.stop()
                self.loop_anim("run")
        elif self.running:
            if dist >= self.aggro_distance:
                self.berserk = False
                self.running = False
                self.actor.stop()
                self.loop_anim("idle")
            elif dist < self.attack_distance:
                self.running = False
                self.attacking = True
                self.actor.stop()
                self.play_anim("attack")
            else:
                self.move_toward(player_pos, dt, others)
        elif self.attacking:
            ctrl = self.actor.getAnimControl(self.anim("attack"))
            if ctrl and ctrl.isPlaying():
                self.look_at_player(player_pos)
            else:
                self.attacking = False
                if dist < self.attack_distance:
                    self.attacking = True
                    self.actor.stop()
                    self.play_anim("attack")
                elif dist < self.aggro_distance:
                    self.running = True
                    self.actor.stop()
                    self.loop_anim("run")
                else:
                    self.berserk = False
                    self.actor.stop()
                    self.loop_anim("idle")

    def look_at_player(self, player_pos):
        """
        Поворачивает NPC к игроку
        Rotates NPC to face the player
        """
        direction = player_pos - self.actor.getPos(self.render)
        direction.setZ(0)

        if direction.lengthSquared() > 0.0001:
            self.actor.setH(degrees(atan2(direction.x, -direction.y)))

    def move_toward(self, player_pos, dt, others=()):
        """
        Движение к цели с разделением и обходом препятствий
        Move toward target with separation and obstacle avoidance
        """
        self.look_at_player(player_pos)

        direction = player_pos - self.actor.getPos(self.render)
        direction.setZ(0)

        length = direction.length()
        if length <= 0.001:
            return

        direction.normalize()

        base = direction + self.separation(others)
        if base.lengthSquared() > 0.0001:
            base.normalize()
        else:
            base = direction

        move = base + self.avoid_obstacle(base)
        if move.lengthSquared() > 0.0001:
            move.normalize()
        else:
            move = base

        self.actor.setPos(self.actor.getPos(self.render) + move * self.run_speed * dt)

    def avoid_obstacle(self, move):
        """
        Обход препятствий тремя лучами
        Obstacle avoidance with three rays
        """
        pos = self.actor.getPos(self.render)
        height = pos.getZ() + self.collider_center.z * self.scale
        perp = LVector3(-move.y, move.x, 0)

        for name, offset in (
            ("left", perp * self.avoid_spacing),
            ("center", LVector3(0, 0, 0)),
            ("right", perp * -self.avoid_spacing),
        ):
            origin = pos + offset
            origin.setZ(height)
            self.avoid_rays[name].setOrigin(origin)
            self.avoid_rays[name].setDirection(move)

        self.avoid_queue.clearEntries()
        self.avoid_trav.traverse(self.render)

        blocked = {"left": False, "right": False}
        center_dist = None
        center_surface = None

        for i in range(self.avoid_queue.getNumEntries()):
            entry = self.avoid_queue.getEntry(i)
            name = self.probe_name(entry.getFromNodePath())
            if name is None:
                continue

            dist = (entry.getSurfacePoint(self.render) - pos).length()
            if dist > self.avoid_lookahead:
                continue

            if name == "center":
                if center_dist is None or dist < center_dist:
                    center_dist = dist
                    center_surface = entry.getSurfacePoint(self.render)
            else:
                blocked[name] = True

        steer = LVector3(0, 0, 0)

        if blocked["left"] and not blocked["right"]:
            steer -= perp * self.avoid_strength
        elif blocked["right"] and not blocked["left"]:
            steer += perp * self.avoid_strength
        elif center_surface is not None:
            obs = center_surface - pos
            obs.setZ(0)
            if move.x * obs.y - move.y * obs.x >= 0:
                steer -= perp * self.avoid_strength
            else:
                steer += perp * self.avoid_strength
        elif blocked["left"] and blocked["right"]:
            steer -= move * self.avoid_strength * 0.5

        return steer

    def probe_name(self, from_np):
        """Определяет, какой луч сработал | Identify which ray was hit"""
        for name, np in self.avoid_nodes.items():
            if from_np == np:
                return name
        return None

    def separation(self, others):
        """Разделение NPC, чтобы не слипались | Separation between NPCs to avoid stacking"""
        steer = LVector3(0, 0, 0)

        for other in others:
            offset = self.actor.getPos(self.render) - other.actor.getPos(self.render)
            offset.setZ(0)

            dist = offset.length()
            if 0 < dist < self.separation_distance:
                offset.normalize()
                steer += offset * (1.0 - dist / self.separation_distance)

        return steer