"""
TTS движок через pyttsx3 (оффлайн).

Поддерживает русскую и английскую речь.
"""

import logging
from typing import Optional, Callable
import threading

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("pyttsx3 не установлен, TTS недоступен")

logger = logging.getLogger(__name__)


class TTSEngine:
    """Движок синтеза речи."""
    
    def __init__(
        self,
        enabled: bool = True,
        voice_id: int = 0,
        rate: int = 150
    ):
        """
        Инициализация TTS.
        
        Args:
            enabled: Включён ли TTS
            voice_id: ID голоса
            rate: Скорость речи (слова в минуту)
        """
        self.enabled = enabled and TTS_AVAILABLE
        self._engine: Optional[pyttsx3.Engine] = None
        self._voice_id = voice_id
        self._rate = rate
        
        if self.enabled:
            self._init_engine()
        
        logger.info(f"TTSEngine инициализирован (enabled={self.enabled})")
    
    def _init_engine(self) -> None:
        """Инициализирует движок TTS."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._rate)
            
            # Пытаемся установить русский голос
            voices = self._engine.getProperty('voices')
            if voices:
                # Ищем русский голос
                ru_voice = None
                for i, voice in enumerate(voices):
                    if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                        ru_voice = i
                        break
                
                if ru_voice is not None:
                    self._engine.setProperty('voice', voices[ru_voice].id)
                    logger.info(f"Установлен русский голос: {voices[ru_voice].name}")
                elif len(voices) > self._voice_id:
                    self._engine.setProperty('voice', voices[self._voice_id].id)
                    
        except Exception as e:
            logger.error(f"Ошибка инициализации TTS: {e}")
            self.enabled = False
    
    def speak(self, text: str, async_mode: bool = False) -> None:
        """
        Произносит текст.
        
        Args:
            text: Текст для произнесения
            async_mode: Асинхронное воспроизведение
        """
        if not self.enabled or not text.strip():
            return
        
        if async_mode:
            thread = threading.Thread(target=self._speak_sync, args=(text,))
            thread.daemon = True
            thread.start()
        else:
            self._speak_sync(text)
    
    def _speak_sync(self, text: str) -> None:
        """Синхронное произнесение."""
        try:
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
                logger.debug(f"TTS: {text[:50]}...")
        except Exception as e:
            logger.error(f"Ошибка TTS: {e}")
    
    def set_rate(self, rate: int) -> None:
        """Устанавливает скорость речи."""
        self._rate = rate
        if self._engine:
            self._engine.setProperty('rate', rate)
    
    def list_voices(self) -> list:
        """Возвращает список доступных голосов."""
        if not self._engine:
            return []
        
        voices = self._engine.getProperty('voices')
        return [
            {"id": i, "name": v.name, "languages": v.languages}
            for i, v in enumerate(voices)
        ]


def main():
    """Тест TTS."""
    tts = TTSEngine(enabled=True)
    
    if not tts.enabled:
        print("TTS недоступен")
        return
    
    print("Доступные голоса:")
    for voice in tts.list_voices():
        print(f"  {voice['id']}: {voice['name']}")
    
    print("\nТест речи:")
    tts.speak("Привет! Я нейро-агент Нейро.", async_mode=False)
    tts.speak("Я работаю полностью локально.", async_mode=False)


if __name__ == "__main__":
    main()
