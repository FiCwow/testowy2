from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QGroupBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from .BotLogger import qt_handler
from .CustomDelegates import RichTextDelegate

class LogsTab(QWidget):
    """
    A tab to display real-time log messages from the bot's operations.
    """
    def __init__(self):
        super().__init__()

        # --- Layout ---
        layout = QVBoxLayout(self)
        log_group = QGroupBox("📜 Bot Activity Log")
        log_layout = QVBoxLayout(log_group)

        # --- Widgets ---
        self.log_list_widget = QListWidget()
        self.log_list_widget.setWordWrap(True)
        self.log_list_widget.setItemDelegate(RichTextDelegate(self.log_list_widget))

        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.log_list_widget.clear)

        log_layout.addWidget(self.log_list_widget)
        log_layout.addWidget(clear_button)
        layout.addWidget(log_group)

        # --- Connections ---
        qt_handler.new_log_record.connect(self.log_list_widget.addItem)

        self.log_list_widget.addItem("<b>Welcome to IglaBot!</b> The log is ready.")