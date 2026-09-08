import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    _ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(_ROOT))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Filename, get_model_path

from src.config import WINDOW_WIDTH, WINDOW_HEIGHT, SKY_COLOR, MODELS_DIR, PROJECT_ROOT
from src.maps.editor_config import EDITOR_CAMERA_PITCH, PICK_MASK_BIT
from src.maps.editor_camera import EditorCameraController
from src.maps.editor_input import EditorInputMixin
from src.maps.editor_map_io import EditorMapIoMixin
from src.maps.editor_models import EditorModelsMixin
from src.maps.editor_player import EditorPlayer
from src.maps.editor_ui import EditorUiMixin
from src.systems.world_setup import WorldSetupMixin


class MapCreatorApp(EditorUiMixin, EditorInputMixin, EditorModelsMixin, EditorMapIoMixin, WorldSetupMixin, ShowBase):
    def __init__(self):
        """Инициализация редактора карт | Initialize map editor"""
        super().__init__()

        get_model_path().prepend_directory(Filename.from_os_specific(str(PROJECT_ROOT)))

        self.disableMouse()
        self.setBackgroundColor(*SKY_COLOR, 1)

        self.setup_lighting()
        self.create_ground_tiles()

        self.player = EditorPlayer(self.render)
        self.camera_controller = EditorCameraController(self.render, self.player.root, self.camera)
        self.camera_controller.pitch = EDITOR_CAMERA_PITCH

        self.models = sorted(f for f in os.listdir(MODELS_DIR) if f.lower().endswith(".bam"))
        self.model_index = 0
        self.current_model = None
        self.placed = []
        self.preview = None
        self.preview_lift = 0.0
        self.notice = ""
        self.heading = 0
        self.rotating = False
        self.pitch = 0
        self.shiftUpWasDown = False
        self.shiftDownWasDown = False
        self.shiftLeftWasDown = False
        self.shiftRightWasDown = False
        self.scaleUpWasDown = False
        self.scaleDownWasDown = False
        self.scale = 1

        self.setup_collision()
        self.setup_ui()

        if self.models:
            self.create_ghost(0)

        self.bind_movement_keys(self.player)

        self.accept("mouse1", self.place_object)
        self.accept("mouse3", self.delete_hovered_object)
        self.accept("x", self.save_map)
        self.accept("l", self.load_map)
        self.accept("r", self.set_rotating, [True])
        self.accept("r-up", self.set_rotating, [False])
        self.accept("wheel_up", self.on_wheel, [1])
        self.accept("wheel_down", self.on_wheel, [-1])

        self.clear_modifier_buttons()

        self.setup_window(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.taskMgr.doMethodLater(0.1, self.init_mouse, "init_mouse")
        self.taskMgr.add(self.update, "update")

    def setup_collision(self):
        """Настройка коллайдеров редактора | Setup editor colliders"""
        self.setup_player_collision()
        self.setup_ground_ray()
        self.pick_ray, self.pick_queue, self.pick_trav = self.create_camera_ray("pickRay", PICK_MASK_BIT)

    def update(self, task):
        """Обновление редактора каждый кадр | Update editor every frame"""
        dt = globalClock.getDt()

        mw = self.mouseWatcherNode
        if mw is not None:
            self.player.shift_down = self.is_shift_down(mw)
            self.camera_controller.update(dt, self.win, mw)
            self.handle_step_rotation(mw)

        self.update_grounding(self.player)

        self.player.update_movement(dt)
        self.player.apply_gravity(dt)
        self.player.clamp_position()

        self.collision_trav.traverse(self.render)

        self.refresh_ghost_position()

        return task.cont


if __name__ == "__main__":
    MapCreatorApp().run()