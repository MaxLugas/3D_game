from src.config import SHOW_BOUNDS
from src.core.collision_masks import MASK_PLAYER, MASK_PICK, MASK_OBSTACLE, collide_mask
from src.entities.base_entity import BaseEntity


class PickupItem(BaseEntity):
    def __init__(self, render, loader, model, pos, heading=0, scale=None):
        """Создаёт подбираемый предмет. | Create pickup item."""
        super().__init__(render, model)

        self.model = self.attach_root(
            loader.loadModel(model),
            pos=pos,
            heading=heading,
            scale=scale if scale else 1,
            show_bounds=SHOW_BOUNDS,
        )

        self.add_bounds_collider(
            f"pickup_{id(self.model)}",
            into_mask=collide_mask(MASK_PLAYER, MASK_PICK, MASK_OBSTACLE),
        )

    def is_available(self):
        """Доступен ли предмет для подбора. | Check if item is available."""
        return self.is_alive()

    def destroy(self):
        """Удаляет предмет. | Destroy the item."""
        self.cleanup()
