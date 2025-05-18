import OpenGL.GL as gl
import math

class Gizmo:
    def __init__(self):
        self.axis_length = 2.0
        self.axis_thickness = 0.05
        self.handle_size = 0.2
        self.selected_axis = None
        self.is_dragging = False
        self.drag_start = None
        self.drag_plane = None

    def draw(self, position, rotation=(0,0,0)):
        gl.glPushMatrix()
        gl.glTranslatef(position[0], position[1], position[2])
        gl.glRotatef(math.degrees(rotation[0]), 1, 0, 0)
        gl.glRotatef(math.degrees(rotation[1]), 0, 1, 0)
        gl.glRotatef(math.degrees(rotation[2]), 0, 0, 1)
        # Draw axes and handles (implementation omitted for brevity)
        gl.glPopMatrix()

    def handle_mouse(self, mouse_pos, mouse_dx, mouse_dy, camera):
        # Handle mouse interaction with gizmo
        pass 