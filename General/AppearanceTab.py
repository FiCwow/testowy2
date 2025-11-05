import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QPushButton, QLabel, QMessageBox, QFontComboBox, QSpinBox, QCheckBox, QColorDialog, QSlider, QHBoxLayout
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

import Addresses


class AppearanceTab(QWidget):
    def __init__(self):
        super().__init__()

        # Store current preview settings
        self.current_preview_color = "#ff0000"  # Default red

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        # --- Theme Selection Group ---
        theme_group = QGroupBox("Application Theme")
        theme_layout = QFormLayout()
        theme_group.setLayout(theme_layout)

        self.theme_combobox = QComboBox(self)
        self.theme_combobox.addItems(["Dark", "Light", "Tibian", "Custom"])
        self.theme_combobox.setToolTip("Select the visual theme for the application.")
        theme_layout.addRow(QLabel("Select Theme:"), self.theme_combobox)

        self.font_combobox = QFontComboBox(self)
        self.font_combobox.setToolTip("Select the application-wide font.")
        theme_layout.addRow(QLabel("Select Font:"), self.font_combobox)

        self.font_size_spinbox = QSpinBox(self)
        self.font_size_spinbox.setRange(8, 16)
        self.font_size_spinbox.setToolTip("Select the application-wide font size.")
        theme_layout.addRow(QLabel("Font Size:"), self.font_size_spinbox)

        self.autosave_checkbox = QCheckBox("Auto-save profile on exit")
        self.autosave_checkbox.setToolTip("If checked, the current state of Targeting and Healing tabs will be saved on exit.")
        theme_layout.addRow(self.autosave_checkbox)

        # --- Preview Frame Settings ---
        preview_settings_label = QLabel("<b>Smart Hotkeys Preview Frame</b>")
        theme_layout.addRow(preview_settings_label)

        # Color picker
        self.preview_color_button = QPushButton("Choose Color")
        self.preview_color_button.setToolTip("Select the color of the area preview frame.")
        self.preview_color_button.clicked.connect(self.choose_preview_color)
        self.preview_color_display = QLabel()
        self.preview_color_display.setFixedSize(22, 22)
        self.preview_color_display.setAutoFillBackground(True)
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.preview_color_button)
        color_layout.addWidget(self.preview_color_display)
        color_layout.addStretch()
        theme_layout.addRow(QLabel("Frame Color:"), color_layout)

        # Opacity slider
        self.preview_opacity_slider = QSlider(Qt.Horizontal)
        self.preview_opacity_slider.setRange(10, 100) # 10% to 100% opacity
        self.preview_opacity_slider.setToolTip("Set the opacity of the area preview frame.")
        theme_layout.addRow(QLabel("Frame Opacity:"), self.preview_opacity_slider)

        apply_theme_button = QPushButton("Apply Theme")
        apply_theme_button.setToolTip("Apply the selected theme. The application style will update immediately.")
        apply_theme_button.clicked.connect(self.save_and_apply_theme)

        custom_theme_label = QLabel(
            "To use a custom theme, create and edit the file:\n"
            "<b>Save/Settings/custom_theme.qss</b>"
        )
        custom_theme_label.setWordWrap(True)

        theme_layout.addRow(apply_theme_button)
        theme_layout.addRow(custom_theme_label)

        self.layout.addWidget(theme_group)

        self.load_current_theme_setting()

    def load_current_theme_setting(self):
        """Loads the saved theme setting and sets the combobox."""
        try:
            with open("Save/Settings/theme.json", "r") as f:
                data = json.load(f)
                theme_choice = data.get("theme", "Tibian").capitalize()
                font_family = data.get("font_family", "Segoe UI")
                font_size = data.get("font_size", 9)
                autosave = data.get("autosave", False)
                self.current_preview_color = data.get("preview_color", "#ff0000")
                preview_opacity = data.get("preview_opacity", 30)

            self.theme_combobox.setCurrentText(theme_choice)
            self.font_combobox.setCurrentFont(QFont(font_family))
            self.font_size_spinbox.setValue(font_size)
            self.autosave_checkbox.setChecked(autosave)
            self.preview_color_display.setStyleSheet(f"background-color: {self.current_preview_color};")
            self.preview_opacity_slider.setValue(preview_opacity)

        except (FileNotFoundError, json.JSONDecodeError):
            self.theme_combobox.setCurrentText("Tibian")
            self.font_combobox.setCurrentFont(QFont("Segoe UI"))
            self.font_size_spinbox.setValue(9)
            self.autosave_checkbox.setChecked(False)
            self.preview_color_display.setStyleSheet("background-color: #ff0000;")
            self.preview_opacity_slider.setValue(30)

    def choose_preview_color(self):
        """Opens a color dialog to select the preview frame color."""
        color = QColorDialog.getColor(QColor(self.current_preview_color))
        if color.isValid():
            self.current_preview_color = color.name()
            self.preview_color_display.setStyleSheet(f"background-color: {self.current_preview_color};")

    def save_and_apply_theme(self):
        """Saves the selected theme to a file and applies it immediately."""
        selected_theme = self.theme_combobox.currentText().lower()
        selected_font = self.font_combobox.currentFont().family()
        selected_font_size = self.font_size_spinbox.value()
        autosave_enabled = self.autosave_checkbox.isChecked()
        preview_opacity = self.preview_opacity_slider.value()

        theme_data = {
            "theme": selected_theme, "font_family": selected_font, "font_size": selected_font_size,
            "autosave": autosave_enabled, "preview_color": self.current_preview_color,
            "preview_opacity": preview_opacity
        }
        
        try:
            os.makedirs("Save/Settings", exist_ok=True)
            with open("Save/Settings/theme.json", "w") as f:
                json.dump(theme_data, f)

            # Apply the theme dynamically
            from StartBot import apply_theme
            apply_theme()

            QMessageBox.information(self, "Theme Applied", f"The '{selected_theme.capitalize()}' theme has been applied.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save or apply theme.\n\nError: {e}")