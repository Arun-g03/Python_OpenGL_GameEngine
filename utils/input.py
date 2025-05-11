import glfw

# Input state
keys = {}
mouse_buttons = {}
mouse_dx = 0
mouse_dy = 0
last_mouse_pos = (0, 0)
mouse_button_pressed = {}  # Track button press events

# Key callback
def key_callback(window, key, scancode, action, mods):
    print(f"Key callback: key={key}, action={action}")
    keys[key] = action

# Mouse button callback
def mouse_button_callback(window, button, action, mods):
    print(f"Mouse button: button={button}, action={action}")
    mouse_buttons[button] = action
    if action == glfw.PRESS:
        mouse_button_pressed[button] = True
    elif action == glfw.RELEASE:
        mouse_button_pressed[button] = False

# Cursor position callback
def cursor_position_callback(window, xpos, ypos):
    global mouse_dx, mouse_dy, last_mouse_pos
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
    is_down = keys.get(key) == glfw.PRESS
    print(f"Checking key {key}: {is_down}")
    return is_down

def is_mouse_down(button):
    is_down = mouse_buttons.get(button) == glfw.PRESS
    print(f"Checking mouse button {button}: {is_down}")
    return is_down

def was_mouse_pressed(button):
    """Check if a mouse button was just pressed this frame"""
    was_pressed = mouse_button_pressed.get(button, False)
    if was_pressed:
        mouse_button_pressed[button] = False  # Reset the press state
    return was_pressed