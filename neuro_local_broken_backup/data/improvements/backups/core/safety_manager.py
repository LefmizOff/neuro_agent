"""
Менеджер безопасности для контроля опасных действий.

Обеспечивает:
- Проверку действий на опасность
- Запрос подтверждения для рискованных операций
- Аварийную остановку по горячей клавише
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import threading
from pynput import keyboard

from .actions_schema import ActionSchema, ActionType

logger = logging.getLogger(__name__)


class DangerLevel(str, Enum):
    """Уровень опасности действия."""
    SAFE = "safe"  # Безопасное действие
    LOW = "low"  # Низкий риск
    MEDIUM = "medium"  # Средний риск
    HIGH = "high"  # Высокий риск
    CRITICAL = "critical"  # Критически опасное


class SafetyManager:
    """
    Менеджер безопасности.
    
    Контролирует выполнение действий и обеспечивает аварийную остановку.
    """
    
    # Классификация опасных действий
    DANGEROUS_ACTIONS = {
        # Удаление файлов и директорий
        "delete_file": DangerLevel.CRITICAL,
        "delete_directory": DangerLevel.CRITICAL,
        
        # Запуск исполняемых файлов
        "execute": DangerLevel.HIGH,
        "download_and_run": DangerLevel.CRITICAL,
        
        # Системные настройки
        "system_settings_change": DangerLevel.HIGH,
        "registry_change": DangerLevel.CRITICAL,
        
        # Сетевые действия
        "send_message": DangerLevel.MEDIUM,
        "open_url": DangerLevel.LOW,
        "download_file": DangerLevel.MEDIUM,
        
        # Финансовые действия
        "purchase": DangerLevel.CRITICAL,
        "payment": DangerLevel.CRITICAL,
        
        # Доступ к данным
        "access_credentials": DangerLevel.HIGH,
        "copy_sensitive_data": DangerLevel.MEDIUM,
    }
    
    # Паттерны опасных команд/текстов
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "del /f",
        "format",
        "shutdown",
        "reboot",
        "sudo",
        "admin",
        "password",
        "credit card",
        "cvv",
    ]
    
    def __init__(
        self,
        dry_run: bool = True,
        require_confirmation: bool = True,
        emergency_hotkey: str = "ctrl+alt+q"
    ):
        """
        Инициализация менеджера безопасности.
        
        Args:
            dry_run: Если True, действия только логируются, не выполняются
            require_confirmation: Требовать подтверждение для опасных действий
            emergency_hotkey: Горячая клавиша для аварийной остановки
        """
        self.dry_run = dry_run
        self.require_confirmation = require_confirmation
        self.emergency_hotkey = emergency_hotkey
        
        self._is_running = True
        self._confirmation_callbacks: List[Callable[[str], bool]] = []
        self._emergency_listeners: List[Callable[[], None]] = []
        
        # Настройка горячей клавиши
        self._setup_emergency_hotkey()
        
        logger.info(f"SafetyManager инициализирован (dry_run={dry_run})")
    
    def _setup_emergency_hotkey(self) -> None:
        """Настраивает горячую клавишу аварийной остановки."""
        # Парсим комбинацию клавиш
        keys = self.emergency_hotkey.split('+')
        
        # Определяем модификаторы и основную клавишу
        self._emergency_keys = set(k.lower().strip() for k in keys)
        
        # Создаем слушателя
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            suppress=False
        )
        self._listener.start()
        
        logger.info(f"Аварийная горячая клавиша: {self.emergency_hotkey}")
    
    def _on_key_press(self, key: keyboard.Key) -> Optional[bool]:
        """Обрабатывает нажатие клавиши для аварийной остановки."""
        try:
            # Получаем имя клавиши
            if hasattr(key, 'char'):
                key_name = key.char.lower()
            else:
                key_name = str(key).replace('Key.', '').lower()
            
            # Проверяем комбинацию
            # TODO: Реализовать полноценное отслеживание комбинаций
            # Сейчас упрощённая проверка
            if key_name == 'q':
                # Проверяем, нажаты ли Ctrl+Alt
                # Это упрощение - в полной версии нужно отслеживать состояние модификаторов
                pass
                
        except Exception as e:
            logger.error(f"Ошибка обработки клавиши: {e}")
        
        return True
    
    def check_action(self, action: ActionSchema) -> DangerLevel:
        """
        Проверяет уровень опасности действия.
        
        Args:
            action: Действие для проверки
            
        Returns:
            Уровень опасности
        """
        action_type = action.action.action_type.value
        reason = action.action.reason.lower()
        
        # Прямая проверка типа действия
        if action_type in self.DANGEROUS_ACTIONS:
            return self.DANGEROUS_ACTIONS[action_type]
        
        # Проверка по паттернам в описании
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in reason:
                return DangerLevel.MEDIUM
        
        # Специфические проверки для типов действий
        if action_type == ActionType.LAUNCH_APP.value:
            # Проверка запускаемых приложений
            app_name = getattr(action.action, 'app_name', '').lower()
            if any(ext in app_name for ext in ['.exe', '.bat', '.cmd', '.ps1']):
                return DangerLevel.LOW
        
        if action_type == ActionType.TYPE.value:
            # Проверка вводимого текста
            text = getattr(action.action, 'text', '').lower()
            if any(pattern in text for pattern in self.DANGEROUS_PATTERNS):
                return DangerLevel.MEDIUM
        
        return DangerLevel.SAFE
    
    def requires_confirmation(self, action: ActionSchema) -> bool:
        """
        Проверяет, требует ли действие подтверждения.
        
        Args:
            action: Действие для проверки
            
        Returns:
            True если требуется подтверждение
        """
        if not self.require_confirmation:
            return False
        
        danger_level = self.check_action(action)
        return danger_level in [DangerLevel.MEDIUM, DangerLevel.HIGH, DangerLevel.CRITICAL]
    
    def request_confirmation(self, action: ActionSchema) -> bool:
        """
        Запрашивает подтверждение выполнения действия.
        
        Args:
            action: Действие для подтверждения
            
        Returns:
            True если пользователь подтвердил
        """
        if not self.requires_confirmation(action):
            return True
        
        danger_level = self.check_action(action)
        action_desc = action.action.reason
        
        print(f"\n⚠️  ОПАСНОЕ ДЕЙСТВИЕ ({danger_level.value})")
        print(f"Действие: {action.action.action_type.value}")
        print(f"Описание: {action_desc}")
        print(f"Dry-run: {self.dry_run}")
        
        if self.dry_run:
            print("✅ Действие будет ЗАПРОТОКОЛИРОВАНО, но НЕ ВЫПОЛНЕНО")
            return True
        
        try:
            response = input("\nВыполнить это действие? (y/n): ").strip().lower()
            confirmed = response in ['y', 'yes', 'да']
            
            if not confirmed:
                logger.warning(f"Действие отклонено пользователем: {action_desc}")
            
            return confirmed
            
        except Exception as e:
            logger.error(f"Ошибка запроса подтверждения: {e}")
            return False
    
    def can_execute(self, action: ActionSchema) -> bool:
        """
        Проверяет, можно ли выполнить действие.
        
        Args:
            action: Действие для проверки
            
        Returns:
            True если действие можно выполнить
        """
        if not self._is_running:
            return False
        
        danger_level = self.check_action(action)
        
        # Блокируем критические действия даже в боевом режиме
        if danger_level == DangerLevel.CRITICAL:
            logger.critical(f"Критическое действие заблокировано: {action.action.reason}")
            print(f"\n🚫 КРИТИЧЕСКОЕ ДЕЙСТВИЕ ЗАБЛОКИРОВАНО:")
            print(f"   {action.action.reason}")
            return False
        
        # Для опасных действий требуем подтверждения
        if self.requires_confirmation(action):
            return self.request_confirmation(action)
        
        return True
    
    def is_dry_run(self) -> bool:
        """Возвращает режим dry-run."""
        return self.dry_run
    
    def set_dry_run(self, value: bool) -> None:
        """Устанавливает режим dry-run."""
        self.dry_run = value
        logger.info(f"Dry-run режим: {value}")
    
    def register_emergency_listener(self, callback: Callable[[], None]) -> None:
        """Регистрирует слушатель аварийной остановки."""
        self._emergency_listeners.append(callback)
    
    def trigger_emergency_stop(self) -> None:
        """Активирует аварийную остановку."""
        logger.critical("АВАРИЙНАЯ ОСТАНОВКА!")
        self._is_running = False
        
        for callback in self._emergency_listeners:
            try:
                callback()
            except Exception as e:
                logger.error(f"Ошибка в emergency listener: {e}")
        
        print("\n🛑 АВАРИЙНАЯ ОСТАНОВКА АКТИВИРОВАНА")
    
    @property
    def is_running(self) -> bool:
        """Проверяет, работает ли система."""
        return self._is_running
    
    def stop(self) -> None:
        """Останавливает менеджер безопасности."""
        self._is_running = False
        if hasattr(self, '_listener'):
            self._listener.stop()
        logger.info("SafetyManager остановлен")
