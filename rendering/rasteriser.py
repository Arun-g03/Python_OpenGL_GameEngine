import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt, gluNewQuadric, gluSphere, gluDeleteQuadric
from utils.settings import WIDTH, HEIGHT
import glfw
import time

class Rasteriser:
    def __init__(self):
        # Camera parameters
        self.camera_pos = [WIDTH // 2, 10, HEIGHT // 2]
        self.camera_yaw = 0
        self.camera_pitch = -math.pi/6
        self.fov = 60
        self.aspect = WIDTH / HEIGHT
        self.near = 0.1
        self.far = 1000.0
        # Demo entities
        self.entities = [
            {"type": "cube", "position": (5, 1, 5), "size": 2},
            {"type": "sphere", "position": (10, 1, 10), "radius": 1.5}
        ]
        self.floor_texture = None

    def set_camera(self, pos, yaw, pitch):
        self.camera_pos = list(pos)
        self.camera_yaw = yaw
        self.camera_pitch = pitch

    def set_floor_texture(self, texture):
        self.floor_texture = texture

    def draw_cube(self, position, size):
        x, y, z = position
        s = size / 2.0
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(s, s, s)
        glColor3f(0.8, 0.2, 0.2)
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-1, -1,  1)
        glVertex3f( 1, -1,  1)
        glVertex3f( 1,  1,  1)
        glVertex3f(-1,  1,  1)
        # Back
        glVertex3f(-1, -1, -1)
        glVertex3f(-1,  1, -1)
        glVertex3f( 1,  1, -1)
        glVertex3f( 1, -1, -1)
        # Left
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, -1,  1)
        glVertex3f(-1,  1,  1)
        glVertex3f(-1,  1, -1)
        # Right
        glVertex3f( 1, -1, -1)
        glVertex3f( 1,  1, -1)
        glVertex3f( 1,  1,  1)
        glVertex3f( 1, -1,  1)
        # Top
        glVertex3f(-1,  1, -1)
        glVertex3f(-1,  1,  1)
        glVertex3f( 1,  1,  1)
        glVertex3f( 1,  1, -1)
        # Bottom
        glVertex3f(-1, -1, -1)
        glVertex3f( 1, -1, -1)
        glVertex3f( 1, -1,  1)
        glVertex3f(-1, -1,  1)
        glEnd()
        glPopMatrix()

    def draw_sphere(self, position, radius, slices=16, stacks=16):
        x, y, z = position
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(0.2, 0.2, 0.8)
        quad = gluNewQuadric()
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)
        glPopMatrix()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, self.near, self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Camera look direction
        look_x = self.camera_pos[0] + math.cos(self.camera_yaw) * math.cos(self.camera_pitch)
        look_y = self.camera_pos[1] + math.sin(self.camera_pitch)
        look_z = self.camera_pos[2] + math.sin(self.camera_yaw) * math.cos(self.camera_pitch)
        gluLookAt(
            self.camera_pos[0], self.camera_pos[1], self.camera_pos[2],
            look_x, look_y, look_z,
            0, 1, 0
        )
        glEnable(GL_DEPTH_TEST)
        # Draw demo entities
        for entity in self.entities:
            if entity["type"] == "cube":
                self.draw_cube(entity["position"], entity["size"])
            elif entity["type"] == "sphere":
                self.draw_sphere(entity["position"], entity["radius"])
        if self.floor_texture:
            glBindTexture(GL_TEXTURE_2D, self.floor_texture)

def main():
    if not glfw.init():
        print("Failed to initialize GLFW")
        return
    window = glfw.create_window(WIDTH, HEIGHT, "OpenGL Rasteriser", None, None)
    if not window:
        glfw.terminate()
        print("Failed to create window")
        return
    glfw.make_context_current(window)
    glfw.swap_interval(1)

    rasteriser = Rasteriser()
    last_time = time.time()
    mouse_look = False
    last_mouse = None
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    def cursor_pos_callback(window, xpos, ypos):
        global mouse_dx, mouse_dy, last_mouse_pos, skip_mouse_delta, suppress_input
        if mouse_look and last_mouse is not None:
            dx = xpos - last_mouse[0]
            dy = ypos - last_mouse[1]
            rasteriser.camera_yaw += dx * 0.002
            rasteriser.camera_pitch -= dy * 0.002
            rasteriser.camera_pitch = max(-math.pi/2, min(math.pi/2, rasteriser.camera_pitch))
        last_mouse = (xpos, ypos)

    glfw.set_cursor_pos_callback(window, cursor_pos_callback)

    while not glfw.window_should_close(window):
        now = time.time()
        dt = now - last_time
        last_time = now

        # Camera movement
        speed = 10.0 * dt
        if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS:
            speed *= 2
        forward = [
            math.cos(rasteriser.camera_yaw) * math.cos(rasteriser.camera_pitch),
            math.sin(rasteriser.camera_pitch),
            math.sin(rasteriser.camera_yaw) * math.cos(rasteriser.camera_pitch)
        ]
        right = [-math.sin(rasteriser.camera_yaw), 0, math.cos(rasteriser.camera_yaw)]
        up = [0, 1, 0]
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            rasteriser.camera_pos = [p + f * speed for p, f in zip(rasteriser.camera_pos, forward)]
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            rasteriser.camera_pos = [p - f * speed for p, f in zip(rasteriser.camera_pos, forward)]
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            rasteriser.camera_pos = [p - r * speed for p, r in zip(rasteriser.camera_pos, right)]
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            rasteriser.camera_pos = [p + r * speed for p, r in zip(rasteriser.camera_pos, right)]
        if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
            rasteriser.camera_pos = [p + u * speed for p, u in zip(rasteriser.camera_pos, up)]
        if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
            rasteriser.camera_pos = [p - u * speed for p, u in zip(rasteriser.camera_pos, up)]

        # Mouse look toggle (hold right mouse button)
        if glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            mouse_look = True
        else:
            mouse_look = False
            last_mouse = None

        # Render
        rasteriser.render()
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main() 