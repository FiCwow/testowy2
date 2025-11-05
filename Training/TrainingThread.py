import random
import win32gui
import time
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from win32con import VK_LBUTTON

from Addresses import fishing_x, fishing_y
from Functions.MemoryFunctions import *
from Functions.KeyboardFunctions import press_hotkey
from Functions.MouseFunctions import mouse_function


class TrainingThread(QThread):

    def __init__(self, enabled_rules: list):
        super().__init__()
        self.rules = enabled_rules
        self.running = True

    def run(self):
        while self.running:
            try:
                current_hp, current_max_hp, current_mp, current_max_mp = read_my_stats()
                if any(v is None for v in [current_hp, current_max_hp, current_mp, current_max_mp]):
                    QThread.msleep(200)
                    continue

                monsters_on_screen = read_targeting_status() != 0

                for rule in self.rules:
                    conditions_met = True

                    # Check Mana Condition
                    mana_cond = rule['mana_cond']
                    if mana_cond == "Above >" and not (current_mp > rule['mana_val1']):
                        conditions_met = False
                    elif mana_cond == "Below <" and not (current_mp < rule['mana_val1']):
                        conditions_met = False
                    elif mana_cond == "Between" and not (rule['mana_val1'] < current_mp < rule['mana_val2']):
                        conditions_met = False

                    # Check HP Condition
                    if conditions_met and rule['hp_cond'] != "Any":
                        hp_cond = rule['hp_cond']
                        if hp_cond == "Above >" and not (current_hp > rule['hp_val1']):
                            conditions_met = False
                        elif hp_cond == "Below <" and not (current_hp < rule['hp_val1']):
                            conditions_met = False
                        elif hp_cond == "Between" and not (rule['hp_val1'] < current_hp < rule['hp_val2']):
                            conditions_met = False

                    # Check Monster Condition
                    if conditions_met and rule['monster_cond'] != "Any":
                        if rule['monster_cond'] == "Monsters on screen" and not monsters_on_screen:
                            conditions_met = False
                        elif rule['monster_cond'] == "No monsters on screen" and monsters_on_screen:
                            conditions_met = False

                    if conditions_met:
                        press_hotkey(rule['hotkey'])
                        QThread.msleep(random.randint(800, 1200)) # Cooldown after casting
                        break # Exit the inner loop and start checks from the top

                QThread.msleep(200) # Wait before next cycle if no rule was met
            except Exception as e:
                print(e)

    def stop(self):
        self.running = False


class ClickThread(QThread):
    def __init__(self, timer, hotkey):
        super().__init__()
        self.timer = timer
        self.hotkey = hotkey
        self.running = True

    def run(self):
        timer = 0
        while self.running:
            try:
                if timer/1000 >= self.timer:
                    press_hotkey(int(self.hotkey[1:]))
                    timer = 0
                sleep_value = random.randint(500, 600)
                QThread.msleep(sleep_value)
                timer += sleep_value

            except Exception as e:
                print(e)

    def stop(self):
        self.running = False


class FishingThread(QThread):
    update_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        timer = 0
        counter = 0
        baits = 0
        if fishing_x[2] != 0:
            QThread.msleep(random.randint(1000, 1100))
            mouse_function(fishing_x[2], fishing_y[2], option=1)
            QThread.msleep(random.randint(1000, 1100))
            mouse_function(fishing_x[1], fishing_y[1], option=2)
            QThread.msleep(random.randint(1000, 1100))
            baits += 1
        while self.running:
            mouse_function(fishing_x[0], fishing_y[0], option=1)
            mouse_function(fishing_x[1], fishing_y[1], option=2)
            counter += 1
            randomizer = random.randint(1000, 1100)
            timer += randomizer
            QThread.msleep(randomizer)
            self.update_status.emit(f"Clicked {counter} times | used {baits} baits")
            if counter % 1015 == 0 and fishing_x[2] != 0:
                QThread.msleep(random.randint(1000, 1100))
                mouse_function(fishing_x[2], fishing_y[2], option=1)
                QThread.msleep(random.randint(1000, 1100))
                mouse_function(fishing_x[1], fishing_y[1], option=2)
                QThread.msleep(random.randint(1000, 1100))
                baits += 1
            if int(timer/1000) >= 20 and fishing_x[3] != 0:
                for _ in range(3):
                    mouse_function(fishing_x[3], fishing_y[3], option=1)
                    QThread.msleep(random.randint(300, 500))
                timer = 0



        return
    def stop(self):
        self.running = False


class SetThread(QThread):

    # Signals to communicate with the main GUI thread
    update_status = pyqtSignal(str, str)  # message, color
    finished_setting = pyqtSignal(int, int, int) # index, x, y

    def __init__(self, index):
        super().__init__()
        self.index = index
        self.running = True

    def run(self):
        self.update_status.emit("Click on the desired location...", "blue")
        while self.running:
            cur_x, cur_y = win32gui.ScreenToClient(Addresses.game, win32api.GetCursorPos())
            QThread.msleep(10)
            self.update_status.emit(f"Current: X={cur_x}  Y={cur_y}", "blue")
            if win32api.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                self.finished_setting.emit(self.index, cur_x, cur_y)
                self.running = False
                return
        # Revert status when thread is stopped without clicking
        self.update_status.emit("", "red")


class AntiIdleThread(QThread):
    """
    A thread to prevent the character from being kicked for inactivity.
    """
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            # Wait for a random interval, e.g., between 60 and 120 seconds
            sleep_time = random.randint(60, 120)
            self.msleep(sleep_time * 1000)

            if not self.running:
                break

            # Perform a small, random action
            action = random.choice(['turn', 'step'])
            if action == 'turn':
                press_hotkey(random.choice([rParam[2], rParam[3]])) # Turn right or left
            elif action == 'step':
                direction = random.choice([rParam[0], rParam[1], rParam[2], rParam[3]])
                press_hotkey(direction)
                self.msleep(200)
                # Step back to original position (opposite direction)
                if direction == rParam[0]: press_hotkey(rParam[1])
                elif direction == rParam[1]: press_hotkey(rParam[0])
                elif direction == rParam[2]: press_hotkey(rParam[3])
                elif direction == rParam[3]: press_hotkey(rParam[2])

    def stop(self):
        self.running = False
