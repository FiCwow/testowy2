import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QMessageBox,
    QPushButton, QListWidget, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt

from Functions.GeneralFunctions import manage_profile
from General.BotLogger import bot_logger
from Settings.ProfileManagerWidget import ProfileManagerWidget


class ProfileSetsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # --- Layout ---
        layout = QVBoxLayout(self)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)

        # --- Widgets ---
        self.profile_listWidget = QListWidget(self)
        self.profile_lineEdit = QLineEdit(self)
        save_button = QPushButton("💾 Save Set", self)
        save_button.setStyleSheet("color: white; background-color: #2980b9; font-weight: bold;")
        load_button = QPushButton("📂 Load Set", self)
        load_button.setStyleSheet("color: white; background-color: #e67e22; font-weight: bold;")
        delete_button = QPushButton("❌ Delete Set", self)
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold;")

        # --- GroupBox ---
        groupbox = QGroupBox("📚 Profile Sets")
        groupbox_layout = QVBoxLayout(groupbox)

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Set Name:"), self.profile_lineEdit)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(delete_button)

        groupbox_layout.addWidget(self.profile_listWidget)
        groupbox_layout.addLayout(form_layout)
        groupbox_layout.addLayout(buttons_layout)

        layout.addWidget(groupbox)
        layout.addWidget(self.status_label)

        # --- Connections ---
        save_button.clicked.connect(self.save_profile_set)
        load_button.clicked.connect(self.load_profile_set)
        delete_button.clicked.connect(self.delete_profile_set)
        self.profile_listWidget.currentItemChanged.connect(
            lambda current: self.profile_lineEdit.setText(current.text() if current else "")
        )
        self.profile_listWidget.itemDoubleClicked.connect(
            lambda item: self.confirm_and_load_set(item)
        )

        self.populate_profiles()

    def populate_profiles(self):
        self.profile_listWidget.clear()
        os.makedirs("Save/ProfileSets", exist_ok=True)
        for file in os.listdir("Save/ProfileSets"):
            if file.endswith(".json"):
                self.profile_listWidget.addItem(file.split('.')[0])

    def save_profile_set(self):
        profile_name = self.profile_lineEdit.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Input Error", "Please enter a name for the profile set.")
            return

        # Gather the names of the currently selected profiles in each tab
        profile_set_data = {}
        tabs_with_profiles = {
            "HealingAttack": self.main_window.healing_tab,
            "Targeting": self.main_window.target_tab, # Corrected from target_loot_tab
            "Looting": self.main_window.looter_tab,
            "Walker": self.main_window.walker_tab,
            "Training": self.main_window.training_tab,
            "SmartHotkeys": self.main_window.smart_hotkeys_tab,
            "Settings": self.main_window.settings_tab,
        }

        for name, tab_instance in tabs_with_profiles.items():
            profile_manager = tab_instance.findChild(ProfileManagerWidget)
            if profile_manager:
                current_item = profile_manager.profile_listWidget.currentItem()
                if current_item:
                    profile_set_data[name] = current_item.text()

        # Save the set
        if manage_profile("save", "Save/ProfileSets", profile_name, profile_set_data):
            self.status_label.setText(f"Profile set '{profile_name}' saved.")
            if not self.profile_listWidget.findItems(profile_name, Qt.MatchExactly):
                self.profile_listWidget.addItem(profile_name)

    def load_profile_set(self):
        current_item = self.profile_listWidget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Error", "Please select a profile set to load.")
            return

        profile_name = current_item.text()
        loaded_set = manage_profile("load", "Save/ProfileSets", profile_name)

        tabs_with_profiles = {
            "HealingAttack": self.main_window.healing_tab,
            "Targeting": self.main_window.target_tab, # Corrected from target_loot_tab
            "Looting": self.main_window.looter_tab,
            "Walker": self.main_window.walker_tab,
            "Training": self.main_window.training_tab,
            "SmartHotkeys": self.main_window.smart_hotkeys_tab,
            "Settings": self.main_window.settings_tab,
        }

        for name, tab_instance in tabs_with_profiles.items():
            profile_manager = tab_instance.findChild(ProfileManagerWidget)
            if name in loaded_set and profile_manager:
                profile_to_load = loaded_set[name]
                items = profile_manager.profile_listWidget.findItems(profile_to_load, Qt.MatchExactly)
                if items:
                    profile_manager.profile_listWidget.setCurrentItem(items[0])
                    profile_manager.load_profile()

        self.status_label.setText(f"Profile set '{profile_name}' loaded.")
        bot_logger.info(f"Loaded profile set: '{profile_name}'.")

    def confirm_and_load_set(self, item):
        """Asks for confirmation and then loads the double-clicked profile set."""
        if not item:
            return

        profile_name = item.text()
        reply = QMessageBox.question(self, 'Confirm Load Set',
                                     f"Are you sure you want to load the profile set '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.profile_listWidget.setCurrentItem(item)
            self.load_profile_set()

    def delete_profile_set(self):
        current_item = self.profile_listWidget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Error", "Please select a profile set to delete.")
            return

        profile_name = current_item.text()
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to delete the profile set '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if manage_profile("delete", "Save/ProfileSets", profile_name):
                self.status_label.setText(f"Profile set '{profile_name}' deleted.")
                self.populate_profiles()