# camera.py
# -------------------------------------------------------------------
# Simple free-flying FPS-style camera.
# -------------------------------------------------------------------

import math
import pygame
from OpenGL.GL import glRotatef, glTranslatef


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 30.0
        self.z = 0.0

        self.yaw = 45.0
        self.pitch = -20.0

    def apply(self):
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(-self.x, -self.y, -self.z)

    def update(self, keys, dt):
        speed = 10.0
        look_speed = 90.0

        if keys[pygame.K_w]:
            self.x += math.sin(math.radians(self.yaw)) * speed * dt
            self.z -= math.cos(math.radians(self.yaw)) * speed * dt
        if keys[pygame.K_s]:
            self.x -= math.sin(math.radians(self.yaw)) * speed * dt
            self.z += math.cos(math.radians(self.yaw)) * speed * dt

        if keys[pygame.K_a]:
            self.x -= math.cos(math.radians(self.yaw)) * speed * dt
            self.z -= math.sin(math.radians(self.yaw)) * speed * dt
        if keys[pygame.K_d]:
            self.x += math.cos(math.radians(self.yaw)) * speed * dt
            self.z += math.sin(math.radians(self.yaw)) * speed * dt

        if keys[pygame.K_LEFT]:
            self.yaw -= look_speed * dt
        if keys[pygame.K_RIGHT]:
            self.yaw += look_speed * dt
        if keys[pygame.K_UP]:
            self.pitch -= look_speed * dt
        if keys[pygame.K_DOWN]:
            self.pitch += look_speed * dt

        self.pitch = max(-89.0, min(89.0, self.pitch))
