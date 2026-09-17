from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from src.systems.world_setup import create_crosshair


class Hud:
    """HUD: прицел, подсказка подбора и счётчик FPS | Hud: crosshair, pickup hint, FPS counter"""

    def __init__(self, aspect2d):
        self.aspect2d = aspect2d
        self.crosshair = create_crosshair(aspect2d)

        self.pickup_hint = OnscreenText(
            text="[E]",
            pos=(0, -0.15),
            scale=0.07,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.pickup_hint.hide()

        self.fps_label = OnscreenText(
            text="",
            pos=(1 / aspect2d.getSx() - 0.02, 0.95),
            align=TextNode.ARight,
            scale=0.05,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.fps_frames = 0
        self.fps_time = 0.0

    def update_fps(self, dt):
        """Обновляет счётчик FPS раз в полсекунды | Update FPS counter every half second"""
        self.fps_frames += 1
        self.fps_time += dt
        if self.fps_time >= 0.5:
            self.fps_label.setText(f"FPS: {round(self.fps_frames / self.fps_time)}")
            self.fps_frames = 0
            self.fps_time = 0.0

    def set_pickup_hint(self, visible):
        """Показывает/скрывает подсказку подбора | Show/hide the pickup hint"""
        if visible:
            self.pickup_hint.show()
        else:
            self.pickup_hint.hide()