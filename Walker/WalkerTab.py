import json
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QSplitter,
    QWidget, QListWidget, QLineEdit, QTextEdit, QCheckBox, QComboBox, QVBoxLayout,
    QHBoxLayout, QGroupBox, QPushButton, QListWidgetItem, QLabel, QGridLayout, QFormLayout
)
from PyQt5.QtGui import QIcon

from Functions.GeneralFunctions import delete_item, manage_profile
from Settings.ProfileManagerWidget import ProfileManagerWidget
from General.CustomDelegates import RichTextDelegate
from Functions.MemoryFunctions import *
from Walker.WalkerThread import WalkerThread, RecordThread


class WalkerTab(QWidget):
    def __init__(self):
        super().__init__()

        # Thread Variables
        self.record_thread = None
        self.walker_thread = None
        self.key_capture_thread = None

        # Other Variables
        self.labels_dictionary = {}

        # --- Status label at the bottom (behaves like a "status bar")
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Widgets
        self.waypointList_listWidget = QListWidget(self)
        self.waypointList_listWidget.setItemDelegate(RichTextDelegate())
        self.record_checkBox = QCheckBox("Auto Recording", self)
        self.record_checkBox.setToolTip("Automatically record your character's steps as waypoints.")
        self.start_checkBox = QCheckBox("Start Walker", self)
        self.start_checkBox.setToolTip("Enable/disable the cavebot.")
        self.option_comboBox = QComboBox(self)
        directions = [
            "Center", "North", "South", "East", "West",
            "North-East", "North-West", "South-East", "South-West", "Lure"
        ]
        self.option_comboBox.addItems(directions)
        self.option_comboBox.setToolTip("Select the action or direction for the next manually added waypoint.")

        # Main Layout
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Create a splitter
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Left panel for waypoints list and controls
        left_panel = QWidget()
        self.left_layout = QVBoxLayout(left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(left_panel)

        # Initialize UI
        profile_manager = ProfileManagerWidget(
            profile_directory="Save/Waypoints",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )
        self.left_layout.addWidget(profile_manager)

        self.start_walker()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.waypointList())
        self.splitter.addWidget(right_panel)

    def waypointList(self) -> QGroupBox:
        groupbox = QGroupBox("🗺️ Waypoints")
        groupbox_layout = QHBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Buttons
        stand_waypoint_button = QPushButton("📍 Stand", self)
        stand_waypoint_button.setToolTip("Adds a waypoint at your current position.\nThe bot will walk to this spot and stop.")
        rope_waypoint_button = QPushButton("🧗 Rope", self)
        rope_waypoint_button.setToolTip("Adds a waypoint to use a rope on the specified tile.\nSet the rope hotkey in Settings -> Tools.")
        shovel_waypoint_button = QPushButton("⛏️ Shovel", self)
        shovel_waypoint_button.setToolTip("Adds a waypoint to use a shovel on the specified tile.\nSet the shovel hotkey in Settings -> Tools.")
        ladder_waypoint_button = QPushButton("🪜 Ladder", self)
        ladder_waypoint_button.setToolTip("Adds a waypoint to use a ladder.\nThe bot will right-click the tile to go up/down.")
        clearWaypointList_button = QPushButton(QIcon.fromTheme("edit-clear"), "Clear List", self)
        clearWaypointList_button.setToolTip("Removes all waypoints from the current list.")

        # Connect to add_waypoint with different indexes
        clearWaypointList_button.clicked.connect(self.clear_waypointList)
        stand_waypoint_button.clicked.connect(lambda: self.add_waypoint(0))
        rope_waypoint_button.clicked.connect(lambda: self.add_waypoint(1))
        shovel_waypoint_button.clicked.connect(lambda: self.add_waypoint(2))
        ladder_waypoint_button.clicked.connect(lambda: self.add_waypoint(3))

        # Layouts
        list_and_move_layout = QHBoxLayout()
        left_layout = QVBoxLayout() # This will contain the list, move buttons, and clear button
        right_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(5, 5, 5, 5) # type: ignore
        manual_buttons_layout = QGridLayout()

        # Up/Down buttons for the list
        move_buttons_layout = QVBoxLayout()
        up_button = QPushButton("▲")
        up_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        up_button.setToolTip("Move selected waypoint up.")
        down_button = QPushButton("▼")
        down_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        down_button.setToolTip("Move selected waypoint down.")
        edit_button = QPushButton(QIcon.fromTheme("document-edit"), "")
        edit_button.setToolTip("Edit selected waypoint's action (e.g., change from Stand to Lure).")
        duplicate_button = QPushButton(QIcon.fromTheme("edit-copy"), "")
        duplicate_button.setToolTip("Duplicate the selected waypoint.")
        delete_button = QPushButton("❌")
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        up_button.setToolTip("Move selected waypoint up.")
        down_button.setToolTip("Move selected waypoint down.")
        delete_button.setToolTip("Delete selected waypoint.")
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(up_button)
        move_buttons_layout.addWidget(down_button)
        move_buttons_layout.addWidget(edit_button)
        move_buttons_layout.addWidget(duplicate_button)
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(delete_button)

        # Left side: List and clear button
        list_and_move_layout.addWidget(self.waypointList_listWidget)
        list_and_move_layout.addLayout(move_buttons_layout)
        left_layout.addLayout(list_and_move_layout)
        left_layout.addWidget(clearWaypointList_button)

        # Right side: Form and buttons
        form_layout.addRow(QLabel("Action:"), self.option_comboBox)
        form_layout.addRow(stand_waypoint_button)

        manual_buttons_layout.addWidget(rope_waypoint_button, 0, 0)
        manual_buttons_layout.addWidget(shovel_waypoint_button, 0, 1)
        manual_buttons_layout.addWidget(ladder_waypoint_button, 1, 0, 1, 2) # Span across 2 columns

        right_layout.addLayout(form_layout)
        right_layout.addLayout(manual_buttons_layout)
        right_layout.addStretch()
        groupbox_layout.addLayout(left_layout)
        groupbox_layout.addLayout(right_layout)

        up_button.clicked.connect(lambda: self.move_list_item(self.waypointList_listWidget, "up"))
        down_button.clicked.connect(lambda: self.move_list_item(self.waypointList_listWidget, "down"))
        delete_button.clicked.connect(self.delete_selected_waypoint)
        self.waypointList_listWidget.itemDoubleClicked.connect(
            lambda item: delete_item(self.waypointList_listWidget, item)
        )

        return groupbox

    def start_walker(self) -> None:
        groupbox = QGroupBox("▶️ Start")
        groupbox_layout = QVBoxLayout()
        groupbox_layout.setSpacing(5)
        groupbox_layout.setContentsMargins(5, 5, 5, 5)
        groupbox.setLayout(groupbox_layout)

        self.start_checkBox.stateChanged.connect(self.start_walker_thread)
        self.record_checkBox.stateChanged.connect(self.start_record_thread)

        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout1.addWidget(self.start_checkBox)
        layout2.addWidget(self.record_checkBox)

        groupbox_layout.addLayout(layout1)
        groupbox_layout.addLayout(layout2)
        self.left_layout.addWidget(groupbox)
        # Add status label at the bottom of the left layout
        self.left_layout.addWidget(self.status_label)

    def save_profile(self, autosave=False):
        """Exposes the save functionality for auto-saving."""
        profile_manager = self.findChild(ProfileManagerWidget)
        if profile_manager:
            profile_manager.save_profile(autosave=True)

    def get_data_for_saving(self):
        """Provides the current waypoint list to be saved."""
        waypoint_list = [
            item.data(Qt.UserRole) for i in range(self.waypointList_listWidget.count())
            if (item := self.waypointList_listWidget.item(i)) and item.data(Qt.UserRole)
        ]
        return {
            "waypoints": waypoint_list,
        }

    def load_data_from_profile(self, loaded_data: dict):
        """Applies the loaded waypoint list."""
        self.waypointList_listWidget.clear()
        for walk_data in loaded_data.get("waypoints", []):
            if not walk_data: continue
            direction_text = self.option_comboBox.itemText(walk_data.get("Direction", 0))
            walk_name = self.format_waypoint_text(walk_data, direction_text)

            walk_item = QListWidgetItem(walk_name)
            walk_item.setData(Qt.UserRole, walk_data)
            self.waypointList_listWidget.addItem(walk_item)

    def add_waypoint(self, index):
        x, y, z = read_my_wpt()

        waypoint_data = {
            "X": x,
            "Y": y,
            "Z": z,
            "Action": index
        }

        self.status_label.setText("")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        direction_text = self.option_comboBox.currentText()
        waypoint_data["Direction"] = self.option_comboBox.currentIndex()
        waypoint_text = self.format_waypoint_text(waypoint_data, direction_text)
        waypoint = QListWidgetItem(waypoint_text)

        waypoint.setData(Qt.UserRole, waypoint_data)
        self.waypointList_listWidget.addItem(waypoint)
        if self.waypointList_listWidget.currentRow() == -1:
            self.waypointList_listWidget.setCurrentRow(0)
        else:
            self.waypointList_listWidget.setCurrentRow(self.waypointList_listWidget.currentRow() + 1)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setText("Waypoint added successfully!")

    def format_waypoint_text(self, data: dict, direction_text: str) -> str:
        """Creates a readable string representation of a waypoint."""
        x, y, z = data['X'], data['Y'], data['Z']
        action_index = data['Action']
        action_name = "Unknown"

        if index == 0:  # Stand
            action_name = "Stand"
            details = f"{x}, {y}, {z} - {direction_text}"
        elif index == 1:  # Rope
            action_name = "Rope"
            details = f"{x}, {y}, {z}"
        elif index == 2:  # Shovel
            action_name = "Shovel"
            details = f"{x}, {y}, {z}"
        elif index == 3:  # Ladder
            action_name = "Ladder"
            details = f"{x}, {y}, {z}"
        
        return f"<b style='color: #ffffff; font-size: 10pt;'>{action_name}</b><br><small style='color: #bbbbbb;'>{details}</small>"

    def delete_selected_waypoint(self) -> None:
        """Deletes the currently selected item from the waypoint list."""
        selected_item = self.waypointList_listWidget.currentItem()
        if selected_item:
            delete_item(self.waypointList_listWidget, selected_item)

    def clear_waypointList(self) -> None:
        self.waypointList_listWidget.clear()
        self.status_label.setText("")  # Clear status if you want

    def start_record_thread(self, state):
        if state == Qt.Checked:
            if not self.record_thread:
                self.record_thread = RecordThread(self.option_comboBox)
                self.record_thread.wpt_update.connect(self.update_waypointList)
                self.record_thread.start()
        else:
            if self.record_thread:
                self.record_thread.stop()
                self.record_thread = None

    def start_walker_thread(self, state):
        if state == Qt.Checked:
            if not self.walker_thread:
                waypoints = []
                for i in range(self.waypointList_listWidget.count()):
                    item = self.waypointList_listWidget.item(i)
                    if item and item.data(Qt.UserRole) is not None:
                        waypoints.append(item.data(Qt.UserRole))
                self.walker_thread = WalkerThread(waypoints)
                self.walker_thread.index_update.connect(self.update_waypointList)
                self.walker_thread.start()
        else:
            if self.walker_thread:
                self.walker_thread.stop()
                self.walker_thread = None

    def update_waypointList(self, option, waypoint):
        if option == 0:
            self.waypointList_listWidget.setCurrentRow(int(waypoint))
        elif option == 1:
            self.waypointList_listWidget.addItem(waypoint)

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
