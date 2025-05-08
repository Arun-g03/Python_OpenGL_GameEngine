import math
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluUnProject
from utils.settings import *
from world.map import game_map, MAP_WIDTH, MAP_HEIGHT, MAP_DEPTH

class EditorCamera:
    def __init__(self):
        self.pos = [MAP_WIDTH * TILE_SIZE_M / 2, 5.0, MAP_DEPTH * TILE_SIZE_M / 2]  # Start above center
        self.pitch = -math.pi/4  # Look down at 45 degrees
        self.yaw = 0
        self.speed = 10.0
        self.mouse_sensitivity = 0.002
        self.selected_block = None
        self.transform_mode = "translate"  # translate, rotate, scale
        self.grid_size = 1  # Changed to integer
        self.placement_pos = None  # Position where block will be placed
        self.placement_normal = None  # Normal of the face where block will be placed

    def update(self, dt, keys, mouse_dx, mouse_dy, mouse_pos):
        # Camera speed control
        if keys[pygame.K_LCTRL]:
            self.speed = 20.0  # Fast movement
        else:
            self.speed = 10.0  # Normal speed

        # Camera rotation
        if pygame.mouse.get_pressed()[1]:  # Middle mouse button
            self.yaw += mouse_dx * self.mouse_sensitivity
            self.pitch -= mouse_dy * self.mouse_sensitivity
            self.pitch = max(-math.pi/2, min(math.pi/2, self.pitch))

        # Camera movement
        forward = [
            math.cos(self.yaw),
            math.tan(self.pitch),
            math.sin(self.yaw)
        ]
        right = [
            -forward[2], 0, forward[0]
        ]
        up = [0, 1, 0]

        velocity = self.speed * dt
        if keys[pygame.K_w]: self.pos = [p + f * velocity for p, f in zip(self.pos, forward)]
        if keys[pygame.K_s]: self.pos = [p - f * velocity for p, f in zip(self.pos, forward)]
        if keys[pygame.K_a]: self.pos = [p - r * velocity for p, r in zip(self.pos, right)]
        if keys[pygame.K_d]: self.pos = [p + r * velocity for p, r in zip(self.pos, right)]
        if keys[pygame.K_SPACE]: self.pos = [p + u * velocity for p, u in zip(self.pos, up)]
        if keys[pygame.K_LSHIFT]: self.pos = [p - u * velocity for p, u in zip(self.pos, up)]
        if keys[pygame.K_e]: self.pos = [p + u * velocity for p, u in zip(self.pos, up)]  # E for up
        if keys[pygame.K_q]: self.pos = [p - u * velocity for p, u in zip(self.pos, up)]  # Q for down

        # Ray casting for block selection
        self.update_block_selection(mouse_pos)

    def update_block_selection(self, mouse_pos):
        # Convert mouse position to normalized device coordinates
        x = (2.0 * mouse_pos[0]) / WIDTH - 1.0
        y = 1.0 - (2.0 * mouse_pos[1]) / HEIGHT
        z = 1.0

        # Get matrices and convert to double arrays
        view_matrix = np.array(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=np.float64)
        proj_matrix = np.array(glGetFloatv(GL_PROJECTION_MATRIX), dtype=np.float64)
        viewport = np.array(glGetIntegerv(GL_VIEWPORT), dtype=np.int32)
        
        try:
            world_pos = gluUnProject(x, y, z, view_matrix, proj_matrix, viewport)
            
            # Ray direction
            dir_x = world_pos[0] - self.pos[0]
            dir_y = world_pos[1] - self.pos[1]
            dir_z = world_pos[2] - self.pos[2]
            
            # Normalize direction
            length = math.sqrt(dir_x*dir_x + dir_y*dir_y + dir_z*dir_z)
            dir_x /= length
            dir_y /= length
            dir_z /= length

            # Ray casting
            t = 0
            last_empty = None
            while t < 100:  # Max distance
                x = int(self.pos[0] + dir_x * t)
                y = int(self.pos[1] + dir_y * t)
                z = int(self.pos[2] + dir_z * t)
                
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and 0 <= z < MAP_DEPTH:
                    if game_map[z][y][x] == 1:
                        self.selected_block = (x, y, z)
                        # Calculate placement position and normal
                        if last_empty:
                            self.placement_pos = last_empty
                            # Calculate normal based on the direction of the ray
                            self.placement_normal = (
                                int(round(dir_x)),
                                int(round(dir_y)),
                                int(round(dir_z))
                            )
                        return
                    else:
                        last_empty = (x, y, z)
                
                t += 0.1
            
            self.selected_block = None
            self.placement_pos = None
            self.placement_normal = None
        except Exception as e:
            print(f"Error in block selection: {e}")
            self.selected_block = None
            self.placement_pos = None
            self.placement_normal = None

    def apply_view(self):
        dir_x = math.cos(self.yaw)
        dir_z = math.sin(self.yaw)
        dir_y = math.tan(self.pitch)
        gluLookAt(
            *self.pos,
            self.pos[0] + dir_x, self.pos[1] + dir_y, self.pos[2] + dir_z,
            0, 1, 0
        )

class EditorRenderer:
    def __init__(self):
        self.camera = EditorCamera()
        self.tools = {
            "place": {"icon": "🔲", "active": True, "tooltip": "Place Block (Left Click)"},
            "delete": {"icon": "🗑️", "active": False, "tooltip": "Delete Block (Right Click)"},
            "translate": {"icon": "↔️", "active": False, "tooltip": "Move Block (Coming Soon)"},
            "rotate": {"icon": "🔄", "active": False, "tooltip": "Rotate Block (Coming Soon)"},
            "scale": {"icon": "📏", "active": False, "tooltip": "Scale Block (Coming Soon)"}
        }
        self.font = pygame.font.SysFont("Arial", 24)
        self.grid_visible = True
        self.show_tooltips = True
        self.grid_sizes = [1, 2, 4, 8]
        self.current_grid_index = 0
        self.show_hotkeys = False  # New: track hotkey menu visibility
        self.hotkeys = [
            ("Movement", [
                "WASD - Move camera",
                "QE - Move up/down",
                "Ctrl - Fast movement",
                "Middle Mouse - Rotate camera"
            ]),
            ("Editing", [
                "Left Click - Place block",
                "Right Click - Delete block",
                "G - Cycle grid size",
                "H - Toggle grid"
            ]),
            ("UI", [
                "T - Toggle tooltips",
                "ESC - Return to menu"
            ])
        ]

    def render(self, dt, keys, mouse_dx, mouse_dy, mouse_pos):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Update camera
        self.camera.update(dt, keys, mouse_dx, mouse_dy, mouse_pos)
        self.camera.apply_view()

        # Draw world
        self.draw_world()
        if self.grid_visible:
            self.draw_grid()
        
        # Draw UI
        self.draw_ui()

    def draw_world(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        
        # Draw blocks
        for z in range(MAP_DEPTH):
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    if game_map[z][y][x] == 1:
                        self.draw_block(x, y, z)

        # Highlight selected block
        if self.camera.selected_block:
            x, y, z = self.camera.selected_block
            self.draw_block_highlight(x, y, z)

        # Draw placement preview
        if self.camera.placement_pos and self.tools["place"]["active"]:
            x, y, z = self.camera.placement_pos
            self.draw_placement_preview(x, y, z)

    def draw_block(self, x, y, z):
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_QUADS)
        
        # Front face
        glVertex3f(x, y, z)
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y + 1, z)
        glVertex3f(x, y + 1, z)
        
        # Back face
        glVertex3f(x, y, z + 1)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x, y + 1, z + 1)
        
        # Left face
        glVertex3f(x, y, z)
        glVertex3f(x, y, z + 1)
        glVertex3f(x, y + 1, z + 1)
        glVertex3f(x, y + 1, z)
        
        # Right face
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x + 1, y + 1, z)
        
        # Top face
        glVertex3f(x, y + 1, z)
        glVertex3f(x + 1, y + 1, z)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x, y + 1, z + 1)
        
        # Bottom face
        glVertex3f(x, y, z)
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x, y, z + 1)
        
        glEnd()

    def draw_block_highlight(self, x, y, z):
        glColor4f(1.0, 1.0, 0.0, 0.3)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        # Draw slightly larger box around selected block
        offset = 0.05
        glVertex3f(x - offset, y - offset, z - offset)
        glVertex3f(x + 1 + offset, y - offset, z - offset)
        glVertex3f(x + 1 + offset, y + 1 + offset, z - offset)
        glVertex3f(x - offset, y + 1 + offset, z - offset)
        
        glVertex3f(x - offset, y - offset, z + 1 + offset)
        glVertex3f(x + 1 + offset, y - offset, z + 1 + offset)
        glVertex3f(x + 1 + offset, y + 1 + offset, z + 1 + offset)
        glVertex3f(x - offset, y + 1 + offset, z + 1 + offset)
        glEnd()
        
        glDisable(GL_BLEND)

    def draw_placement_preview(self, x, y, z):
        glColor4f(0.0, 1.0, 0.0, 0.3)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        glVertex3f(x, y, z)
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y + 1, z)
        glVertex3f(x, y + 1, z)
        
        glVertex3f(x, y, z + 1)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x, y + 1, z + 1)
        
        glVertex3f(x, y, z)
        glVertex3f(x, y, z + 1)
        glVertex3f(x, y + 1, z + 1)
        glVertex3f(x, y + 1, z)
        
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x + 1, y + 1, z)
        
        glVertex3f(x, y + 1, z)
        glVertex3f(x + 1, y + 1, z)
        glVertex3f(x + 1, y + 1, z + 1)
        glVertex3f(x, y + 1, z + 1)
        
        glVertex3f(x, y, z)
        glVertex3f(x + 1, y, z)
        glVertex3f(x + 1, y, z + 1)
        glVertex3f(x, y, z + 1)
        glEnd()
        
        glDisable(GL_BLEND)

    def draw_grid(self):
        glDisable(GL_DEPTH_TEST)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        
        # Draw grid lines
        grid_size = self.grid_sizes[self.current_grid_index]
        for x in range(0, MAP_WIDTH + 1, grid_size):
            glVertex3f(x, 0, 0)
            glVertex3f(x, 0, MAP_DEPTH)
        
        for z in range(0, MAP_DEPTH + 1, grid_size):
            glVertex3f(0, 0, z)
            glVertex3f(MAP_WIDTH, 0, z)
        
        glEnd()
        glEnable(GL_DEPTH_TEST)

    def draw_ui(self):
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw hotkey menu button
        hotkey_button_width = 120
        hotkey_button_height = 40
        padding = 10
        hotkey_x = WIDTH - hotkey_button_width - padding
        hotkey_y = padding
        
        # Draw hotkey button background
        glColor4f(0.2, 0.2, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(hotkey_x, hotkey_y)
        glVertex2f(hotkey_x + hotkey_button_width, hotkey_y)
        glVertex2f(hotkey_x + hotkey_button_width, hotkey_y + hotkey_button_height)
        glVertex2f(hotkey_x, hotkey_y + hotkey_button_height)
        glEnd()
        
        # Draw hotkey button text
        text = "Show Hotkeys" if not self.show_hotkeys else "Hide Hotkeys"
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        width, height = text_surface.get_size()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(hotkey_x + (hotkey_button_width - width)/2, hotkey_y + (hotkey_button_height - height)/2)
        glTexCoord2f(1, 1); glVertex2f(hotkey_x + (hotkey_button_width + width)/2, hotkey_y + (hotkey_button_height - height)/2)
        glTexCoord2f(1, 0); glVertex2f(hotkey_x + (hotkey_button_width + width)/2, hotkey_y + (hotkey_button_height + height)/2)
        glTexCoord2f(0, 0); glVertex2f(hotkey_x + (hotkey_button_width - width)/2, hotkey_y + (hotkey_button_height + height)/2)
        glEnd()
        glDisable(GL_BLEND)
        
        glDeleteTextures([tex_id])

        # Draw hotkey menu if visible
        if self.show_hotkeys:
            menu_x = WIDTH - 300 - padding
            menu_y = hotkey_y + hotkey_button_height + padding
            menu_width = 300
            menu_height = 400
            
            # Draw menu background
            glColor4f(0.1, 0.1, 0.1, 0.9)
            glBegin(GL_QUADS)
            glVertex2f(menu_x, menu_y)
            glVertex2f(menu_x + menu_width, menu_y)
            glVertex2f(menu_x + menu_width, menu_y + menu_height)
            glVertex2f(menu_x, menu_y + menu_height)
            glEnd()
            
            # Draw menu border
            glColor4f(0.3, 0.3, 0.3, 1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(menu_x, menu_y)
            glVertex2f(menu_x + menu_width, menu_y)
            glVertex2f(menu_x + menu_width, menu_y + menu_height)
            glVertex2f(menu_x, menu_y + menu_height)
            glEnd()
            
            # Draw hotkey sections
            current_y = menu_y + padding
            for section_title, hotkeys in self.hotkeys:
                # Draw section title
                title_surface = self.font.render(section_title, True, (255, 255, 255))
                title_data = pygame.image.tostring(title_surface, "RGBA", True)
                title_width, title_height = title_surface.get_size()
                
                tex_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, title_width, title_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, title_data)
                
                glEnable(GL_TEXTURE_2D)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glColor4f(1, 1, 1, 1)
                glBegin(GL_QUADS)
                glTexCoord2f(0, 1); glVertex2f(menu_x + padding, current_y)
                glTexCoord2f(1, 1); glVertex2f(menu_x + padding + title_width, current_y)
                glTexCoord2f(1, 0); glVertex2f(menu_x + padding + title_width, current_y + title_height)
                glTexCoord2f(0, 0); glVertex2f(menu_x + padding, current_y + title_height)
                glEnd()
                glDisable(GL_BLEND)
                
                glDeleteTextures([tex_id])
                
                current_y += title_height + padding
                
                # Draw hotkeys
                for hotkey in hotkeys:
                    hotkey_surface = self.font.render(hotkey, True, (200, 200, 200))
                    hotkey_data = pygame.image.tostring(hotkey_surface, "RGBA", True)
                    hotkey_width, hotkey_height = hotkey_surface.get_size()
                    
                    tex_id = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, tex_id)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, hotkey_width, hotkey_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, hotkey_data)
                    
                    glEnable(GL_TEXTURE_2D)
                    glEnable(GL_BLEND)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                    glColor4f(1, 1, 1, 1)
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 1); glVertex2f(menu_x + padding * 2, current_y)
                    glTexCoord2f(1, 1); glVertex2f(menu_x + padding * 2 + hotkey_width, current_y)
                    glTexCoord2f(1, 0); glVertex2f(menu_x + padding * 2 + hotkey_width, current_y + hotkey_height)
                    glTexCoord2f(0, 0); glVertex2f(menu_x + padding * 2, current_y + hotkey_height)
                    glEnd()
                    glDisable(GL_BLEND)
                    
                    glDeleteTextures([tex_id])
                    
                    current_y += hotkey_height + padding
        
        # Draw tool buttons
        button_width = 60
        button_height = 40
        start_x = padding
        start_y = HEIGHT - button_height - padding
        
        for i, (tool_name, tool) in enumerate(self.tools.items()):
            x = start_x + i * (button_width + padding)
            y = start_y
            
            # Draw button background
            glColor4f(0.2, 0.2, 0.2, 0.8 if tool["active"] else 0.5)
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + button_width, y)
            glVertex2f(x + button_width, y + button_height)
            glVertex2f(x, y + button_height)
            glEnd()
            
            # Draw tool icon
            text_surface = self.font.render(tool["icon"], True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            width, height = text_surface.get_size()
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex2f(x + (button_width - width)/2, y + (button_height - height)/2)
            glTexCoord2f(1, 1); glVertex2f(x + (button_width + width)/2, y + (button_height - height)/2)
            glTexCoord2f(1, 0); glVertex2f(x + (button_width + width)/2, y + (button_height + height)/2)
            glTexCoord2f(0, 0); glVertex2f(x + (button_width - width)/2, y + (button_height + height)/2)
            glEnd()
            glDisable(GL_BLEND)
            
            glDeleteTextures([tex_id])

            # Draw tooltip
            if self.show_tooltips:
                mouse_pos = pygame.mouse.get_pos()
                if x <= mouse_pos[0] <= x + button_width and y <= mouse_pos[1] <= y + button_height:
                    tooltip_surface = self.font.render(tool["tooltip"], True, (255, 255, 255))
                    tooltip_data = pygame.image.tostring(tooltip_surface, "RGBA", True)
                    tooltip_width, tooltip_height = tooltip_surface.get_size()
                    
                    tooltip_tex_id = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, tooltip_tex_id)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tooltip_width, tooltip_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, tooltip_data)
                    
                    glEnable(GL_TEXTURE_2D)
                    glEnable(GL_BLEND)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                    glColor4f(0.2, 0.2, 0.2, 0.9)
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 1); glVertex2f(x, y - tooltip_height - 5)
                    glTexCoord2f(1, 1); glVertex2f(x + tooltip_width, y - tooltip_height - 5)
                    glTexCoord2f(1, 0); glVertex2f(x + tooltip_width, y - 5)
                    glTexCoord2f(0, 0); glVertex2f(x, y - 5)
                    glEnd()
                    
                    glColor4f(1, 1, 1, 1)
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 1); glVertex2f(x, y - tooltip_height - 5)
                    glTexCoord2f(1, 1); glVertex2f(x + tooltip_width, y - tooltip_height - 5)
                    glTexCoord2f(1, 0); glVertex2f(x + tooltip_width, y - 5)
                    glTexCoord2f(0, 0); glVertex2f(x, y - 5)
                    glEnd()
                    glDisable(GL_BLEND)
                    
                    glDeleteTextures([tooltip_tex_id])
        
        # Draw coordinates and grid size
        info_text = [
            f"X: {self.camera.pos[0]:.1f} Y: {self.camera.pos[1]:.1f} Z: {self.camera.pos[2]:.1f}",
            f"Grid Size: {self.grid_sizes[self.current_grid_index]}"
        ]
        
        for i, text in enumerate(info_text):
            text_surface = self.font.render(text, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            width, height = text_surface.get_size()
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex2f(padding, padding + i * (height + 5))
            glTexCoord2f(1, 1); glVertex2f(padding + width, padding + i * (height + 5))
            glTexCoord2f(1, 0); glVertex2f(padding + width, padding + (i + 1) * (height + 5))
            glTexCoord2f(0, 0); glVertex2f(padding, padding + (i + 1) * (height + 5))
            glEnd()
            glDisable(GL_BLEND)
            
            glDeleteTextures([tex_id])
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)

    def handle_click(self, pos):
        # Check hotkey menu button
        hotkey_button_width = 120
        hotkey_button_height = 40
        padding = 10
        hotkey_x = WIDTH - hotkey_button_width - padding
        hotkey_y = padding
        
        if hotkey_x <= pos[0] <= hotkey_x + hotkey_button_width and hotkey_y <= pos[1] <= hotkey_y + hotkey_button_height:
            self.show_hotkeys = not self.show_hotkeys
            return True

        # Check tool button clicks
        button_width = 60
        button_height = 40
        start_x = padding
        start_y = HEIGHT - button_height - padding
        
        for i, (tool_name, tool) in enumerate(self.tools.items()):
            x = start_x + i * (button_width + padding)
            y = start_y
            
            if x <= pos[0] <= x + button_width and y <= pos[1] <= y + button_height:
                # Deactivate all tools
                for t in self.tools.values():
                    t["active"] = False
                # Activate clicked tool
                tool["active"] = True
                return True
        
        return False

    def handle_block_edit(self, pos):
        if not self.camera.placement_pos:
            return
        
        x, y, z = self.camera.placement_pos
        
        # Place block
        if self.tools["place"]["active"]:
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and 0 <= z < MAP_DEPTH:
                game_map[z][y][x] = 1
        
        # Delete block
        elif self.tools["delete"]["active"] and self.camera.selected_block:
            x, y, z = self.camera.selected_block
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and 0 <= z < MAP_DEPTH:
                game_map[z][y][x] = 0

    def handle_key(self, key):
        # Grid size control
        if key == pygame.K_g:
            self.current_grid_index = (self.current_grid_index + 1) % len(self.grid_sizes)
        # Toggle grid visibility
        elif key == pygame.K_h:
            self.grid_visible = not self.grid_visible
        # Toggle tooltips
        elif key == pygame.K_t:
            self.show_tooltips = not self.show_tooltips
