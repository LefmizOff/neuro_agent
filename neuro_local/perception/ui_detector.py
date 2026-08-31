"""
Заглушка для UIDetector
"""
from PIL import Image
from typing import List, Dict, Any


class UIDetector:
    """Детектор UI элементов (заглушка)"""
    
    def detect_ui_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Обнаруживает UI элементы"""
        # TODO: Реализовать детекцию через OpenCV эвристики
        return []
