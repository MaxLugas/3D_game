# ================ Уничтожаемые NPC | Destroyable enemies ================
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class NpcSettings:
    """Параметры NPC | NPC parameters"""
    aggro_distance: float = 10                          # Дистанция активации преследования | Distance to trigger chase
    attack_distance: float = 1                          # Дистанция начала атаки | Distance to start attacking
    run_speed: float = 9                                # Скорость бега | Run speed
    separation_distance: float = 1.5                    # Дистанция разделения NPC | NPC separation distance
    avoid_lookahead: float = 3.0                        # Дистанция обнаружения препятствий | Obstacle lookahead distance
    avoid_spacing: float = 0.9                          # Расстояние между лучами обхода | Ray spacing for avoidance
    avoid_strength: float = 2.0                         # Сила уклонения от препятствий | Obstacle avoidance strength
    anims: dict = field(default_factory=dict)           # Имена анимаций | Animation names


DEFAULTS = NpcSettings()

NPCS = {
    "droid.bam": NpcSettings(
        anims={
            "idle": "Idle",
            "aggro": "Berserker_Call",
            "run": "Running_03",
            "attack": "Attack_02",
        },
    ),
    "robot_zombie_warrior.bam": NpcSettings(
        anims={
            "idle": "Alert",
            "aggro": "Skill_01",
            "run": "Running",
            "attack": "Skill_03",
        },
    ),
}

NPC_MODELS = tuple(NPCS)


def npc_config(model):
    """Конфиг NPC по модели с общими значениями | NPC config by model with defaults"""
    model_settings = NPCS.get(model)
    if model_settings is None:
        return DEFAULTS
    if model_settings.anims:
        return replace(DEFAULTS, anims=dict(model_settings.anims))
    return DEFAULTS