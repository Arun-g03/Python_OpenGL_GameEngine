import pygame
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *

class Enemy:
    def __init__(self, x, y, sprite_sheet):
        self.x = x
        self.y = y
        self.sprite_sheet = sprite_sheet
        self.texture_id = self.load_texture()
        self.size = TILE_SIZE_M  # Enemy size in world units

        self.frame_size = 64  # assume 64x64 tiles
        self.directions = 8   # 360° / 45°
        self.frames_per_dir = 3  # walk cycle, adjust if needed
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_rate = 10  # frames per update

        self.anim_row = 0  # walk anim row

    def load_texture(self):
        # Convert pygame surface to OpenGL texture
        texture_data = pygame.image.tostring(self.sprite_sheet, "RGBA", True)
        width, height = self.sprite_sheet.get_size()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        return texture_id

    def render(self):
        # Calculate screen position based on player's view
        # This is a simple billboard rendering
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glColor4f(1, 1, 1, 1)
        
        # Draw enemy as a billboard (always facing the camera)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(self.x - self.size/2, 0, self.y - self.size/2)
        glTexCoord2f(1, 0); glVertex3f(self.x + self.size/2, 0, self.y - self.size/2)
        glTexCoord2f(1, 1); glVertex3f(self.x + self.size/2, self.size, self.y - self.size/2)
        glTexCoord2f(0, 1); glVertex3f(self.x - self.size/2, self.size, self.y - self.size/2)
        glEnd()
        
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

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

        sprite = self.sprite_sheet.subsurface(frame_rect)

        # Project on screen
        dist = math.hypot(dx, dy)
        if dist == 0: return
        proj_height = PROJ_COEFF / (dist + 0.0001)
        scale = proj_height / self.frame_size

        sprite = pygame.transform.scale(sprite, (int(self.frame_size * scale), int(self.frame_size * scale)))
        screen_x = WIDTH // 2 + int(math.tan(angle) * PROJ_COEFF)

        screen.blit(sprite, (screen_x - sprite.get_width() // 2, HEIGHT // 2 - sprite.get_height() // 2))
