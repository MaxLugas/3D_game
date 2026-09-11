# ================ Уничтожаемые NPC | Destroyable enemies ================

NPC_DEFAULTS = {
    "aggro_distance": 10,                          # Дистанция активации преследования | Distance to trigger chase
    "attack_distance": 1,                          # Дистанция начала атаки | Distance to start attacking
    "run_speed": 9,                                # Скорость бега | Run speed
    "separation_distance": 1.5,                    # Дистанция разделения NPC | NPC separation distance
    "avoid_lookahead": 3.0,                        # Дистанция обнаружения препятствий | Obstacle lookahead distance
    "avoid_spacing": 0.9,                          # Расстояние между лучами обхода | Ray spacing for avoidance
    "avoid_strength": 2.0,                         # Сила уклонения от препятствий | Obstacle avoidance strength
}

NPCS = {
    "droid.bam" : {
        "anims": {
            "idle": "Idle",
            "aggro": "Berserker_Call",
            "run": "Running_03",
            "attack": "Attack_02",
        },
    },
    "robot_zombie_warrior.bam": {
        "anims": {
            "idle": "Alert",
            "aggro": "Skill_01",
            "run": "Running",
            "attack": "Skill_03",
        },
    },
}

NPC_MODELS = tuple(NPCS)


def npc_config(model):
    """Конфиг NPC по модели с общими значениями | NPC config by model with defaults"""
    config = dict(NPC_DEFAULTS)
    config.update(NPCS.get(model, {}))
    return config