from panda3d.core import Vec3
from src.config import (
    MOUSE_SENSITIVITY,
    CAMERA_DISTANCE,
    CAMERA_HEIGHT,
    CAMERA_PITCH_MIN,
    CAMERA_PITCH_MAX,
    CAMERA_TARGET_OFFSET,
    CAMERA_PITCH_DIVISOR,
    CAMERA_ZOOM_DISTANCE_POSITIVE,
    CAMERA_ZOOM_DISTANCE_NEGATIVE,
    CAMERA_ZOOM_HEIGHT,
    CAMERA_LERP_SPEED,
)

PARAM_NAMES = (
    "mouse_sensitivity", "camera_distance", "camera_height",
    "pitch_min", "pitch_max", "pitch_divisor",
    "zoom_dist_positive", "zoom_dist_negative", "zoom_height", "lerp_speed",
)

DEFAULT_CAMERA_PARAMS = {
    "mouse_sensitivity": MOUSE_SENSITIVITY,
    "camera_distance": CAMERA_DISTANCE,
    "camera_height": CAMERA_HEIGHT,
    "pitch_min": CAMERA_PITCH_MIN,
    "pitch_max": CAMERA_PITCH_MAX,
    "pitch_divisor": CAMERA_PITCH_DIVISOR,
    "zoom_dist_positive": CAMERA_ZOOM_DISTANCE_POSITIVE,
    "zoom_dist_negative": CAMERA_ZOOM_DISTANCE_NEGATIVE,
    "zoom_height": CAMERA_ZOOM_HEIGHT,
    "lerp_speed": CAMERA_LERP_SPEED,
}


class CameraController:
    def __init__(self, render, player_root, camera, overrides=None):
        """Создаёт иерархию камеры вокруг игрока | Create camera hierarchy around player"""
        self.camera = camera
        self.player_root = player_root

        params = dict(DEFAULT_CAMERA_PARAMS)
        if overrides:
            params.update(overrides)
        for name in PARAM_NAMES:
            setattr(self, name, params[name])

        self.camera_target = player_root.attachNewNode("camera_target")
        self.camera_target.setPos(*CAMERA_TARGET_OFFSET)

        self.camera_yaw = self.camera_target.attachNewNode("camera_yaw")
        self.camera_pitch = self.camera_yaw.attachNewNode("camera_pitch")
        self.camera_arm = self.camera_pitch.attachNewNode("camera_arm")

        self.camera.reparentTo(self.camera_arm)
        self.camera.setPos(0, -self.camera_distance, self.camera_height)

        self.yaw = 0
        self.pitch = 0

    def update(self, dt, win, mouse_watcher):
        """Обновление камеры: поворот мышью и плавный зум | Update camera: mouse look and smooth zoom"""
        if mouse_watcher.hasMouse():
            pointer = win.getPointer(0)

            center_x = win.getXSize() // 2
            center_y = win.getYSize() // 2

            dx = pointer.getX() - center_x
            dy = pointer.getY() - center_y

            self.yaw -= dx * self.mouse_sensitivity
            self.pitch -= dy * self.mouse_sensitivity
            self.pitch = max(self.pitch_min, min(self.pitch_max, self.pitch))

            win.movePointer(0, center_x, center_y)

        self.player_root.setH(self.yaw)
        self.camera_pitch.setP(self.pitch)

        pitch = self.pitch / self.pitch_divisor

        if pitch > 0:
            target_distance = self.camera_distance - pitch * self.zoom_dist_positive
        else:
            target_distance = self.camera_distance - pitch * self.zoom_dist_negative

        target_height = self.camera_height + pitch * self.zoom_height

        target = Vec3(0, -target_distance, target_height)
        current = self.camera.getPos()
        self.camera.setPos(current + (target - current) * min(self.lerp_speed * dt, 1.0))