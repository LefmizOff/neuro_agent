"""
Менеджер памяти с LLM-переоценкой релевантности
"""
from typing import List, Dict, Any, Optional
from core.ollama_client import OllamaClient
from core.config_loader import ConfigLoader
from memory.sqlite_storage import SQLiteStorage


class MemoryManager:
    """Менеджер памяти с поиском и LLM-reranking"""
    
    def __init__(self, ollama_client: OllamaClient, config: ConfigLoader):
        self.ollama_client = ollama_client
        self.config = config
        self.storage = SQLiteStorage(config.get("memory.db_path", "./data/memory.db"))
        self.text_model = config.get("ollama.text_model", "qwen2.5:7b-instruct")
        
    def save_episode(self, goal: str, perception: Dict[str, Any], plan: Dict[str, Any], 
                     action: Dict[str, Any], result: Dict[str, Any], error: Optional[str] = None):
        """Сохраняет эпизод"""
        self.storage.save_episode(goal, perception, plan, action, result, error)
        
    def save_fact(self, category: str, content: str, importance: float = 0.5):
        """Сохраняет факт"""
        self.storage.save_fact(category, content, importance)
        
    def save_skill(self, name: str, description: str, steps: List[Dict[str, Any]], 
                   success_rate: float = 0.0):
        """Сохраняет навык"""
        self.storage.save_skill(name, description, steps, success_rate)
        
    def save_error(self, error_type: str, error_message: str, context: Dict[str, Any], 
                   solution: Optional[str] = None):
        """Сохраняет ошибку"""
        self.storage.save_error(error_type, error_message, context, solution)
        
    def retrieve_relevant_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Извлекает релевантные воспоминания с LLM-переоценкой"""
        if not query:
            return []
        
        # Грубый поиск по ключевым словам
        raw_results = []
        
        episodes = self.storage.search_episodes(query, limit=10)
        for ep in episodes:
            raw_results.append({
                "type": "episode",
                "content": f"Goal: {ep.get('goal', '')}, Action: {str(ep.get('action', ''))[:100]}",
                "original": ep
            })
        
        facts = self.storage.search_facts(query, limit=10)
        for fact in facts:
            raw_results.append({
                "type": "fact", 
                "content": fact.get('content', ''),
                "original": fact
            })
        
        skills = self.storage.search_skills(query, limit=10)
        for skill in skills:
            raw_results.append({
                "type": "skill",
                "content": f"Skill: {skill.get('name', '')}, {skill.get('description', '')}",
                "original": skill
            })
        
        if not raw_results:
            return []
        
        # LLM-переоценка
        reranked = self._rerank_with_llm(query, raw_results)
        return reranked[:top_k]
        
    def _rerank_with_llm(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Переоченивает релевантность через LLM"""
        if len(candidates) <= 1:
            return candidates
        
        candidates_text = "\n".join([
            f"{i+1}. {c['content']}" for i, c in enumerate(candidates)
        ])
        
        prompt = f"""Запрос: {query}

Кандидаты:
{candidates_text}

Верни номера наиболее релевантных в порядке убывания (JSON массив): [1, 3, 2]"""
        
        try:
            response = self.ollama_client.chat(
                model=self.text_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json, re
            json_match = re.search(r'\[(.*?)\]', response)
            if json_match:
                indices = json.loads(f"[{json_match.group(1)}]")
                ranked = []
                for idx in indices:
                    if 0 < idx <= len(candidates):
                        ranked.append(candidates[idx-1])
                return ranked
        except Exception as e:
            print(f"[Memory] Ошибка rerank: {e}")
        
        return candidates
        
    def get_context_summary(self) -> Dict[str, Any]:
        """Сводка по памяти"""
        return {
            "episodes_count": len(self.storage.get_recent_episodes(limit=1000)),
            "facts_count": len(self.storage.get_all_facts()),
            "skills_count": len(self.storage.get_all_skills()),
            "recent_episodes": self.storage.get_recent_episodes(limit=5)
        }
