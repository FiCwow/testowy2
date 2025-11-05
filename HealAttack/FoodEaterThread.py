import time
import random
from PyQt5.QtCore import QThread
import Addresses
from Functions.KeyboardFunctions import press_hotkey


class FoodEaterThread(QThread):
    def __init__(self, food_hotkey, interval):
        super().__init__()
        self.running = True
        self.food_hotkey = food_hotkey.lower()
        self.interval = interval

    def run(self):
        while self.running:
            try:
                # Use the hotkey immediately on start
                press_hotkey(self.food_hotkey)

                # Wait for the specified interval with some randomization
                random_wait = self.interval + random.uniform(-5, 5)
                self.msleep(int(random_wait * 1000))

            except Exception as e:
                print(f"Error in FoodEaterThread: {e}")

    def stop(self):
        self.running = False