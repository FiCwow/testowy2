import json
import os
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QLineEdit, QListWidget, QPushButton, QSplitter,
    QVBoxLayout, QHBoxLayout, QGroupBox, QListWidgetItem, QLabel, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QIcon
import Addresses
from Functions.GeneralFunctions import delete_item
from Functions.KeyCaptureThread import KeyCaptureThread
from General.CustomDelegates import RichTextDelegate
from General.BotLogger import bot_logger
from SmartHotkeys.ConditionalHotkeysThread import ConditionalHotkeysThread, SetCoordinateThread, SetColorThread, AreaPreviewWindow


class SmartHotkeysTab(QWidget):
    def __init__(self):
        super().__init__()

        # --- Thread Variables ---
        self.active_threads = {} # Dictionary to hold running threads for each item
        self.conditional_hotkeys_thread = None
        self.set_coord_thread = None
        self.set_color_thread = None
        self.currently_editing_item = None
        self.preview_window = None

        # --- Main Layout ---
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()

        # --- Status Label ---
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # --- UI Elements ---
        self.hotkey_list_widget = QListWidget()
        self.hotkey_list_widget.setItemDelegate(RichTextDelegate())
        self.hotkey_list_widget.setToolTip("List of configured conditional hotkeys. Double-click an item to edit it.")
        self.hotkey_list_widget.itemDoubleClicked.connect(self.edit_hotkey_action)

        self.hotkey_combobox = QComboBox()
        Addresses.populate_keys_combobox(self.hotkey_combobox)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., 'Haste Icon Check'")

        self.condition_combobox = QComboBox()
        self.condition_combobox.addItems(["Color is present", "Color is NOT present"])

        self.add_button = QPushButton(QIcon.fromTheme("list-add"), "Add")
        self.add_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        self.cancel_edit_button = QPushButton(QIcon.fromTheme("edit-undo"), "Cancel Edit")
        self.cancel_edit_button.setStyleSheet("background-color: #95a5a6;")
        self.edit_button = QPushButton("Edit")
        self.edit_button.setStyleSheet("background-color: #7f8c8d; font-weight: bold;")
        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.setStyleSheet("background-color: #7f8c8d; font-weight: bold;")
        self.show_frame_button = QPushButton("Show Frame")
        self.show_frame_button.setStyleSheet("background-color: #7f8c8d; font-weight: bold;")
        self.change_color_button = QPushButton("Change Color")
        self.change_color_button.setStyleSheet("background-color: #7f8c8d; font-weight: bold;")
        self.delete_button = QPushButton("X")
        self.delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        self.set_area_button = QPushButton(QIcon.fromTheme("zoom-fit-best"), "Set Area")
        self.set_area_button.setStyleSheet("background-color: #8e44ad;") # Purple
        self.set_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
        self.set_key_button.setStyleSheet("background-color: #8e44ad;") # Purple

        self.color_preview_label = QLabel()
        self.color_preview_label.setFixedSize(22, 22)
        self.color_preview_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.color_preview_label.setToolTip("Preview of the selected color.")

        # --- Setup UI ---
        controls_group = self.setup_controls()
        list_group = self.setup_list_view()
        profile_manager = self.setup_profile_manager()

        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(list_group)
        left_layout.addWidget(controls_group)
        left_layout.addWidget(self.status_label)

        splitter.addWidget(left_panel)
        splitter.addWidget(profile_manager)

    def setup_list_view(self) -> QGroupBox:
        groupbox = QGroupBox("⚙️ Configured Hotkeys")
        layout = QHBoxLayout(groupbox)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.duplicate_button)
        button_layout.addWidget(self.show_frame_button)
        button_layout.addWidget(self.change_color_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        layout.addWidget(self.hotkey_list_widget)
        layout.addLayout(button_layout)

        self.edit_button.clicked.connect(self.edit_hotkey_action)
        self.hotkey_list_widget.currentItemChanged.connect(self.edit_hotkey_action)
        self.show_frame_button.clicked.connect(self.toggle_selected_frame_preview)
        self.duplicate_button.clicked.connect(self.duplicate_selected_hotkey)
        self.hotkey_list_widget.itemChanged.connect(self.on_item_changed)
        self.change_color_button.clicked.connect(self.change_color_action)
        self.delete_button.clicked.connect(self.delete_selected_hotkey)

        return groupbox

    def setup_controls(self) -> QGroupBox:
        groupbox = QGroupBox("➕ Add / Edit Hotkey")
        layout = QFormLayout(groupbox)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.hotkey_combobox)
        key_layout.addWidget(self.set_key_button)

        set_area_layout = QHBoxLayout()
        set_area_layout.addWidget(self.set_area_button)
        set_area_layout.addWidget(self.color_preview_label)
        set_area_layout.addStretch()

        layout.addRow(QLabel("Rule Name:"), self.name_edit)
        layout.addRow(set_area_layout)
        layout.addRow(QLabel("Condition:"), self.condition_combobox)
        layout.addRow(QLabel("Press Key:"), key_layout)
        layout.addRow(self.add_button)
        layout.addRow(self.cancel_edit_button)

        self.cancel_edit_button.hide() # Initially hidden

        self.add_button.clicked.connect(self.add_or_update_hotkey)
        self.cancel_edit_button.clicked.connect(self.cancel_edit_mode)
        self.set_area_button.clicked.connect(self.start_set_coordinate_thread)
        self.set_key_button.clicked.connect(
            lambda: self.start_key_capture(self.set_key_button, self.hotkey_combobox)
        )

        return groupbox

    def setup_profile_manager(self) -> QWidget:
        # Using a generic QWidget as a container for the ProfileManagerWidget
        # This avoids circular dependencies if ProfileManagerWidget needs this class
        from Settings.ProfileManagerWidget import ProfileManagerWidget
        profile_manager = ProfileManagerWidget(
            profile_directory="Save/SmartHotkeys",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )
        profile_manager.set_status_label(self.status_label)

        return profile_manager


    def start_set_coordinate_thread(self):
        self.set_area_button.setText("Setting...")
        self.set_area_button.setEnabled(False)

        self.set_coord_thread = SetCoordinateThread()
        self.set_coord_thread.update_status.connect(self.update_status_label_from_thread)
        self.set_coord_thread.finished_setting.connect(self.on_coordinate_set)
        self.set_coord_thread.start()

    def update_status_label_from_thread(self, message):
        self.status_label.setStyleSheet("color: blue;")
        self.status_label.setText(message)

    def toggle_selected_frame_preview(self):
        """Toggles the visibility of the preview frame for the selected item."""
        selected_item = self.hotkey_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a hotkey from the list to see its frame.")
            return

        if self.preview_window and self.preview_window.isVisible():
            self.preview_window.hide()
            return

        data = selected_item.data(Qt.UserRole)
        if self.preview_window is None:
            self.preview_window = AreaPreviewWindow()

        self.preview_window.update_geometry_and_show(data['x1'], data['y1'], data['x2'], data['y2'])


    def change_color_action(self):
        """Starts the process to change only the color of a selected rule."""
        selected_item = self.hotkey_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a hotkey from the list to change its color.")
            return

        self.currently_editing_item = selected_item
        self.change_color_button.setText("...")
        self.change_color_button.setEnabled(False)

        self.set_color_thread = SetColorThread()
        self.set_color_thread.update_status.connect(self.update_status_label_from_thread)
        self.set_color_thread.color_captured.connect(self.on_color_changed)
        self.set_color_thread.start()

    def on_color_changed(self, color):
        """Updates the color of the rule being edited."""
        if self.currently_editing_item:
            self.current_color = color
            r, g, b = color
            self.color_preview_label.setStyleSheet(f"border: 1px solid gray; background-color: rgb({r},{g},{b});")
            self.update_existing_hotkey(self.currently_editing_item)
        self.change_color_button.setText("Change Color")
        self.change_color_button.setEnabled(True)

    def on_coordinate_set(self, x1, y1, x2, y2, color):
        self.set_area_button.setText("Set Area")
        self.set_area_button.setEnabled(True)
        self.current_area = (x1, y1, x2, y2)
        self.current_color = color
        r, g, b = color
        self.color_preview_label.setStyleSheet(f"border: 1px solid gray; background-color: rgb({r},{g},{b});")
        self.status_label.setStyleSheet("color: green;")
        self.status_label.setText(f"Area set from ({x1},{y1}) to ({x2},{y2}) with color {color}.")

    def update_existing_hotkey(self, item_to_update):
        """Helper function to update an existing item with current UI data."""
        old_data = item_to_update.data(Qt.UserRole)

        # Use existing area if not changed
        x1, y1, x2, y2 = self.current_area if hasattr(self, 'current_area') else (old_data['x1'], old_data['y1'], old_data['x2'], old_data['y2'])
        # Use existing color if not changed
        r, g, b = self.current_color if hasattr(self, 'current_color') else (old_data['r'], old_data['g'], old_data['b'])
        
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a name for the rule.")
            return

        hotkey = self.hotkey_combobox.currentText()
        condition = self.condition_combobox.currentText()

        hotkey_data = {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "r": r, "g": g, "b": b,
            "enabled": True, # Enabled by default
            "name": name,
            "hotkey": hotkey,
            "condition": condition
        }

        self.update_item_display(item_to_update, hotkey_data)
        item_to_update.setFlags(item_to_update.flags() | Qt.ItemIsUserCheckable)
        item_to_update.setCheckState(Qt.Checked)
        item_to_update.setData(Qt.UserRole, hotkey_data)

        # Reset state
        if hasattr(self, 'current_area'): del self.current_area
        if hasattr(self, 'current_color'): del self.current_color
        self.currently_editing_item = None
        self.add_button.setText("Add")
        self.color_preview_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.name_edit.clear()
        self.status_label.setText("Hotkey updated successfully.")

    def add_or_update_hotkey(self):
        if self.currently_editing_item:
            self.update_existing_hotkey(self.currently_editing_item)
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a name for the rule.")
            return

        if not hasattr(self, 'current_area') or not hasattr(self, 'current_color'):
            QMessageBox.warning(self, "No Area Set", "Please use the 'Set Area' button to choose a pixel on the screen first.")
            return

        hotkey = self.hotkey_combobox.currentText()
        x1, y1, x2, y2 = self.current_area
        r, g, b = self.current_color
        condition = self.condition_combobox.currentText()

        hotkey_data = {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "r": r, "g": g, "b": b,
            "enabled": True, # New rules are enabled by default
            "name": name,
            "hotkey": hotkey,
            "condition": condition
        }

        item = QListWidgetItem()
        self.update_item_display(item, hotkey_data)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole, hotkey_data)
        self.hotkey_list_widget.addItem(item)

        # Reset for next entry
        del self.current_area
        del self.current_color
        self.color_preview_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.name_edit.clear()
        self.status_label.setText("Hotkey added successfully.")

    def edit_hotkey_action(self):
        selected_item = self.hotkey_list_widget.currentItem()
        if not selected_item:
            self.cancel_edit_mode()
            return
        
        self.currently_editing_item = selected_item
        data = selected_item.data(Qt.UserRole)

        r, g, b = data['r'], data['g'], data['b']
        self.color_preview_label.setStyleSheet(f"border: 1px solid gray; background-color: rgb({r},{g},{b});")
        self.name_edit.setText(data.get("name", ""))

        self.hotkey_combobox.setCurrentText(data['hotkey'])
        self.condition_combobox.setCurrentText(data.get('condition', 'Color is present'))
        self.status_label.setStyleSheet("color: blue;")
        self.status_label.setText(f"Editing rule. Change settings and click 'Add' to save.")
        self.add_button.setText("Save Changes")
        self.cancel_edit_button.show() # type: ignore

        # Show preview window for the selected area
        if self.preview_window is None:
            self.preview_window = AreaPreviewWindow()
        self.preview_window.update_geometry_and_show(data['x1'], data['y1'], data['x2'], data['y2'])

    def cancel_edit_mode(self):
        """Clears the form and resets the UI to 'add' mode."""
        self.currently_editing_item = None
        self.hotkey_list_widget.clearSelection()
        self.name_edit.clear()
        self.hotkey_combobox.setCurrentIndex(0)
        self.condition_combobox.setCurrentIndex(0)
        self.color_preview_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.add_button.setText("Add")
        self.cancel_edit_button.hide() # type: ignore
        self.status_label.setText("")
        # Hide preview window
        if self.preview_window:
            self.preview_window.hide()


    def duplicate_selected_hotkey(self):
        """Creates a copy of the selected hotkey rule."""
        selected_item = self.hotkey_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a hotkey from the list to duplicate.")
            return

        original_data = selected_item.data(Qt.UserRole).copy()
        original_name = original_data.get("name", "Unnamed Rule")
        original_data["name"] = f"{original_name} (copy)"

        new_item = QListWidgetItem()
        self.update_item_display(new_item, original_data)
        new_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        new_item.setCheckState(selected_item.checkState())
        new_item.setData(Qt.UserRole, original_data.copy()) # Create a shallow copy of the data

        # If the original item was checked, start a thread for the new one too
        if new_item.checkState() == Qt.Checked:
            self.on_item_changed(new_item)

        self.hotkey_list_widget.addItem(new_item)
        self.status_label.setText("Hotkey duplicated.")

    def delete_selected_hotkey(self):
        current_item = self.hotkey_list_widget.currentItem()
        if current_item:
            delete_item(self.hotkey_list_widget, current_item)
            # Also stop and remove its thread if it was running
            item_id = id(current_item)
            if item_id in self.active_threads:
                thread = self.active_threads.pop(item_id)
                thread.stop()
                thread.wait()
            self.status_label.setText("Hotkey deleted.")

    def on_item_changed(self, item: QListWidgetItem):
        """Called when an item's state (like checkbox) changes."""
        data = item.data(Qt.UserRole)
        if not data:
            return

        data['enabled'] = item.checkState() == Qt.Checked
        item.setData(Qt.UserRole, data)

        item_id = id(item)

        if item.checkState() == Qt.Checked:
            # Start a thread for this specific rule if it's not already running
            if item_id not in self.active_threads:
                thread = ConditionalHotkeysThread([data]) # Pass rule as a list
                thread.status_update.connect(lambda status, item=item: self.update_item_status_text(item, status))
                self.active_threads[item_id] = thread
                thread.start()
        else:
            # Stop the thread for this specific rule if it is running
            if item_id in self.active_threads:
                thread = self.active_threads.pop(item_id)
                thread.stop()
                thread.wait()
                self.update_item_status_text(item, None) # Clear status

    def get_data_for_saving(self) -> dict:
        """Provides the current hotkey rules to be saved."""
        rules = []
        for i in range(self.hotkey_list_widget.count()):
            item = self.hotkey_list_widget.item(i)
            if item:
                rule_data = item.data(Qt.UserRole)
                rule_data['enabled'] = item.checkState() == Qt.Checked
                rules.append(rule_data)
        return {"rules": rules}

    def load_data_from_profile(self, loaded_data: dict):
        """Applies the loaded hotkey rules."""
        self.hotkey_list_widget.clear()
        for rule in loaded_data.get("rules", []):
            name = rule.get("name", "Unnamed Rule")
            item = QListWidgetItem()
            self.update_item_display(item, rule)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked if rule.get("enabled", True) else Qt.Unchecked)
            item.setData(Qt.UserRole, rule)
            self.hotkey_list_widget.addItem(item)
        bot_logger.info("Loaded a profile in 'Smart Hotkeys' tab.")

    def update_item_display(self, item: QListWidgetItem, name: str, color: tuple):
        """Sets the item's text and icon based on the rule's name and color."""
    def update_item_display(self, item: QListWidgetItem, data: dict):
        """Sets the item's text and icon based on the rule's data."""
        name = data.get("name", "Unnamed Rule")
        color = (data.get('r', 0), data.get('g', 0), data.get('b', 0))
        condition_text = "is" if data.get('condition') == "Color is present" else "is NOT"
        hotkey = data.get('hotkey', 'F1')
        details = f"If color {condition_text} present, press '{hotkey}'"

        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(*color))
        item.setIcon(QIcon(pixmap))
        item.setText(f"<b style='color: #ffffff; font-size: 10pt;'>{name}</b><br><small style='color: #bbbbbb;'>{details}</small>")

    def update_item_status_text(self, item: QListWidgetItem, status: str | None):
        """Updates the item's text to include the live detection status."""
        # Check if the item still exists in the list widget before updating.
        # This prevents a crash if the item is deleted while its thread is still sending a final signal.
        if self.hotkey_list_widget.row(item) == -1:
            return

        data = item.data(Qt.UserRole)
        if data:
            name = data.get("name", "Unnamed Rule")
            if status:
                item.setText(f"{name} - {status}")
            else:
                item.setText(name) # Revert to just the name

    def stop_all_threads(self):
        """Stops all running hotkey threads."""
        for thread in self.active_threads.values():
            thread.stop()
            thread.wait()
        self.active_threads.clear()
        # Ensure preview window is also closed
        if self.preview_window:
            self.preview_window.close()
        if self.set_coord_thread:
            self.set_coord_thread.stop()
            self.set_coord_thread.wait()
        if self.set_color_thread:
            self.set_color_thread.stop()
            self.set_color_thread.wait()


    def start_key_capture(self, button: QPushButton, combobox: QComboBox):
        """Starts a thread to capture a single key press."""
        self.key_capture_thread = KeyCaptureThread(button, combobox)
        self.key_capture_thread.key_captured.connect(
            lambda key_name: self.set_combobox_key(combobox, key_name)
        )
        self.key_capture_thread.start()

    def set_combobox_key(self, combobox: QComboBox, key_name: str):
        """Sets the QComboBox to the captured key if it exists in the list."""
        index = combobox.findText(key_name, Qt.MatchFixedString)
        if index >= 0:
            combobox.setCurrentIndex(index)

    def update_checkbox_style(self, state):
        """Changes the color of the checkbox text to green when checked."""
        checkbox = self.sender()
        if state == Qt.Checked:
            checkbox.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            checkbox.setStyleSheet("")