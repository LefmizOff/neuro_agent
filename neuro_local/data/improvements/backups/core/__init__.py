"""
Модуль ядра системы Neuro Local
Содержит основные компоненты: Ollama-клиент, планировщик, шину событий, безопасность, схемы действий
"""
from core.ollama_client import OllamaClient
from core.config_loader import ConfigLoader
from core.event_bus import EventBus
from core.planner import Planner
from core.safety_manager import SafetyManager
from core.actions_schema import (
    Action, ActionType, Position,
    MouseClickAction, MouseMoveAction,
    KeyboardPressAction, KeyboardTypeAction,
    RunApplicationAction, SleepAction
)

__all__ = [
    'OllamaClient',
    'ConfigLoader',
    'EventBus',
    'Planner',
    'SafetyManager',
    'Action',
    'ActionType',
    'Position',
    'MouseClickAction',
    'MouseMoveAction',
    'KeyboardPressAction',
    'KeyboardTypeAction',
    'RunApplicationAction',
    'SleepAction'
]
