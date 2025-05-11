import glfw
from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    EDITOR = auto()
    PAUSED = auto()

# Input state
keys = {}
mouse_buttons = {}
mouse_dx = 0
mouse_dy = 0
last_mouse_pos = (0, 0)
mouse_button_pressed = {}  # Track button press events
current_game_state = GameState.MENU
is_right_mouse_down = False

def set_game_state(state):
    global current_game_state
    current_game_state = state

def get_game_state():
    return current_game_state

# Key callback
def key_callback(window, key, scancode, action, mods):
    keys[key] = action
    if key == glfw.KEY_ESCAPE:
        if action == glfw.PRESS:
            if current_game_state == GameState.PLAYING:
                set_game_state(GameState.PAUSED)
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            elif current_game_state == GameState.PAUSED:
                set_game_state(GameState.PLAYING)
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
            elif current_game_state == GameState.EDITOR:
                set_game_state(GameState.MENU)
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)

# Mouse button callback
def mouse_button_callback(window, button, action, mods):
    global is_right_mouse_down, last_mouse_pos
    mouse_buttons[button] = action
    if action == glfw.PRESS:
        mouse_button_pressed[button] = True
        if button == glfw.MOUSE_BUTTON_RIGHT:
            is_right_mouse_down = True
            if current_game_state == GameState.EDITOR:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                # Reset mouse position to center when starting rotation
                center_x, center_y = glfw.get_window_size(window)
                center_x //= 2
                center_y //= 2
                glfw.set_cursor_pos(window, center_x, center_y)
                last_mouse_pos = (center_x, center_y)
    elif action == glfw.RELEASE:
        mouse_button_pressed[button] = False
        if button == glfw.MOUSE_BUTTON_RIGHT:
            is_right_mouse_down = False
            if current_game_state == GameState.EDITOR:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)

# Cursor position callback
def cursor_position_callback(window, xpos, ypos):
    global mouse_dx, mouse_dy, last_mouse_pos
    if is_right_mouse_down and current_game_state == GameState.EDITOR:
        # Calculate delta from center of screen
        center_x, center_y = glfw.get_window_size(window)
        center_x //= 2
        center_y //= 2
        mouse_dx = xpos - center_x
        mouse_dy = ypos - center_y
        # Reset cursor to center
        glfw.set_cursor_pos(window, center_x, center_y)
    else:
        mouse_dx = xpos - last_mouse_pos[0]
        mouse_dy = ypos - last_mouse_pos[1]
    last_mouse_pos = (xpos, ypos)

# Reset mouse deltas (call after consuming them)
def reset_mouse_delta():
    global mouse_dx, mouse_dy
    mouse_dx = 0
    mouse_dy = 0

# Utility functions
def is_key_down(key):
    return keys.get(key) == glfw.PRESS

def is_mouse_down(button):
    return mouse_buttons.get(button) == glfw.PRESS

def was_mouse_pressed(button):
    """Check if a mouse button was just pressed this frame"""
    was_pressed = mouse_button_pressed.get(button, False)
    if was_pressed:
        mouse_button_pressed[button] = False  # Reset the press state
    return was_pressed

def get_mouse_position():
    return last_mouse_pos

def get_mouse_delta():
    return mouse_dx, mouse_dy

def is_right_mouse_held():
    return is_right_mouse_down