import pygame
import math
from utils.settings import *
from world.map import game_map, MAP_HEIGHT, MAP_WIDTH, MAP_DEPTH

class Player:
    """
    Base player class
    """
    def __init__(self):
        self.x = TILE_SIZE_M * 1.5
        self.y = TILE_SIZE_M * 1.5
        self.angle = 0
        self.pitch = 0  # in radians
        self.vertical_offset = 0  # for looking up/down
        self.eye_height = TILE_SIZE_M * 0.5  # about halfway up a tile

    def movement(self, delta_time):
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0
        speed = PLAYER_SPEED * delta_time
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        if keys[pygame.K_w]:
            dx += cos_a * speed
            dy += sin_a * speed
        if keys[pygame.K_s]:
            dx -= cos_a * speed
            dy -= sin_a * speed
        if keys[pygame.K_a]:
            dx += sin_a * speed
            dy -= cos_a * speed
        if keys[pygame.K_d]:
            dx -= sin_a * speed
            dy += cos_a * speed

        self.check_wall_collision(dx, dy)


    def check_wall_collision(self, dx, dy):
        scale = 0.1  # prevent clipping too close to wall

        next_x = self.x + dx
        next_y = self.y + dy

        # Check X axis collision
        if not self.is_wall(next_x + scale * math.copysign(1, dx), self.y):
            self.x = next_x

        # Check Y axis collision
        if not self.is_wall(self.x, next_y + scale * math.copysign(1, dy)):
            self.y = next_y

    def is_wall(self, x, z):
        i = int(x / TILE_SIZE_M)
        k = int(z / TILE_SIZE_M)
        y = 0  # collision at ground level

        if 0 <= i < MAP_WIDTH and 0 <= y < MAP_HEIGHT and 0 <= k < MAP_DEPTH:
            return game_map[k][y][i] == 1
        return True  # out of bounds is a wall


    def mouse_control(self):
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        self.angle += mouse_dx * MOUSE_SENSITIVITY
        self.pitch -= mouse_dy * MOUSE_SENSITIVITY  # invert for natural feel

        # Optional clamp
        self.pitch = max(-math.pi / 2, min(math.pi / 2, self.pitch))

            


    def update(self, delta_time):
        self.movement(delta_time)
        self.mouse_control()

