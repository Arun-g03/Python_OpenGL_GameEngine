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
                    ray_info = self.cast_ray(ray_angle)
                    if ray_info:
                        logger.log(f"Ray {x}: distance={ray_info['distance']}")
                        # Calculate wall height
                        wall_height = (TILE_SIZE_M * HEIGHT) / (ray_info['distance'] * math.cos(ray_angle - self.player.angle))
                        logger.log(f"Ray {x}: wall_height={wall_height}")
                        # Draw wall slice
                        self.draw_wall_slice(x, wall_height, ray_info)
                    else:
                        logger.log(f"Ray {x}: no hit")
                except Exception as e:
                    logger.log(f"Error processing ray {x}: {e}")
                    continue
            logger.log("Ray casting completed successfully")
        except Exception as e:
            logger.log(f"Error in cast_rays: {e}")

    def cast_ray(self, ray_angle):
        try:
            # Calculate ray direction
            ray_dir_x = math.cos(ray_angle)
            ray_dir_y = math.sin(ray_angle)
            
            # Calculate ray start position (in world coordinates)
            ray_x = self.player.x / TILE_SIZE_M
            ray_y = self.player.y / TILE_SIZE_M
            
            # Calculate step size
            step_x = 1.0 / abs(ray_dir_x) if ray_dir_x != 0 else float('inf')
            step_y = 1.0 / abs(ray_dir_y) if ray_dir_y != 0 else float('inf')
            
            # Calculate initial distance to next grid line
            if ray_dir_x < 0:
                dist_x = (ray_x - int(ray_x)) * step_x
                step_dir_x = -1
            else:
                dist_x = (int(ray_x) + 1 - ray_x) * step_x
                step_dir_x = 1
            
            if ray_dir_y < 0:
                dist_y = (ray_y - int(ray_y)) * step_y
                step_dir_y = -1
            else:
                dist_y = (int(ray_y) + 1 - ray_y) * step_y
                step_dir_y = 1
            
            # DDA variables
            map_x = int(ray_x)
            map_y = int(ray_y)
            hit = False
            side = 0  # 0 for x-side, 1 for y-side
            max_steps = 100  # Safety limit
            
            # DDA loop
            for _ in range(max_steps):
                # Check if ray hit a wall
                if map_x < 0 or map_x >= len(self.game_map[0]) or map_y < 0 or map_y >= len(self.game_map):
                    break
                
                if self.game_map[map_y][map_x] == 1:
                    hit = True
                    break
                
                # Move to next grid line
                if dist_x < dist_y:
                    dist_x += step_x
                    map_x += step_dir_x
                    side = 0
                else:
                    dist_y += step_y
                    map_y += step_dir_y
                    side = 1
            
            if hit:
                # Calculate distance to wall
                if side == 0:
                    perp_wall_dist = (map_x - ray_x + (1 - step_dir_x) / 2) / ray_dir_x
                else:
                    perp_wall_dist = (map_y - ray_y + (1 - step_dir_y) / 2) / ray_dir_y
                
                # Convert to world units
                perp_wall_dist *= TILE_SIZE_M
                
                # Calculate wall height
                line_height = int(HEIGHT / perp_wall_dist)
                
                # Calculate lowest and highest pixel to fill
                draw_start = -line_height / 2 + HEIGHT / 2
                if draw_start < 0:
                    draw_start = 0
                draw_end = line_height / 2 + HEIGHT / 2
                if draw_end >= HEIGHT:
                    draw_end = HEIGHT - 1
                
                return {
                    'distance': perp_wall_dist,
                    'side': side,
                    'line_height': line_height,
                    'draw_start': draw_start,
                    'draw_end': draw_end,
                    'map_x': map_x,
                    'map_y': map_y
                }
            
            return None
        except Exception as e:
            logger.log(f"Error in cast_ray: {e}")
            return None

    def draw_wall_slice(self, x, height, ray_info):
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

    def enable_opengl_states(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


