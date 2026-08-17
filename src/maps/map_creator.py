import os
import sys

if __package__ in (None, ""):
    _ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, _ROOT)
    sys.path.insert(0, _SRC)
    os.chdir(_ROOT)

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import *

from src.config import GROUND_TOLERANCE, WINDOW_WIDTH, WINDOW_HEIGHT, SKY_COLOR
from src.maps.editor_config import MODELS_DIR, EDITOR_CAMERA_PITCH
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

        get_model_path().prepend_directory(Filename(os.getcwd()))

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

        for k in self.player.keys:
            self.accept(k, self.player.set_key, [k, True])
            self.accept(f"{k}-up", self.player.set_key, [k, False])

        self.accept("mouse1", self.place_object)
        self.accept("u", self.delete_object)
        self.accept("x", self.save_map)
        self.accept("l", self.load_map)
        self.accept("r", self.set_rotating, [True])
        self.accept("r-up", self.set_rotating, [False])
        self.accept("wheel_up", self.on_wheel, [1])
        self.accept("wheel_down", self.on_wheel, [-1])

        if self.mouseWatcherNode is not None:
            self.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        if self.buttonThrowers is not None:
            for thrower in self.buttonThrowers:
                thrower.node().set_modifier_buttons(ModifierButtons())

        if hasattr(self.win, "requestProperties"):
            props = WindowProperties()
            props.setCursorHidden(True)
            props.setSize(WINDOW_WIDTH, WINDOW_HEIGHT)
            self.win.requestProperties(props)

        self.taskMgr.doMethodLater(0.1, self.init_mouse, "init_mouse")
        self.taskMgr.add(self.update, "update")

    def setup_collision(self):
        """Настройка коллайдеров редактора | Setup editor colliders"""
        self.setup_player_collision()
        self.setup_ground_ray()

    def update(self, task):
        """Обновление редактора каждый кадр | Update editor every frame"""
        dt = globalClock.getDt()

        mw = self.mouseWatcherNode
        if mw is not None:
            self.player.shift_down = (
                mw.isButtonDown(KeyboardButton.lshift())
                or mw.isButtonDown(KeyboardButton.rshift())
            )
            self.camera_controller.update(dt, self.win, mw)
            self.handle_step_rotation(mw)

        self.ground_queue.clearEntries()
        self.ground_trav.traverse(self.render)

        self.player.is_grounded = False

        if self.ground_queue.getNumEntries() > 0:
            self.ground_queue.sortEntries()
            entry = self.ground_queue.getEntry(0)
            z = entry.getSurfacePoint(self.render).getZ()
            if self.player.root.getZ() <= z + GROUND_TOLERANCE and self.player.velocity_z <= 0:
                self.player.is_grounded = True
                self.player.root.setZ(z)
                self.player.velocity_z = 0

        self.player.update_movement(dt)
        self.player.apply_gravity(dt)
        self.player.clamp_position()

        self.collision_trav.traverse(self.render)

        self.refresh_ghost_position()

        return task.cont


if __name__ == "__main__":
    MapCreatorApp().run()