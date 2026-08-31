"""
Схемы действий для Neuro Local агента
Все действия должны соответствовать этим Pydantic-моделям
"""
from enum import Enum
from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    KEYBOARD_PRESS = "keyboard_press"
    KEYBOARD_TYPE = "keyboard_type"
    RUN_APPLICATION = "run_application"
    SLEEP = "sleep"


class Position(BaseModel):
    x: int = Field(..., description="Координата X")
    y: int = Field(..., description="Координата Y")
    
    @field_validator('x', 'y')
    @classmethod
    def validate_coordinates(cls, v):
        if v < -10000 or v > 100000:
            raise ValueError(f"Координата {v} выходит за разумные пределы")
        return v


class MouseClickAction(BaseModel):
    type: Literal[ActionType.MOUSE_CLICK] = ActionType.MOUSE_CLICK
    position: Position
    button: str = Field(default="left", description="Кнопка мыши: left, right, middle")
    clicks: int = Field(default=1, ge=1, le=10, description="Количество кликов")


class MouseMoveAction(BaseModel):
    type: Literal[ActionType.MOUSE_MOVE] = ActionType.MOUSE_MOVE
    position: Position
    duration: float = Field(default=0.2, ge=0.01, le=10.0, description="Время перемещения в секундах")


class KeyboardPressAction(BaseModel):
    type: Literal[ActionType.KEYBOARD_PRESS] = ActionType.KEYBOARD_PRESS
    key: str = Field(..., description="Название клавиши")


class KeyboardTypeAction(BaseModel):
    type: Literal[ActionType.KEYBOARD_TYPE] = ActionType.KEYBOARD_TYPE
    text: str = Field(..., description="Текст для ввода")
    
    @field_validator('text')
    @classmethod
    def validate_text_length(cls, v):
        if len(v) > 10000:
            raise ValueError("Текст слишком длинный (максимум 10000 символов)")
        return v


class RunApplicationAction(BaseModel):
    type: Literal[ActionType.RUN_APPLICATION] = ActionType.RUN_APPLICATION
    application: str = Field(..., description="Путь или имя приложения")
    arguments: Optional[List[str]] = Field(default=None, description="Аргументы командной строки")


class SleepAction(BaseModel):
    type: Literal[ActionType.SLEEP] = ActionType.SLEEP
    seconds: float = Field(..., ge=0.1, le=3600, description="Время ожидания в секундах")


# Union всех возможных действий
Action = Union[
    MouseClickAction,
    MouseMoveAction,
    KeyboardPressAction,
    KeyboardTypeAction,
    RunApplicationAction,
    SleepAction
]
