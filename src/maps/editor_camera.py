from src.maps.editor_config import (
    EDITOR_MOUSE_SENSITIVITY,
    EDITOR_CAMERA_DISTANCE,
    EDITOR_CAMERA_HEIGHT,
    EDITOR_CAMERA_PITCH_MIN,
    EDITOR_CAMERA_PITCH_MAX,
    EDITOR_CAMERA_PITCH_DIVISOR,
    EDITOR_CAMERA_ZOOM_DISTANCE_POSITIVE,
    EDITOR_CAMERA_ZOOM_DISTANCE_NEGATIVE,
    EDITOR_CAMERA_ZOOM_HEIGHT,
    EDITOR_CAMERA_LERP_SPEED,
)
from src.systems.camera import CameraController


class EditorCameraController(CameraController):
    def __init__(self, render, player_root, camera):
        """Камера редактора с другими параметрами. | Editor camera with different settings."""
        super().__init__(render, player_root, camera)
        self.mouse_sensitivity = EDITOR_MOUSE_SENSITIVITY
        self.camera_distance = EDITOR_CAMERA_DISTANCE
        self.camera_height = EDITOR_CAMERA_HEIGHT
        self.pitch_min = EDITOR_CAMERA_PITCH_MIN
        self.pitch_max = EDITOR_CAMERA_PITCH_MAX
        self.pitch_divisor = EDITOR_CAMERA_PITCH_DIVISOR
        self.zoom_dist_positive = EDITOR_CAMERA_ZOOM_DISTANCE_POSITIVE
        self.zoom_dist_negative = EDITOR_CAMERA_ZOOM_DISTANCE_NEGATIVE
        self.zoom_height = EDITOR_CAMERA_ZOOM_HEIGHT
        self.lerp_speed = EDITOR_CAMERA_LERP_SPEED