import pygame
from OpenGL.GL import *

class MainMenu:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 48)
        self.buttons = [
            {"label": "Start Game", "rect": pygame.Rect(300, 200, 200, 60)},
            {"label": "Enter Editor", "rect": pygame.Rect(300, 280, 200, 60)},
            {"label": "Options", "rect": pygame.Rect(300, 360, 200, 60)},
            {"label": "Quit", "rect": pygame.Rect(300, 360, 200, 60)}
        ]

    def draw(self):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 800, 600, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Background
        glColor4f(0.05, 0.05, 0.05, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(800, 0)
        glVertex2f(800, 600)
        glVertex2f(0, 600)
        glEnd()

        # Buttons and labels
        screen = pygame.display.get_surface()
        for button in self.buttons:
            rect = button["rect"]

            # Draw button rectangle
            glColor4f(0.25, 0.25, 0.25, 1.0)
            glBegin(GL_QUADS)
            glVertex2f(rect.left, rect.top)
            glVertex2f(rect.right, rect.top)
            glVertex2f(rect.right, rect.bottom)
            glVertex2f(rect.left, rect.bottom)
            glEnd()

            # Render text label with Pygame
            self.draw_text_label(button["label"], button["rect"].center)


        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)


    def handle_click(self, pos):
        if self.buttons[0]["rect"].collidepoint(pos):
            return "start"
        elif self.buttons[1]["rect"].collidepoint(pos):
            return "editor"
        elif self.buttons[2]["rect"].collidepoint(pos):
            return "quit"
        return None


    def draw_text_label(self, text, center):
        # Render Pygame text surface
        text_surface = self.font.render(text, True, (255, 255, 255), (0, 0, 0, 0))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        width, height = text_surface.get_size()

        # Generate OpenGL texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Draw textured quad
        x, y = center[0] - width // 2, center[1] - height // 2
        glEnable(GL_TEXTURE_2D)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + width, y)
        glTexCoord2f(1, 0); glVertex2f(x + width, y + height)
        glTexCoord2f(0, 0); glVertex2f(x, y + height)

        glEnd()
        glDeleteTextures([tex_id])
