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

        # Button labels
        labels = ["Start Game", "Enter Editor", "Options", "Quit"]
        self.buttons = []
        self.text_textures = {}
        padding_x = 40
        padding_y = 24
        max_width = 0
        total_height = 0
        button_heights = []
        # Calculate button sizes and create textures
        for label in labels:
            bbox = self.font.getbbox(label)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            width = text_width + padding_x * 2
            height = text_height + padding_y * 2
            self.text_textures[label] = self.create_text_texture(label)
            self.buttons.append({"label": label, "rect": [0, 0, width, height]})
            max_width = max(max_width, width)
            button_heights.append(height)
            total_height += height
        button_gap = 32
        total_height += button_gap * (len(self.buttons) - 1)
        # Center buttons
        start_y = (HEIGHT - total_height) // 2
        for i, button in enumerate(self.buttons):
            width = button["rect"][2]
            height = button["rect"][3]
            x = (WIDTH - max_width) // 2
            y = start_y + i * (height + button_gap)
            button["rect"] = [x, y, max_width, height]

    def create_text_texture(self, text):
        # Create a new image with transparent background
        bbox = self.font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        image = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Draw text with offset to handle negative bbox
        draw.text((-bbox[0], -bbox[1]), text, font=self.font, fill=(255, 255, 255, 255))
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
            # Draw text centered in button
            self.draw_text(button["label"], (x + width//2, y + height//2))

        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def update(self):
        # Check for mouse clicks using the centralized input system
        if input.was_mouse_pressed(glfw.MOUSE_BUTTON_LEFT):
            mouse_pos = input.get_mouse_position()
            if mouse_pos:
                x, y = mouse_pos
                print(f"Menu click detected at: x={x}, y={y}")
                
                # Check each button
                for i, button in enumerate(self.buttons):
                    bx, by, bw, bh = button["rect"]
                    if (bx <= x <= bx + bw and by <= y <= by + bh):
                        print(f"Button {i} clicked: {button['label']}")
                        
                        # Map button actions to game states
                        if i == 0:  # Start Game
                            return "start"
                        elif i == 1:  # Enter Editor
                            return "editor"
                        elif i == 2:  # Options
                            return "options"
                        elif i == 3:  # Quit
                            return "quit"
        return None
