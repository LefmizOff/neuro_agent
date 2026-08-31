"""
Планировщик задач для агента.

Использует LLM (qwen2.5:7b-instruct) для генерации планов действий.
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .ollama_client import OllamaClient, LLMModel
from .actions_schema import ActionSchema, ActionType

logger = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """Шаг плана."""
    step_number: int
    description: str
    expected_outcome: str


class Plan(BaseModel):
    """План выполнения задачи."""
    goal: str
    steps: List[PlanStep]
    current_step: int = 0
    completed_steps: List[int] = []
    
    def next_step(self) -> Optional[PlanStep]:
        """Возвращает следующий шаг."""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def mark_completed(self, step_number: int) -> None:
        """Отмечает шаг как выполненный."""
        if step_number not in self.completed_steps:
            self.completed_steps.append(step_number)
        self.current_step = max(self.completed_steps) + 1 if self.completed_steps else 0
    
    def is_complete(self) -> bool:
        """Проверяет завершённость плана."""
        return self.current_step >= len(self.steps)


class Planner:
    """
    Планировщик задач на основе LLM.
    
    Генерирует пошаговые планы и определяет следующее действие.
    """
    
    SYSTEM_PROMPT = """Ты — планировщик задач локального ИИ-агента Neuro.
Твоя задача — разбивать сложные цели на простые шаги и определять конкретные действия.

Важные правила:
1. Всегда действуй безопасно — не предлагай опасных действий без подтверждения
2. Учитывай контекст: активное окно, позицию мыши, видимые элементы
3. Если не уверен — предложи подождать или запросить уточнение
4. Используй память о предыдущих успехах и ошибках
5. Действия должны быть конкретными и выполнимыми

Формат ответа:
1. Краткий анализ ситуации
2. План шагов (если задача сложная)
3. Конкретное следующее действие в JSON формате

Доступные типы действий:
- click: клик мышью по координатам
- double_click: двойной клик
- right_click: правый клик
- move: перемещение мыши
- drag: перетаскивание
- type: ввод текста
- press_key: нажатие клавиши
- hotkey: комбинация клавиш (например, ctrl+c)
- wait: ожидание
- scroll: прокрутка
- launch_app: запуск приложения
- close_window: закрытие окна
- speak: произнесение текста
- none: бездействие (ожидание)

ВАЖНО: Ответ должен содержать JSON объекта с полем "action", который соответствует схеме ActionSchema."""

    def __init__(self, ollama_client: OllamaClient):
        """
        Инициализация планировщика.
        
        Args:
            ollama_client: Клиент Ollama для работы с LLM
        """
        self.client = ollama_client
        self.current_plan: Optional[Plan] = None
        self.action_history: List[Dict[str, Any]] = []
        
        logger.info("Planner инициализирован")
    
    def create_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        memories: Optional[List[str]] = None
    ) -> Plan:
        """
        Создаёт план выполнения задачи.
        
        Args:
            goal: Цель задачи
            context: Контекст (окно, скриншот описание, последние действия)
            memories: Релевантные воспоминания из памяти
            
        Returns:
            План выполнения
        """
        prompt = self._build_plan_prompt(goal, context, memories)
        
        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2048
            )
            
            # Парсим ответ для извлечения шагов
            steps = self._parse_plan_steps(response, goal)
            
            self.current_plan = Plan(goal=goal, steps=steps)
            logger.info(f"Создан план: {len(steps)} шагов для цели '{goal}'")
            
            return self.current_plan
            
        except Exception as e:
            logger.error(f"Ошибка создания плана: {e}")
            # Возвращаем минимальный план
            return Plan(
                goal=goal,
                steps=[PlanStep(step_number=1, description="Выполнить задачу", expected_outcome="Задача выполнена")]
            )
    
    def get_next_action(
        self,
        goal: str,
        perception: Dict[str, Any],
        memories: Optional[List[str]] = None
    ) -> ActionSchema:
        """
        Определяет следующее действие на основе текущего состояния.
        
        Args:
            goal: Текущая цель
            perception: Данные восприятия (скриншот, OCR, UI элементы)
            memories: Релевантные воспоминания
            
        Returns:
            Следующее действие
        """
        prompt = self._build_action_prompt(goal, perception, memories)
        
        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Более детерминированный выбор
                max_tokens=1024
            )
            
            # Извлекаем JSON действия из ответа
            action = self._parse_action(response)
            
            # Сохраняем в историю
            self.action_history.append({
                "goal": goal,
                "perception_summary": str(perception)[:200],
                "action": action.to_dict()
            })
            
            return action
            
        except Exception as e:
            logger.error(f"Ошибка определения действия: {e}")
            # Возвращаем безопасное действие ожидания
            from .actions_schema import WaitAction, ActionSchema
            return ActionSchema(
                action=WaitAction(seconds=2.0, reason=f"Ошибка планирования: {e}")
            )
    
    def _build_plan_prompt(
        self,
        goal: str,
        context: Dict[str, Any],
        memories: Optional[List[str]] = None
    ) -> str:
        """Строит промпт для создания плана."""
        parts = [f"Цель: {goal}\n"]
        
        if context.get("active_window"):
            parts.append(f"Активное окно: {context['active_window']}\n")
        
        if context.get("description"):
            parts.append(f"Описание экрана: {context['description']}\n")
        
        if context.get("last_actions"):
            parts.append("Последние действия:\n")
            for i, action in enumerate(context["last_actions"][-5:], 1):
                parts.append(f"  {i}. {action}\n")
        
        if memories:
            parts.append("\nРелевантные воспоминания:\n")
            for mem in memories[:3]:
                parts.append(f"  - {mem}\n")
        
        parts.append("\nСоздай пошаговый план выполнения задачи.")
        
        return "".join(parts)
    
    def _build_action_prompt(
        self,
        goal: str,
        perception: Dict[str, Any],
        memories: Optional[List[str]] = None
    ) -> str:
        """Строит промпт для определения следующего действия."""
        parts = [f"Цель: {goal}\n\n"]
        
        # Информация о восприятии
        parts.append("Текущее состояние:\n")
        
        if perception.get("active_window"):
            parts.append(f"- Активное окно: {perception['active_window']}\n")
        
        if perception.get("mouse_position"):
            pos = perception["mouse_position"]
            parts.append(f"- Позиция мыши: ({pos['x']}, {pos['y']})\n")
        
        if perception.get("screen_description"):
            parts.append(f"- Описание экрана: {perception['screen_description']}\n")
        
        if perception.get("ocr_text"):
            text = perception["ocr_text"][:500]
            parts.append(f"- Найденный текст: {text}...\n")
        
        if perception.get("ui_elements"):
            elements = perception["ui_elements"][:5]
            parts.append(f"- UI элементы: {elements}\n")
        
        # Последние действия
        if self.action_history:
            parts.append("\nПоследние действия:\n")
            for item in self.action_history[-5:]:
                action_type = item["action"]["action"]["action_type"]
                reason = item["action"]["action"].get("reason", "")
                parts.append(f"  - {action_type}: {reason}\n")
        
        # Воспоминания
        if memories:
            parts.append("\nПолезные воспоминания:\n")
            for mem in memories[:3]:
                parts.append(f"  - {mem}\n")
        
        parts.append("\n\nОпредели следующее конкретное действие. Ответ должен содержать JSON с полем 'action'.")
        
        return "".join(parts)
    
    def _parse_plan_steps(self, response: str, goal: str) -> List[PlanStep]:
        """Парсит ответ LLM для извлечения шагов плана."""
        # Простая эвристика для извлечения шагов
        steps = []
        lines = response.split('\n')
        
        step_number = 1
        for line in lines:
            line = line.strip()
            # Ищем строки вида "1. Описание шага"
            if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                try:
                    # Извлекаем номер и описание
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        desc = parts[1].strip()
                        steps.append(PlanStep(
                            step_number=step_number,
                            description=desc,
                            expected_outcome=f"Шаг {step_number} выполнен"
                        ))
                        step_number += 1
                except Exception:
                    continue
        
        # Если не нашли структурированные шаги, создаём один общий
        if not steps:
            steps = [PlanStep(
                step_number=1,
                description=f"Выполнить: {goal}",
                expected_outcome="Задача выполнена"
            )]
        
        return steps
    
    def _parse_action(self, response: str) -> ActionSchema:
        """Парсит ответ LLM для извлечения JSON действия с улучшенной обработкой."""
        import json
        import re
        
        if not response or not response.strip():
            logger.warning("Пустой ответ от LLM")
            return self._fallback_action("Пустой ответ от модели")
        
        # Пытаемся найти JSON в ответе (включая markdown блоки)
        json_patterns = [
            r'```(?:json)?\s*(\{[^{}]*"action"[^{}]*\})\s*```',  # Markdown блок с action
            r'```(?:json)?\s*(\{[^{}]*"action_type"[^{}]*\})\s*```',  # Markdown блок с action_type
            r'(\{[^{}]*"action"[^{}]*\})',  # Объект с полем action
            r'(\{[^{}]*"action_type"[^{}]*\})',  # Объект с action_type
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1) if match.lastindex else match.group(0)
                try:
                    data = json.loads(json_str)
                    return ActionSchema.model_validate(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Validation error: {e}")
                    continue
        
        # Если не нашли JSON, пробуем распарсить весь ответ
        try:
            data = json.loads(response.strip())
            return ActionSchema.model_validate(data)
        except Exception:
            pass
        
        # Fallback: возвращаем действие ожидания
        return self._fallback_action("Не удалось распарсить ответ LLM")
    
    def _fallback_action(self, reason: str) -> ActionSchema:
        """Создаёт безопасное fallback действие."""
        from .actions_schema import WaitAction
        logger.warning(f"Используется fallback действие: {reason}")
        return ActionSchema(
            action=WaitAction(seconds=2.0, reason=reason)
        )
    
    def reset(self) -> None:
        """Сбрасывает текущий план и историю."""
        self.current_plan = None
        self.action_history = []
        logger.info("Planner сброшен")
