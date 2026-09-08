# 🎮 Panda3D Game

**Комиксная игра на Panda3D с анимированными персонажами и встроенным редактором карт**  
*A comic-book styled game built on Panda3D with animated characters and a built-in map editor*

---

## 🛠️ Технологии / Tech Stack

| Русский | English |
|---------|---------|
| **Python**: 3.12 | **Python**: 3.12 |
| **Движок**: [Panda3D](https://www.panda3d.org/) 1.10.16 | **Engine**: [Panda3D](https://www.panda3d.org/) 1.10.16 |
| **Рендеринг**: panda3d-simplepbr (PBR) | **Rendering**: panda3d-simplepbr (PBR) |
| **Конвертация**: panda3d-gltf (GLB → BAM) | **Conversion**: panda3d-gltf (GLB → BAM) |
| **Анимации**: Panda3D Actor system (BAM) | **Animation**: Panda3D Actor system (BAM) |
| **Карта**: JSON с группировкой объектов по моделям | **Map**: JSON with objects grouped by model |
| **Коллайдеры**: Автоматически по `getTightBounds` | **Colliders**: Auto-generated from `getTightBounds` |

## 🌟 Особенности / Features

| Русский                                                          | English                                               |
|------------------------------------------------------------------|-------------------------------------------------------|
| 🎮 Игрок: WASD, бег, прыжки, заклинания, подбор предметов        | 🎮 Player: WASD, sprint, jumping, spells, item pickup |
| 👾 NPC-враги: патрулирование, агрессия, уклонение от препятствий | 👾 NPCs Enemy: patrol, aggro, obstacle avoidance      |
| 🗿 Статуи-предметы: подбор по расстоянию или лучу                | 🗿 Statue pickups: collect by distance or ray         |
| 🗺️ Встроенный редактор карт с сохранением в `assets/map.json`   | 🗺️ Built-in map editor saving to `assets/map.json`   |
| 🎨 Автоколлайдеры: подбор размеров по границам модели            | 🎨 Auto-colliders: sized from model bounds            |
| 🐾 Separation — NPC не слипаются друг с другом                   | 🐾 Separation — NPCs avoid overlapping each other     |

## ⚙️ Конфигурация / Configuration

Настройки разнесены по категориям в отдельные файлы | Settings are split into categorized files:

| Файл / File | Содержимое / Contents                         |
|-------------|-----------------------------------------------|
| `src/config.py` | Игра, камера, игрок, физика, визуал           | Game, camera, player, physics, visuals |
| `src/core/npc_config.py` | Параметры NPC | Droid params |
| `src/core/objects_config.py` | Модели объектов мира                          | World object models |
| `src/maps/editor_config.py` | Настройки редактора карт                      | Map editor settings |

**Примеры настроек / Configuration examples:**
```python
# src/config.py
MOVE_SPEED = 10            # Скорость игрока | Player speed
GRAVITY = -25              # Гравитация | Gravity
CAMERA_DISTANCE = 8.5      # Дистанция камеры | Camera distance
SHOW_BOUNDS = True         # Отладочные границы | Debug bounds

# src/core/npc_config.py
DROID_AGGRO_DISTANCE = 8   # Дистанция агрессии | Aggro distance
DROID_RUN_SPEED = 6        # Скорость бега | Run speed
```

## 🗺️ Формат карты / Map Format

`assets/map.json` хранит объекты, сгруппированные по именам моделей | stores objects grouped by model name:

```json
{
  "objects": {
    "statue.bam": [
      { "pos": [1.56, 10.07, 1.0], "heading": 357, "pitch": 0, "scale": 1 }
    ],
    "house.bam": [
      { "pos": [16.14, 6.42, 1.0], "heading": 0, "pitch": 0, "scale": 1 }
    ]
  }
}
```

Модели автоматически распознаются по имени: `Droid.bam` → враг-дроид, `statue.bam` → предмет подбора, остальные → статичные объекты.
Models are auto-detected by name: `Droid.bam` → enemy droid, `statue.bam` → pickup, others → static objects.

## 🚀 Установка и запуск / Setup & Run

### Требования / Requirements
- Python 3.12
- Panda3D 1.10.16

### Инструкция / Instructions

```bash
# 1. Клонировать репозиторий | Clone repo
git clone ...
cd project_folder

# 2. Создать виртуальное окружение | Create venv
python -m venv venv

# 3. Активировать виртуальное окружение | Activate venv
Windows:      venv\Scripts\activate
Linux:        . venv/bin/activate

# 4. Установить зависимости | Install dependencies
pip install -r requirements.txt

# 5. Запустить игру | Launch the game
python src/main.py

# 6. Открыть редактор карт | Open the map editor
python src/maps/map_creator.py
```

## 🔧 Инструменты / Tools

| Скрипт / Script | Назначение / Purpose |
|-----------------|----------------------|
| `tools/convert_glb.py` | Конвертация GLB в BAM | Convert GLB to BAM (`python tools/convert_glb.py model.glb`) |
| `tools/test_anim.py` | Просмотр анимаций моделей | Model animation viewer (LMB: rotate, ↑/↓: next/prev anim, Tab: frame mode) |

## 📂 Структура проекта / Project Structure
```
project/
├── assets/
│   ├── models/               # 3D-модели | 3D models
│   ├── icons/                # Иконки для редактора | Editor icons
│   ├── audio/                # Звуковые эффекты | Sound effects
│   └── map.json              # Карта объектов | Object map
├── src/
│   ├── main.py               # Точка входа в игру | Game entry point
│   ├── config.py             # Настройки игры | Game configuration
│   ├── core/
│   │   ├── app.py            # Инициализация игры и сцены | Game and scene setup
│   │   ├── npc_config.py     # Настройки дроидов | Droid configuration
│   │   └── objects_config.py # Настройки объектов мира | World objects configuration
│   ├── entities/
│   │   ├── player.py         # Игрок | Player
│   │   ├── droid.py          # Дроиды-враги | Enemy droids
│   │   └── pickup.py         # Предметы подбора | Pickups
│   ├── maps/
│   │   ├── map_loader.py     # Загрузка карты из JSON | JSON map loader
│   │   ├── map_creator.py    # Редактор карт | Map editor
│   │   ├── editor_*.py       # Модули редактора | Editor modules
│   │   └── model_loader.py   # Загрузка моделей по имени | Model loading by name
│   └── systems/
│       ├── world_setup.py    # Создание мира (земля, свет, коллайдеры) | World setup (ground, lights, colliders)
│       └── camera.py         # Камера игрока | Player camera
├── tools/                    # Утилиты разработчика | Developer utilities
└── requirements.txt          # Зависимости | Dependencies
```

---

## 📜 Лицензия / License

Этот проект распространяется под лицензией **MIT**.
This project is licensed under the **MIT License**.

---

## 📬 Контакты / Contact

📧 **Email**: [maxim.lugovsky@gmail.com](mailto:maxim.lugovsky@gmail.com)  
💬 **Telegram**: [@mxm_lugas](https://t.me/mxm_lugas)  
📱 **WhatsApp**: [+972 55-257-5915](https://wa.me/972552575915)