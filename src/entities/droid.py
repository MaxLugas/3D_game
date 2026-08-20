import os

from math import atan2, degrees

from direct.actor.Actor import Actor
from panda3d.core import CollisionRay, CollisionNode, BitMask32, LVector3
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from src.config import (
    SHOW_BOUNDS,
    OBSTACLE_MASK_BIT,
    MODELS_DIR,
)
from src.core.npc_config import (
    DROID_MODEL,
    DROID_AGGRO_DISTANCE,
    DROID_ATTACK_DISTANCE,
    DROID_RUN_SPEED,
    DROID_SEPARATION_DISTANCE,
    DROID_AVOID_LOOKAHEAD,
    DROID_AVOID_SPACING,
    DROID_AVOID_STRENGTH,
)
from src.maps.model_loader import create_bounds_collider


class Droid:
    def __init__(self, render, pos, pusher, collision_trav, heading=0, scale=1):
        """Создаёт дроида: модель, анимации, коллайдер | Create droid: model, animations, collider"""
        self.render = render
        self.scale = scale

        self.actor = Actor(os.path.join(MODELS_DIR, DROID_MODEL))
        self.actor.reparentTo(render)
        self.actor.setScale(scale)
        self.actor.setPos(pos)
        self.actor.setH(heading)
        if SHOW_BOUNDS:
            self.actor.showBounds()
        self.actor.loop("Idle")

        self.berserk = False
        self.running = False
        self.attacking = False

        # === СОЗДАНИЕ КОЛЛАЙДЕРА | CREATE COLLIDER ===
        # Коллайдер из границ модели; масштаб наследуется родителем | Collider from model bounds; scale inherited from parent
        lmin, lmax = self.actor.getTightBounds(self.actor)
        self.collider_center = (lmin + lmax) * 0.5
        self.collider_half = (lmax - lmin) * 0.5

        collider_node = create_bounds_collider(
            self.actor,
            f"droid_{id(self)}",
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

    def is_alive(self):
        """Жив ли дроид | Check if droid is alive"""
        return not self.actor.isEmpty()

    def die(self):
        """Удаляет дроида и его коллайдеры | Remove droid and its colliders"""
        self.pusher.removeCollider(self.collider)
        self.collision_trav.removeCollider(self.collider)
        for np in self.avoid_nodes.values():
            np.removeNode()
        self.actor.cleanup()

    def update(self, player_pos, dt, others=()):
        """Обновление состояния дроида каждый кадр | Update droid state every frame"""
        dist = (self.actor.getPos(self.render) - player_pos).length()

        # Логика состояний | State machine
        if not self.berserk and dist < DROID_AGGRO_DISTANCE:
            self.berserk = True
            self.running = False
            self.attacking = False
            self.actor.stop()
            self.actor.play("Berserker_Call")
        elif self.berserk and not self.running and not self.attacking:
            ctrl = self.actor.getAnimControl("Berserker_Call")
            if not ctrl or not ctrl.isPlaying():
                self.running = True
                self.actor.stop()
                self.actor.loop("Running_03")
        elif self.running:
            if dist >= DROID_AGGRO_DISTANCE:
                self.berserk = False
                self.running = False
                self.actor.stop()
                self.actor.loop("Idle")
            elif dist < DROID_ATTACK_DISTANCE:
                self.running = False
                self.attacking = True
                self.actor.stop()
                self.actor.play("Attack_02")
            else:
                self.move_toward(player_pos, dt, others)
        elif self.attacking:
            ctrl = self.actor.getAnimControl("Attack_02")
            if ctrl and ctrl.isPlaying():
                self.look_at_player(player_pos)
            else:
                self.attacking = False
                if dist < DROID_ATTACK_DISTANCE:
                    self.attacking = True
                    self.actor.stop()
                    self.actor.play("Attack_02")
                elif dist < DROID_AGGRO_DISTANCE:
                    self.running = True
                    self.actor.stop()
                    self.actor.loop("Running_03")
                else:
                    self.berserk = False
                    self.actor.stop()
                    self.actor.loop("Idle")

    def look_at_player(self, player_pos):
        """
        Поворачивает дроида к игроку
        Rotates droid to face the player
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

        self.actor.setPos(self.actor.getPos(self.render) + move * DROID_RUN_SPEED * dt)

    def avoid_obstacle(self, move):
        """
        Обход препятствий тремя лучами
        Obstacle avoidance with three rays
        """
        pos = self.actor.getPos(self.render)
        height = pos.getZ() + self.collider_center.z * self.scale
        perp = LVector3(-move.y, move.x, 0)

        for name, offset in (
            ("left", perp * DROID_AVOID_SPACING),
            ("center", LVector3(0, 0, 0)),
            ("right", perp * -DROID_AVOID_SPACING),
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
            if dist > DROID_AVOID_LOOKAHEAD:
                continue

            if name == "center":
                if center_dist is None or dist < center_dist:
                    center_dist = dist
                    center_surface = entry.getSurfacePoint(self.render)
            else:
                blocked[name] = True

        steer = LVector3(0, 0, 0)

        if blocked["left"] and not blocked["right"]:
            steer -= perp * DROID_AVOID_STRENGTH
        elif blocked["right"] and not blocked["left"]:
            steer += perp * DROID_AVOID_STRENGTH
        elif center_surface is not None:
            obs = center_surface - pos
            obs.setZ(0)
            if move.x * obs.y - move.y * obs.x >= 0:
                steer -= perp * DROID_AVOID_STRENGTH
            else:
                steer += perp * DROID_AVOID_STRENGTH
        elif blocked["left"] and blocked["right"]:
            steer -= move * DROID_AVOID_STRENGTH * 0.5

        return steer

    def probe_name(self, from_np):
        """Определяет, какой луч сработал | Identify which ray was hit"""
        for name, np in self.avoid_nodes.items():
            if from_np == np:
                return name
        return None

    def separation(self, others):
        """Разделение дроидов, чтобы не слипались | Separation between droids to avoid stacking"""
        steer = LVector3(0, 0, 0)

        for other in others:
            offset = self.actor.getPos(self.render) - other.actor.getPos(self.render)
            offset.setZ(0)

            dist = offset.length()
            if 0 < dist < DROID_SEPARATION_DISTANCE:
                offset.normalize()
                steer += offset * (1.0 - dist / DROID_SEPARATION_DISTANCE)

        return steer