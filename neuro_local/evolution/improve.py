"""
Анализ и улучшение агента через LLM
С защитой от самоповреждения
"""
import json
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.ollama_client import OllamaClient
from core.config_loader import ConfigLoader


class EvolutionAnalyzer:
    """Анализатор с защитой от повреждения ядра"""
    
    # Защищенные файлы которые нельзя удалять/ломать
    PROTECTED_FILES = [
        "main.py", "mini_agent.py",
        "core/", "action/", "memory/", "perception/",
        "safety_manager.py", "ollama_client.py"
    ]
    
    def __init__(self, ollama_client: OllamaClient, config: ConfigLoader):
        self.ollama_client = ollama_client
        self.config = config
        self.text_model = config.get("ollama.text_model", "qwen2.5:7b-instruct")
        self.improvements_dir = config.get("paths.improvements_dir", "./data/improvements")
        
    def analyze_session(self, session: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализирует сессию"""
        if not session:
            return {"effectiveness_score": 5, "issues_found": [], "improvement_suggestions": []}
        
        summary = self._summarize_session(session)
        
        prompt = f"""Проанализируй сессию ИИ-агента и предложи улучшения.

Сессия: {json.dumps(summary, ensure_ascii=False)[:2000]}

Верни JSON:
{{
  "effectiveness_score": 5,
  "issues_found": ["проблема 1"],
  "improvement_suggestions": [{{"category": "safety", "description": "описание", "priority": "medium"}}]
}}"""
        
        try:
            response = self.ollama_client.chat(
                model=self.text_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._extract_json(response) or {
                "effectiveness_score": 5,
                "issues_found": [],
                "improvement_suggestions": []
            }
        except Exception as e:
            print(f"[Evolution] Ошибка анализа: {e}")
            return {"effectiveness_score": 5, "issues_found": [], "improvement_suggestions": []}
    
    def generate_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерирует предложения улучшений"""
        improvements = []
        suggestions = analysis.get("improvement_suggestions", [])
        
        for i, sugg in enumerate(suggestions):
            imp = {
                "id": f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                "timestamp": datetime.now().isoformat(),
                "category": sugg.get("category", "other"),
                "description": sugg.get("description", ""),
                "priority": sugg.get("priority", "medium"),
                "status": "proposed"
            }
            improvements.append(imp)
        
        return improvements
    
    def save_improvements(self, improvements: List[Dict[str, Any]]):
        """Сохраняет улучшения"""
        os.makedirs(self.improvements_dir, exist_ok=True)
        
        # Сохраняем все в один файл
        all_file = os.path.join(self.improvements_dir, "all_improvements.json")
        with open(all_file, 'w', encoding='utf-8') as f:
            json.dump(improvements, f, ensure_ascii=False, indent=2)
        
        # И отдельно каждое
        for imp in improvements:
            filepath = os.path.join(self.improvements_dir, f"{imp['id']}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(imp, f, ensure_ascii=False, indent=2)
    
    def apply_improvements(self, improvements: List[Dict[str, Any]], auto_apply: bool = False):
        """Применяет улучшения с проверкой безопасности"""
        if not auto_apply:
            print("[Evolution] Автоприменение отключено")
            return
        
        applied = 0
        for imp in improvements:
            target = imp.get("target_file", "")
            
            # Проверка на защищенные файлы
            is_protected = any(
                target == p or (isinstance(p, str) and target.startswith(p))
                for p in self.PROTECTED_FILES
            )
            
            if is_protected and ("delete" in imp.get("type", "").lower() or 
                                 "remove" in imp.get("description", "").lower()):
                print(f"[BLOCKED] Защита: {target}")
                imp["status"] = "rejected_security"
                continue
            
            if imp.get("status") == "approved":
                print(f"[APPLY] {imp['description']}")
                imp["status"] = "implemented"
                imp["applied_at"] = datetime.now().isoformat()
                applied += 1
        
        print(f"Применено {applied} улучшений")
    
    def _summarize_session(self, session: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Краткое резюме сессии"""
        if not session:
            return {}
        
        action_types = {}
        errors = []
        
        for entry in session:
            if 'action' in entry and isinstance(entry['action'], dict):
                atype = entry['action'].get('type', 'unknown')
                action_types[atype] = action_types.get(atype, 0) + 1
            
            if entry.get('error'):
                errors.append(entry['error'])
        
        return {
            "entries": len(session),
            "actions": action_types,
            "errors_count": len(errors),
            "error_samples": errors[:3]
        }
    
    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Извлекает JSON из ответа"""
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None


def main():
    """Точка входа для анализа"""
    config = ConfigLoader()
    ollama = OllamaClient(timeout=config.get("ollama.timeout", 120))
    analyzer = EvolutionAnalyzer(ollama, config)
    
    from evolution.collect_logs import collect_recent_sessions
    sessions = collect_recent_sessions(days_back=7)
    
    print(f"Анализ {len(sessions)} сессий...")
    
    all_improvements = []
    for session in sessions[:5]:  # Максимум 5 сессий
        analysis = analyzer.analyze_session(session)
        improvements = analyzer.generate_improvements(analysis)
        all_improvements.extend(improvements)
    
    analyzer.save_improvements(all_improvements)
    print(f"Сохранено {len(all_improvements)} предложений")


if __name__ == "__main__":
    main()
