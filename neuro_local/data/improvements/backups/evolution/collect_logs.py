#!/usr/bin/env python3
"""
Сбор логов сессий для анализа.

Использование:
    python evolution/collect_logs.py --session 2024-01-15
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogCollector:
    """Сборщик логов сессий."""
    
    def __init__(self, logs_dir: str = "data/logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_session(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Собирает логи за указанную дату.
        
        Args:
            date: Дата в формате YYYY-MM-DD (по умолчанию сегодня)
            
        Returns:
            Список записей логов
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.logs_dir / f"session_{date}.jsonl"
        
        if not log_file.exists():
            logger.warning(f"Лог файл не найден: {log_file}")
            return []
        
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Собрано {len(entries)} записей за {date}")
        return entries
    
    def get_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Создаёт сводку по логам.
        
        Args:
            entries: Список записей логов
            
        Returns:
            Словарь сводки
        """
        if not entries:
            return {"total": 0}
        
        actions = {}
        errors = []
        
        for entry in entries:
            action_type = entry.get("action", {}).get("action", {}).get("action_type", "unknown")
            actions[action_type] = actions.get(action_type, 0) + 1
            
            if entry.get("error"):
                errors.append(entry["error"])
        
        return {
            "total": len(entries),
            "actions": actions,
            "errors_count": len(errors),
            "success_rate": (len(entries) - len(errors)) / len(entries) if entries else 0
        }
    
    def export_for_analysis(self, date: Optional[str] = None) -> str:
        """
        Экспортирует логи в формат для анализа LLM.
        
        Returns:
            Текст для отправки в LLM
        """
        entries = self.collect_session(date)
        summary = self.get_summary(entries)
        
        lines = [
            "=== АНАЛИЗ СЕССИИ ===",
            f"Дата: {date or 'сегодня'}",
            f"Всего действий: {summary['total']}",
            f"Успешность: {summary.get('success_rate', 0):.1%}",
            "",
            "Распределение действий:"
        ]
        
        for action, count in summary.get("actions", {}).items():
            lines.append(f"  {action}: {count}")
        
        if summary.get("errors_count", 0) > 0:
            lines.append("")
            lines.append("Ошибки:")
            for i, err in enumerate(entries[:10]):  # Первые 10 ошибок
                if err.get("error"):
                    lines.append(f"  {i+1}. {err['error']}")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Сбор логов сессии")
    parser.add_argument("--session", help="Дата сессии (YYYY-MM-DD)")
    parser.add_argument("--export", action="store_true", help="Экспортировать для анализа")
    
    args = parser.parse_args()
    
    collector = LogCollector()
    
    if args.export:
        text = collector.export_for_analysis(args.session)
        print(text)
    else:
        entries = collector.collect_session(args.session)
        summary = collector.get_summary(entries)
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
