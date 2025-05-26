from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget,
                                 QWidget, QVBoxLayout, QLabel, QListWidget,
                                 QTextEdit, QFileSystemModel, QTreeView, QPushButton, QMenu, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QToolTip, QCheckBox)
from PySide6.QtCore import Qt, QDir, QTimer, QTime
from PySide6.QtGui import QAction
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective
import sys
import math
import numpy as np
from .editor_camera import EditorCamera
from rendering.texture_loader import load_cubemap
from rendering.rasteriser import Rasteriser
from pyrr import Vector3, Matrix44
from rendering.my_shaders import Material
import os
import pywavefront
from PIL import Image

class GLViewport(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = EditorCamera()
        self.camera.pitch = -0.3  # Look down a small amount
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        self.last_mouse_pos = None
        self.mouse_wheel = 0
        self.skybox_tex = None
        self.keys_pressed = set()  # Track currently pressed keys
        self.last_update_time = None
        self.view_type = "Lit"
        self._init_view_type_button()
        self.setAcceptDrops(True)
        self.rasteriser = None
        self.editor_renderer = None
        print("GLViewport initialized")

    def _init_view_type_button(self):
        self.view_type_button = QPushButton(self.view_type, self)
        self.view_type_button.setFixedSize(60, 28)
        self.view_type_button.move(10, 10)
        self.view_type_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(40, 40, 40, 200);
                color: white;
                border: 1px solid #888;
                border-radius: 6px;
                font-weight: bold;
            }
            """
        )
        self.view_type_menu = QMenu(self)
        self.view_type_actions = {}
        for view in ["Lit", "Unlit"]:
            action = self.view_type_menu.addAction(view, lambda v=view: self.set_view_type(v))
            action.setCheckable(True)
            self.view_type_actions[view] = action
        self.view_type_button.setMenu(self.view_type_menu)
        self._update_view_type_checks()

    def set_view_type(self, view_type):
        self.view_type = view_type
        self.view_type_button.setText(view_type)
        self._update_view_type_checks()
        self.update()

    def _update_view_type_checks(self):
        for view, action in self.view_type_actions.items():
            action.setChecked(view == self.view_type)

    def initializeGL(self):
        print("GLViewport.initializeGL called")
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        self.rasteriser = Rasteriser()
        self.skybox_tex = self.rasteriser.sky_texture
        print("Skybox HDR texture loaded via Rasteriser")
        
        # Initialize the editor renderer
        parent = self.parent()
        print(f"Parent type: {type(parent)}")
        if parent and hasattr(parent, "scene"):
            print(f"Parent has scene: {parent.scene}")
            from .editor_render import EditorRenderer
            self.editor_renderer = EditorRenderer(parent.scene, parent)
            self.editor_renderer.rasteriser = self.rasteriser
            print("EditorRenderer initialized successfully")
        else:
            print("ERROR: Parent has no scene attribute or parent is None")
            print(f"Parent attributes: {dir(parent) if parent else 'None'}")

    def paintGL(self):
        # Calculate delta time
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if self.last_update_time is None:
            self.last_update_time = current_time
        dt = (current_time - self.last_update_time) / 1000.0  # Convert to seconds
        self.last_update_time = current_time

        # Update camera with current keys
        keys = {key: True for key in self.keys_pressed}
        self.camera.update(dt, keys, 0, 0, (0, 0), self.mouse_wheel)
        self.mouse_wheel = 0  # Reset wheel after use

        # Restore clear color to original dark gray
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # --- Legacy grid drawing ---
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, self.width() / self.height() if self.height() != 0 else 1, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply_view()
        self.draw_grid()  # Only grid or legacy stuff here

        # --- Modern mesh drawing ---
        # DO NOT touch OpenGL matrix state here!
        view, projection = self.camera.get_view_and_projection(self.width(), self.height())
        scene = self.parent().scene
        for obj in scene.objects:
            self.rasteriser.draw_mesh(
                mesh=obj.mesh,
                position=obj.location,
                rotation=obj.rotation,
                scale=obj.scale,
                material=obj.material,
                view=view,
                projection=projection,
                camera_pos=Vector3(self.camera.pos)
            )

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def draw_grid(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Calculate grid size based on camera position
        camera_distance = math.sqrt(
            self.camera.pos[0] * self.camera.pos[0] +
            self.camera.pos[1] * self.camera.pos[1] +
            self.camera.pos[2] * self.camera.pos[2]
        )
        
        # Make grid size proportional to camera distance
        grid_size = max(100, int(camera_distance * 2))
        fade_distance = grid_size * 0.5  # Only draw within 50% of grid size
        
        # Calculate grid bounds based on camera position
        cam_x = int(self.camera.pos[0])
        cam_z = int(self.camera.pos[2])
        
        # Calculate visible grid range
        min_x = cam_x - int(fade_distance)
        max_x = cam_x + int(fade_distance)
        min_z = cam_z - int(fade_distance)
        max_z = cam_z + int(fade_distance)
        
        # Draw minor grid lines (1 meter spacing)
        glBegin(GL_LINES)
        # Draw lines along X axis
        for z in range(min_z, max_z + 1):
            # Calculate fade factor based on distance from camera
            dz = z - self.camera.pos[2]
            dist = abs(dz)
            if dist <= fade_distance:
                alpha = 1.0 - (dist / fade_distance)
                glColor4f(0.2, 0.2, 0.2, alpha)
                glVertex3f(min_x, 0, z)
                glVertex3f(max_x, 0, z)
        
        # Draw lines along Z axis
        for x in range(min_x, max_x + 1):
            # Calculate fade factor based on distance from camera
            dx = x - self.camera.pos[0]
            dist = abs(dx)
            if dist <= fade_distance:
                alpha = 1.0 - (dist / fade_distance)
                glColor4f(0.2, 0.2, 0.2, alpha)
                glVertex3f(x, 0, min_z)
                glVertex3f(x, 0, max_z)
        glEnd()
        
        # Draw major grid lines (10 meter spacing)
        glBegin(GL_LINES)
        # Draw lines along X axis
        for z in range(min_z - (min_z % 10), max_z + 1, 10):
            # Calculate fade factor based on distance from camera
            dz = z - self.camera.pos[2]
            dist = abs(dz)
            if dist <= fade_distance:
                alpha = 1.0 - (dist / fade_distance)
                glColor4f(0.3, 0.3, 0.3, alpha)
                glVertex3f(min_x, 0, z)
                glVertex3f(max_x, 0, z)
        
        # Draw lines along Z axis
        for x in range(min_x - (min_x % 10), max_x + 1, 10):
            # Calculate fade factor based on distance from camera
            dx = x - self.camera.pos[0]
            dist = abs(dx)
            if dist <= fade_distance:
                alpha = 1.0 - (dist / fade_distance)
                glColor4f(0.3, 0.3, 0.3, alpha)
                glVertex3f(x, 0, min_z)
                glVertex3f(x, 0, max_z)
        glEnd()
        
        glDisable(GL_BLEND)

    #Wrapper for the renderer's draw_world
    def draw_world(self):
        if self.editor_renderer is not None:
            print("GLViewport.draw_world: Calling editor_renderer.draw_world()")
            self.editor_renderer.draw_world()
        else:
            print("WARNING: editor_renderer is None in draw_world")

    def draw_skybox(self):
        if not self.skybox_tex:
            return
        # Use Rasteriser's draw_sky method for HDR sky
        if self.rasteriser:
            # You need to pass view and projection matrices; here we use identity for demo
            view = np.identity(4, dtype=np.float32)
            projection = np.identity(4, dtype=np.float32)
            self.rasteriser.draw_sky(view, projection)
        else:
            print("WARNING: Rasteriser not initialized for skybox drawing")

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.position()
        if event.button() == Qt.RightButton:
            self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setCursor(Qt.ArrowCursor)
        self.last_mouse_pos = None

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is not None:
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()
            self.camera.update(0.016, {}, dx, dy, (event.position().x(), event.position().y()), self.mouse_wheel)
            self.last_mouse_pos = event.position()
            self.update()

    def wheelEvent(self, event):
        self.mouse_wheel = event.angleDelta().y() / 120
        self.camera.update(0.016, {}, 0, 0, (0, 0), self.mouse_wheel)
        self.update()

    def keyPressEvent(self, event):
        # Add key to pressed set
        if event.key() == Qt.Key_W:
            self.keys_pressed.add('W')
        elif event.key() == Qt.Key_S:
            self.keys_pressed.add('S')
        elif event.key() == Qt.Key_A:
            self.keys_pressed.add('A')
        elif event.key() == Qt.Key_D:
            self.keys_pressed.add('D')
        elif event.key() == Qt.Key_Space:
            self.keys_pressed.add('SPACE')
        elif event.key() == Qt.Key_Shift:
            self.keys_pressed.add('LEFT_SHIFT')
        elif event.key() == Qt.Key_Control:
            self.keys_pressed.add('LEFT_CONTROL')
        elif event.key() == Qt.Key_E:
            self.keys_pressed.add('E')
        elif event.key() == Qt.Key_Q:
            self.keys_pressed.add('Q')
        
        self.update()

    def keyReleaseEvent(self, event):
        # Remove key from pressed set
        if event.key() == Qt.Key_W:
            self.keys_pressed.discard('W')
        elif event.key() == Qt.Key_S:
            self.keys_pressed.discard('S')
        elif event.key() == Qt.Key_A:
            self.keys_pressed.discard('A')
        elif event.key() == Qt.Key_D:
            self.keys_pressed.discard('D')
        elif event.key() == Qt.Key_Space:
            self.keys_pressed.discard('SPACE')
        elif event.key() == Qt.Key_Shift:
            self.keys_pressed.discard('LEFT_SHIFT')
        elif event.key() == Qt.Key_Control:
            self.keys_pressed.discard('LEFT_CONTROL')
        elif event.key() == Qt.Key_E:
            self.keys_pressed.discard('E')
        elif event.key() == Qt.Key_Q:
            self.keys_pressed.discard('Q')
        
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"Attempting to load file: {file_path}")  # Debug log
                if file_path.endswith('.obj'):
                    try:
                        # Convert screen position to world space using ray-plane intersection
                        mouse_pos = (event.position().x(), event.position().y())
                        print(f"Mouse position: {mouse_pos}")  # Debug log
                        origin, direction = self.camera.get_ray_from_mouse(mouse_pos, self.width(), self.height())
                        print(f"Ray origin: {origin}, direction: {direction}")  # Debug log
                        
                        # Ray-plane intersection with ground (y=0)
                        if abs(direction[1]) > 1e-6:  # Avoid division by zero
                            t = -origin[1] / direction[1]
                            drop_pos = origin + t * direction
                            # Round to nearest grid point
                            drop_pos = [round(drop_pos[0]), 0.0, round(drop_pos[2])]
                            print(f"Calculated drop position: {drop_pos}")  # Debug log
                        else:
                            # If ray is parallel to ground, use a default position
                            drop_pos = [5.0, 0.0, 5.0]
                            print(f"Using default drop position: {drop_pos}")  # Debug log
                        
                        # Add the object to the scene
                        self.parent().add_object_to_scene_from_file(file_path, drop_pos)
                        print(f"Successfully added object to scene at {drop_pos}")  # Debug log
                    except Exception as e:
                        print(f"Error adding object to scene: {e}")  # Debug log
                        # Try adding with default position if there's an error
                        self.parent().add_object_to_scene_from_file(file_path, [5.0, 0.0, 5.0])
            event.acceptProposedAction()

class HierarchyPanel(QListWidget):
    def __init__(self):
        super().__init__()
        self.addItems(["Cube", "Sphere", "Camera"])

    def update_items(self, names):
        self.clear()
        self.addItems(names)

class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.type_label = QLabel()
        self.location_edits = [QLineEdit(), QLineEdit(), QLineEdit()]
        self.rotation_edits = [QLineEdit(), QLineEdit(), QLineEdit()]
        self.scale_edits = [QLineEdit(), QLineEdit(), QLineEdit()]

        # Material fields
        self.base_color_edits = [QLineEdit(), QLineEdit(), QLineEdit()]
        self.metallic_edit = QLineEdit()
        self.roughness_edit = QLineEdit()
        self.specular_edit = QLineEdit()
        self.emissive_color_edits = [QLineEdit(), QLineEdit(), QLineEdit()]

        # Set up layouts for float3 fields
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Type:", self.type_label)
        self.layout.addRow("Location:", self._make_row(self.location_edits))
        self.layout.addRow("Rotation:", self._make_row(self.rotation_edits))
        self.layout.addRow("Scale:", self._make_row(self.scale_edits))
        self.layout.addRow("Base Color:", self._make_row(self.base_color_edits))
        self.layout.addRow("Metallic:", self.metallic_edit)
        self.layout.addRow("Roughness:", self.roughness_edit)
        self.layout.addRow("Specular:", self.specular_edit)
        self.layout.addRow("Emissive Color:", self._make_row(self.emissive_color_edits))

        # Disable editing type
        self.type_label.setStyleSheet("background: #eee; padding: 4px;")
        self.type_label.setMinimumWidth(60)
        self.type_label.setMaximumHeight(24)

        # Store current object
        self.current_obj = None

        # Connect signals
        self.name_edit.editingFinished.connect(self._on_name_changed)
        for i, edits in enumerate([self.location_edits, self.rotation_edits, self.scale_edits]):
            for j, edit in enumerate(edits):
                edit.editingFinished.connect(self._make_on_vec3_changed(i, j))
        for i, edit in enumerate(self.base_color_edits):
            edit.editingFinished.connect(self._make_on_material_vec3_changed("base_color", i))
        self.metallic_edit.editingFinished.connect(self._on_material_scalar_changed("metallic"))
        self.roughness_edit.editingFinished.connect(self._on_material_scalar_changed("roughness"))
        self.specular_edit.editingFinished.connect(self._on_material_scalar_changed("specular"))
        for i, edit in enumerate(self.emissive_color_edits):
            edit.editingFinished.connect(self._make_on_material_vec3_changed("emissive_color", i))

    def _make_row(self, edits):
        row = QHBoxLayout()
        for label, edit in zip("XYZ", edits):
            row.addWidget(QLabel(label))
            row.addWidget(edit)
        container = QWidget()
        container.setLayout(row)
        return container

    def set_object(self, obj):
        self.current_obj = obj
        if obj is None:
            self.name_edit.setText("")
            self.type_label.setText("")
            for edits in [self.location_edits, self.rotation_edits, self.scale_edits]:
                for edit in edits:
                    edit.setText("")
            for edit in self.base_color_edits + self.emissive_color_edits:
                edit.setText("")
            self.metallic_edit.setText("")
            self.roughness_edit.setText("")
            self.specular_edit.setText("")
            self.set_fields_enabled(False)
            return

        self.name_edit.setText(obj.name)
        self.type_label.setText(obj.type)
        # For location only, swap Y and Z
        loc = obj.location
        loc_swapped = [loc[0], loc[2], loc[1]]  # X, Z, Y

        for edits, values in zip(
            [self.location_edits, self.rotation_edits, self.scale_edits],
            [loc_swapped, obj.rotation, obj.scale]
        ):
            for edit, value in zip(edits, values):
                edit.setText(str(value))
                edit.setEnabled(True)
        self.name_edit.setEnabled(True)

        if hasattr(obj, "material") and obj.material:
            mat = obj.material
            for edit, value in zip(self.base_color_edits, mat.base_color):
                edit.setText(str(value))
                edit.setEnabled(True)
            self.metallic_edit.setText(str(mat.metallic))
            self.metallic_edit.setEnabled(True)
            self.roughness_edit.setText(str(mat.roughness))
            self.roughness_edit.setEnabled(True)
            self.specular_edit.setText(str(mat.specular))
            self.specular_edit.setEnabled(True)
            for edit, value in zip(self.emissive_color_edits, mat.emissive_color):
                edit.setText(str(value))
                edit.setEnabled(True)
        else:
            for edit in self.base_color_edits + self.emissive_color_edits:
                edit.setText("")
                edit.setEnabled(False)
            self.metallic_edit.setText("")
            self.metallic_edit.setEnabled(False)
            self.roughness_edit.setText("")
            self.roughness_edit.setEnabled(False)
            self.specular_edit.setText("")
            self.specular_edit.setEnabled(False)

        self.set_fields_enabled(True)

    def _on_name_changed(self):
        if self.current_obj:
            self.current_obj.name = self.name_edit.text()

    def _make_on_vec3_changed(self, vec_index, comp_index):
        # vec_index: 0=location, 1=rotation, 2=scale
        def handler():
            if self.current_obj:
                edit = [self.location_edits, self.rotation_edits, self.scale_edits][vec_index][comp_index]
                text = edit.text()
                try:
                    value = float(text)
                    [self.current_obj.location, self.current_obj.rotation, self.current_obj.scale][vec_index][comp_index] = value
                    edit.setToolTip("")  # Clear tooltip on valid input
                except ValueError:
                    # Restore previous value from the object
                    prev_value = [self.current_obj.location, self.current_obj.rotation, self.current_obj.scale][vec_index][comp_index]
                    QToolTip.showText(edit.mapToGlobal(edit.rect().bottomLeft()), f"'{text}' is not a valid number.", edit)
                    edit.setText(str(prev_value))
        return handler

    def _make_on_material_vec3_changed(self, attr, idx):
        def handler():
            if self.current_obj and hasattr(self.current_obj, "material"):
                edit = getattr(self, f"{attr}_edits")[idx]
                text = edit.text()
                try:
                    value = float(text)
                    color = list(getattr(self.current_obj.material, attr))
                    color[idx] = value
                    setattr(self.current_obj.material, attr, tuple(color))
                    edit.setToolTip("")
                except ValueError:
                    prev_value = getattr(self.current_obj.material, attr)[idx]
                    QToolTip.showText(edit.mapToGlobal(edit.rect().bottomLeft()), f"'{text}' is not a valid number.", edit)
                    edit.setText(str(prev_value))
        return handler

    def _on_material_scalar_changed(self, attr):
        def handler():
            if self.current_obj and hasattr(self.current_obj, "material"):
                edit = getattr(self, f"{attr}_edit")
                text = edit.text()
                try:
                    value = float(text)
                    setattr(self.current_obj.material, attr, value)
                    edit.setToolTip("")
                except ValueError:
                    prev_value = getattr(self.current_obj.material, attr)
                    QToolTip.showText(edit.mapToGlobal(edit.rect().bottomLeft()), f"'{text}' is not a valid number.", edit)
                    edit.setText(str(prev_value))
        return handler

    def set_fields_enabled(self, enabled):
        # Transform fields
        for edits in [self.location_edits, self.rotation_edits, self.scale_edits]:
            for edit in edits:
                edit.setEnabled(enabled)
        # Material fields
        for edit in self.base_color_edits + self.emissive_color_edits:
            edit.setEnabled(enabled)
        self.metallic_edit.setEnabled(enabled)
        self.roughness_edit.setEnabled(enabled)
        self.specular_edit.setEnabled(enabled)
        # Name field
        self.name_edit.setEnabled(enabled)

class ContentBrowser(QTreeView):
    def __init__(self):
        super().__init__()
        model = QFileSystemModel()
        model.setRootPath(QDir.currentPath())
        self.setModel(model)
        self.setRootIndex(model.index(QDir.currentPath()))
        self.setDragEnabled(True)

class Scene:
    def __init__(self):
        self.objects = []  # List of scene objects

    def add_object(self, obj):
        self.objects.append(obj)
        # Signal or callback to update UI

    def remove_object(self, obj):
        self.objects.remove(obj)
        # Signal or callback to update UI

    def get_object_names(self):
        return [obj.name for obj in self.objects]

class SceneObject:
    def __init__(self, name, obj_type, mesh=None, location=None, rotation=None, scale=None, material=None):
        self.name = name
        self.type = obj_type
        self.mesh = mesh  # This will be a MeshData object
        self.location = location if location is not None else [0.0, 0.0, 0.0]
        self.rotation = rotation if rotation is not None else [0.0, 0.0, 0.0]
        self.scale = scale if scale is not None else [1.0, 1.0, 1.0]
        self.material = material if material is not None else Material()
        # Add more properties as needed (transform, mesh, etc.)

class MeshData:
    def __init__(self, vertices, normals, indices, uvs=None):
        self.vertices = vertices
        self.normals = normals
        self.indices = indices
        self.uvs = uvs

    @staticmethod
    def load_obj_mesh(file_path):
        try:
            # First try to load with materials
            scene = pywavefront.Wavefront(file_path, collect_faces=True, parse=True)
        except Exception as e:
            print(f"Error loading with materials, falling back to basic parsing: {e}")
            # If that fails, try loading without materials
            try:
                scene = pywavefront.Wavefront(file_path, collect_faces=True, parse=False)
                # Manually parse the file to extract vertices and faces
                with open(file_path, 'r') as f:
                    vertices = []
                    normals = []
                    uvs = []
                    faces = []
                    for line in f:
                        if line.startswith('v '):  # Vertex
                            v = list(map(float, line.split()[1:4]))
                            vertices.extend(v)
                        elif line.startswith('vn '):  # Normal
                            n = list(map(float, line.split()[1:4]))
                            normals.extend(n)
                        elif line.startswith('vt '):  # UV
                            t = list(map(float, line.split()[1:3]))
                            uvs.extend(t)
                        elif line.startswith('f '):  # Face
                            face = line.split()[1:]
                            faces.append(face)
                    # Triangulate faces
                    indices = []
                    for face in faces:
                        if len(face) < 3:
                            continue  # skip degenerate faces
                        # Convert face indices to vertex indices
                        idxs = [int(part.split('/')[0]) - 1 for part in face]
                        # Fan triangulation
                        for i in range(1, len(idxs) - 1):
                            indices.extend([idxs[0], idxs[i], idxs[i + 1]])
                    mesh_data = MeshData(
                        vertices=vertices,
                        normals=normals if normals else [0.0, 1.0, 0.0] * (len(vertices) // 3),
                        indices=indices,
                        uvs=uvs if uvs else [0.0, 0.0] * (len(vertices) // 3)
                    )
                    return mesh_data, (0.8, 0.8, 0.8)  # Light grey color
            except Exception as e:
                print(f"Error in basic parsing: {e}")
                raise

        # If we got here, we have a valid scene with materials
        vertices = []
        normals = []
        indices = []
        uvs = []
        materials = {}

        vertex_map = {}
        for mesh in scene.mesh_list:
            # Extract material if present
            mat = None
            if hasattr(mesh, 'materials') and mesh.materials:
                mat = mesh.materials[0]  # Use the first material for now
                materials[mesh.name] = mat

            for face in mesh.faces:
                for idx in face:
                    v = scene.vertices[idx]
                    key = tuple(v)
                    if key not in vertex_map:
                        vertex_map[key] = len(vertices) // 3
                        vertices.extend(v[:3])
                        if len(v) >= 6:
                            normals.extend(v[3:6])
                        else:
                            normals.extend([0.0, 0.0, 0.0])
                        if len(v) >= 8:
                            uvs.extend(v[6:8])
                        else:
                            uvs.extend([0.0, 0.0])
                    indices.append(vertex_map[key])

        # Extract material properties for the first mesh/material
        mat = next(iter(materials.values()), None)
        if mat:
            base_color = tuple(getattr(mat, 'diffuse', (0.8, 0.8, 0.8)))  # Light grey as fallback
        else:
            base_color = (0.8, 0.8, 0.8)  # Light grey as default

        mesh_data = MeshData(vertices, normals, indices, uvs)
        return mesh_data, base_color

class CameraOptionsPanel(QWidget):
    def __init__(self, viewport):
        super().__init__()
        self.viewport = viewport
        self.layout = QFormLayout(self)
        # Position fields
        self.pos_edits = [QLineEdit(), QLineEdit(), QLineEdit()]
        pos_row = QHBoxLayout()
        for label, edit in zip("XYZ", self.pos_edits):
            pos_row.addWidget(QLabel(label))
            pos_row.addWidget(edit)
        pos_container = QWidget()
        pos_container.setLayout(pos_row)
        self.layout.addRow("Position:", pos_container)
        # Pitch, Yaw, Roll fields
        self.pitch_edit = QLineEdit()
        self.yaw_edit = QLineEdit()
        self.roll_edit = QLineEdit()
        self.layout.addRow("Pitch:", self.pitch_edit)
        self.layout.addRow("Yaw:", self.yaw_edit)
        self.layout.addRow("Roll:", self.roll_edit)
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_camera)
        self.layout.addRow(self.reset_btn)
        # Connect edits
        for i, edit in enumerate(self.pos_edits):
            edit.editingFinished.connect(self._make_on_pos_changed(i))
        self.pitch_edit.editingFinished.connect(self._on_pitch_changed)
        self.yaw_edit.editingFinished.connect(self._on_yaw_changed)
        self.roll_edit.editingFinished.connect(self._on_roll_changed)
        # Timer for live update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_fields)
        self.timer.start(100)
        self._updating = False
        # Store last displayed values
        self._last_displayed = None

    def reset_camera(self):
        cam = self.viewport.camera
        cam.pos = [0.0, 0.0, 0.0]
        cam.pitch = 0.0
        cam.yaw = 0.0
        cam.roll = 0.0
        self.update_fields()

    def _make_on_pos_changed(self, idx):
        def handler():
            if self._updating:
                return
            try:
                value = float(self.pos_edits[idx].text())
                self.viewport.camera.pos[idx] = value
            except ValueError:
                pass
        return handler

    def _on_pitch_changed(self):
        if self._updating:
            return
        try:
            self.viewport.camera.pitch = float(self.pitch_edit.text())
        except ValueError:
            pass

    def _on_yaw_changed(self):
        if self._updating:
            return
        try:
            self.viewport.camera.yaw = float(self.yaw_edit.text())
        except ValueError:
            pass

    def _on_roll_changed(self):
        if self._updating:
            return
        try:
            self.viewport.camera.roll = float(self.roll_edit.text())
        except ValueError:
            pass

    def update_fields(self):
        self._updating = True
        cam = self.viewport.camera
        values = [
            f"{cam.pos[0]:.4f}", f"{cam.pos[1]:.4f}", f"{cam.pos[2]:.4f}",
            f"{cam.pitch:.4f}", f"{cam.yaw:.4f}", f"{cam.roll:.4f}"
        ]
        if self._last_displayed == values:
            self._updating = False
            return
        for i, edit in enumerate(self.pos_edits):
            edit.setText(values[i])
        self.pitch_edit.setText(values[3])
        self.yaw_edit.setText(values[4])
        self.roll_edit.setText(values[5])
        self._last_displayed = values
        self._updating = False

class MainEditor(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        print("MainEditor initializing with scene:", scene)
        self.scene = scene
        self.setWindowTitle("3D Editor")
        self.setGeometry(100, 100, 1280, 720)

        # Central OpenGL viewport
        self.viewport = GLViewport(self)
        self.setCentralWidget(self.viewport)
        print("Viewport created and set as central widget")

        # Hierarchy dock (left)
        self.hierarchy_dock = QDockWidget("World Outliner", self)
        self.hierarchy_panel = HierarchyPanel()
        self.hierarchy_dock.setWidget(self.hierarchy_panel)
        self.hierarchy_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.hierarchy_dock)

        # Properties dock (right)
        self.properties_dock = QDockWidget("Details", self)
        self.properties_panel = PropertiesPanel()
        self.properties_dock.setWidget(self.properties_panel)
        self.properties_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self.resizeDocks([self.properties_dock], [150], Qt.Horizontal)

        # Camera options dock (right, below Details)
        self.camera_options_dock = QDockWidget("Camera Options", self)
        self.camera_options_panel = CameraOptionsPanel(self.viewport)
        self.camera_options_dock.setWidget(self.camera_options_panel)
        self.camera_options_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.camera_options_dock)
        self.tabifyDockWidget(self.properties_dock, self.camera_options_dock)
        self.camera_options_dock.raise_()

        # Content browser dock (bottom)
        self.content_dock = QDockWidget("Content Browser", self)
        self.content_browser = ContentBrowser()
        self.content_dock.setWidget(self.content_browser)
        self.content_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.content_dock)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(QAction("New Scene", self))
        file_menu.addAction(QAction("Open Scene", self))
        file_menu.addAction(QAction("Save Scene", self))
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        # Set up timer for continuous updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_viewport)
        self.timer.start(16)  # ~60 FPS

        self.hierarchy_panel.update_items(self.scene.get_object_names())
        self.hierarchy_panel.currentTextChanged.connect(self.on_outliner_selection)
        self.hierarchy_panel.itemDoubleClicked.connect(self.on_outliner_double_click)
        print("MainEditor initialization complete")

    def update_viewport(self):
        self.viewport.update()

    def keyPressEvent(self, event):
        # Forward to viewport for camera controls
        self.viewport.keyPressEvent(event)
        # Handle deletion
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_items = self.hierarchy_panel.selectedItems()
            if selected_items:
                name = selected_items[0].text()
                obj = next((o for o in self.scene.objects if o.name == name), None)
                if obj:
                    self.remove_object(obj)
                    self.properties_panel.set_object(None)
                    self.hierarchy_panel.clearSelection()
        else:
            super().keyPressEvent(event)

    def add_object(self, obj):
        self.scene.add_object(obj)
        self.hierarchy_panel.update_items(self.scene.get_object_names())
        # Select the new object in the outliner
        items = self.hierarchy_panel.findItems(obj.name, Qt.MatchExactly)
        if items:
            self.hierarchy_panel.setCurrentItem(items[0])

    def remove_object(self, obj):
        self.scene.remove_object(obj)
        self.hierarchy_panel.update_items(self.scene.get_object_names())

    def add_object_to_scene_from_file(self, file_path, position=None):
        from .editor_UI import MeshData, SceneObject
        mesh, base_color = MeshData.load_obj_mesh(file_path)
        name = os.path.basename(file_path)
        print(f"Adding object at world-space position: {position}")  # Debug

        location = position if position is not None else [0.0, 0.0, 0.0]

        scene_obj = SceneObject(
            name=name,
            obj_type="Mesh",
            mesh=mesh,
            location=location,
            material=Material(base_color=base_color)
        )
        self.add_object(scene_obj)
        print("Added object to scene:", name)

    def on_outliner_selection(self, name):
        selected_obj = next((obj for obj in self.scene.objects if obj.name == name), None)
        self.properties_panel.set_object(selected_obj)

    def on_outliner_double_click(self, item):
        name = item.text()
        selected_obj = next((obj for obj in self.scene.objects if obj.name == name), None)
        if selected_obj:
            # Move the camera to the object's location (optionally offset Y for a better view)
            self.viewport.camera.pos = [
                selected_obj.location[0],
                selected_obj.location[1] + 5.0,  # Raise camera above the object
                selected_obj.location[2] + 5.0   # Move camera back a bit
            ]
            # Optionally, look at the object
            self.viewport.camera.pitch = -0.5  # Look down a bit
            self.viewport.camera.yaw = 0.0     # Reset yaw (optional)
            self.viewport.update()

    def get_unique_name(self, base_name):
        names = set(obj.name for obj in self.scene.objects)
        if base_name not in names:
            return base_name
        i = 1
        while f"{base_name} ({i})" in names:
            i += 1
        return f"{base_name} ({i})"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = Scene()
    editor = MainEditor(scene)
    editor.show()
    sys.exit(app.exec())
