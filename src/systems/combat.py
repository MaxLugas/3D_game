from src.config import SPELL_RANGE
from src.systems.world_setup import cast_ray


class CombatSystem:
    """Боевая система: заклинание игрока и попадания по NPC | Combat: player spell and NPC hits"""

    def __init__(self, render, camera, player, npc_enemies, spell_ray, spell_queue, spell_trav):
        self.render = render
        self.camera = camera
        self.player = player
        self.npc_enemies = npc_enemies
        self.spell_ray = spell_ray
        self.spell_queue = spell_queue
        self.spell_trav = spell_trav

    def on_shoot(self):
        """Обработчик выстрела | Shoot handler"""
        self.player.shoot(on_spell_hit=self.perform_shot)

    def perform_shot(self):
        """Проверка попадания заклинания в NPC | Check spell hit against NPCs"""
        alive = [d for d in self.npc_enemies if d.is_alive()]
        if not alive:
            return

        entry = cast_ray(self.render, self.spell_ray, self.spell_trav, self.spell_queue)
        if entry is None:
            return

        hit_np = entry.getIntoNodePath()
        dist = (entry.getSurfacePoint(self.render) - self.camera.getPos(self.render)).length()

        for enemy in alive:
            if hit_np == enemy.collider and dist <= SPELL_RANGE:
                enemy.die()
                break