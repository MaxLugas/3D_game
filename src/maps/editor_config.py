from src.config import PLAYER_MODEL
from src.core.collision_masks import MASK_PICK

# ================ Размещение объектов | Object Placement ================
PLACEMENT_DISTANCE = 6                           # Дистанция размещения | Placement distance
PICK_MASK_BIT = MASK_PICK                        # Бит маски для пикинга объектов | Mask bit for object picking

# ================ Камера редактора | Editor Camera ================
EDITOR_CAMERA_PITCH = -20                        # Начальный наклон камеры | Camera start pitch
EDITOR_CAMERA = {
    "mouse_sensitivity": 0.2,                    # Чувствительность мыши | Mouse sensitivity
    "camera_distance": 8.5,                      # Дистанция камеры от игрока | Camera distance
    "camera_height": 1.5,                        # Высота камеры | Camera height
    "pitch_min": -80,                            # Минимальный наклон камеры | Minimum camera pitch
    "pitch_max": -5,                             # Максимальный наклон камеры | Maximum camera pitch
    "pitch_divisor": 80.0,                       # Делитель наклона для зума | Pitch divisor for zoom
    "zoom_dist_positive": 2.5,                   # Зум дистанции при взгляде вверх | Distance zoom when looking up
    "zoom_dist_negative": 1.0,                   # Зум дистанции при взгляде вниз | Distance zoom when looking down
    "zoom_height": 0.8,                          # Зум высоты | Height zoom
    "lerp_speed": 8.0,                           # Скорость сглаживания камеры | Camera lerp speed
}

# ================ Управление | Controls ================
MODEL_ROTATE_SPEED = 90                          # Скорость вращения модели при удержании R | Model rotate speed while holding R
LIFT_STEP = 0.1                                  # Шаг подъёма модели | Model lift step

# ================ Параметры движения редактора | Editor Movement ================
EDITOR_MOVE_SPEED = 20                           # Скорость движения | Move speed
EDITOR_SPRINT_SPEED_MULTIPLIER = 3               # Ускорение при беге | Sprint multiplier
EDITOR_GRAVITY = -40                             # Гравитация | Gravity

# ================ Цвета превью | Preview Colors ================
GHOST_COLOR = (0.4, 1, 0.4, 1)                   # Цвет призрака (можно размещать) | Ghost color (can place)
GHOST_WARN_COLOR = (1, 1, 0, 1)                  # Цвет предупреждения | Warning color
COLLISION_WARN_COLOR = (1, 0.3, 0.3, 1)          # Цвет запрета размещения | Collision warning color
GHOST_NORMAL_MODELS = (PLAYER_MODEL,)            # Модели без цветной подсветки | Models without color tint