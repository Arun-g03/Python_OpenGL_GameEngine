import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import traceback
from utils.settings import *
from utils.logger import logger
from player.player import Player
from rendering.rasteriser import Rasteriser
from world.map import game_map

from enemies.enemy import Enemy
from rendering.texture_loader import load_texture
from rendering.pause_menu import PauseMenu
from rendering.main_menu import MainMenu
from rendering.editor_renderer.editor_render import EditorRenderer
from rendering.game_render import GameRenderer
from utils.input import GameState, set_game_state, get_game_state, get_mouse_position, get_mouse_delta
import math
from utils import input
from PySide6.QtWidgets import QApplication
from rendering.editor_renderer.editor_UI import MainEditor
import sys

def init_glfw():
    if not glfw.init():
        logger.log("Failed to initialize GLFW")
        return False
    
    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(WIDTH, HEIGHT, "DOOM Clone (OpenGL + GLFW)", None, None)
    if not window:
        logger.log("Failed to create GLFW window")
        glfw.terminate()
        return False
    
    # Make the window's context current
    glfw.make_context_current(window)
    
    # Set up OpenGL
    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, width / height, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0, 0, 0, 1)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Set initial cursor mode
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
    
    # Register input callbacks
    glfw.set_key_callback(window, input.key_callback)
    glfw.set_mouse_button_callback(window, input.mouse_button_callback)
    glfw.set_cursor_pos_callback(window, input.cursor_position_callback)
    
    # Register framebuffer size callback
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    
    return window

def framebuffer_size_callback(window, width, height):
    glViewport(0, 0, width, height)
    EditorRenderer.window_width = width
    EditorRenderer.window_height = height
    EditorRenderer.resize_ui()

def main():
    window = init_glfw()
    if not window:
        return

    try:
        # Initialize game objects
        player = Player()
        player.x = 8
        player.y = 8
        player.z = 5  # Start higher up
        player.rot_x = 0
        player.rot_y = 0
        player.angle = 0  # Initialize player angle
        
        # Load textures
        floor_texture = load_texture("assets/Stone_floor.jpg")
        if not floor_texture:
            logger.log("Failed to load floor texture")
            return
        
        # Initialize menus and renderers
        main_menu = MainMenu()
        pause_menu = PauseMenu()
        game_renderer = GameRenderer(player, game_map, floor_texture)
        editor_renderer = EditorRenderer()
        
        def transition_to_game():
            try:
                # Reset player position and rotation
                player.x = 8
                player.y = 8
                player.z = 5  # Start higher up
                player.rot_x = 0
                player.rot_y = 0
                player.angle = 0  # Reset player angle
                
                # Reinitialize game renderer
                game_renderer.cleanup()
                game_renderer.__init__(player, game_map, floor_texture)
                
                # Switch to game state
                set_game_state(GameState.PLAYING)
                # Hide cursor
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                
                # Reset mouse position
                glfw.set_cursor_pos(window, WIDTH//2, HEIGHT//2)
            except Exception as e:
                logger.log(f"Error in transition_to_game: {e}")
                traceback.print_exc()
                set_game_state(GameState.MENU)  # Fall back to menu if transition fails
        
        # Main loop
        while not glfw.window_should_close(window):
            try:
                # Calculate delta time
                current_time = glfw.get_time()
                delta_time = current_time - (getattr(main, 'last_time', current_time))
                main.last_time = current_time
                
                # Clear the screen
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                # Update and render based on game state
                glfw.poll_events()
                current_state = get_game_state()
                if current_state == GameState.MENU:
                    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                    result = main_menu.update()
                    if result == "start":
                        logger.log("Start game button clicked")
                        set_game_state(GameState.PLAYING)
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                        glfw.set_cursor_pos(window, WIDTH//2, HEIGHT//2)
                    elif result == "editor":
                        logger.log("Editor button clicked")
                        set_game_state(GameState.EDITOR)
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                        glfw.set_cursor_pos(window, WIDTH//2, HEIGHT//2)
                    elif result == "options":
                        logger.log("Options button clicked")
                        # TODO: Implement options menu
                    elif result == "quit":
                        logger.log("Quit button clicked")
                        glfw.set_window_should_close(window, True)
                    main_menu.draw()
                elif current_state == GameState.PLAYING:
                    player.update(delta_time, input.keys, input.mouse_buttons)
                    game_renderer.update(delta_time)
                    game_renderer.render(delta_time)
                elif current_state == GameState.EDITOR:
                    editor_renderer.render(delta_time, input.keys, *get_mouse_delta(), get_mouse_position())
                elif current_state == GameState.PAUSED:
                    game_renderer.render(delta_time)  # Render game in background
                    pause_menu.draw()
                
                # Swap front and back buffers
                glfw.swap_buffers(window)
                
               
                # Reset mouse delta at the end of the frame
                input.reset_mouse_delta()
            except Exception as e:
                logger.log(f"Error in main loop: {e}")
                traceback.print_exc()
                break
        
        # Cleanup
        game_renderer.cleanup()
    except Exception as e:
        logger.log(f"Error in main: {e}")
        traceback.print_exc()
    finally:
        glfw.terminate()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = MainEditor()
    editor.show()
    sys.exit(app.exec())
