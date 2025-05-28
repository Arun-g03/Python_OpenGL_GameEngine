import OpenGL.GL as gl

class EditorMenuBar:
    def __init__(self, width, height=25):
        self.width = width
        self.height = height
        self.menus = []  # List of (name, items)
    def draw(self):
        gl.glColor4f(0.2, 0.2, 0.2, 0.9)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(0, 0)
        gl.glVertex2f(self.width, 0)
        gl.glVertex2f(self.width, self.height)
        gl.glVertex2f(0, self.height)
        gl.glEnd()
        # Draw menu names (text rendering to be handled by renderer)

class EditorToolbar:
    def __init__(self, width, y, height=40):
        self.width = width
        self.y = y
        self.height = height
        self.tools = []  # List of tool icons/buttons
    def draw(self):
        gl.glColor4f(0.25, 0.25, 0.25, 0.9)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(0, self.y)
        gl.glVertex2f(self.width, self.y)
        gl.glVertex2f(self.width, self.y + self.height)
        gl.glVertex2f(0, self.y + self.height)
        gl.glEnd()
        # Draw tool icons/buttons 