import OpenGL.GL as gl

class EditorViewport:
    def __init__(self, x, y, width, height, camera):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.camera = camera

    def draw(self, draw_world_callback=None):
        # Set OpenGL viewport and draw 3D scene
        gl.glViewport(self.x, self.y, self.width, self.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = self.width / self.height if self.height != 0 else 1
        from OpenGL.GLU import gluPerspective
        gluPerspective(60, aspect, 0.1, 1000.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        if self.camera:
            self.camera.apply_view()
        if draw_world_callback:
            draw_world_callback() 