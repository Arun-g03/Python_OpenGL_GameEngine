import math
import pygame

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt

class EditorCamera:
    def __init__(self):
        self.pos = [0.0, 2.0, 5.0]
        self.pitch = 0
        self.yaw = 0
        self.speed = 5.0

    def update(self, dt, keys, mouse_dx, mouse_dy):
        self.yaw += mouse_dx * 0.002
        self.pitch -= mouse_dy * 0.002
        self.pitch = max(-math.pi/2, min(math.pi/2, self.pitch))

        forward = [
            math.cos(self.yaw),
            math.tan(self.pitch),
            math.sin(self.yaw)
        ]
        right = [
            -forward[2], 0, forward[0]
        ]

        velocity = self.speed * dt
        if keys[pygame.K_w]: self.pos = [p + f * velocity for p, f in zip(self.pos, forward)]
        if keys[pygame.K_s]: self.pos = [p - f * velocity for p, f in zip(self.pos, forward)]
        if keys[pygame.K_a]: self.pos = [p - r * velocity for p, r in zip(self.pos, right)]
        if keys[pygame.K_d]: self.pos = [p + r * velocity for p, r in zip(self.pos, right)]

    def apply_view(self):
        dir_x = math.cos(self.yaw)
        dir_z = math.sin(self.yaw)
        dir_y = math.tan(self.pitch)
        gluLookAt(
            *self.pos,
            self.pos[0] + dir_x, self.pos[1] + dir_y, self.pos[2] + dir_z,
            0, 1, 0
        )
