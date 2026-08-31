"""
Perception module - восприятие агента.

Содержит:
- Скриншоты экрана
- OCR (распознавание текста)
- Поиск UI элементов
- Set-of-Mark разметка
"""

from .screen_capture import ScreenCapture
from .ocr_engine import OCREngine
from .ui_detector import UIDetector
from .set_of_mark import SetOfMarker

__all__ = [
    "ScreenCapture",
    "OCREngine",
    "UIDetector",
    "SetOfMarker",
]
