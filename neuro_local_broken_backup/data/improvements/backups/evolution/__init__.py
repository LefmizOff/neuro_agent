"""
Evolution module - эволюция и улучшение агента.

Содержит:
- Сбор логов сессий
- Анализ через qwen2.5:7b-instruct
- Предложения улучшений
"""

from .collect_logs import LogCollector
from .improve import ImprovementAnalyzer

__all__ = [
    "LogCollector",
    "ImprovementAnalyzer",
]
