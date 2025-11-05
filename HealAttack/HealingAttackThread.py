import random
import winsound
from PyQt5.QtCore import QThread, Qt

import Addresses
from Addresses import coordinates_x, coordinates_y
from Functions.KeyboardFunctions import press_hotkey
from Functions.MemoryFunctions import *
from Functions.MouseFunctions import mouse_function


class HealThread(QThread):

    def __init__(self, healing_list, low_hp_alert_enabled=False, low_hp_alert_threshold=0):
        super().__init__()
        self.rules = []
        for i in range(healing_list.count()):
            item = healing_list.item(i)
            if item:
                self.rules.append(item.data(Qt.UserRole))
        self.low_hp_alert_enabled = low_hp_alert_enabled
        self.low_hp_alert_threshold = low_hp_alert_threshold
        self.alert_cooldown = 0
        self.last_alert_time = 0
        self.running = True

    def run(self):
        while self.running:
            try:
                current_hp, current_max_hp, current_mp, current_max_mp = read_my_stats()
                if any(v is None for v in [current_hp, current_max_hp, current_mp, current_max_mp]):
                    QThread.msleep(200)
                    continue

                # --- Low HP Alert Check ---
                if self.low_hp_alert_enabled:
                    hp_percent = (current_hp * 100) / current_max_hp if current_max_hp > 0 else 0
                    current_time = QThread.msleep(0) # Using msleep(0) to get a time reference
                    if hp_percent < self.low_hp_alert_threshold and (current_time - self.last_alert_time > 3000): # 3 sec cooldown
                        winsound.Beep(800, 500) # Frequency 800Hz, Duration 500ms
                        self.last_alert_time = current_time


                # --- Healing Logic ---
                for rule in self.rules:
                    if current_mp < rule.get("MinMp", 0):
                        continue

                    value_to_check = 0
                    if rule['Type'] == "HP %":
                        value_to_check = (current_hp * 100) / current_max_hp if current_max_hp > 0 else 0
                    elif rule['Type'] == "MP %":
                        value_to_check = (current_mp * 100) / current_max_mp if current_max_mp > 0 else 0
                    elif rule['Type'] == "HP":
                        value_to_check = current_hp
                    elif rule['Type'] == "MP":
                        value_to_check = current_mp

                    condition_met = False
                    condition = rule.get("Condition", "is below <") # Safely get condition, default to old logic
                    val1 = rule.get("Value1")
                    val2 = rule.get("Value2")

                    # Backward compatibility for old profiles with "Below" and "Above"
                    if val1 is None: val1 = rule.get("Below")
                    if val2 is None: val2 = rule.get("Above")

                    if condition == "is below <" and val1 is not None and value_to_check < val1:
                        condition_met = True
                    elif condition == "is above >" and val1 is not None and value_to_check > val1:
                        condition_met = True
                    elif condition == "is between" and all(v is not None for v in [val1, val2]) and val1 < value_to_check < val2:
                        condition_met = True

                    if condition_met:
                        # Execute the first rule that matches and then break the loop for this cycle.
                        # Priority is now determined by the order in the list.
                        if rule['Key'] == "Health":
                            mouse_function(coordinates_x[5], coordinates_y[5], option=5)
                        elif rule['Key'] == "Mana":
                            mouse_function(coordinates_x[11], coordinates_y[11], option=5)
                        else:
                            press_hotkey(rule['Key'])
                        QThread.msleep(random.randint(300, 500)) # Cooldown after action
                        break # Exit inner loop and start checks from the top in the next cycle

                QThread.msleep(150) # Wait before next cycle if no rule was met
            except Exception as e:
                print("Exception: ", e)

    def stop(self):
        self.running = False


def attack_monster(attack_data) -> bool:
    target_x, target_y, target_z, target_name, target_hp = read_target_info()
    current_hp, current_max_hp, current_mp, current_max_mp = read_my_stats()

    if any(v is None for v in [target_hp, current_hp, current_max_hp, current_mp]):
        return False

    if target_hp < 0 or target_hp > 100:
        target_hp = 100
    hp_percentage = (current_hp * 100) / current_max_hp
    if ((int(attack_data['HpFrom']) >= target_hp > int(attack_data['HpTo'])) or int(attack_data['HpFrom'] == 0)
            and current_mp >= int(attack_data['MinMp'])
            and (attack_data['Name'] == '*' or target_name in attack_data['Name'])
            and attack_data['MinHp'] <= hp_percentage):
        return True
    return False


class AttackThread(QThread):

    def __init__(self, attack_list):
        super().__init__()
        self.attack_list = attack_list
        self.running = True

    def run(self):
        while self.running:
            try:
                for attack_index in range(self.attack_list.count()):
                    attack_data = self.attack_list.item(attack_index).data(Qt.UserRole)
                    if read_targeting_status() != 0:
                        if attack_monster(attack_data):
                            if attack_data['Key'][0] == 'F':

                                press_hotkey(int(attack_data['Key'][1:]))
                                QThread.msleep(random.randint(150, 250))
                            else:
                                if attack_data['Key'] == 'First Rune':
                                    mouse_function(coordinates_x[6],
                                                coordinates_y[6],
                                                   option=1)
                                elif attack_data['Key'] == 'Second Rune':
                                    mouse_function(coordinates_x[8],
                                                coordinates_y[8],
                                                   option=1)
                                x, y, z = read_my_wpt()
                                target_x, target_y, target_z, target_name, target_hp = read_target_info()
                                x = target_x - x
                                y = target_y - y
                                mouse_function(coordinates_x[0] + x * Addresses.square_size, coordinates_y[0] + y * Addresses.square_size, option=2)
                                QThread.msleep(random.randint(800, 1000))
                QThread.msleep(random.randint(100, 200))
            except Exception as e:
                print(e)

    def stop(self):
        self.running = False
