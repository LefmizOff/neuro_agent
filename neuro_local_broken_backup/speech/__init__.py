"""
Speech module - речь агента.

Содержит:
- TTS через pyttsx3 (оффлайн)
- Текстовый ввод CLI
- STT опционально через vosk
"""

from .tts_engine import TTSEngine

__all__ = ["TTSEngine"]
