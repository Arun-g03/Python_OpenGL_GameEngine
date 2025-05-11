import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from utils.settings import *
from utils.logger import logger
from player.player import Player
from rendering.raycaster import Raycaster
from world.map import game_map
from enemies.enemy import Enemy
from rendering.texture_loader import load_texture
from rendering.pause_menu import PauseMenu
from rendering.main_menu import MainMenu
from rendering.editor_render import EditorRenderer
from rendering.game_render import GameRenderer
from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    EDITOR = auto()
    PAUSED = auto()

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
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WIDTH / HEIGHT, 0.1, RENDER_DISTANCE)
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
    
    return window

def main():
    window = init_glfw()
    if not window:
        return

    try:
        # Initialize game objects
        player = Player()
        player.x = 8
        player.y = 8
        player.z = 0
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
        
        # Game state
        game_state = GameState.MENU
        keys = {}
        
        def transition_to_game():
            nonlocal game_state
            try:
                logger.log("Starting game transition...")
                
                # Reset player position and rotation
                logger.log("Resetting player state...")
                player.x = 8
                player.y = 8
                player.z = 0
                player.rot_x = 0
                player.rot_y = 0
                player.angle = 0
                logger.log(f"Player position reset to: x={player.x}, y={player.y}, z={player.z}")
                logger.log(f"Player rotation reset to: rot_x={player.rot_x}, rot_y={player.rot_y}, angle={player.angle}")
                
                # Reinitialize game renderer
                logger.log("Reinitializing game renderer...")
                game_renderer.cleanup()
                game_renderer.__init__(player, game_map, floor_texture)
                logger.log("Game renderer reinitialized")
                
                # Switch to game state
                logger.log("Switching to game state...")
                game_state = GameState.PLAYING
                
                # Hide cursor
                logger.log("Hiding cursor...")
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                
                # Reset mouse position
                logger.log("Resetting mouse position...")
                glfw.set_cursor_pos(window, WIDTH//2, HEIGHT//2)
                
                logger.log("Game transition completed successfully")
            except Exception as e:
                logger.log(f"Error in transition_to_game: {e}")
                logger.log("Falling back to menu state")
                game_state = GameState.MENU
        
        # Set up input callbacks
        def key_callback(window, key, scancode, action, mods):
            nonlocal game_state
            if key == glfw.KEY_ESCAPE:
                if action == glfw.PRESS:
                    if game_state == GameState.PLAYING:
                        game_state = GameState.PAUSED
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                    elif game_state == GameState.PAUSED:
                        game_state = GameState.PLAYING
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                    elif game_state == GameState.EDITOR:
                        game_state = GameState.MENU
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            keys[key] = action
            if game_state == GameState.PLAYING:
                player.key_callback(window, key, scancode, action, mods)

        def mouse_button_callback(window, button, action, mods):
            nonlocal game_state
            if action == glfw.PRESS:
                x, y = glfw.get_cursor_pos(window)
                if game_state == GameState.MENU:
                    result = main_menu.handle_click((x, y))
                    if result == "start":
                        logger.log("Start game button clicked")
                        transition_to_game()
                    elif result == "editor":
                        logger.log("Editor button clicked")
                        game_state = GameState.EDITOR
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                    elif result == "quit":
                        logger.log("Quit button clicked")
                        glfw.set_window_should_close(window, True)
                elif game_state == GameState.PAUSED:
                    result = pause_menu.handle_click((x, y))
                    if result == "resume":
                        logger.log("Resume button clicked")
                        game_state = GameState.PLAYING
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                    elif result == "menu":
                        logger.log("Menu button clicked")
                        game_state = GameState.MENU
                        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                    elif result == "quit":
                        logger.log("Quit button clicked")
                        glfw.set_window_should_close(window, True)

        glfw.set_key_callback(window, key_callback)
        glfw.set_mouse_button_callback(window, mouse_button_callback)
        
        # Mouse position tracking
        last_mouse_x, last_mouse_y = glfw.get_cursor_pos(window)
        
        # Main loop
        while not glfw.window_should_close(window):
            try:
                # Calculate delta time
                current_time = glfw.get_time()
                delta_time = current_time - (getattr(main, 'last_time', current_time))
                main.last_time = current_time
                
                # Calculate mouse movement
                current_mouse_x, current_mouse_y = glfw.get_cursor_pos(window)
                mouse_dx = current_mouse_x - last_mouse_x
                mouse_dy = current_mouse_y - last_mouse_y
                last_mouse_x, last_mouse_y = current_mouse_x, current_mouse_y
                
                # Clear the screen
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                # Update and render based on game state
                if game_state == GameState.MENU:
                    main_menu.draw()
                elif game_state == GameState.PLAYING:
                    logger.log("Updating game state...")
                    player.update(delta_time, mouse_dx, mouse_dy)
                    game_renderer.update(delta_time)
                    logger.log("Rendering game...")
                    game_renderer.render(delta_time)
                elif game_state == GameState.EDITOR:
                    editor_renderer.render(delta_time, keys, mouse_dx, mouse_dy, (current_mouse_x, current_mouse_y))
                elif game_state == GameState.PAUSED:
                    game_renderer.render(delta_time)  # Render game in background
                    pause_menu.draw()
                
                # Swap front and back buffers
                glfw.swap_buffers(window)
                
                # Poll for and process events
                glfw.poll_events()
            except Exception as e:
                logger.log(f"Error in main loop: {e}")
                break
        
        # Cleanup
        game_renderer.cleanup()
    except Exception as e:
        logger.log(f"Error in main: {e}")
    finally:
        glfw.terminate()

if __name__ == "__main__":
    main()
