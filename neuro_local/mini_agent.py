#!/usr/bin/env python3
"""
Минимальный рабочий агент Neuro.

Скриншот → qwen2.5vl:7b → JSON-действие → dry-run или --run

Использование:
    python mini_agent.py --dry-run     # Режим просмотра (по умолчанию)
    python mini_agent.py --run         # Боевой режим
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent))

from core.ollama_client import OllamaClient, VisionModel, LLMModel
from core.actions_schema import ActionSchema, WaitAction
from perception.screen_capture import ScreenCapture

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты — визуальный ИИ-ассистент Neuro. Твоя задача — анализировать скриншоты экрана и определять следующее действие.

Доступные типы действий:
- click: клик мышью (требует x, y координаты)
- double_click: двойной клик
- right_click: правый клик
- move: перемещение мыши
- type: ввод текста
- press_key: нажатие клавиши
- hotkey: комбинация клавиш (например, ["ctrl", "c"])
- wait: ожидание (в секундах)
- scroll: прокрутка
- none: бездействие

Ответь ТОЛЬКО JSON объектом в формате:
{
    "action": {
        "action_type": "<тип>",
        ...параметры...
        "reason": "<обоснование>"
    },
    "confidence": 0.0-1.0
}

Пример ответа для клика:
{
    "action": {
        "action_type": "click",
        "target": {"x": 100, "y": 200},
        "button": "left",
        "reason": "Нажать кнопку Сохранить"
    },
    "confidence": 0.95
}"""


class MiniAgent:
    """Минимальный агент."""
    
    def __init__(self, dry_run: bool = True):
        """Инициализация агента."""
        self.dry_run = dry_run
        
        # Инициализация компонентов
        self.ollama = OllamaClient()
        self.screen = ScreenCapture()
        
        logger.info(f"MiniAgent инициализирован (dry_run={dry_run})")
    
    def run_cycle(self, goal: str = "Опиши что видишь и предложи действие") -> dict:
        """
        Выполняет один цикл работы агента.
        
        Args:
            goal: Цель/задача для текущего цикла
            
        Returns:
            Результат выполнения
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "success": False
        }
        
        try:
            # 1. Делаем скриншот
            logger.info("Захват скриншота...")
            screenshot = self.screen.capture_full()
            
            # 2. Отправляем в VLM
            logger.info("Анализ скриншота через qwen2.5vl:7b...")
            prompt = f"{goal}\n\nПроанализируй этот скриншот и определи следующее действие."
            
            response = self.ollama.vision_chat(
                image=screenshot,
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=1024
            )
            
            result["vision_response"] = response[:500] + "..." if len(response) > 500 else response
            
            # 3. Парсим ответ для извлечения действия
            action = self._parse_action(response)
            result["action"] = action.to_dict()
            
            # 4. Выполняем действие
            if self.dry_run:
                logger.info(f"[DRY-RUN] Действие: {action.action.action_type.value}")
                logger.info(f"  Причина: {action.action.reason}")
                result["executed"] = False
                result["dry_run"] = True
            else:
                logger.info(f"Выполнение действия: {action.action.action_type.value}")
                # TODO: Интегрировать ActionExecutor
                result["executed"] = True
                result["dry_run"] = False
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Ошибка цикла: {e}")
            result["error"] = str(e)
        
        return result
    
    def _parse_action(self, response: str) -> ActionSchema:
        """Парсит ответ LLM для извлечения действия."""
        import json
        import re
        
        # Пытаемся найти JSON в ответе
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return ActionSchema.model_validate(data)
            except Exception:
                pass
        
        # Fallback - действие ожидания
        return ActionSchema(
            action=WaitAction(seconds=2.0, reason="Не удалось распарсить ответ LLM")
        )
    
    def interactive_loop(self, max_cycles: int = 10):
        """
        Интерактивный цикл работы агента.
        
        Args:
            max_cycles: Максимум циклов работы
        """
        print("\n" + "="*50)
        print("Neuro Mini Agent запущен")
        print(f"Режим: {'DRY-RUN' if self.dry_run else 'БОЕВОЙ'}")
        print("="*50)
        print("Команды:")
        print("  quit/exit - выход")
        print("  [текст] - выполнить задачу")
        print("="*50 + "\n")
        
        for i in range(max_cycles):
            try:
                goal = input(f"\n[{i+1}] Задача: ").strip()
                
                if goal.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not goal:
                    goal = "Опиши что видишь на экране"
                
                result = self.run_cycle(goal)
                
                print(f"\nРезультат:")
                print(f"  Успех: {result['success']}")
                if 'action' in result:
                    print(f"  Действие: {result['action']['action']['action_type']}")
                    print(f"  Причина: {result['action']['action']['reason']}")
                if 'error' in result:
                    print(f"  Ошибка: {result['error']}")
                
            except KeyboardInterrupt:
                print("\n\nПрервано пользователем")
                break
        
        print("\nАгент остановлен")


def main():
    parser = argparse.ArgumentParser(description="Neuro Mini Agent")
    parser.add_argument(
        '--run',
        action='store_true',
        help='Боевой режим (выполнять действия)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Режим просмотра (по умолчанию)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Выполнить один цикл и выйти'
    )
    
    args = parser.parse_args()
    
    dry_run = not args.run
    
    # Проверка доступности Ollama
    ollama = OllamaClient()
    if not ollama.is_available():
        logger.error("Ollama недоступен! Убедитесь, что сервис запущен.")
        sys.exit(1)
    
    # Проверка моделей
    models = ollama.check_required_models()
    if not all(models.values()):
        logger.warning(f"Не все модели доступны: {models}")
        logger.warning("Установите модели: ollama pull qwen2.5vl:7b && ollama pull qwen2.5:7b-instruct")
    
    # Запуск агента
    agent = MiniAgent(dry_run=dry_run)
    
    if args.once:
        result = agent.run_cycle()
        print(f"Результат: {result}")
    else:
        agent.interactive_loop()


if __name__ == "__main__":
    main()
