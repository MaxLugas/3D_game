from direct.actor.Actor import Actor
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LVector3, LPoint3, BitMask32

from src.config import MAP_SIZE, PLAYER_MODEL
from src.maps.editor_config import (
    GHOST_COLOR,
    GHOST_NORMAL_MODELS,
    GHOST_WARN_COLOR,
    COLLISION_WARN_COLOR,
    MODEL_ROTATE_SPEED,
    PLACEMENT_DISTANCE,
    PICK_MASK_BIT,
)
from src.maps.model_loader import load_model_or_actor, create_bounds_collider, apply_world_render


class EditorModelsMixin:
    def load_actor_or_model(self, name):
        """Загружает модель или актёра с анимациями | Load model or animated actor"""
        return load_model_or_actor(self.loader, name)

    def destroy_node(self, node):
        """Удаляет узел сцены | Destroy scene node"""
        if node is None:
            return
        if isinstance(node, Actor):
            node.cleanup()
        else:
            node.removeNode()

    def create_ghost(self, index):
        """Создаёт призрак модели для предпросмотра размещения | Create ghost preview of the model"""
        self.model_index = index % len(self.models)
        self.current_model = self.models[self.model_index]

        if self.preview is not None:
            self.destroy_node(self.preview)

        self.preview = self.load_actor_or_model(self.current_model)
        self.preview.reparentTo(self.render)
        self.preview.showBounds()
        self.scale = 1
        self.preview.setScale(self.scale)
        self.preview.setH(self.camera.getH(self.render) + self.heading)
        self.preview_lift = -self.preview.getTightBounds()[0].z
        self.preview.setPos(0, 0, 0)
        self.preview.setHpr(0, 0, 0)
        pmin, pmax = self.preview.getTightBounds(self.preview)
        self.preview_min = pmin
        self.preview_max = pmax
        if self.current_model in GHOST_NORMAL_MODELS:
            self.preview.setTwoSided(True)
        else:
            self.preview.setColor(GHOST_COLOR)
            self.preview.setLightOff()
            self.preview.setMaterialOff()
            self.preview.setTwoSided(True)
        self.preview.hide()

        self.update_ui_text()

    def next_model(self):
        """Переключает на следующую модель | Switch to next model"""
        self.create_ghost(self.model_index + 1)

    def prev_model(self):
        """Переключает на предыдущую модель | Switch to previous model"""
        self.create_ghost(self.model_index - 1)

    def get_target(self):
        """Вычисляет точку размещения на земле | Compute placement point on the ground"""
        direction = self.camera.getQuat(self.render).getForward()
        pos = self.camera.getPos(self.render)

        if direction.z < -0.0001:
            distance = -pos.z / direction.z
            hit = pos + direction * distance
        else:
            flat = LVector3(direction)
            flat.setZ(0)
            flat.normalize()
            hit = pos + flat * PLACEMENT_DISTANCE
            hit.z = 0

        if abs(hit.x) > MAP_SIZE or abs(hit.y) > MAP_SIZE:
            return None

        return hit

    def place_object(self):
        """Размещает объект | Place object"""
        if self.current_model is None:
            return

        target = self.get_target()
        if target is None:
            return

        entry = {
            "model": self.current_model,
            "pos": [round(target.x, 2), round(target.y, 2), round(self.preview_lift, 2)],
            "heading": round(self.camera.getH(self.render) + self.heading) % 360,
            "pitch": round(self.pitch) % 360,
            "scale": round(self.scale, 2),
        }

        if self.current_model == PLAYER_MODEL:
            for i, (old_entry, old_node, _, _) in enumerate(self.placed):
                if old_entry["model"] == PLAYER_MODEL:
                    old_entry["pos"] = entry["pos"]
                    old_entry["heading"] = entry["heading"]
                    old_entry["pitch"] = entry["pitch"]
                    old_entry["scale"] = entry["scale"]
                    old_node.setPos(*entry["pos"])
                    old_node.setH(entry["heading"])
                    old_node.setP(entry["pitch"])
                    old_node.setScale(entry["scale"])
                    self.notice = "player start moved"
                    self.update_ui_text()
                    self.taskMgr.doMethodLater(2.0, self.clear_notice, "clear_notice_player_start")
                    return

        node = self.create_world_object(self.current_model, entry["pos"], entry["heading"], entry["pitch"], entry["scale"])
        bmin, bmax = node.getTightBounds(self.render)

        for other_entry, other_node, omin, omax in self.placed:
            if (
                bmin.x <= omax.x and bmax.x >= omin.x
                and bmin.y <= omax.y and bmax.y >= omin.y
                and bmin.z <= omax.z and bmax.z >= omin.z
            ):
                self.destroy_node(node)
                self.notice = "overlap: not placed"
                self.update_ui_text()
                self.taskMgr.doMethodLater(2.0, self.clear_notice, "clear_notice_overlap")
                return

        self.placed.append((entry, node, bmin, bmax))
        self.update_ui_text()

    def create_world_object(self, name, pos, heading=0, pitch=0, scale=None):
        """Создаёт объект мира по названию модели | Create world object by model name"""
        node = self.load_actor_or_model(name)
        node.reparentTo(self.render)
        node.showBounds()
        apply_world_render(node, name)
        node.setPos(*pos)
        if scale is None:
            scale = 1
        node.setScale(scale)
        node.setH(heading)
        if pitch:
            node.setP(pitch)

        pick_node = create_bounds_collider(
            node,
            f"pick_{id(node)}",
            into_mask=BitMask32.bit(PICK_MASK_BIT),
        )
        node.attachNewNode(pick_node)
        return node

    def delete_hovered_object(self):
        """Удаляет объект под прицелом по ПКМ | Delete object under the crosshair with RMB"""
        entry = self.cast_ray(self.pick_ray, self.pick_trav, self.pick_queue)
        if entry is None:
            return

        hit_np = entry.getIntoNodePath()

        for i, (placed_entry, node, _, _) in enumerate(self.placed):
            if hit_np.getParent() == node:
                self.destroy_node(node)
                del self.placed[i]
                self.notice = f"deleted {placed_entry['model']}"
                self.update_ui_text()
                self.taskMgr.doMethodLater(2.0, self.clear_notice, "clear_notice_delete")
                return

    def refresh_ghost_position(self):
        """Обновляет позицию призрака по направлению взгляда | Update ghost position from camera aim"""
        if self.preview is None:
            return

        if self.rotating:
            self.heading = (self.heading + MODEL_ROTATE_SPEED * globalClock.getDt()) % 360
            self.update_ui_text()

        self.preview.setH(self.camera.getH(self.render) + self.heading)
        self.preview.setP(self.pitch)
        self.preview.setScale(self.scale)

        target = self.get_target()
        if target is None:
            self.preview.hide()
            return

        self.preview.setPos(target.x, target.y, self.preview_lift)
        self.preview.show()

        if self.is_placement_blocked():
            self.preview.setColor(COLLISION_WARN_COLOR)
        elif self.get_display_y() < -0.01:
            self.preview.setColor(GHOST_WARN_COLOR)
        elif self.current_model not in GHOST_NORMAL_MODELS:
            self.preview.setColor(GHOST_COLOR)

    def preview_world_bounds(self):
        """Мировые границы призрака | World bounds of ghost"""
        q = self.preview.getQuat(self.render)
        scale = self.preview.getScale(self.render)
        pos = self.preview.getPos(self.render)

        mn = [float("inf")] * 3
        mx = [float("-inf")] * 3
        for x in (self.preview_min.x, self.preview_max.x):
            for y in (self.preview_min.y, self.preview_max.y):
                for z in (self.preview_min.z, self.preview_max.z):
                    v = q.xform(LVector3(x * scale.x, y * scale.y, z * scale.z)) + pos
                    for i in range(3):
                        if v[i] < mn[i]:
                            mn[i] = v[i]
                        if v[i] > mx[i]:
                            mx[i] = v[i]
        return (LPoint3(*mn), LPoint3(*mx))

    def is_placement_blocked(self):
        """Проверяет, пересекается ли призрак с размещёнными объектами | Check ghost overlap with placed objects"""
        if not self.placed:
            return False
        pmin, pmax = self.preview_world_bounds()
        for other_entry, other_node, omin, omax in self.placed:
            if (
                pmin.x <= omax.x and pmax.x >= omin.x
                and pmin.y <= omax.y and pmax.y >= omin.y
                and pmin.z <= omax.z and pmax.z >= omin.z
            ):
                return True
        return False

    def get_display_y(self):
        """Минимальная мировая высота призрака | Minimum world height of the ghost"""
        return self.preview_world_bounds()[0].z