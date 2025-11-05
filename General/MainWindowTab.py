from PyQt5.QtCore import Qt

import json
import Addresses
import win32gui
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QApplication, QTabWidget, QLabel, QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QIcon, QFont
from HealAttack.HealingAttackTab import HealingTab

from Target.TargetLootTab import TargetLootTab
from LooterTab import LooterTab
from Settings.SettingsTab import SettingsTab
from Training.TrainingTab import TrainingTab
from .CharacterStatusWidget import CharacterStatusWidget
from .AppearanceTab import AppearanceTab
from ProfileSetsTab import ProfileSetsTab
from .LogsTab import LogsTab
from .VisionTab import VisionTab
from Settings.ProfileManagerWidget import ProfileManagerWidget
from Walker.WalkerTab import WalkerTab


class MainWindowTab(QWidget):
    # This needs to be defined before initTabs
    try:
        from SmartHotkeys.SmartHotkeysTab import SmartHotkeysTab
    except ImportError:
        print("Warning: SmartHotkeysTab module not found. The tab will be disabled.")
        SmartHotkeysTab = None

    try:
        from ProfileSetsTab import ProfileSetsTab
    except ImportError:
        print("Warning: ProfileSetsTab module not found. The tab will be disabled.")
        ProfileSetsTab = None

    def __init__(self):
        super().__init__()

        # Handle closing
        if QApplication.instance():
            QApplication.instance().aboutToQuit.connect(self.on_close)

        # Load Icon
        self.setWindowIcon(QIcon('Images/Icon.jpg'))
        # Set Title and Size
        self.setWindowTitle("IglaBot Control Panel")

        # Layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Title Label
        title_label = QLabel("IglaBot")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        # --- Character Status Widget ---
        self.status_widget = CharacterStatusWidget()
        main_layout.addWidget(self.status_widget)


        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- System Tray Icon ---
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('Images/Icon.jpg'))
        self.tray_icon.setToolTip("IglaBot Control Panel")

        # Create context menu
        tray_menu = QMenu()
        show_action = QAction("Show / Hide", self)
        exit_action = QAction("Exit", self)

        show_action.triggered.connect(self.toggle_visibility)
        exit_action.triggered.connect(self.exit_application)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Handle tray icon activation (left-click)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def initTabs(self):
        """Initializes and adds all tabs to the main window."""
        self.healing_tab = HealingTab()
        self.target_tab = TargetLootTab()
        self.looter_tab = LooterTab()
        self.walker_tab = WalkerTab()
        self.training_tab = TrainingTab()
        if MainWindowTab.SmartHotkeysTab:
            self.smart_hotkeys_tab = MainWindowTab.SmartHotkeysTab()
        self.appearance_tab = AppearanceTab()
        self.settings_tab = SettingsTab()
        self.logs_tab = LogsTab()
        self.vision_tab = VisionTab(self) # Pass the main window instance
        if MainWindowTab.ProfileSetsTab:
            self.profile_sets_tab = MainWindowTab.ProfileSetsTab(self)

        self.tabs.addTab(self.healing_tab, "⚕️ Healing & Attack")
        self.tabs.addTab(self.target_tab, "🎯 Targeting")
        self.tabs.addTab(self.logs_tab, "📜 Logs")
        self.tabs.addTab(self.looter_tab, "💰 Looter")
        self.tabs.addTab(self.vision_tab, "👁️ Vision")
        self.tabs.addTab(self.walker_tab, "🚶 Walker")
        self.tabs.addTab(self.training_tab, "💪 Training")
        if MainWindowTab.SmartHotkeysTab and hasattr(self, 'smart_hotkeys_tab'):
            self.tabs.addTab(self.smart_hotkeys_tab, "⚡ Smart Hotkeys")
        if MainWindowTab.ProfileSetsTab and hasattr(self, 'profile_sets_tab'):
            self.tabs.addTab(self.profile_sets_tab, "📚 Profile Sets")
        self.tabs.addTab(self.appearance_tab, "🎨 Appearance")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")


    def on_close(self):
        if Addresses.game:
            win32gui.SetWindowText(Addresses.game, Addresses.game_name)

        # Check if auto-save is enabled
        try:
            with open("Save/Settings/theme.json", "r") as f:
                settings = json.load(f)
                if not settings.get("autosave", False):
                    return

        except (FileNotFoundError, json.JSONDecodeError):
            return # If settings file doesn't exist or is invalid, do nothing

        # List of all tabs that might have threads or need saving
        tabs_with_profiles = [
            getattr(self, 'target_tab', None),
            getattr(self, 'healing_tab', None),
            getattr(self, 'looter_tab', None),
            getattr(self, 'walker_tab', None),
            getattr(self, 'training_tab', None),
            getattr(self, 'settings_tab', None),
            getattr(self, 'smart_hotkeys_tab', None)
        ]

        for tab in filter(None, tabs_with_profiles):
            # Find ProfileManagerWidget to save profile
            profile_manager = tab.findChild(ProfileManagerWidget)
            if profile_manager and hasattr(profile_manager, 'save_profile'):
                profile_manager.save_profile(autosave=True)

            # Stop all threads in the tab
            if hasattr(tab, 'stop_all_threads'):
                tab.stop_all_threads()


    def exit_application(self):
        """Properly exits the application."""
        self.tray_icon.hide()
        # Stop all tab threads and perform auto-save if enabled
        self.on_close()

        # Stop the status widget's thread
        if hasattr(self, 'status_widget'):
            self.status_widget.stop_thread()

        QApplication.instance().quit()

    def toggle_visibility(self):
        """Shows or hides the main window."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def on_tray_icon_activated(self, reason):
        """Handle clicks on the tray icon."""
        if reason == QSystemTrayIcon.Trigger:  # Left-click
            self.toggle_visibility()

    def closeEvent(self, event):
        """Override the close event to hide the window to the system tray."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Confirm Action')
        msg_box.setText("What do you want to do?")
        msg_box.setIcon(QMessageBox.Question)
        
        # Add buttons with custom text
        minimize_button = msg_box.addButton('Minimize to Tray', QMessageBox.AcceptRole)
        exit_button = msg_box.addButton('Exit Application', QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton('Cancel', QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(cancel_button)
        msg_box.exec_()

        if msg_box.clickedButton() == minimize_button:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("IglaBot is still running", "The application has been minimized to the system tray.", QSystemTrayIcon.Information, 2000)
        elif msg_box.clickedButton() == exit_button:
            self.exit_application()
        else:  # Cancel
            event.ignore()