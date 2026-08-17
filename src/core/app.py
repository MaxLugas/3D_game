import os

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import *

from src.config import SKY_COLOR, SPELL_RANGE, PICKUP_RANGE, PICKUP_RAY_RANGE, GROUND_TOLERANCE, WINDOW_WIDTH, WINDOW_HEIGHT
from src.entities.player import Player
from src.systems.camera import CameraController
from src.systems.world_setup import WorldSetupMixin
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

        self.droids = self.map_loader.droids
        self.pickups = self.map_loader.pickups

        for k in self.player.keys:
            self.accept(k, self.player.set_key, [k, True])
            self.accept(f"{k}-up", self.player.set_key, [k, False])

        self.accept("space", self.player.jump)
        self.accept("mouse1", self.on_shoot)
        self.accept("e", self.pickup)

        self.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        for thrower in self.buttonThrowers:
            thrower.node().set_modifier_buttons(ModifierButtons())

        props = WindowProperties()
        props.setCursorHidden(True)
        props.setSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.win.requestProperties(props)

        self.taskMgr.doMethodLater(0.1, self.init_mouse, "init_mouse")
        self.taskMgr.add(self.update, "update")

    def setup_collision(self):
        """Настройка коллайдеров: игрок, лучи заклинания и подбора | Setup colliders: player, spell and pickup rays"""
        self.setup_player_collision()

        self.spell_ray = CollisionRay()
        spell_ray_node = CollisionNode("spellRay")
        spell_ray_node.addSolid(self.spell_ray)
        spell_ray_node.setFromCollideMask(BitMask32.bit(1))
        spell_ray_node.setIntoCollideMask(BitMask32.allOff())

        self.spell_ray_np = self.camera.attachNewNode(spell_ray_node)
        self.spell_queue = CollisionHandlerQueue()
        self.spell_trav = CollisionTraverser()
        self.spell_trav.addCollider(self.spell_ray_np, self.spell_queue)

        self.pickup_ray = CollisionRay()
        pickup_ray_node = CollisionNode("pickupRay")
        pickup_ray_node.addSolid(self.pickup_ray)
        pickup_ray_node.setFromCollideMask(BitMask32.bit(2))
        pickup_ray_node.setIntoCollideMask(BitMask32.allOff())

        self.pickup_ray_np = self.camera.attachNewNode(pickup_ray_node)
        self.pickup_queue = CollisionHandlerQueue()
        self.pickup_trav = CollisionTraverser()
        self.pickup_trav.addCollider(self.pickup_ray_np, self.pickup_queue)

        self.setup_ground_ray()

    def setup_ui(self):
        """Создаёт прицел и подсказку подбора | Create crosshair and pickup hint"""
        cm_cross = CardMaker("crosshair")
        cm_cross.setFrame(-0.01, 0.01, -0.01, 0.01)

        self.crosshair = self.aspect2d.attachNewNode(cm_cross.generate())
        self.crosshair.setColor(1, 1, 1, 1)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair.setBin("fixed", 100)
        self.crosshair.setDepthTest(False)
        self.crosshair.setDepthWrite(False)

        self.pickup_hint = OnscreenText(
            text="[E]",
            pos=(0, -0.15),
            scale=0.07,
            fg=(1, 1, 1, 1),
            mayChange=True
        )
        self.pickup_hint.hide()

    def on_shoot(self):
        """Обработчик выстрела | Shoot handler"""
        self.player.shoot(on_spell_hit=self._perform_shot)

    def _perform_shot(self):
        """Проверка попадания заклинания в дроидов | Check spell hit against droids"""
        alive = [d for d in self.droids if d.is_alive()]
        if not alive:
            return

        self.spell_ray.setOrigin(0, 0, 0)
        self.spell_ray.setDirection(0, 1, 0)

        self.spell_queue.clearEntries()
        self.spell_trav.traverse(self.render)

        if self.spell_queue.getNumEntries() == 0:
            return

        self.spell_queue.sortEntries()
        entry = self.spell_queue.getEntry(0)

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

        self.pickup_ray.setOrigin(0, 0, 0)
        self.pickup_ray.setDirection(0, 1, 0)

        self.pickup_queue.clearEntries()
        self.pickup_trav.traverse(self.render)

        if self.pickup_queue.getNumEntries() == 0:
            return None

        self.pickup_queue.sortEntries()
        entry = self.pickup_queue.getEntry(0)
        hit_np = entry.getIntoNodePath()
        dist = (entry.getSurfacePoint(self.render) - player_pos).length()

        for p in available:
            if hit_np == p.collider and dist <= PICKUP_RAY_RANGE:
                return p
        return None

    def update(self, task):
        """Обновление игры каждый кадр | Update game every frame"""
        dt = globalClock.getDt()

        self.player.shift_down = (
            self.mouseWatcherNode.isButtonDown(KeyboardButton.lshift())
            or self.mouseWatcherNode.isButtonDown(KeyboardButton.rshift())
        )

        self.camera_controller.update(dt, self.win, self.mouseWatcherNode)

        self.ground_queue.clearEntries()
        self.ground_trav.traverse(self.render)

        self.player.is_grounded = False

        if self.ground_queue.getNumEntries() > 0:
            self.ground_queue.sortEntries()
            entry = self.ground_queue.getEntry(0)
            z = entry.getSurfacePoint(self.render).getZ()
            if self.player.root.getZ() <= z + GROUND_TOLERANCE and self.player.velocity_z <= 0:
                self.player.is_grounded = True
                self.player.root.setZ(z)
                self.player.velocity_z = 0

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

        self.player.resolve_animation(on_spell_hit=self._perform_shot)

        return task.cont
