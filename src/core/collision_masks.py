from panda3d.core import BitMask32

# ================ Биты масок коллайдеров | Collision mask bits ================
MASK_PLAYER = 1                                       # Игрок и земля | Player and ground
MASK_PICK = 2                                         # Пик объектов в редакторе | Editor pick ray
MASK_OBSTACLE = 2                                     # Препятствия (для врагов и обхода) | Obstacles (enemies + avoidance)


def collide_mask(*bits):
    """Создаёт CollisionMask из набора битов | Create a CollisionMask from a set of bits"""
    mask = BitMask32.allOff()
    for b in bits:
        mask |= BitMask32.bit(b)
    return mask
