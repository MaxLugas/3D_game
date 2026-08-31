from direct.actor.Actor import Actor
from panda3d.core import CollisionNode, CollisionBox, Point3, BitMask32

from src.config import LIGHT_OFF_MODELS


def model_basename(name):
    """Сравнивает название модели без пути и регистра | Model name without path, lowercased"""
    return name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def apply_world_render(node, name):
    """
    Отключает освещение для моделей, которые некорректно отображаются под светом (см. LIGHT_OFF_MODELS)
    Disable lighting for models that render incorrectly under lighting (see LIGHT_OFF_MODELS)
    """
    if model_basename(name) in LIGHT_OFF_MODELS:
        node.setLightOff()
    return node


def pose_t_pose(actor, anims):
    """Ставит актёра в T-позу | Pose the actor in T-pose"""
    tpose = next(
        (a for a in anims if "tpose" in a.lower().replace("_", "") or "t_pose" in a.lower()),
        None,
    )
    if tpose is not None:
        actor.pose(tpose, 0)


def load_model_or_actor(loader, path):
    """Загружает модель, а если есть персонаж — актёра с анимациями | Load model, or actor with animations if character found"""
    node = loader.loadModel(path)
    if node.findAllMatches("**/+Character").getNumPaths() == 0:
        return node
    node.removeNode()
    try:
        actor = Actor(path)
        anims = actor.getAnimNames()
        if anims:
            pose_t_pose(actor, anims)
        return actor
    except Exception:
        return loader.loadModel(path)


def create_bounds_collider(node, name, into_mask, from_mask=BitMask32.allOff()):
    """Создаёт коллайдер-коробку по границам модели | Create box collider from model bounds"""
    lmin, lmax = node.getTightBounds(node)
    center = (lmin + lmax) * 0.5
    half = (lmax - lmin) * 0.5
    collision = CollisionNode(name)
    collision.addSolid(CollisionBox(Point3(center.x, center.y, center.z), half.x, half.y, half.z))
    collision.setIntoCollideMask(into_mask)
    collision.setFromCollideMask(from_mask)
    return collision