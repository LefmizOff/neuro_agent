"""
Реестр навыков агента.

Навыки могут быть:
- Встроенные (Python)
- YAML (декларативные)
- Динамические (из памяти)
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class Skill:
    """Базовый класс навыка."""
    
    def __init__(
        self,
        name: str,
        description: str,
        trigger_keywords: List[str]
    ):
        self.name = name
        self.description = description
        self.trigger_keywords = trigger_keywords
    
    def can_execute(self, query: str) -> bool:
        """Проверяет, подходит ли навык для запроса."""
        query_lower = query.lower()
        return any(kw.lower() in query_lower for kw in self.trigger_keywords)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет навык."""
        raise NotImplementedError


class BuiltInSkill(Skill):
    """Встроенный навык (Python)."""
    
    def __init__(
        self,
        name: str,
        description: str,
        trigger_keywords: List[str],
        func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        super().__init__(name, description, trigger_keywords)
        self.func = func
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.func(context)
        except Exception as e:
            logger.error(f"Ошибка выполнения навыка {self.name}: {e}")
            return {"success": False, "error": str(e)}


class YAMLSkill(Skill):
    """YAML декларативный навык."""
    
    def __init__(
        self,
        name: str,
        description: str,
        trigger_keywords: List[str],
        steps: List[Dict[str, Any]]
    ):
        super().__init__(name, description, trigger_keywords)
        self.steps = steps
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Реализовать выполнение шагов из YAML
        return {
            "skill": self.name,
            "steps": self.steps,
            "context": context
        }


class SkillRegistry:
    """Реестр навыков."""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        
        self._register_builtin_skills()
        self._load_yaml_skills()
        
        logger.info(f"SkillRegistry инициализирован: {len(self.skills)} навыков")
    
    def _register_builtin_skills(self) -> None:
        """Регистрирует встроенные навыки."""
        
        # Навык: открыть приложение
        self.register(BuiltInSkill(
            name="open_app",
            description="Открыть приложение",
            trigger_keywords=["открыть", "запустить", "launch", "open"],
            func=self._open_app_skill
        ))
        
        # Навык: закрыть приложение
        self.register(BuiltInSkill(
            name="close_app",
            description="Закрыть приложение",
            trigger_keywords=["закрыть", "close"],
            func=self._close_app_skill
        ))
        
        # Навык: поиск текста
        self.register(BuiltInSkill(
            name="find_text",
            description="Найти текст на экране",
            trigger_keywords=["найти", "поиск", "find", "search"],
            func=self._find_text_skill
        ))
        
        # Навык: сделать скриншот
        self.register(BuiltInSkill(
            name="screenshot",
            description="Сделать скриншот",
            trigger_keywords=["скриншот", "screenshot", "снимок"],
            func=self._screenshot_skill
        ))
    
    def _open_app_skill(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Навык открытия приложения."""
        app_name = context.get("app_name", "unknown")
        return {
            "success": True,
            "action": "launch_app",
            "app": app_name
        }
    
    def _close_app_skill(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Навык закрытия приложения."""
        return {
            "success": True,
            "action": "close_window"
        }
    
    def _find_text_skill(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Навык поиска текста."""
        search_text = context.get("text", "")
        return {
            "success": True,
            "action": "ocr_search",
            "text": search_text
        }
    
    def _screenshot_skill(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Навык скриншота."""
        return {
            "success": True,
            "action": "take_screenshot"
        }
    
    def _load_yaml_skills(self) -> None:
        """Загружает навыки из YAML файлов."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for yaml_file in self.skills_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data and isinstance(data, dict):
                    skill = YAMLSkill(
                        name=data.get("name", yaml_file.stem),
                        description=data.get("description", ""),
                        trigger_keywords=data.get("triggers", []),
                        steps=data.get("steps", [])
                    )
                    self.skills[skill.name] = skill
                    logger.debug(f"Загружен навык из YAML: {skill.name}")
                    
            except Exception as e:
                logger.error(f"Ошибка загрузки навыка {yaml_file}: {e}")
    
    def register(self, skill: Skill) -> None:
        """Регистрирует навык."""
        self.skills[skill.name] = skill
        logger.debug(f"Зарегистрирован навык: {skill.name}")
    
    def unregister(self, name: str) -> None:
        """Удаляет навык из реестра."""
        if name in self.skills:
            del self.skills[name]
            logger.debug(f"Удалён навык: {name}")
    
    def find_skill(self, query: str) -> Optional[Skill]:
        """Ищет навык по запросу."""
        for skill in self.skills.values():
            if skill.can_execute(query):
                return skill
        return None
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Находит и выполняет подходящий навык.
        
        Args:
            query: Запрос пользователя
            context: Контекст выполнения
            
        Returns:
            Результат выполнения
        """
        context = context or {}
        context["query"] = query
        
        skill = self.find_skill(query)
        
        if skill:
            logger.info(f"Выполнение навыка: {skill.name}")
            result = skill.execute(context)
            result["skill_name"] = skill.name
            return result
        else:
            return {
                "success": False,
                "error": "Навык не найден",
                "query": query
            }
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """Возвращает список всех навыков."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "triggers": s.trigger_keywords
            }
            for s in self.skills.values()
        ]
