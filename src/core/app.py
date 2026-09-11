from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import (
    Filename,
    KeyboardButton,
    get_model_path,
)

from src.config import (
    SKY_COLOR,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    PROJECT_ROOT,
)
from src.entities.player import Player
from src.systems.camera import CameraController
from src.systems.world_setup import WorldSetupMixin
from src.systems.minimap import Minimap
from src.systems.hud import Hud
from src.systems.combat import CombatSystem
from src.systems.pickup import PickupSystem
from src.systems.npc_manager import NpcManager
from src.maps.map_loader import MapLoader


class Game(WorldSetupMixin, ShowBase):
    def __init__(self):
        """Инициализация игры: сцена, игрок, коллайдеры, карта | Initialize game: scene, player, colliders, map"""
        super().__init__()

        get_model_path().prepend_directory(Filename.from_os_specific(str(PROJECT_ROOT)))

        self.disableMouse()
        self.setBackgroundColor(*SKY_COLOR, 1)

        self.setup_lighting()
        self.create_ground_tiles()

        self.player = Player(self.render)
        self.camera_controller = CameraController(self.player.root, self.camera)

        self.setup_collision()
        self.hud = Hud(self.aspect2d)

        self.npc_manager = NpcManager(self.render)

        self.map_loader = MapLoader(
            self.render, self.loader, self.pusher, self.collision_trav,
            npc_manager=self.npc_manager,
        )
        self.map_loader.load_map()

        start = self.map_loader.player_start
        if start is not None:
            self.player.root.setPos(start[0])
            self.camera_controller.yaw = start[1] + 180

        self.npc_enemies = self.map_loader.npc_enemies
        self.pickups = self.map_loader.pickups

        self.combat = CombatSystem(
            self.render, self.camera, self.player,
            self.npc_enemies,
            self.spell_ray, self.spell_queue, self.spell_trav,
        )
        self.pickup_system = PickupSystem(
            self.render, self.player, self.pickups,
            self.pickup_ray, self.pickup_queue, self.pickup_trav,
        )

        self.minimap = Minimap(
            self.render,
            self.aspect2d,
            self.loader,
            self.player.root,
            self.map_loader.objects,
            self.npc_enemies,
            self.pickups,
        )

        self.bind_movement_keys(self.player)

        self.accept("space", self.player.jump)
        self.accept("mouse1", self.combat.on_shoot)
        self.accept("e", self.pickup_system.pickup)

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

    def update(self, task):
        """Обновление игры каждый кадр | Update game every frame"""
        dt = globalClock.getDt()

        mw = self.mouseWatcherNode
        if mw is None:
            return task.cont  # headless/offscreen: нет ввода | no input available

        self.hud.update_fps(dt)

        tab_held = mw.isButtonDown(KeyboardButton.tab())
        self.minimap.set_visible(tab_held)
        if tab_held:
            self.minimap.update()

        self.player.shift_down = self.is_shift_down(mw)

        self.camera_controller.update(dt, self.win, mw)

        self.player.update_movement(dt)
        self.update_grounding(self.player)
        self.player.apply_gravity(dt)
        self.player.clamp_position()

        self.pickup_system.update()
        self.hud.set_pickup_hint(self.pickup_system.can_pickup_now)

        player_pos = self.player.root.getPos(self.render)
        self.npc_manager.update(player_pos, dt)

        self.collision_trav.traverse(self.render)

        self.player.resolve_animation(on_spell_hit=self.combat.perform_shot)

        return task.cont