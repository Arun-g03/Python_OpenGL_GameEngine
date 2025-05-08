import pygame
import math
from utils.settings import *

class Enemy:
    def __init__(self, x, y, spritesheet):
        self.x = x
        self.y = y
        self.spritesheet = spritesheet

        self.frame_size = 64  # assume 64x64 tiles
        self.directions = 8   # 360° / 45°
        self.frames_per_dir = 3  # walk cycle, adjust if needed
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_rate = 10  # frames per update

        self.anim_row = 0  # walk anim row

    def update(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frame_rate:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % self.frames_per_dir

    def draw(self, screen, player):
        dx = self.x - player.x
        dy = self.y - player.y
        angle = math.atan2(dy, dx) - player.angle

        # convert to screen direction
        dir_index = int((angle % (2 * math.pi)) / (2 * math.pi / self.directions))
        frame_rect = pygame.Rect(
            self.current_frame * self.frame_size,
            dir_index * self.frame_size,
            self.frame_size, self.frame_size
        )

        sprite = self.spritesheet.subsurface(frame_rect)

        # Project on screen
        dist = math.hypot(dx, dy)
        if dist == 0: return
        proj_height = PROJ_COEFF / (dist + 0.0001)
        scale = proj_height / self.frame_size

        sprite = pygame.transform.scale(sprite, (int(self.frame_size * scale), int(self.frame_size * scale)))
        screen_x = WIDTH // 2 + int(math.tan(angle) * PROJ_COEFF)

        screen.blit(sprite, (screen_x - sprite.get_width() // 2, HEIGHT // 2 - sprite.get_height() // 2))
