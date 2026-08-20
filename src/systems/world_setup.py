from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    CardMaker,
    CollisionNode,
    CollisionBox,
    CollisionSphere,
    CollisionRay,
    CollisionTraverser,
    CollisionHandlerPusher,
    CollisionHandlerQueue,
    Point3,
    BitMask32,
    KeyboardButton,
    ModifierButtons,
    WindowProperties,
    TransparencyAttrib,
)

from src.config import (
    MAP_SIZE,
    GROUND_COLOR,
    AMBIENT_COLOR,
    SUN_COLOR,
    SUN_HPR,
    GROUND_THICKNESS,
    GROUND_TOLERANCE,
    PLAYER_COLLISION_CENTER,
    PLAYER_COLLISION_RADIUS,
)


def create_crosshair(aspect2d):
    """Создаёт прицел в центре экрана | Create crosshair at screen center"""
    card_maker = CardMaker("crosshair")
    card_maker.setFrame(-0.01, 0.01, -0.01, 0.01)
    crosshair = aspect2d.attachNewNode(card_maker.generate())
    crosshair.setColor(1, 1, 1, 1)
    crosshair.setTransparency(TransparencyAttrib.MAlpha)
    crosshair.setBin("fixed", 100)
    crosshair.setDepthTest(False)
    crosshair.setDepthWrite(False)
    return crosshair


class WorldSetupMixin:
    def setup_lighting(self):
        """Настройка освещения сцены | Setup scene lighting"""
        ambient = AmbientLight("ambient")
        ambient.setColor(AMBIENT_COLOR)
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(SUN_COLOR)
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(*SUN_HPR)
        self.render.setLight(sun_np)

    def create_ground_tiles(self):
        """Создаёт землю и невидимый коллайдер | Create ground and invisible collider"""
        cm = CardMaker("ground")
        cm.setFrame(-MAP_SIZE, MAP_SIZE, -MAP_SIZE, MAP_SIZE)

        ground = self.render.attachNewNode(cm.generate())
        ground.setP(-90)
        ground.setColor(*GROUND_COLOR, 1)
        ground.setTwoSided(True)

        # === Коллайдер земли | Ground collider ===
        ground_box = CollisionNode("groundCollision")
        ground_box.addSolid(CollisionBox(Point3(0, 0, -GROUND_THICKNESS), MAP_SIZE, MAP_SIZE, GROUND_THICKNESS))
        ground_box.setIntoCollideMask(BitMask32.bit(1))
        self.render.attachNewNode(ground_box)

    def setup_player_collision(self):
        """Настройка коллайдера игрока и толкателя | Setup player collider and pusher"""
        self.collision_trav = CollisionTraverser()

        player_node = CollisionNode("player")
        player_node.addSolid(CollisionSphere(*PLAYER_COLLISION_CENTER, PLAYER_COLLISION_RADIUS))
        player_node.setFromCollideMask(BitMask32.bit(1))
        player_node.setIntoCollideMask(BitMask32.allOff())

        self.player_collider = self.player.root.attachNewNode(player_node)

        self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(self.player_collider, self.player.root)
        self.collision_trav.addCollider(self.player_collider, self.pusher)

    def setup_ground_ray(self):
        """Создаёт луч к земле для определения приземления | Create ground ray for landing detection"""
        self.ground_ray = CollisionRay()
        self.ground_ray.setOrigin(0, 0, 1)
        self.ground_ray.setDirection(0, 0, -1)

        ground_ray_node = CollisionNode("groundRay")
        ground_ray_node.addSolid(self.ground_ray)
        ground_ray_node.setFromCollideMask(BitMask32.bit(1))
        ground_ray_node.setIntoCollideMask(BitMask32.allOff())

        self.ground_ray_np = self.player.root.attachNewNode(ground_ray_node)
        self.ground_queue = CollisionHandlerQueue()
        self.ground_trav = CollisionTraverser()
        self.ground_trav.addCollider(self.ground_ray_np, self.ground_queue)

    def create_camera_ray(self, name, mask_bit):
        """Создаёт луч из камеры | Create a ray from the camera"""
        ray = CollisionRay()
        ray_node = CollisionNode(name)
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(BitMask32.bit(mask_bit))
        ray_node.setIntoCollideMask(BitMask32.allOff())

        ray_np = self.camera.attachNewNode(ray_node)
        queue = CollisionHandlerQueue()
        trav = CollisionTraverser()
        trav.addCollider(ray_np, queue)
        return ray, queue, trav

    def cast_ray(self, ray, trav, queue):
        """Запускает луч и возвращает ближайшее попадание | Cast ray and return closest entry"""
        ray.setOrigin(0, 0, 0)
        ray.setDirection(0, 1, 0)

        queue.clearEntries()
        trav.traverse(self.render)

        if queue.getNumEntries() == 0:
            return None

        queue.sortEntries()
        return queue.getEntry(0)

    def init_mouse(self, task):
        """Возвращает курсор в центр экрана | Recenter the mouse cursor"""
        if hasattr(self.win, "movePointer"):
            self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
        return task.done

    def setup_window(self, width, height):
        """Настраивает окно: размер и скрытый курсор | Setup window: size and hidden cursor"""
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setSize(width, height)
        self.win.requestProperties(props)

    def bind_movement_keys(self, player):
        """Привязывает WASD игрока | Bind WASD movement keys"""
        for key in player.keys:
            self.accept(key, player.set_key, [key, True])
            self.accept(f"{key}-up", player.set_key, [key, False])

    def clear_modifier_buttons(self):
        """Убирает модификаторы у кнопок | Clear modifier buttons"""
        if self.mouseWatcherNode is not None:
            self.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        if self.buttonThrowers is not None:
            for thrower in self.buttonThrowers:
                thrower.node().set_modifier_buttons(ModifierButtons())

    def is_shift_down(self, mouse_watcher):
        """Зажат ли Shift | Is Shift held"""
        if mouse_watcher is None:
            return False
        return (
            mouse_watcher.isButtonDown(KeyboardButton.lshift())
            or mouse_watcher.isButtonDown(KeyboardButton.rshift())
        )

    def update_grounding(self, player):
        """Определяет приземление по лучу к земле | Detect landing with ground ray"""
        self.ground_queue.clearEntries()
        self.ground_trav.traverse(self.render)

        player.is_grounded = False

        if self.ground_queue.getNumEntries() > 0:
            self.ground_queue.sortEntries()
            entry = self.ground_queue.getEntry(0)
            z = entry.getSurfacePoint(self.render).getZ()
            if player.root.getZ() <= z + GROUND_TOLERANCE and player.velocity_z <= 0:
                player.is_grounded = True
                player.root.setZ(z)
                player.velocity_z = 0