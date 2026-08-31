"""
Планировщик действий для Neuro Local агента
С надежным парсингом JSON из ответов модели
"""
import json
import re
from typing import Dict, Any, List, Optional
from core.ollama_client import OllamaClient
from core.actions_schema import Action
from core.config_loader import ConfigLoader
from memory.memory_manager import MemoryManager


class Planner:
    """Планировщик действий с устойчивым парсингом JSON"""
    
    SYSTEM_PROMPT = """
Ты - планировщик действий для локального ИИ-агента. 
Отвечай ТОЛЬКО в формате JSON без markdown и лишних слов.
Доступные действия: mouse_click, mouse_move, keyboard_press, keyboard_type, run_application, sleep.
Если действие определить невозможно, верни null.
"""
    
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
        """Планирует следующее действие"""
        if not goal:
            print("[Planner] Пустая цель")
            return None
        
        context_parts = [
            f"Цель: {goal}",
            f"Окно: {current_state.get('active_window', 'неизвестно')}",
            f"Мышь: {current_state.get('mouse_position', 'неизвестна')}",
            f"OCR: {current_state.get('ocr_text', '')[:500]}",
            f"UI элементы: {len(current_state.get('ui_elements', []))} найдено",
        ]
        
        if relevant_memories:
            context_parts.append(f"Воспоминания: {len(relevant_memories)} найдено")
        
        user_prompt = "\n".join(context_parts) + "\n\nВерни JSON действия:"
        
        try:
            response = self.ollama_client.chat(
                model=self.text_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            action_dict = self._extract_json_from_response(response)
            
            if action_dict and isinstance(action_dict, dict):
                action = Action.model_validate(action_dict)
                return action
            else:
                print(f"[Planner] Не удалось распарсить ответ: {response[:200]}")
                return None
                
        except Exception as e:
            print(f"[Planner] Ошибка планирования: {e}")
            return None
            
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Извлекает JSON из ответа модели, обрабатывая markdown и шум"""
        if not response or not isinstance(response, str):
            return None
        
        # Сначала пробуем найти JSON в markdown блоках
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE)
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
            print(f"[Planner] JSON error: {e}. Fragment: {json_str[:100]}")
            return None
