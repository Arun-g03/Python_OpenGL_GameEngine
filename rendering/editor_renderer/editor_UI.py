from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget,
                                 QWidget, QVBoxLayout, QLabel, QListWidget,
                                 QTextEdit, QFileSystemModel, QTreeView)
from PySide6.QtCore import Qt, QDir, QTimer
from PySide6.QtGui import QAction
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective
import sys
import math
import numpy as np
from .editor_render import EditorCamera
from rendering.texture_loader import load_cubemap

class GLViewport(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = EditorCamera()
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        self.last_mouse_pos = None
        self.mouse_wheel = 0
        self.skybox_tex = None

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
        glBegin(GL_LINES)
        glColor3f(0.3, 0.3, 0.3)
        size = 20
        step = 1
        for i in range(-size, size + 1, step):
            glVertex3f(i, 0, -size)
            glVertex3f(i, 0, size)
            glVertex3f(-size, 0, i)
            glVertex3f(size, 0, i)
        glEnd()

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
        keys = {}
        if event.key() == Qt.Key_W:
            keys['W'] = True
        elif event.key() == Qt.Key_S:
            keys['S'] = True
        elif event.key() == Qt.Key_A:
            keys['A'] = True
        elif event.key() == Qt.Key_D:
            keys['D'] = True
        elif event.key() == Qt.Key_Space:
            keys['SPACE'] = True
        elif event.key() == Qt.Key_Shift:
            keys['LEFT_SHIFT'] = True
        
        self.camera.update(0.016, keys, 0, 0, (0, 0), 0)
        self.update()

class HierarchyPanel(QListWidget):
    def __init__(self):
        super().__init__()
        self.addItems(["Cube", "Sphere", "Camera"])

class PropertiesPanel(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlainText("Select an object to view properties")

class ContentBrowser(QTreeView):
    def __init__(self):
        super().__init__()
        model = QFileSystemModel()
        model.setRootPath(QDir.currentPath())
        self.setModel(model)
        self.setRootIndex(model.index(QDir.currentPath()))

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

    def update_viewport(self):
        self.viewport.update()

    def keyPressEvent(self, event):
        self.viewport.keyPressEvent(event)
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MainEditor()
    editor.show()
    sys.exit(app.exec())
