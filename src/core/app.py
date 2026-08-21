import os

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import (
    Filename,
    KeyboardButton,
    TextNode,
    get_model_path,
)

from src.config import (
    SKY_COLOR,
    SPELL_RANGE,
    PICKUP_RANGE,
    PICKUP_RAY_RANGE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from src.entities.player import Player
from src.systems.camera import CameraController
from src.systems.world_setup import WorldSetupMixin, create_crosshair
from src.systems.minimap import Minimap
from src.maps.map_loader import MapLoader


class Game(WorldSetupMixin, ShowBase):
    def __init__(self):
        """Инициализация игры: сцена, игрок, коллайдеры, карта | Initialize game: scene, player, colliders, map"""
        super().__init__()

        get_model_path().prepend_directory(Filename(os.getcwd()))

        self.disableMouse()
        self.setBackgroundColor(*SKY_COLOR, 1)

        self.setup_lighting()
        self.create_ground_tiles()

        self.player = Player(self.render)
        self.camera_controller = CameraController(self.render, self.player.root, self.camera)

        self.setup_collision()
        self.setup_ui()

        self.map_loader = MapLoader(self.render, self.loader, self.pusher, self.collision_trav)
        self.map_loader.load_map()

        start = self.map_loader.player_start
        if start is not None:
            self.player.root.setPos(start[0])
            self.camera_controller.yaw = start[1] + 180

        self.droids = self.map_loader.droids
        self.pickups = self.map_loader.pickups

        self.minimap = Minimap(
            self.render,
            self.aspect2d,
            self.loader,
            self.player.root,
            self.map_loader.objects,
            self.droids,
            self.pickups,
        )

        self.bind_movement_keys(self.player)

        self.accept("space", self.player.jump)
        self.accept("mouse1", self.on_shoot)
        self.accept("e", self.pickup)

        self.clear_modifier_buttons()

        self.setup_window(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.taskMgr.doMethodLater(0.1, self.init_mouse, "init_mouse")
        self.taskMgr.add(self.update, "update")

    def setup_collision(self):
        """Настройка коллайдеров: игрок, лучи заклинания и подбора | Setup colliders: player, spell and pickup rays"""
        self.setup_player_collision()

        self.spell_ray, self.spell_queue, self.spell_trav = self.create_camera_ray("spellRay", 1)
        self.pickup_ray, self.pickup_queue, self.pickup_trav = self.create_camera_ray("pickupRay", 2)

        self.setup_ground_ray()

    def setup_ui(self):
        """Создаёт прицел, подсказку подбора и счётчик FPS | Create crosshair, pickup hint and FPS counter"""
        self.crosshair = create_crosshair(self.aspect2d)

        self.pickup_hint = OnscreenText(
            text="[E]",
            pos=(0, -0.15),
            scale=0.07,
            fg=(1, 1, 1, 1),
            mayChange=True
        )
        self.pickup_hint.hide()

        self.fps_label = OnscreenText(
            text="",
            pos=(1 / self.aspect2d.getSx() - 0.02, 0.95),
            align=TextNode.ARight,
            scale=0.05,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.fps_frames = 0
        self.fps_time = 0.0

    def update_fps(self, dt):
        """Обновляет счётчик FPS раз в полсекунды | Update FPS counter every half second"""
        self.fps_frames += 1
        self.fps_time += dt
        if self.fps_time >= 0.5:
            self.fps_label.setText(f"FPS: {round(self.fps_frames / self.fps_time)}")
            self.fps_frames = 0
            self.fps_time = 0.0

    def on_shoot(self):
        """Обработчик выстрела | Shoot handler"""
        self.player.shoot(on_spell_hit=self.perform_shot)

    def perform_shot(self):
        """Проверка попадания заклинания в дроидов | Check spell hit against droids"""
        alive = [d for d in self.droids if d.is_alive()]
        if not alive:
            return

        entry = self.cast_ray(self.spell_ray, self.spell_trav, self.spell_queue)
        if entry is None:
            return

        hit_np = entry.getIntoNodePath()
        dist = (entry.getSurfacePoint(self.render) - self.camera.getPos(self.render)).length()

        for droid in alive:
            if hit_np == droid.collider and dist <= SPELL_RANGE:
                droid.die()
                break

    def pickup(self):
        """Подбор предмета клавишей E | Pick up item with E key"""
        if self.player.jump_state in ("start", "loop"):
            return
        target = self.can_pickup()
        if target is not None:
            target.destroy()
            self.player.play_animation("PickUp_Table")

    def can_pickup(self):
        """Определяет предмет подбора | Find pickup target"""
        available = [p for p in self.pickups if p.is_available()]
        if not available:
            return None

        player_pos = self.player.root.getPos(self.render)

        nearest = None
        nearest_dist = PICKUP_RANGE
        for p in available:
            d = (p.get_position() - player_pos).length()
            if d <= nearest_dist:
                nearest = p
                nearest_dist = d
        if nearest is not None:
            return nearest

        entry = self.cast_ray(self.pickup_ray, self.pickup_trav, self.pickup_queue)
        if entry is None:
            return None

        hit_np = entry.getIntoNodePath()
        dist = (entry.getSurfacePoint(self.render) - player_pos).length()

        for p in available:
            if hit_np == p.collider and dist <= PICKUP_RAY_RANGE:
                return p
        return None

    def update(self, task):
        """Обновление игры каждый кадр | Update game every frame"""
        dt = globalClock.getDt()

        self.update_fps(dt)

        tab_held = self.mouseWatcherNode.isButtonDown(KeyboardButton.tab())
        self.minimap.set_visible(tab_held)
        if tab_held:
            self.minimap.update()

        self.player.shift_down = self.is_shift_down(self.mouseWatcherNode)

        self.camera_controller.update(dt, self.win, self.mouseWatcherNode)

        self.update_grounding(self.player)

        if self.can_pickup() is not None:
            self.pickup_hint.show()
        else:
            self.pickup_hint.hide()

        self.player.update_movement(dt)
        self.player.apply_gravity(dt)
        self.player.clamp_position()

        player_pos = self.player.root.getPos(self.render)
        alive = [d for d in self.droids if d.is_alive()]
        for droid in alive:
            others = [d for d in alive if d is not droid]
            droid.update(player_pos, dt, others)

        self.collision_trav.traverse(self.render)

        self.player.resolve_animation(on_spell_hit=self.perform_shot)

        return task.cont