#!/usr/bin/env python3
"""
Анализ логов и предложения улучшений через LLM.

Использование:
    python evolution/improve.py              # Анализ последних логов
    python evolution/improve.py --apply      # Применить улучшения (требует подтверждения)
"""

import json
import logging
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from core.ollama_client import OllamaClient
from .collect_logs import LogCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты — система анализа и улучшения ИИ-агента Neuro.
Твоя задача — анализировать логи сессий и предлагать конкретные улучшения.

Формат ответа (JSON):
{
    "summary": "Краткая сводка анализа",
    "issues": [
        {
            "type": "error|inefficiency|optimization",
            "description": "Описание проблемы",
            "suggestion": "Предложение по улучшению"
        }
    ],
    "prompt_improvements": ["предложения по улучшению промптов"],
    "skill_suggestions": ["новые навыки которые стоит добавить"],
    "confidence": 0.0-1.0
}

Будь конкретен в предложениях. Избегай общих фраз."""


class ImprovementAnalyzer:
    """Анализатор для предложений улучшений."""
    
    def __init__(self, improvements_dir: str = "data/improvements"):
        self.client = OllamaClient()
        self.collector = LogCollector()
        self.improvements_dir = Path(improvements_dir)
        self.improvements_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_session(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Анализирует сессию и предлагает улучшения.
        
        Args:
            date: Дата сессии (по умолчанию сегодня)
            
        Returns:
            Результат анализа
        """
        # Собираем логи
        entries = self.collector.collect_session(date)
        
        if not entries:
            return {"error": "Нет данных для анализа"}
        
        # Формируем текст для анализа
        log_text = self.collector.export_for_analysis(date)
        
        # Отправляем в LLM
        prompt = f"""Проанализируй эту сессию работы агента Neuro:

{log_text}

Предложи конкретные улучшения для:
1. Промптов и инструкций
2. Навыков (skills)
3. Обработки ошибок
4. Оптимизации действий"""

        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            # Парсим ответ
            analysis = self._parse_analysis(response)
            
            # Сохраняем результат
            self._save_analysis(analysis, date)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return {"error": str(e)}
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Парсит ответ LLM."""
        import re
        
        # Пытаемся найти JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback - структурированный ответ
        return {
            "summary": response[:500],
            "issues": [],
            "prompt_improvements": [],
            "skill_suggestions": [],
            "raw_response": response
        }
    
    def _save_analysis(self, analysis: Dict[str, Any], date: Optional[str]) -> Path:
        """Сохраняет анализ в файл."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"improvement_{date}.json"
        filepath = self.improvements_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Анализ сохранён: {filepath}")
        return filepath
    
    def apply_improvements(self, filepath: Optional[str] = None) -> bool:
        """
        Применяет улучшения из файла анализа.
        
        TODO: Реализовать реальное применение улучшений
        Сейчас только выводит предложения
        """
        if filepath is None:
            # Ищем последний файл анализа
            files = sorted(self.improvements_dir.glob("improvement_*.json"))
            if not files:
                logger.error("Нет файлов анализа для применения")
                return False
            filepath = str(files[-1])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        print("\n=== ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ ===\n")
        print(f"Сводка: {analysis.get('summary', 'Нет сводки')}\n")
        
        issues = analysis.get('issues', [])
        if issues:
            print("Проблемы и предложения:")
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. [{issue.get('type', 'issue')}]")
                print(f"   Проблема: {issue.get('description', 'Нет описания')}")
                print(f"   Решение: {issue.get('suggestion', 'Нет предложения')}")
        
        prompts = analysis.get('prompt_improvements', [])
        if prompts:
            print("\nУлучшения промптов:")
            for p in prompts:
                print(f"  - {p}")
        
        skills = analysis.get('skill_suggestions', [])
        if skills:
            print("\nНовые навыки:")
            for s in skills:
                print(f"  - {s}")
        
        print("\n=== ДЛЯ ПРИМЕНЕНИЯ ТРЕБУЕТСЯ РУЧНАЯ РЕАЛИЗАЦИЯ ===")
        print("TODO: Автоматическое применение улучшений")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Анализ и улучшение агента")
    parser.add_argument("--session", help="Дата сессии для анализа")
    parser.add_argument("--apply", action="store_true", help="Применить улучшения")
    parser.add_argument("--file", help="Файл анализа для применения")
    
    args = parser.parse_args()
    
    analyzer = ImprovementAnalyzer()
    
    if args.apply or args.file:
        success = analyzer.apply_improvements(args.file)
        exit(0 if success else 1)
    else:
        result = analyzer.analyze_session(args.session)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
