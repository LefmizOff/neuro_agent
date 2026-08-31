"""
Менеджер памяти с LLM-reranker.

Использует текстовый поиск + qwen2.5:7b-instruct для reranking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .sqlite_storage import SQLiteStorage
from core.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Менеджер памяти с LLM-reranker.
    
    Алгоритм поиска:
    1. Текстовый поиск по ключевым словам (LIKE %query%)
    2. Получение топ-k кандидатов
    3. LLM-reranker выбирает наиболее релевантные
    """
    
    def __init__(
        self,
        storage: SQLiteStorage,
        ollama_client: OllamaClient,
        rerank_top_k: int = 5
    ):
        """
        Инициализация менеджера памяти.
        
        Args:
            storage: SQLite хранилище
            ollama_client: Клиент Ollama для reranking
            rerank_top_k: Сколько кандидатов передавать reranker'у
        """
        self.storage = storage
        self.client = ollama_client
        self.rerank_top_k = rerank_top_k
        
        logger.info(f"MemoryManager инициализирован (rerank_top_k={rerank_top_k})")
    
    # === Поиск с reranking ===
    
    def search_memories(
        self,
        query: str,
        memory_type: str = "all",
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Ищет воспоминания с LLM-reranking.
        
        Args:
            query: Поисковый запрос
            memory_type: Тип памяти ("episodes", "facts", "skills", "all")
            limit: Сколько результатов вернуть
            
        Returns:
            Список релевантных воспоминаний
        """
        candidates = []
        
        # Собираем кандидатов из разных источников
        if memory_type in ["episodes", "all"]:
            episodes = self.storage.search_episodes(query, limit=self.rerank_top_k)
            for ep in episodes:
                candidates.append({
                    "type": "episode",
                    "content": f"Goal: {ep.get('goal', '')}; Result: {ep.get('result', '')}",
                    "data": ep
                })
        
        if memory_type in ["facts", "all"]:
            facts = self.storage.search_facts(query, limit=self.rerank_top_k)
            for fact in facts:
                candidates.append({
                    "type": "fact",
                    "content": f"{fact.get('key', '')}: {fact.get('value', '')}",
                    "data": fact
                })
        
        if not candidates:
            return []
        
        # Если кандидатов мало или не нужен reranking
        if len(candidates) <= limit:
            return [c["data"] for c in candidates]
        
        # LLM-reranking
        reranked = self._rerank_candidates(query, candidates, limit)
        return reranked
    
    def _rerank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Использует LLM для выбора наиболее релевантных кандидатов.
        
        Args:
            query: Поисковый запрос
            candidates: Список кандидатов
            limit: Сколько лучших вернуть
            
        Returns:
            Список отранжированных кандидатов
        """
        # Формируем промпт для reranking
        candidates_text = "\n\n".join([
            f"[{i}] {c['type']}: {c['content']}"
            for i, c in enumerate(candidates, 1)
        ])
        
        prompt = f"""Ты — система ранжирования воспоминаний.

Поисковый запрос: "{query}"

Кандидаты:
{candidates_text}

Выбери топ-{limit} наиболее релевантных воспоминаний для этого запроса.
Верни только номера через запятую (например: 1, 3, 2)."""

        try:
            response = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Детерминированный выбор
                max_tokens=100
            )
            
            # Парсим ответ - извлекаем номера
            numbers = []
            for char in response:
                if char.isdigit():
                    numbers.append(int(char))
            
            # Возвращаем в порядке релевантности
            result = []
            for num in numbers:
                idx = num - 1
                if 0 <= idx < len(candidates):
                    result.append(candidates[idx]["data"])
                    if len(result) >= limit:
                        break
            
            return result if result else [candidates[0]["data"]]
            
        except Exception as e:
            logger.error(f"Ошибка LLM-reranking: {e}")
            # Fallback: возвращаем первых по порядку
            return [c["data"] for c in candidates[:limit]]
    
    # === Добавление воспоминаний ===
    
    def store_episode(
        self,
        goal: str,
        perception: Dict[str, Any],
        action: Dict[str, Any],
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> int:
        """Сохраняет эпизод."""
        return self.storage.add_episode(goal, perception, action, result, error)
    
    def store_fact(
        self,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> None:
        """Сохраняет факт."""
        self.storage.add_fact(category, key, value, confidence)
    
    def store_skill(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> None:
        """Сохраняет навык."""
        self.storage.add_skill(name, description, steps)
    
    def store_error(
        self,
        error_type: str,
        context: str,
        solution: Optional[str] = None
    ) -> None:
        """Сохраняет ошибку."""
        self.storage.add_error(error_type, context, solution)
    
    # === Получение ===
    
    def get_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получает факты."""
        return self.storage.get_facts(category)
    
    def get_skills(self) -> List[Dict[str, Any]]:
        """Получает навыки."""
        return self.storage.get_skills()
    
    def close(self) -> None:
        """Закрывает хранилище."""
        self.storage.close()
