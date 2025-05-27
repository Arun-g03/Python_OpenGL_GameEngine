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
from .editor_UI import MainEditor
from .editor_camera import EditorCamera
from PySide6.QtCore import Qt


EDITOR_WIDTH = 32
EDITOR_HEIGHT = 8
EDITOR_DEPTH = 32

class Entity:
    def __init__(self, position, rotation=(0,0,0), scale=(1,1,1), type="block"):
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)
        self.scale = np.array(scale, dtype=float)
        self.type = type



class EditorRenderer:
    def __init__(self, scene, editor):
        self.scene = scene
        self.editor = editor
        print("EditorRenderer initialized")
        self.camera = EditorCamera()
        self.gizmo = Gizmo()
        self.selected_object = None
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.editor.show()
        try:
            from utils.settings import WIDTH, HEIGHT
            self.window_width = WIDTH
            self.window_height = HEIGHT
        except ImportError:
            self.window_width = 1280
            self.window_height = 720

        """ # Create panels
        #self.top_bar = EditorTopBar(self.window_width)
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
 """
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
        
        self.last_ray_origin = None
        self.last_ray_direction = None

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
        self.camera.update(dt, keys, mouse_dx, mouse_dy, mouse_pos, mouse_wheel)
        self.editor.update_viewport()

    def draw_world(self):
        print("\n=== DRAW WORLD CALLED ===")
        if not hasattr(self, "rasteriser") or self.rasteriser is None:
            print("ERROR: No rasteriser available")
            return
            
        if not hasattr(self.editor, "scene"):
            print("ERROR: No scene available")
            return
            
        print(f"Scene objects count: {len(self.editor.scene.objects)}")
        if len(self.editor.scene.objects) == 0:
            print("WARNING: Scene is empty")
            return
            
        # Get camera position and matrices
        cam_pos = Vector3(self.camera.pos)
        look_dir = Vector3([
            math.cos(self.camera.yaw) * math.cos(self.camera.pitch),
            math.sin(self.camera.pitch),
            math.sin(self.camera.yaw) * math.cos(self.camera.pitch)
        ])
        view = Matrix44.look_at(cam_pos, cam_pos + look_dir, Vector3([0, 1, 0]))
        projection = Matrix44.perspective_projection(60, self.viewport_width / self.viewport_height, 0.1, 1000.0)

        print(f"Camera position: {cam_pos}")
        print(f"View matrix:\n{view}")
        print(f"Projection matrix:\n{projection}")

        # Draw sky first
        print("Drawing sky...")
        #self.rasteriser.draw_sky(view, projection)

        
        # Draw all scene objects
        print("\nDrawing scene objects:")
        for obj in self.editor.scene.objects:
            print(f"\nObject: {obj.name}")
            print(f"  Type: {obj.type}")
            print(f"  Position: {obj.location}")
            print(f"  Has mesh: {obj.mesh is not None}")
            if obj.mesh:
                print(f"  Mesh vertices: {len(obj.mesh.vertices)//3}")
                print(f"  Mesh indices: {len(obj.mesh.indices)}")
                print(f"  Mesh normals: {len(obj.mesh.normals)//3 if obj.mesh.normals else 0}")
                print(f"  Material: {obj.material}")

                print(f"{obj.name} -> obj.location = {obj.location}")
                
                # Draw object
                self.rasteriser.draw_mesh(
                    mesh=obj.mesh,
                    position=obj.location,
                    rotation=obj.rotation,
                    scale=obj.scale,
                    material=obj.material,
                    view=view,
                    projection=projection,
                    camera_pos=cam_pos
                )
                
                # Draw gizmo for selected object
                if obj == self.selected_object:
                    print(f"[GIZMO] Drawing gizmo for selected object: {obj.name}")
                    self.gizmo.draw(obj.location, obj.rotation)
                    
                    # Draw selection highlight
                    glPushMatrix()
                    glTranslatef(*obj.location)
                    glRotatef(math.degrees(obj.rotation[0]), 1, 0, 0)
                    glRotatef(math.degrees(obj.rotation[1]), 0, 1, 0)
                    glRotatef(math.degrees(obj.rotation[2]), 0, 0, 1)
                    
                    # Draw wireframe box
                    glColor3f(1.0, 1.0, 0.0)  # Yellow
                    glLineWidth(2.0)
                    glBegin(GL_LINE_LOOP)
                    size = 1.0
                    glVertex3f(-size, -size, -size)
                    glVertex3f(size, -size, -size)
                    glVertex3f(size, size, -size)
                    glVertex3f(-size, size, -size)
                    glEnd()
                    
                    glBegin(GL_LINE_LOOP)
                    glVertex3f(-size, -size, size)
                    glVertex3f(size, -size, size)
                    glVertex3f(size, size, size)
                    glVertex3f(-size, size, size)
                    glEnd()
                    
                    glBegin(GL_LINES)
                    glVertex3f(-size, -size, -size)
                    glVertex3f(-size, -size, size)
                    glVertex3f(size, -size, -size)
                    glVertex3f(size, -size, size)
                    glVertex3f(size, size, -size)
                    glVertex3f(size, size, size)
                    glVertex3f(-size, size, -size)
                    glVertex3f(-size, size, size)
                    glEnd()
                    
                    glPopMatrix()
        # Draw the last ray if available
        if self.last_ray_origin is not None and self.last_ray_direction is not None:
            glColor3f(1.0, 0.0, 0.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glVertex3f(*self.last_ray_origin)
            ray_end = self.last_ray_origin + self.last_ray_direction * 1000.0
            glVertex3f(*ray_end)
            glEnd()
        print("=== DRAW WORLD COMPLETE ===\n")

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
            
        # New key handlers for transform modes
        elif key == glfw.KEY_1:  # Translate mode
            self.gizmo.set_transform_mode("translate")
        elif key == glfw.KEY_2:  # Rotate mode
            self.gizmo.set_transform_mode("rotate")
        elif key == glfw.KEY_3:  # Scale mode
            self.gizmo.set_transform_mode("scale")
        elif key == glfw.KEY_ESCAPE:  # Deselect object
            self.selected_object = None
            self.gizmo.selected_axis = None
            self.gizmo.is_dragging = False

    def handle_mouse_press(self, x, y, button, viewport_width, viewport_height):
        if button == Qt.LeftButton:
            self.mouse_pressed = True
            print ("[DEBUG] left mouse button pressed")
            
            # First check if we're clicking on the gizmo
            if self.selected_object and self.gizmo.handle_mouse((x, y), 0, 0, self.camera, viewport_width, viewport_height):
                return

            # Get ray from mouse position
            ray_origin, ray_direction = self.camera.get_ray_from_mouse(
                (x, y), viewport_width, viewport_height
            )
            print(f"[RAY] Origin: {ray_origin}, Direction: {ray_direction}")
            self.last_ray_origin = ray_origin
            self.last_ray_direction = ray_direction
            
            # Create intersection handler and find intersections
            print ("[DEBUG] Creating intersection handler")
            intersection_handler = RayIntersectionHandler()
            print(f"[DEBUG] intersection_handler: {type(intersection_handler)}, id={id(intersection_handler)}")
            intersection_handler.set_ray(ray_origin, ray_direction)
            print (f"[DEBUG] Ray set using {ray_origin} and {ray_direction}")
            print ("[DEBUG] trying to print scene.objects:")
            print(f"[DEBUG] scene.objects: {self.editor.scene.objects}")
            for obj in self.editor.scene.objects:
                print(f"[DEBUG] Object: {getattr(obj, 'name', str(obj))}, mesh: {getattr(obj, 'mesh', None)}")
            try:
                intersections = intersection_handler.find_intersections(self.editor.scene.objects)
            except Exception as e:
                print(f"[ERROR] Exception in find_intersections: {e}")
            print(f"[RAY] Intersections found: {len(intersections)}")
            for obj, dist, point in intersections:
                print(f"[RAY] Hit object: {obj.name}, Distance: {dist}, Point: {point}")
            
            if intersections:
                # Get the closest intersection
                closest_intersection = min(intersections, key=lambda x: x[1])
                self.selected_object = closest_intersection[0]
                print(f"[DEBUG] Object clicked: {self.selected_object.name}")
                
                # Update properties panel
                if hasattr(self.editor, 'properties_panel'):
                    self.editor.properties_panel.set_object(self.selected_object)
                
                # Update hierarchy panel selection
                if hasattr(self.editor, 'hierarchy_panel'):
                    self.editor.hierarchy_panel.highlight_item(self.selected_object.name)
            else:
                self.selected_object = None
                if hasattr(self.editor, 'properties_panel'):
                    self.editor.properties_panel.set_object(None)
                if hasattr(self.editor, 'hierarchy_panel'):
                    self.editor.hierarchy_panel.clearSelection()

    def handle_mouse_release(self, x, y, button):
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.gizmo.is_dragging = False

    def handle_mouse_move(self, x, y):
        if not self.last_mouse_pos:
            self.last_mouse_pos = (x, y)
            return
            
        dx = x - self.last_mouse_pos[0]
        dy = y - self.last_mouse_pos[1]
        
        if self.mouse_pressed and self.selected_object:
            # Handle gizmo interaction
            if self.gizmo.selected_axis:
                self.gizmo.is_dragging = True
                if self.gizmo.transform_mode == "translate":
                    movement = self.gizmo._handle_translate(dx, dy, self.camera)
                    if movement:
                        self.selected_object.location = [
                            self.selected_object.location[0] + movement[0],
                            self.selected_object.location[1] + movement[1],
                            self.selected_object.location[2] + movement[2]
                        ]
                elif self.gizmo.transform_mode == "rotate":
                    rotation = self.gizmo._handle_rotate(dx, dy, self.camera)
                    if rotation:
                        self.selected_object.rotation = [
                            self.selected_object.rotation[0] + rotation[0],
                            self.selected_object.rotation[1] + rotation[1],
                            self.selected_object.rotation[2] + rotation[2]
                        ]
                elif self.gizmo.transform_mode == "scale":
                    scale = self.gizmo._handle_scale(dx, dy, self.camera)
                    if scale:
                        self.selected_object.scale = [
                            self.selected_object.scale[0] * scale[0],
                            self.selected_object.scale[1] * scale[1],
                            self.selected_object.scale[2] * scale[2]
                        ]
                # Update properties panel
                if hasattr(self.editor, 'properties_panel'):
                    self.editor.properties_panel.set_object(self.selected_object)
        
        self.last_mouse_pos = (x, y)

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

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)


class RayIntersectionHandler:
    def __init__(self):
        try:
            print ("\n\n")
            print("[INTERSECT] RayIntersectionHandler constructed")
            self.ray_origin = None
            self.ray_direction = None 
            self.intersections = []
        except Exception as e:
            print(f"Error initializing RayIntersectionHandler: {e}")
            raise
        
    def set_ray(self, origin, direction):
        self.ray_origin = Vector3(origin)
        self.ray_direction = Vector3(direction)
        
    def transform_ray_to_object_space(self, obj):
        """Transform ray from world space to object space"""
        try:
            # Create transformation matrices
            translation = Matrix44.from_translation(Vector3(obj.location))
            rotation = Matrix44.from_eulers(Vector3(obj.rotation))
            scale = Matrix44.from_scale(Vector3(obj.scale))
            
            # Combine transformations
            obj_matrix = translation * rotation * scale
            inv_matrix = obj_matrix.inverse
            
            # Transform ray points to homogeneous coordinates
            ray_origin_h = np.array([*self.ray_origin, 1.0], dtype=np.float32)
            ray_end_h = np.array([*(self.ray_origin + self.ray_direction * 1000.0), 1.0], dtype=np.float32)
            
            # Transform points using matrix multiplication
            ray_origin_obj_h = np.dot(inv_matrix, ray_origin_h)
            ray_end_obj_h = np.dot(inv_matrix, ray_end_h)
            
            # Convert back to 3D vectors and normalize
            # Use numpy operations for division to avoid pyrr matrix operations
            ray_origin_obj = Vector3(np.array(ray_origin_obj_h[:3]) / ray_origin_obj_h[3])
            ray_end_obj = Vector3(np.array(ray_end_obj_h[:3]) / ray_end_obj_h[3])
            print(f"[INTERSECT]   ray_origin_obj: {ray_origin_obj}, ray_end_obj: {ray_end_obj}")
            direction_vec = Vector3(ray_end_obj - ray_origin_obj)
            print(f"[INTERSECT]   direction_vec: {direction_vec}, length: {direction_vec.length}")
            if direction_vec.length == 0:
                print("[INTERSECT]   Zero-length ray direction in object space! Skipping object.")
                return ray_origin_obj, None, obj_matrix
            ray_dir_obj = direction_vec.normalized
            
            print(f"[INTERSECT]   Ray in object space: origin={ray_origin_obj}, dir={ray_dir_obj}")
            
            return ray_origin_obj, ray_dir_obj, obj_matrix
            
        except Exception as e:
            print(f"Error in transform_ray_to_object_space: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
        
    def test_triangle_intersection(self, v0, v1, v2, ray_origin, ray_dir):
        """Test ray-triangle intersection using Möller–Trumbore algorithm"""
        try:
            # Ensure all inputs are Vector3
            v0 = Vector3(v0)
            v1 = Vector3(v1)
            v2 = Vector3(v2)
            ray_origin = Vector3(ray_origin)
            ray_dir = Vector3(ray_dir)
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            h = ray_dir.cross(edge2)
            a = edge1.dot(h)
            
            if abs(a) < 1e-6:  # Ray is parallel to triangle
                return None
                
            f = 1.0 / a
            s = ray_origin - v0
            u = f * s.dot(h)
            
            if u < 0.0 or u > 1.0:
                return None
                
            q = s.cross(edge1)
            v = f * ray_dir.dot(q)
            
            if v < 0.0 or u + v > 1.0:
                return None
                
            t = f * edge2.dot(q)
            
            if t > 1e-6:  # Intersection found
                return t
                
            return None
        except Exception as e:
            print(f"[INTERSECT] Error in test_triangle_intersection: {e}")
            return None
        
    def transform_intersection_to_world_space(self, intersection_obj, obj_matrix):
        """Transform intersection point from object space back to world space"""
        try:
            # Convert intersection point to homogeneous coordinates
            intersection_h = np.array([*intersection_obj, 1.0], dtype=np.float32)
            
            # Transform using matrix multiplication
            intersection_world_h = np.dot(obj_matrix, intersection_h)
            
            # Convert back to 3D vector, handling perspective division
            if abs(intersection_world_h[3]) > 1e-6:  # Avoid division by zero
                intersection_world = Vector3([
                    intersection_world_h[0] / intersection_world_h[3],
                    intersection_world_h[1] / intersection_world_h[3],
                    intersection_world_h[2] / intersection_world_h[3]
                ])
            else:
                intersection_world = Vector3([
                    intersection_world_h[0],
                    intersection_world_h[1],
                    intersection_world_h[2]
                ])
                
            return intersection_world
        except Exception as e:
            print(f"[INTERSECT] Error in transform_intersection_to_world_space: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def find_intersections(self, objects):
        print("[INTERSECT] find_intersections CALLED")
        self.intersections = []
        print("[INTERSECT] Starting intersection tests...")
        for obj in objects:
            print(f"[INTERSECT] Checking object: {getattr(obj, 'name', str(obj))}")
            if not obj.mesh:
                print("[INTERSECT]   No mesh, skipping.")
                continue
            try:
                # Transform ray to object space
                ray_origin_obj, ray_dir_obj, obj_matrix = self.transform_ray_to_object_space(obj)
                print(f"[INTERSECT]   Ray in object space: origin={ray_origin_obj}, dir={ray_dir_obj}")
                vertices = obj.mesh.vertices
                indices = obj.mesh.indices
                print(f"[INTERSECT]   Mesh vertices: {len(vertices)//3}, indices: {len(indices)}")
                found = False
                for i in range(0, len(indices), 3):
                    # Extract vertex positions as Vector3
                    v0 = Vector3(vertices[indices[i]*3:indices[i]*3+3])
                    v1 = Vector3(vertices[indices[i+1]*3:indices[i+1]*3+3])
                    v2 = Vector3(vertices[indices[i+2]*3:indices[i+2]*3+3])
                    
                    t = self.test_triangle_intersection(v0, v1, v2, ray_origin_obj, ray_dir_obj)
                    if t is not None:
                        intersection_obj = ray_origin_obj + ray_dir_obj * t
                        intersection = self.transform_intersection_to_world_space(intersection_obj, obj_matrix)
                        dist = (intersection - self.ray_origin).length
                        self.intersections.append((obj, dist, intersection))
                        found = True
                        print(f"[INTERSECT]   Found intersection at distance {dist}")
                if found:
                    print(f"[INTERSECT]   Intersection found for object: {getattr(obj, 'name', str(obj))}")
                else:
                    print(f"[INTERSECT]   No intersection for object: {getattr(obj, 'name', str(obj))}")
            except Exception as e:
                print(f"[INTERSECT]   Error testing object {getattr(obj, 'name', str(obj))}: {e}")
                import traceback
                traceback.print_exc()
                continue
        print(f"[INTERSECT] Total intersections found: {len(self.intersections)}")
        # Sort intersections by distance
        self.intersections.sort(key=lambda x: x[1])
        return self.intersections


    
