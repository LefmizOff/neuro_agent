"""
Модуль восприятия для Neuro Local агента
"""
from perception.screen_capture import ScreenCapture
from perception.ocr_engine import OCREngine
from perception.ui_detector import UIDetector
from perception.set_of_mark import SetOfMark

__all__ = ['ScreenCapture', 'OCREngine', 'UIDetector', 'SetOfMark']
