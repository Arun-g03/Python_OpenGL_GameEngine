import OpenGL.GL as gl
import math
import numpy as np
from pyrr import Vector3, Matrix44

class Gizmo:
    def __init__(self):
        self.axis_length = 2.0
        self.axis_thickness = 0.05
        self.handle_size = 0.2
        self.selected_axis = None
        self.is_dragging = False
        self.drag_start = None
        self.drag_plane = None
        self.transform_mode = "translate"  # "translate", "rotate", or "scale"
        
        # Colors for each axis
        self.colors = {
            "x": (1.0, 0.0, 0.0),  # Red
            "y": (0.0, 1.0, 0.0),  # Green
            "z": (0.0, 0.0, 1.0)   # Blue
        }
        
        # Handle positions for each axis
        self.handles = {
            "x": (self.axis_length, 0, 0),
            "y": (0, self.axis_length, 0),
            "z": (0, 0, self.axis_length)
        }

    def draw(self, position, rotation=(0,0,0)):
        gl.glPushMatrix()
        gl.glTranslatef(position[0], position[1], position[2])
        gl.glRotatef(math.degrees(rotation[0]), 1, 0, 0)
        gl.glRotatef(math.degrees(rotation[1]), 0, 1, 0)
        gl.glRotatef(math.degrees(rotation[2]), 0, 0, 1)
        
        # Draw axes
        for axis, color in self.colors.items():
            # Set color for this axis
            gl.glColor3f(*color)
            
            # Draw axis line
            gl.glLineWidth(3.0)
            gl.glBegin(gl.GL_LINES)
            gl.glVertex3f(0, 0, 0)
            gl.glVertex3f(*self.handles[axis])
            gl.glEnd()
            
            # Draw handle
            if self.transform_mode == "translate":
                self._draw_translate_planes()
                self._draw_translate_handle(axis)
            elif self.transform_mode == "rotate":
                self._draw_rotate_handle(axis)
            elif self.transform_mode == "scale":
                self._draw_scale_handle(axis)
        
        gl.glPopMatrix()
        

    def _draw_translate_handle(self, axis):
        # Draw arrow head
        gl.glPushMatrix()
        gl.glTranslatef(*self.handles[axis])
        
        # Draw cone for arrow head
        gl.glBegin(gl.GL_TRIANGLES)
        if axis == "x":
            gl.glVertex3f(0, 0, 0)
            gl.glVertex3f(-0.2, 0.1, 0)
            gl.glVertex3f(-0.2, -0.1, 0)
        elif axis == "y":
            gl.glVertex3f(0, 0, 0)
            gl.glVertex3f(0.1, -0.2, 0)
            gl.glVertex3f(-0.1, -0.2, 0)
        elif axis == "z":
            gl.glVertex3f(0, 0, 0)
            gl.glVertex3f(0.1, 0, -0.2)
            gl.glVertex3f(-0.1, 0, -0.2)
        gl.glEnd()
        
        gl.glPopMatrix()

    def _draw_rotate_handle(self, axis):
        gl.glPushMatrix()
        # No translation, rings are centered
        segments = 64
        radius = self.axis_length * 0.9
        gl.glLineWidth(3.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            if axis == "x":
                gl.glVertex3f(0, radius * math.cos(angle), radius * math.sin(angle))
            elif axis == "y":
                gl.glVertex3f(radius * math.cos(angle), 0, radius * math.sin(angle))
            elif axis == "z":
                gl.glVertex3f(radius * math.cos(angle), radius * math.sin(angle), 0)
        gl.glEnd()
        gl.glPopMatrix()

    def _draw_scale_handle(self, axis):
        # Draw cube for scale handle
        gl.glPushMatrix()
        gl.glTranslatef(*self.handles[axis])
        
        size = self.handle_size / 2
        gl.glBegin(gl.GL_QUADS)
        # Front face
        gl.glVertex3f(-size, -size, size)
        gl.glVertex3f(size, -size, size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(-size, size, size)
        # Back face
        gl.glVertex3f(-size, -size, -size)
        gl.glVertex3f(-size, size, -size)
        gl.glVertex3f(size, size, -size)
        gl.glVertex3f(size, -size, -size)
        # Top face
        gl.glVertex3f(-size, size, -size)
        gl.glVertex3f(-size, size, size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(size, size, -size)
        # Bottom face
        gl.glVertex3f(-size, -size, -size)
        gl.glVertex3f(size, -size, -size)
        gl.glVertex3f(size, -size, size)
        gl.glVertex3f(-size, -size, size)
        # Right face
        gl.glVertex3f(size, -size, -size)
        gl.glVertex3f(size, size, -size)
        gl.glVertex3f(size, size, size)
        gl.glVertex3f(size, -size, size)
        # Left face
        gl.glVertex3f(-size, -size, -size)
        gl.glVertex3f(-size, -size, size)
        gl.glVertex3f(-size, size, size)
        gl.glVertex3f(-size, size, -size)
        gl.glEnd()
        
        gl.glPopMatrix()

    def _draw_translate_planes(self):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        # XY plane (cyan)
        gl.glColor4f(0, 1, 1, 0.3)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.axis_length * 0.7, 0, 0)
        gl.glVertex3f(self.axis_length * 0.7, self.axis_length * 0.7, 0)
        gl.glVertex3f(0, self.axis_length * 0.7, 0)
        gl.glEnd()
        # YZ plane (yellow)
        gl.glColor4f(1, 1, 0, 0.3)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, self.axis_length * 0.7, 0)
        gl.glVertex3f(0, self.axis_length * 0.7, self.axis_length * 0.7)
        gl.glVertex3f(0, 0, self.axis_length * 0.7)
        gl.glEnd()
        # XZ plane (magenta)
        gl.glColor4f(1, 0, 1, 0.3)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(self.axis_length * 0.7, 0, 0)
        gl.glVertex3f(self.axis_length * 0.7, 0, self.axis_length * 0.7)
        gl.glVertex3f(0, 0, self.axis_length * 0.7)
        gl.glEnd()
        gl.glDisable(gl.GL_BLEND)

    def handle_mouse(self, mouse_pos, mouse_dx, mouse_dy, camera, viewport_width, viewport_height):
        if not self.is_dragging:
            # Check if mouse is over any handle
            for axis, handle_pos in self.handles.items():
                if self._is_mouse_over_handle(mouse_pos, handle_pos, camera, viewport_width, viewport_height):
                    self.selected_axis = axis
                    self.drag_start = mouse_pos
                    return True
            self.selected_axis = None
            return False
        else:
            # Handle dragging
            if self.transform_mode == "translate":
                return self._handle_translate(mouse_dx, mouse_dy, camera)
            elif self.transform_mode == "rotate":
                return self._handle_rotate(mouse_dx, mouse_dy, camera)
            elif self.transform_mode == "scale":
                return self._handle_scale(mouse_dx, mouse_dy, camera)
            return False

    def _is_mouse_over_handle(self, mouse_pos, handle_pos, camera, viewport_width, viewport_height):
        # Convert handle position to screen space
        handle_screen = self._world_to_screen(handle_pos, camera, viewport_width, viewport_height)
        
        # Check if mouse is within handle bounds
        mouse_x, mouse_y = mouse_pos
        handle_x, handle_y = handle_screen
        
        distance = math.sqrt((mouse_x - handle_x)**2 + (mouse_y - handle_y)**2)
        return distance < 15  # Increased threshold for easier selection

    def _world_to_screen(self, world_pos, camera, viewport_width, viewport_height):
        # Convert world position to screen coordinates
        view = camera.get_view_matrix()
        proj = camera.get_projection_matrix(viewport_width, viewport_height)
        
        # Transform world position to clip space
        clip_pos = proj @ view @ np.array([*world_pos, 1.0])
        
        # Convert to screen coordinates
        screen_x = (clip_pos[0] / clip_pos[3] + 1.0) * viewport_width / 2
        screen_y = (1.0 - clip_pos[1] / clip_pos[3]) * viewport_height / 2
        
        return (screen_x, screen_y)

    def _handle_translate(self, mouse_dx, mouse_dy, camera):
        # Calculate movement in world space based on selected axis
        movement = Vector3([0, 0, 0])
        sensitivity = 0.1
        
        if self.selected_axis == "x":
            movement[0] = mouse_dx * sensitivity
        elif self.selected_axis == "y":
            movement[1] = -mouse_dy * sensitivity
        elif self.selected_axis == "z":
            movement[2] = mouse_dx * sensitivity
            
        return movement

    def _handle_rotate(self, mouse_dx, mouse_dy, camera):
        # Calculate rotation based on selected axis
        rotation = Vector3([0, 0, 0])
        sensitivity = 0.1
        
        if self.selected_axis == "x":
            rotation[0] = mouse_dy * sensitivity
        elif self.selected_axis == "y":
            rotation[1] = mouse_dx * sensitivity
        elif self.selected_axis == "z":
            rotation[2] = mouse_dx * sensitivity
            
        return rotation

    def _handle_scale(self, mouse_dx, mouse_dy, camera):
        # Calculate scale factor based on selected axis
        scale = Vector3([1, 1, 1])
        sensitivity = 0.01
        
        if self.selected_axis == "x":
            scale[0] = 1 + mouse_dx * sensitivity
        elif self.selected_axis == "y":
            scale[1] = 1 - mouse_dy * sensitivity
        elif self.selected_axis == "z":
            scale[2] = 1 + mouse_dx * sensitivity
            
        return scale

    def set_transform_mode(self, mode):
        if mode in ["translate", "rotate", "scale"]:
            self.transform_mode = mode
            self.selected_axis = None
            self.is_dragging = False 