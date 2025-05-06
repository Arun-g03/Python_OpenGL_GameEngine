import math

# Screen settings
WIDTH = 800
HEIGHT = 600
FPS = 60

# Map settings
TILE = 64  # each map square is 64x64 pixels

# Raycasting settings
FOV = 60 * (3.14 / 180)  # convert degrees to radians
NUM_RAYS = WIDTH // 2
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(FOV / 2))
PROJ_COEFF = 3 * DIST * TILE
SCALE = WIDTH // NUM_RAYS

# Player settings
PLAYER_SPEED = 2
ROT_SPEED = 0.03

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


MOUSE_SENSITIVITY = 0.002
VERTICAL_LOOK_SCALE = 1000  # Higher = faster pitch
