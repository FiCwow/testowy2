import time
import pyautogui
import win32api
import json
import numpy as np
import win32gui
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget
from win32con import VK_LBUTTON

import Addresses
from Functions.KeyboardFunctions import press_hotkey


class AreaPreviewWindow(QWidget):
    """A semi-transparent, borderless window to show a preview of an area."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool # Ensures it doesn't show up in the taskbar
        )
        # This combination makes the window semi-transparent but not click-through, which is more reliable.
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.load_style()

    def load_style(self):
        """Loads color and opacity from settings and applies them."""
        try:
            with open("Save/Settings/theme.json", "r") as f:
                settings = json.load(f)
                color_hex = settings.get("preview_color", "#ff0000")
                opacity_percent = settings.get("preview_opacity", 30)
        except (FileNotFoundError, json.JSONDecodeError):
            color_hex = "#ff0000"
            opacity_percent = 30

        opacity = opacity_percent / 100.0
        self.setStyleSheet(f"background-color: rgba({int(color_hex[1:3], 16)}, {int(color_hex[3:5], 16)}, {int(color_hex[5:7], 16)}, {opacity}); border: 2px solid {color_hex};")

    def update_geometry_and_show(self, x1, y1, x2, y2):
        """Calculates absolute screen coordinates and shows the window."""
        try:
            game_rect = win32gui.GetWindowRect(Addresses.game)
            abs_x = game_rect[0] + x1
            abs_y = game_rect[1] + y1
            width = x2 - x1
            height = y2 - y1

            self.setGeometry(abs_x, abs_y, width, height)
            self.show()
        except Exception as e:
            print(f"Could not show preview window: {e}")


class ConditionalHotkeysThread(QThread):
    status_update = pyqtSignal(str)

    def __init__(self, rules):
        super().__init__()
        self.running = True
        self.rules = rules
        self.first_check_done = False

    def run(self):
        if not self.rules:
            return

        # --- Optimization: Calculate a single bounding box for all rules ---
        min_x1 = min(r['x1'] for r in self.rules)
        min_y1 = min(r['y1'] for r in self.rules)
        max_x2 = max(r['x2'] for r in self.rules)
        max_y2 = max(r['y2'] for r in self.rules)

        while self.running:
            try:
                # Get game window position
                game_rect = win32gui.GetWindowRect(Addresses.game)
                
                # Define the single, large region for the screenshot
                screenshot_region = (
                    game_rect[0] + min_x1,
                    game_rect[1] + min_y1,
                    max_x2 - min_x1,
                    max_y2 - min_y1
                )

                # Take one screenshot for all rules
                screenshot = pyautogui.screenshot(region=screenshot_region)
                img_array = np.array(screenshot)

                for rule in self.rules:
                    # Calculate the rule's area relative to the large screenshot
                    relative_x1 = rule['x1'] - min_x1
                    relative_y1 = rule['y1'] - min_y1
                    relative_x2 = rule['x2'] - min_x1
                    relative_y2 = rule['y2'] - min_y1

                    # "Crop" the area from the numpy array (very fast)
                    rule_area_array = img_array[relative_y1:relative_y2, relative_x1:relative_x2]

                    target_color = np.array([rule['r'], rule['g'], rule['b']])
                    condition = rule.get("condition", "Color is present")

                    # Efficiently check for the color in the cropped numpy array
                    color_found = np.any(np.all(rule_area_array == target_color, axis=-1))

                    self.status_update.emit("DETECTED" if color_found else "Not found")

                    # Only press hotkey after the first check has completed
                    if self.first_check_done:
                        if (condition == "Color is present" and color_found) or \
                           (condition == "Color is NOT present" and not color_found):
                            press_hotkey(rule['hotkey'])
                            self.msleep(500) # Cooldown after action
                            break # Move to next main loop iteration after an action

            except Exception as e:
                print(f"Error checking conditional hotkey: {e}")
            
            self.msleep(150) # Check frequency
            # After the first loop, enable hotkey pressing
            if not self.first_check_done:
                self.first_check_done = True

    def stop(self):
        self.running = False


class SetCoordinateThread(QThread):
    """A thread to guide the user through setting an area and a color."""
    update_status = pyqtSignal(str)
    finished_setting = pyqtSignal(int, int, int, int, tuple)  # x1, y1, x2, y2, (r, g, b)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        try:
            # Step 1: Get top-left corner
            self.update_status.emit("Click the TOP-LEFT corner of the area...")
            while not (win32api.GetKeyState(VK_LBUTTON) & 0x8000): self.msleep(10)
            x1_screen, y1_screen = win32api.GetCursorPos()
            x1_client, y1_client = win32gui.ScreenToClient(Addresses.game, (x1_screen, y1_screen))
            self.msleep(200) # Debounce

            # Step 2: Get bottom-right corner
            self.update_status.emit("Click the BOTTOM-RIGHT corner of the area...")
            while not (win32api.GetKeyState(VK_LBUTTON) & 0x8000): self.msleep(10)
            x2_screen, y2_screen = win32api.GetCursorPos()
            x2_client, y2_client = win32gui.ScreenToClient(Addresses.game, (x2_screen, y2_screen))
            self.msleep(200) # Debounce

            # Step 3: Get the color to detect
            self.update_status.emit("Now, click on the COLOR to detect...")
            while not (win32api.GetKeyState(VK_LBUTTON) & 0x8000): self.msleep(10)
            color_x_screen, color_y_screen = win32api.GetCursorPos()
            color = pyautogui.pixel(color_x_screen, color_y_screen)

            # Ensure coordinates are positive and within window bounds
            x1, y1 = max(0, x1_client), max(0, y1_client)
            x2, y2 = max(0, x2_client), max(0, y2_client)

            self.finished_setting.emit(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), color)
        except Exception as e:
            print(f"Error in SetCoordinateThread: {e}")


class SetColorThread(QThread):
    """A thread to capture only a pixel color."""
    update_status = pyqtSignal(str)
    color_captured = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        self.update_status.emit("Click on the new color to detect...")
        while not (win32api.GetKeyState(VK_LBUTTON) & 0x8000):
            self.msleep(10)
            if not self.running: return

        x, y = win32api.GetCursorPos()
        # We don't need to convert to client coordinates here, just get the color
        color = pyautogui.pixel(x, y)
        self.color_captured.emit(color)