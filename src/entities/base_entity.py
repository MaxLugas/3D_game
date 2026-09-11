from panda3d.core import BitMask32

from src.maps.model_loader import create_bounds_collider


class BaseEntity:
    """
    Общая основа сущностей: корневой узел, коллайдер, позиция и очистка.
    Shared entity base: root node, collider, position and cleanup.
    """

    def __init__(self, render, model=None):
        self.render = render
        self.model_name = model
        self.root = None
        self.collider = None

    def attach_root(self, node, pos=(0, 0, 0), heading=0, scale=1, show_bounds=False):
        """Привязывает узел сцены и задаёт трансформации | Attach scene node and set transforms"""
        self.root = node
        node.reparentTo(self.render)
        if scale is not None:
            node.setScale(scale)
        node.setPos(*pos)
        if heading:
            node.setH(heading)
        if show_bounds:
            node.showBounds()
        return node

    def add_bounds_collider(self, name, into_mask, from_mask=BitMask32.allOff()):
        """Создаёт и крепит коллайдер по границам модели | Create and attach bounds collider"""
        collider_node = create_bounds_collider(self.root, name, into_mask, from_mask)
        self.collider = self.root.attachNewNode(collider_node)
        return self.collider

    def get_position(self):
        """Текущая мировая позиция сущности | Current world position of the entity"""
        return self.root.getPos(self.render)

    def is_alive(self):
        """Существует ли узел сущности | Whether the entity node still exists"""
        return self.root is not None and not self.root.isEmpty()

    def cleanup(self):
        """Удаляет узел сущности из сцены | Remove the entity node from the scene"""
        if self.is_alive():
            self.root.removeNode()
        self.root = None
        self.collider = None
