from OpenGL.GL import *
from utils.settings import *
import pygame

class PauseMenu:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 48)
        self.buttons = [
            {"label": "Resume Game", "rect": pygame.Rect(WIDTH // 2 - 100, 200, 200, 60)},
            {"label": "Game Mode", "rect": pygame.Rect(WIDTH // 2 - 100, 280, 200, 60)},
            {"label": "Editor Mode", "rect": pygame.Rect(WIDTH // 2 - 100, 360, 200, 60)},
            {"label": "Main Menu", "rect": pygame.Rect(WIDTH // 2 - 100, 440, 200, 60)}
        ]

    def draw(self):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Setup orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Draw translucent black overlay
        glColor4f(0, 0, 0, 0.6)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WIDTH, 0)
        glVertex2f(WIDTH, HEIGHT)
        glVertex2f(0, HEIGHT)
        glEnd()

        # Draw gray button rectangles
        for button in self.buttons:
            rect = button["rect"]
            glColor4f(0.3, 0.3, 0.3, 0.9)
            glBegin(GL_QUADS)
            glVertex2f(rect.left, rect.top)
            glVertex2f(rect.right, rect.top)
            glVertex2f(rect.right, rect.bottom)
            glVertex2f(rect.left, rect.bottom)
            glEnd()

            # Render text label
            self.draw_text_label(button["label"], button["rect"].center)

        # Cleanup and restore
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def handle_click(self, pos):
        for i, button in enumerate(self.buttons):
            if button["rect"].collidepoint(pos):
                if i == 0:  # Resume Game
                    return "resume"
                elif i == 1:  # Game Mode
                    return "game"
                elif i == 2:  # Editor Mode
                    return "editor"
                elif i == 3:  # Main Menu
                    return "menu"
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