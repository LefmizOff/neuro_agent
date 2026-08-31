"""
Загрузчик конфигурации из YAML файлов.

Поддерживает:
- Загрузку из config.yaml
- Переопределение через .env
- Валидацию настроек
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Загрузчик и менеджер конфигурации.
    
    Загружает настройки из YAML файла и переопределяет через переменные окружения.
    """
    
    DEFAULT_CONFIG_PATH = "config/config.yaml"
    DEFAULT_ENV_PATH = ".env"
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_path: Optional[str] = None
    ):
        """
        Инициализация загрузчика конфигурации.
        
        Args:
            config_path: Путь к YAML файлу конфигурации
            env_path: Путь к .env файлу
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.env_path = env_path or self.DEFAULT_ENV_PATH
        
        self._config: Dict[str, Any] = {}
        self._loaded = False
        
        # Загружаем переменные окружения
        self._load_env()
        
        logger.info(f"ConfigLoader инициализирован: {self.config_path}")
    
    def _load_env(self) -> None:
        """Загружает переменные окружения из .env файла."""
        env_file = Path(self.env_path)
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug(f"Загружен .env файл: {env_file}")
        else:
            logger.debug(".env файл не найден, используем системные переменные")
    
    def load(self) -> Dict[str, Any]:
        """
        Загружает конфигурацию из YAML файла.
        
        Returns:
            Словарь конфигурации
        """
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(f"Файл конфигурации не найден: {config_file}")
            self._config = self._get_default_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Конфигурация загружена: {config_file}")
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации: {e}")
                self._config = self._get_default_config()
        
        # Применяем переменные окружения
        self._apply_env_overrides()
        
        self._loaded = True
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию по умолчанию."""
        return {
            "ollama": {
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                "vision_model": os.getenv("VISION_MODEL", "qwen2.5vl:7b"),
                "llm_model": os.getenv("LLM_MODEL", "qwen2.5:7b-instruct"),
                "timeout": 120
            },
            "security": {
                "dry_run": os.getenv("DRY_RUN", "true").lower() == "true",
                "emergency_hotkey": os.getenv("EMERGENCY_HOTKEY", "ctrl+alt+q"),
                "failsafe_enabled": True,
                "require_confirmation": True
            },
            "perception": {
                "screenshot_interval": 1.0,
                "ocr_enabled": True,
                "ui_detection_enabled": True,
                "set_of_mark_enabled": True,
                "max_ui_elements": 20
            },
            "memory": {
                "db_path": "data/memory/neuro_memory.db",
                "max_episodes": 10000,
                "rerank_top_k": 5
            },
            "speech": {
                "tts_enabled": True,
                "tts_voice_id": 0,
                "tts_rate": 150,
                "stt_enabled": False
            },
            "action": {
                "mouse_speed": 0.5,
                "keyboard_delay": 0.05,
                "click_pause": 0.1
            },
            "minecraft": {
                "enabled": True,
                "window_title": "Minecraft",
                "use_pydirectinput": True
            },
            "logging": {
                "level": "INFO",
                "jsonl_enabled": True,
                "logs_dir": "data/logs"
            },
            "evolution": {
                "enabled": True,
                "improvements_dir": "data/improvements",
                "auto_apply": False
            }
        }
    
    def _apply_env_overrides(self) -> None:
        """Применяет переопределения из переменных окружения."""
        # Ollama настройки
        if os.getenv("OLLAMA_BASE_URL"):
            self._config.setdefault("ollama", {})["base_url"] = os.getenv("OLLAMA_BASE_URL")
        if os.getenv("VISION_MODEL"):
            self._config.setdefault("ollama", {})["vision_model"] = os.getenv("VISION_MODEL")
        if os.getenv("LLM_MODEL"):
            self._config.setdefault("ollama", {})["llm_model"] = os.getenv("LLM_MODEL")
        
        # Безопасность
        if os.getenv("DRY_RUN"):
            self._config.setdefault("security", {})["dry_run"] = os.getenv("DRY_RUN").lower() == "true"
        if os.getenv("EMERGENCY_HOTKEY"):
            self._config.setdefault("security", {})["emergency_hotkey"] = os.getenv("EMERGENCY_HOTKEY")
        
        # Пути
        if os.getenv("LOGS_DIR"):
            self._config.setdefault("logging", {})["logs_dir"] = os.getenv("LOGS_DIR")
        if os.getenv("MEMORY_DIR"):
            self._config.setdefault("memory", {})["db_path"] = os.path.join(
                os.getenv("MEMORY_DIR"), "neuro_memory.db"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение по ключу.
        
        Args:
            key: Ключ в формате "section.key" или "section"
            default: Значение по умолчанию
            
        Returns:
            Значение конфигурации
        """
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Получает целый раздел конфигурации.
        
        Args:
            section: Название раздела
            
        Returns:
            Словарь раздела
        """
        if not self._loaded:
            self.load()
        
        return self._config.get(section, {})
    
    @property
    def ollama_config(self) -> Dict[str, Any]:
        """Конфигурация Ollama."""
        return self.get_section("ollama")
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Конфигурация безопасности."""
        return self.get_section("security")
    
    @property
    def perception_config(self) -> Dict[str, Any]:
        """Конфигурация восприятия."""
        return self.get_section("perception")
    
    @property
    def memory_config(self) -> Dict[str, Any]:
        """Конфигурация памяти."""
        return self.get_section("memory")
    
    @property
    def minecraft_config(self) -> Dict[str, Any]:
        """Конфигурация Minecraft."""
        return self.get_section("minecraft")
    
    def reload(self) -> Dict[str, Any]:
        """Перезагружает конфигурацию из файла."""
        self._loaded = False
        return self.load()
