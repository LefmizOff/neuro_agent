"""
Детектор UI элементов на скриншотах.

Использует OpenCV для поиска кнопок, полей и других элементов.
"""

import logging
from typing import List, Dict, Any, Optional
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class UIDetector:
    """Детектор UI элементов."""
    
    def __init__(self):
        self._templates_dir = None  # TODO: Загрузить шаблоны
        logger.info("UIDetector инициализирован")
    
    def detect_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Детектирует UI элементы на изображении.
        
        Returns:
            Список элементов с координатами и типами
        """
        # Базовая эвристика - поиск прямоугольных областей
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        elements = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Фильтруем слишком маленькие и большие
            if 20 < w < 500 and 20 < h < 300:
                aspect_ratio = w / h
                element_type = self._classify_element(w, h, aspect_ratio)
                
                elements.append({
                    "type": element_type,
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "confidence": 0.5  # TODO: Улучшить оценку
                })
        
        return elements[:20]  # Ограничиваем количество
    
    def _classify_element(self, w: int, h: int, aspect_ratio: float) -> str:
        """Классифицирует тип элемента по размерам."""
        if aspect_ratio > 3:
            return "button"
        elif aspect_ratio > 1.5:
            return "input_field"
        elif h > w * 2:
            return "scrollbar"
        else:
            return "unknown"
    
    def match_template(
        self,
        image: Image.Image,
        template: np.ndarray,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Ищет шаблон на изображении."""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        if len(template.shape) == 3:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        matches = []
        for pt in zip(*loc[::-1]):
            matches.append({
                "bbox": {
                    "x": int(pt[0]),
                    "y": int(pt[1]),
                    "width": template.shape[1],
                    "height": template.shape[0]
                },
                "confidence": float(res[pt[1], pt[0]])
            })
        
        return matches
