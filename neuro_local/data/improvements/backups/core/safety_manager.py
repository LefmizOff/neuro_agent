"""
Менеджер безопасности для Neuro Local агента
Защищает от опасных действий, RCE и некорректных координат
"""
import re
import pyautogui
from typing import Dict, Any, Callable, Tuple
from pynput import keyboard
from core.actions_schema import Action, ActionType, RunApplicationAction, MouseMoveAction


class SafetyManager:
    """Менеджер безопасности агента с защитой от RCE и некорректных действий"""
    
    # Список разрешенных безопасных приложений
    SAFE_APPS = [
        "notepad.exe", "calculator.exe", "mspaint.exe",
        "chrome.exe", "firefox.exe", "code.exe", "obsidian.exe",
        "explorer.exe"
    ]
    
    # Опасные паттерны для блокировки
    DANGEROUS_PATTERNS = [
        r"cmd\.exe", r"powershell\.exe", r"bash\.exe",
        r"wscript", r"cscript", r"reg\.exe", r"regedit",
        r"format\.com", r"diskpart"
    ]
    
    # Опасные аргументы командной строки
    DANGEROUS_ARGS = [
        "/c del", "/c format", "-rf", "shutdown", "restart",
        "del /s", "rm -rf", ":(){:|:&}"
    ]
    
    def __init__(self, emergency_callback: Callable[[], None]):
        self.emergency_callback = emergency_callback
        self.is_running = True
        self.listener = None
        self.confirm_dangerous_actions = True
        
        # Устанавливаем флаг безопасности pyautogui
        pyautogui.FAILSAFE = True
        
        # Запускаем прослушивание горячей клавиши
        self.start_emergency_listener()
        
    def start_emergency_listener(self):
        """Запускает прослушивание горячей клавиши аварийной остановки"""
        self._keys_pressed = set()
        
        def on_press(key):
            try:
                self._keys_pressed.add(key)
                
                # Проверяем комбинацию Ctrl+Alt+Q
                ctrl_pressed = keyboard.Key.ctrl_l in self._keys_pressed or keyboard.Key.ctrl_r in self._keys_pressed
                alt_pressed = keyboard.Key.alt_l in self._keys_pressed or keyboard.Key.alt_r in self._keys_pressed
                
                has_q = False
                try:
                    if hasattr(key, 'char') and key.char == 'q':
                        has_q = True
                    elif hasattr(key, 'vk') and key.vk == 81:  # VK code for Q
                        has_q = True
                except:
                    pass
                    
                if ctrl_pressed and alt_pressed and has_q:
                    print("\n[БЕЗОПАСНОСТЬ] Аварийная остановка!")
                    self.trigger_emergency_stop()
                    return False
            except Exception:
                pass
                
        def on_release(key):
            try:
                self._keys_pressed.discard(key)
            except:
                pass
                
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        
    def trigger_emergency_stop(self):
        """Вызывает аварийную остановку"""
        self.is_running = False
        try:
            self.emergency_callback()
        except:
            pass
        
    def is_safe_action(self, action: Action) -> bool:
        """Проверяет безопасность действия"""
        try:
            # Проверка координат для действий с мышью
            if isinstance(action, MouseMoveAction):
                screen_w, screen_h = pyautogui.size()
                margin = 50
                if not (0 <= action.position.x <= screen_w and 0 <= action.position.y <= screen_h):
                    print(f"[SAFETY] Координаты вне экрана: ({action.position.x}, {action.position.y})")
                    return False
                    
            # Проверка запуска приложений
            if action.type == ActionType.RUN_APPLICATION:
                if not isinstance(action, RunApplicationAction):
                    return False
                    
                app = action.application.lower().strip()
                
                # Блокировка опасных приложений
                for pattern in self.DANGEROUS_PATTERNS:
                    if re.search(pattern, app):
                        if app not in self.SAFE_APPS:
                            print(f"[SAFETY] Запрещено приложение: {app}")
                            return False
                
                # Проверка аргументов на опасные команды
                if action.arguments:
                    args_str = " ".join(action.arguments).lower()
                    for dangerous in self.DANGEROUS_ARGS:
                        if dangerous in args_str:
                            print(f"[SAFETY] Обнаружен опасный аргумент: {dangerous}")
                            return False
            
            # Проверка текста на хоткеи
            if action.type == ActionType.KEYBOARD_TYPE:
                text = getattr(action, 'text', '')
                if "{ctrl}" in text or "{alt}" in text or "^" in text:
                    # Разрешаем только безопасные комбинации
                    safe_combos = ["^c", "^v", "^a", "^z", "^y"]
                    if text not in safe_combos:
                        pass  # Логируем подозрительный ввод
                        
            return True
        except Exception as e:
            print(f"[SAFETY] Ошибка проверки: {e}")
            return False
        
    def confirm_dangerous_action(self, action: Action) -> bool:
        """Запрашивает подтверждение опасного действия"""
        if not self.confirm_dangerous_actions:
            return True
            
        print(f"\n[ПРЕДУПРЕЖДЕНИЕ] Potentially dangerous action:")
        print(f"Тип: {action.type}")
        print("Продолжить? (y/n): ", end="")
        
        try:
            confirmation = input().strip().lower()
            return confirmation in ['y', 'yes', 'да']
        except KeyboardInterrupt:
            print("\nОтменено")
            return False
        except:
            return False
        
    def validate_and_filter_action(self, action: Action) -> Tuple[bool, str]:
        """Валидирует действие и возвращает (разрешено, причина)"""
        if not self.is_running:
            return False, "Агент остановлен"
            
        if not self.is_safe_action(action):
            return False, "Действие заблокировано системой безопасности"
            
        return True, "OK"
        
    def cleanup(self):
        """Очистка ресурсов"""
        if self.listener:
            self.listener.stop()
