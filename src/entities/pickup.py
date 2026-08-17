import os

from panda3d.core import CollisionNode, CollisionBox, Point3, BitMask32

from config import SHOW_BOUNDS
from config import OBSTACLE_MASK_BIT
from src.maps.editor_config import MODELS_DIR


class PickupItem:
    def __init__(self, render, loader, pos, heading=0, scale=None):
        """Создаёт подбираемый предмет (статуя). | Create pickup item (statue)."""
        self.render = render

        self.model = loader.loadModel(os.path.join(MODELS_DIR, "statue.bam"))
        self.model.reparentTo(render)
        scale = scale if scale else 1
        self.model.setScale(scale)
        self.model.setPos(pos)
        self.model.setH(heading)
        if SHOW_BOUNDS:
            self.model.showBounds()

        node = CollisionNode("yellowCube")
        # Коллайдер строится из размеров модели, как для статичных объектов | Collider built from model bounds, like for static objects
        lmin, lmax = self.model.getTightBounds(self.model)
        center = (lmin + lmax) * 0.5
        half = (lmax - lmin) * 0.5
        node.addSolid(CollisionBox(Point3(center.x, center.y, center.z), half.x, half.y, half.z))
        node.setIntoCollideMask(BitMask32.bit(1) | BitMask32.bit(2) | BitMask32.bit(OBSTACLE_MASK_BIT))

        self.collider = self.model.attachNewNode(node)

    def is_available(self):
        """Доступен ли предмет для подбора. | Check if item is available."""
        return not self.model.isEmpty()

    def destroy(self):
        """Удаляет предмет. | Destroy the item."""
        self.model.removeNode()

    def get_position(self):
        """Возвращает текущую позицию предмета. | Returns current item position."""
        return self.model.getPos(self.render)
