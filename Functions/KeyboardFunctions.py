import random
import time
import win32api
import win32gui
import win32con
import Addresses
from Addresses import rParam, lParam, coordinates_x, coordinates_y
from Functions.MouseFunctions import mouse_function
import win32con


def walk(wpt_direction, my_x, my_y, my_z, map_x, map_y, map_z) -> None:
    x = map_x - my_x
    y = map_y - my_y
    z = map_z - my_z

    # Priority 1: Z level change
    if z > 0: # Going down
        mouse_function(coordinates_x[0] + x * Addresses.square_size, coordinates_y[0] + y * Addresses.square_size, option=2)
        time.sleep(random.uniform(0.5, 0.7))
        return
    if z < 0: # Going up (handled by rope/ladder/shovel waypoints)
        # This case is handled by specific waypoint actions, but we can add a map click as a fallback.
        mouse_function(coordinates_x[0] + x * Addresses.square_size, coordinates_y[0] + y * Addresses.square_size, option=2)
        time.sleep(random.uniform(0.5, 0.7))
        return

    # Priority 2: Step-by-step walking for adjacent squares
    if abs(x) <= 1 and abs(y) <= 1 and z == 0:
        if y == -1: # North
            press_key('up')
        elif y == 1: # South
            press_key('down')
        elif x == 1: # East
            press_key('right')
        elif x == -1: # West
            press_key('left')
        time.sleep(random.uniform(0.2, 0.4))
        return

    # Priority 3: Map click for distant waypoints on the same floor
    if abs(x) <= 7 and abs(y) <= 5 and z == 0:
        mouse_function(coordinates_x[0] + x * Addresses.square_size, coordinates_y[0] + y * Addresses.square_size, option=2)
        time.sleep(random.uniform(0.5, 0.7))
        return


def stay_diagonal(my_x, my_y, monster_x, monster_y) -> None:
    x = monster_x - my_x
    y = monster_y - my_y
    if abs(x) == 1 and abs(y) == 1:
        return
    if x == 1 and y == 0:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])  # Up key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])  # Up key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[1], lParam[1])  # Down key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[1], lParam[1])  # Down key up
            return
    if x == -1 and y == 0:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])  # Up key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])  # Up key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[1], lParam[1])  # Down key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[1], lParam[1])  # Down key up
            return
    if x == 0 and y == 1:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[2], lParam[2])  # Right key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[2], lParam[2])  # Right key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[3], lParam[3])  # Left key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[3], lParam[3])  # Left key up
            return
    if x == 0 and y == -1:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[2], lParam[2])  # Right key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[2], lParam[2])  # Right key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[3], lParam[3])  # Left key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[3], lParam[3])  # Left key up
            return


def chaseDiagonal_monster(my_x, my_y, monster_x, monster_y) -> None:
    x_diff = monster_x - my_x
    y_diff = monster_y - my_y

    if abs(x_diff) == 1 and abs(y_diff) == 1:
        return

    if (x_diff == 0 and abs(y_diff) == 1) or (y_diff == 0 and abs(x_diff) == 1):
        stay_diagonal(my_x, my_y, monster_x, monster_y)
    else:
        chase_monster(my_x, my_y, monster_x, monster_y)


def chase_monster(my_x, my_y, monster_x, monster_y) -> None:
    x = monster_x - my_x
    y = monster_y - my_y
    if abs(x) == 1 and abs(y) == 1:
        return

    if x > 0 and y == 0:
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[2], lParam[2])  # Right key down
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[2], lParam[2])  # Right key up
        return
    if x > 0 > y:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[2], lParam[2])  # Right key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[2], lParam[2])  # Right key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])  # Up key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])  # Up key up
            return
    if x > 0 and y > 0:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[2], lParam[2])  # Right key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[2], lParam[2])  # Right key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[1], lParam[1])  # Down key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[1], lParam[1])  # Down key up
            return
    if x < 0 and y == 0:
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[3], lParam[3])  # Left key down
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[3], lParam[3])  # Left key up
        return
    if x < 0 and y < 0:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[3], lParam[3])  # Left key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[3], lParam[3])  # Left key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])  # Up key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])  # Up key up
            return
    if x < 0 < y:
        if random.randint(0, 1) == 0:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[3], lParam[3])  # Left key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[3], lParam[3])  # Left key up
            return
        else:
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[1], lParam[1])  # Down key down
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[1], lParam[1])  # Down key up
            return
    if x == 0 and y < 0:
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])  # Up key down
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])  # Up key up
        return
    if x == 0 and y > 0:
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[1], lParam[1])  # Down key down
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[1], lParam[1])  # Down key up
        return


def press_key(key) -> None:
    vk_code = win32api.VkKeyScan(key[0])
    if vk_code != -1:
        scan_code = win32api.MapVirtualKey(vk_code & 0xFF, 0)
        keydown_lparam = (scan_code << 16) | 1
        keyup_lparam = keydown_lparam | (0x3 << 30)
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, vk_code & 0xFF, keydown_lparam)
        win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, vk_code & 0xFF, keyup_lparam)


def press_hotkey(hotkey) -> None: # Can be int (1-12 for F-keys) or str ('f1', 'a', 'space')
    if isinstance(hotkey, str):
        hotkey = hotkey.lower()
        if hotkey.startswith('f') and hotkey[1:].isdigit():
            f_key_num = int(hotkey[1:])
            if 1 <= f_key_num <= 12:
                vk_code = win32con.VK_F1 + f_key_num - 1
                hotkey_index = (((0x003A0001 >> 16) + f_key_num) << 16) + 1
                win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, vk_code, hotkey_index)
                win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, vk_code, hotkey_index)
        elif hotkey in ['up', 'down', 'left', 'right']:
            key_map = {'up': 0, 'down': 1, 'right': 2, 'left': 3}
            idx = key_map[hotkey]
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, rParam[0], lParam[0])
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, rParam[0], lParam[0])
        else:
            # Handle other keys like 'a', 'space', etc.
            # This part can be expanded with a mapping if needed.
            press_key(hotkey)

    elif isinstance(hotkey, int):
        # Check if it's a function key (F1-F12)
        if 1 <= hotkey <= 12:
            vk_code = win32con.VK_F1 + hotkey - 1
            hotkey_index = (((0x003A0001 >> 16) + hotkey) << 16) + 1
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, vk_code, hotkey_index)
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, vk_code, hotkey_index)
        else: # Assume it's a direction key from rParam
            try:
                win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, hotkey, lParam[rParam.index(hotkey)])
                win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, hotkey, lParam[rParam.index(hotkey)])
            except (ValueError, IndexError):
                print(f"Warning: Could not press hotkey with code {hotkey}. Not a valid direction key.")