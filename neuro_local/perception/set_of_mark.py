"""
Заглушки для недостающих модулей восприятия
"""
from PIL import Image
from typing import List, Dict, Any


class UIDetector:
    """Детектор UI элементов (заглушка)"""
    
    def detect_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Обнаруживает UI элементы"""
        # TODO: Реализовать детекцию через OpenCV эвристики
        return []


class SetOfMark:
    """Set-of-Mark разметка (заглушка)"""
    
    def mark_elements(self, image: Image.Image, elements: List[Dict[str, Any]]) -> Image.Image:
        """Добавляет метки к элементам"""
        # TODO: Реализовать рисование рамок и номеров
        return image.copy()
