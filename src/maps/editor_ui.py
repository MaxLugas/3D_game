from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, TextNode, TransparencyAttrib


class EditorUiMixin:
    def setup_ui(self):
        """Создаёт прицел и статус панель | Create crosshair and status panel"""
        cm_cross = CardMaker("crosshair")
        cm_cross.setFrame(-0.01, 0.01, -0.01, 0.01)

        self.crosshair = self.aspect2d.attachNewNode(cm_cross.generate())
        self.crosshair.setColor(1, 1, 1, 1)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair.setBin("fixed", 100)
        self.crosshair.setDepthTest(False)
        self.crosshair.setDepthWrite(False)

        self.status_lines = []
        for i in range(6):
            self.status_lines.append(
                OnscreenText(
                    text="",
                    pos=(-1.3, 0.94 - i * 0.055),
                    align=TextNode.ALeft,
                    scale=0.045,
                    fg=(1, 1, 1, 1),
                    mayChange=True,
                )
            )

    def clear_notice(self, task):
        """Очищает уведомление через 2 секунды | Clear notice after 2 seconds"""
        self.notice = ""
        self.update_ui_text()
        return task.done

    def update_ui_text(self):
        """Обновляет текст статус панели | Update status panel text"""
        total = len(self.models)
        index = self.model_index + 1 if self.models else 0
        lines = [
            f"model: {self.current_model} ({index}/{total})",
            "wheel: switch model  |  Shift+wheel: lift  |  LMB: place  |  R: rotate  |  Shift+[/]: scale  |  U: undo  |  X: save  |  L: load",
            f"rotate horizontal 90°: Shift + Arrow left / Arrow right: {round(self.heading)}",
            f"rotate vertical 90°: Shift + Arrow up / Arrow down: {round(self.pitch)}",
            f"scale: {self.scale}  height: {round(self.preview_lift, 2)}  placed: {len(self.placed)}",
            self.notice,
        ]
        for text, line in zip(self.status_lines, lines):
            text.setText(line)