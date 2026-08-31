"""
Модуль эволюции для Neuro Local агента
"""
from evolution.collect_logs import collect_session_logs, collect_recent_sessions
from evolution.improve import EvolutionAnalyzer

__all__ = ['collect_session_logs', 'collect_recent_sessions', 'EvolutionAnalyzer']
