from PyQt5.QtWidgets import QApplication
import Addresses
import os
import json
import textwrap
import logging

from General.SelectTibiaTab import SelectTibiaTab


def ensure_default_config_exists():
    """
    Checks if the default 'IglaOTS.py' config exists, and creates it if not.
    This ensures there is always a template for creating new clients.
    """
    config_dir = "ClientConfigs"
    default_config_path = os.path.join(config_dir, "IglaOTS.py")

    if not os.path.exists(default_config_path):
        print("Default config 'IglaOTS.py' not found. Creating it.")
        default_config_content = textwrap.dedent("""
            def get_config():
                return {
                    'square_size': 60, 'application_architecture': 64, 'collect_threshold': 0.85, 'client_name': "Tibia -",
                    'my_x_address': 0x019C6628, 'my_x_address_offset': [0x510, 0x60], 'my_x_type': 3,
                    'my_y_address': 0x019C6628, 'my_y_address_offset': [0x510, 0x64], 'my_y_type': 3,
                    'my_z_address': 0x019C6628, 'my_z_address_offset': [0x510, 0x68], 'my_z_type': 2,
                    'my_stats_address': 0x019C6628,
                    'my_hp_offset': [0xD8, 0x18], 'my_hp_max_offset': [0xD8, 0x1C], 'my_hp_type': 2,
                    'my_mp_offset': [0xD8, 0x60], 'my_mp_max_offset': [0xD8, 0x64], 'my_mp_type': 2,
                    'my_speed_offset': [0xD8, 0x78], 'my_speed_type': 2,
                    'attack_address': 0x019C6628, 'attack_address_offset': [0x2C0, 0x2C], 'my_attack_type': 3,
                    'target_x_offset': 0x38, 'target_x_type': 3,
                    'target_y_offset': 0x3C, 'target_y_type': 3,
                    'target_z_offset': 0x40, 'target_z_type': 2,
                    'target_hp_offset': 0xE8, 'target_hp_type': 1,
                    'target_name_offset': 0xA8, 'target_name_type': 6
                }
        """)
        with open(default_config_path, "w") as f:
            f.write(default_config_content)

def get_theme_stylesheet():
    """Reads the theme setting and returns the corresponding QSS stylesheet."""
    try:
        with open("Save/Settings/theme.json", "r") as f:
            data = json.load(f)
            theme_choice = data.get("theme", "tibian")
            font_family = data.get("font_family", "Segoe UI")
            font_size = data.get("font_size", 9)
    except (FileNotFoundError, json.JSONDecodeError):
        theme_choice = "tibian"
        font_family = "Segoe UI"
        font_size = 9

    base_stylesheet = ""
    if theme_choice == "light":
        base_stylesheet = Addresses.light_theme
    elif theme_choice == "tibian":
        base_stylesheet = Addresses.tibian_theme
    elif theme_choice == "custom":
        try:
            with open("Save/Settings/custom_theme.qss", "r") as custom_f:
                base_stylesheet = custom_f.read()
        except FileNotFoundError:
            print("Warning: 'custom_theme.qss' not found. Falling back to dark theme.")
            base_stylesheet = Addresses.dark_theme
    else: # Default to dark
        base_stylesheet = Addresses.dark_theme

    font_style = f"QWidget {{ font-family: '{font_family}'; font-size: {font_size}pt; }}"
    return font_style + base_stylesheet

def apply_theme():
    """Applies the currently selected theme to the entire application."""
    stylesheet = get_theme_stylesheet()
    app = QApplication.instance()
    if app:
        app.setStyleSheet(stylesheet) # type: ignore

def setup_logging():
    """Configures logging to save exceptions to a file."""
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "error.log")

    # Configure logging
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a' # Append to the log file
    )

def main():
    # Make directories
    os.makedirs("Images", exist_ok=True)
    os.makedirs("ClientConfigs", exist_ok=True)
    os.makedirs("Save", exist_ok=True)
    os.makedirs("Save/Targeting", exist_ok=True)
    os.makedirs("Save/Settings", exist_ok=True)
    os.makedirs("Save/Waypoints", exist_ok=True)
    os.makedirs("Save/HealingAttack", exist_ok=True)
    os.makedirs("Save/Training", exist_ok=True)

    # Setup logging before anything else
    setup_logging()

    ensure_default_config_exists()
    
    app = QApplication([])
    # Set organization and application name for QSettings
    app.setOrganizationName("IglaBot")
    app.setApplicationName("IglaBot")

    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)  # Prevent app from closing when window is hidden
    app.setStyleSheet(get_theme_stylesheet())
    login_window = SelectTibiaTab()
    login_window.show()

    try:
        app.exec()
    except Exception as e:
        logging.exception("An unhandled exception occurred")
        print(f"Unhandled exception: {e}")


if __name__ == '__main__':
    main()