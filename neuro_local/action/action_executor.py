"""
Исполнитель действий для Neuro Local агента
С поддержкой кириллицы через буфер обмена и безопасным запуском приложений
"""
import time
import subprocess
import os
import pyperclip
import pydirectinput
import pyautogui
from typing import Dict, Any, Optional
from core.actions_schema import (
    Action, MouseClickAction, MouseMoveAction, 
    KeyboardPressAction, KeyboardTypeAction, 
    RunApplicationAction, SleepAction, ActionType
)
from core.config_loader import ConfigLoader


class ActionExecutor:
    """Исполнитель действий с поддержкой кириллицы и безопасностью"""
    
    SAFE_APPS = [
        "notepad.exe", "calculator.exe", "mspaint.exe", 
        "chrome.exe", "firefox.exe", "code.exe", "obsidian.exe"
    ]
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        self.pyautogui = pyautogui
        self.pydirectinput = pydirectinput
        self.pyautogui.FAILSAFE = True
        
        self.config = config or ConfigLoader()
        self.default_delay = self.config.get("actions.default_delay", 0.5)
        self.max_retries = self.config.get("actions.max_retries", 3)
        self.dry_run = self.config.get("actions.dry_run", True)
        
    def execute_action(self, action: Action) -> Dict[str, Any]:
        """Выполняет действие с проверками"""
        if self.dry_run:
            return {
                "success": True,
                "message": f"DRY-RUN: {action.type}",
                "details": {"dry_run": True, "action": action.model_dump()}
            }
        
        for attempt in range(self.max_retries):
            try:
                if action.type == ActionType.MOUSE_CLICK:
                    result = self._execute_mouse_click(action)
                elif action.type == ActionType.MOUSE_MOVE:
                    result = self._execute_mouse_move(action)
                elif action.type == ActionType.KEYBOARD_PRESS:
                    result = self._execute_keyboard_press(action)
                elif action.type == ActionType.KEYBOARD_TYPE:
                    result = self._execute_keyboard_type(action)
                elif action.type == ActionType.RUN_APPLICATION:
                    result = self._execute_run_application(action)
                elif action.type == ActionType.SLEEP:
                    result = self._execute_sleep(action)
                else:
                    return {"success": False, "message": f"Неизвестный тип: {action.type}"}
                
                if result["success"]:
                    time.sleep(self.default_delay)
                    return result
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(0.5)
                        
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
                else:
                    return {"success": False, "message": f"Ошибка: {str(e)}"}
        
        return {"success": False, "message": "Превышено число попыток"}
    
    def _execute_mouse_click(self, action) -> Dict[str, Any]:
        try:
            x, y = action.position.x, action.position.y
            button = getattr(action, 'button', 'left')
            clicks = getattr(action, 'clicks', 1)
            
            self.pydirectinput.click(x=x, y=y, button=button, clicks=clicks)
            
            return {"success": True, "message": f"Клик ({x},{y}) {button}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _execute_mouse_move(self, action) -> Dict[str, Any]:
        try:
            x, y = action.position.x, action.position.y
            duration = getattr(action, 'duration', 0.2)
            
            self.pydirectinput.moveTo(x=x, y=y, duration=duration)
            
            return {"success": True, "message": f"Перемещение в ({x},{y})"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _execute_keyboard_press(self, action) -> Dict[str, Any]:
        try:
            key = action.key
            self.pydirectinput.press(key)
            return {"success": True, "message": f"Нажата клавиша: {key}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _execute_keyboard_type(self, action) -> Dict[str, Any]:
        """Ввод текста через буфер обмена для поддержки кириллицы"""
        try:
            text = action.text
            if not text:
                return {"success": False, "message": "Пустой текст"}
            
            if len(text) > 5000:
                text = text[:5000]
            
            old_clip = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.1)
            
            with pyautogui.hold('ctrl'):
                pyautogui.press('v')
            
            time.sleep(0.2)
            
            return {
                "success": True,
                "message": f"Текст введен ({len(text)} симв.)",
                "details": {"length": len(text)}
            }
        except Exception as e:
            return {"success": False, "message": f"Ошибка ввода: {str(e)}"}
    
    def _execute_run_application(self, action) -> Dict[str, Any]:
        """Безопасный запуск приложений"""
        try:
            application = action.application.strip()
            arguments = getattr(action, 'arguments', []) or []
            
            # Проверка на опасные приложения
            app_lower = application.lower()
            dangerous = ["cmd", "powershell", "bash", "wscript", "regedit", "format"]
            
            if any(d in app_lower for d in dangerous) and app_lower not in self.SAFE_APPS:
                return {"success": False, "message": f"Запрещено: {application}"}
            
            # Добавляем .exe если нет расширения
            if not application.lower().endswith(('.exe', '.bat', '.cmd')):
                application += ".exe"
            
            # Проверка существования файла для абсолютных путей
            if os.path.isabs(application) and not os.path.exists(application):
                return {"success": False, "message": f"Не найдено: {application}"}
            
            cmd = [application] + arguments
            
            process = subprocess.Popen(cmd, shell=False)
            
            return {
                "success": True,
                "message": f"Запущено: {application}",
                "details": {"pid": process.pid}
            }
        except Exception as e:
            return {"success": False, "message": f"Ошибка запуска: {str(e)}"}
    
    def _execute_sleep(self, action) -> Dict[str, Any]:
        try:
            seconds = action.seconds
            time.sleep(seconds)
            return {"success": True, "message": f"Пауза {seconds}с"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def set_dry_run(self, dry_run: bool):
        self.dry_run = dry_run
