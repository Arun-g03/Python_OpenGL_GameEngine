import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *

class Raycaster:
    def __init__(self, player, game_map):
        self.player = player
        self.game_map = game_map
        self.floor_texture_id = None
        self.sky_color = (0.5, 0.7, 1.0)  # Light blue sky color

    def set_floor_texture(self, texture_id):
        self.floor_texture_id = texture_id

    def update(self, delta_time):
        # Update any raycaster-specific state if needed
        pass

    def render(self):
        # Draw sky
        self.draw_sky()
        
        # Cast rays and draw walls
        self.cast_rays()
        
        # Draw floor if texture is set
        if self.floor_texture_id:
            self.draw_textured_floor()

    def draw_sky(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        
        # Draw sky dome
        glColor3f(*self.sky_color)
        glBegin(GL_QUADS)
        glVertex3f(-1000, -500, -1000)
        glVertex3f(1000, -500, -1000)
        glVertex3f(1000, 500, -1000)
        glVertex3f(-1000, 500, -1000)
        glEnd()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

    def cast_rays(self):
        # Cast rays for each screen column
        for x in range(WIDTH):
            # Calculate ray angle
            ray_angle = (self.player.angle - FOV/2) + (x * FOV/WIDTH)
            
            # Cast ray
            distance = self.cast_ray(ray_angle)
            
            # Calculate wall height
            wall_height = (TILE_SIZE_M * HEIGHT) / (distance * math.cos(ray_angle - self.player.angle))
            
            # Draw wall slice
            self.draw_wall_slice(x, wall_height)

    def cast_ray(self, angle):
        # Ray starting position
        ray_x = self.player.x
        ray_y = self.player.y
        
        # Ray direction
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)
        
        # DDA variables
        map_x = int(ray_x / TILE_SIZE_M)
        map_y = int(ray_y / TILE_SIZE_M)
        
        # Length of ray from current position to next x or y-side
        side_dist_x = 0
        side_dist_y = 0
        
        # Length of ray from one x or y-side to next x or y-side
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')
        
        # Direction to step in x and y
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1
        
        # Perform DDA
        hit = False
        side = 0  # 0 for x-side, 1 for y-side
        
        while not hit:
            # Jump to next map square
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            # Check if ray has hit a wall
            if 0 <= map_x < len(self.game_map[0][0]) and 0 <= map_y < len(self.game_map[0]):
                if self.game_map[0][map_y][map_x] == 1:
                    hit = True
        
        # Calculate distance to wall
        if side == 0:
            distance = (map_x - ray_x/TILE_SIZE_M + (1 - step_x)/2) / ray_dir_x
        else:
            distance = (map_y - ray_y/TILE_SIZE_M + (1 - step_y)/2) / ray_dir_y
        
        return distance * TILE_SIZE_M

    def draw_wall_slice(self, x, height):
        # Calculate wall slice coordinates
        wall_top = (HEIGHT - height) / 2
        wall_bottom = (HEIGHT + height) / 2
        
        # Draw wall slice
        glColor3f(0.8, 0.8, 0.8)  # Wall color
        glBegin(GL_QUADS)
        glVertex2f(x, wall_top)
        glVertex2f(x + 1, wall_top)
        glVertex2f(x + 1, wall_bottom)
        glVertex2f(x, wall_bottom)
        glEnd()

    def draw_textured_floor(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.floor_texture_id)
        
        # Draw floor
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-1000, 0, -1000)
        glTexCoord2f(100, 0); glVertex3f(1000, 0, -1000)
        glTexCoord2f(100, 100); glVertex3f(1000, 0, 1000)
        glTexCoord2f(0, 100); glVertex3f(-1000, 0, 1000)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)


