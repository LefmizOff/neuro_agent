"""
Загрузчик конфигурации для Neuro Local агента
"""
import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    def __init__(self, config_path: str = "./config/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        # Загружаем конфигурацию если файл существует
        if self.config_path.exists():
            self.load_config()
        else:
            # Используем значения по умолчанию если файла нет
            self._config = self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию по умолчанию"""
        return {
            "ollama": {
                "host": "http://127.0.0.1:11434",
                "vision_model": "qwen2.5vl:7b",
                "text_model": "qwen2.5:7b-instruct",
                "timeout": 120
            },
            "safety": {
                "emergency_hotkey": "ctrl+alt+q",
                "timeout": 30,
                "failsafe": True,
                "confirm_dangerous_actions": True
            },
            "memory": {
                "db_path": "./data/memory.db",
                "max_episodes": 1000,
                "max_facts": 500,
                "max_skills": 100,
                "max_errors": 200
            },
            "paths": {
                "logs_dir": "./data/logs",
                "screenshots_dir": "./data/screenshots",
                "improvements_dir": "./data/improvements"
            },
            "actions": {
                "default_delay": 0.5,
                "max_retries": 3,
                "dry_run": True
            }
        }
        
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из YAML файла"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
                
            # Заменяем переменные окружения в конфиге
            self._replace_env_vars(self._config)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}. Используются значения по умолчанию.")
            self._config = self._get_default_config()
            
        return self._config
        
    def _replace_env_vars(self, obj):
        """Рекурсивно заменяет переменные окружения в значениях конфига"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._replace_env_vars(item)
        elif isinstance(obj, str):
            import re
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            for match in matches:
                env_var = os.getenv(match)
                if env_var:
                    obj = obj.replace(f"${{{match}}}", env_var)
                    
        return obj
        
    def get(self, key: str, default=None):
        """Получает значение из конфига по точечному пути"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    @property
    def config(self) -> Dict[str, Any]:
        """Возвращает полную конфигурацию"""
        return self._config
