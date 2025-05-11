import math
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *
from PIL import Image
import numpy as np

class Enemy:
    def __init__(self, x, y, sprite_path):
        self.x = x
        self.y = y
        self.texture_id = self.load_texture(sprite_path)
        self.size = TILE_SIZE_M  # Enemy size in world units

        self.frame_size = 64  # assume 64x64 tiles
        self.directions = 8   # 360° / 45°
        self.frames_per_dir = 3  # walk cycle, adjust if needed
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_rate = 10  # frames per update

        self.anim_row = 0  # walk anim row

    def load_texture(self, sprite_path):
        # Load image using PIL
        image = Image.open(sprite_path)
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get image data as bytes
        texture_data = np.array(image)
        width, height = image.size
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        return texture_id

    def render(self, player):
        # Calculate angle between enemy and player
        dx = self.x - player.x
        dy = self.y - player.y
        angle = math.atan2(dy, dx) - player.angle

        # Calculate distance for scaling
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        # Calculate screen position
        proj_height = PROJ_COEFF / (dist + 0.0001)
        scale = proj_height / self.frame_size
        screen_x = WIDTH // 2 + int(math.tan(angle) * PROJ_COEFF)
        
        # Calculate texture coordinates for current frame
        dir_index = int((angle % (2 * math.pi)) / (2 * math.pi / self.directions))
        tex_x = self.current_frame / self.frames_per_dir
        tex_y = dir_index / self.directions
        
        # Enable necessary states
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Set up 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Bind texture and draw sprite
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glColor4f(1, 1, 1, 1)
        
        sprite_width = int(self.frame_size * scale)
        sprite_height = int(self.frame_size * scale)
        
        glBegin(GL_QUADS)
        glTexCoord2f(tex_x, tex_y); glVertex2f(screen_x - sprite_width//2, HEIGHT//2 - sprite_height//2)
        glTexCoord2f(tex_x + 1/self.frames_per_dir, tex_y); glVertex2f(screen_x + sprite_width//2, HEIGHT//2 - sprite_height//2)
        glTexCoord2f(tex_x + 1/self.frames_per_dir, tex_y + 1/self.directions); glVertex2f(screen_x + sprite_width//2, HEIGHT//2 + sprite_height//2)
        glTexCoord2f(tex_x, tex_y + 1/self.directions); glVertex2f(screen_x - sprite_width//2, HEIGHT//2 + sprite_height//2)
        glEnd()
        
        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        # Disable states
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

    def update(self, delta_time):
        self.frame_timer += delta_time * self.frame_rate
        if self.frame_timer >= 1.0:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % self.frames_per_dir
