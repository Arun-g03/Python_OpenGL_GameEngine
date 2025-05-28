import OpenGL.GL as gl
import os
from .ui_utils import draw_text

class EditorPanel:
    def __init__(self, x, y, width, height, title="Panel"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.visible = True

    def draw(self):
        if not self.visible:
            return
        gl.glColor4f(0.2, 0.2, 0.2, 0.9)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(self.x, self.y)
        gl.glVertex2f(self.x + self.width, self.y)
        gl.glVertex2f(self.x + self.width, self.y + self.height)
        gl.glVertex2f(self.x, self.y + self.height)
        gl.glEnd()
        # Draw title (text rendering to be handled by renderer)

class SceneHierarchyPanel(EditorPanel):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, title="World Outliner")
        self.entities = []  # To be set externally
    def draw(self):
        super().draw()
        padding = 0
        item_height = 20
        x = self.x + padding
        y = self.y + 40
        for idx, entity in enumerate(self.entities):
            gl.glColor4f(0.4, 0.4, 0.4, 0.8)
            gl.glBegin(gl.GL_QUADS)
            gl.glVertex2f(x, y)
            gl.glVertex2f(x + self.width - 2 * padding, y)
            gl.glVertex2f(x + self.width - 2 * padding, y + item_height)
            gl.glVertex2f(x, y + item_height)
            gl.glEnd()
            draw_text(entity.type, x + 5, y + 5)
            y += item_height + padding

class PropertiesPanel(EditorPanel):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, title="Details")
        self.selected_entity = None  # To be set externally
    def draw(self):
        super().draw()
        if not self.selected_entity:
            return
        x = self.x + 10
        y = self.y + 40
        props = [
            f"Type: {self.selected_entity.type}",
            f"Position: {tuple(round(p, 2) for p in self.selected_entity.position)}",
            f"Rotation: {tuple(round(r, 2) for r in self.selected_entity.rotation)}",
            f"Scale: {tuple(round(s, 2) for s in self.selected_entity.scale)}",
        ]
        for prop in props:
            draw_text(prop, x, y)
            y += 20

class ContentBrowserPanel(EditorPanel):
    def __init__(self, x, y, width, height, assets_path="assets"):
        super().__init__(x, y, width, height, title="Content Browser")
        self.assets_path = assets_path
        self.items = self.scan_assets()

    def scan_assets(self):
        items = []
        if os.path.exists(self.assets_path):
            for entry in os.scandir(self.assets_path):
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "path": entry.path
                })
        return items

    def draw(self):
        super().draw()
        # Draw content browser content (folders/files as grid)
        padding = 10
        item_width = 100
        item_height = 40
        x = self.x + padding
        y = self.y + 40
        for item in self.items:
            # Draw folder/file background
            gl.glColor4f(0.3, 0.3, 0.3, 0.8)
            gl.glBegin(gl.GL_QUADS)
            gl.glVertex2f(x, y)
            gl.glVertex2f(x + item_width, y)
            gl.glVertex2f(x + item_width, y + item_height)
            gl.glVertex2f(x, y + item_height)
            gl.glEnd()
            # Draw folder/file name
            draw_text(item["name"], x + 5, y + 10)
            x += item_width + padding
            if x + item_width > self.x + self.width:
                x = self.x + padding
                y += item_height + padding 