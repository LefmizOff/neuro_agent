"""Тесты для core модулей."""

import pytest
from pathlib import Path
import sys

# Добавляем parent directory в path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOllamaClient:
    """Тесты для OllamaClient."""
    
    def test_import(self):
        """Проверка импорта."""
        from core.ollama_client import OllamaClient, VisionModel, LLMModel
        
        assert VisionModel.QWEN_VL == "qwen2.5vl:7b"
        assert LLMModel.QWEN_INSTRUCT == "qwen2.5:7b-instruct"
    
    def test_client_init(self):
        """Инициализация клиента."""
        from core.ollama_client import OllamaClient
        
        client = OllamaClient()
        assert client.vision_model == "qwen2.5vl:7b"
        assert client.llm_model == "qwen2.5:7b-instruct"


class TestActionSchema:
    """Тесты для схемы действий."""
    
    def test_click_action(self):
        """Создание действия клика."""
        from core.actions_schema import ClickAction, TargetPosition, ActionSchema
        
        action = ClickAction(
            target=TargetPosition(x=100, y=200),
            button="left",
            reason="Тестовый клик"
        )
        
        schema = ActionSchema(action=action)
        assert schema.action.action_type.value == "click"
    
    def test_wait_action(self):
        """Создание действия ожидания."""
        from core.actions_schema import WaitAction, ActionSchema
        
        action = WaitAction(seconds=2.0, reason="Ждём загрузки")
        schema = ActionSchema(action=action)
        
        assert schema.action.action_type.value == "wait"
        assert schema.action.seconds == 2.0
    
    def test_invalid_coordinates(self):
        """Проверка валидации координат."""
        from core.actions_schema import TargetPosition
        
        with pytest.raises(ValueError):
            TargetPosition(x=-1, y=100)


class TestSafetyManager:
    """Тесты для менеджера безопасности."""
    
    def test_dry_run_default(self):
        """Проверка dry-run по умолчанию."""
        from core.safety_manager import SafetyManager
        
        manager = SafetyManager()
        assert manager.dry_run is True
    
    def test_danger_level_classification(self):
        """Классификация уровней опасности."""
        from core.safety_manager import SafetyManager, DangerLevel
        from core.actions_schema import WaitAction, ActionSchema
        
        manager = SafetyManager()
        action = ActionSchema(action=WaitAction(seconds=1.0, reason="test"))
        
        level = manager.check_action(action)
        assert level == DangerLevel.SAFE


class TestConfigLoader:
    """Тесты загрузчика конфигурации."""
    
    def test_default_config(self):
        """Конфигурация по умолчанию."""
        from core.config_loader import ConfigLoader
        
        loader = ConfigLoader(config_path="nonexistent.yaml")
        config = loader.load()
        
        assert "ollama" in config
        assert config["ollama"]["base_url"] == "http://127.0.0.1:11434"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
