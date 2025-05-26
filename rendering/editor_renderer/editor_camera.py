import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluUnProject, gluPerspective
from utils.settings import *

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

    def get_ray_from_mouse(self, mouse_pos):
        # Convert mouse position to normalized device coordinates
        x = (2.0 * mouse_pos[0]) / WIDTH - 1.0
        y = 1.0 - (2.0 * mouse_pos[1]) / HEIGHT
        z = 1.0
        ray_clip = np.array([x, y, z, 1.0])
        
        # Get view and projection matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, WIDTH / HEIGHT, 0.1, 1000.0)
        projection = glGetFloatv(GL_PROJECTION_MATRIX)
        glPopMatrix()
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        look_x = self.pos[0] + math.cos(self.yaw) * math.cos(self.pitch)
        look_y = self.pos[1] + math.sin(self.pitch)
        look_z = self.pos[2] + math.sin(self.yaw) * math.cos(self.pitch)
        gluLookAt(self.pos[0], self.pos[1], self.pos[2], look_x, look_y, look_z, 0, 1, 0)
        view = glGetFloatv(GL_MODELVIEW_MATRIX)
        glPopMatrix()
        
        # Convert to world space
        ray_eye = np.linalg.inv(projection) @ ray_clip
        ray_eye = np.array([ray_eye[0], ray_eye[1], -1.0, 0.0])
        ray_world = np.linalg.inv(view) @ ray_eye
        ray_world = ray_world[:3]
        ray_world = ray_world / np.linalg.norm(ray_world)
        
        return np.array(self.pos), ray_world 