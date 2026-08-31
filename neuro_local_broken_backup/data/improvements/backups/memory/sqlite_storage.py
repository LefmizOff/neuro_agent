"""
SQLite хранилище для памяти агента.

Структура таблиц:
- episodes: эпизоды (что видел/сделал)
- facts: факты (предпочтения, имена)
- skills: навыки (успешные последовательности)
- errors: ошибки и их решения
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """SQLite хранилище для памяти."""
    
    def __init__(self, db_path: str = "data/memory/neuro_memory.db"):
        """
        Инициализация хранилища.
        
        Args:
            db_path: Путь к базе данных
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()
        
        logger.info(f"SQLiteStorage инициализирован: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с БД."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self) -> None:
        """Инициализирует структуру БД."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица эпизодов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                goal TEXT,
                perception TEXT,
                action TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица фактов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        """)
        
        # Таблица навыков
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                steps TEXT,
                success_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица ошибок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                context TEXT,
                solution TEXT,
                occurred_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индексы для поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_goal ON episodes(goal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key)")
        
        conn.commit()
        logger.debug("База данных инициализирована")
    
    # === Эпизоды ===
    
    def add_episode(
        self,
        goal: str,
        perception: Dict[str, Any],
        action: Dict[str, Any],
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> int:
        """Добавляет эпизод."""
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO episodes (timestamp, goal, perception, action, result, error)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            goal,
            json.dumps(perception),
            json.dumps(action),
            result,
            error
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def search_episodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Ищет эпизоды по тексту."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM episodes
            WHERE goal LIKE ? OR result LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # === Факты ===
    
    def add_fact(
        self,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> None:
        """Добавляет или обновляет факт."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO facts (category, key, value, confidence)
            VALUES (?, ?, ?, ?)
        """, (category, key, value, confidence))
        
        conn.commit()
    
    def get_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получает факты, опционально по категории."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM facts WHERE category = ?", (category,))
        else:
            cursor.execute("SELECT * FROM facts")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Ищет факты по ключу или значению."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM facts
            WHERE key LIKE ? OR value LIKE ?
            ORDER BY confidence DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # === Навыки ===
    
    def add_skill(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> None:
        """Добавляет навык."""
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO skills (name, description, steps, last_used)
            VALUES (?, ?, ?, ?)
        """, (name, description, json.dumps(steps), datetime.now().isoformat()))
        
        conn.commit()
    
    def get_skills(self) -> List[Dict[str, Any]]:
        """Получает все навыки."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills ORDER BY success_count DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def increment_skill_success(self, name: str) -> None:
        """Увеличивает счётчик успешных использований навыка."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE skills
            SET success_count = success_count + 1, last_used = ?
            WHERE name = ?
        """, (datetime.now().isoformat(), name))
        
        conn.commit()
    
    # === Ошибки ===
    
    def add_error(
        self,
        error_type: str,
        context: str,
        solution: Optional[str] = None
    ) -> None:
        """Добавляет ошибку."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO errors (error_type, context, solution)
            VALUES (?, ?, ?)
        """, (error_type, context, solution))
        
        conn.commit()
    
    def search_errors(self, error_type: str) -> List[Dict[str, Any]]:
        """Ищет ошибки по типу."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM errors
            WHERE error_type LIKE ?
            ORDER BY occurred_at DESC
        """, (f"%{error_type}%",))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self._conn:
            self._conn.close()
            self._conn = None
