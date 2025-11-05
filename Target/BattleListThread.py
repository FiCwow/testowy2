from PyQt5.QtCore import QThread, pyqtSignal
from Functions.MemoryFunctions import read_targeting_status, read_target_info


class BattleListThread(QThread):
    """
    A thread that periodically reads the battle list from memory
    and emits the monster count and their names.
    """
    update_signal = pyqtSignal(int, list)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                target_id = read_targeting_status()
                if target_id != 0:
                    _, _, _, target_name, _ = read_target_info()
                    if target_name:
                        self.update_signal.emit(1, [target_name])
                    else:
                        self.update_signal.emit(1, ["Monster Detected"])
                else:
                    self.update_signal.emit(0, [])
            except Exception as e:
                pass
            self.msleep(250)  # Update four times per second

    def stop(self):
        self.running = False