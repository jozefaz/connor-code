# camera.py
from __future__ import annotations
import math
from pygame.locals import K_w, K_s, K_a, K_d, K_SPACE, K_LSHIFT

class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 2.0
        self.z = 6.0

        self.yaw = 0.0
        self.pitch = 0.0

        self.move_speed = 0.15
        self.mouse_sensitivity = 0.15
        self.fly_speed = 0.15

    def apply_mouse(self, dx: float, dy: float) -> None:
        self.yaw += dx * self.mouse_sensitivity
        self.pitch -= dy * self.mouse_sensitivity
        self.pitch = max(-89, min(89, self.pitch))

    def apply_keyboard(self, keys) -> None:
        rad = math.radians(self.yaw)

        fx = math.sin(rad)
        fz = -math.cos(rad)

        rx = math.cos(rad)
        rz = math.sin(rad)

        if keys[K_w]:
            self.x += fx * self.move_speed
            self.z += fz * self.move_speed
        if keys[K_s]:
            self.x -= fx * self.move_speed
            self.z -= fz * self.move_speed
        if keys[K_a]:
            self.x -= rx * self.move_speed
            self.z -= rz * self.move_speed
        if keys[K_d]:
            self.x += rx * self.move_speed
            self.z += rz * self.move_speed

        if keys[K_SPACE]:
            self.y += self.fly_speed
        if keys[K_LSHIFT]:
            self.y -= self.fly_speed

    def apply_gl_transform(self, glRotatef, glTranslatef) -> None:
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(-self.x, -self.y, -self.z)
