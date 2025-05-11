import math
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.settings import *
from utils.logger import logger

class Raycaster:
    def __init__(self, player, game_map):
        logger.log("Initializing raycaster...")
        self.player = player
        self.game_map = game_map
        self.floor_texture_id = None
        self.sky_color = (0.5, 0.7, 1.0)  # Light blue sky color
        
        # Validate game map
        if not game_map or not isinstance(game_map, list) or len(game_map) == 0:
            logger.log("Error: Invalid game map provided to raycaster")
            raise ValueError("Invalid game map provided to raycaster")
        
        # Ensure player has required attributes
        if not hasattr(player, 'x') or not hasattr(player, 'y') or not hasattr(player, 'angle'):
            logger.log("Error: Player missing required attributes")
            raise ValueError("Player missing required attributes")
        
        logger.log("Raycaster initialized successfully")

    def set_floor_texture(self, texture_id):
        logger.log("Setting floor texture...")
        if not texture_id:
            logger.log("Warning: Setting null floor texture")
        self.floor_texture_id = texture_id
        logger.log("Floor texture set successfully")

    def update(self, delta_time):
        # Update any raycaster-specific state if needed
        pass

    def render(self):
        try:
            logger.log("Starting raycaster render...")
            # Save current matrices
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            # Draw sky
            logger.log("Drawing sky...")
            self.draw_sky()
            
            # Cast rays and draw walls
            logger.log("Casting rays...")
            self.cast_rays()
            
            # Draw floor if texture is set
            if self.floor_texture_id:
                logger.log("Drawing textured floor...")
                self.draw_textured_floor()

            # Restore matrices
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            
            # Ensure we're back in modelview mode
            glMatrixMode(GL_MODELVIEW)
            logger.log("Raycaster render completed successfully")
        except Exception as e:
            logger.log(f"Error in raycaster render: {e}")
            # Ensure matrices are restored even if there's an error
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

    def draw_sky(self):
        try:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_TEXTURE_2D)
            
            # Draw sky as a full-screen quad
            glColor3f(*self.sky_color)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(WIDTH, 0)
            glVertex2f(WIDTH, HEIGHT/2)  # Sky only in upper half
            glVertex2f(0, HEIGHT/2)
            glEnd()
            
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_TEXTURE_2D)
        except Exception as e:
            print(f"Error drawing sky: {e}")

    def cast_rays(self):
        try:
            logger.log("Starting ray casting...")
            # Cast rays for each screen column
            for x in range(WIDTH):
                try:
                    # Calculate ray angle
                    ray_angle = (self.player.angle - FOV/2) + (x * FOV/WIDTH)
                    logger.log(f"Calculating ray {x}: angle={ray_angle}")
                    
                    # Cast ray
                    distance = self.cast_ray(ray_angle)
                    logger.log(f"Ray {x}: distance={distance}")
                    
                    # Calculate wall height
                    wall_height = (TILE_SIZE_M * HEIGHT) / (distance * math.cos(ray_angle - self.player.angle))
                    logger.log(f"Ray {x}: wall_height={wall_height}")
                    
                    # Draw wall slice
                    self.draw_wall_slice(x, wall_height)
                except Exception as e:
                    logger.log(f"Error processing ray {x}: {e}")
                    continue
            logger.log("Ray casting completed successfully")
        except Exception as e:
            logger.log(f"Error in cast_rays: {e}")

    def cast_ray(self, angle):
        try:
            logger.log(f"Starting ray cast at angle {angle}")
            # Ray starting position
            ray_x = self.player.x
            ray_y = self.player.y
            logger.log(f"Ray start position: x={ray_x}, y={ray_y}")
            
            # Ray direction
            ray_dir_x = math.cos(angle)
            ray_dir_y = math.sin(angle)
            logger.log(f"Ray direction: dx={ray_dir_x}, dy={ray_dir_y}")
            
            # DDA variables
            map_x = int(ray_x / TILE_SIZE_M)
            map_y = int(ray_y / TILE_SIZE_M)
            logger.log(f"Initial map position: x={map_x}, y={map_y}")
            
            # Length of ray from current position to next x or y-side
            side_dist_x = 0
            side_dist_y = 0
            
            # Length of ray from one x or y-side to next x or y-side
            delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
            delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')
            logger.log(f"Delta distances: dx={delta_dist_x}, dy={delta_dist_y}")
            
            # Direction to step in x and y
            step_x = 1 if ray_dir_x >= 0 else -1
            step_y = 1 if ray_dir_y >= 0 else -1
            logger.log(f"Step directions: x={step_x}, y={step_y}")
            
            # Perform DDA
            hit = False
            side = 0  # 0 for x-side, 1 for y-side
            steps = 0
            
            while not hit and steps < 100:  # Add safety limit
                steps += 1
                # Jump to next map square
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    side = 0
                else:
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    side = 1
                
                logger.log(f"Step {steps}: map_x={map_x}, map_y={map_y}, side={side}")
                
                # Check if ray has hit a wall
                if 0 <= map_x < len(self.game_map[0][0]) and 0 <= map_y < len(self.game_map[0]):
                    if self.game_map[0][map_y][map_x] == 1:
                        hit = True
                        logger.log(f"Hit wall at map_x={map_x}, map_y={map_y}")
                else:
                    logger.log(f"Ray out of bounds at map_x={map_x}, map_y={map_y}")
                    break
            
            if not hit:
                logger.log("Ray did not hit any wall")
                return 1.0  # Return safe default distance
            
            # Calculate distance to wall
            if side == 0:
                distance = (map_x - ray_x/TILE_SIZE_M + (1 - step_x)/2) / ray_dir_x
            else:
                distance = (map_y - ray_y/TILE_SIZE_M + (1 - step_y)/2) / ray_dir_y
            
            final_distance = distance * TILE_SIZE_M
            logger.log(f"Final distance: {final_distance}")
            return final_distance
            
        except Exception as e:
            logger.log(f"Error in cast_ray: {e}")
            return 1.0  # Return a safe default distance

    def draw_wall_slice(self, x, height):
        try:
            # Calculate wall slice coordinates
            wall_top = (HEIGHT - height) / 2
            wall_bottom = (HEIGHT + height) / 2
            
            # Draw wall slice
            glColor3f(0.8, 0.8, 0.8)  # Wall color
            glBegin(GL_QUADS)
            glVertex2f(x, wall_top)
            glVertex2f(x + 1, wall_top)
            glVertex2f(x + 1, wall_bottom)
            glVertex2f(x, wall_bottom)
            glEnd()
        except Exception as e:
            print(f"Error drawing wall slice: {e}")

    def draw_textured_floor(self):
        try:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.floor_texture_id)
            
            # Draw floor in 2D mode
            glColor3f(1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(0, HEIGHT/2)
            glTexCoord2f(1, 0); glVertex2f(WIDTH, HEIGHT/2)
            glTexCoord2f(1, 1); glVertex2f(WIDTH, HEIGHT)
            glTexCoord2f(0, 1); glVertex2f(0, HEIGHT)
            glEnd()
            
            glDisable(GL_TEXTURE_2D)
        except Exception as e:
            print(f"Error drawing textured floor: {e}")


