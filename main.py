import pygame
import sys
from settings import *
from player import Player
from raycaster import Raycaster
from map import game_map
from enemy import Enemy
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
    gluPerspective(60, WIDTH / HEIGHT, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)
    glClearColor(0, 0, 0, 1)

    # Game setup
    enemy_sheet = pygame.image.load("ITEMS4-4071190784.PNG")
    enemy = Enemy(4 * TILE, 4 * TILE, enemy_sheet)
    player = Player()
    raycaster = Raycaster(player, game_map)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        player.update()
        enemy.update()  # Note: enemy.draw must be converted to OpenGL if used

        glClear(GL_COLOR_BUFFER_BIT)
        raycaster.render()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
