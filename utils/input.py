import glfw
from enum import Enum, auto
import math
suppress_input = False 
# --- Game States ---
class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    EDITOR = auto()
    PAUSED = auto()

# --- Input State ---
keys = {}
mouse_buttons = {}
mouse_dx, mouse_dy = 0, 0
last_mouse_pos = (0, 0)
mouse_button_pressed = {}
current_game_state = GameState.MENU
is_right_mouse_down = False
place_block_pressed = False
delete_block_pressed = False
 # suppress deltas for 1 frame

# --- Action Bindings ---
bindings = {
    GameState.EDITOR: {
        "move_forward": glfw.KEY_W,
        "move_back": glfw.KEY_S,
        "move_left": glfw.KEY_A,
        "move_right": glfw.KEY_D,
        "move_up": glfw.KEY_E,
        "move_down": glfw.KEY_Q,
        "fast_mode": glfw.KEY_LEFT_CONTROL,
        "camera_look": glfw.MOUSE_BUTTON_RIGHT,
    },
    GameState.PLAYING: {
        "jump": glfw.KEY_SPACE,
        "shoot": glfw.MOUSE_BUTTON_LEFT,
    },
    GameState.MENU: {},
    GameState.PAUSED: {},
}

# --- Game State Setter ---
def set_game_state(state):
    global current_game_state
    current_game_state = state

def get_game_state():
    return current_game_state

# --- GLFW Callbacks ---
def key_callback(window, key, scancode, action, mods):
    keys[key] = action

def mouse_button_callback(window, button, action, mods):
    global is_right_mouse_down, last_mouse_pos, place_block_pressed, delete_block_pressed, suppress_input, mouse_dx, mouse_dy
    mouse_buttons[button] = action
    
    # Handle button press
    if action == glfw.PRESS:
        mouse_button_pressed[button] = True
        
        if button == glfw.MOUSE_BUTTON_RIGHT:
            is_right_mouse_down = True
            if current_game_state == GameState.EDITOR:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                width, height = glfw.get_window_size(window)
                glfw.set_cursor_pos(window, width // 2, height // 2)
                
                suppress_input = True
                mouse_dx = 0
                mouse_dy = 0



        
        # Left mouse button handling
        elif button == glfw.MOUSE_BUTTON_LEFT:
            if current_game_state == GameState.PLAYING:
                # Handle shooting in playing state
                pass
            elif current_game_state == GameState.EDITOR:
                place_block_pressed = True
                
        # Middle mouse button handling
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            if current_game_state == GameState.EDITOR:
                # Handle panning/orbit in editor state
                pass
            elif current_game_state == GameState.PLAYING:
                # Handle alternate actions in playing state
                pass
    
    # Handle button release
    elif action == glfw.RELEASE:
        mouse_button_pressed[button] = False
        
        # Right mouse button handling
        if button == glfw.MOUSE_BUTTON_RIGHT:
            is_right_mouse_down = False
            if current_game_state == GameState.EDITOR:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        
        # Left mouse button handling
        elif button == glfw.MOUSE_BUTTON_LEFT:
            if current_game_state == GameState.PLAYING:
                # Handle end of shooting in playing state
                pass
            elif current_game_state == GameState.EDITOR:
                # Handle end of selection/placement in editor state
                pass
                
        # Middle mouse button handling
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            if current_game_state == GameState.EDITOR:
                # Handle end of panning/orbit in editor state
                pass
            elif current_game_state == GameState.PLAYING:
                # Handle end of alternate actions in playing state
                pass

def cursor_position_callback(window, xpos, ypos):
    global mouse_dx, mouse_dy, last_mouse_pos, skip_mouse_delta, suppress_input

    width, height = glfw.get_window_size(window)
    center_x, center_y = width // 2, height // 2

    if suppress_input:
        mouse_dx = 0
        mouse_dy = 0
        suppress_input = False
        glfw.set_cursor_pos(window, center_x, center_y)
        return


    if is_right_mouse_down and current_game_state == GameState.EDITOR:
        mouse_dx = xpos - center_x
        mouse_dy = ypos - center_y
        glfw.set_cursor_pos(window, center_x, center_y)
    else:
        mouse_dx = 0
        mouse_dy = 0

    last_mouse_pos = (xpos, ypos)




# --- Input Query API ---
def reset_mouse_delta():
    global mouse_dx, mouse_dy
    mouse_dx = 0
    mouse_dy = 0

def get_mouse_delta():
    return mouse_dx, mouse_dy

def get_mouse_position():
    return last_mouse_pos

def is_key_down(key):
    return keys.get(key, glfw.RELEASE) == glfw.PRESS

def is_mouse_down(button):
    return mouse_buttons.get(button, glfw.RELEASE) == glfw.PRESS

def was_mouse_pressed(button):
    """Detect one-frame mouse press."""
    was_pressed = mouse_button_pressed.get(button, False)
    if was_pressed:
        mouse_button_pressed[button] = False
    return was_pressed

def is_right_mouse_held():
    return is_right_mouse_down

# --- Action Mapping ---
def is_action_active(action_name):
    state_bindings = bindings.get(current_game_state, {})
    key = state_bindings.get(action_name)
    if key is None:
        return False
    if isinstance(key, int):
        return is_key_down(key) or is_mouse_down(key)
    return False

def was_place_block_pressed():
    global place_block_pressed
    if place_block_pressed:
        place_block_pressed = False
        return True
    return False

def was_delete_block_pressed():
    global delete_block_pressed
    if delete_block_pressed:
        delete_block_pressed = False
        return True
    return False

def was_mouse_clicked():
    """Detect one-frame left mouse click (for UI selection)."""
    return was_mouse_pressed(glfw.MOUSE_BUTTON_LEFT)
