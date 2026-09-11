from pathlib import Path

from panda3d.core import Filename, get_model_path

# ================ Пути | Paths ================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "assets" / "models"          # Директория 3D-моделей | 3D models directory
MAP_FILE = PROJECT_ROOT / "assets" / "map.json"          # Файл карты | Map file
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"            # Директория иконок | Icons directory
GENERATOR_TOOL = PROJECT_ROOT / "tools" / "generate_icons.py"  # Генератор иконок | Icon generator

# Регистрируем пути моделей и иконок в Panda3D (кросс-платформенно) | Register model & icon paths in Panda3D (cross-platform)
get_model_path().prepend_directory(Filename.from_os_specific(str(MODELS_DIR)))
get_model_path().prepend_directory(Filename.from_os_specific(str(ICONS_DIR)))


def panda_path(path):
    """Преобразует путь в формат Panda3D, пригодный для загрузки на любой ОС | Convert a path to a Panda3D-loadable format on any OS"""
    return Filename.from_os_specific(str(path))

# ================ Модели | Models ================
PLAYER_MODEL = "UAL1_Standard.bam"                       # Модель игрока | Player model
PICKUP_MODELS = ("statue.bam", 'chest.bam')              # Имена моделей-предметов подбора в map.json | Pickup model names in map.json
PLAYER_ICON = "player.png"                               # Иконка игрока на миникарте | Player minimap icon

# Модели, которые некорректно рендерятся под освещением сцены (чернеют/невидимы).
# incorrectly under the scene lighting (turn black/invisible). Lighting is disabled for them.
LIGHT_OFF_MODELS = {"droid.bam", "robot_zombie_warrior.bam"}

# ================ Игровые параметры | Game Parameters ================
MAP_SIZE = 50                                    # Размер игрового поля | Game field size
GRAVITY = -25                                    # Гравитация | Gravity
JUMP_POWER = 10                                  # Сила прыжка | Jump power
MOVE_SPEED = 10                                  # Базовая скорость игрока | Player base speed
SPRINT_SPEED_MULTIPLIER = 2                      # Ускорение при беге | Sprint multiplier
MOUSE_SENSITIVITY = 0.15                         # Чувствительность мыши | Mouse sensitivity

# ================ Камера | Camera ================
CAMERA_DISTANCE = 8.5                            # Дистанция камеры от игрока | Camera distance from player
CAMERA_HEIGHT = 1.5                              # Высота камеры | Camera height
CAMERA_PITCH_MIN = -30                           # Минимальный наклон камеры | Minimum camera pitch
CAMERA_PITCH_MAX = 15                            # Максимальный наклон камеры | Maximum camera pitch
CAMERA_TARGET_OFFSET = (1, 0, 2.2)               # Смещение цели камеры | Camera target offset
CAMERA_PITCH_DIVISOR = 80.0                      # Делитель наклона для зума | Pitch divisor for zoom
CAMERA_ZOOM_DISTANCE_POSITIVE = 1.6              # Зум дистанции при взгляде вверх | Distance zoom when looking up
CAMERA_ZOOM_DISTANCE_NEGATIVE = 0.5              # Зум дистанции при взгляде вниз | Distance zoom when looking down
CAMERA_ZOOM_HEIGHT = 0.4                         # Зум высоты | Height zoom
CAMERA_LERP_SPEED = 8.0                          # Скорость сглаживания камеры | Camera lerp speed

# ================ Игрок | Player ================
PLAYER_SCALE = 2                                 # Масштаб игрока | Player scale
PLAYER_HEADING = 180                             # Начальный поворот игрока | Player start heading
PLAYER_COLLISION_CENTER = (0, 0, 1)              # Центр коллайдера игрока | Player collider center
PLAYER_COLLISION_RADIUS = 0.5                    # Радиус коллайдера игрока | Player collider radius

# ================ Предметы и заклинания | Pickups and Spells ================
PICKUP_RANGE = 5                                 # Радиус подбора предмета | Pickup range
PICKUP_RAY_RANGE = 20                            # Дистанция луча подбора | Pickup ray range
SPELL_RANGE = 25                                 # Дистанция заклинания | Spell range

# ================ Физика и графика | Physics and Graphics ================
GROUND_TOLERANCE = 0.05                          # Допуск приземления | Ground tolerance
GROUND_SNAP = 0.6                                # Порог отрыва от земли (спуск) | Ground snap/drop threshold
GROUND_THICKNESS = 0.5                           # Толщина земли | Ground thickness
WINDOW_WIDTH = 1280                              # Ширина окна | Window width
WINDOW_HEIGHT = 720                              # Высота окна | Window height

# ================ Миникарта | Minimap ================
MINIMAP_SIZE = 0.6                                # Размер миникарты | Minimap size
MINIMAP_MARGIN = 0.01                             # Отступ от края экрана | Margin from screen edge
MINIMAP_VIEW_RADIUS = 20                          # Радиус обзора миникарты (зум) | Minimap view radius (zoom)
MINIMAP_BG_ALPHA = 0.7                            # Прозрачность фона | Background transparency
MINIMAP_PLAYER_MARKER_SCALE = 0.05                # Масштаб маркера игрока | Player marker scale
MINIMAP_NPC_MARKER_SCALE = MINIMAP_SIZE / 10      # Масштаб маркера NPC | NPC marker scale
MINIMAP_OBJECT_MARKER_SCALE = MINIMAP_SIZE / 10   # Масштаб маркера объекта | Object marker scale

# ================ Освещение и окружение | Lighting and Environment ================
SHOW_BOUNDS = False                               # Отображение отладочных границ | Show debug bounds
SKY_COLOR = (0.55, 0.75, 1.0)                    # Цвет неба | Sky color
GROUND_COLOR = (0.2, 0.7, 0.2)                   # Цвет земли | Ground color
AMBIENT_COLOR = (0.2, 0.2, 0.2, 1)               # Цвет фонового освещения | Ambient light color
SUN_COLOR = (1, 1, 1, 1)                         # Цвет направленного света | Directional light color
SUN_HPR = (-45, -45, 0)                          # Поворот солнца | Sun rotation