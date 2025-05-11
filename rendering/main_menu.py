from OpenGL.GL import *
from utils.settings import WIDTH, HEIGHT
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from utils import input
import glfw

class MainMenu:
    def __init__(self):
        # Initialize font
        self.font_size = 48
        self.font_path = os.path.join("assets", "fonts", "arial.ttf")  # Make sure to have this font file
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        
        # Define button positions and sizes
        button_width = 200
        button_height = 60
        button_x = (WIDTH - button_width) // 2
        button_y_start = HEIGHT // 3
        button_gap = 80
        
        self.buttons = [
            {"label": "Start Game", "rect": (button_x, button_y_start, button_width, button_height)},
            {"label": "Enter Editor", "rect": (button_x, button_y_start + button_gap, button_width, button_height)},
            {"label": "Options", "rect": (button_x, button_y_start + 2 * button_gap, button_width, button_height)},
            {"label": "Quit", "rect": (button_x, button_y_start + 3 * button_gap, button_width, button_height)}
        ]
        
        # Pre-render text textures
        self.text_textures = {}
        for button in self.buttons:
            self.text_textures[button["label"]] = self.create_text_texture(button["label"])

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

        # Background
        glColor4f(0.05, 0.05, 0.05, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WIDTH, 0)
        glVertex2f(WIDTH, HEIGHT)
        glVertex2f(0, HEIGHT)
        glEnd()

        # Draw buttons
        for button in self.buttons:
            x, y, width, height = button["rect"]
            
            # Draw button background
            glColor4f(0.25, 0.25, 0.25, 1.0)
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + width, y)
            glVertex2f(x + width, y + height)
            glVertex2f(x, y + height)
            glEnd()

            # Draw text
            self.draw_text(button["label"], (x + width//2, y + height//2))

        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def draw_text(self, text, center):
        texture = self.text_textures[text]
        width, height = texture["width"], texture["height"]
        x, y = center[0] - width//2, center[1] - height//2

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

    def update(self):
        # Check for mouse clicks using the centralized input system
        if input.was_mouse_pressed(glfw.MOUSE_BUTTON_LEFT):
            x, y = input.last_mouse_pos
            print(f"Menu click detected at: x={x}, y={y}")
            for i, button in enumerate(self.buttons):
                bx, by, bw, bh = button["rect"]
                if (bx <= x <= bx + bw and by <= y <= by + bh):
                    print(f"Button {i} clicked: {self.buttons[i]['label']}")
                    if i == 0:  # Start Game
                        return "start"
                    elif i == 1:  # Enter Editor
                        return "editor"
                    elif i == 2:  # Options
                        return "options"
                    elif i == 3:  # Quit
                        return "quit"

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

    def handle_click(self, pos):
        x, y = pos
        for i, button in enumerate(self.buttons):
            bx, by, bw, bh = button["rect"]
            if (bx <= x <= bx + bw and by <= y <= by + bh):
                if i == 0:  # Start Game
                    return "start"
                elif i == 1:  # Enter Editor
                    return "editor"
                elif i == 2:  # Options
                    return "options"
                elif i == 3:  # Quit
                    return "quit"
        return None
