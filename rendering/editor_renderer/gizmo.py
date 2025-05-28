import OpenGL.GL as gl
import math
import numpy as np
from pyrr import Vector3, Matrix44
from OpenGL.GL import glGetDoublev, GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX
from OpenGL.GLU import gluProject

class Gizmo:
    def __init__(self):
        self.axis_length = 1.0  # Reduced from 2.0 for better visibility
        self.axis_thickness = 0.05
        self.handle_size = 0.2
        self.selected_axis = None
        self.hover_axis = None  # Track which axis is being hovered
        self.is_dragging = False
        self.mouse_pressed = False  # Add mouse state tracking
        self.drag_start = None
        self.drag_plane = None
        self.transform_mode = "translate"  # "translate", "rotate", or "scale"
        
        # Colors for each axis
        self.colors = {
            "x": (1.0, 0.0, 0.0),  # Red
            "y": (0.0, 1.0, 0.0),  # Green
            "z": (0.0, 0.0, 1.0)   # Blue
        }
        
        # Handle positions for each axis (reduced length)
        self.handles = {
            "x": (self.axis_length, 0, 0),
            "y": (0, self.axis_length, 0),
            "z": (0, 0, self.axis_length)
        }
        print("[GIZMO] Initialized with transform mode:", self.transform_mode)

    def draw(self, position, rotation=(0,0,0)):
        # Save current OpenGL state
        gl.glPushAttrib(gl.GL_ALL_ATTRIB_BITS)
        
        # Disable depth testing for gizmo to always be visible
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # Set line width for better visibility
        gl.glLineWidth(3.0)
        
        gl.glPushMatrix()
        # Apply object's transform
        gl.glTranslatef(position[0], position[1], position[2])
        gl.glRotatef(math.degrees(rotation[0]), 1, 0, 0)
        gl.glRotatef(math.degrees(rotation[1]), 0, 1, 0)
        gl.glRotatef(math.degrees(rotation[2]), 0, 0, 1)
        
        # Draw axes
        for axis, color in self.colors.items():
            # Set color for this axis
            gl.glColor3f(*color)
            
            # Draw axis line
            gl.glBegin(gl.GL_LINES)
            gl.glVertex3f(0, 0, 0)
            gl.glVertex3f(*self.handles[axis])
            gl.glEnd()
            
            # Draw handle with highlight if hovered
            if self.transform_mode == "translate":
                self._draw_translate_planes()
                self._draw_translate_handle(axis, axis == self.hover_axis)
            elif self.transform_mode == "rotate":
                self._draw_rotate_handle(axis, axis == self.hover_axis)
            elif self.transform_mode == "scale":
                self._draw_scale_handle(axis, axis == self.hover_axis)
        
        gl.glPopMatrix()
        
        # Restore OpenGL state
        gl.glPopAttrib()

    def _draw_translate_handle(self, axis, is_hovered):
        # Draw arrow head
        gl.glPushMatrix()
        gl.glTranslatef(*self.handles[axis])
        
        # Scale up if hovered
        if is_hovered:
            gl.glScalef(1.5, 1.5, 1.5)
        
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

    def _draw_rotate_handle(self, axis, is_hovered):
        gl.glPushMatrix()
        # No translation, rings are centered
        segments = 64
        radius = self.axis_length * 0.9
        if is_hovered:
            radius *= 1.2  # Make ring larger when hovered
            gl.glLineWidth(4.0)  # Make line thicker when hovered
        else:
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

    def _draw_scale_handle(self, axis, is_hovered):
        # Draw cube for scale handle
        gl.glPushMatrix()
        gl.glTranslatef(*self.handles[axis])
        
        # Scale up if hovered
        if is_hovered:
            gl.glScalef(1.5, 1.5, 1.5)
        
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
        print(f"[GIZMO] handle_mouse called with pos={mouse_pos}, dx={mouse_dx}, dy={mouse_dy}")
        print(f"[GIZMO] Current state: mode={self.transform_mode}, dragging={self.is_dragging}, selected={self.selected_axis}")
        print(f"[GIZMO] Mouse coordinates: {mouse_pos}")
        
        # Calculate viewport coordinates
        viewport_x = 0
        viewport_y = 0
        viewport = [viewport_x, viewport_y, viewport_width, viewport_height]
        
        if not self.is_dragging:
            # Check if mouse is over any handle
            closest_handle = None
            closest_distance = float('inf')
            
            # Get object's world position and rotation from the selected object
            if not hasattr(camera, 'selected_object') or camera.selected_object is None:
                return False
                
            obj_pos = camera.selected_object.location
            obj_rot = camera.selected_object.rotation
            
            # Create rotation matrix
            rot_x = Matrix44.from_x_rotation(obj_rot[0])
            rot_y = Matrix44.from_y_rotation(obj_rot[1])
            rot_z = Matrix44.from_z_rotation(obj_rot[2])
            rotation = rot_z * rot_y * rot_x
            
            for axis, handle_pos in self.handles.items():
                # Transform handle position to world space
                handle_pos_h = np.array([*handle_pos, 1.0])  # Create 4D vector
                rotated_pos = np.array(rotation @ handle_pos_h)  # Convert result to numpy array
                handle_world = rotated_pos[:3] + np.array(obj_pos)  # Extract xyz and add object position
                
                print(f"[GIZMO] Testing handle {axis} at world position {handle_world}")
                distance = self._is_mouse_over_handle(
                    mouse_pos, handle_world, camera, viewport_x, viewport_y, viewport_width, viewport_height
                )
                
                # Only consider handles that are visible and within click distance
                if distance is not None and distance < 25:  # Increased threshold for easier selection
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_handle = axis
                        print(f"[GIZMO] Found closer handle: {axis} at distance {distance}")
            
            # Update hover state
            if closest_handle != self.hover_axis:
                self.hover_axis = closest_handle
                if self.hover_axis:
                    print(f"[GIZMO] Hovering over {self.transform_mode.upper()} {self.hover_axis.upper()} axis")
            
            # Handle mouse press for selection
            if closest_handle is not None and self.mouse_pressed:
                print(f"[GIZMO] Selected {self.transform_mode.upper()} {closest_handle.upper()} axis (distance: {closest_distance:.2f})")
                self.selected_axis = closest_handle
                self.drag_start = mouse_pos
                self.is_dragging = True
                return True
                
            self.selected_axis = None
            return False
        else:
            # Handle dragging
            if self.transform_mode == "translate":
                movement = self._handle_translate(mouse_dx, mouse_dy, camera)
                if movement is not None and np.any(np.array(movement) != 0):
                    print(f"[GIZMO] Translating on {self.selected_axis.upper()} axis: {movement}")
                return movement
            elif self.transform_mode == "rotate":
                rotation = self._handle_rotate(mouse_dx, mouse_dy, camera)
                if rotation is not None and np.any(np.array(rotation) != 0):
                    print(f"[GIZMO] Rotating on {self.selected_axis.upper()} axis: {rotation}")
                return rotation
            elif self.transform_mode == "scale":
                scale = self._handle_scale(mouse_dx, mouse_dy, camera)
                if scale is not None and np.any(np.array(scale) != 1):
                    print(f"[GIZMO] Scaling on {self.selected_axis.upper()} axis: {scale}")
                return scale
            return False

    def _is_mouse_over_handle(self, mouse_pos, handle_pos, camera, viewport_x, viewport_y, viewport_width, viewport_height):
        viewport = [viewport_x, viewport_y, viewport_width, viewport_height]
        handle_screen = self._world_to_screen(handle_pos, camera, viewport)
                
        # Check if handle is behind camera or off-screen
        if handle_screen[0] < 0 or handle_screen[1] < 0:
            return None
        
        # Check if mouse is within handle bounds
        mouse_x, mouse_y = mouse_pos
        handle_x, handle_y = handle_screen
        
        # Calculate distance in screen space
        distance = math.sqrt((mouse_x - handle_x)**2 + (mouse_y - handle_y)**2)
        
        # Print debug info only when close to handle
        if distance < 30:  # Increased threshold for debug output
            print(f"[GIZMO] Handle screen pos: ({handle_x:.1f}, {handle_y:.1f}), mouse: ({mouse_x:.1f}, {mouse_y:.1f}), distance: {distance:.1f}")
        
        # Return distance if within threshold, None otherwise
        return distance if distance < 25 else None

    def _world_to_screen(self, world_pos, camera, viewport):
        from OpenGL.GL import glGetDoublev, GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX
        from OpenGL.GLU import gluProject
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        screen_x, screen_y, screen_z = gluProject(
            world_pos[0], world_pos[1], world_pos[2],
            modelview, projection, viewport
        )
        # Flip y to match Qt's top-left origin
        screen_y = viewport[3] + viewport[1] - screen_y
        print(f"[GIZMO] World pos: {world_pos} -> Screen pos: ({screen_x}, {screen_y})")
        return (screen_x, screen_y)

    def _handle_translate(self, mouse_dx, mouse_dy, camera):
        # Calculate movement in world space based on selected axis
        movement = Vector3([0, 0, 0])
        sensitivity = 0.1
        
        # Get camera's right and up vectors
        right = Vector3([
            math.cos(camera.yaw),
            0,
            math.sin(camera.yaw)
        ])
        up = Vector3([0, 1, 0])
        
        if self.selected_axis == "x":
            movement = right * mouse_dx * sensitivity
        elif self.selected_axis == "y":
            movement = up * -mouse_dy * sensitivity
        elif self.selected_axis == "z":
            # Use camera's forward vector for Z movement
            forward = Vector3([
                math.cos(camera.yaw) * math.cos(camera.pitch),
                math.sin(camera.pitch),
                math.sin(camera.yaw) * math.cos(camera.pitch)
            ])
            movement = forward * mouse_dx * sensitivity
            
        print(f"[GIZMO] Translation movement: {movement}")
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
            
        print(f"[GIZMO] Rotation: {rotation}")
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
            
        print(f"[GIZMO] Scale: {scale}")
        return scale

    def set_transform_mode(self, mode):
        if mode in ["translate", "rotate", "scale"]:
            print(f"[GIZMO] Switching to {mode.upper()} mode")
            self.transform_mode = mode
            self.selected_axis = None
            self.is_dragging = False 