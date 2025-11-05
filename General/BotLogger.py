import logging
from PyQt5.QtCore import QObject, pyqtSignal

class QtLogHandler(logging.Handler, QObject):
    """
    A custom logging handler that emits a PyQt signal for each log record.
    This allows log messages to be displayed in a GUI widget from any thread.
    """
    new_log_record = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        """Emits the formatted log record via a signal."""
        msg = self.format(record)
        self.new_log_record.emit(msg)

# --- Global Logger Setup ---

# Create a custom logger
bot_logger = logging.getLogger('BotLogger')
bot_logger.setLevel(logging.INFO)

# Create the Qt handler and add it to the logger
qt_handler = QtLogHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
qt_handler.setFormatter(formatter)
bot_logger.addHandler(qt_handler)