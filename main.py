import pygame
import sys
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
from rendering.game_render import GameRenderer  # NEW

"""OPENGL IMPORTS"""
from OpenGL.GL import *
from OpenGL.GLU import *



def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("DOOM Clone (OpenGL)")
    clock = pygame.time.Clock()

    logger.log("OpenGL and Pygame initialized.")

    # OpenGL setup
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

    # States
    state = "menu"
    is_paused = False
    update_cursor(state, is_paused)

    # Game setup
    main_menu = MainMenu()
    pause_menu = PauseMenu()
    editor_renderer = EditorRenderer()
    enemy_sheet = pygame.image.load("assets\\Enemy_devil.PNG")
    floor_texture = load_texture("assets\\Stone_floor.jpg")
    glBindTexture(GL_TEXTURE_2D, floor_texture)

    enemy = Enemy(4 * TILE_SIZE_M, 4 * TILE_SIZE_M, enemy_sheet)
    player = Player()
    player.x = 8
    player.y = 8
    logger.log(f"Player start: x={player.x}, y={player.y}")
    logger.log(f"Map sample: {game_map[0][0][0:10]}")
    game_renderer = GameRenderer(player, game_map, floor_texture)  # NEW
    game_renderer.add_enemy(enemy)  # NEW

    # Ensure cursor is visible for menu state
    update_cursor(state, is_paused)

    # Mouse tracking for editor
    last_mouse_pos = pygame.mouse.get_pos()
    mouse_dx = 0
    mouse_dy = 0

    while True:
        delta_time = clock.tick(FPS) / 1000.0

        # Calculate mouse movement
        current_mouse_pos = pygame.mouse.get_pos()
        mouse_dx = current_mouse_pos[0] - last_mouse_pos[0]
        mouse_dy = current_mouse_pos[1] - last_mouse_pos[1]
        last_mouse_pos = current_mouse_pos

        for event in pygame.event.get():
            #logger.log(f"Event: {event}")
            if event.type == pygame.QUIT:
                logger.log("Quit event received. Exiting.")
                pygame.quit()
                sys.exit()

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = main_menu.handle_click(pygame.mouse.get_pos())
                    logger.log(f"Menu action: {action}")
                    if action == "start":
                        state = "game"
                        is_paused = False
                        update_cursor(state, is_paused)
                        logger.log("Switched to game state.")
                    elif action == "editor":
                        state = "editor"
                        update_cursor(state)
                        logger.log("Switched to editor state.")
                    elif action == "quit":
                        logger.log("Quit selected from menu. Exiting.")
                        pygame.quit()
                        sys.exit()

            elif state == "game":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = not is_paused
                    update_cursor(state, is_paused)
                    logger.log(f"Pause toggled. is_paused={is_paused}")
                elif is_paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = pause_menu.handle_click(pygame.mouse.get_pos())
                    logger.log(f"Pause menu action: {action}")
                    if action == "resume":
                        is_paused = False
                        update_cursor(state, is_paused)
                        logger.log("Resumed game from pause.")
                    elif action == "game":
                        state = "game"
                        is_paused = False
                        update_cursor(state, is_paused)
                        logger.log("Returned to game from pause menu.")
                    elif action == "editor":
                        state = "editor"
                        is_paused = False
                        update_cursor(state)
                        logger.log("Switched to editor from pause menu.")
                    elif action == "menu":
                        state = "menu"
                        is_paused = False
                        update_cursor(state)
                        logger.log("Returned to main menu from pause menu.")

            elif state == "editor":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "menu"
                    update_cursor(state)
                    logger.log("Exited editor to main menu.")
                elif event.type == pygame.KEYDOWN:
                    editor_renderer.handle_key(event.key)
                    logger.log(f"Editor key: {event.key}")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        if not editor_renderer.handle_click(pygame.mouse.get_pos()):
                            editor_renderer.handle_block_edit(pygame.mouse.get_pos())
                        logger.log("Editor left click.")
                    elif event.button == 3:  # Right click
                        editor_renderer.handle_block_edit(pygame.mouse.get_pos())
                        logger.log("Editor right click.")

        # === RENDER ===
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if state == "menu":
            main_menu.draw()
        elif state == "game":
            if not is_paused:
                player.update(delta_time)
                game_renderer.update(delta_time)
            game_renderer.render(delta_time)
            if is_paused:
                pause_menu.draw()
        elif state == "editor":
            keys = pygame.key.get_pressed()
            editor_renderer.render(delta_time, keys, mouse_dx, mouse_dy, pygame.mouse.get_pos())

        pygame.display.flip()


def update_cursor(state, is_paused=False):
    if state == "menu":
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    elif state == "game":
        pygame.mouse.set_visible(is_paused)
        pygame.event.set_grab(not is_paused)
    elif state == "editor":
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)




if __name__ == "__main__":
    main()
