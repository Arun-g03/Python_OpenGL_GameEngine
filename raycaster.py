import math
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt
from settings import *
from map import MAP_WIDTH, MAP_HEIGHT, MAP_DEPTH  # include depth now


class Raycaster:
    def __init__(self, player, game_map):
        self.player = player
        self.map = game_map
        map_center_x = MAP_WIDTH * TILE / 2
        map_center_y = MAP_HEIGHT * TILE / 2
        self.light_pos = (map_center_x, map_center_y)
        self.ray_cosines = [math.cos(-FOV/2 + i * DELTA_ANGLE) for i in range(NUM_RAYS)]

    def cast_ray(self, angle):
        ox, oz = self.player.x / TILE, self.player.y / TILE
        map_x, map_z = int(ox), int(oz)

        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        delta_dist_x = abs(1 / cos_a) if cos_a != 0 else float('inf')
        delta_dist_z = abs(1 / sin_a) if sin_a != 0 else float('inf')

        step_x = 1 if cos_a >= 0 else -1
        step_z = 1 if sin_a >= 0 else -1

        side_dist_x = (map_x + 1 - ox if step_x > 0 else ox - map_x) * delta_dist_x
        side_dist_z = (map_z + 1 - oz if step_z > 0 else oz - map_z) * delta_dist_z

        for _ in range(MAX_DEPTH):
            if side_dist_x < side_dist_z:
                map_x += step_x
                side_dist_x += delta_dist_x
                hit_distance = side_dist_x - delta_dist_x
                wall_side = 'vertical'
            else:
                map_z += step_z
                side_dist_z += delta_dist_z
                hit_distance = side_dist_z - delta_dist_z
                wall_side = 'horizontal'

            if 0 <= map_x < MAP_WIDTH and 0 <= map_z < MAP_DEPTH:
                for y in range(MAP_HEIGHT):
                    if self.map[map_z][y][map_x] == 1:
                        return hit_distance * TILE, wall_side

        return MAX_DEPTH, 'none'

    def draw_3d_floor_grid(self):
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_LINES)
        for z in range(0, MAP_DEPTH * TILE, TILE):
            glVertex3f(0, 0, z)
            glVertex3f(MAP_WIDTH * TILE, 0, z)
        for x in range(0, MAP_WIDTH * TILE, TILE):
            glVertex3f(x, 0, 0)
            glVertex3f(x, 0, MAP_DEPTH * TILE)
        glEnd()

    def draw_light_source(self):
        light_screen_x = WIDTH // 2
        light_screen_y = HEIGHT // 2 - int(self.player.vertical_offset)

        glBegin(GL_POINTS)
        glColor3f(1.0, 1.0, 0.4)
        glVertex2f(light_screen_x, light_screen_y)
        glEnd()

    def draw_wall_blocks(self):
        for z in range(MAP_DEPTH):
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    if self.map[z][y][x] == 1:
                        self.draw_wall_cube(x * TILE, y * TILE, z * TILE)

    def draw_wall_cube(self, x, y, z, size=TILE):
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_QUADS)

        # Front face
        glVertex3f(x, y, z)
        glVertex3f(x + size, y, z)
        glVertex3f(x + size, y + size, z)
        glVertex3f(x, y + size, z)

        # Back face
        glVertex3f(x, y, z + size)
        glVertex3f(x + size, y, z + size)
        glVertex3f(x + size, y + size, z + size)
        glVertex3f(x, y + size, z + size)

        # Left
        glVertex3f(x, y, z)
        glVertex3f(x, y, z + size)
        glVertex3f(x, y + size, z + size)
        glVertex3f(x, y + size, z)

        # Right
        glVertex3f(x + size, y, z)
        glVertex3f(x + size, y, z + size)
        glVertex3f(x + size, y + size, z + size)
        glVertex3f(x + size, y + size, z)

        # Top
        glVertex3f(x, y + size, z)
        glVertex3f(x + size, y + size, z)
        glVertex3f(x + size, y + size, z + size)
        glVertex3f(x, y + size, z + size)

        # Bottom
        glVertex3f(x, y, z)
        glVertex3f(x + size, y, z)
        glVertex3f(x + size, y, z + size)
        glVertex3f(x, y, z + size)

        glEnd()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        cam_x = self.player.x
        cam_y = self.player.eye_height
        cam_z = self.player.y

        dir_x = math.cos(self.player.angle)
        dir_z = math.sin(self.player.angle)
        dir_y = math.tan(self.player.pitch)  # look up/down by pitching the view

        gluLookAt(
            cam_x, cam_y, cam_z,
            cam_x + dir_x, cam_y + dir_y, cam_z + dir_z,
            0, 1, 0
        )

        self.draw_3d_floor_grid()
        self.draw_wall_blocks()
        self.draw_light_source()
