"""
Шина событий для асинхронной коммуникации между модулями.

Позволяет модулям подписываться на события и реагировать на них.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading
from queue import Queue

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Типы событий в системе."""
    # События восприятия
    SCREENSHOT_TAKEN = "screenshot_taken"
    OCR_COMPLETED = "ocr_completed"
    UI_DETECTED = "ui_detected"
    
    # События действий
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    
    # События планирования
    PLAN_CREATED = "plan_created"
    PLAN_STEP_COMPLETED = "plan_step_completed"
    PLAN_COMPLETED = "plan_completed"
    
    # События памяти
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"
    
    # События речи
    SPEECH_STARTED = "speech_started"
    SPEECH_COMPLETED = "speech_completed"
    
    # События безопасности
    DANGER_DETECTED = "danger_detected"
    EMERGENCY_STOP = "emergency_stop"
    
    # События эволюции
    LOG_RECORDED = "log_recorded"
    IMPROVEMENT_SUGGESTED = "improvement_suggested"
    
    # Пользовательские события
    USER_COMMAND = "user_command"
    GOAL_CHANGED = "goal_changed"


@dataclass
class Event:
    """Событие в системе."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует событие в словарь."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class EventBus:
    """
    Шина событий для коммуникации между модулями.
    
    Поддерживает:
    - Подписку на события по типу
    - Обработку событий в отдельных потоках
    - Приоритетные обработчики
    """
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "EventBus":
        """Реализация паттерна Singleton."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._priority_subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_queue: Queue = Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        self._initialized = True
        logger.info("EventBus инициализирован")
    
    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None],
        priority: bool = False
    ) -> None:
        """
        Подписывает обработчик на событие.
        
        Args:
            event_type: Тип события
            callback: Функция-обработчик
            priority: Если True, обработчик вызывается первым
        """
        subscribers = self._priority_subscribers if priority else self._subscribers
        
        if event_type not in subscribers:
            subscribers[event_type] = []
        
        if callback not in subscribers[event_type]:
            subscribers[event_type].append(callback)
            logger.debug(f"Подписка на {event_type.value}: {callback.__name__}")
    
    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ) -> None:
        """Отписывает обработчик от события."""
        for subscribers in [self._subscribers, self._priority_subscribers]:
            if event_type in subscribers and callback in subscribers[event_type]:
                subscribers[event_type].remove(callback)
                logger.debug(f"Отписка от {event_type.value}: {callback.__name__}")
    
    def publish(self, event: Event) -> None:
        """
        Публикует событие в шину.
        
        Args:
            event: Событие для публикации
        """
        self._event_queue.put(event)
        logger.debug(f"Событие опубликовано: {event.event_type.value}")
    
    def publish_sync(self, event: Event) -> None:
        """
        Публикует событие и синхронно вызывает обработчики.
        
        Args:
            event: Событие для публикации
        """
        self._dispatch_event(event)
    
    def start(self) -> None:
        """Запускает рабочий поток обработки событий."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
        logger.info("EventBus запущен")
    
    def stop(self) -> None:
        """Останавливает обработку событий."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        logger.info("EventBus остановлен")
    
    def _process_events(self) -> None:
        """Основной цикл обработки событий."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._dispatch_event(event)
            except Exception:
                continue
    
    def _dispatch_event(self, event: Event) -> None:
        """Вызывает всех подписчиков события."""
        all_callbacks = []
        
        # Сначала приоритетные обработчики
        if event.event_type in self._priority_subscribers:
            all_callbacks.extend(self._priority_subscribers[event.event_type])
        
        # Затем обычные обработчики
        if event.event_type in self._subscribers:
            all_callbacks.extend(self._subscribers[event.event_type])
        
        for callback in all_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Ошибка в обработчике {callback.__name__}: {e}")
    
    def clear(self) -> None:
        """Очищает все подписки и очередь событий."""
        self._subscribers.clear()
        self._priority_subscribers.clear()
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
        logger.info("EventBus очищен")


# Глобальный экземпляр
def get_event_bus() -> EventBus:
    """Возвращает глобальный экземпляр EventBus."""
    return EventBus()
