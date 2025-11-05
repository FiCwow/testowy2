import random

import numpy as np
from PyQt5.QtCore import QThread, QMutex, QMutexLocker

import Addresses
from Addresses import screen_width, screen_height, screen_x, screen_y
from Functions.GeneralFunctions import load_items_images, WindowCapture, merge_close_points
from Functions.MouseFunctions import manage_collect
from General.BotLogger import bot_logger
import cv2 as cv

lootLoop = 4


class LootThread(QThread):

    def __init__(self, loot_list):
        super().__init__()
        self.loot_list = loot_list
        self.running = True
        self.state_lock = QMutex()

    def run(self):
        global lootLoop
        zoom_img = 3
        load_items_images(self.loot_list)
        item_image = Addresses.item_list
        capture_screen = WindowCapture(screen_width[0] - screen_x[0], screen_height[0] - screen_y[0],
                                       screen_x[0], screen_y[0])

        while self.running:
            try:
                # --- OPTIMIZATION: Take only one screenshot per loop ---
                screenshot = capture_screen.get_screenshot()
                screenshot_gray = cv.cvtColor(screenshot, cv.COLOR_BGR2GRAY)
                screenshot_gray = cv.GaussianBlur(screenshot_gray, (7, 7), 0)
                screenshot_resized = cv.resize(screenshot_gray, None, fx=zoom_img, fy=zoom_img, interpolation=cv.INTER_CUBIC)

                all_found_items = []

                for file_name, value_list in item_image.items(): # For each item type (e.g., platinum coin)
                    for val in value_list[:-1]: # For each template image of that item
                        result = cv.matchTemplate(screenshot_resized, val, cv.TM_CCOEFF_NORMED)
                        locations = np.where(result >= Addresses.collect_threshold)
                        
                        for pt in zip(*locations[::-1]): # Switch x and y
                            # Store the location and the container it belongs to
                            all_found_items.append(((int(pt[0] / zoom_img), int(pt[1] / zoom_img)), value_list[-1]))

                # After checking all items, process the found locations
                if all_found_items:
                    # Sort by y-coordinate to loot from top to bottom
                    sorted_items = sorted(all_found_items, key=lambda item: item[0][1])
                    for (lx, ly), container in sorted_items:
                        # We don't know the item name here, just the action.
                        manage_collect(lx, ly, container)
                        bot_logger.info(f"Looting item at ({lx}, {ly}) into container: {container}")
                        QThread.msleep(random.randint(400, 650)) # Wait after each click

                QThread.msleep(300) # Wait before starting the next full scan
            except Exception as e:
                print(e)

    def stop(self):
        self.running = False