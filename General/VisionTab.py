import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QCheckBox, QHBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtGui import QPainter, QColor, QPen, QIcon, QFont
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

import Addresses
from Functions.GeneralFunctions import WindowCapture


class VisionTab(QWidget):
    """
    A tab that allows the user to see what the bot sees by capturing
    and displaying the game window's content.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # --- Controls Layout ---
        controls_layout = QHBoxLayout()

        # --- Widgets ---
        self.refresh_button = QPushButton("Refresh View", self)
        self.refresh_button.setToolTip("Capture the current game window view.")
        self.refresh_button.setStyleSheet("color: white; background-color: #3498db; font-weight: bold; padding: 8px;")

        self.live_view_checkbox = QCheckBox("Live View (1 FPS)", self)
        self.live_view_checkbox.setToolTip("Automatically refresh the view every second.")

        self.show_hotkey_areas_checkbox = QCheckBox("Show Smart Hotkey Areas", self)
        self.show_hotkey_areas_checkbox.setToolTip("Draws the detection areas from the Smart Hotkeys tab.")

        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.live_view_checkbox)
        controls_layout.addWidget(self.show_hotkey_areas_checkbox)
        controls_layout.addStretch(1)

        # --- Main View Layout (Image + Legend) ---
        view_layout = QHBoxLayout()

        self.image_label = QLabel("Click the button to capture the game view.", self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480) # Set a reasonable minimum size
        self.image_label.setStyleSheet("border: 1px solid #555; background-color: #2E2E2E;")

        self.legend_list_widget = QListWidget()
        self.legend_list_widget.setToolTip("Legend for the Smart Hotkey areas shown on the screenshot.")
        self.legend_list_widget.setFixedWidth(200)
        self.legend_list_widget.hide() # Initially hidden

        view_layout.addWidget(self.image_label, 1) # Give image label more stretch factor
        view_layout.addWidget(self.legend_list_widget)

        # --- Timer for Live View ---
        self.view_timer = QTimer(self)
        self.view_timer.setInterval(1000) # 1000 ms = 1 second

        # --- Add Widgets to Layout ---
        layout.addLayout(controls_layout)
        layout.addLayout(view_layout)

        # --- Connections ---
        self.refresh_button.clicked.connect(self.update_game_view)
        self.live_view_checkbox.stateChanged.connect(self.toggle_live_view)
        self.show_hotkey_areas_checkbox.stateChanged.connect(lambda state: self.legend_list_widget.setVisible(state == Qt.Checked))
        self.view_timer.timeout.connect(self.update_game_view)

    def update_game_view(self):
        if not Addresses.game:
            QMessageBox.warning(self, "Error", "Game window not found. Please load a client first.")
            return

        try:
            # Ensure window dimensions are up-to-date before capturing
            Addresses.update_window_dimensions()

            # Get client area dimensions, as PrintWindow will capture only this part.
            client_rect = Addresses.win32gui.GetClientRect(Addresses.game)
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]

            capture = WindowCapture(
                client_width,
                client_height,
                0, # x and y are not used by PrintWindow, but kept for class structure
                0  # y
            )
            screenshot = capture.get_screenshot() # Returns a NumPy array (BGR)

            # Convert from OpenCV's BGR to Qt's RGB format
            rgb_image = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Draw Smart Hotkey areas if the checkbox is checked
            if self.show_hotkey_areas_checkbox.isChecked():
                pixmap = self.draw_smart_hotkey_areas(pixmap)

            # Scale pixmap to fit the label while maintaining aspect ratio
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        except Exception as e:
            self.image_label.setText(f"Failed to capture view.\nError: {e}")
            print(f"Error in update_game_view: {e}")

    def draw_smart_hotkey_areas(self, pixmap: QPixmap) -> QPixmap:
        """Draws rectangles on the pixmap for each Smart Hotkey rule."""
        smart_hotkeys_tab = getattr(self.main_window, 'smart_hotkeys_tab', None)
        if not smart_hotkeys_tab:
            return pixmap

        hotkey_list = smart_hotkeys_tab.hotkey_list_widget
        self.legend_list_widget.clear()

        # ----- Colors for the legend -----
        legend_colors = [
            QColor("#ff0000"), QColor("#00ff00"), QColor("#0000ff"), QColor("#ffff00"),
            QColor("#ff00ff"), QColor("#00ffff"), QColor("#ff8000"), QColor("#8000ff")
        ]

        painter = QPainter(pixmap)
        font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(font)

        for i in range(hotkey_list.count()):
            item = hotkey_list.item(i)
            data = item.data(Qt.UserRole)

            # The coordinates are saved relative to the client area.
            # Since the screenshot is now *only* the client area, no offset is needed.
            x1, y1, x2, y2 = data['x1'], data['y1'], data['x2'], data['y2']
            width, height = x2 - x1, y2 - y1

            # ----- Drawing -----
            color = legend_colors[i % len(legend_colors)]
            pen = QPen(color, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x1, y1, width, height)

            # Number in the top-left corner of the rectangle
            painter.setPen(QPen(Qt.white))
            painter.drawText(x1 + 4, y1 + 14, str(i + 1))

            # ----- Legend -----
            legend_item = QListWidgetItem(f" {i + 1}. {data.get('name', 'Unnamed Rule')}")
            legend_item.setIcon(self.create_color_icon(color))
            self.legend_list_widget.addItem(legend_item)

        painter.end()
        return pixmap

    def toggle_live_view(self, state):
        """Starts or stops the timer based on the checkbox state."""
        if state == Qt.Checked:
            self.view_timer.start()
        else:
            self.view_timer.stop()

    def create_color_icon(self, color: QColor) -> QIcon:
        """Creates a square QIcon of a given color."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        return QIcon(pixmap)