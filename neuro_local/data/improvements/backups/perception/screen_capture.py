"""
Захват скриншотов с учетом DPI
"""
import mss
from PIL import Image
import sys


class ScreenCapture:
    """Захват экрана с поддержкой DPI"""
    
    def __init__(self):
        self.sct = mss.mss()
        self._setup_dpi()
        
    def _setup_dpi(self):
        """Настраивает DPI awareness для Windows"""
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI
            except Exception:
                pass  # Игнорируем если не удалось
                
    def take_screenshot(self) -> Image.Image:
        """Делает скриншот всего экрана"""
        monitor = self.sct.monitors[1]  # Главный монитор
        sct_img = self.sct.grab(monitor)
        
        # Конвертация в PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img
        
    def take_region_screenshot(self, region: tuple) -> Image.Image:
        """Скриншот области (x, y, width, height)"""
        x, y, width, height = region
        monitor = {"top": y, "left": x, "width": width, "height": height}
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img
        
    def get_screen_size(self) -> tuple:
        """Возвращает размер экрана (width, height)"""
        monitor = self.sct.monitors[1]
        return monitor["width"], monitor["height"]
