import OpenGL.GL as gl
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
import math

class EditorViewport:
    def __init__(self, x, y, width, height, camera):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.camera = camera
        self.grid_visible = True
        self.grid_size = 1
        self.grid_color = (0.3, 0.3, 0.3)  # Dark gray color for grid

    def draw_grid(self):
        if not self.grid_visible:
            return

        glDisable(GL_DEPTH_TEST)
        glColor3f(*self.grid_color)
        glBegin(GL_LINES)
        
        # Draw grid lines
        size = 20  # Grid size in world units
        step = self.grid_size
        
        # Draw lines along X axis
        for z in range(-size, size + 1, step):
            glVertex3f(-size, 0, z)
            glVertex3f(size, 0, z)
        
        # Draw lines along Z axis
        for x in range(-size, size + 1, step):
            glVertex3f(x, 0, -size)
            glVertex3f(x, 0, size)
        
        glEnd()
        glEnable(GL_DEPTH_TEST)

    def draw(self, draw_world_callback=None):
        # Set OpenGL viewport and draw 3D scene
        gl.glViewport(self.x, self.y, self.width, self.height)
        
        # Clear the viewport
        gl.glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark gray background
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = self.width / self.height if self.height != 0 else 1
        gluPerspective(60, aspect, 0.1, 1000.0)
        
        # Set up view matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        if self.camera:
            self.camera.apply_view()
        
        # Draw the grid first (it will be at the bottom of the scene)
        self.draw_grid()
        
        # Draw the rest of the world
        if draw_world_callback:
            draw_world_callback() 