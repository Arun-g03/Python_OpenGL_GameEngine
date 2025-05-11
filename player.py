import math
import glfw

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.rot_x = 0  # Vertical rotation (pitch)
        self.rot_y = 0  # Horizontal rotation (yaw)
        self.angle = 0  # Current angle in radians
        self.speed = 5.0
        self.mouse_sensitivity = 0.002
        self.jump_force = 10.0
        self.gravity = 20.0
        self.velocity_y = 0
        self.is_jumping = False
        self.is_grounded = True

    def update(self, dt, keys, mouse_buttons):
        # Handle movement
        move_speed = self.speed * dt
        
        # Calculate forward and right vectors based on current rotation
        forward_x = math.cos(self.rot_y)
        forward_z = math.sin(self.rot_y)
        right_x = -forward_z
        right_z = forward_x
        
        # Movement
        if keys.get(glfw.KEY_W):
            self.x += forward_x * move_speed
            self.z += forward_z * move_speed
        if keys.get(glfw.KEY_S):
            self.x -= forward_x * move_speed
            self.z -= forward_z * move_speed
        if keys.get(glfw.KEY_A):
            self.x += right_x * move_speed
            self.z += right_z * move_speed
        if keys.get(glfw.KEY_D):
            self.x -= right_x * move_speed
            self.z -= right_z * move_speed
            
        # Jumping
        if keys.get(glfw.KEY_SPACE) and self.is_grounded:
            self.velocity_y = self.jump_force
            self.is_grounded = False
            self.is_jumping = True
            
        # Apply gravity
        if not self.is_grounded:
            self.velocity_y -= self.gravity * dt
            self.z += self.velocity_y * dt
            
            # Check if landed
            if self.z <= 0:
                self.z = 0
                self.velocity_y = 0
                self.is_grounded = True
                self.is_jumping = False 