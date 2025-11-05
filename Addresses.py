import ctypes as c
import os
import threading
import importlib.util
import win32gui
import win32process

from Functions.MemoryFunctions import enable_debug_privilege_pywin32

enable_debug_privilege_pywin32()
# Keystrokes codes
lParam = [
    0X00480001, 0x00500001, 0X004D0001,  # 8, 2, 6
    0X004B0001, 0X00490001, 0X00470001,  # 4, 9, 7
    0X00510001, 0X004F0001  # 3, 1
]
rParam = [
    0X26, 0x28, 0X27,  # 8, 2, 6
    0x25, 0x21, 0x24,  # 4, 9, 7
    0x22, 0x23  # 3, 1
]

# Locks
walker_Lock = threading.Lock()

# There is 6 types of values
# 1 Byte - 1 byte
# 2 Short - 2 byte
# 3 Int - 4 bytes
# 4 Long - 8 bytes
# 5 Double - Floating point number
# 6 String - Decoding with UTF-8

# Character Addresses
my_x_address = None
my_x_address_offset = None
my_x_type = 3

my_y_address = None
my_y_address_offset = None
my_y_type = 3

my_z_address = None
my_z_address_offset = None
my_z_type = 2

my_stats_address = None

my_hp_offset = None
my_hp_max_offset = None
my_hp_type = 2

my_mp_offset = None
my_mp_max_offset = None
my_mp_type = 2

my_speed_offset = None
my_speed_type = 2



# Target Addresses
attack_address = None
attack_address_offset = None
my_attack_type = 3

target_x_offset = None
target_x_type = 3

target_y_offset = None
target_y_type = 3

target_z_offset = None
target_z_type = 2

target_hp_offset = None
target_hp_type = 1

target_name_offset = None
target_name_type = 6

# Battle List Addresses
battle_list_start = None
battle_list_offset = None
battle_list_step = None
battle_list_max_creatures = None
battle_list_creature_id_offset = None
battle_list_creature_name_offset = None
battle_list_is_visible_offset = None


# Game Variables
game_name = None
game = None
base_address = None
process_handle = None
proc_id = None
client_name = None
square_size = 75
application_architecture = 32
collect_threshold = 0.8

# Coordinates
screen_x = [0] * 1
screen_y = [0] * 1
battle_x = [0] * 1
battle_y = [0] * 1
screen_width = [0] * 1
screen_height = [0] * 1
coordinates_x = [0] * 12
coordinates_y = [0] * 12

fishing_x = [0] * 4
fishing_y = [0] * 4

# Other Variables
item_list = {}


# Your OTS Client
def load_client(client_file_name: str) -> None:
    """
    Loads the client configuration from the specified file into the global variables of this module.
    """
    global my_x_address, my_x_address_offset, my_y_address, my_y_address_offset, my_z_address, my_z_address_offset,\
        my_x_type, my_y_type, my_z_type, my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        my_hp_type, my_mp_type, my_speed_offset, my_speed_type, attack_address, attack_address_offset, my_attack_type, target_name_offset, target_x_offset, \
        target_y_offset, target_z_offset, target_hp_offset, target_x_type, target_y_type, target_z_type, target_hp_type, \
        target_name_type, battle_list_start, battle_list_offset, battle_list_step, battle_list_max_creatures, \
        battle_list_creature_id_offset, battle_list_creature_name_offset, battle_list_is_visible_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        square_size, application_architecture, collect_threshold

    # Dynamically load the configuration module
    config_path = os.path.join("ClientConfigs", client_file_name)
    spec = importlib.util.spec_from_file_location(client_file_name.replace('.py', ''), config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module specification for {client_file_name}")

    client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client_module) # type: ignore

    # Get config dictionary
    config = client_module.get_config()

    # Assign all variables from the config dictionary to globals
    for key, value in config.items():
        globals()[key] = value

    # Validate that client_name was loaded before trying to use it
    if client_name is None:
        raise ValueError(f"Configuration file '{client_file_name}' is missing the 'client_name' key.")

    # Game 'n' Client names (this part remains as it depends on the loaded config)
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)

    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    if not game:
        raise Exception(f"Could not find game window for client '{client_name}'. Is the game running?")

    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    if not modules:
        raise Exception("Could not enumerate process modules. Please try running the bot as an administrator.")

    base_address = modules[0]


def get_client_config_dict(client_file_name: str) -> dict:
    """
    Dynamically loads a client configuration file and returns its config dictionary.
    """
    config_path = os.path.join("ClientConfigs", client_file_name)
    spec = importlib.util.spec_from_file_location(client_file_name.replace('.py', ''), config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module specification for {client_file_name}")

    client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client_module)

    # Get config dictionary from the loaded module
    return client_module.get_config()


def fin_window_name(name) -> str:
    matching_titles = []

    def enum_window_callback(hwnd, _):
        window_text = win32gui.GetWindowText(hwnd)
        if name in window_text and "IglaBot" not in window_text:
            matching_titles.append(window_text)

    win32gui.EnumWindows(enum_window_callback, None)
    if not matching_titles:
        raise Exception(f"Could not find any window with '{name}' in the title. Is the game client running?")
    
    # If multiple windows match, this will return the first one found.
    return matching_titles[0]

def update_window_dimensions():
    """
    Updates the global screen coordinate variables based on the current game window handle.
    """
    global screen_x, screen_y, screen_width, screen_height
    if game:
        rect = win32gui.GetWindowRect(game)
        x, y, width, height = rect
        screen_x[0] = x
        screen_y[0] = y
        screen_width[0] = width
        screen_height[0] = height

def populate_keys_combobox(combobox, include_special_actions=None):
    """
    Populates a QComboBox with a structured and grouped list of keyboard keys.
    """
    if include_special_actions is None:
        include_special_actions = []

    combobox.clear()

    # --- Function Keys ---
    for i in range(1, 13):
        combobox.addItem(f"F{i}")
    combobox.insertSeparator(combobox.count())

    # --- Number Keys ---
    for i in range(10):
        combobox.addItem(str(i))
    combobox.insertSeparator(combobox.count())

    # --- Letter Keys ---
    for i in range(ord('A'), ord('Z') + 1):
        combobox.addItem(chr(i))
    combobox.insertSeparator(combobox.count())

    # --- Other Common Keys ---
    combobox.addItems(["Space", "Enter", "Shift", "Ctrl", "Alt", "Tab"])

    # --- Special Actions (if any) ---
    if include_special_actions:
        combobox.insertSeparator(combobox.count())
        combobox.addItems(include_special_actions)

# User Interface
dark_theme = """
     QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QMainWindow, QDialog {
        background-color: #2b2b2b;
    }
    QTabWidget::pane {
        border: 1px solid #444;
        border-radius: 4px;
    }
    QTabBar::tab {
        background: #2b2b2b;
        border: 1px solid #444;
        padding: 8px 20px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background: #3c3c3c;
        border-bottom-color: #3c3c3c;
    }
    QTabBar::tab:!selected:hover {
        background: #484848;
    }
    QPushButton {
        background-color: #4a4a4a;
        border: 1px solid #666;
        padding: 6px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
    }
    QPushButton:pressed {
        background-color: #646464;
    }
    QLineEdit, QTextEdit, QComboBox, QListWidget {
        background-color: #3c3c3c;
        border: 1px solid #666;
        padding: 4px;
        border-radius: 4px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #444;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
    }
    QCheckBox {
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 15px;
        height: 15px;
        border: 1px solid #777;
        border-radius: 3px;
    }
    QCheckBox::indicator:unchecked:hover {
        border: 1px solid #888;
    }
    QCheckBox::indicator:checked {
        background-color: #5e90f5;
        border: 1px solid #5e90f5;
    }
    QScrollBar:vertical {
        background-color: #2b2b2b;
        width: 12px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background-color: #555;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #777;
    }
"""

light_theme = """
    QWidget {
        background-color: #f0f0f0;
        color: #000000;
    }

    QMainWindow {
        background-color: #f0f0f0;
    }

    QTabWidget::pane {
        border: 1px solid #c5c5c5;
        border-radius: 5px;
    }

    QTabBar::tab {
        background: #e1e1e1;
        border: 1px solid #c5c5c5;
        padding: 8px 15px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }

    QTabBar::tab:selected {
        background: #f0f0f0;
        border-bottom-color: #f0f0f0;
    }

    QTabBar::tab:!selected:hover {
        background: #dcdcdc;
    }

    QPushButton {
        background-color: #e1e1e1;
        border: 1px solid #c5c5c5;
        color: #000000;
        padding: 6px;
        border-radius: 5px;
    }

    QPushButton:hover {
        background-color: #dcdcdc;
    }

    QPushButton:pressed {
        background-color: #c5c5c5;
    }

    QLineEdit, QTextEdit, QComboBox, QListWidget {
        background-color: #ffffff;
        border: 1px solid #c5c5c5;
        color: #000000;
        padding: 3px;
        border-radius: 5px;
    }

    QGroupBox {
        font-weight: bold;
        border: 1px solid #c5c5c5;
        border-radius: 5px;
        margin-top: 10px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
    }

    QCheckBox::indicator {
        border: 1px solid #777777;
    }

    QCheckBox::indicator:checked {
        background-color: #0078d7;
        border: 1px solid #0078d7;
    }
"""

tibian_theme = """
    QWidget {
        background-color: #3c3c3c; /* Dark brownish-gray */
        color: #e0e0e0; /* Light gray text */
    }

    QMainWindow, QDialog {
        background-color: #3c3c3c;
    }

    QTabWidget::pane {
        border: 1px solid #222222;
        border-radius: 5px;
        background-color: #464646; /* Slightly lighter pane */
    }

    QTabBar::tab {
        background: #3c3c3c;
        border: 1px solid #222222;
        padding: 8px 15px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        color: #aaaaaa; /* Dimmed text for non-selected tabs */
    }

    QTabBar::tab:selected {
        background: #464646;
        border-bottom-color: #464646; /* Make selected tab blend with pane */
        color: #ffffff; /* White text for selected tab */
        font-weight: bold;
    }

    QTabBar::tab:!selected:hover {
        background: #505050;
        color: #dddddd;
    }

    QPushButton {
        background-color: #5a5a5a;
        border: 1px solid #222222;
        color: #ffffff;
        padding: 6px;
        border-radius: 5px;
        border-style: outset; /* Tibia-like button style */
    }

    QPushButton:hover {
        background-color: #6a6a6a;
    }

    QPushButton:pressed {
        background-color: #707070;
        border-style: inset; /* Sunken button effect */
    }

    QLineEdit, QTextEdit, QComboBox, QListWidget {
        background-color: #2E2E2E; /* A very dark gray, almost black */
        border: 1px solid #222222;
        color: #ffffff;
        padding: 3px;
        border-radius: 5px;
    }

    QGroupBox {
        font-weight: bold;
        border: 1px solid #222222;
        border-radius: 5px;
        margin-top: 10px;
        background-color: #4a4a4a; /* Groupbox background */
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
        background-color: #4a4a4a;
        color: #ffffff;
    }

    QCheckBox::indicator:checked {
        background-color: #c88f32; /* Gold/yellow for checkmark */
        border: 1px solid #b87f22;
    }
"""
