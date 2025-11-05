import time
from PyQt5.QtCore import QThread
from Functions.MemoryFunctions import read_character_speed
from Functions.KeyboardFunctions import press_hotkey
from General.BotLogger import bot_logger

class TimedSpellsThread(QThread):
    def __init__(self, spells_to_cast, cast_if_needed=False):
        """
        spells_to_cast: A list of dictionaries, e.g.,
        [
            {'spell': 'utani hur', 'hotkey': 'f1', 'interval': 30, 'last_cast': 0},
            {'spell': 'utamo vita', 'hotkey': 'f2', 'interval': 200, 'last_cast': 0}
        ]
        cast_if_needed: Boolean, if True, haste spells are only cast if not already hasted.
        """
        super().__init__()
        self.running = True
        self.spells = spells_to_cast
        self.cast_if_needed = cast_if_needed

    def run(self):
        current_time = time.time()
        for spell in self.spells:
            spell['last_cast'] = 0  # Initialize to 0 to allow immediate casting

        while self.running:
            current_time = time.time()
            for spell in self.spells:
                if current_time - spell['last_cast'] >= spell['interval']:
                    # Special handling for haste spells if 'cast_if_needed' is on
                    if self.cast_if_needed and spell['spell'] in ['utani hur', 'utani gran hur']:
                        speed = read_character_speed()
                        if speed is not None and speed > 220:  # Player is already hasted, so skip
                            spell['last_cast'] = current_time # Reset timer to avoid spamming checks
                            continue

                    press_hotkey(spell['hotkey'])
                    bot_logger.info(f"Casting timed spell: '{spell['spell']}'")
                    spell['last_cast'] = current_time
                    time.sleep(0.1)  # Small delay to prevent casting multiple spells at once
            time.sleep(0.5)

    def stop(self):
        self.running = False