import time
from PyQt5.QtWidgets import QWidget, QGroupBox, QFormLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from Functions.MemoryFunctions import read_hp, read_mp, read_my_wpt


class StatusUpdateThread(QThread):
    """A thread that continuously reads character status and emits signals."""
    status_updated = pyqtSignal(int, int, int, int, int, int, int)  # hp, max_hp, mp, max_mp, x, y, z

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                hp, max_hp = read_hp()
                mp, max_mp = read_mp()
                x, y, z = read_my_wpt()

                if all(v is not None for v in [hp, max_hp, mp, max_mp, x, y, z]):
                    self.status_updated.emit(hp, max_hp, mp, max_mp, x, y, z)
            except Exception as e:
                print(f"Error reading status: {e}")
            time.sleep(0.2)  # Update 5 times per second

    def stop(self):
        self.running = False


class CharacterStatusWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- Icons (using emoji symbols) ---
        hp_icon_label = QLabel("💖")
        hp_icon_label.setToolTip("Health")

        mp_icon_label = QLabel("💧")
        mp_icon_label.setToolTip("Mana")

        coords_icon_label = QLabel("📍")
        coords_icon_label.setToolTip("Coordinates")

        # --- Health Bar ---
        self.hp_bar = QProgressBar()
        self.hp_bar.setTextVisible(True) # Keep text on bar
        self.hp_label = QLabel("0 / 0")

        # --- Mana Bar ---
        self.mp_bar = QProgressBar()
        self.mp_bar.setTextVisible(True) # Keep text on bar
        self.mp_label = QLabel("0 / 0")

        self.coords_label = QLabel("X: 0, Y: 0, Z: 0")

        # --- Layout ---
        layout = QHBoxLayout(self)
        layout.addWidget(hp_icon_label)
        layout.addWidget(self.hp_bar)
        layout.addWidget(self.hp_label)
        layout.addWidget(mp_icon_label)
        layout.addWidget(self.mp_bar)
        layout.addWidget(self.mp_label)
        layout.addSpacing(20) # Add a fixed small space
        layout.addWidget(coords_icon_label)
        layout.addWidget(self.coords_label) # type: ignore

        # Start the update thread
        self.status_thread = StatusUpdateThread()
        self.status_thread.status_updated.connect(self.update_status_display)
        self.status_thread.start()

    def _get_color_for_percent(self, percent, bar_type='hp'):
        """Returns a color hex code based on the percentage value and bar type."""
        if bar_type == 'hp':
            if percent > 60:
                return "#e74c3c"  # Bright Red
            elif percent > 30:
                return "#c0392b"  # Medium Red
            else:
                return "#a93226"  # Dark Red
        elif bar_type == 'mp':
            if percent > 60:
                return "#3498db"  # Bright Blue
            elif percent > 30:
                return "#2980b9"  # Medium Blue
            else:
                return "#1f618d"  # Dark Blue
        return "#7f8c8d" # Default gray

    def update_status_display(self, hp, max_hp, mp, max_mp, x, y, z):
        """Updates the progress bars and labels with new values."""
        # --- Health ---
        self.hp_bar.setMaximum(max_hp if max_hp > 0 else 100)
        self.hp_bar.setValue(hp if hp is not None else 0)
        hp_percent = (hp * 100) / max_hp if max_hp and hp is not None else 0
        hp_color = self._get_color_for_percent(hp_percent, 'hp')
        self.hp_bar.setStyleSheet(f"QProgressBar {{ text-align: center; }} QProgressBar::chunk {{ background-color: {hp_color}; }}")
        self.hp_bar.setFormat(f"{hp_percent:.0f}%")
        self.hp_label.setStyleSheet("")  # Remove color from text
        self.hp_label.setText(f"{hp or 0} / {max_hp or 0}")

        # --- Mana ---
        self.mp_bar.setMaximum(max_mp if max_mp > 0 else 100)
        self.mp_bar.setValue(mp if mp is not None else 0)
        mp_percent = (mp * 100) / max_mp if max_mp and mp is not None else 0
        mp_color = self._get_color_for_percent(mp_percent, 'mp')
        self.mp_bar.setStyleSheet(f"QProgressBar {{ text-align: center; }} QProgressBar::chunk {{ background-color: {mp_color}; }}")
        self.mp_bar.setFormat(f"{mp_percent:.0f}%")
        self.mp_label.setStyleSheet("") # Remove color from text
        self.mp_label.setText(f"{mp or 0} / {max_mp or 0}")

        # --- Coordinates ---
        self.coords_label.setText(f"X: {x}, Y: {y}, Z: {z}")

    def stop_thread(self):
        self.status_thread.stop()
        self.status_thread.wait()