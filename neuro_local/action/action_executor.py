"""
Исполнитель действий для Neuro Local агента
Исправлено: кириллица через буфер, безопасность путей, валидация
"""
import time
import subprocess
import pyperclip
import pydirectinput
import pyautogui
import os
from typing import Dict, Any, Optional
from core.actions_schema import (
    Action, MouseClickAction, MouseMoveAction, 
    KeyboardPressAction, KeyboardTypeAction, 
    RunApplicationAction, SleepAction, ActionType
)
from core.config_loader import ConfigLoader


class ActionExecutor:
    """Исполнитель действий агента"""
    def __init__(self, config: Optional[ConfigLoader] = None):
        self.pyautogui = pyautogui
        self.pydirectinput = pydirectinput
        
        # Устанавливаем безопасность pyautogui
        self.pyautogui.FAILSAFE = True
        
        self.config = config or ConfigLoader()
        self.default_delay = self.config.get("actions.default_delay", 0.5)
        self.max_retries = self.config.get("actions.max_retries", 3)
        self.dry_run = self.config.get("actions.dry_run", True)
        
        # Белый список безопасных приложений
        self.safe_apps = [
            "notepad.exe", "calculator.exe", "mspaint.exe", 
            "chrome.exe", "firefox.exe", "code.exe", "obsidian.exe",
            "explorer.exe", "spotify.exe", "discord.exe"
        ]
        
    def execute_action(self, action: Action) -> Dict[str, Any]:
        """
        Выполняет действие и возвращает результат
        
        Args:
            action: Действие для выполнения
            
        Returns:
            Результат выполнения в формате {"success": bool, "message": str, "details": dict}
        """
        if self.dry_run:
            return {
                "success": True,
                "message": f"DRY-RUN: Выполнено действие {action.type}",
                "details": {"dry_run": True, "action": action.model_dump()}
            }
        
        # Пытаемся выполнить действие с повторными попытками
        for attempt in range(self.max_retries):
            try:
                if action.type == "mouse_click":
                    result = self._execute_mouse_click(action)
                elif action.type == "mouse_move":
                    result = self._execute_mouse_move(action)
                elif action.type == "keyboard_press":
                    result = self._execute_keyboard_press(action)
                elif action.type == "keyboard_type":
                    result = self._execute_keyboard_type(action)
                elif action.type == "run_application":
                    result = self._execute_run_application(action)
                elif action.type == "sleep":
                    result = self._execute_sleep(action)
                else:
                    return {
                        "success": False,
                        "message": f"Неизвестный тип действия: {action.type}",
                        "details": {}
                    }
                
                # Если выполнение прошло успешно
                if result["success"]:
                    time.sleep(self.default_delay)  # Задержка между действиями
                    return result
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(0.5)  # Ждем перед повторной попыткой
                        continue
                    else:
                        return result
                        
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    return {
                        "success": False,
                        "message": f"Ошибка при выполнении действия: {str(e)}",
                        "details": {"exception": str(e), "attempt": attempt + 1}
                    }
    
    def _execute_mouse_click(self, action: MouseClickAction) -> Dict[str, Any]:
        """Выполняет клик мышью"""
        try:
            x, y = action.position.x, action.position.y
            button = action.button
            clicks = action.clicks
            
            # Проверка границ экрана
            screen_w, screen_h = pyautogui.size()
            if not (0 <= x <= screen_w and 0 <= y <= screen_h):
                return {
                    "success": False,
                    "message": f"Координаты вне экрана: ({x}, {y}), размер: {screen_w}x{screen_h}",
                    "details": {"out_of_bounds": True}
                }
            
            # Используем pydirectinput для более надежного взаимодействия
            self.pydirectinput.click(x=x, y=y, button=button, clicks=clicks)
            
            return {
                "success": True,
                "message": f"Выполнен клик по ({x}, {y}), кнопка: {button}, кликов: {clicks}",
                "details": {"position": (x, y), "button": button, "clicks": clicks}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при выполнении клика: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_mouse_move(self, action: MouseMoveAction) -> Dict[str, Any]:
        """Перемещает курсор мыши"""
        try:
            x, y = action.position.x, action.position.y
            duration = action.duration
            
            # Проверка границ
            screen_w, screen_h = pyautogui.size()
            if not (0 <= x <= screen_w and 0 <= y <= screen_h):
                return {
                    "success": False,
                    "message": f"Координаты вне экрана: ({x}, {y})",
                    "details": {"out_of_bounds": True}
                }
            
            self.pydirectinput.moveTo(x=x, y=y, duration=duration)
            
            return {
                "success": True,
                "message": f"Курсор перемещен в ({x}, {y}) за {duration}s",
                "details": {"position": (x, y), "duration": duration}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при перемещении курсора: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_keyboard_press(self, action: KeyboardPressAction) -> Dict[str, Any]:
        """Нажимает клавишу"""
        try:
            key = action.key
            
            # Блокировка опасных комбинаций
            dangerous_keys = ["win", "command", "ctrl+alt+del", "alt+f4"]
            if any(dk in key.lower() for dk in dangerous_keys):
                return {
                    "success": False,
                    "message": f"Опасная клавиша заблокирована: {key}",
                    "details": {"blocked": True}
                }
            
            self.pydirectinput.press(key)
            
            return {
                "success": True,
                "message": f"Нажата клавиша: {key}",
                "details": {"key": key}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при нажатии клавиши: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_keyboard_type(self, action: KeyboardTypeAction) -> Dict[str, Any]:
        """Вводит текст через буфер обмена (поддержка кириллицы)"""
        try:
            text = action.text
            
            if not text:
                return {"success": False, "message": "Пустой текст"}
            
            # Ограничение длины текста
            if len(text) > 5000:
                text = text[:5000]
            
            if self.dry_run:
                return {"success": True, "message": f"DRY-RUN: Ввод текста ({len(text)} симв.)"}

            # Сохраняем старый буфер
            old_clip = pyperclip.paste()
            
            # Копируем текст в буфер
            pyperclip.copy(text)
            time.sleep(0.1)
            
            # Вставляем через Ctrl+V
            with pyautogui.hold('ctrl'):
                pyautogui.press('v')
                
            time.sleep(0.2)
            
            # Восстанавливаем буфер (опционально)
            # pyperclip.copy(old_clip)
            
            return {
                "success": True,
                "message": f"Текст введен через буфер обмена: '{text[:50]}...'",
                "details": {"length": len(text), "method": "clipboard"}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при вводе текста: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_run_application(self, action: RunApplicationAction) -> Dict[str, Any]:
        """Запускает приложение с проверкой безопасности"""
        try:
            application = action.application.strip()
            arguments = action.arguments or []
            
            # Проверка на опасные команды
            dangerous_keywords = ["cmd", "powershell", "bash", "sh", "del", "rm", "format", "reg", "shutdown"]
            app_lower = application.lower()
            
            # Добавляем .exe если нет расширения
            if not any(app_lower.endswith(ext) for ext in [".exe", ".bat", ".cmd", ".ps1"]):
                application += ".exe"
                app_lower = application.lower()
            
            # Блокировка опасных системных утилит
            if any(k in app_lower for k in dangerous_keywords):
                if app_lower not in self.safe_apps:
                    return {
                        "success": False,
                        "message": f"Безопасность: Запуск '{application}' запрещен.",
                        "details": {"blocked": True, "reason": "dangerous_app"}
                    }
            
            # Проверка существования файла для абсолютных путей
            if os.path.isabs(application) and not os.path.exists(application):
                return {"success": False, "message": f"Файл не найден: {application}"}

            # Формируем команду БЕЗ shell=True для безопасности
            cmd = [application] + arguments
            
            process = subprocess.Popen(cmd, shell=False)
            
            return {
                "success": True,
                "message": f"Запущено: {application}",
                "details": {"pid": process.pid, "cmd": cmd}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка запуска приложения: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_sleep(self, action: SleepAction) -> Dict[str, Any]:
        """Выполняет паузу с валидацией времени"""
        try:
            seconds = action.seconds
            
            # Валидация времени
            if seconds < 0:
                return {"success": False, "message": "Отрицательное время сна недопустимо"}
            if seconds > 3600:
                seconds = 3600  # Максимум 1 час
                
            time.sleep(seconds)
            
            return {
                "success": True,
                "message": f"Выполнена пауза на {seconds} секунд",
                "details": {"seconds": seconds}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при выполнении паузы: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def set_dry_run(self, dry_run: bool):
        """Устанавливает режим dry-run"""
        self.dry_run = dry_run
