from src.maps.editor_config import EDITOR_CAMERA
from src.systems.camera import CameraController


class EditorCameraController(CameraController):
    def __init__(self, player_root, camera):
        """Камера редактора с другими параметрами. | Editor camera with different settings."""
        super().__init__(player_root, camera, overrides=EDITOR_CAMERA)