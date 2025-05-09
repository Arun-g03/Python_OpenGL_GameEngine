"""
File that contains all the settings for the game.
"""

import math

# Screen settings
WIDTH = 1280
HEIGHT = 720
MAP_DEPTH = 32  # or whatever value you want
FPS = 60
RENDER_DISTANCE = 5000  
# Map settings
TILE_SIZE_M = 1.0  

# Raycasting settings
FOV = 60 * (3.14 / 180)  # convert degrees to radians
NUM_RAYS = WIDTH // 2
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(FOV / 2))
PROJ_COEFF = 3 * DIST * TILE_SIZE_M
SCALE = WIDTH // NUM_RAYS

# Player settings
PLAYER_SPEED = 3
ROT_SPEED = 3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


MOUSE_SENSITIVITY = 0.002
VERTICAL_LOOK_SCALE = 1000  # Higher = faster pitch

LOG_DEBUG = True
