import os

from panda3d.core import BitMask32

from src.config import SHOW_BOUNDS, OBSTACLE_MASK_BIT, MODELS_DIR, PICKUP_MODEL
from src.maps.model_loader import create_bounds_collider


class PickupItem:
    def __init__(self, render, loader, pos, heading=0, scale=None):
        """Создаёт подбираемый предмет (статуя). | Create pickup item (statue)."""
        self.render = render

        self.model = loader.loadModel(os.path.join(MODELS_DIR, PICKUP_MODEL))
        self.model.reparentTo(render)
        scale = scale if scale else 1
        self.model.setScale(scale)
        self.model.setPos(pos)
        self.model.setH(heading)
        if SHOW_BOUNDS:
            self.model.showBounds()

        collider_node = create_bounds_collider(
            self.model,
            f"pickup_{id(self.model)}",
            into_mask=BitMask32.bit(1) | BitMask32.bit(2) | BitMask32.bit(OBSTACLE_MASK_BIT),
        )

        self.collider = self.model.attachNewNode(collider_node)

    def is_available(self):
        """Доступен ли предмет для подбора. | Check if item is available."""
        return not self.model.isEmpty()

    def destroy(self):
        """Удаляет предмет. | Destroy the item."""
        self.model.removeNode()

    def get_position(self):
        """Возвращает текущую позицию предмета. | Returns current item position."""
        return self.model.getPos(self.render)