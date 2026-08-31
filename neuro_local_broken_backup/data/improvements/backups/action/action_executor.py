"""
Исполнитель действий агента.

Выполняет действия из ActionSchema через pyautogui/pydirectinput.
"""

import logging
from typing import Dict, Any, Optional
import pyautogui

# Для Windows - используем pydirectinput для игр
try:
    import pydirectinput
    PYDIRECTINPUT_AVAILABLE = True
except ImportError:
    PYDIRECTINPUT_AVAILABLE = False

from core.actions_schema import (
    ActionSchema, ActionType,
    ClickAction, MoveAction, TypeAction, PressKeyAction,
    HotkeyAction, WaitAction, ScrollAction, LaunchAppAction,
    CloseWindowAction, DragAction, NoneAction
)

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Исполнитель действий."""
    
    def __init__(
        self,
        dry_run: bool = True,
        mouse_speed: float = 0.5,
        keyboard_delay: float = 0.05
    ):
        """
        Инициализация исполнителя.
        
        Args:
            dry_run: Если True, действия только логируются
            mouse_speed: Скорость мыши (0.1-1.0)
            keyboard_delay: Задержка между нажатиями клавиш
        """
        self.dry_run = dry_run
        self.mouse_speed = mouse_speed
        self.keyboard_delay = keyboard_delay
        
        # Настройка pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = keyboard_delay
        
        logger.info(f"ActionExecutor инициализирован (dry_run={dry_run})")
    
    def execute(self, action_schema: ActionSchema) -> Dict[str, Any]:
        """
        Выполняет действие.
        
        Args:
            action_schema: Схема действия
            
        Returns:
            Результат выполнения
        """
        action = action_schema.action
        action_type = action.action_type
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Действие: {action_type.value} - {action.reason}")
            return {"success": True, "dry_run": True, "action": action_type.value}
        
        try:
            result = self._execute_action(action)
            logger.info(f"Выполнено: {action_type.value} - {action.reason}")
            return {"success": True, "dry_run": False, "result": result}
        except Exception as e:
            logger.error(f"Ошибка выполнения {action_type.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_action(self, action) -> Dict[str, Any]:
        """Выполняет конкретное действие."""
        
        if isinstance(action, (ClickAction,)):
            return self._click(action)
        elif isinstance(action, MoveAction):
            return self._move(action)
        elif isinstance(action, DragAction):
            return self._drag(action)
        elif isinstance(action, TypeAction):
            return self._type(action)
        elif isinstance(action, PressKeyAction):
            return self._press_key(action)
        elif isinstance(action, HotkeyAction):
            return self._hotkey(action)
        elif isinstance(action, WaitAction):
            return self._wait(action)
        elif isinstance(action, ScrollAction):
            return self._scroll(action)
        elif isinstance(action, LaunchAppAction):
            return self._launch_app(action)
        elif isinstance(action, CloseWindowAction):
            return self._close_window(action)
        elif isinstance(action, NoneAction):
            return {"status": "no_action"}
        else:
            raise ValueError(f"Неизвестный тип действия: {type(action)}")
    
    def _click(self, action: ClickAction) -> Dict[str, Any]:
        """Клик мышью."""
        pyautogui.click(
            x=action.target.x,
            y=action.target.y,
            clicks=action.clicks,
            button=action.button,
            duration=self.mouse_speed
        )
        return {"clicked": (action.target.x, action.target.y), "button": action.button}
    
    def _move(self, action: MoveAction) -> Dict[str, Any]:
        """Перемещение мыши."""
        pyautogui.moveTo(
            action.target.x,
            action.target.y,
            duration=action.duration
        )
        return {"position": (action.target.x, action.target.y)}
    
    def _drag(self, action: DragAction) -> Dict[str, Any]:
        """Перетаскивание."""
        pyautogui.drag(
            action.end.x - action.start.x,
            action.end.y - action.start.y,
            duration=action.duration,
            button=action.button
        )
        return {"from": (action.start.x, action.start.y), "to": (action.end.x, action.end.y)}
    
    def _type(self, action: TypeAction) -> Dict[str, Any]:
        """Ввод текста через буфер обмена для поддержки кириллицы."""
        import pyperclip
        import time
        
        text = action.text
        
        # Ограничиваем длину текста
        if len(text) > 5000:
            logger.warning(f"Текст обрезан до 5000 символов (было {len(text)})")
            text = text[:5000]
        
        if not text.strip():
            return {"text_length": 0, "warning": "Пустой текст"}
        
        try:
            # Сохраняем текущий буфер
            old_clip = pyperclip.paste()
            
            # Копируем текст в буфер
            pyperclip.copy(text)
            time.sleep(0.1)
            
            # Вставляем через Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            
            return {"text_length": len(text), "method": "clipboard"}
        except Exception as e:
            # Fallback на обычный ввод (не поддерживает кириллицу)
            logger.warning(f"Буфер обмена не доступен, используем fallback: {e}")
            pyautogui.write(text, interval=action.interval)
            return {"text_length": len(text), "method": "fallback"}
    
    def _press_key(self, action: PressKeyAction) -> Dict[str, Any]:
        """Нажатие клавиши."""
        use_direct = PYDIRECTINPUT_AVAILABLE and action.key in ['w', 'a', 's', 'd', 'space']
        
        for _ in range(action.presses):
            if use_direct:
                pydirectinput.press(action.key)
            else:
                pyautogui.press(action.key)
        return {"key": action.key, "presses": action.presses}
    
    def _hotkey(self, action: HotkeyAction) -> Dict[str, Any]:
        """Комбинация клавиш."""
        pyautogui.hotkey(*action.keys)
        return {"keys": action.keys}
    
    def _wait(self, action: WaitAction) -> Dict[str, Any]:
        """Ожидание."""
        import time
        time.sleep(action.seconds)
        return {"waited": action.seconds}
    
    def _scroll(self, action: ScrollAction) -> Dict[str, Any]:
        """Прокрутка."""
        if action.target:
            pyautogui.scroll(action.amount, action.target.x, action.target.y)
        else:
            pyautogui.scroll(action.amount)
        return {"amount": action.amount}
    
    def _launch_app(self, action: LaunchAppAction) -> Dict[str, Any]:
        """Запуск приложения."""
        import subprocess
        try:
            args = [action.app_name] + (action.arguments or [])
            subprocess.Popen(args)
            return {"launched": action.app_name}
        except Exception as e:
            return {"error": str(e)}
    
    def _close_window(self, action: CloseWindowAction) -> Dict[str, Any]:
        """Закрытие окна."""
        # Alt+F4 для закрытия активного окна
        pyautogui.hotkey('alt', 'f4')
        return {"closed": action.window_title or "active_window"}
    
    def set_dry_run(self, value: bool) -> None:
        """Устанавливает режим dry-run."""
        self.dry_run = value
        logger.info(f"Dry-run: {value}")
