"""
Модуль планирования для Neuro Local агента
Исправлено: надежный парсинг JSON из ответов модели
"""
from typing import Dict, Any, List, Optional
import json
import re
from core.ollama_client import OllamaClient
from core.actions_schema import Action
from core.config_loader import ConfigLoader
from memory.memory_manager import MemoryManager


class Planner:
    """Планировщик действий агента"""
    def __init__(self, ollama_client: OllamaClient, config: ConfigLoader, memory_manager: MemoryManager):
        self.ollama_client = ollama_client
        self.config = config
        self.memory_manager = memory_manager
        self.text_model = config.get("ollama.text_model", "qwen2.5:7b-instruct")
        
    def plan_next_action(
        self,
        goal: str,
        current_state: Dict[str, Any],
        relevant_memories: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Action]:
        """
        Планирует следующее действие на основе цели и текущего состояния
        """
        if not goal:
            print("[ПЛАНИРОВЩИК] Цель не задана")
            return None
            
        system_prompt = """
Ты - планировщик действий для локального ИИ-агента. Твоя задача - принимать решения о следующем действии
на основе цели, текущего состояния системы и релевантных воспоминаний.

Ты можешь выполнить следующие действия:
- mouse_click: Кликнуть в определённую точку экрана
- mouse_move: Переместить курсор в определённую точку
- keyboard_press: Нажать клавишу
- keyboard_type: Ввести текст
- run_application: Запустить приложение
- sleep: Пауза

ВАЖНО: Всегда отвечай в формате JSON с соответствующей схемой действия.
Если невозможно определить следующее действие, верни null.
Отвечай ТОЛЬКО JSON, без markdown и лишнего текста.
"""

        context_parts = [
            f"Цель: {goal}",
            f"Активное окно: {current_state.get('active_window', 'неизвестно')}",
            f"Позиция мыши: {current_state.get('mouse_position', 'неизвестна')}",
            f"Результаты OCR: {str(current_state.get('ocr_text', ''))[:500]}",
            f"Обнаруженные UI-элементы: {len(current_state.get('ui_elements', []))} шт.",
            f"Последние действия: {len(current_state.get('recent_actions', []))} шт.",
        ]
        
        if relevant_memories:
            context_parts.append(f"Релевантные воспоминания: {len(relevant_memories)} найдено")
        
        context = "\n".join(context_parts)
        
        user_prompt = f"""
Текущее состояние системы:
{context}

Выбери одно действие, которое логично выполнить в данной ситуации.
Ответь ТОЛЬКО в формате JSON.
"""
        
        try:
            response = self.ollama_client.chat(
                model=self.text_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Извлекаем JSON из ответа
            action_json = self._extract_json_from_response(response)
            
            if action_json:
                try:
                    action = Action.model_validate(action_json)
                    return action
                except Exception as e:
                    print(f"Ошибка валидации действия: {e}")
                    return None
            else:
                print(f"Не удалось извлечь JSON из ответа планировщика")
                return None
                
        except Exception as e:
            print(f"Ошибка при планировании действия: {e}")
            return None
            
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Извлекает JSON из текстового ответа (поддержка markdown)"""
        if not response or not isinstance(response, str):
            return None
            
        # Сначала ищем JSON в markdown блоках ```json ... ```
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Ищем первую и последнюю фигурные скобки
            start_idx = response.find('{')
            if start_idx == -1:
                return None
                
            end_idx = response.rfind('}')
            if end_idx == -1 or end_idx <= start_idx:
                return None
                
            json_str = response[start_idx:end_idx+1]
        
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return None
            return data
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}. Фрагмент: {json_str[:100]}")
            return None
