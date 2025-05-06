MAP_WIDTH = 20
MAP_HEIGHT = 5   # vertical height (Z)
MAP_DEPTH = 20
TILE = 64

# Create 3D empty map: depth (Z), height (Y), width (X)
game_map = [[[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)] for _ in range(MAP_DEPTH)]

# Floor (Z=0) outer walls
for x in range(MAP_WIDTH):
    game_map[0][0][x] = 1
    game_map[0][MAP_HEIGHT - 1][x] = 1
for y in range(MAP_HEIGHT):
    game_map[0][y][0] = 1
    game_map[0][y][MAP_WIDTH - 1] = 1
for z in range(MAP_DEPTH):
    game_map[z][0][0] = 1
    game_map[z][MAP_HEIGHT - 1][0] = 1
    game_map[z][0][MAP_WIDTH - 1] = 1

# # Optional: place a few interior 3D blocks
# for x in range(3, 6):
#     for z in range(3, 6):
#         for y in range(1, 3):  # vertical stack
#             game_map[z][y][x] = 1
