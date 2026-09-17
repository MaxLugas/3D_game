from pathlib import Path

from direct.actor.Actor import Actor
from panda3d.core import CollisionNode, CollisionBox, Point3, BitMask32


def load_lod(loader, path, lod="LOD0"):
    """Загружает модель и оставляет только один уровень детализации | Load model and keep only one LOD level"""
    node = loader.loadModel(path)
    if not node.getChildren():
        return node
    base = Path(path).stem

    lod_nodes = {}
    for child in node.getChildren():
        name = child.getName()
        if name.startswith(f"{base}_LOD"):
            lod_nodes[name.rsplit("_", 1)[-1]] = child

    if not lod_nodes:
        return node

    if lod not in lod_nodes:
        fallback = next((lvl for lvl in ("LOD2", "LOD1", "LOD0") if lvl in lod_nodes), None)
        if fallback is not None and fallback != lod:
            print(f"[warn] LOD '{lod}' не найден в {path}, используется '{fallback}'")
            lod = fallback

    for child in node.getChildren():
        if child != lod_nodes[lod]:
            child.hide()
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


def create_mesh_collider(node, name, into_mask, from_mask=BitMask32.allOff()):
    """Назначает геометрию самой низкой LOD как коллайдер | Use lowest LOD geometry as collider"""
    base = Path(str(node)).stem if hasattr(node, 'getTag') else ""
    best = None
    for child in node.getChildren():
        child_name = child.getName()
        if "_LOD" in child_name:
            level = child_name.rsplit("_", 1)[-1]
            try:
                lvl_num = int(level.replace("LOD", ""))
            except ValueError:
                continue
            if best is None or lvl_num > int(best.getName().rsplit("_", 1)[-1].replace("LOD", "")):
                best = child

    if best is None:
        best = node

    best.setCollideMask(into_mask)
    best.setName(name)
    return best
