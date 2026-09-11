from panda3d.core import CollisionTraverser, CollisionHandlerQueue


class NpcManager:
    """
    Общий менеджер NPC: один traverser и очередь для лучей обхода препятствий.
    Shared NPC manager: single traverser and queue for obstacle-avoidance rays.

    Раньше каждый NPC создавал свой CollisionTraverser и обходил сцену отдельно
    (N врагов = N полных обходов за кадр). Теперь обход выполняется один раз.
    """

    def __init__(self, render):
        self.render = render
        self.traverser = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.entities = []

    def register(self, enemy):
        """Регистрирует NPC и его лучи в общем traverser | Register NPC and its rays in the shared traverser"""
        if enemy in self.entities:
            return
        self.entities.append(enemy)
        for node in enemy.avoid_nodes.values():
            self.traverser.addCollider(node, self.queue)

    def unregister(self, enemy):
        """Снимает NPC и его лучи с общего traverser | Unregister NPC and its rays from the shared traverser"""
        if enemy in self.entities:
            self.entities.remove(enemy)
        for node in enemy.avoid_nodes.values():
            self.traverser.removeCollider(node)

    def update(self, player_pos, dt):
        """
        Фаза планирования (лучи), один обход сцены, фаза применения движения.
        Planning phase (rays), one scene traversal, movement apply phase.
        """
        alive = [e for e in self.entities if e.is_alive()]

        moving = []
        for enemy in alive:
            others = [e for e in alive if e is not enemy]
            if enemy.update(player_pos, others):
                moving.append(enemy)

        if not moving:
            return

        self.queue.clearEntries()
        self.traverser.traverse(self.render)

        for enemy in moving:
            enemy.apply_move(dt)
