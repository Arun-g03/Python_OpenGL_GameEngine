from OpenGL.GL import *
from utils.settings import *
import pygame

class PauseMenu:
    def __init__(self):
        self.buttons = [
            {"label": "Resume Game", "rect": pygame.Rect(WIDTH // 2 - 100, 200, 200, 60)},
            {"label": "Enter Editor", "rect": pygame.Rect(WIDTH // 2 - 100, 300, 200, 60)},
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

        # Cleanup and restore
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)