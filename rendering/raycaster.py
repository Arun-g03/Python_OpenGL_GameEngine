import math
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt
from utils.settings import *
from world.map import MAP_WIDTH, MAP_HEIGHT, MAP_DEPTH  # include depth now


class Raycaster:

    """
    Raycaster class for rendering the game world.
    
    """
    def __init__(self, player, game_map):
        self.player = player
        self.map = game_map
        map_center_x = MAP_WIDTH * TILE_SIZE_M / 2
        map_center_y = MAP_HEIGHT * TILE_SIZE_M / 2
        self.light_pos = (map_center_x, map_center_y)
        self.ray_cosines = [math.cos(-FOV/2 + i * DELTA_ANGLE) for i in range(NUM_RAYS)]

    def cast_ray(self, angle):
        ox, oz = self.player.x / TILE_SIZE_M, self.player.y / TILE_SIZE_M
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
                        return hit_distance * TILE_SIZE_M, wall_side

        return MAX_DEPTH, 'none'

    def draw_3d_floor_grid(self):
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_LINES)

        for z in range(MAP_DEPTH):
            z_pos = z * TILE_SIZE_M
            glVertex3f(0, 0, z_pos)
            glVertex3f(MAP_WIDTH * TILE_SIZE_M, 0, z_pos)

        for x in range(MAP_WIDTH):
            x_pos = x * TILE_SIZE_M
            glVertex3f(x_pos, 0, 0)
            glVertex3f(x_pos, 0, MAP_DEPTH * TILE_SIZE_M)

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
                        self.draw_wall_cube(x * TILE_SIZE_M, y * TILE_SIZE_M, z * TILE_SIZE_M
)

    def draw_wall_cube(self, x, y, z, size=TILE_SIZE_M):
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
        self.draw_sky(player_angle=self.player.angle)
        self.draw_3d_floor_grid()
        self.draw_wall_blocks()
        self.draw_light_source()

    def draw_textured_floor(self):
        glBindTexture(GL_TEXTURE_2D, self.floor_texture_id)
        glBegin(GL_QUADS)
        glColor3f(1, 1, 1)

        for z in range(MAP_DEPTH):
            for x in range(MAP_WIDTH):
                glTexCoord2f(0, 0); glVertex3f(x * TILE_SIZE_M, 0, z * TILE_SIZE_M)
                glTexCoord2f(1, 0); glVertex3f((x + 1) * TILE_SIZE_M, 0, z * TILE_SIZE_M)
                glTexCoord2f(1, 1); glVertex3f((x + 1) * TILE_SIZE_M, 0, (z + 1) * TILE_SIZE_M)
                glTexCoord2f(0, 1); glVertex3f(x * TILE_SIZE_M, 0, (z + 1) * TILE_SIZE_M)

        glEnd()


    def draw_sky(self, player_angle):
        glDisable(GL_DEPTH_TEST)
        glPushMatrix()

        glRotatef(-math.degrees(player_angle), 0, 1, 0)

        glColor3f(0.435, 0.608, 1)
        slices = 32
        stacks = 16
        radius = 2000
        vertical_offset = -1250  

        for i in range(stacks // 2):
            lat0 = math.pi * i / stacks / 2
            lat1 = math.pi * (i + 1) / stacks / 2
            y0 = radius * math.cos(lat0) + vertical_offset
            y1 = radius * math.cos(lat1) + vertical_offset
            r0 = radius * math.sin(lat0)
            r1 = radius * math.sin(lat1)

            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lon = 2 * math.pi * j / slices
                x0 = r0 * math.cos(lon)
                z0 = r0 * math.sin(lon)
                x1 = r1 * math.cos(lon)
                z1 = r1 * math.sin(lon)

                glVertex3f(x0, y0, z0)
                glVertex3f(x1, y1, z1)
            glEnd()

        glPopMatrix()
        glEnable(GL_DEPTH_TEST)


