import glfw
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
        self.keys = set()  # Store currently pressed keys

    def movement(self, delta_time):
        dx, dy = 0, 0
        speed = PLAYER_SPEED * delta_time
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        if glfw.KEY_W in self.keys:
            dx += cos_a * speed
            dy += sin_a * speed
        if glfw.KEY_S in self.keys:
            dx -= cos_a * speed
            dy -= sin_a * speed
        if glfw.KEY_A in self.keys:
            dx += sin_a * speed
            dy -= cos_a * speed
        if glfw.KEY_D in self.keys:
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

    def mouse_control(self, mouse_dx, mouse_dy):
        self.angle += mouse_dx * MOUSE_SENSITIVITY
        self.pitch -= mouse_dy * MOUSE_SENSITIVITY  # invert for natural feel

        # Optional clamp
        self.pitch = max(-math.pi / 2, min(math.pi / 2, self.pitch))

    def update(self, delta_time, mouse_dx, mouse_dy):
        self.movement(delta_time)
        self.mouse_control(mouse_dx, mouse_dy)

    def key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            self.keys.add(key)
        elif action == glfw.RELEASE:
            self.keys.discard(key)

