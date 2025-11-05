import io
import urllib
import ctypes as c
import win32con

import requests
import win32con
import win32gui
import win32ui
from PIL import Image, ImageSequence, ImageFile
import numpy as np
import cv2 as cv
from PyQt5.QtCore import Qt
from bs4 import BeautifulSoup

import Addresses
import os
import json


def load_items_images(list_widget) -> None:
    zoom_img = 3
    Addresses.item_list = {}
    for item_index in range(list_widget.count()):
        item_name = list_widget.item(item_index).text()
        item_data = list_widget.item(item_index).data(Qt.UserRole)
        loot_container = item_data['Loot']
        item = Image.open(f'Images/{Addresses.client_name}/{item_name}.png').convert('RGBA')
        item = np.array(item)
        item = item[:22, :, :]
        item = cv.cvtColor(item, cv.COLOR_BGR2GRAY)
        item = cv.GaussianBlur(item, (7, 7), 0)
        item = cv.resize(item, None, fx=zoom_img, fy=zoom_img, interpolation=cv.INTER_CUBIC)
        Addresses.item_list[item_name] = []
        Addresses.item_list[item_name].append(item)
        Addresses.item_list[item_name].append(loot_container)


def merge_close_points(points, distance_threshold):
    merged_points = []
    merged_indices = set()

    def merge_distance(point1, point2):
        return np.sqrt(np.sum((point1 - point2) ** 2))
    for i in range(len(points)):
        if i not in merged_indices:
            current_point = points[i]
            merged_point = np.array(current_point)
            for j in range(i + 1, len(points)):
                if merge_distance(np.array(current_point), np.array(points[j])) < distance_threshold:
                    merged_point = (merged_point + np.array(points[j])) / 2
                    merged_indices.add(j)
            merged_points.append(tuple(merged_point))
    return merged_points


class WindowCapture:
    def __init__(self, w, h, x, y):
        self.hwnd = win32gui.FindWindow(None, Addresses.game_name)
        self.w = w
        self.h = h
        self.x = x
        self.y = y

        # Define CAPTUREBLT if it's not in win32con
        if not hasattr(win32con, 'CAPTUREBLT'):
            win32con.CAPTUREBLT = 0x40000000

    def get_screenshot(self):
        # This implementation uses PrintWindow, which can capture window content
        # even if it's minimized or obscured. We will switch to BitBlt with CAPTUREBLT
        # for better compatibility with game clients.

        # Validate dimensions to prevent crash on zero-sized window
        if self.w <= 0 or self.h <= 0:
            raise ValueError(f"Invalid capture dimensions: width={self.w}, height={self.h}")

        wDC = win32gui.GetWindowDC(self.hwnd)
        dc_obj = win32ui.CreateDCFromHandle(wDC)
        cDC = dc_obj.CreateCompatibleDC()
        data_bitmap = win32ui.CreateBitmap()
        data_bitmap.CreateCompatibleBitmap(dc_obj, self.w, self.h)
        cDC.SelectObject(data_bitmap)
        
        # Use PrintWindow for a more reliable capture of the window content, avoiding BitBlt offset issues.
        # The last parameter (1) specifies to capture the client area.
        result = c.windll.user32.PrintWindow(self.hwnd, cDC.GetSafeHdc(), 1)
        
        signed_ints_array = data_bitmap.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (self.h, self.w, 4)
        dc_obj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(data_bitmap.GetHandle())

        img = img[..., :3]
        img = np.ascontiguousarray(img)
        return img


def delete_item(list_widget, item) -> None:
    index = list_widget.row(item)
    list_widget.takeItem(index)


def manage_profile(action: str, directory: str, profile_name: str, data: dict = None, new_name: str = None):
    file_path = os.path.join(directory, f"{profile_name}.json")
    if action.lower() == "save":
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    elif action.lower() == "load":
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r") as f:
            return json.load(f)
    elif action.lower() == "delete":
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    elif action.lower() == "rename":
        if new_name:
            new_file_path = os.path.join(directory, f"{new_name}.json")
            if os.path.exists(file_path) and not os.path.exists(new_file_path):
                os.rename(file_path, new_file_path)
                return True
        return False
    return False
