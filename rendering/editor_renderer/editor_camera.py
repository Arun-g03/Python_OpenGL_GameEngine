import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluUnProject, gluPerspective
from utils.settings import *
from pyrr import Matrix44, Vector3

    


EDITOR_WIDTH = 32
EDITOR_HEIGHT = 8
EDITOR_DEPTH = 32

class EditorCamera:
    def __init__(self):
        self.pos = [EDITOR_WIDTH * TILE_SIZE_M / 2, 10.0, EDITOR_DEPTH * TILE_SIZE_M / 2]
        self.pitch = math.pi/6
        self.yaw = 0
        self.roll = 0
        self.speed = 10.0
        self.mouse_sensitivity = 0.005
        self.fast_speed = 20.0
        self.slow_speed = 10.0
        self.selected_entity = None
        self.transform_mode = "translate"
        self.grid_size = 1
        self.placement_pos = None
        self.placement_normal = None
        self.fly_mode = True  # Always fly mode
        self.last_mouse_pos = None
        self.selected_object = None  # Add selected_object property

    def update(self, dt, keys, mouse_dx, mouse_dy, mouse_pos, mouse_wheel=0):
        # Speed control
        if keys.get('LEFT_CONTROL'):
            self.speed = self.fast_speed
        else:
            self.speed = self.slow_speed

        # Mouse look (hold right mouse button)
        if mouse_dx != 0 or mouse_dy != 0:
            sensitivity = self.mouse_sensitivity
            self.yaw += mouse_dx * sensitivity
            self.pitch -= mouse_dy * sensitivity

            # Clamp pitch to just under ±90°
            max_pitch = math.radians(89.0)
            self.pitch = max(-max_pitch, min(max_pitch, self.pitch))

            # Wrap yaw
            self.yaw = self.yaw % (2 * math.pi)

        # Calculate movement vectors based on current rotation
        forward = [
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
            math.sin(self.yaw) * math.cos(self.pitch)
        ]
        right = [
            -math.sin(self.yaw),
            0,
            math.cos(self.yaw)
        ]
        up = [0, 1, 0]

        # Apply movement
        velocity = self.speed * dt
        if keys.get('W'):
            self.pos = [p + f * velocity for p, f in zip(self.pos, forward)]
        if keys.get('S'):
            self.pos = [p - f * velocity for p, f in zip(self.pos, forward)]
        if keys.get('A'):
            self.pos = [p - r * velocity for p, r in zip(self.pos, right)]
        if keys.get('D'):
            self.pos = [p + r * velocity for p, r in zip(self.pos, right)]
        if keys.get('SPACE'):
            self.pos = [p + u * velocity for p, u in zip(self.pos, up)]
        if keys.get('LEFT_SHIFT'):
            self.pos = [p - u * velocity for p, u in zip(self.pos, up)]
        if keys.get('E'):
            self.pos = [p + u * velocity for p, u in zip(self.pos, up)]
        if keys.get('Q'):
            self.pos = [p - u * velocity for p, u in zip(self.pos, up)]

        # Mouse wheel for fast forward/backward
        if mouse_wheel != 0:
            self.pos = [p + f * mouse_wheel * self.speed * 0.5 for p, f in zip(self.pos, forward)]

        # Only print if values have changed
        if not hasattr(self, '_last_pos') or self.pos != self._last_pos or \
           not hasattr(self, '_last_yaw') or self.yaw != self._last_yaw or \
           not hasattr(self, '_last_pitch') or self.pitch != self._last_pitch or \
           not hasattr(self, '_last_speed') or self.speed != self._last_speed:
            
            # Store current values
            self._last_pos = self.pos.copy() if hasattr(self.pos, 'copy') else self.pos
            self._last_yaw = self.yaw
            self._last_pitch = self.pitch
            self._last_speed = self.speed

    def apply_view(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Calculate look direction based on yaw and pitch
        look_x = self.pos[0] + math.cos(self.yaw) * math.cos(self.pitch)
        look_y = self.pos[1] + math.sin(self.pitch)
        look_z = self.pos[2] + math.sin(self.yaw) * math.cos(self.pitch)
        
        # Apply camera transformation
        gluLookAt(
            self.pos[0], self.pos[1], self.pos[2],  # Camera position
            look_x, look_y, look_z,                 # Look at point
            0, 1, 0                                 # Up vector
        )

    

    def get_ray_from_mouse(self, mouse_pos, viewport_width, viewport_height):
        x = int(mouse_pos[0])
        y = int(viewport_height - mouse_pos[1])  # Flip Y for OpenGL

        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        # Unproject near and far points
        near = gluUnProject(x, y, 0.0, modelview, projection, viewport)
        far  = gluUnProject(x, y, 1.0, modelview, projection, viewport)

        origin = np.array(near, dtype=np.float32)
        direction = np.array(far, dtype=np.float32) - origin
        direction = direction / np.linalg.norm(direction)

        return origin, direction

    def get_view_projection_matrices(self, viewport_width, viewport_height):
        cam_pos = Vector3(self.pos)
        forward = Vector3([
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
            math.sin(self.yaw) * math.cos(self.pitch)
        ])

        view = Matrix44.look_at(cam_pos, cam_pos + forward, Vector3([0.0, 1.0, 0.0]))
        projection = Matrix44.perspective_projection(
            60.0, viewport_width / viewport_height, 0.1, 1000.0
        )

        return view, projection

    def get_view_and_projection(self, viewport_width, viewport_height):
        """Alias for get_view_projection_matrices to maintain compatibility"""
        return self.get_view_projection_matrices(viewport_width, viewport_height)

    def get_view_matrix(self):
        """Get the current view matrix"""
        cam_pos = Vector3(self.pos)
        forward = Vector3([
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
            math.sin(self.yaw) * math.cos(self.pitch)
        ])
        return Matrix44.look_at(cam_pos, cam_pos + forward, Vector3([0.0, 1.0, 0.0]))

    def get_projection_matrix(self, viewport_width, viewport_height):
        """Get the current projection matrix"""
        return Matrix44.perspective_projection(
            60.0, viewport_width / viewport_height, 0.1, 1000.0
        )