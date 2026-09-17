from src.entities.player import Player
from src.maps.editor_config import (
    EDITOR_MOVE_SPEED,
    EDITOR_SPRINT_SPEED_MULTIPLIER,
    EDITOR_GRAVITY,
)


class EditorPlayer(Player):
    def __init__(self, render):
        """Игрок редактора: без модели, ускоренный. | Editor player: no model, faster movement."""
        super().__init__(
            render,
            with_model=False,
            move_speed=EDITOR_MOVE_SPEED,
            sprint_multiplier=EDITOR_SPRINT_SPEED_MULTIPLIER,
            gravity=EDITOR_GRAVITY,
        )