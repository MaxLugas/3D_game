from direct.actor.Actor import Actor


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