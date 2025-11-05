import os
import shutil

import Addresses
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QComboBox, QLineEdit, QLabel, QMessageBox, QHBoxLayout, QApplication, QInputDialog, QGroupBox, QFormLayout)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSettings
from .MainWindowTab import MainWindowTab
from .ConfigEditor import ConfigEditor


class SelectTibiaTab(QWidget):
    def __init__(self):
        super().__init__()
        self.main_window = None

        self.config_editor_window = None
        # Set window icon
        self.setWindowIcon(QIcon('Images/Icon.jpg'))
        self.setWindowTitle("IglaBot Select Client")
        self.setFixedWidth(350)

        # Layout
        self.layout = QVBoxLayout(self)

        # --- Client Selection Group ---
        selection_group = QGroupBox("Load Existing Client")
        selection_layout = QVBoxLayout()

        self.client_combobox = QComboBox(self)
        self.client_combobox.setToolTip("Select a client configuration to load.")
        self.populate_clients()
        selection_layout.addWidget(self.client_combobox)

        # Buttons for actions
        action_button_layout = QHBoxLayout()
        self.load_client_button = QPushButton(QIcon.fromTheme("document-open"), " Load", self)
        self.load_client_button.setStyleSheet("color: white; background-color: #e67e22; font-weight: bold;") # Orange
        self.load_client_button.setToolTip("Load the selected client configuration and start the bot.")
        self.edit_client_button = QPushButton(QIcon.fromTheme("document-edit"), " Edit", self)
        self.edit_client_button.setStyleSheet("background-color: #7f8c8d;") # Gray
        self.edit_client_button.setToolTip("Edit the memory addresses and settings for the selected client.")
        self.duplicate_client_button = QPushButton(QIcon.fromTheme("edit-copy"), " Duplicate", self)
        self.duplicate_client_button.setStyleSheet("background-color: #7f8c8d;") # Gray
        self.duplicate_client_button.setToolTip("Create a copy of the selected client configuration with a new name.")
        self.delete_client_button = QPushButton(QIcon.fromTheme("edit-delete"), " Delete", self)
        self.delete_client_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold;") # Red
        self.delete_client_button.setToolTip("Delete the selected client configuration file.")

        action_button_layout.addWidget(self.load_client_button)
        action_button_layout.addWidget(self.edit_client_button)
        action_button_layout.addWidget(self.duplicate_client_button)
        action_button_layout.addWidget(self.delete_client_button)
        selection_layout.addLayout(action_button_layout)
        selection_group.setLayout(selection_layout)
        self.layout.addWidget(selection_group)

        # --- Add New Client Group ---
        add_group = QGroupBox("Create New Client")
        add_layout = QFormLayout()

        self.new_client_name_edit = QLineEdit(self)
        self.new_client_name_edit.setPlaceholderText("Enter new client name (e.g., MyOTS)")
        self.new_client_name_edit.setToolTip("Enter a unique name for the new client configuration.")
        add_layout.addRow(QLabel("Name:"), self.new_client_name_edit)

        self.add_client_button = QPushButton(QIcon.fromTheme("document-new"), " Add New Client", self)
        self.add_client_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        self.add_client_button.setToolTip("Create a new client configuration file based on the default template.")
        add_layout.addRow(self.add_client_button)
        add_group.setLayout(add_layout)
        self.layout.addWidget(add_group)

        # Buttons Functions
        self.load_client_button.clicked.connect(self.load_client_button_clicked)
        self.edit_client_button.clicked.connect(self.edit_client_button_clicked)
        self.delete_client_button.clicked.connect(self.delete_client_button_clicked)
        self.duplicate_client_button.clicked.connect(self.duplicate_client_button_clicked)
        self.add_client_button.clicked.connect(self.add_new_client)

        # Center the window on the screen
        self.center()

    def populate_clients(self):
        self.client_combobox.clear()
        config_dir = "ClientConfigs"
        if not os.path.exists(config_dir):
            return
        for file in os.listdir(config_dir):
            if file.endswith(".py") and not file.startswith("__"):
                self.client_combobox.addItem(file)

    def load_client_button_clicked(self) -> None:
        selected_client = self.client_combobox.currentText()
        if not selected_client:
            QMessageBox.warning(self, "No Client Selected", "Please select a client from the list.")
            return
        try:
            Addresses.load_client(selected_client)
            self.close()

            settings = QSettings()

            self.main_window = MainWindowTab()

            # Initialize tabs now that addresses are loaded
            self.main_window.initTabs()

            # Restore splitter state after tabs are initialized
            healing_splitter_state = settings.value("healingAttackSplitterState")
            if healing_splitter_state and hasattr(self.main_window, 'healing_tab'):
                self.main_window.healing_tab.splitter.restoreState(healing_splitter_state)

            walker_splitter_state = settings.value("walkerSplitterState")
            if walker_splitter_state and hasattr(self.main_window, 'walker_tab'):
                self.main_window.walker_tab.splitter.restoreState(walker_splitter_state)

            # Show the window first, then restore geometry
            self.main_window.show()
            geometry = settings.value("mainWindowGeometry")
            if geometry:
                self.main_window.restoreGeometry(geometry)


            # Restore the last opened tab
            last_tab_index = settings.value("lastTabIndex", 0, type=int)
            self.main_window.tabs.setCurrentIndex(last_tab_index)

            # Dynamically add a closeEvent to the main window to save settings
            self.main_window.closeEvent = self.create_close_event(self.main_window)

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Client", f"Failed to load client configuration.\n\nError: {e}")

    def edit_client_button_clicked(self):
        selected_client = self.client_combobox.currentText()
        if not selected_client:
            QMessageBox.warning(self, "No Client Selected", "Please select a client from the list to edit.")
            return

        if self.config_editor_window is None or not self.config_editor_window.isVisible():
            self.config_editor_window = ConfigEditor(selected_client)
            self.config_editor_window.show()

    def delete_client_button_clicked(self):
        selected_client = self.client_combobox.currentText()
        if not selected_client:
            QMessageBox.warning(self, "No Client Selected", "Please select a client to delete.")
            return

        if selected_client == "IglaOTS.py":
            QMessageBox.warning(self, "Cannot Delete", "The default 'IglaOTS.py' template cannot be deleted.")
            return

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to delete '{selected_client}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            os.remove(os.path.join("ClientConfigs", selected_client))
            self.populate_clients()
            QMessageBox.information(self, "Deleted", f"Client '{selected_client}' has been deleted.")

    def duplicate_client_button_clicked(self):
        selected_client = self.client_combobox.currentText()
        if not selected_client:
            QMessageBox.warning(self, "No Client Selected", "Please select a client to duplicate.")
            return

        new_name, ok = QInputDialog.getText(self, 'Duplicate Client',
                                              f"Enter a new name for the copy of '{selected_client.replace('.py', '')}':")

        if ok and new_name:
            new_name = new_name.strip()
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "The new client name cannot be empty.")
                return

            if not self._is_valid_filename(new_name):
                QMessageBox.warning(self, "Invalid Name",
                                    f"The name '{new_name}' contains invalid characters.\n"
                                    "The following are not allowed: <>:\"/\\|?*")
                return

            source_path = os.path.join("ClientConfigs", selected_client)
            new_filename = f"{new_name}.py"
            dest_path = os.path.join("ClientConfigs", new_filename)

            if os.path.exists(dest_path):
                QMessageBox.warning(self, "Client Exists", f"A client configuration named '{new_name}' already exists.")
                return

            try:
                shutil.copy(source_path, dest_path)
                QMessageBox.information(self, "Success",
                                        f"Client '{selected_client.replace('.py', '')}' was successfully duplicated as '{new_name}'.")
                self.populate_clients()
                self.client_combobox.setCurrentText(new_filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to duplicate client.\n\nError: {e}")

    def _is_valid_filename(self, name: str) -> bool:
        """
        Checks if a string is a valid filename by checking for invalid characters.
        """
        invalid_chars = r'<>:"/\|?*'
        if any(char in name for char in invalid_chars):
            return False
        return True

    def add_new_client(self):
        new_name = self.new_client_name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a name for the new client.")
            return

        new_filename = f"{new_name}.py"
        if not self._is_valid_filename(new_name):
            QMessageBox.warning(self, "Invalid Name",
                                f"The name '{new_name}' contains invalid characters.\n"
                                "The following are not allowed: <>:\"/\\|?*")
            return
        new_filepath = os.path.join("ClientConfigs", new_filename)

        if os.path.exists(new_filepath):
            QMessageBox.warning(self, "Client Exists", f"A client configuration named '{new_name}' already exists.")
            return

        template_path = os.path.join("ClientConfigs", "IglaOTS.py")
        if not os.path.exists(template_path):
            QMessageBox.critical(self, "Template Missing",
                                 f"The template file '{template_path}' was not found.\n"
                                 "Cannot create a new client.")
            return

        shutil.copy(template_path, new_filepath)

        QMessageBox.information(self, "Success", f"New client '{new_name}' added. You can now edit the file\n{new_filepath}\nto set the correct addresses.")
        self.populate_clients()
        self.new_client_name_edit.clear()

    def create_close_event(self, window_instance):
        """
        A factory function to create a closeEvent handler for the main window.
        This allows us to save settings when the window is closed.
        """
        original_close_event = window_instance.closeEvent

        def closeEvent(event):
            settings = QSettings()
            # Save window geometry
            settings.setValue("mainWindowGeometry", window_instance.saveGeometry())
            # Save last opened tab
            settings.setValue("lastTabIndex", window_instance.tabs.currentIndex())

            # Save splitter states
            if hasattr(window_instance, 'healing_tab'):
                settings.setValue("healingAttackSplitterState", window_instance.healing_tab.splitter.saveState())
            if hasattr(window_instance, 'walker_tab'):
                settings.setValue("walkerSplitterState", window_instance.walker_tab.splitter.saveState())

            original_close_event(event)

        return closeEvent

    def center(self):
        """Centers the window on the screen."""
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
