import glfw
import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluUnProject, gluPerspective
from utils.settings import *
from rendering.texture_loader import load_texture
from PIL import Image, ImageDraw, ImageFont
import os
from rendering.rasteriser import Rasteriser
from utils import input

from rendering.my_shaders import Material
from pyrr import Vector3, Matrix44

EDITOR_WIDTH = 32
EDITOR_HEIGHT = 8
EDITOR_DEPTH = 32

class Entity:
    def __init__(self, position, rotation=(0,0,0), scale=(1,1,1), type="block"):
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)
        self.scale = np.array(scale, dtype=float)
        self.type = type

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
        if keys.get(glfw.KEY_LEFT_CONTROL):
            self.speed = self.fast_speed
        else:
            self.speed = self.slow_speed

        # Mouse look (hold right mouse button)
        if input.is_right_mouse_held():
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
        if keys.get(glfw.KEY_W):
            self.pos = [p + f * velocity for p, f in zip(self.pos, forward)]
        if keys.get(glfw.KEY_S):
            self.pos = [p - f * velocity for p, f in zip(self.pos, forward)]
        if keys.get(glfw.KEY_A):
            self.pos = [p - r * velocity for p, r in zip(self.pos, right)]
        if keys.get(glfw.KEY_D):
            self.pos = [p + r * velocity for p, r in zip(self.pos, right)]
        if keys.get(glfw.KEY_SPACE):
            self.pos = [p + u * velocity for p, u in zip(self.pos, up)]
        if keys.get(glfw.KEY_LEFT_SHIFT):
            self.pos = [p - u * velocity for p, u in zip(self.pos, up)]
        if keys.get(glfw.KEY_E):
            self.pos = [p + u * velocity for p, u in zip(self.pos, up)]
        if keys.get(glfw.KEY_Q):
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
        
        # Initialize font
        self.font_size = 24
        self.font_path = os.path.join("assets", "fonts", "arial.ttf")
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        
        self.grid_visible = True
        self.show_tooltips = True
        self.grid_sizes = [1, 2, 4, 8]
        self.current_grid_index = 0
        self.show_hotkeys = False
        
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
        
        self.floor_texture = load_texture("assets/Stone_floor.jpg")
        # Entities: type, position, size/radius
        self.entities = [
            {"type": "cube", "position": (5, 1, 5), "size": 2},
            {"type": "sphere", "position": (10, 1, 10), "radius": 1.5}
        ]
        
        # Pre-render text textures
        self.text_textures = {}
        self.update_text_textures()
        self.rasteriser = Rasteriser()
        self.use_rasteriser = False

    def update_text_textures(self):
        # Update all text textures
        self.text_textures = {}
        # Add tool icons
        for tool in self.tools.values():
            self.text_textures[tool["icon"]] = self.create_text_texture(tool["icon"])
            self.text_textures[tool["tooltip"]] = self.create_text_texture(tool["tooltip"])
        # Add hotkey texts
        for section_title, hotkeys in self.hotkeys:
            self.text_textures[section_title] = self.create_text_texture(section_title)
            for hotkey in hotkeys:
                self.text_textures[hotkey] = self.create_text_texture(hotkey)

    def create_text_texture(self, text):
        # Create a new image with transparent background
        bbox = self.font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        image = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw text
        draw.text((0, 0), text, font=self.font, fill=(255, 255, 255, 255))
        
        # Convert to OpenGL texture
        image_data = np.array(image)
        width, height = image.size
        
        # Generate texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        
        return {"id": tex_id, "width": width, "height": height}

    def render(self, dt, keys, mouse_dx, mouse_dy, mouse_pos, mouse_wheel=0):
        if self.use_rasteriser:
            self.rasteriser.render()
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Update camera with current input state
        self.camera.update(dt, keys, mouse_dx, mouse_dy, mouse_pos, mouse_wheel)

        # --- Block placement/deletion ---
        if input.was_place_block_pressed():
            self.handle_block_edit("place")
        if input.was_delete_block_pressed():
            self.handle_block_edit("delete")

        # --- 3D WORLD ---
        # Set up perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, WIDTH / HEIGHT, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Apply camera view
        self.camera.apply_view()

        cam_pos = Vector3(self.camera.pos)
        look_dir = Vector3([
            math.cos(self.camera.yaw) * math.cos(self.camera.pitch),
            math.sin(self.camera.pitch),
            math.sin(self.camera.yaw) * math.cos(self.camera.pitch)
        ])

        view = Matrix44.look_at(cam_pos, cam_pos + look_dir, Vector3([0, 1, 0]))
        projection = Matrix44.perspective_projection(60, WIDTH / HEIGHT, 0.1, 1000.0)

        self.rasteriser.draw_sky(view, projection)
        # Draw world (floor, entities, grid, etc.)
        self.draw_world()
        if self.grid_visible:
            self.draw_grid()

        # --- UI ---
        # Switch to orthographic projection for UI
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        self.draw_ui()

        # Restore matrices and state
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    

    def draw_world(self):
        glEnable(GL_DEPTH_TEST)

        cam_pos = Vector3(self.camera.pos)
        look_dir = Vector3([
            math.cos(self.camera.yaw) * math.cos(self.camera.pitch),
            math.sin(self.camera.pitch),
            math.sin(self.camera.yaw) * math.cos(self.camera.pitch)
        ])
        view = Matrix44.look_at(cam_pos, cam_pos + look_dir, Vector3([0, 1, 0]))
        projection = Matrix44.perspective_projection(60, WIDTH / HEIGHT, 0.1, 1000.0)

        # Floor rendering
        self.rasteriser.draw_floor(view, projection, Material(base_color=(0.2, 0.6, 0.2), roughness=0.9), cam_pos)

        # Draw entities using rasteriser
        for entity in self.entities:
            if entity["type"] == "cube":
                pos = Vector3(entity["position"])
                material = Material(base_color=(0.8, 0.2, 0.2))
                self.rasteriser.draw_cube(pos, entity["size"], view, projection, material, cam_pos)
            elif entity["type"] == "sphere":
                pos = Vector3(entity["position"])
                material = Material(base_color=(0.2, 0.4, 0.9), roughness=0.3, metallic=0.0, specular=0.5)
                self.rasteriser.draw_sphere(pos, entity["radius"], view, projection, material, cam_pos)

        # Highlight selected block
        if self.camera.selected_entity:
            self.draw_entity_highlight(self.camera.selected_entity)

        # Placement preview
        if self.camera.placement_pos and self.tools["place"]["active"]:
            self.draw_placement_preview(self.camera.placement_pos)

    def draw_grid(self):
        glDisable(GL_DEPTH_TEST)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        
        # Draw grid lines
        grid_size = self.grid_sizes[self.current_grid_index]
        for x in range(0, EDITOR_WIDTH + 1, grid_size):
            glVertex3f(x, 0, 0)
            glVertex3f(x, 0, EDITOR_DEPTH)
        
        for z in range(0, EDITOR_DEPTH + 1, grid_size):
            glVertex3f(0, 0, z)
            glVertex3f(EDITOR_WIDTH, 0, z)
        
        glEnd()
        glEnable(GL_DEPTH_TEST)

    def draw_ui(self):
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
        self.draw_text(text, (hotkey_x + hotkey_button_width/2, hotkey_y + hotkey_button_height/2))

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
                self.draw_text(section_title, (menu_x + padding, current_y))
                current_y += self.text_textures[section_title]["height"] + padding
                
                # Draw hotkeys
                for hotkey in hotkeys:
                    self.draw_text(hotkey, (menu_x + padding * 2, current_y))
                    current_y += self.text_textures[hotkey]["height"] + padding
        
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
            self.draw_text(tool["icon"], (x + button_width/2, y + button_height/2))

            # Draw tooltip
            if self.show_tooltips:
                mouse_x, mouse_y = glfw.get_cursor_pos(glfw.get_current_context())
                if x <= mouse_x <= x + button_width and y <= mouse_y <= y + button_height:
                    self.draw_text(tool["tooltip"], (x, y - 5))
        
        # Draw coordinates, grid size, camera mode, and camera rotation
        info_text = [
            f"X: {self.camera.pos[0]:.1f} Y: {self.camera.pos[1]:.1f} Z: {self.camera.pos[2]:.1f}",
            f"Grid Size: {self.grid_sizes[self.current_grid_index]}",
            f"Mode: {'Fly' if self.camera.fly_mode else 'Orbit'}",
            f"Yaw: {math.degrees(self.camera.yaw):.1f}°  Pitch: {math.degrees(self.camera.pitch):.1f}°"
        ]
        
        for i, text in enumerate(info_text):
            self.draw_text(text, (10, 10 + i * (self.font_size + 5)))

    def draw_text(self, text, center):
        if text not in self.text_textures:
            self.text_textures[text] = self.create_text_texture(text)
            
        texture = self.text_textures[text]
        width, height = texture["width"], texture["height"]
        x, y = center[0] - width/2, center[1] - height/2

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture["id"])
        glColor4f(1, 1, 1, 1)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + width, y)
        glTexCoord2f(1, 1); glVertex2f(x + width, y + height)
        glTexCoord2f(0, 1); glVertex2f(x, y + height)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

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

    def handle_block_edit(self, action):
        if not self.camera.placement_pos:
            return
        x, y, z = self.camera.placement_pos
        if action == "place" and self.tools["place"]["active"]:
            # Place block logic here
            print(f"Placing block at {self.camera.placement_pos}")
            # (Add your block placement logic)
        elif action == "delete" and self.tools["delete"]["active"]:
            # Delete block logic here
            print(f"Deleting block at {self.camera.placement_pos}")
            # (Add your block deletion logic)

    def handle_key(self, key):
        # Grid size control
        if key == glfw.KEY_G:
            self.current_grid_index = (self.current_grid_index + 1) % len(self.grid_sizes)
        # Toggle grid visibility
        elif key == glfw.KEY_H:
            self.grid_visible = not self.grid_visible
        # Toggle tooltips
        elif key == glfw.KEY_T:
            self.show_tooltips = not self.show_tooltips
        # Toggle rasteriser
        elif key == glfw.KEY_R:
            self.use_rasteriser = not self.use_rasteriser

    def draw_entity_highlight(self, entity):
        # Implementation for highlighting selected entities
        pass

    def draw_placement_preview(self, position):
        # Implementation for placement preview
        pass


    
