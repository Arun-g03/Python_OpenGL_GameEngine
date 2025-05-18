import glfw
import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluUnProject, gluPerspective
from OpenGL.GLUT import *
from utils.settings import *
from rendering.texture_loader import load_texture
from PIL import Image, ImageDraw, ImageFont
import os
from rendering.rasteriser import Rasteriser
from utils import input

from rendering.my_shaders import Material
from pyrr import Vector3, Matrix44

from .panels import SceneHierarchyPanel, PropertiesPanel, ContentBrowserPanel
from .viewport import EditorViewport
from .menu import EditorMenuBar, EditorToolbar
from .gizmo import Gizmo
from .ui_utils import draw_text


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

class EditorRenderer:
    def __init__(self):
        self.camera = EditorCamera()
        self.gizmo = Gizmo()
        try:
            from utils.settings import WIDTH, HEIGHT
            self.window_width = WIDTH
            self.window_height = HEIGHT
        except ImportError:
            self.window_width = 1280
            self.window_height = 720

        # Create panels
        self.top_bar = EditorTopBar(self.window_width)
        self.menu_bar = EditorMenuBar(self.window_width)
        self.toolbar = EditorToolbar(self.window_width, self.menu_bar.height)
        self.left_panel = SceneHierarchyPanel(0, 0, 250, 100)
        self.right_panel = PropertiesPanel(0, 0, 300, 100)
        self.bottom_panel = ContentBrowserPanel(0, 0, 100, 200)
        self.viewport = EditorViewport(0, 0, 100, 100, self.camera)

        # Main area: left, viewport, right
        self.main_area = HorizontalBox(0, 0, self.window_width, self.window_height)
        self.main_area.add_child(self.left_panel)
        self.main_area.add_child(self.viewport)
        self.main_area.add_child(self.right_panel)

        # Root layout: top bar, menu, toolbar, main area, content browser
        self.root_container = VerticalBox(0, 0, self.window_width, self.window_height)
        self.root_container.add_child(self.top_bar)
        self.root_container.add_child(self.menu_bar)
        self.root_container.add_child(self.toolbar)
        self.root_container.add_child(self.main_area)
        self.root_container.add_child(self.bottom_panel)

        # UI Layout
        self.menu_height = 25
        self.toolbar_height = 40
        self.status_bar_height = 25
        self.left_panel_width = 250
        self.right_panel_width = 300
        self.content_browser_height = 200
        
        # Viewport dimensions
        self.viewport_x = self.left_panel_width
        self.viewport_y = self.menu_height + self.toolbar_height
        self.viewport_width = WIDTH - self.left_panel_width - self.right_panel_width
        self.viewport_height = HEIGHT - self.menu_height - self.toolbar_height - self.status_bar_height - self.content_browser_height
        
        # Menu items
        self.menus = {
            "File": ["New Scene", "Open Scene", "Save Scene", "Save Scene As...", "Exit"],
            "Edit": ["Undo", "Redo", "Cut", "Copy", "Paste", "Delete"],
            "View": ["Toggle Grid", "Toggle Gizmo", "Toggle Content Browser", "Toggle Properties"],
            "Tools": ["Place Object", "Select", "Move", "Rotate", "Scale"],
            "Window": ["Scene Hierarchy", "Properties", "Content Browser", "Console"]
        }
        
        self.tools = {
            "place": {"icon": "🔲", "active": True, "tooltip": "Place Block (Left Click)"},
            "delete": {"icon": "🗑️", "active": False, "tooltip": "Delete Block (Right Click)"},
            "translate": {"icon": "↔️", "active": False, "tooltip": "Move Block (Gizmo)"},
            "rotate": {"icon": "🔄", "active": False, "tooltip": "Rotate Block (Coming Soon)"},
            "scale": {"icon": "📏", "active": False, "tooltip": "Scale Block (Coming Soon)"}
        }
        
        # Panel states
        self.show_content_browser = True
        self.show_properties = True
        self.show_hierarchy = True
        
        # Initialize font
        self.font_size = 24
        self.font_path = os.path.join("assets", "fonts", "arial.ttf")
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        
        self.grid_visible = True
        self.show_tooltips = True
        self.grid_sizes = [1, 2, 4, 8]
        self.current_grid_index = 0
        
        # Content browser items
        self.content_items = [
            {"name": "Cube", "icon": "🔲", "type": "cube"},
            {"name": "Sphere", "icon": "⚪", "type": "sphere"},
            {"name": "Cylinder", "icon": "⭕", "type": "cylinder"},
            {"name": "Plane", "icon": "⬜", "type": "plane"}
        ]
        
        self.entities = [
            Entity((5, 1, 5), type="cube", scale=(2, 2, 2)),
            Entity((10, 1, 10), type="sphere", scale=(1.5, 1.5, 1.5))
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
        # Add menu items
        for menu_name, items in self.menus.items():
            self.text_textures[menu_name] = self.create_text_texture(menu_name)
            for item in items:
                self.text_textures[item] = self.create_text_texture(item)
        # Add content browser items
        for item in self.content_items:
            self.text_textures[item["name"]] = self.create_text_texture(item["name"])
            self.text_textures[item["icon"]] = self.create_text_texture(item["icon"])

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

        # --- UI DATA SYNC ---
        self.left_panel.entities = self.entities
        self.right_panel.selected_entity = self.camera.selected_entity
        self.bottom_panel.items = self.bottom_panel.scan_assets()
        self.viewport.camera = self.camera
        self.top_bar.width = self.window_width

        # --- UI INTERACTION ---
        if input.was_mouse_clicked():
            mx, my = input.get_mouse_position()
            # Handle top bar button clicks
            action = self.top_bar.handle_click(mx, my)
            if action:
                # TODO: Implement actions for file/edit/selection/view/run
                pass
            # (Selection logic for panels can be improved to use container hierarchy)

        # Update container sizes
        self.root_container.width = self.window_width
        self.root_container.height = self.window_height
        self.main_area.width = self.window_width
        self.main_area.height = self.window_height - self.menu_bar.height - self.toolbar.height - self.bottom_panel.height - self.top_bar.height
        self.viewport.width = max(100, self.window_width - self.left_panel.width - self.right_panel.width)
        self.viewport.height = self.main_area.height
        self.bottom_panel.width = self.window_width

        # Draw everything via containers
        self.root_container.draw()

    def draw_world(self):
        glEnable(GL_DEPTH_TEST)

        cam_pos = Vector3(self.camera.pos)
        look_dir = Vector3([
            math.cos(self.camera.yaw) * math.cos(self.camera.pitch),
            math.sin(self.camera.pitch),
            math.sin(self.camera.yaw) * math.cos(self.camera.pitch)
        ])
        view = Matrix44.look_at(cam_pos, cam_pos + look_dir, Vector3([0, 1, 0]))
        projection = Matrix44.perspective_projection(60, self.viewport_width / self.viewport_height, 0.1, 1000.0)

        # Draw sky
        self.rasteriser.draw_sky(view, projection)

        # Highlight selected block
        if self.camera.selected_entity:
            self.draw_entity_highlight(self.camera.selected_entity)

        # Placement preview
        if self.camera.placement_pos and self.tools["place"]["active"]:
            self.draw_placement_preview(self.camera.placement_pos)

        # Draw gizmo if an entity is selected
        if self.camera.selected_entity:
            self.gizmo.draw(
                self.camera.selected_entity.position,
                self.camera.selected_entity.rotation
            )

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
        if not entity:
            return
            
        glPushMatrix()
        glTranslatef(*entity.position)
        
        # Draw selection box
        glColor4f(1.0, 1.0, 0.0, 0.5)  # Yellow with transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        if entity.type == "cube":
            size = entity.scale[0]
            glBegin(GL_LINE_LOOP)
            glVertex3f(-size/2, -size/2, -size/2)
            glVertex3f(size/2, -size/2, -size/2)
            glVertex3f(size/2, size/2, -size/2)
            glVertex3f(-size/2, size/2, -size/2)
            glEnd()
            
            glBegin(GL_LINE_LOOP)
            glVertex3f(-size/2, -size/2, size/2)
            glVertex3f(size/2, -size/2, size/2)
            glVertex3f(size/2, size/2, size/2)
            glVertex3f(-size/2, size/2, size/2)
            glEnd()
            
            glBegin(GL_LINES)
            glVertex3f(-size/2, -size/2, -size/2)
            glVertex3f(-size/2, -size/2, size/2)
            glVertex3f(size/2, -size/2, -size/2)
            glVertex3f(size/2, -size/2, size/2)
            glVertex3f(size/2, size/2, -size/2)
            glVertex3f(size/2, size/2, size/2)
            glVertex3f(-size/2, size/2, -size/2)
            glVertex3f(-size/2, size/2, size/2)
            glEnd()
            
        elif entity.type == "sphere":
            radius = entity.scale[0]
            # Draw three circles for sphere highlight
            for i in range(3):
                glBegin(GL_LINE_LOOP)
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    if i == 0:  # XY plane
                        x = radius * math.cos(rad)
                        y = radius * math.sin(rad)
                        z = 0
                    elif i == 1:  # XZ plane
                        x = radius * math.cos(rad)
                        y = 0
                        z = radius * math.sin(rad)
                    else:  # YZ plane
                        x = 0
                        y = radius * math.cos(rad)
                        z = radius * math.sin(rad)
                    glVertex3f(x, y, z)
                glEnd()
        
        glDisable(GL_BLEND)
        glPopMatrix()

    def draw_placement_preview(self, position):
        # Implementation for placement preview
        pass

    def draw_viewport(self, dt, keys, mouse_dx, mouse_dy, mouse_pos, mouse_wheel):
        # Set up viewport
        glViewport(self.viewport_x, self.viewport_y, self.viewport_width, self.viewport_height)
        
        # Set up perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, self.viewport_width / self.viewport_height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Apply camera view
        self.camera.apply_view()

        # Draw world content
        self.draw_world()
        if self.grid_visible:
            self.draw_grid()

    def resize_ui(self):
        # Calculate dynamic panel dimensions based on window size
        self.left_panel_width = int(self.window_width * 0.2)  # 20% of window width
        self.right_panel_width = int(self.window_width * 0.25)  # 25% of window width
        self.content_browser_height = int(self.window_height * 0.2)  # 20% of window height
        
        # Update menu bar
        self.menu_bar.width = self.window_width
        
        # Update toolbar
        self.toolbar.width = self.window_width
        
        # Update left panel
        self.left_panel.width = self.left_panel_width
        self.left_panel.height = self.window_height - self.menu_height - self.toolbar_height - self.content_browser_height - self.status_bar_height
        
        # Update right panel
        self.right_panel.x = self.window_width - self.right_panel_width
        self.right_panel.width = self.right_panel_width
        self.right_panel.height = self.left_panel.height
        
        # Update bottom panel
        self.bottom_panel.y = self.window_height - self.content_browser_height - self.status_bar_height
        self.bottom_panel.width = self.window_width
        self.bottom_panel.height = self.content_browser_height
        
        # Update viewport
        self.viewport.x = self.left_panel_width
        self.viewport.y = self.menu_height + self.toolbar_height
        self.viewport.width = self.window_width - self.left_panel_width - self.right_panel_width
        self.viewport.height = self.window_height - self.menu_height - self.toolbar_height - self.content_browser_height - self.status_bar_height
        
        # Update viewport dimensions for rendering
        self.viewport_x = self.viewport.x
        self.viewport_y = self.viewport.y
        self.viewport_width = self.viewport.width
        self.viewport_height = self.viewport.height


    
