from PyQt5.QtCore import Qt
import os
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QComboBox, QLineEdit, QListWidget, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidgetItem, QLabel, QFormLayout, QMessageBox
)
from PyQt5.QtGui import QIcon
import Addresses
from Functions.GeneralFunctions import manage_profile, delete_item
from Settings.ProfileManagerWidget import ProfileManagerWidget
from Functions.KeyCaptureThread import KeyCaptureThread
from General.CustomDelegates import RichTextDelegate
from Training.TrainingThread import TrainingThread, ClickThread, SetThread, FishingThread, AntiIdleThread


class TrainingTab(QWidget):
    def __init__(self):
        super().__init__()

        # Thread Variables
        self.click_thread = None
        self.training_thread = None
        self.set_thread = None
        self.fishing_thread = None
        self.anti_idle_thread = None
        self.active_training_threads = {}
        self.currently_editing_item = None

        # --- Status label at the bottom (for messages, instructions, and showing coordinates)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # Check Boxes
        self.start_click_checkbox = QCheckBox("Start", self)
        self.start_click_checkbox.setToolTip("Enable/disable the auto-clicker.")
        self.start_fishing_checkbox = QCheckBox("Start", self)
        self.start_fishing_checkbox.setToolTip("Enable/disable auto-fishing.")
        self.anti_idle_checkbox = QCheckBox("Enable Anti-Idle", self)
        self.anti_idle_checkbox.setToolTip("Prevents being kicked for inactivity by making small, random movements.")

        # Combo Boxes
        self.spell_hotkey_combobox = QComboBox(self)
        self.key_list_combobox = QComboBox(self)

        self.mana_condition_combobox = QComboBox()
        self.mana_condition_combobox.addItems(["Above >", "Below <", "Between"])
        self.hp_condition_combobox = QComboBox()
        self.hp_condition_combobox.addItems(["Any", "Above >", "Below <", "Between"])
        self.monster_condition_combobox = QComboBox()
        self.monster_condition_combobox.addItems(["Any", "Monsters on screen", "No monsters on screen"])

        # Line Edits
        self.mana_val1_edit = QLineEdit(self)
        self.mana_val2_edit = QLineEdit(self)
        self.hp_val1_edit = QLineEdit(self)
        self.hp_val2_edit = QLineEdit(self)
        self.timer_line_edit = QLineEdit(self)
        self.timer_line_edit.setToolTip("Interval in seconds for the auto-clicker.")

        # List Widgets
        self.burn_mana_list_widget = QListWidget(self)
        self.burn_mana_list_widget.setItemDelegate(RichTextDelegate())

        # Layout
        main_layout = QVBoxLayout(self)
        columns_layout = QHBoxLayout()

        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        # --- Left Column ---
        left_column.addWidget(self.setup_mana_burner())
        left_column.addWidget(self.setup_click_key())
        left_column.addStretch()

        # --- Right Column ---
        right_column.addWidget(self.setup_fishing())
        right_column.addWidget(self.setup_anti_idle())
        right_column.addWidget(self.setup_profile_list())
        right_column.addStretch()

        columns_layout.addLayout(left_column)
        columns_layout.addLayout(right_column)

        main_layout.addLayout(columns_layout)
        main_layout.addWidget(self.status_label)

        # Connect checkboxes to style updater
        self.start_click_checkbox.stateChanged.connect(self.update_checkbox_style)
        self.start_fishing_checkbox.stateChanged.connect(self.update_checkbox_style)
        self.anti_idle_checkbox.stateChanged.connect(self.update_checkbox_style)
        self.anti_idle_checkbox.stateChanged.connect(self.start_anti_idle_thread)

    def setup_mana_burner(self) -> QGroupBox:
        groupbox = QGroupBox("🔥 Spell Trainer")
        # Buttons
        self.add_hotkey_button = QPushButton(QIcon.fromTheme("list-add"), "Add", self) # type: ignore
        self.add_hotkey_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        self.edit_hotkey_button = QPushButton(QIcon.fromTheme("document-edit"), "Edit", self) # type: ignore
        self.edit_hotkey_button.setStyleSheet("background-color: #7f8c8d;")
        self.delete_hotkey_button = QPushButton(QIcon.fromTheme("edit-delete"), "Delete", self) # type: ignore
        self.delete_hotkey_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold;")
        self.cancel_edit_button = QPushButton(QIcon.fromTheme("edit-undo"), "Cancel", self) # type: ignore
        self.cancel_edit_button.setStyleSheet("background-color: #95a5a6;")
        
        # Move/Delete buttons
        move_buttons_layout = QVBoxLayout()
        up_button = QPushButton("↑")
        up_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        up_button.setToolTip("Move selected hotkey up.")
        down_button = QPushButton("↓")
        down_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        down_button.setToolTip("Move selected hotkey down.")
        delete_button = QPushButton("X")
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        delete_button.setToolTip("Delete the selected hotkey.")
        move_buttons_layout.addWidget(up_button)
        move_buttons_layout.addWidget(down_button)
        move_buttons_layout.addWidget(delete_button)

        # Button functions
        self.add_hotkey_button.clicked.connect(self.add_or_update_hotkey)
        self.edit_hotkey_button.clicked.connect(self.edit_hotkey_action)
        self.delete_hotkey_button.clicked.connect(lambda: self.delete_selected_item(self.burn_mana_list_widget))
        self.cancel_edit_button.clicked.connect(self.cancel_edit_action)
        self.cancel_edit_button.hide()

        # Connect move/delete buttons
        up_button.clicked.connect(lambda: self.move_list_item(self.burn_mana_list_widget, "up"))
        down_button.clicked.connect(lambda: self.move_list_item(self.burn_mana_list_widget, "down"))
        delete_button.clicked.connect(lambda: self.delete_selected_item(self.burn_mana_list_widget)) # This one is just an icon
        self.burn_mana_list_widget.itemDoubleClicked.connect(self.edit_hotkey_action)
        self.burn_mana_list_widget.itemChanged.connect(self.on_spell_trainer_item_changed)
        
        # Combo Boxes
        Addresses.populate_keys_combobox(self.spell_hotkey_combobox)

        # Use QGridLayout for a more compact and aligned form
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        list_layout = QHBoxLayout()
        buttons_layout = QHBoxLayout()

        # --- Condition Layouts ---
        grid_layout.addWidget(QLabel("If Mana:"), 0, 0)
        grid_layout.addWidget(self.mana_condition_combobox, 0, 1)
        grid_layout.addWidget(self.mana_val1_edit, 0, 2)
        grid_layout.addWidget(self.mana_val2_edit, 0, 3)
        self.mana_val2_edit.hide() # Initially hidden

        grid_layout.addWidget(QLabel("and HP:"), 1, 0)
        grid_layout.addWidget(self.hp_condition_combobox, 1, 1)
        grid_layout.addWidget(self.hp_val1_edit, 1, 2)
        grid_layout.addWidget(self.hp_val2_edit, 1, 3)
        self.hp_val1_edit.hide()
        self.hp_val2_edit.hide()

        self.mana_condition_combobox.currentTextChanged.connect(lambda text: self.mana_val2_edit.setVisible(text == "Between"))
        self.hp_condition_combobox.currentTextChanged.connect(self.toggle_hp_fields)

        grid_layout.addWidget(QLabel("and Target:"), 2, 0)
        grid_layout.addWidget(self.monster_condition_combobox, 2, 1, 1, 3)
        grid_layout.addWidget(QLabel("Press:"), 3, 0)
        grid_layout.addWidget(self.spell_hotkey_combobox, 3, 1, 1, 2)
        set_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set") # type: ignore
        set_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_key_button.setToolTip("Click and then press the desired key to set it.")
        grid_layout.addWidget(set_key_button, 3, 3)
        set_key_button.clicked.connect(lambda: self.start_key_capture(set_key_button, self.spell_hotkey_combobox))

        list_layout.addWidget(self.burn_mana_list_widget)
        list_layout.addLayout(move_buttons_layout)

        buttons_layout.addWidget(self.add_hotkey_button)
        buttons_layout.addWidget(self.edit_hotkey_button)
        buttons_layout.addWidget(self.delete_hotkey_button)
        buttons_layout.addWidget(self.cancel_edit_button)

        # Add Layouts
        groupbox_layout = QVBoxLayout(groupbox)
        groupbox_layout.addLayout(grid_layout)
        groupbox_layout.addLayout(buttons_layout)
        groupbox_layout.addLayout(list_layout)
        
        return groupbox

    def toggle_hp_fields(self, text):
        is_between = text == "Between"
        is_any = text == "Any"
        self.hp_val1_edit.setVisible(not is_any)
        self.hp_val2_edit.setVisible(is_between)

    def setup_profile_list(self) -> QGroupBox:
        profile_manager = ProfileManagerWidget(
            profile_directory="Save/Training",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )
        profile_manager.set_status_label(self.status_label)

        return profile_manager

    def setup_click_key(self) -> QGroupBox:
        groupbox = QGroupBox("🖱️ Auto Clicker")
        groupbox_layout = QVBoxLayout(groupbox)
        Addresses.populate_keys_combobox(self.key_list_combobox)
        self.start_click_checkbox.stateChanged.connect(self.start_click_thread)

        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(5, 5, 5, 5)
        key_layout = QHBoxLayout()
        set_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set") # type: ignore
        set_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_key_button.setToolTip("Click and then press the desired key to set it.")
        key_layout.addWidget(self.key_list_combobox)
        key_layout.addWidget(set_key_button)

        form_layout.addRow(QLabel("Time (s):"), self.timer_line_edit)
        form_layout.addRow(QLabel("Key:"), key_layout)
        set_key_button.clicked.connect(lambda: self.start_key_capture(set_key_button, self.key_list_combobox))

        groupbox_layout.addLayout(form_layout)
        groupbox_layout.addWidget(self.start_click_checkbox)
        return groupbox

    def setup_fishing(self) -> QGroupBox:
        groupbox = QGroupBox("🎣 Auto Fishing")
        groupbox_layout = QVBoxLayout(groupbox)

        fishing_button = QPushButton("🎣 Fishing Rod", self)
        fishing_button.setStyleSheet("background-color: #8e44ad;") # Purple
        water_button = QPushButton("💧 Water", self)
        water_button.setStyleSheet("background-color: #8e44ad;") # Purple
        bait_button = QPushButton("🐛 Bait", self)
        bait_button.setStyleSheet("background-color: #8e44ad;") # Purple
        food_button = QPushButton("🍖 Food", self)
        food_button.setStyleSheet("background-color: #8e44ad;") # Purple

        self.start_fishing_checkbox.stateChanged.connect(self.start_fishing_thread)

        fishing_button.clicked.connect(lambda: self.startSet_thread(0))
        water_button.clicked.connect(lambda: self.startSet_thread(1))
        bait_button.clicked.connect(lambda: self.startSet_thread(2))
        food_button.clicked.connect(lambda: self.startSet_thread(3))

        button_layout = QHBoxLayout()
        button_layout.addWidget(fishing_button)
        button_layout.addWidget(water_button)
        button_layout.addWidget(bait_button)
        button_layout.addWidget(food_button)
        button_layout.addWidget(self.start_fishing_checkbox)
        groupbox_layout.addLayout(button_layout)
        return groupbox

    def setup_anti_idle(self) -> QGroupBox:
        groupbox = QGroupBox("🚶‍♂️ Anti-Idle")
        layout = QVBoxLayout(groupbox)
        layout.addWidget(self.anti_idle_checkbox)
        return groupbox

    def add_or_update_hotkey(self) -> None:
        """Handles both adding a new hotkey and updating an existing one."""
        if self.currently_editing_item:
            self._update_hotkey()
        else:
            self._add_hotkey()

    def _add_hotkey(self) -> None:
        if not self.mana_val1_edit.text().strip() and self.mana_condition_combobox.currentText() != "Any":
            self.status_label.setText("Mana value cannot be empty.")
            return

        hotkey_data = {
            "hotkey": self.spell_hotkey_combobox.currentText(),
            "mana_cond": self.mana_condition_combobox.currentText(),
            "mana_val1": int(self.mana_val1_edit.text() or "0"),
            "mana_val2": int(self.mana_val2_edit.text() or "0"),
            "hp_cond": self.hp_condition_combobox.currentText(),
            "hp_val1": int(self.hp_val1_edit.text() or "0"),
            "hp_val2": int(self.hp_val2_edit.text() or "0"),
            "monster_cond": self.monster_condition_combobox.currentText(),
            "enabled": True # New rules are enabled by default
        }

        display_text = self.format_rule_text(hotkey_data)
        hotkey = QListWidgetItem(display_text)
        hotkey.setFlags(hotkey.flags() | Qt.ItemIsUserCheckable)
        hotkey.setCheckState(Qt.Checked)
        hotkey.setData(Qt.UserRole, hotkey_data)
        self.burn_mana_list_widget.addItem(hotkey)
        self.clear_spell_trainer_form()
        self.status_label.setText(f"Rule for '{hotkey_data['hotkey']}' added.")

    def format_rule_text(self, data: dict) -> str:
        """Creates a readable string representation of a rule."""
        hotkey = data.get('hotkey', 'F1')
        parts = []
        # Mana
        if data['mana_cond'] == "Between":
            parts.append(f"Mana is {data['mana_val1']}-{data['mana_val2']}")
        else:
            parts.append(f"Mana {data['mana_cond'].lower()} {data['mana_val1']}")
        # HP
        if data['hp_cond'] != "Any":
            if data['hp_cond'] == "Between":
                parts.append(f"HP is {data['hp_val1']}-{data['hp_val2']}")
            else:
                parts.append(f"HP {data['hp_cond'].lower()} {data['hp_val1']}")
        # Monsters
        if data['monster_cond'] != "Any":
            parts.append(data['monster_cond'])
        
        rule_text = "If " + ' & '.join(parts)
        return f"<b style='color: #ffffff; font-size: 10pt;'>Press '{hotkey}'</b><br><small style='color: #bbbbbb;'>{rule_text}</small>"

    def _update_hotkey(self) -> None:
        """Saves the changes to the item being edited."""
        if not self.currently_editing_item:
            return

        if not self.mana_val1_edit.text().strip():
            self.status_label.setText("Mana value cannot be empty.")
            return

        new_data = {
            "hotkey": self.spell_hotkey_combobox.currentText(),
            "mana_cond": self.mana_condition_combobox.currentText(),
            "mana_val1": int(self.mana_val1_edit.text() or "0"),
            "mana_val2": int(self.mana_val2_edit.text() or "0"),
            "hp_cond": self.hp_condition_combobox.currentText(),
            "hp_val1": int(self.hp_val1_edit.text() or "0"),
            "hp_val2": int(self.hp_val2_edit.text() or "0"),
            "monster_cond": self.monster_condition_combobox.currentText(),
            "enabled": self.currently_editing_item.checkState() == Qt.Checked
        }

        display_text = self.format_rule_text(new_data)
        self.currently_editing_item.setText(display_text)
        self.currently_editing_item.setData(Qt.UserRole, new_data)

        self.cancel_edit_action()
        self.status_label.setText(f"Rule for '{new_data['hotkey']}' updated.")

    def edit_hotkey_action(self) -> None:
        """Populates the input fields with data from the selected item for editing."""
        selected_item = self.burn_mana_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a hotkey from the list to edit.")
            return

        self.currently_editing_item = selected_item
        data = selected_item.data(Qt.UserRole)

        # Populate fields
        self.spell_hotkey_combobox.setCurrentText(data.get("hotkey", "F1"))
        self.mana_condition_combobox.setCurrentText(data.get("mana_cond", "Above >"))
        self.mana_val1_edit.setText(str(data.get("mana_val1", "")))
        self.mana_val2_edit.setText(str(data.get("mana_val2", "")))
        self.hp_condition_combobox.setCurrentText(data.get("hp_cond", "Any"))
        self.hp_val1_edit.setText(str(data.get("hp_val1", "")))
        self.hp_val2_edit.setText(str(data.get("hp_val2", "")))
        self.monster_condition_combobox.setCurrentText(data.get("monster_cond", "Any"))

        # Change button text and show cancel button
        self.add_hotkey_button.setText("Save")
        self.cancel_edit_button.show()
        self.status_label.setText(f"Editing rule...")

    def cancel_edit_action(self) -> None:
        """Resets the UI from 'edit mode' back to 'add mode'."""
        self.currently_editing_item = None
        self.add_hotkey_button.setText("Add")
        self.cancel_edit_button.hide()
        self.clear_spell_trainer_form()
        self.status_label.setText("")

    def clear_spell_trainer_form(self):
        """Clears all input fields in the spell trainer form."""
        for editor in [self.mana_val1_edit, self.mana_val2_edit, self.hp_val1_edit, self.hp_val2_edit]:
            editor.clear()

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

    def move_list_item(self, list_widget: QListWidget, direction: str):
        """Moves the selected item in the QListWidget up or down."""
        current_item = list_widget.currentItem()
        if not current_item:
            return

        current_row = list_widget.row(current_item)

        if direction == "up" and current_row > 0:
            list_widget.takeItem(current_row)
            list_widget.insertItem(current_row - 1, current_item)
            list_widget.setCurrentRow(current_row - 1)
        elif direction == "down" and current_row < list_widget.count() - 1:
            list_widget.takeItem(current_row)
            list_widget.insertItem(current_row + 1, current_item)
            list_widget.setCurrentRow(current_row + 1)

    def delete_selected_item(self, list_widget: QListWidget):
        """Deletes the currently selected item from the given list widget."""
        current_item = list_widget.currentItem()
        if current_item:
            from Functions.GeneralFunctions import delete_item
            delete_item(list_widget, current_item)

        # If the deleted item was a spell trainer rule, stop its thread
        if list_widget == self.burn_mana_list_widget:
            item_id = id(current_item)
            if item_id in self.active_training_threads:
                thread = self.active_training_threads.pop(item_id)
                thread.stop()
                thread.wait()

    def get_data_for_saving(self):
        """Provides the current training rules to be saved."""
        burn_mana_list = []
        for i in range(self.burn_mana_list_widget.count()):
            item = self.burn_mana_list_widget.item(i)
            if item and item.data(Qt.UserRole):
                rule_data = item.data(Qt.UserRole)
                rule_data['enabled'] = item.checkState() == Qt.Checked
                burn_mana_list.append(rule_data)
        return {"burn_mana": burn_mana_list}

    def load_data_from_profile(self, loaded_data: dict):
        """Applies the loaded training rules."""
        try:
            self.burn_mana_list_widget.clear()
            for hotkey_data in loaded_data.get("burn_mana", []):
                display_text = self.format_rule_text(hotkey_data)
                hotkey = QListWidgetItem(display_text)
                hotkey.setFlags(hotkey.flags() | Qt.ItemIsUserCheckable)
                hotkey.setCheckState(Qt.Checked if hotkey_data.get("enabled", True) else Qt.Unchecked)
                hotkey.setData(Qt.UserRole, hotkey_data)
                self.burn_mana_list_widget.addItem(hotkey)
        except Exception as e:
            self.status_label.setText(f"Error loading profile: {e}")

    def start_click_thread(self, state) -> None:
        if state == Qt.Checked:
            if self.click_thread is None:
                self.click_thread = ClickThread(int(self.timer_line_edit.text()), self.key_list_combobox.currentText())
                self.click_thread.start()
        else:
            if self.click_thread:
                self.click_thread.stop()
                self.click_thread = None

    def on_spell_trainer_item_changed(self, item: QListWidgetItem):
        """Called when a spell trainer rule's checkbox state changes."""
        data = item.data(Qt.UserRole)
        if not data:
            return

        data['enabled'] = item.checkState() == Qt.Checked
        item.setData(Qt.UserRole, data)

        item_id = id(item)

        if item.checkState() == Qt.Checked:
            # Start a thread for this specific rule if it's not already running
            if item_id not in self.active_training_threads:
                thread = TrainingThread([data]) # Pass rule as a list
                self.active_training_threads[item_id] = thread
                thread.start()
        else:
            # Stop the thread for this specific rule if it is running
            if item_id in self.active_training_threads:
                thread = self.active_training_threads.pop(item_id)
                thread.stop()
                thread.wait()

    def start_fishing_thread(self, state) -> None:
        if state == Qt.Checked:
            if self.fishing_thread is None:
                self.fishing_thread = FishingThread()
                self.fishing_thread.update_status.connect(self.update_fishing_status)
                self.fishing_thread.start()
        else:
            if self.fishing_thread:
                self.fishing_thread.stop()
                self.fishing_thread = None

    def start_anti_idle_thread(self, state):
        if state == Qt.Checked:
            if self.anti_idle_thread is None:
                self.anti_idle_thread = AntiIdleThread()
                self.anti_idle_thread.start()
        else:
            if self.anti_idle_thread:
                self.anti_idle_thread.stop()
                self.anti_idle_thread = None

    def stop_all_threads(self):
        """Stops all running threads in this tab."""
        for thread in self.active_training_threads.values():
            thread.stop()
            thread.wait()
        self.active_training_threads.clear()
        if self.click_thread:
            self.click_thread.stop()
            self.click_thread.wait()
        if self.set_thread:
            self.set_thread.stop()
            self.set_thread.wait()
        if self.fishing_thread:
            self.fishing_thread.stop()
            self.fishing_thread.wait()
        if self.anti_idle_thread:
            self.anti_idle_thread.stop()
            self.anti_idle_thread.wait()

    def startSet_thread(self, index) -> None:
        # Stop any previous instance of the thread
        if self.set_thread and self.set_thread.isRunning():
            self.set_thread.stop()

        self.set_thread = SetThread(index)
        self.set_thread.update_status.connect(self.update_status_label)
        self.set_thread.finished_setting.connect(self.set_fishing_coordinates)
        self.set_thread.start()

    def update_fishing_status(self, message: str):
        self.status_label.setStyleSheet("color: blue; font-weight: normal;")
        self.status_label.setText(message)

    def update_status_label(self, message: str, color: str):
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.status_label.setText(message)

    def set_fishing_coordinates(self, index: int, x: int, y: int):
        Addresses.fishing_x[index], Addresses.fishing_y[index] = x, y
        self.update_status_label(f"Coordinates set at X={x}, Y={y}", "green")

    def update_checkbox_style(self, state):
        """Changes the color of the checkbox text to green when checked."""
        checkbox = self.sender()
        if state == Qt.Checked:
            checkbox.setStyleSheet("color: #4CAF50; font-weight: bold;")  # Green color
        else:
            checkbox.setStyleSheet("color: #aaaaaa; font-weight: normal;") # Dimmed color for unchecked
