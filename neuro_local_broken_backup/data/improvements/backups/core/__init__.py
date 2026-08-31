"""
Core module - ядро системы Neuro Local Agent.

Содержит:
- Ollama клиент для работы с локальными моделями
- Планировщик задач
- Шина событий
- Схема действий (Pydantic)
- Менеджер безопасности
"""

from .ollama_client import OllamaClient, VisionModel, LLMModel
from .actions_schema import ActionSchema, ActionType, ClickAction, MoveAction, TypeAction, PressKeyAction, HotkeyAction, WaitAction, ScrollAction, LaunchAppAction, CloseWindowAction, DragAction
from .planner import Planner
from .event_bus import EventBus, Event, EventType
from .safety_manager import SafetyManager, DangerLevel
from .config_loader import ConfigLoader

__all__ = [
    # Ollama клиент
    "OllamaClient",
    "VisionModel",
    "LLMModel",
    
    # Схема действий
    "ActionSchema",
    "ActionType",
    "ClickAction",
    "MoveAction",
    "TypeAction",
    "PressKeyAction",
    "HotkeyAction",
    "WaitAction",
    "ScrollAction",
    "LaunchAppAction",
    "CloseWindowAction",
    "DragAction",
    
    # Планировщик
    "Planner",
    
    # Шина событий
    "EventBus",
    "Event",
    "EventType",
    
    # Безопасность
    "SafetyManager",
    "DangerLevel",
    
    # Конфигурация
    "ConfigLoader",
]
