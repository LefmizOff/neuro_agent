"""
Модуль захвата скриншотов экрана.

Использует mss для быстрого захвата и Pillow для обработки.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
import mss
import mss.tools
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Захват скриншотов экрана.
    
    Поддерживает:
    - Захват полного экрана
    - Захват области
    - Захват конкретного монитора
    - Сохранение в файл
    """
    
    def __init__(self, save_dir: str = "data/screenshots"):
        """
        Инициализация захвата скриншотов.
        
        Args:
            save_dir: Директория для сохранения скриншотов
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self._sct = mss.mss()
        self.monitors = self._sct.monitors
        
        logger.info(f"ScreenCapture инициализирован: {len(self.monitors)-1} мониторов")
    
    def get_primary_monitor(self) -> Dict[str, int]:
        """Возвращает информацию о первичном мониторе."""
        return self.monitors[1] if len(self.monitors) > 1 else self.monitors[0]
    
    def capture_full(
        self,
        monitor: int = 1,
        save: bool = False,
        filename: Optional[str] = None
    ) -> Image.Image:
        """
        Захватывает полный экран.
        
        Args:
            monitor: Номер монитора (1 - первичный, 0 - все мониторы)
            save: Сохранить в файл
            filename: Имя файла (если None, генерируется автоматически)
            
        Returns:
            PIL Image со скриншотом
        """
        try:
            # Выбираем монитор
            if monitor == 0 or monitor >= len(self.monitors):
                mon = self.monitors[0]  # Все мониторы
            else:
                mon = self.monitors[monitor]
            
            # Делаем скриншот
            screenshot = self._sct.grab(mon)
            
            # Конвертируем в PIL Image
            img = Image.frombytes(
                'RGB',
                screenshot.size,
                screenshot.bgra,
                'raw',
                'BGRX'
            )
            
            # Сохраняем если нужно
            if save:
                self._save_image(img, filename)
            
            return img
            
        except Exception as e:
            logger.error(f"Ошибка захвата экрана: {e}")
            raise
    
    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        save: bool = False,
        filename: Optional[str] = None
    ) -> Image.Image:
        """
        Захватывает область экрана.
        
        Args:
            x: Координата X левого верхнего угла
            y: Координата Y левого верхнего угла
            width: Ширина области
            height: Высота области
            save: Сохранить в файл
            filename: Имя файла
            
        Returns:
            PIL Image с областью
        """
        try:
            # Определяем область захвата
            monitor = {
                "left": x,
                "top": y,
                "width": width,
                "height": height
            }
            
            # Делаем скриншот
            screenshot = self._sct.grab(monitor)
            
            # Конвертируем в PIL Image
            img = Image.frombytes(
                'RGB',
                screenshot.size,
                screenshot.bgra,
                'raw',
                'BGRX'
            )
            
            # Сохраняем если нужно
            if save:
                self._save_image(img, filename)
            
            return img
            
        except Exception as e:
            logger.error(f"Ошибка захвата области: {e}")
            raise
    
    def capture_around_point(
        self,
        x: int,
        y: int,
        width: int = 500,
        height: int = 500,
        save: bool = False
    ) -> Image.Image:
        """
        Захватывает область вокруг точки.
        
        Args:
            x: Координата X центра
            y: Координата Y центра
            width: Ширина области
            height: Высота области
            save: Сохранить в файл
            
        Returns:
            PIL Image с областью
        """
        # Вычисляем левый верхний угол
        left = max(0, x - width // 2)
        top = max(0, y - height // 2)
        
        return self.capture_region(left, top, width, height, save)
    
    def _save_image(
        self,
        img: Image.Image,
        filename: Optional[str] = None
    ) -> Path:
        """
        Сохраняет изображение в файл.
        
        Args:
            img: PIL Image
            filename: Имя файла (если None, генерируется по времени)
            
        Returns:
            Путь к сохранённому файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"screenshot_{timestamp}.png"
        
        filepath = self.save_dir / filename
        img.save(filepath, "PNG")
        logger.debug(f"Скриншот сохранён: {filepath}")
        
        return filepath
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию об экранах.
        
        Returns:
            Словарь с информацией о мониторах
        """
        info = {
            "num_monitors": len(self.monitors) - 1,
            "monitors": []
        }
        
        for i, mon in enumerate(self.monitors[1:], 1):
            info["monitors"].append({
                "index": i,
                "left": mon["left"],
                "top": mon["top"],
                "width": mon["width"],
                "height": mon["height"]
            })
        
        return info
    
    @property
    def screen_size(self) -> Tuple[int, int]:
        """Возвращает размер основного экрана (width, height)."""
        mon = self.get_primary_monitor()
        return (mon["width"], mon["height"])
