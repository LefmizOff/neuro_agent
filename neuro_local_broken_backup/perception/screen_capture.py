"""
Модуль захвата экрана для Neuro Local агента
Исправлено: DPI awareness для Windows
"""
import mss
from PIL import Image
from typing import Tuple
import sys


class ScreenCapture:
    """Класс для захвата скриншотов экрана"""
    def __init__(self):
        self.sct = mss.mss()
        self._setup_dpi_awareness()
        
    def _setup_dpi_awareness(self):
        """Настраивает DPI awareness для корректных координат на Windows"""
        if sys.platform == 'win32':
            try:
                import ctypes
                # PROCESS_PER_MONITOR_DPI_AWARE = 3
                ctypes.windll.shcore.SetProcessDpiAwareness(3)
            except Exception as e:
                print(f"Warning: Не удалось настроить DPI awareness: {e}")
        
    def take_screenshot(self) -> Image.Image:
        """
        Делает скриншот всего экрана
        
        Returns:
            PIL Image объект скриншота
        """
        monitor = self.sct.monitors[1]
        sct_img = self.sct.grab(monitor)
        
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img
        
    def take_region_screenshot(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """
        Делает скриншот определенной области экрана
        
        Args:
            region: Кортеж (x, y, width, height) для области захвата
            
        Returns:
            PIL Image объект скриншота
        """
        x, y, width, height = region
        monitor = {"top": y, "left": x, "width": width, "height": height}
        sct_img = self.sct.grab(monitor)
        
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img
        
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Возвращает размеры экрана
        
        Returns:
            Кортеж (ширина, высота)
        """
        monitor = self.sct.monitors[1]
        return monitor["width"], monitor["height"]
        
    def get_physical_screen_size(self) -> Tuple[int, int]:
        """
        Возвращает физические размеры экрана с учетом DPI
        
        Returns:
            Кортеж (ширина, высота)
        """
        return self.get_screen_size()
