import json
import os
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QMessageBox,
    QPushButton, QListWidget, QLineEdit, QLabel
)

from Functions.GeneralFunctions import manage_profile


class ProfileManagerWidget(QGroupBox):
    """
    A self-contained widget for saving and loading settings profiles.
    It wraps a QListWidget, QLineEdit, and buttons, handling all related logic.
    """
    def __init__(self, profile_directory: str, data_provider_func: callable, data_consumer_func: callable, parent=None):
        super().__init__("Save & Load", parent)

        self.profile_dir = profile_directory
        self.get_data_to_save = data_provider_func
        self.load_data_from_profile = data_consumer_func
        self.status_label = None  # Will be set from outside
        self.currently_loaded_item = None

        # --- Widgets ---
        self.profile_listWidget = QListWidget(self)
        self.profile_lineEdit = QLineEdit(self)
        save_button = QPushButton("Save", self)
        save_button.setStyleSheet("color: white; background-color: #2980b9; font-weight: bold;")
        load_button = QPushButton("Load", self)
        load_button.setStyleSheet("color: white; background-color: #e67e22; font-weight: bold;")
        rename_button = QPushButton("Rename", self)
        rename_button.setStyleSheet("background-color: #7f8c8d;")
        delete_button = QPushButton("Delete", self)
        delete_button.setStyleSheet("color: white; background-color: #c0392b;")

        # --- Layout ---
        groupbox_layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Name:"), self.profile_lineEdit)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(5)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(delete_button)

        groupbox_layout.addWidget(self.profile_listWidget)
        groupbox_layout.addLayout(form_layout)
        groupbox_layout.addWidget(rename_button)
        groupbox_layout.addLayout(buttons_layout)

        # --- Connections ---
        save_button.clicked.connect(self.save_profile)
        load_button.clicked.connect(self.load_profile)
        rename_button.clicked.connect(self.rename_profile)
        delete_button.clicked.connect(self.delete_profile)
        self.profile_listWidget.currentItemChanged.connect(
            lambda current: self.profile_lineEdit.setText(current.text() if current else "")
        )
        self.profile_listWidget.itemDoubleClicked.connect(self.confirm_and_load_profile)
        self.populate_profiles()

    def set_status_label(self, status_label: QLabel):
        """Assigns an external QLabel to show status messages."""
        self.status_label = status_label

    def _update_status(self, message: str, is_error: bool = False):
        if self.status_label:
            color = "red" if is_error else "green"
            self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.status_label.setText(message)

    def populate_profiles(self):
        """Clears and loads all .json profile names from the directory."""
        self.profile_listWidget.clear()
        os.makedirs(self.profile_dir, exist_ok=True)
        for file in os.listdir(self.profile_dir):
            if file.endswith(".json"):
                self.profile_listWidget.addItem(file.split('.')[0])

    def save_profile(self, autosave=False):
        if autosave:
            profile_name = "_last"
        else:
            profile_name = self.profile_lineEdit.text().strip()
            if not profile_name:
                self._update_status("Please enter a profile name to save.", is_error=True)
                return

            # Check if profile exists and ask for confirmation to overwrite
            filename = os.path.join(self.profile_dir, f"{profile_name}.json")
            if os.path.exists(filename):
                reply = QMessageBox.question(self, 'Confirm Overwrite',
                                             f"A profile named '{profile_name}' already exists. Do you want to overwrite it?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self._update_status("Save operation cancelled.", is_error=True)
                    return

        data_to_save = self.get_data_to_save()

        if not autosave:
            if manage_profile("save", self.profile_dir, profile_name, data_to_save):
                self._update_status(f"Profile '{profile_name}' has been saved!")
                # Add to list if it's not already there
                if not self.profile_listWidget.findItems(profile_name, Qt.MatchExactly):
                    self.profile_listWidget.addItem(profile_name)

    def load_profile(self):
        current_item = self.profile_listWidget.currentItem()
        if not current_item:
            self.profile_listWidget.setStyleSheet("border: 2px solid red;")
            self._update_status("Please select a profile from the list to load.", is_error=True)
            return

        self.profile_listWidget.setStyleSheet("")
        profile_name = current_item.text()
        filename = os.path.join(self.profile_dir, f"{profile_name}.json")

        # Reset color of previously loaded item
        if self.currently_loaded_item:
            self.currently_loaded_item.setForeground(Qt.white) # Or your default text color

        # Set new loaded item and color it
        current_item.setForeground(Qt.red)
        self.currently_loaded_item = current_item


        with open(filename, "r") as f:
            loaded_data = json.load(f)

        self.load_data_from_profile(loaded_data)
        self._update_status(f"Profile '{profile_name}' loaded successfully!")

    def confirm_and_load_profile(self, item):
        """Asks for confirmation and then loads the double-clicked profile."""
        if not item:
            return

        profile_name = item.text()
        reply = QMessageBox.question(self, 'Confirm Load',
                                     f"Are you sure you want to load the profile '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.profile_listWidget.setCurrentItem(item)
            self.load_profile()

    def load_profile_by_name(self, profile_name: str):
        """Loads a profile by its name without requiring user selection."""
        filename = os.path.join(self.profile_dir, f"{profile_name}.json")
        if not os.path.exists(filename):
            self._update_status(f"Profile '{profile_name}' not found.", is_error=True)
            return

        try:
            with open(filename, "r") as f:
                loaded_data = json.load(f)
            self.load_data_from_profile(loaded_data)

            # Visually mark the loaded profile
            items = self.profile_listWidget.findItems(profile_name, Qt.MatchExactly)
            if items:
                # Reset color of previously loaded item
                if self.currently_loaded_item:
                    self.currently_loaded_item.setForeground(Qt.white)
                # Set new loaded item and color it
                items[0].setForeground(Qt.red)
                self.currently_loaded_item = items[0]

        except Exception as e:
            self._update_status(f"Error loading profile '{profile_name}': {e}", is_error=True)

    def delete_profile(self):
        """Deletes the currently selected profile."""
        current_item = self.profile_listWidget.currentItem()
        if not current_item:
            self._update_status("Please select a profile to delete.", is_error=True)
            return

        profile_name = current_item.text()
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to delete the profile '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if manage_profile("delete", self.profile_dir, profile_name):
                self._update_status(f"Profile '{profile_name}' deleted.")
                self.populate_profiles()

    def rename_profile(self):
        """Renames the currently selected profile."""
        current_item = self.profile_listWidget.currentItem()
        if not current_item:
            self._update_status("Please select a profile to rename.", is_error=True)
            return

        old_name = current_item.text()
        new_name = self.profile_lineEdit.text().strip()

        if not new_name:
            self._update_status("Please enter a new name for the profile.", is_error=True)
            return

        if old_name == new_name:
            self._update_status("The new name is the same as the old name.", is_error=True)
            return

        if manage_profile("rename", self.profile_dir, old_name, new_name=new_name):
            self._update_status(f"Profile '{old_name}' renamed to '{new_name}'.")
            self.populate_profiles()
            # Find and select the renamed item
            items = self.profile_listWidget.findItems(new_name, Qt.MatchExactly)
            if items:
                self.profile_listWidget.setCurrentItem(items[0])