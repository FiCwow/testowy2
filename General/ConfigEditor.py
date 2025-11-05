import ast
import os
import textwrap

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit,
                             QFormLayout, QScrollArea, QMessageBox)
from PyQt5.QtGui import QIcon

import Addresses

VALIDATION_SCHEMA = {
    # Game variables
    'square_size': 'int',
    'application_architecture': 'int',
    'collect_threshold': 'float',
    'client_name': 'str',

    # Character Addresses
    'my_x_address': 'hex',
    'my_x_address_offset': 'hex_list',
    'my_x_type': 'int',
    'my_y_address': 'hex',
    'my_y_address_offset': 'hex_list',
    'my_y_type': 'int',
    'my_z_address': 'hex',
    'my_z_address_offset': 'hex_list',
    'my_z_type': 'int',
    'my_stats_address': 'hex',
    'my_hp_offset': 'hex_list',
    'my_hp_max_offset': 'hex_list',
    'my_hp_type': 'int',
    'my_mp_offset': 'hex_list',
    'my_mp_max_offset': 'hex_list',
    'my_mp_type': 'int',

    # Target Addresses
    'attack_address': 'hex',
    'attack_address_offset': 'hex_list',
    'my_attack_type': 'int',
    'target_x_offset': 'hex', 'target_x_type': 'int',
    'target_y_offset': 'hex', 'target_y_type': 'int',
    'target_z_offset': 'hex', 'target_z_type': 'int',
    'target_hp_offset': 'hex', 'target_hp_type': 'int',
    'target_name_offset': 'hex', 'target_name_type': 'int'
}

class ConfigEditor(QWidget):
    def __init__(self, client_file_name):
        super().__init__()
        self.client_file_name = client_file_name
        self.client_file_path = os.path.join("ClientConfigs", self.client_file_name)
        self.widgets = {}

        self.setWindowTitle(f"Edit Config: {self.client_file_name}")
        self.setWindowIcon(QIcon('Images/Icon.jpg'))
        self.setMinimumSize(450, 600)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Scroll Area for form
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)

        # Container widget for the form
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        scroll_area.setWidget(form_container)

        # Buttons
        self.save_button = QPushButton("Save and Close", self)
        self.save_button.clicked.connect(self.save_config)
        self.main_layout.addWidget(self.save_button)

        self.load_and_display_config()

    def load_and_display_config(self):
        try:
            config = Addresses.get_client_config_dict(self.client_file_name)
            for key, value in config.items():
                label = QLabel(f"{key}:")
                if isinstance(value, list):
                    # Convert list to a string representation for editing
                    value_str = ', '.join(map(lambda x: hex(x) if isinstance(x, int) else str(x), value))
                elif isinstance(value, int):
                    # Show integers as hex
                    value_str = hex(value)
                else:
                    value_str = str(value)

                line_edit = QLineEdit(value_str, self)
                self.form_layout.addRow(label, line_edit)
                self.widgets[key] = line_edit
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration file.\n\nError: {e}")
            self.close()

    def save_config(self):
        new_config = {}
        try:
            for key, line_edit in self.widgets.items():
                line_edit.setStyleSheet("")  # Reset border color
                value_str = line_edit.text().strip()
                expected_type = VALIDATION_SCHEMA.get(key, 'str')  # Default to string if not in schema
                new_config[key] = self._validate_and_parse(value_str, expected_type)

            self.write_config_to_file(new_config)
            QMessageBox.information(self, "Success", f"Configuration for '{self.client_file_name}' saved successfully.")
            self.close()

        except ValueError as e:
            # Highlight the problematic field and show an error
            line_edit.setStyleSheet("border: 2px solid red;")
            QMessageBox.critical(self, "Invalid Input", f"Error in field '{key}':\n\n{e}")

    def _validate_and_parse(self, value_str: str, expected_type: str):
        """
        Validates and parses a string value based on the expected type from the schema.
        Raises ValueError on failure.
        """
        if expected_type == 'str':
            return value_str
        if expected_type == 'int':
            try:
                return int(value_str, 0)  # The '0' base automatically handles '0x' prefixes
            except ValueError:
                raise ValueError("Must be a valid integer (e.g., 64).")
        if expected_type == 'float':
            try:
                return float(value_str)
            except ValueError:
                raise ValueError("Must be a valid number (e.g., 0.85).")
        if expected_type == 'hex':
            try:
                return int(value_str, 16)
            except ValueError:
                raise ValueError("Must be a valid hexadecimal address (e.g., 0x123ABC).")
        if expected_type == 'hex_list':
            # Allow comma-separated values, with or without brackets
            clean_str = value_str.strip().replace('[', '').replace(']', '')
            if not clean_str:
                return []
            parts = [part.strip() for part in clean_str.split(',')]
            try:
                return [int(part, 16) for part in parts]
            except ValueError:
                raise ValueError("Must be a comma-separated list of hex values (e.g., 0x510, 0x60).")

        # Fallback for any other types, though we defined all we need
        try:
            return ast.literal_eval(value_str)
        except (ValueError, SyntaxError):
            raise ValueError("The format of the input is incorrect.")

    def write_config_to_file(self, config_dict):
        # Group keys to maintain some order and readability
        game_vars = ['square_size', 'application_architecture', 'collect_threshold', 'client_name']
        char_addrs = [k for k in config_dict if k.startswith('my_')]
        target_addrs = [k for k in config_dict if k.startswith('target_') or k.startswith('attack_')]

        # Build the file content string
        content = textwrap.dedent("""
            def get_config():
                \"\"\"
                Returns the configuration dictionary.
                \"\"\"
                return {
        """).strip() + "\n"

        content += "    # Game variables\n"
        for key in game_vars:
            if key in config_dict:
                content += f"    '{key}': {self.format_value(config_dict[key])},\n"

        content += "\n    # Character Addresses\n"
        for key in char_addrs:
            if key in config_dict:
                content += f"    '{key}': {self.format_value(config_dict[key])},\n"

        content += "\n    # Target Addresses\n"
        for key in target_addrs:
            if key in config_dict:
                content += f"    '{key}': {self.format_value(config_dict[key])},\n"

        # Add any remaining keys
        remaining_keys = set(config_dict.keys()) - set(game_vars) - set(char_addrs) - set(target_addrs)
        if remaining_keys:
            content += "\n    # Other\n"
            for key in sorted(list(remaining_keys)):
                content += f"    '{key}': {self.format_value(config_dict[key])},\n"

        content += "}\n"

        with open(self.client_file_path, 'w') as f:
            f.write(content)

    @staticmethod
    def format_value(value):
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, int):
            return hex(value)
        if isinstance(value, list):
            return '[' + ', '.join(map(ConfigEditor.format_value, value)) + ']'
        return str(value)