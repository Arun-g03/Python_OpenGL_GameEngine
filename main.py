import pygame
import sys
from utils.settings import *
from player.player import Player
from rendering.raycaster import Raycaster
from world.map import game_map
from enemies.enemy import Enemy
from rendering.texture_loader import load_texture
from rendering.pause_menu import PauseMenu
from rendering.main_menu import MainMenu  # NEW


"""OPENGL IMPORTS"""
from OpenGL.GL import *
from OpenGL.GLU import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("DOOM Clone (OpenGL)")
    clock = pygame.time.Clock()

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

    # States
    state = "menu"
    is_paused = False
    update_cursor(state, is_paused)



    # Game setup
    main_menu = MainMenu()

    pause_menu = PauseMenu()
    enemy_sheet = pygame.image.load("assets\\Enemy_devil.PNG")
    floor_texture = load_texture("assets\\Stone_floor.jpg")
    glBindTexture(GL_TEXTURE_2D, floor_texture)

    enemy = Enemy(4 * TILE_SIZE_M, 4 * TILE_SIZE_M, enemy_sheet)
    player = Player()
    raycaster = Raycaster(player, game_map)

    while True:
        delta_time = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = main_menu.handle_click(pygame.mouse.get_pos())
                    if action == "start":
                        state = "game"
                        is_paused = False
                        update_cursor(state, is_paused)
                    elif action == "editor":
                        state = "editor"
                        update_cursor(state)
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()

            elif state == "game":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_paused = not is_paused
                    update_cursor(state, is_paused)
                elif is_paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = pause_menu.handle_click(pygame.mouse.get_pos())
                    if action == "resume":
                        is_paused = False
                        update_cursor(state)
                    elif action == "editor":
                        state = "editor"
                        is_paused = False
                        update_cursor(state)

        # === RENDER ===
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if state == "menu":
            main_menu.draw()
        elif state == "game":
            if not is_paused:
                player.update(delta_time)
                enemy.update()
            raycaster.render()
            if is_paused:
                pause_menu.draw()
        elif state == "editor":
            # editor_renderer.render()
            pass

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
