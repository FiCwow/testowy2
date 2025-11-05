import os
import json
from Functions.GeneralFunctions import delete_item
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QComboBox, QLineEdit, QListWidget, QGridLayout, QFormLayout, QMessageBox, QTextEdit,
    QGroupBox, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QListWidgetItem
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import Addresses
from Functions.KeyCaptureThread import KeyCaptureThread
from Settings.ProfileManagerWidget import ProfileManagerWidget
from Target.TargetLootThread import TargetThread
from General.CustomDelegates import RichTextDelegate
from Target.BattleListThread import BattleListThread


class TargetLootTab(QWidget):
    def __init__(self):
        super().__init__()

        # Thread Variables
        self.target_thread = None
        self.currently_editing_target_item = None
        self.battle_list_thread = None

        # --- Status "bar" label at the bottom
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # Check Boxes
        self.startTarget_checkBox = QCheckBox("Targeting", self)
        self.startTarget_checkBox.setToolTip("Enable/disable auto-targeting and attacking monsters.")
        self.startTarget_checkBox.stateChanged.connect(self.start_target_thread)

        # Combo Boxes
        self.attackDist_comboBox = QComboBox(self)
        self.attackDist_comboBox.addItems(["All", "1", "2", "3", "4", "5", "6", "7"])
        self.attackDist_comboBox.setToolTip("Set the maximum distance to engage a target.")
        self.stance_comboBox = QComboBox(self)
        self.stance_comboBox.addItems(["Do Nothing", "Chase", "Diagonal", "Chase-Diagonal"])
        self.stance_comboBox.setToolTip("Define how the bot should position itself relative to the target.")
        self.attackKey_comboBox = QComboBox(self)
        Addresses.populate_keys_combobox(self.attackKey_comboBox)
        self.attackKey_comboBox.setToolTip("The key used to attack the selected target.")

        # Line Edits
        self.targetName_lineEdit = QLineEdit(self)

        # List Widgets
        self.targetList_listWidget = QListWidget(self)
        self.targetList_listWidget.setItemDelegate(RichTextDelegate())
        self.targetList_listWidget.setToolTip("List of monsters to attack. Double-click to edit.")

        # Main Layout
        self.main_layout = QHBoxLayout(self)
        self.setLayout(self.main_layout)

        # Initialize UI components
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(self.targetList())
        left_layout.addWidget(self.status_label)

        profile_manager = ProfileManagerWidget(
            profile_directory="Save/Targeting",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )

        self.main_layout.addWidget(left_panel)
        self.main_layout.addWidget(profile_manager)

        # Start the battle list thread
        self.battle_list_thread = BattleListThread()
        self.battle_list_thread.update_signal.connect(self.update_battle_list_display)
        self.battle_list_thread.start()


        self.startTarget_checkBox.stateChanged.connect(self.update_checkbox_style)

        # Load the last used profile on startup by finding the manager and telling it to load "_last"
        if os.path.exists("Save/Targeting/_last.json"):
            profile_manager.load_profile_by_name("_last")


    def targetList(self) -> None:
        groupbox = QGroupBox("🎯 Targeting")
        groupbox_layout = QHBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Buttons
        clearTargetList_button = QPushButton(QIcon.fromTheme("edit-clear"), "Clear List", self)
        clearTargetList_button.setStyleSheet("background-color: #95a5a6;")
        clearTargetList_button.setToolTip("Remove all monsters from the targeting list.")
        self.add_target_button = QPushButton(QIcon.fromTheme("list-add"), "Add", self)
        self.add_target_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")

        # Button Functions
        clearTargetList_button.clicked.connect(self.clearTarget_list)
        self.add_target_button.clicked.connect(self.add_target)

        # Layouts
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        move_buttons_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Up/Down buttons for the list
        up_button = QPushButton("↑")
        up_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        down_button = QPushButton("↓")
        down_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        delete_button = QPushButton("X")
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        up_button.setToolTip("Move selected monster up (higher priority).")
        down_button.setToolTip("Move selected monster down (lower priority).")
        delete_button.setToolTip("Delete the selected monster from the list.")
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(up_button)
        move_buttons_layout.addWidget(down_button)
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(delete_button)
        move_buttons_layout.addStretch()

        # Left side: List and clear button
        left_layout.addWidget(self.targetList_listWidget)

        # Right side: Form layout for controls
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.targetName_lineEdit)
        name_layout.addWidget(self.add_target_button)
        form_layout.addRow(QLabel("Name:"), name_layout)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.attackKey_comboBox)
        set_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
        set_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_key_button.setToolTip("Click and then press the desired key to set it.")
        key_layout.addWidget(set_key_button)
        form_layout.addRow(QLabel("Attack Key:"), key_layout)
        form_layout.addRow(QLabel("Distance:"), self.attackDist_comboBox)
        form_layout.addRow(QLabel("Stance:"), self.stance_comboBox)

        right_layout.addLayout(form_layout)
        right_layout.addWidget(self.startTarget_checkBox)
        right_layout.addWidget(clearTargetList_button)
        right_layout.addStretch() # Pushes everything up
        right_layout.addWidget(self.setup_battle_list_group())

        self.targetName_lineEdit.setPlaceholderText("Orc, * - All Monsters")

        groupbox_layout.addLayout(left_layout)
        groupbox_layout.addLayout(move_buttons_layout)
        groupbox_layout.addLayout(right_layout)
        set_key_button.clicked.connect(
            lambda: self.start_key_capture(set_key_button, self.attackKey_comboBox)
        )
        self.targetList_listWidget.itemDoubleClicked.connect(
            self.edit_target_action
        )

        # Connect move buttons
        up_button.clicked.connect(lambda: self.move_list_item(self.targetList_listWidget, "up"))
        down_button.clicked.connect(lambda: self.move_list_item(self.targetList_listWidget, "down"))
        delete_button.clicked.connect(self.delete_selected_target)

        return groupbox

    def setup_battle_list_group(self) -> QGroupBox:
        """Sets up the groupbox to display monsters on screen."""
        groupbox = QGroupBox("👹 Monsters On Screen")
        layout = QVBoxLayout(groupbox)

        self.monster_on_screen_label = QLabel("Monster on screen: No")
        self.monsters_count_label = QLabel("Count: 0")
        self.monsters_list_textedit = QTextEdit()
        self.monsters_list_textedit.setReadOnly(True)
        self.monsters_list_textedit.setFixedHeight(80) # Adjust height as needed

        layout.addWidget(self.monster_on_screen_label)
        layout.addWidget(self.monsters_count_label) # type: ignore
        layout.addWidget(self.monsters_list_textedit)

        return groupbox


    def add_target(self) -> None:
        if self.currently_editing_target_item:
            self._update_target()
            return

        self.status_label.setText("")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.targetName_lineEdit.setStyleSheet("")

        monster_name = self.targetName_lineEdit.text().strip()
        if not monster_name:
            QMessageBox.warning(self, "Input Error", "Please enter a monster name.")
            return

        target_data = {
            "Name": monster_name,
            "Dist": self.attackDist_comboBox.currentIndex(),
            "Stance": self.stance_comboBox.currentIndex(),
        }

        dist_text = self.attackDist_comboBox.currentText()
        stance_text = self.stance_comboBox.currentText()
        display_text = f"<b style='color: #ffffff; font-size: 10pt;'>{monster_name}</b><br><small style='color: #bbbbbb;'>Dist: {dist_text}, Stance: {stance_text}</small>"
        monster = QListWidgetItem(display_text)
        monster.setData(Qt.UserRole, target_data)
        self.targetList_listWidget.addItem(monster)

        # Clear field
        self.targetName_lineEdit.clear()
        self.attackDist_comboBox.setCurrentIndex(0)
        self.stance_comboBox.setCurrentIndex(0)

        # Success message
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setText(f"Target '{monster_name}' has been added!")


    def _update_target(self):
        if not self.currently_editing_target_item:
            return

        new_data = {
            "Name": self.targetName_lineEdit.text().strip(),
            "Dist": self.attackDist_comboBox.currentIndex(),
            "Stance": self.stance_comboBox.currentIndex(),
        }
        dist_text = self.attackDist_comboBox.currentText()
        stance_text = self.stance_comboBox.currentText()
        display_text = f"<b style='color: #ffffff; font-size: 10pt;'>{new_data['Name']}</b><br><small style='color: #bbbbbb;'>Dist: {dist_text}, Stance: {stance_text}</small>"

        self.currently_editing_target_item.setText(display_text)
        self.currently_editing_target_item.setData(Qt.UserRole, new_data)

        self.currently_editing_target_item = None
        self.targetName_lineEdit.clear()
        self.attackDist_comboBox.setCurrentIndex(0)
        self.stance_comboBox.setCurrentIndex(0)
        self.add_target_button.setText("Add")

    def edit_target_action(self):
        selected_item = self.targetList_listWidget.currentItem()
        if not selected_item:
            return

        self.currently_editing_target_item = selected_item
        data = selected_item.data(Qt.UserRole)

        self.targetName_lineEdit.setText(data.get("Name", ""))
        self.attackDist_comboBox.setCurrentIndex(data.get("Dist", 0))
        self.stance_comboBox.setCurrentIndex(data.get("Stance", 0))
        self.status_label.setText(f"Editing target '{data.get('Name', '')}'...")
        self.add_target_button.setText("Save Changes")

    def delete_selected_target(self):
        """Deletes the currently selected item from the target list."""
        current_item = self.targetList_listWidget.currentItem()
        if current_item:
            delete_item(self.targetList_listWidget, current_item)

    def get_data_for_saving(self) -> dict:
        target_list = []
        for i in range(self.targetList_listWidget.count()):
            item = self.targetList_listWidget.item(i)
            if item and item.data(Qt.UserRole):
                target_list.append(item.data(Qt.UserRole))

        ui_state = {
            "attackKey": self.attackKey_comboBox.currentText(),
            "startTargeting": self.startTarget_checkBox.isChecked()
        }
        return {
            "targets": target_list,
            "ui_state": ui_state
        }

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

    def load_data_from_profile(self, loaded_data: dict):
        """Applies the loaded targeting rules."""
        self.targetList_listWidget.clear()

        # Restore UI state
        ui_state = loaded_data.get("ui_state", {})
        self.attackKey_comboBox.setCurrentText(ui_state.get("attackKey", "F1"))
        self.startTarget_checkBox.setChecked(ui_state.get("startTargeting", False))

        # Restore target list
        for target_data in loaded_data.get("targets", []):
            if not target_data: continue
            dist_text = self.attackDist_comboBox.itemText(target_data.get("Dist", 0))
            stance_text = self.stance_comboBox.itemText(target_data.get("Stance", 0))
            target_item = QListWidgetItem(f"<b style='color: #ffffff; font-size: 10pt;'>{target_data['Name']}</b><br><small style='color: #bbbbbb;'>Dist: {dist_text}, Stance: {stance_text}</small>")
            target_item.setData(Qt.UserRole, target_data)
            self.targetList_listWidget.addItem(target_item)

    def clearTarget_list(self) -> None:
        self.targetList_listWidget.clear()
        self.status_label.setText("")  # optional

    def start_target_thread(self, state) -> None:
        if state == Qt.Checked:
            targets = []
            for i in range(self.targetList_listWidget.count()):
                item = self.targetList_listWidget.item(i)
                if item and item.data(Qt.UserRole):
                    targets.append(item.data(Qt.UserRole))
            self.target_thread = TargetThread(targets, self.attackKey_comboBox.currentIndex()) # type: ignore
            self.target_thread.start()
        else:
            if self.target_thread:
                self.target_thread.stop()
                self.target_thread = None

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
            checkbox.setStyleSheet("color: #4CAF50; font-weight: bold;")  # Green color
        else:
            checkbox.setStyleSheet("color: #aaaaaa; font-weight: normal;") # Dimmed color for unchecked

    def update_battle_list_display(self, count, names):
        """Updates the monster count and list display."""
        if count > 0:
            self.monster_on_screen_label.setText("Monster on screen: <b style='color: #e74c3c;'>Yes</b>")
        else:
            self.monster_on_screen_label.setText("Monster on screen: <b style='color: #2ecc71;'>No</b>")

        self.monsters_count_label.setText(f"Count: {count}")
        self.monsters_list_textedit.setText("\n".join(names))

    def stop_all_threads(self):
        """Stops all running threads in this tab."""
        if self.battle_list_thread:
            self.battle_list_thread.stop()
            self.battle_list_thread.wait()
        if self.target_thread:
            self.target_thread.stop()
            self.target_thread.wait()
