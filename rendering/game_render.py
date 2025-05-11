from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *
from rendering.rasteriser import Rasteriser
from enemies.enemy import Enemy
from utils.logger import logger
import traceback

class GameRenderer:
    def __init__(self, player, game_map, floor_texture):
        logger.log("Initializing game renderer...")
        if not player:
            logger.log("Error: Player object is required")
            raise ValueError("Player object is required")
        if not game_map:
            logger.log("Error: Game map is required")
            raise ValueError("Game map is required")
            
        self.player = player
        self.game_map = game_map
        self.floor_texture = floor_texture
        self.enemies = []
        
        # Initialize rasteriser
        try:
            logger.log("Creating rasteriser...")
            self.rasteriser = Rasteriser()
            if floor_texture:
                logger.log("Setting floor texture in rasteriser...")
                self.rasteriser.set_floor_texture(floor_texture)
            else:
                logger.log("Warning: No floor texture provided")
            logger.log("Rasteriser created successfully")
        except Exception as e:
            logger.log(f"Error initializing rasteriser: {e}")
            traceback.print_exc()
            self.rasteriser = None
        
        logger.log("Game renderer initialized successfully")

    def add_enemy(self, enemy):
        if enemy:
            logger.log("Adding enemy to renderer...")
            self.enemies.append(enemy)
            logger.log("Enemy added successfully")

    def render(self, delta_time):
        try:
            logger.log("Starting game render...")
            # Clear the screen and depth buffer
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Set up the camera
            logger.log("Setting up camera...")
            glRotatef(self.player.rot_x, 1, 0, 0)
            glRotatef(self.player.rot_y, 0, 1, 0)
            glTranslatef(-self.player.x, -self.player.y, -self.player.z)

            # Render the world using the Rasteriser
            if self.rasteriser:
                logger.log("Rendering world with Rasteriser...")
                self.rasteriser.render()
            else:
                logger.log("Warning: Rasteriser not initialized")

            # Render enemies
            logger.log("Rendering enemies...")
            self.render_enemies()
            
            logger.log("Game render completed successfully")
        except Exception as e:
            logger.log(f"Error in game render: {e}")
            traceback.print_exc()

    def render_enemies(self):
        try:
            for enemy in self.enemies:
                if enemy:
                    enemy.render()
        except Exception as e:
            logger.log(f"Error rendering enemies: {e}")

    def update(self, delta_time):
        try:
            logger.log("Updating game state...")
            # Update Rasteriser if needed
            if self.rasteriser:
                self.rasteriser.update(delta_time)
            
            # Update enemies
            for enemy in self.enemies:
                if enemy:
                    enemy.update()
            logger.log("Game state updated successfully")
        except Exception as e:
            logger.log(f"Error in game update: {e}")
            traceback.print_exc()

    def cleanup(self):
        try:
            logger.log("Cleaning up game renderer...")
            # Clean up any resources
            self.enemies.clear()
            if self.rasteriser:
                self.rasteriser = None
            logger.log("Game renderer cleanup completed")
        except Exception as e:
            logger.log(f"Error in cleanup: {e}") 
            traceback.print_exc()