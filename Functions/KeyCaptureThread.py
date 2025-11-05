import keyboard
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QComboBox


class KeyCaptureThread(QThread):
    """
    A thread that listens for a single key press and emits the key name.
    """
    key_captured = pyqtSignal(str)

    def __init__(self, button: QPushButton, combobox: QComboBox):
        super().__init__()
        self.button = button
        self.combobox = combobox
        self.original_text = self.button.text()

    def run(self):
        """
        Waits for a key press, captures it, and emits the signal.
        """
        self.button.setText("Press a key...")
        self.button.setEnabled(False)

        try:
            # Wait for the next key event
            key_event = keyboard.read_event(suppress=True)
            if key_event.event_type == keyboard.KEY_DOWN:
                key_name = self.format_key_name(key_event.name)
                self.key_captured.emit(key_name)
        except Exception as e:
            print(f"Error capturing key: {e}")
        finally:
            # Restore button state
            self.button.setText(self.original_text)
            self.button.setEnabled(True)

    def format_key_name(self, name: str) -> str:
        """
        Formats the key name from the 'keyboard' library to match the QComboBox content.
        e.g., 'f1' -> 'F1', 'space' -> 'Space', 'a' -> 'A'
        """
        if name.startswith('f') and name[1:].isdigit():
            return name.upper()
        if len(name) == 1 and name.isalpha():
            return name.upper()
        return name.capitalize()