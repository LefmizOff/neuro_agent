"""
Менеджер безопасности для Neuro Local агента
Исправлено: глубокая валидация действий, проверка координат
"""
import threading
import time
import re
from typing import Dict, Any, Callable
from pynput import keyboard
from core.actions_schema import Action, ActionType, MouseMoveAction, RunApplicationAction
import pyautogui


class SafetyManager:
    """Менеджер безопасности агента"""
    def __init__(self, emergency_callback: Callable[[], None]):
        self.emergency_callback = emergency_callback
        self.emergency_hotkey = "ctrl+alt+q"
        self.is_running = True
        self.listener = None
        self.confirm_dangerous_actions = True
        
        # Устанавливаем флаг безопасности pyautogui
        pyautogui.FAILSAFE = True
        
        # Запускаем прослушивание горячей клавиши
        self.start_emergency_listener()
        
    def start_emergency_listener(self):
        """Запускает прослушивание горячей клавиши аварийной остановки"""
        self._ctrl_pressed = False
        self._alt_pressed = False
        
        def on_press(key):
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self._ctrl_pressed = True
                elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    self._alt_pressed = True
                elif self._ctrl_pressed and self._alt_pressed:
                    if hasattr(key, 'char') and key.char and key.char.lower() == 'q':
                        print("\n[БЕЗОПАСНОСТЬ] Обнаружена комбинация аварийной остановки!")
                        self.trigger_emergency_stop()
                        return False
            except Exception:
                pass
                
        def on_release(key):
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self._ctrl_pressed = False
                elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    self._alt_pressed = False
            except Exception:
                pass
                
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        
    def trigger_emergency_stop(self):
        """Вызывает аварийную остановку"""
        self.is_running = False
        self.emergency_callback()
        
    def is_safe_action(self, action: Action) -> bool:
        """Проверяет, является ли действие безопасным"""
        # Проверка координат для действий с мышью
        if isinstance(action, MouseMoveAction):
            screen_w, screen_h = pyautogui.size()
            margin = 50
            
            if not (margin <= action.position.x <= screen_w - margin and 
                    margin <= action.position.y <= screen_h - margin):
                print(f"[SAFETY] Координаты слишком близко к краю: {action.position}")
                return False

        # Проверка запуска приложений
        if action.type == ActionType.RUN_APPLICATION:
            if not isinstance(action, RunApplicationAction):
                return False
                
            app = action.application.lower()
            
            # Блокировка системных утилит
            blocked_patterns = [
                r"cmd\.exe", r"powershell\.exe", r"bash\.exe", 
                r"wscript", r"cscript", r"reg\.exe", r"regedit"
            ]
            
            for pattern in blocked_patterns:
                if re.search(pattern, app):
                    return False
            
            # Проверка аргументов на опасные команды
            if action.arguments:
                args_str = " ".join(action.arguments).lower()
                dangerous_args = ["/c del", "/c format", "-rf", "shutdown", "restart"]
                if any(d in args_str for d in dangerous_args):
                    return False

        # Проверка ввода текста на горячие клавиши
        if action.type == ActionType.KEYBOARD_TYPE:
            text = getattr(action, 'text', '')
            if "{ctrl}" in text or "{alt}" in text or "^" in text:
                return False

        return True
        
    def confirm_dangerous_action(self, action: Action) -> bool:
        """Запрашивает подтверждение на выполнение потенциально опасного действия"""
        if not self.confirm_dangerous_actions:
            return True
            
        print(f"\n[ПРЕДУПРЕЖДЕНИЕ] Запланировано потенциально опасное действие:")
        print(f"Тип: {action.type}")
        print(f"Данные: {action.model_dump()}")
        print("Продолжить? (y/n): ", end="")
        
        try:
            confirmation = input().strip().lower()
            return confirmation in ['y', 'yes', 'да']
        except KeyboardInterrupt:
            print("\nОтменено пользователем")
            return False
            
    def validate_and_filter_action(self, action: Action) -> tuple:
        """
        Валидирует действие и возвращает (разрешено, причина)
        """
        # Проверяем, не остановлен ли агент
        if not self.is_running:
            return False, "Агент остановлен по сигналу безопасности"
            
        # Проверяем безопасность действия
        if not self.is_safe_action(action):
            return False, "Действие заблокировано системой безопасности"
            
        # Для опасных действий требуем подтверждения
        if not self.is_safe_action(action):
            if not self.confirm_dangerous_action(action):
                return False, "Пользователь отменил действие"
                
        return True, "OK"
        
    def cleanup(self):
        """Очистка ресурсов"""
        if self.listener:
            self.listener.stop()
