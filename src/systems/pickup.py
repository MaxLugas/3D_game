from direct.showbase.MessengerGlobal import messenger

from src.config import PICKUP_RANGE, PICKUP_RAY_RANGE
from src.systems.world_setup import cast_ray


class PickupSystem:
    """
    Система подбора предметов: поиск цели и подбор по E.
    Вычисление цели кэшируется один раз за кадр в update().
    Pickup system: target search and pick by E. Target is cached once per frame.
    """

    def __init__(self, render, player, pickups, pickup_ray, pickup_queue, pickup_trav):
        self.render = render
        self.player = player
        self.pickups = pickups
        self.pickup_ray = pickup_ray
        self.pickup_queue = pickup_queue
        self.pickup_trav = pickup_trav
        self.current_target = None

    def update(self):
        """Обновляет кэшированную цель подбора | Refresh the cached pickup target"""
        self.current_target = self._find_target()

    @property
    def can_pickup_now(self):
        return self.current_target is not None

    def _find_target(self):
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

        entry = cast_ray(self.render, self.pickup_ray, self.pickup_trav, self.pickup_queue)
        if entry is None:
            return None

        hit_np = entry.getIntoNodePath()
        dist = (entry.getSurfacePoint(self.render) - player_pos).length()

        for p in available:
            if hit_np == p.collider and dist <= PICKUP_RAY_RANGE:
                return p
        return None

    def pickup(self):
        """Подбор предмета клавишей E | Pick up item with E key"""
        if self.player.jump_state in ("start", "loop"):
            return
        target = self.current_target
        if target is None:
            return
        target.destroy()
        self.current_target = None
        self.player.play_animation("PickUp_Table")
        messenger.send("item:collected", [target.model_name])