from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget,
                                 QWidget, QVBoxLayout, QLabel, QListWidget,
                                 QTextEdit, QFileSystemModel, QTreeView, QPushButton, QMenu, QFormLayout, QHBoxLayout, QLineEdit)
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

class GLViewport(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = EditorCamera()
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        self.last_mouse_pos = None
        self.mouse_wheel = 0
        self.skybox_tex = None
        self.keys_pressed = set()  # Track currently pressed keys
        self.last_update_time = None
        self.view_type = "Lit"
        self._init_view_type_button()
        self.setAcceptDrops(True)

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
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        # Load skybox cubemap
        faces = [
            'assets/skybox/right.png',
            'assets/skybox/left.png',
            'assets/skybox/top.png',
            'assets/skybox/bottom.png',
            'assets/skybox/front.png',
            'assets/skybox/back.png',
        ]
        self.skybox_tex = load_cubemap(faces)

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
        
        # Set up projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / self.height() if self.height() != 0 else 1
        gluPerspective(60, aspect, 0.1, 1000.0)
        
        # Set up view matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.camera.apply_view()
        
        # Draw grid
        self.draw_grid()
        
        # Draw any other scene elements here
        self.draw_world()

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

    def draw_world(self):
        # Render the skybox
        self.draw_skybox()
        # (Add other world rendering here)
        pass

    def draw_skybox(self):
        if not self.skybox_tex:
            return
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_TEXTURE_CUBE_MAP)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.skybox_tex)
        glPushMatrix()
        # Remove translation from view matrix
        m = np.identity(4, dtype=np.float32)
        glGetFloatv(GL_MODELVIEW_MATRIX, m)
        m[3][0] = 0
        m[3][1] = 0
        m[3][2] = 0
        glLoadMatrixf(m)
        size = 50.0
        glBegin(GL_QUADS)
        # Right
        glTexCoord3f(1, -1, -1); glVertex3f( size, -size, -size)
        glTexCoord3f(1, -1,  1); glVertex3f( size, -size,  size)
        glTexCoord3f(1,  1,  1); glVertex3f( size,  size,  size)
        glTexCoord3f(1,  1, -1); glVertex3f( size,  size, -size)
        # Left
        glTexCoord3f(-1, -1,  1); glVertex3f(-size, -size,  size)
        glTexCoord3f(-1, -1, -1); glVertex3f(-size, -size, -size)
        glTexCoord3f(-1,  1, -1); glVertex3f(-size,  size, -size)
        glTexCoord3f(-1,  1,  1); glVertex3f(-size,  size,  size)
        # Top
        glTexCoord3f(-1, 1, -1); glVertex3f(-size, size, -size)
        glTexCoord3f( 1, 1, -1); glVertex3f( size, size, -size)
        glTexCoord3f( 1, 1,  1); glVertex3f( size, size,  size)
        glTexCoord3f(-1, 1,  1); glVertex3f(-size, size,  size)
        # Bottom
        glTexCoord3f(-1, -1,  1); glVertex3f(-size, -size,  size)
        glTexCoord3f( 1, -1,  1); glVertex3f( size, -size,  size)
        glTexCoord3f( 1, -1, -1); glVertex3f( size, -size, -size)
        glTexCoord3f(-1, -1, -1); glVertex3f(-size, -size, -size)
        # Front
        glTexCoord3f(-1, -1, -1); glVertex3f(-size, -size, -size)
        glTexCoord3f( 1, -1, -1); glVertex3f( size, -size, -size)
        glTexCoord3f( 1,  1, -1); glVertex3f( size,  size, -size)
        glTexCoord3f(-1,  1, -1); glVertex3f(-size,  size, -size)
        # Back
        glTexCoord3f( 1, -1,  1); glVertex3f( size, -size,  size)
        glTexCoord3f(-1, -1,  1); glVertex3f(-size, -size,  size)
        glTexCoord3f(-1,  1,  1); glVertex3f(-size,  size,  size)
        glTexCoord3f( 1,  1,  1); glVertex3f( size,  size,  size)
        glEnd()
        glPopMatrix()
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
        glDisable(GL_TEXTURE_CUBE_MAP)
        glDepthFunc(GL_LESS)

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
                if file_path.endswith('.obj'):
                    # Here you would add the object to the scene
                    self.parent().add_object_to_scene_from_file(file_path, event.position())
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

        # Set up layouts for float3 fields
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Type:", self.type_label)
        self.layout.addRow("Location:", self._make_row(self.location_edits))
        self.layout.addRow("Rotation:", self._make_row(self.rotation_edits))
        self.layout.addRow("Scale:", self._make_row(self.scale_edits))

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
                    edit.setEnabled(False)
            self.name_edit.setEnabled(False)
            return

        self.name_edit.setText(obj.name)
        self.type_label.setText(obj.type)
        for edits, values in zip(
            [self.location_edits, self.rotation_edits, self.scale_edits],
            [obj.location, obj.rotation, obj.scale]
        ):
            for edit, value in zip(edits, values):
                edit.setText(str(value))
                edit.setEnabled(True)
        self.name_edit.setEnabled(True)

    def _on_name_changed(self):
        if self.current_obj:
            self.current_obj.name = self.name_edit.text()

    def _make_on_vec3_changed(self, vec_index, comp_index):
        # vec_index: 0=location, 1=rotation, 2=scale
        def handler():
            if self.current_obj:
                try:
                    value = float([self.location_edits, self.rotation_edits, self.scale_edits][vec_index][comp_index].text())
                    [self.current_obj.location, self.current_obj.rotation, self.current_obj.scale][vec_index][comp_index] = value
                except ValueError:
                    pass  # Ignore invalid input
        return handler

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
    def __init__(self, name, obj_type, location=None, rotation=None, scale=None):
        self.name = name
        self.type = obj_type
        self.location = location if location is not None else [0.0, 0.0, 0.0]
        self.rotation = rotation if rotation is not None else [0.0, 0.0, 0.0]
        self.scale = scale if scale is not None else [1.0, 1.0, 1.0]
        # Add more properties as needed (transform, mesh, etc.)

class MainEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Editor")
        self.setGeometry(100, 100, 1280, 720)

        # Central OpenGL viewport
        self.viewport = GLViewport(self)
        self.setCentralWidget(self.viewport)

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

        self.scene = Scene()
        self.hierarchy_panel.update_items(self.scene.get_object_names())
        self.hierarchy_panel.currentTextChanged.connect(self.on_outliner_selection)
        self.hierarchy_panel.itemDoubleClicked.connect(self.on_outliner_double_click)

    def update_viewport(self):
        self.viewport.update()

    def keyPressEvent(self, event):
        self.viewport.keyPressEvent(event)
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

    def add_object_to_scene_from_file(self, file_path, drop_pos):
        obj_name = file_path.split('/')[-1].split('.')[0]
        new_obj = SceneObject(obj_name, "Mesh")
        self.add_object(new_obj)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MainEditor()
    editor.show()
    sys.exit(app.exec())
