"""
Шина событий для Neuro Local агента
"""
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """Представление события"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """Центральная шина событий"""
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        
    def subscribe(self, event_name: str, handler: Callable):
        """Подписывает обработчик на событие"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        
    def unsubscribe(self, event_name: str, handler: Callable):
        """Отписывает обработчик от события"""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass
                
    def publish(self, event: Event):
        """Публикует событие всем подписчикам"""
        handlers = self._handlers.get(event.name, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Ошибка при обработке события {event.name}: {e}")
                
    def emit(self, event_name: str, data: Dict[str, Any]):
        """Создаёт и публикует событие"""
        event = Event(name=event_name, data=data)
        self.publish(event)
