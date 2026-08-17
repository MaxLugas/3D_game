from panda3d.core import KeyboardButton

from src.maps.editor_config import LIFT_STEP


class EditorInputMixin:
    def on_wheel(self, direction):
        """Обработка колеса: смена модели или подъём. | Handle wheel: switch model or lift."""
        mw = self.mouseWatcherNode
        shift_down = mw is not None and (
            mw.isButtonDown(KeyboardButton.lshift())
            or mw.isButtonDown(KeyboardButton.rshift())
        )
        if shift_down:
            self.preview_lift += direction * LIFT_STEP
            self.update_ui_text()
        elif direction > 0:
            self.next_model()
        else:
            self.prev_model()

    def set_rotating(self, value):
        """Включает/выключает вращение модели. | Enable/disable model rotation."""
        self.rotating = value

    def handle_step_rotation(self, mw):
        """Пошаговый поворот на 90° и масштаб клавишами. | Step rotation by 90° and scale keys."""
        shift_down = (
            mw.isButtonDown(KeyboardButton.lshift())
            or mw.isButtonDown(KeyboardButton.rshift())
        )

        changed = False

        if shift_down and mw.isButtonDown(KeyboardButton.up()):
            if not self.shiftUpWasDown:
                self.pitch = (self.pitch - 90) % 360
                self.shiftUpWasDown = True
                changed = True
        elif shift_down and mw.isButtonDown(KeyboardButton.down()):
            if not self.shiftDownWasDown:
                self.pitch = (self.pitch + 90) % 360
                self.shiftDownWasDown = True
                changed = True
        elif shift_down and mw.isButtonDown(KeyboardButton.left()):
            if not self.shiftLeftWasDown:
                self.heading = (self.heading - 90) % 360
                self.shiftLeftWasDown = True
                changed = True
        elif shift_down and mw.isButtonDown(KeyboardButton.right()):
            if not self.shiftRightWasDown:
                self.heading = (self.heading + 90) % 360
                self.shiftRightWasDown = True
                changed = True
        elif mw.isButtonDown(KeyboardButton.ascii_key(b"[")):
            if not self.scaleDownWasDown:
                self.scale = max(0.1, round(self.scale - 0.1, 1))
                self.scaleDownWasDown = True
                changed = True
        elif mw.isButtonDown(KeyboardButton.ascii_key(b"]")):
            if not self.scaleUpWasDown:
                self.scale = min(100, round(self.scale + 0.1, 1))
                self.scaleUpWasDown = True
                changed = True
        else:
            self.shiftUpWasDown = False
            self.shiftDownWasDown = False
            self.shiftLeftWasDown = False
            self.shiftRightWasDown = False
            self.scaleDownWasDown = False
            self.scaleUpWasDown = False

        if changed:
            self.update_ui_text()