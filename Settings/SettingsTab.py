from Addresses import screen_x, screen_y, screen_width, screen_height, coordinates_x, coordinates_y
import json
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox,
    QGridLayout, QPushButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from Functions.GeneralFunctions import manage_profile
from Settings.ProfileManagerWidget import ProfileManagerWidget
from Settings.SettingsThread import SettingsThread


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()

        # Thread Variables
        self.settings_thread = None

        # --- Status label at the bottom (for messages, instructions, and showing coordinates)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # Main layout
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        # Initialize sections
        self.set_environment()
        self.set_tools()
        self.setup_profile_manager()

        # Finally, add the status label in row=2 (bottom)
        self.layout.addWidget(self.status_label, 2, 0, 1, 2)

    def set_environment(self) -> None:
        """
        GroupBox for environment settings, like setting character position or loot screen area.
        """
        groupbox = QGroupBox("🌍 Environment", self)
        groupbox_layout = QVBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Buttons
        set_character_pos_button = QPushButton("🚶 Set Character", self)
        set_character_pos_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_character_pos_button.setToolTip("Click and then click on the center of your character on the screen.")
        set_loot_screen_button = QPushButton("💰 Set Loot Area", self)
        set_loot_screen_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_loot_screen_button.setToolTip("Click and then draw a rectangle over the area where loot appears.")

        # Button functions
        set_character_pos_button.clicked.connect(lambda: self.startSet_thread(0))
        set_loot_screen_button.clicked.connect(lambda: self.startSet_thread(-1))

        groupbox_layout.addWidget(set_character_pos_button)
        groupbox_layout.addWidget(set_loot_screen_button)

        self.layout.addWidget(groupbox, 0, 0)

    def set_tools(self) -> None:
        """
        GroupBox for setting backpack/tools coordinates (rope, shovel, runes, etc.).
        """
        groupbox = QGroupBox("🛠️ Tools", self)
        groupbox_layout = QVBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Buttons
        item_bp_button = QPushButton("🎒 1 Backpack", self)
        item_bp_button.setStyleSheet("background-color: #8e44ad;") # Purple
        item_bp_button.setToolTip("Set the coordinates of the first backpack slot.")
        item_bp1_button = QPushButton("🎒 2 Backpack", self)
        item_bp1_button.setStyleSheet("background-color: #8e44ad;") # Purple
        item_bp1_button.setToolTip("Set the coordinates of the second backpack slot.")
        item_bp2_button = QPushButton("🎒 3 Backpack", self)
        item_bp2_button.setStyleSheet("background-color: #8e44ad;") # Purple
        item_bp2_button.setToolTip("Set the coordinates of the third backpack slot.")
        item_bp3_button = QPushButton("🎒 4 Backpack", self)
        item_bp3_button.setStyleSheet("background-color: #8e44ad;") # Purple
        item_bp3_button.setToolTip("Set the coordinates of the fourth backpack slot.")
        rune1_button = QPushButton("🔥 First Rune", self)
        rune1_button.setStyleSheet("background-color: #8e44ad;") # Purple
        rune1_button.setToolTip("Set the coordinates of the rune used for 'First Rune' action.")
        health_button = QPushButton("💖 Health", self)
        health_button.setStyleSheet("background-color: #8e44ad;") # Purple
        health_button.setToolTip("Set the coordinates of your health bar.")
        mana_button = QPushButton("💧 Mana", self)
        mana_button.setStyleSheet("background-color: #8e44ad;") # Purple
        mana_button.setToolTip("Set the coordinates of your mana bar.")
        rune2_button = QPushButton("❄️ Second Rune", self)
        rune2_button.setStyleSheet("background-color: #8e44ad;") # Purple
        rune2_button.setToolTip("Set the coordinates of the rune used for 'Second Rune' action.")
        rope_button = QPushButton("🧗 Rope", self)
        rope_button.setStyleSheet("background-color: #8e44ad;") # Purple
        rope_button.setToolTip("Set the coordinates of the rope on your hotbar or backpack.")
        shovel_button = QPushButton("⛏️ Shovel", self)
        shovel_button.setStyleSheet("background-color: #8e44ad;") # Purple
        shovel_button.setToolTip("Set the coordinates of the shovel on your hotbar or backpack.")

        # Button -> coordinate index mapping
        item_bp_button.clicked.connect(lambda: self.startSet_thread(1))
        item_bp1_button.clicked.connect(lambda: self.startSet_thread(2))
        item_bp2_button.clicked.connect(lambda: self.startSet_thread(3))
        item_bp3_button.clicked.connect(lambda: self.startSet_thread(4))
        health_button.clicked.connect(lambda: self.startSet_thread(5))
        mana_button.clicked.connect(lambda: self.startSet_thread(11))
        rune1_button.clicked.connect(lambda: self.startSet_thread(6))
        rune2_button.clicked.connect(lambda: self.startSet_thread(8))
        shovel_button.clicked.connect(lambda: self.startSet_thread(9))
        rope_button.clicked.connect(lambda: self.startSet_thread(10))

        # Layout arrangement
        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()
        layout4 = QHBoxLayout()
        layout5 = QHBoxLayout()

        layout1.addWidget(item_bp_button)
        layout1.addWidget(item_bp1_button)

        layout2.addWidget(item_bp2_button)
        layout2.addWidget(item_bp3_button)

        layout3.addWidget(health_button)
        layout3.addWidget(mana_button)

        layout4.addWidget(rune1_button)
        layout4.addWidget(rune2_button)

        layout5.addWidget(rope_button)
        layout5.addWidget(shovel_button)

        groupbox_layout.addLayout(layout1)
        groupbox_layout.addLayout(layout2)
        groupbox_layout.addLayout(layout3)
        groupbox_layout.addLayout(layout4)
        groupbox_layout.addLayout(layout5)

        self.layout.addWidget(groupbox, 0, 1, 2, 1)

    def setup_profile_manager(self) -> None:
        """
        Initializes and places the ProfileManagerWidget.
        """
        profile_manager = ProfileManagerWidget( # type: ignore
            profile_directory="Save/Settings",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )
        profile_manager.set_status_label(self.status_label)

        self.layout.addWidget(profile_manager, 1, 0)

    def save_profile(self, autosave=False):
        """Exposes the save functionality for auto-saving."""
        profile_manager = self.findChild(ProfileManagerWidget)
        if profile_manager:
            profile_manager.save_profile(autosave=True)

    def get_data_for_saving(self) -> dict:
        """Provides the current settings data to be saved."""
        return {
            "screen_data": {
            "screenX": screen_x[0],
            "screenY": screen_y[0],
            "screenWidth": screen_width[0],
            "screenHeight": screen_height[0],
            "X": coordinates_x,
            "Y": coordinates_y
            }
        }

    def load_data_from_profile(self, loaded_data: dict) -> None:
        """Applies the loaded settings data."""
        settings_data = loaded_data.get("screen_data", {})
        screen_x[0] = settings_data.get("screenX", 0)
        screen_y[0] = settings_data.get("screenY", 0)
        screen_width[0] = settings_data.get("screenWidth", 0)
        screen_height[0] = settings_data.get("screenHeight", 0)
        bp_data_x = settings_data.get("X", [0] * len(coordinates_x))
        bp_data_y = settings_data.get("Y", [0] * len(coordinates_y))

        for i in range(len(coordinates_x)):
            coordinates_x[i] = bp_data_x[i]
            coordinates_y[i] = bp_data_y[i]

    def startSet_thread(self, index) -> None:
        # Stop any previous instance to avoid multiple threads running
        if self.settings_thread and self.settings_thread.isRunning():
            self.settings_thread.stop()

        self.settings_thread = SettingsThread(index, self.status_label)
        self.settings_thread.start()
