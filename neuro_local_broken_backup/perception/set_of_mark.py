"""
Set-of-Mark разметка для VLM.

Добавляет рамки и номера к UI элементам на скриншоте.
"""

import logging
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np

logger = logging.getLogger(__name__)


class SetOfMarker:
    """Разметка Set-of-Mark для изображений."""
    
    def __init__(self):
        self._colors = [
            (255, 0, 0),      # Красный
            (0, 255, 0),      # Зелёный
            (0, 0, 255),      # Синий
            (255, 255, 0),    # Жёлтый
            (255, 0, 255),    # Пурпурный
            (0, 255, 255),    # Голубой
            (255, 128, 0),    # Оранжевый
            (128, 0, 255),    # Фиолетовый
        ]
        logger.info("SetOfMarker инициализирован")
    
    def mark_elements(
        self,
        image: Image.Image,
        elements: List[Dict[str, Any]],
        max_elements: int = 20
    ) -> Tuple[Image.Image, str]:
        """
        Добавляет рамки и номера к элементам.
        
        Args:
            image: Исходное изображение
            elements: Список элементов с bbox
            max_elements: Максимум элементов для разметки
            
        Returns:
            (размеченное изображение, описание элементов)
        """
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        description_parts = []
        
        for i, elem in enumerate(elements[:max_elements]):
            bbox = elem.get("bbox", {})
            x = bbox.get("x", 0)
            y = bbox.get("y", 0)
            w = bbox.get("width", 50)
            h = bbox.get("height", 50)
            
            # Выбираем цвет
            color = self._colors[i % len(self._colors)]
            
            # Рисуем рамку
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            
            # Рисуем номер
            num_str = str(i + 1)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Фон для номера
            text_bbox = draw.textbbox((0, 0), num_str, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            
            draw.rectangle(
                [x, y - text_h - 4, x + text_w + 4, y],
                fill=color
            )
            draw.text((x + 2, y - text_h - 2), num_str, fill=(255, 255, 255), font=font)
            
            # Добавляем в описание
            elem_type = elem.get("type", "object")
            description_parts.append(f"{i + 1}: {elem_type} at ({x}, {y})")
        
        description = "; ".join(description_parts)
        return img_copy, description
    
    def create_prompt_with_marks(
        self,
        marked_description: str,
        task: str
    ) -> str:
        """
        Создаёт промпт для VLM с размеченными элементами.
        
        Args:
            marked_description: Описание размеченных элементов
            task: Задача для выполнения
            
        Returns:
            Промпт для отправки в VLM
        """
        prompt = f"""На этом скриншоте отмечены UI элементы цифрами:
{marked_description}

Задача: {task}

Проанализируй изображение и укажи, с каким элементом (по номеру) нужно взаимодействовать.
Ответь в формате JSON с полем "target_element" (номер) и "action" (тип действия)."""
        
        return prompt
