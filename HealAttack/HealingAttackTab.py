import json, os
from PyQt5.QtWidgets import (QWidget, QCheckBox, QComboBox, QLineEdit, QListWidget, QGridLayout, QGroupBox, QVBoxLayout, QMessageBox,
                             QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QFormLayout, QSizePolicy, QSplitter,
                             QStyledItemDelegate, QStyle)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt

from HealAttack.HealingAttackThread import HealThread, AttackThread
from Functions.GeneralFunctions import delete_item
from Functions.KeyCaptureThread import KeyCaptureThread
from HealAttack.FoodEaterThread import FoodEaterThread
from HealAttack.TimedSpellsThread import TimedSpellsThread
from Settings.ProfileManagerWidget import ProfileManagerWidget
from General.BotLogger import bot_logger
import Addresses
from General.CustomDelegates import RichTextDelegate

class HealingTab(QWidget):
    def __init__(self):
        super().__init__()

        # Thread Variables
        self.attack_thread = None
        self.heal_thread = None
        self.food_eater_thread = None
        self.timed_spells_thread = None

        # State variable for editing
        self.currently_editing_heal_item = None
        self.currently_editing_attack_item = None

        # GroupBoxes for side panel
        self.auto_eater_groupbox = None
        self.timed_spells_groupbox = None
        self.alerts_groupbox = None

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: Red; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Check Boxes
        self.startHeal_checkBox = QCheckBox("Start", self)
        self.startHeal_checkBox.setToolTip("Enable/disable the auto-healing module.")
        self.startAttack_checkBox = QCheckBox("Start", self)
        self.startAttack_checkBox.setToolTip("Enable/disable the auto-attacking module.")
        self.start_eater_checkbox = QCheckBox("Enable Brown Mushroom Eater", self)
        self.start_eater_checkbox.setToolTip("Automatically eats a brown mushroom at a set interval.")
        self.start_timed_spells_checkbox = QCheckBox("Enable Timed Spells", self)
        self.start_timed_spells_checkbox.setToolTip("Enable/disable all timed spells below.")

        # Timed Spells Checkboxes
        self.haste_checkbox = QCheckBox("Auto Haste (utani hur)", self)
        self.strong_haste_checkbox = QCheckBox("Strong Haste (utani gran hur)", self)
        self.mana_shield_checkbox = QCheckBox("Mana Shield (utamo vita)", self)
        self.cast_if_needed_checkbox = QCheckBox("Cast only when needed", self)
        self.cast_if_needed_checkbox.setToolTip("If checked, haste spells will only be cast if the character is not already hasted.")

        # Timed Spells LineEdits
        self.haste_interval_edit = QLineEdit("30", self)
        self.strong_haste_interval_edit = QLineEdit("21", self)
        self.mana_shield_interval_edit = QLineEdit("200", self)

        # Combo Boxes
        # Heal
        self.healKey_comboBox = QComboBox(self)
        self.heal_condition_type_combobox = QComboBox(self)
        self.heal_condition_type_combobox.setToolTip("Choose what to monitor: Health/Mana percentage or absolute value.")
        self.heal_condition_type_combobox.addItems(["HP %", "MP %", "HP", "MP"])
        self.heal_condition_op_combobox = QComboBox(self)
        self.heal_condition_op_combobox.setToolTip("Set the condition for the rule (e.g., 'is below <' a certain value).")
        self.heal_condition_op_combobox.addItems(["is below <", "is above >", "is between"])

        self.mushroom_interval_edit = QLineEdit("264", self)
        self.mushroom_interval_edit.setToolTip("The interval in seconds to eat a brown mushroom.")


        # Attack
        self.attackKey_comboBox = QComboBox(self)
        self.food_hotkey_combobox = QComboBox(self)

        # Timed Spells ComboBoxes
        self.haste_hotkey_combobox = QComboBox(self)
        self.strong_haste_hotkey_combobox = QComboBox(self)
        self.mana_shield_hotkey_combobox = QComboBox(self)

        # Line Edits
        # Heal
        self.heal_val1_edit = QLineEdit(self)
        self.heal_val1_edit.setToolTip("The primary value for the condition (e.g., if HP is below 50, enter 50).")
        self.heal_val2_edit = QLineEdit(self)
        self.heal_val2_edit.setToolTip("The secondary value, used only for the 'is between' condition.")
        self.heal_name_edit = QLineEdit(self)
        self.heal_name_edit.setToolTip("A custom name for this rule to easily identify it in the list.")
        self.minMPHeal_lineEdit = QLineEdit(self)
        self.minMPHeal_lineEdit.setToolTip("Minimum mana required to cast the healing spell.")

        # Attack
        self.targetName_lineEdit = QLineEdit(self)
        self.hpFrom_lineEdit = QLineEdit(self)
        self.hpFrom_lineEdit.setFixedWidth(30)
        self.hpFrom_lineEdit.setMaxLength(3)
        self.hpTo_lineEdit = QLineEdit(self)
        self.hpTo_lineEdit.setFixedWidth(30)
        self.hpTo_lineEdit.setMaxLength(2)
        self.minMPAttack_lineEdit = QLineEdit(self)
        self.minMPAttack_lineEdit.setFixedWidth(30)
        self.minMPAttack_lineEdit.setToolTip("Minimum mana required to cast the attack spell.")
        self.minHPAttack_lineEdit = QLineEdit(self)
        self.minHPAttack_lineEdit.setFixedWidth(30)
        self.minHPAttack_lineEdit.setToolTip("Bot will not use this attack if your HP is below this value.")

        int_validator_3 = QIntValidator(0, 9999, self)
        int_validator_2 = QIntValidator(1, 100, self)
        int_validator_1 = QIntValidator(0, 99, self)

        self.hpTo_lineEdit.setValidator(int_validator_1)
        self.minHPAttack_lineEdit.setValidator(int_validator_1)
        self.hpFrom_lineEdit.setValidator(int_validator_2)

        self.minMPHeal_lineEdit.setValidator(int_validator_3)
        self.minMPAttack_lineEdit.setValidator(int_validator_3)
        self.heal_val1_edit.setValidator(int_validator_3)
        self.heal_val2_edit.setValidator(int_validator_3)


        # List Widgets
        self.healList_listWidget = QListWidget(self)
        self.healList_listWidget.setItemDelegate(RichTextDelegate())
        self.attackList_listWidget = QListWidget(self)
        self.attackList_listWidget.setItemDelegate(RichTextDelegate())
        self.healList_listWidget.setToolTip("Double-click an item to edit it.")
        self.attackList_listWidget.setToolTip("Double-click an item to edit it.")

        # Layout
        # Main layout will contain the splitter
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Create a splitter to make panels resizable
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Create a container widget for the left panel
        left_panel = QWidget()
        self.left_layout = QVBoxLayout(left_panel)
        self.splitter.addWidget(left_panel)

        # Initialize sections
        self.healList()
        self.attackList()
        self.setup_side_panel(self.splitter) # Pass the splitter to the setup method
        self.alerts() # Add alerts groupbox

        # Add status label at the bottom of the left layout
        self.left_layout.addWidget(self.status_label)

        # Connect checkboxes to style updater
        checkboxes_to_style = [self.startHeal_checkBox, self.startAttack_checkBox, self.start_eater_checkbox,
                               self.start_timed_spells_checkbox, self.haste_checkbox, self.strong_haste_checkbox,
                               self.mana_shield_checkbox, self.cast_if_needed_checkbox]
        for checkbox in checkboxes_to_style:
            checkbox.stateChanged.connect(self.update_checkbox_style)

    def healList(self) -> None:
        groupbox = QGroupBox("❤️ Heal & Support")
        groupbox_layout = QHBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Button
        self.add_or_update_heal_button = QPushButton(QIcon.fromTheme("list-add"), "Add", self)
        self.add_or_update_heal_button.setToolTip("Add the current configuration as a new healing rule.")
        self.add_or_update_heal_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        self.add_or_update_heal_button.clicked.connect(self.add_or_update_heal)
        editHeal_button = QPushButton(QIcon.fromTheme("document-edit"), "Edit", self)
        editHeal_button.setToolTip("Load the selected rule from the list into the form for editing.")
        editHeal_button.setStyleSheet("background-color: #7f8c8d;")
        editHeal_button.clicked.connect(self.edit_heal_action)
        self.cancel_edit_button = QPushButton(QIcon.fromTheme("edit-undo"), "Cancel", self)
        self.cancel_edit_button.setToolTip("Cancel editing and clear the form.")
        self.cancel_edit_button.setStyleSheet("background-color: #95a5a6;")
        self.cancel_edit_button.clicked.connect(self.cancel_edit_action)

        # Key capture button
        set_heal_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
        set_heal_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_heal_key_button.setToolTip("Click and then press the desired key to set it.")

        # ComboBoxes
        Addresses.populate_keys_combobox(self.healKey_comboBox, include_special_actions=["Health", "Mana"])
        self.healKey_comboBox.setToolTip("Select the hotkey or action to perform when the condition is met.")

        # CheckBox function
        self.startHeal_checkBox.stateChanged.connect(self.startHeal_thread)

        # Use QGridLayout for a more compact and aligned form
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        self.heal_condition_op_combobox.currentTextChanged.connect(lambda text: self.heal_val2_edit.setVisible(text == "is between"))

        # Add Widgets
        grid_layout.addWidget(QLabel("If:"), 0, 0)
        grid_layout.addWidget(self.heal_condition_type_combobox, 0, 1)
        grid_layout.addWidget(self.heal_condition_op_combobox, 0, 2)

        grid_layout.addWidget(QLabel("Value:"), 1, 0)
        grid_layout.addWidget(self.heal_val1_edit, 1, 1)
        grid_layout.addWidget(self.heal_val2_edit, 1, 2)
        self.heal_val2_edit.hide()

        grid_layout.addWidget(QLabel("Press:"), 2, 0)
        grid_layout.addWidget(self.healKey_comboBox, 2, 1)
        grid_layout.addWidget(set_heal_key_button, 2, 2)
        grid_layout.addWidget(QLabel("Spell Name:"), 3, 0)
        grid_layout.addWidget(self.heal_name_edit, 3, 1, 1, 2) # Span across 2 columns
        grid_layout.addWidget(QLabel("Min MP:"), 4, 0)
        grid_layout.addWidget(self.minMPHeal_lineEdit, 4, 1, 1, 2)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_or_update_heal_button)
        buttons_layout.addWidget(editHeal_button)
        buttons_layout.addWidget(self.startHeal_checkBox)
        buttons_layout.addWidget(self.cancel_edit_button)


        # Up/Down buttons for the list
        move_buttons_layout = QVBoxLayout()
        up_button = QPushButton("↑")
        up_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        up_button.setToolTip("Move selected rule up (higher priority).")
        down_button = QPushButton("↓")
        down_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        down_button.setToolTip("Move selected rule down (lower priority).")
        delete_button = QPushButton("X")
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        delete_button.setToolTip("Delete the selected rule.")

        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(up_button)
        move_buttons_layout.addWidget(down_button)
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(delete_button)
        move_buttons_layout.addStretch()

        self.minMPHeal_lineEdit.setPlaceholderText("90")

        controls_layout = QVBoxLayout()
        controls_layout.addLayout(grid_layout)
        controls_layout.addLayout(buttons_layout)
        self.cancel_edit_button.hide()  # Hide cancel button initially



        groupbox_layout.addWidget(self.healList_listWidget)
        groupbox_layout.addLayout(move_buttons_layout)
        groupbox_layout.addLayout(controls_layout)
        self.left_layout.addWidget(groupbox)

        up_button.clicked.connect(lambda: self.move_list_item(self.healList_listWidget, "up"))
        down_button.clicked.connect(lambda: self.move_list_item(self.healList_listWidget, "down"))
        delete_button.clicked.connect(lambda: self.delete_selected_item(self.healList_listWidget))
        set_heal_key_button.clicked.connect(
            lambda: self.start_key_capture(set_heal_key_button, self.healKey_comboBox)
        )
        self.healList_listWidget.itemDoubleClicked.connect(self.edit_heal_action)
        # Clear selection on the other list when this one is clicked
        self.healList_listWidget.itemClicked.connect(lambda: self.attackList_listWidget.clearSelection())


    def attackList(self) -> None:
        groupbox = QGroupBox("⚔️ Attack")
        groupbox_layout = QHBoxLayout()
        groupbox.setLayout(groupbox_layout)

        # Button
        self.add_or_update_attack_button = QPushButton(QIcon.fromTheme("list-add"), "Add", self)
        self.add_or_update_attack_button.setStyleSheet("color: white; background-color: #27ae60; font-weight: bold;")
        self.add_or_update_attack_button.clicked.connect(self.add_or_update_attack)

        edit_attack_button = QPushButton(QIcon.fromTheme("document-edit"), "Edit", self)
        edit_attack_button.setStyleSheet("background-color: #7f8c8d;")
        edit_attack_button.clicked.connect(self.edit_attack_action)

        self.cancel_attack_edit_button = QPushButton(QIcon.fromTheme("edit-undo"), "Cancel", self)
        self.cancel_attack_edit_button.setStyleSheet("background-color: #95a5a6;")
        self.cancel_attack_edit_button.clicked.connect(self.cancel_attack_edit_action)

        # Key capture button
        set_attack_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
        set_attack_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_attack_key_button.setToolTip("Click and then press the desired key to set it.")

        # ComboBox
        Addresses.populate_keys_combobox(self.attackKey_comboBox, include_special_actions=["First Rune", "Second Rune"])

        # CheckBox function
        self.startAttack_checkBox.stateChanged.connect(self.start_attack_thread)

        # Use QGridLayout for a more compact and aligned form
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout = QHBoxLayout()

        # Form fields
        grid_layout.addWidget(QLabel("Target Name:"), 0, 0)
        grid_layout.addWidget(self.targetName_lineEdit, 0, 1, 1, 2) # Span 2 columns
        self.targetName_lineEdit.setPlaceholderText("Orc, Minotaur, etc., * - All Monsters")

        grid_layout.addWidget(QLabel("Key:"), 1, 0)
        grid_layout.addWidget(self.attackKey_comboBox, 1, 1)
        grid_layout.addWidget(set_attack_key_button, 1, 2)

        grid_layout.addWidget(QLabel("Target HP%:"), 2, 0)
        grid_layout.addWidget(self.hpFrom_lineEdit, 2, 1)
        grid_layout.addWidget(self.hpTo_lineEdit, 2, 2)

        grid_layout.addWidget(QLabel("Min. MP:"), 3, 0)
        grid_layout.addWidget(self.minMPAttack_lineEdit, 3, 1, 1, 2)
        grid_layout.addWidget(QLabel("Min. HP%:"), 4, 0)
        grid_layout.addWidget(self.minHPAttack_lineEdit, 4, 1, 1, 2)

        self.minMPAttack_lineEdit.setPlaceholderText("300")
        self.hpFrom_lineEdit.setPlaceholderText("100")
        self.hpTo_lineEdit.setPlaceholderText("0")
        self.minHPAttack_lineEdit.setPlaceholderText("50")

        buttons_layout.addWidget(self.add_or_update_attack_button)
        buttons_layout.addWidget(edit_attack_button)
        buttons_layout.addWidget(self.startAttack_checkBox)
        buttons_layout.addWidget(self.cancel_attack_edit_button)
        self.cancel_attack_edit_button.hide()

        # Up/Down buttons for the list
        move_buttons_layout = QVBoxLayout()
        up_button = QPushButton("↑")
        up_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        up_button.setToolTip("Move selected rule up (higher priority).")
        down_button = QPushButton("↓")
        down_button.setStyleSheet("font-size: 12pt; font-weight: bold;")
        down_button.setToolTip("Move selected rule down (lower priority).")
        delete_button = QPushButton("X")
        delete_button.setStyleSheet("color: white; background-color: #c0392b; font-weight: bold; font-size: 10pt;")
        delete_button.setToolTip("Delete the selected rule.")

        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(up_button)
        move_buttons_layout.addWidget(down_button)
        move_buttons_layout.addStretch()
        move_buttons_layout.addWidget(delete_button)
        move_buttons_layout.addStretch()

        controls_layout = QVBoxLayout()
        controls_layout.addLayout(grid_layout)
        controls_layout.addLayout(buttons_layout)

        groupbox_layout.addWidget(self.attackList_listWidget)
        groupbox_layout.addLayout(move_buttons_layout)
        groupbox_layout.addLayout(controls_layout)
        self.left_layout.addWidget(groupbox)

        up_button.clicked.connect(lambda: self.move_list_item(self.attackList_listWidget, "up"))
        down_button.clicked.connect(lambda: self.move_list_item(self.attackList_listWidget, "down"))
        delete_button.clicked.connect(lambda: self.delete_selected_item(self.attackList_listWidget))
        set_attack_key_button.clicked.connect(
            lambda: self.start_key_capture(set_attack_key_button, self.attackKey_comboBox)
        )
        self.attackList_listWidget.itemDoubleClicked.connect(self.edit_attack_action)
        # Clear selection on the other list when this one is clicked
        self.attackList_listWidget.itemClicked.connect(lambda: self.healList_listWidget.clearSelection())

    def autoEater(self) -> None:
        """
        GroupBox for the Auto Food Eater feature.
        """
        self.auto_eater_groupbox = QGroupBox("🍄 Brown Mushroom Eater")
        layout = QFormLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        self.auto_eater_groupbox.setLayout(layout)

        Addresses.populate_keys_combobox(self.food_hotkey_combobox)
        self.food_hotkey_combobox.setToolTip("Select the hotkey assigned to your brown mushroom.")

        set_food_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
        set_food_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
        set_food_key_button.setToolTip("Click and then press the desired key to set it.")

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.food_hotkey_combobox)
        key_layout.addWidget(set_food_key_button)

        layout.addRow(self.start_eater_checkbox)
        layout.addRow(QLabel("Mushroom Hotkey:"), key_layout)
        layout.addRow(QLabel("Interval (s):"), self.mushroom_interval_edit)

        self.start_eater_checkbox.stateChanged.connect(self.start_food_eater_thread)
        set_food_key_button.clicked.connect(
            lambda: self.start_key_capture(set_food_key_button, self.food_hotkey_combobox)
        )

    def timedSpells(self) -> None:
        """
        GroupBox for timed spells like Haste and Mana Shield.
        """
        self.timed_spells_groupbox = QGroupBox("✨ Timed Spells") # type: ignore
        grid_layout = QGridLayout(self.timed_spells_groupbox)
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(5, 5, 5, 5)

        # Populate ComboBoxes
        Addresses.populate_keys_combobox(self.haste_hotkey_combobox)
        Addresses.populate_keys_combobox(self.strong_haste_hotkey_combobox)
        Addresses.populate_keys_combobox(self.mana_shield_hotkey_combobox)

        # Helper to create a row
        def create_spell_row(row_index, checkbox, combobox, line_edit):
            set_key_button = QPushButton(QIcon.fromTheme("input-keyboard"), "Set")
            set_key_button.setStyleSheet("background-color: #8e44ad;") # Purple
            set_key_button.setToolTip("Click and then press the desired key to set it.")
            set_key_button.clicked.connect(lambda: self.start_key_capture(set_key_button, combobox))

            interval_label = QLabel("Interval (s):")
            line_edit.setFixedWidth(40)

            grid_layout.addWidget(checkbox, row_index, 0)
            grid_layout.addWidget(combobox, row_index, 1)
            grid_layout.addWidget(set_key_button, row_index, 2)
            grid_layout.addWidget(interval_label, row_index, 3)
            grid_layout.addWidget(line_edit, row_index, 4)

        # Header
        grid_layout.addWidget(self.start_timed_spells_checkbox, 0, 0, 1, 3)
        grid_layout.addWidget(self.cast_if_needed_checkbox, 0, 3, 1, 2)

        # Spell Rows
        create_spell_row(1, self.haste_checkbox, self.haste_hotkey_combobox, self.haste_interval_edit)
        create_spell_row(2, self.strong_haste_checkbox, self.strong_haste_hotkey_combobox, self.strong_haste_interval_edit)
        create_spell_row(3, self.mana_shield_checkbox, self.mana_shield_hotkey_combobox, self.mana_shield_interval_edit)

        # Set column stretch to push interval to the right
        grid_layout.setColumnStretch(1, 1)

        # Connect key capture buttons

        # Connect checkboxes to the thread starter function
        self.start_timed_spells_checkbox.stateChanged.connect(self.toggle_timed_spells_thread)
        self.haste_checkbox.stateChanged.connect(self.toggle_timed_spells_thread)
        self.strong_haste_checkbox.stateChanged.connect(self.toggle_timed_spells_thread)
        self.mana_shield_checkbox.stateChanged.connect(self.toggle_timed_spells_thread)

    def alerts(self) -> None:
        """
        GroupBox for user alerts, like low HP sound.
        """
        self.alerts_groupbox = QGroupBox("🚨 Alerts")
        layout = QFormLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        self.alerts_groupbox.setLayout(layout)

        self.low_hp_alert_checkbox = QCheckBox("Enable Low HP Sound Alert", self)
        self.low_hp_alert_checkbox.setToolTip("Plays a warning sound when HP drops below the specified percentage.")
        self.low_hp_alert_threshold_edit = QLineEdit("20", self)
        self.low_hp_alert_threshold_edit.setValidator(QIntValidator(1, 99, self))
        self.low_hp_alert_threshold_edit.setFixedWidth(40)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self.low_hp_alert_threshold_edit)
        threshold_layout.addWidget(QLabel("%"))
        layout.addRow(self.low_hp_alert_checkbox)
        layout.addRow(QLabel("Alert at HP:"), threshold_layout)

    def setup_side_panel(self, splitter: QSplitter):
        """Creates the right-side panel with utilities and profile management."""
        # Create a container widget for the right panel
        right_panel = QWidget()
        side_panel_layout = QVBoxLayout(right_panel)
        side_panel_layout.setAlignment(Qt.AlignTop)

        # Add the right panel widget to the splitter
        splitter.addWidget(right_panel)

        # Initialize and add the individual utility widgets
        self.autoEater()
        self.timedSpells()
        self.alerts()

        # Create a horizontal layout for the smaller group boxes to save vertical space
        small_group_layout = QHBoxLayout()
        small_group_layout.addWidget(self.auto_eater_groupbox)
        small_group_layout.addWidget(self.alerts_groupbox)

        # Add the utility widgets to the side panel
        side_panel_layout.addLayout(small_group_layout)
        side_panel_layout.addWidget(self.timed_spells_groupbox)

        # Add the Profile Manager
        profile_manager = ProfileManagerWidget(
            profile_directory="Save/HealingAttack",
            data_provider_func=self.get_data_for_saving,
            data_consumer_func=self.load_data_from_profile,
            parent=self
        )
        profile_manager.set_status_label(self.status_label)
        side_panel_layout.addWidget(profile_manager)

    def get_data_for_saving(self) -> dict: # type: ignore
        """Provides the current healing/attack rules to be saved."""
        heal_list = [
            item.data(Qt.UserRole) for i in range(self.healList_listWidget.count())
            if (item := self.healList_listWidget.item(i)) and item.data(Qt.UserRole)
        ]
        attack_list = [
            item.data(Qt.UserRole) for i in range(self.attackList_listWidget.count())
            if (item := self.attackList_listWidget.item(i)) and item.data(Qt.UserRole)
        ]
        ui_state = {
            "startHeal": self.startHeal_checkBox.isChecked(),
            "startAttack": self.startAttack_checkBox.isChecked(),
            "autoEater": {
                "enabled": self.start_eater_checkbox.isChecked(),
                "hotkey": self.food_hotkey_combobox.currentText(),
                "interval": self.mushroom_interval_edit.text()
            },
            "timedSpells": {
                "enabled": self.start_timed_spells_checkbox.isChecked(),
                "cast_if_needed": self.cast_if_needed_checkbox.isChecked(),
                "haste": {
                    "enabled": self.haste_checkbox.isChecked(),
                    "hotkey": self.haste_hotkey_combobox.currentText(),
                    "interval": self.haste_interval_edit.text()
                },
                "strong_haste": {
                    "enabled": self.strong_haste_checkbox.isChecked(),
                    "hotkey": self.strong_haste_hotkey_combobox.currentText(),
                    "interval": self.strong_haste_interval_edit.text()
                },
                "mana_shield": {
                    "enabled": self.mana_shield_checkbox.isChecked(),
                    "hotkey": self.mana_shield_hotkey_combobox.currentText(),
                    "interval": self.mana_shield_interval_edit.text()
                }
            },
            "alerts": {
                "low_hp_enabled": self.low_hp_alert_checkbox.isChecked(),
                "low_hp_threshold": self.low_hp_alert_threshold_edit.text()
            }
        }
        return {
            "healing": heal_list,
            "attacking": attack_list,
            "ui_state": ui_state
        }

    def load_data_from_profile(self, loaded_data: dict):
        """Applies the loaded healing/attack rules."""
        self.healList_listWidget.clear()
        self.attackList_listWidget.clear()

        # Restore UI state first
        ui_state = loaded_data.get("ui_state", {})
        self._restore_ui_state(ui_state)

        for heal_data in loaded_data.get("healing", []):
            if not heal_data: continue
            heal_item = QListWidgetItem(self.format_heal_rule_text(heal_data))
            heal_item.setData(Qt.UserRole, heal_data)
            self.healList_listWidget.addItem(heal_item)
        for attack_data in loaded_data.get("attacking", []):
            if not attack_data: continue
            attack_item = QListWidgetItem(self.format_attack_rule_text(attack_data))
            attack_item.setData(Qt.UserRole, attack_data)
            self.attackList_listWidget.addItem(attack_item)
        bot_logger.info("Loaded a profile in 'Healing & Attack' tab.")

    def format_attack_rule_text(self, data: dict) -> str:
        """Creates a readable string representation of an attack rule."""
        target = data.get("Name", "*")
        hp_from = data.get("HpFrom", 100)
        hp_to = data.get("HpTo", 0)
        key = data.get("Key", "F1")
        rule_text = f"HP: {hp_from}%-{hp_to}%, Use: {key}"
        return f"<b style='color: #ffffff; font-size: 10pt;'>{target}</b><br><small style='color: #bbbbbb;'>{rule_text}</small>"

    def _restore_ui_state(self, ui_state: dict):
        """Helper function to restore the state of UI elements from the profile."""
        self.startHeal_checkBox.setChecked(ui_state.get("startHeal", False))
        self.startAttack_checkBox.setChecked(ui_state.get("startAttack", False))

        # Auto Eater
        auto_eater_state = ui_state.get("autoEater", {})
        self.start_eater_checkbox.setChecked(auto_eater_state.get("enabled", False))
        self.food_hotkey_combobox.setCurrentText(auto_eater_state.get("hotkey", "F1"))
        self.mushroom_interval_edit.setText(auto_eater_state.get("interval", "264"))

        # Timed Spells
        timed_spells_state = ui_state.get("timedSpells", {})
        self.start_timed_spells_checkbox.setChecked(timed_spells_state.get("enabled", False))
        self.cast_if_needed_checkbox.setChecked(timed_spells_state.get("cast_if_needed", False))

        haste_state = timed_spells_state.get("haste", {})
        self.haste_checkbox.setChecked(haste_state.get("enabled", False))
        self.haste_hotkey_combobox.setCurrentText(haste_state.get("hotkey", "F1"))
        self.haste_interval_edit.setText(haste_state.get("interval", "30"))

        strong_haste_state = timed_spells_state.get("strong_haste", {})
        self.strong_haste_checkbox.setChecked(strong_haste_state.get("enabled", False))
        self.strong_haste_hotkey_combobox.setCurrentText(strong_haste_state.get("hotkey", "F1"))
        self.strong_haste_interval_edit.setText(strong_haste_state.get("interval", "21"))

        mana_shield_state = timed_spells_state.get("mana_shield", {})
        self.mana_shield_checkbox.setChecked(mana_shield_state.get("enabled", False))
        self.mana_shield_hotkey_combobox.setCurrentText(mana_shield_state.get("hotkey", "F1"))
        self.mana_shield_interval_edit.setText(mana_shield_state.get("interval", "200"))

        # Alerts
        alerts_state = ui_state.get("alerts", {})
        self.low_hp_alert_checkbox.setChecked(alerts_state.get("low_hp_enabled", False))
        self.low_hp_alert_threshold_edit.setText(alerts_state.get("low_hp_threshold", "20"))


    def add_or_update_heal(self) -> None:
        """Handles both adding a new heal rule and updating an existing one."""
        if self.currently_editing_heal_item:
            self._update_heal()
        else:
            self._add_heal()

    def _add_heal(self) -> None:
        if not self.heal_val1_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Value field cannot be empty.")
            return
        if self.heal_condition_op_combobox.currentText() == "is between" and not self.heal_val2_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "The second value field cannot be empty for 'is between' condition.")
            return

        heal_data = {
            "Type": self.heal_condition_type_combobox.currentText(),
            "Condition": self.heal_condition_op_combobox.currentText(),
            "Name": self.heal_name_edit.text().strip() or "Unnamed Heal",
            "Value1": int(self.heal_val1_edit.text()),
            "Value2": int(self.heal_val2_edit.text() or "0"),
            "Key": self.healKey_comboBox.currentText(),
            "MinMp": int(self.minMPHeal_lineEdit.text() or "0")
        }

        heal_item = QListWidgetItem(self.format_heal_rule_text(heal_data))
        heal_item.setData(Qt.UserRole, heal_data)
        self.healList_listWidget.addItem(heal_item)

        self.clear_heal_form()
        self.status_label.setText("Heal action added successfully!")

    def format_heal_rule_text(self, data: dict) -> str:
        """Creates a readable string representation of a heal rule."""
        cond_type = data.get("Type", "HP %")
        condition = data.get("Condition", "is below <")
        val1 = data.get("Value1", 0)
        val2 = data.get("Value2", 0)
        key = data.get("Key", "F1")
        name = data.get("Name", "Unnamed")

        rule_text = ""
        if condition == "is between":
            rule_text = f"If {cond_type} {condition} {val1} and {val2}, press {key}"
        else:
            rule_text = f"If {cond_type} {condition} {val1}, press {key}"        
        return f"<b style='color: #ffffff; font-size: 10pt;'>{name}</b><br><small style='color: #bbbbbb;'>{rule_text}</small>"

    def clear_heal_form(self):
        """Clears all input fields in the heal form."""
        self.heal_val1_edit.clear()
        self.heal_val2_edit.clear()
        self.heal_name_edit.clear()
        self.minMPHeal_lineEdit.clear()
        self.heal_condition_type_combobox.setCurrentIndex(0)
        self.heal_condition_op_combobox.setCurrentIndex(0)
        self.healKey_comboBox.setCurrentIndex(0)

    def _update_heal(self) -> None:
        """Saves the changes to the item being edited."""
        if not self.currently_editing_heal_item:
            return

        # Validate input fields
        if not self.heal_val1_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Value field cannot be empty.")
            return

        # Create new data and display text
        new_heal_data = {
            "Type": self.heal_condition_type_combobox.currentText(),
            "Condition": self.heal_condition_op_combobox.currentText(),
            "Name": self.heal_name_edit.text().strip() or "Unnamed Heal",
            "Value1": int(self.heal_val1_edit.text()),
            "Value2": int(self.heal_val2_edit.text() or "0"),
            "Key": self.healKey_comboBox.currentText(),
            "MinMp": int(self.minMPHeal_lineEdit.text() or "0")
        }
        new_heal_name = self.format_heal_rule_text(new_heal_data)

        # Update the item in the list and its text
        self.currently_editing_heal_item.setText(new_heal_name)
        self.currently_editing_heal_item.setData(Qt.UserRole, new_heal_data)

        # Reset UI to "add" mode
        self.cancel_edit_action()
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setText("Heal action updated successfully!")

    def edit_heal_action(self) -> None:
        """Populates the input fields with data from the selected item for editing."""
        selected_item = self.healList_listWidget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a heal action from the list to edit.")
            return

        self.currently_editing_heal_item = selected_item
        data = selected_item.data(Qt.UserRole)

        # Populate fields
        self.heal_condition_type_combobox.setCurrentText(data.get("Type", "HP %"))
        self.heal_condition_op_combobox.setCurrentText(data.get("Condition", "is below <"))
        self.heal_val1_edit.setText(str(data.get("Value1", "")))
        self.heal_name_edit.setText(data.get("Name", ""))
        self.heal_val2_edit.setText(str(data.get("Value2", "")))
        self.healKey_comboBox.setCurrentText(data.get("Key", "F1"))
        self.minMPHeal_lineEdit.setText(str(data.get("MinMp", "")))
        # Ensure the visibility of the second value field is correct
        self.heal_val2_edit.setVisible(self.heal_condition_op_combobox.currentText() == "is between")

        # Change button text and show cancel button
        self.add_or_update_heal_button.setText("Save Changes")
        self.cancel_edit_button.show()
        self.status_label.setText(f"Editing heal action...")

    def add_or_update_attack(self) -> None:
        """Handles both adding a new attack rule and updating an existing one."""
        if self.currently_editing_attack_item:
            self._update_attack()
        else:
            self._add_attack()

    def _add_attack(self) -> None:
        self.status_label.setText("")
        self.targetName_lineEdit.setStyleSheet("")
        self.hpFrom_lineEdit.setStyleSheet("")
        self.hpTo_lineEdit.setStyleSheet("")

        self.status_label.setStyleSheet("color: Red; font-weight: bold;")

        has_error = False

        if not self.targetName_lineEdit.text().strip():
            self.targetName_lineEdit.setStyleSheet("border: 2px solid red;")
            self.status_label.setText("Please fill in the 'Name' field.")
            has_error = True

        if not self.hpFrom_lineEdit.text().strip():
            self.hpFrom_lineEdit.setStyleSheet("border: 2px solid red;")
            if not has_error:
                self.status_label.setText("Please fill in the 'From' field.")
            has_error = True

        if not self.hpTo_lineEdit.text().strip():
            self.hpTo_lineEdit.setStyleSheet("border: 2px solid red;")
            if not has_error:
                self.status_label.setText("Please fill in the 'To' field.")
            has_error = True

        if has_error:
            return

        self.status_label.setStyleSheet("color: Green; font-weight: bold;")

        if not self.minMPAttack_lineEdit.text():
            self.minMPAttack_lineEdit.setText("0")
        if not self.minHPAttack_lineEdit.text():
            self.minHPAttack_lineEdit.setText("0")

        target_name = self.targetName_lineEdit.text().strip()
        hp_from_val = int(self.hpFrom_lineEdit.text())
        hp_to_val = int(self.hpTo_lineEdit.text())
        min_mp_val = int(self.minMPAttack_lineEdit.text())
        min_hp_val = int(self.minHPAttack_lineEdit.text())

        attack_data = {
            "Name": target_name,
            "Key": self.attackKey_comboBox.currentText(),
            "HpFrom": hp_from_val,
            "HpTo": hp_to_val,
            "MinMp": min_mp_val,
            "MinHp": min_hp_val,
        }
        attack_item = QListWidgetItem(self.format_attack_rule_text(attack_data))
        attack_item.setData(Qt.UserRole, attack_data)
        self.attackList_listWidget.addItem(attack_item)

        self.hpFrom_lineEdit.clear()
        self.hpTo_lineEdit.clear()
        self.minMPAttack_lineEdit.clear()
        self.minHPAttack_lineEdit.clear()
        self.targetName_lineEdit.clear()
        self.status_label.setText("Attack action added successfully!")

    def _update_attack(self) -> None:
        """Saves the changes to the item being edited."""
        if not self.currently_editing_attack_item:
            return

        # Basic validation
        if not self.targetName_lineEdit.text().strip():
            QMessageBox.warning(self, "Input Error", "Target name cannot be empty.")
            return

        # Create new data and display text
        new_attack_data = {
            "Name": self.targetName_lineEdit.text().strip(),
            "Key": self.attackKey_comboBox.currentText(),
            "HpFrom": int(self.hpFrom_lineEdit.text() or "100"),
            "HpTo": int(self.hpTo_lineEdit.text() or "0"),
            "MinMp": int(self.minMPAttack_lineEdit.text() or "0"),
            "MinHp": int(self.minHPAttack_lineEdit.text() or "0"),
        }
        new_attack_name = self.format_attack_rule_text(new_attack_data)

        # Update the item in the list
        self.currently_editing_attack_item.setText(new_attack_name)
        self.currently_editing_attack_item.setData(Qt.UserRole, new_attack_data)

        # Reset UI to "add" mode
        self.cancel_attack_edit_action()
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setText("Attack action updated successfully!")

    def edit_attack_action(self) -> None:
        """Populates the attack input fields with data from the selected item."""
        selected_item = self.attackList_listWidget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select an attack action from the list to edit.")
            return

        self.currently_editing_attack_item = selected_item
        data = selected_item.data(Qt.UserRole)

        # Populate fields
        self.targetName_lineEdit.setText(data.get("Name", ""))
        self.attackKey_comboBox.setCurrentText(data.get("Key", "F1"))
        self.hpFrom_lineEdit.setText(str(data.get("HpFrom", "")))
        self.hpTo_lineEdit.setText(str(data.get("HpTo", "")))
        self.minMPAttack_lineEdit.setText(str(data.get("MinMp", "")))
        self.minHPAttack_lineEdit.setText(str(data.get("MinHp", "")))

        # Change button text and show cancel button
        self.add_or_update_attack_button.setText("Save Changes")
        self.cancel_attack_edit_button.show()
        self.status_label.setText(f"Editing attack action...")

    def cancel_attack_edit_action(self) -> None:
        """Resets the attack UI from 'edit mode' back to 'add mode'."""
        self.currently_editing_attack_item = None
        self.add_or_update_attack_button.setText("Add")
        self.cancel_attack_edit_button.hide()

        # Clear input fields
        for field in [self.targetName_lineEdit, self.hpFrom_lineEdit, self.hpTo_lineEdit,
                      self.minMPAttack_lineEdit, self.minHPAttack_lineEdit]:
            field.clear()
        self.status_label.setText("")

    def cancel_edit_action(self) -> None:
        """Resets the UI from 'edit mode' back to 'add mode'."""
        self.currently_editing_heal_item = None
        self.add_or_update_heal_button.setText("Add")
        self.cancel_edit_button.hide()

        # Clear input fields
        self.clear_heal_form()
        self.status_label.setText("")

    def startHeal_thread(self, state) -> None:
        if state == Qt.Checked:
            if not self.heal_thread:
                alert_enabled = self.low_hp_alert_checkbox.isChecked()
                alert_threshold = int(self.low_hp_alert_threshold_edit.text() or 0)
                self.heal_thread = HealThread(
                    healing_list=self.healList_listWidget,
                    low_hp_alert_enabled=alert_enabled,
                    low_hp_alert_threshold=alert_threshold)
                self.heal_thread.start()
                bot_logger.info('<font color="#4CAF50">Healing & Support module started.</font>')
        else:
            if self.heal_thread:
                bot_logger.info('<font color="#c0392b">Healing & Support module stopped.</font>')
                self.heal_thread.stop()
                self.heal_thread = None

    def start_attack_thread(self, state) -> None:
        if state == Qt.Checked:
            if not self.attack_thread:
                self.attack_thread = AttackThread(self.attackList_listWidget)
                self.attack_thread.start()
                bot_logger.info('<font color="#4CAF50">Attack module started.</font>')
        else:
            if self.attack_thread:
                bot_logger.info('<font color="#c0392b">Attack module stopped.</font>')
                self.attack_thread.stop()
                self.attack_thread = None

    def start_food_eater_thread(self, state) -> None:
        if state == Qt.Checked:
            if not self.food_eater_thread:
                food_hotkey = self.food_hotkey_combobox.currentText()
                interval = int(self.mushroom_interval_edit.text() or "264")
                self.food_eater_thread = FoodEaterThread(food_hotkey, interval)
                self.food_eater_thread.start()
                bot_logger.info('<font color="#4CAF50">Brown Mushroom Eater started.</font>')
        else:
            if self.food_eater_thread:
                bot_logger.info('<font color="#c0392b">Brown Mushroom Eater stopped.</font>')
                self.food_eater_thread.stop()
                self.food_eater_thread = None

    def toggle_timed_spells_thread(self) -> None:
        """Starts, stops, or restarts the TimedSpellsThread based on checkbox states."""
        # Stop any existing thread first
        if self.timed_spells_thread:
            self.timed_spells_thread.stop()
            self.timed_spells_thread = None

        # Check if the main toggle is enabled and at least one spell is selected
        if not self.start_timed_spells_checkbox.isChecked():
            bot_logger.info('<font color="#c0392b">Timed Spells module stopped.</font>')
            return

        spells_to_cast = []
        if self.haste_checkbox.isChecked():
            spells_to_cast.append({
                'spell': 'utani hur',
                'hotkey': self.haste_hotkey_combobox.currentText().lower(),
                'interval': int(self.haste_interval_edit.text() or 30)
            })
        if self.strong_haste_checkbox.isChecked():
            spells_to_cast.append({
                'spell': 'utani gran hur',
                'hotkey': self.strong_haste_hotkey_combobox.currentText().lower(),
                'interval': int(self.strong_haste_interval_edit.text() or 21)
            })
        if self.mana_shield_checkbox.isChecked():
            spells_to_cast.append({
                'spell': 'utamo vita',
                'hotkey': self.mana_shield_hotkey_combobox.currentText().lower(),
                'interval': int(self.mana_shield_interval_edit.text() or 200)
            })

        # If there are spells to cast, start a new thread
        if spells_to_cast:
            self.timed_spells_thread = TimedSpellsThread(spells_to_cast, self.cast_if_needed_checkbox.isChecked())
            self.timed_spells_thread.start()
            bot_logger.info('<font color="#4CAF50">Timed Spells module started.</font>')


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
            reply = QMessageBox.question(self, 'Confirm Deletion',
                                         f"Are you sure you want to delete this rule?\n\n'{current_item.text()}'",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                row = list_widget.row(current_item)
                list_widget.takeItem(row)

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

    def stop_all_threads(self):
        """Stops all running threads in this tab."""
        if self.heal_thread:
            self.heal_thread.stop()
            self.heal_thread.wait()
        if self.attack_thread:
            self.attack_thread.stop()
            self.attack_thread.wait()
        if self.food_eater_thread:
            self.food_eater_thread.stop()
            self.food_eater_thread.wait()
        if self.timed_spells_thread:
            self.timed_spells_thread.stop()
            self.timed_spells_thread.wait()