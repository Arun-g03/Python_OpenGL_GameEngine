import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *
from rendering.raycaster import Raycaster
from enemies.enemy import Enemy

class GameRenderer:
    def __init__(self, player, game_map, floor_texture):
        self.raycaster = Raycaster(player, game_map)
        self.raycaster.set_floor_texture(floor_texture)
        self.enemies = []
        self.floor_texture = floor_texture

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def render(self, delta_time):
        # Clear the screen and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Render the world using the raycaster
        self.raycaster.render()

        # Render enemies
        self.render_enemies()

    def render_enemies(self):
        for enemy in self.enemies:
            enemy.render()

    def update(self, delta_time):
        # Update raycaster if needed
        self.raycaster.update(delta_time)
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update() 