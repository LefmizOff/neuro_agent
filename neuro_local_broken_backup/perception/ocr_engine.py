"""
OCR движок для распознавания текста на скриншотах.

Поддерживает:
- RapidOCR (быстрый, локальный)
- Tesseract (через pytesseract)
- Заглушку если OCR не установлен
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Движок оптического распознавания символов.
    
    Использует доступный OCR движок для извлечения текста из изображений.
    """
    
    def __init__(self, engine: str = "rapidocr"):
        """
        Инициализация OCR движка.
        
        Args:
            engine: Название движка ("rapidocr", "tesseract", "none")
        """
        self.engine_name = engine
        self._engine = None
        self._available = False
        
        self._init_engine()
        logger.info(f"OCREngine инициализирован: {engine}")
    
    def _init_engine(self) -> None:
        """Инициализирует выбранный OCR движок."""
        if self.engine_name == "rapidocr":
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._engine = RapidOCR()
                self._available = True
                logger.info("RapidOCR успешно инициализирован")
            except ImportError:
                logger.warning("RapidOCR не установлен, пробуем tesseract")
                self._init_tesseract()
        elif self.engine_name == "tesseract":
            self._init_tesseract()
        else:
            logger.info("OCR отключён")
    
    def _init_tesseract(self) -> None:
        """Инициализирует Tesseract OCR."""
        try:
            import pytesseract
            self._engine = pytesseract
            self._available = True
            logger.info("Tesseract OCR успешно инициализирован")
        except ImportError:
            logger.warning("Tesseract не установлен, OCR будет недоступен")
            self._available = False
    
    def is_available(self) -> bool:
        """Проверяет доступность OCR."""
        return self._available
    
    def recognize(
        self,
        image: Image.Image,
        lang: str = "en+ru"
    ) -> List[Dict[str, Any]]:
        """
        Распознаёт текст на изображении.
        
        Args:
            image: PIL Image со скриншотом
            lang: Языки распознавания
            
        Returns:
            Список найденных текстовых блоков с координатами
        """
        if not self._available:
            return []
        
        try:
            if self.engine_name == "rapidocr" and isinstance(self._engine, object):
                return self._recognize_rapid(image)
            elif self.engine_name == "tesseract":
                return self._recognize_tesseract(image, lang)
            else:
                return []
        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return []
    
    def _recognize_rapid(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Распознавание через RapidOCR."""
        # Конвертируем в numpy array
        img_array = np.array(image)
        
        # Выполняем распознавание
        result, _ = self._engine(img_array)
        
        if result is None:
            return []
        
        texts = []
        for item in result:
            bbox, text, confidence = item
            texts.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": {
                    "x": int(bbox[0][0]),
                    "y": int(bbox[0][1]),
                    "width": int(bbox[2][0] - bbox[0][0]),
                    "height": int(bbox[2][1] - bbox[0][1])
                }
            })
        
        return texts
    
    def _recognize_tesseract(
        self,
        image: Image.Image,
        lang: str
    ) -> List[Dict[str, Any]]:
        """Распознавание через Tesseract."""
        import pytesseract
        
        # Получаем данные с bounding boxes
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT
        )
        
        texts = []
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Только уверенные результаты
                texts.append({
                    "text": data['text'][i],
                    "confidence": float(data['conf'][i]) / 100.0,
                    "bbox": {
                        "x": int(data['left'][i]),
                        "y": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i])
                    }
                })
        
        return texts
    
    def get_full_text(self, image: Image.Image, lang: str = "en+ru") -> str:
        """
        Возвращает весь распознанный текст как строку.
        
        Args:
            image: PIL Image
            lang: Языки
            
        Returns:
            Строка с распознанным текстом
        """
        blocks = self.recognize(image, lang)
        return " ".join(block["text"] for block in blocks if block["text"].strip())
    
    def find_text(
        self,
        image: Image.Image,
        search_text: str,
        threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Ищет конкретный текст на изображении.
        
        Args:
            image: PIL Image
            search_text: Текст для поиска
            threshold: Порог схожести
            
        Returns:
            Информация о найденном тексте или None
        """
        blocks = self.recognize(image)
        search_lower = search_text.lower()
        
        for block in blocks:
            text = block["text"].lower()
            
            # Точное совпадение
            if search_lower in text or text in search_lower:
                return block
            
            # Частичное совпадение
            similarity = self._string_similarity(search_lower, text)
            if similarity >= threshold:
                return block
        
        return None
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Вычисляет схожесть строк (упрощённая)."""
        if not s1 or not s2:
            return 0.0
        
        # Простая проверка на подстроку
        if s1 in s2 or s2 in s1:
            return 0.9
        
        # Проверка первых символов
        common = sum(1 for a, b in zip(s1, s2) if a == b)
        return common / max(len(s1), len(s2))
