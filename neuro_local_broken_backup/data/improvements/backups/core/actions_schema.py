"""
Схема действий агента на основе Pydantic.

Все действия строго типизированы и валидируются.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """Типы доступных действий."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE = "move"
    DRAG = "drag"
    TYPE = "type"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    WAIT = "wait"
    SCROLL = "scroll"
    LAUNCH_APP = "launch_app"
    CLOSE_WINDOW = "close_window"
    SPEAK = "speak"
    NONE = "none"  # Никакого действия (ожидание)


class TargetPosition(BaseModel):
    """Позиция цели на экране."""
    x: int = Field(..., description="Координата X")
    y: int = Field(..., description="Координата Y")
    
    @field_validator('x', 'y')
    @classmethod
    def validate_coordinates(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Координаты не могут быть отрицательными")
        return v


class ClickAction(BaseModel):
    """Действие клика мышью."""
    action_type: Literal[ActionType.CLICK] = ActionType.CLICK
    target: TargetPosition
    button: Literal["left", "right", "middle"] = "left"
    clicks: int = 1
    reason: str = Field(..., description="Обоснование действия")


class DoubleClickAction(BaseModel):
    """Действие двойного клика."""
    action_type: Literal[ActionType.DOUBLE_CLICK] = ActionType.DOUBLE_CLICK
    target: TargetPosition
    reason: str


class RightClickAction(BaseModel):
    """Действие правого клика."""
    action_type: Literal[ActionType.RIGHT_CLICK] = ActionType.RIGHT_CLICK
    target: TargetPosition
    reason: str


class MoveAction(BaseModel):
    """Действие перемещения мыши."""
    action_type: Literal[ActionType.MOVE] = ActionType.MOVE
    target: TargetPosition
    duration: float = Field(default=0.5, description="Длительность перемещения в секундах")
    reason: str


class DragAction(BaseModel):
    """Действие перетаскивания."""
    action_type: Literal[ActionType.DRAG] = ActionType.DRAG
    start: TargetPosition
    end: TargetPosition
    button: Literal["left", "right", "middle"] = "left"
    duration: float = Field(default=1.0, description="Длительность перетаскивания")
    reason: str


class TypeAction(BaseModel):
    """Действие ввода текста."""
    action_type: Literal[ActionType.TYPE] = ActionType.TYPE
    text: str = Field(..., description="Текст для ввода")
    interval: float = Field(default=0.05, description="Интервал между символами")
    reason: str


class PressKeyAction(BaseModel):
    """Действие нажатия клавиши."""
    action_type: Literal[ActionType.PRESS_KEY] = ActionType.PRESS_KEY
    key: str = Field(..., description="Клавиша (например, 'enter', 'escape', 'a')")
    presses: int = Field(default=1, description="Количество нажатий")
    interval: float = Field(default=0.1, description="Интервал между нажатиями")
    reason: str


class HotkeyAction(BaseModel):
    """Действие комбинации клавиш."""
    action_type: Literal[ActionType.HOTKEY] = ActionType.HOTKEY
    keys: List[str] = Field(..., description="Список клавиш для комбинации")
    reason: str
    
    @field_validator('keys')
    @classmethod
    def validate_hotkey(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("Hotkey должен содержать минимум 2 клавиши")
        return v


class WaitAction(BaseModel):
    """Действие ожидания."""
    action_type: Literal[ActionType.WAIT] = ActionType.WAIT
    seconds: float = Field(default=1.0, description="Длительность ожидания в секундах")
    reason: str


class ScrollAction(BaseModel):
    """Действие прокрутки."""
    action_type: Literal[ActionType.SCROLL] = ActionType.SCROLL
    amount: int = Field(..., description="Количество шагов прокрутки (положительное - вверх, отрицательное - вниз)")
    target: Optional[TargetPosition] = None
    reason: str


class LaunchAppAction(BaseModel):
    """Действие запуска приложения."""
    action_type: Literal[ActionType.LAUNCH_APP] = ActionType.LAUNCH_APP
    app_name: str = Field(..., description="Имя приложения или путь к исполняемому файлу")
    arguments: Optional[List[str]] = None
    reason: str


class CloseWindowAction(BaseModel):
    """Действие закрытия окна."""
    action_type: Literal[ActionType.CLOSE_WINDOW] = ActionType.CLOSE_WINDOW
    window_title: Optional[str] = None  # Если None, закрывает активное окно
    reason: str


class SpeakAction(BaseModel):
    """Действие произнесения текста."""
    action_type: Literal[ActionType.SPEAK] = ActionType.SPEAK
    text: str = Field(..., description="Текст для произнесения")
    reason: str


class NoneAction(BaseModel):
    """Отсутствие действия (агент ожидает)."""
    action_type: Literal[ActionType.NONE] = ActionType.NONE
    reason: str = Field(default="Ожидание следующего шага")


# Union всех типов действий
AnyAction = Union[
    ClickAction,
    DoubleClickAction,
    RightClickAction,
    MoveAction,
    DragAction,
    TypeAction,
    PressKeyAction,
    HotkeyAction,
    WaitAction,
    ScrollAction,
    LaunchAppAction,
    CloseWindowAction,
    SpeakAction,
    NoneAction
]


class ActionSchema(BaseModel):
    """
    Основная схема действия агента.
    
    Используется для валидации и сериализации всех действий.
    """
    action: AnyAction = Field(..., discriminator="action_type")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Уверенность агента в действии")
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": {
                    "action_type": "click",
                    "target": {"x": 100, "y": 200},
                    "button": "left",
                    "reason": "Нажать кнопку 'Сохранить'"
                },
                "confidence": 0.95,
                "metadata": {"source": "vision"}
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует действие в словарь."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_json(cls, json_str: str) -> "ActionSchema":
        """Создаёт действие из JSON строки."""
        import json
        data = json.loads(json_str)
        return cls.model_validate(data)


def create_action(
    action_type: ActionType,
    reason: str,
    **kwargs
) -> ActionSchema:
    """
    Фабрика для создания действий.
    
    Args:
        action_type: Тип действия
        reason: Обоснование действия
        **kwargs: Параметры конкретного действия
        
    Returns:
        ActionSchema с валидированным действием
    """
    action_classes = {
        ActionType.CLICK: ClickAction,
        ActionType.DOUBLE_CLICK: DoubleClickAction,
        ActionType.RIGHT_CLICK: RightClickAction,
        ActionType.MOVE: MoveAction,
        ActionType.DRAG: DragAction,
        ActionType.TYPE: TypeAction,
        ActionType.PRESS_KEY: PressKeyAction,
        ActionType.HOTKEY: HotkeyAction,
        ActionType.WAIT: WaitAction,
        ActionType.SCROLL: ScrollAction,
        ActionType.LAUNCH_APP: LaunchAppAction,
        ActionType.CLOSE_WINDOW: CloseWindowAction,
        ActionType.SPEAK: SpeakAction,
        ActionType.NONE: NoneAction,
    }
    
    action_class = action_classes.get(action_type)
    if not action_class:
        raise ValueError(f"Неизвестный тип действия: {action_type}")
    
    action = action_class(reason=reason, **kwargs)
    return ActionSchema(action=action)
