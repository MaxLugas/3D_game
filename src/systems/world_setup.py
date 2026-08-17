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
)

from src.config import (
    MAP_SIZE,
    GROUND_COLOR,
    AMBIENT_COLOR,
    SUN_COLOR,
    SUN_HPR,
    GROUND_THICKNESS,
    PLAYER_COLLISION_CENTER,
    PLAYER_COLLISION_RADIUS,
)


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

    def init_mouse(self, task):
        """Возвращает курсор в центр экрана | Recenter the mouse cursor"""
        if hasattr(self.win, "movePointer"):
            self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
        return task.done