# ================ Пути | Paths ================
MODELS_DIR = "assets/models"                     # Директория 3D-моделей | 3D models directory
MAP_FILE = "assets/map.json"                     # Файл карты | Map file

# ================ Размещение объектов | Object Placement ================
PLACEMENT_DISTANCE = 6                           # Дистанция размещения | Placement distance

# ================ Камера редактора | Editor Camera ================
EDITOR_CAMERA_PITCH = -20                        # Наклон камеры | Camera pitch
EDITOR_MOVE_SPEED = 20                           # Скорость движения | Move speed
EDITOR_SPRINT_SPEED_MULTIPLIER = 3               # Ускорение при беге | Sprint multiplier
EDITOR_GRAVITY = -40                             # Гравитация | Gravity
EDITOR_MOUSE_SENSITIVITY = 0.2                   # Чувствительность мыши | Mouse sensitivity
EDITOR_CAMERA_DISTANCE = 1                       # Дистанция камеры от игрока | Camera distance from player
EDITOR_CAMERA_HEIGHT = 0                         # Высота камеры | Camera height
EDITOR_CAMERA_PITCH_MIN = -80                    # Минимальный наклон камеры | Minimum camera pitch
EDITOR_CAMERA_PITCH_MAX = -5                     # Максимальный наклон камеры | Maximum camera pitch
EDITOR_CAMERA_TARGET_OFFSET = (0, 0, 0)          # Смещение цели камеры | Camera target offset
EDITOR_CAMERA_PITCH_DIVISOR = 80.0               # Делитель наклона для зума | Pitch divisor for zoom
EDITOR_CAMERA_ZOOM_DISTANCE_POSITIVE = 2.5       # Зум дистанции при взгляде вверх | Distance zoom when looking up
EDITOR_CAMERA_ZOOM_DISTANCE_NEGATIVE = 1.0       # Зум дистанции при взгляде вниз | Distance zoom when looking down
EDITOR_CAMERA_ZOOM_HEIGHT = 0.8                  # Зум высоты | Height zoom
EDITOR_CAMERA_LERP_SPEED = 8.0                   # Скорость сглаживания камеры | Camera lerp speed

# ================ Управление | Controls ================
MODEL_ROTATE_SPEED = 90                          # Скорость вращения модели при удержании R | Model rotate speed while holding R
LIFT_STEP = 0.1                                  # Шаг подъёма модели | Model lift step

# ================ Цвета превью | Preview Colors ================
GHOST_COLOR = (0.4, 1, 0.4, 1)                   # Цвет призрака (можно размещать) | Ghost color (can place)
GHOST_WARN_COLOR = (1, 1, 0, 1)                  # Цвет предупреждения | Warning color
COLLISION_WARN_COLOR = (1, 0.3, 0.3, 1)          # Цвет запрета размещения | Collision warning color
GHOST_NORMAL_MODELS = ("UAL1_Standard.bam",)     # Модели без цветной подсветки | Models without color tint