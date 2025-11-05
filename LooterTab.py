import json
import os
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QLineEdit, QListWidget,
    QGroupBox, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from Functions.GeneralFunctions import delete_item
from LootThread import LootThread
from General.BotLogger import bot_logger
from Settings.ProfileManagerWidget import ProfileManagerWidget


class LooterTab(QWidget):
    def __init__(self):
        super().__init__()

        self.loot_thread = None

        # --- Main Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # --- UI Elements ---
        self.startLoot_checkBox = QCheckBox("Looting", self)
        self.startLoot_checkBox.setToolTip("Enable/disable auto-looting from killed monsters.")
        self.startLoot_checkBox.stateChanged.connect(self.start_loot_thread)
        self.startLoot_checkBox.stateChanged.connect(self.update_checkbox_style)

        self.itemName_lineEdit = QLineEdit(self)
        self.lootOption_lineEdit = QLineEdit(self)
        self.lootOption_lineEdit.setFixedWidth(20)
        self.lootOption_lineEdit.setMaxLength(2)
        self.lootList_listWidget = QListWidget(self)
        self.lootList_listWidget.setToolTip("List of items to loot. Double-click to delete.")

        # --- Setup UI ---
        loot_list_group = self.setup_loot_list()
        left_layout.addWidget(loot_list_group)

        # --- Profile Manager (Right Panel) ---
        profile_manager = ProfileManagerWidget(
            profile_directory="Save/Looting",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )

        main_layout.addWidget(left_panel)
        main_layout.addWidget(profile_manager)

    def setup_loot_list(self) -> QGroupBox:
        groupbox = QGroupBox("💰 Loot List", self)
        groupbox_layout = QVBoxLayout(groupbox)

        add_item_button = QPushButton(QIcon.fromTheme("list-add"), "Add", self)
        add_item_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        add_item_button.setFixedWidth(40)
        self.itemName_lineEdit.setToolTip("Name of the item to loot.")
        self.lootOption_lineEdit.setToolTip("Container to place the loot in (e.g., 1 for first backpack).")
        add_item_button.clicked.connect(self.add_item)

        self.lootList_listWidget.itemDoubleClicked.connect(
            lambda item: delete_item(self.lootList_listWidget, item)
        )

        layout1 = QHBoxLayout()
        layout1.addWidget(self.itemName_lineEdit)
        layout1.addWidget(self.lootOption_lineEdit)
        layout1.addWidget(add_item_button)

        groupbox_layout.addWidget(self.startLoot_checkBox)
        groupbox_layout.addWidget(self.lootList_listWidget)
        groupbox_layout.addLayout(layout1)
        return groupbox

    def add_item(self) -> None:
        item_name = self.itemName_lineEdit.text().strip()
        loot_container = self.lootOption_lineEdit.text().strip()

        if not item_name or not loot_container:
            QMessageBox.warning(self, "Input Error", "Please fill in both item name and container number.")
            return

        # Check for duplicates (case-insensitive)
        for i in range(self.lootList_listWidget.count()):
            if self.lootList_listWidget.item(i).text().lower() == item_name.lower():
                QMessageBox.warning(self, "Duplicate Item", f"The item '{item_name}' is already in the loot list.")
                return

        for index in range(self.lootList_listWidget.count()):
            item = self.lootList_listWidget.item(index)
            if item and item_name.upper() == item.text().upper():
                return

        item_data = {
            "Name": item_name,
            "Loot": int(loot_container)
        }

        item = QListWidgetItem(item_name)
        item.setData(Qt.UserRole, item_data)
        self.lootList_listWidget.addItem(item)

        self.lootOption_lineEdit.clear()
        self.itemName_lineEdit.clear()

    def get_data_for_saving(self) -> dict:
        loot_list = [
            item.data(Qt.UserRole) for i in range(self.lootList_listWidget.count())
            if (item := self.lootList_listWidget.item(i)) and item.data(Qt.UserRole)
        ]
        return {
            "loot": loot_list,
            "enabled": self.startLoot_checkBox.isChecked()
        }

    def load_data_from_profile(self, loaded_data: dict):
        self.lootList_listWidget.clear()
        self.startLoot_checkBox.setChecked(loaded_data.get("enabled", False))
        for loot_data in loaded_data.get("loot", []):
            if not loot_data: continue
            loot_item = QListWidgetItem(loot_data['Name'])
            loot_item.setData(Qt.UserRole, loot_data)
            self.lootList_listWidget.addItem(loot_item)
        bot_logger.info("Loaded a profile in 'Looter' tab.")

    def start_loot_thread(self, state) -> None:
        if state == Qt.Checked:
            self.loot_thread = LootThread(self.lootList_listWidget)
            self.loot_thread.start()
            bot_logger.info('<font color="#4CAF50">Looting module started.</font>')
        else:
            if self.loot_thread:
                bot_logger.info('<font color="#c0392b">Looting module stopped.</font>')
                self.loot_thread.stop()
                self.loot_thread.wait()

    def update_checkbox_style(self, state):
        checkbox = self.sender()
        if state == Qt.Checked:
            checkbox.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            checkbox.setStyleSheet("")

    def stop_all_threads(self):
        if self.loot_thread:
            self.loot_thread.stop()
            self.loot_thread.wait()