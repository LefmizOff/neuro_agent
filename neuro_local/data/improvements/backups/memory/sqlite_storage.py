"""
Менеджер памяти с потокобезопасным доступом к SQLite
"""
import sqlite3
import threading
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class SQLiteStorage:
    """Потокобезопасное хранилище на SQLite с WAL режимом"""
    
    _lock = threading.Lock()
    _connections: Dict[int, sqlite3.Connection] = {}
    
    def __init__(self, db_path: str = "./data/memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
        
    def get_connection(self) -> sqlite3.Connection:
        """Получает потокобезопасное соединение"""
        thread_id = threading.get_ident()
        
        if thread_id not in self._connections or self._connections[thread_id] is None:
            with self._lock:
                conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                self._connections[thread_id] = conn
                
        return self._connections[thread_id]
        
    def init_db(self):
        """Инициализирует базу данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    goal TEXT,
                    perception TEXT,
                    plan TEXT,
                    action TEXT,
                    result TEXT,
                    error TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 0.5
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    steps TEXT,
                    success_rate REAL DEFAULT 0.0,
                    last_used TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    context TEXT,
                    solution TEXT
                )
            """)
            
            conn.commit()
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            raise
            
    def save_episode(self, goal: str, perception: Dict[str, Any], plan: Dict[str, Any], 
                     action: Dict[str, Any], result: Dict[str, Any], error: Optional[str] = None):
        """Сохраняет эпизод"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        with self._lock:
            try:
                cursor.execute("""
                    INSERT INTO episodes (timestamp, goal, perception, plan, action, result, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    goal,
                    json.dumps(perception, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False) if plan else None,
                    json.dumps(action, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                    error
                ))
                conn.commit()
            except Exception as e:
                print(f"Ошибка сохранения эпизода: {e}")
                
    def save_fact(self, category: str, content: str, importance: float = 0.5):
        """Сохраняет факт"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        with self._lock:
            cursor.execute("""
                INSERT INTO facts (timestamp, category, content, importance)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                category,
                content,
                importance
            ))
            conn.commit()
            
    def save_skill(self, name: str, description: str, steps: List[Dict[str, Any]], 
                   success_rate: float = 0.0):
        """Сохраняет навык"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        with self._lock:
            cursor.execute("""
                INSERT OR REPLACE INTO skills (timestamp, name, description, steps, success_rate, last_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                name,
                description,
                json.dumps(steps, ensure_ascii=False),
                success_rate,
                datetime.now().isoformat()
            ))
            conn.commit()
            
    def save_error(self, error_type: str, error_message: str, context: Dict[str, Any], 
                   solution: Optional[str] = None):
        """Сохраняет ошибку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        with self._lock:
            cursor.execute("""
                INSERT INTO errors (timestamp, error_type, error_message, context, solution)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                error_type,
                error_message,
                json.dumps(context, ensure_ascii=False),
                solution
            ))
            conn.commit()
            
    def search_episodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск эпизодов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM episodes 
            WHERE goal LIKE ? OR perception LIKE ? OR action LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            episode = dict(zip(columns, row))
            for field in ['perception', 'plan', 'action', 'result']:
                if episode.get(field):
                    try:
                        episode[field] = json.loads(episode[field])
                    except:
                        pass
            results.append(episode)
        
        return results
        
    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск фактов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM facts 
            WHERE content LIKE ? OR category LIKE ?
            ORDER BY importance DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
        
    def search_skills(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск навыков"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM skills 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY success_rate DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            skill = dict(zip(columns, row))
            if skill.get('steps'):
                try:
                    skill['steps'] = json.loads(skill['steps'])
                except:
                    pass
            results.append(skill)
        
        return results
        
    def search_errors(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск ошибок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM errors 
            WHERE error_type LIKE ? OR error_message LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            error = dict(zip(columns, row))
            if error.get('context'):
                try:
                    error['context'] = json.loads(error['context'])
                except:
                    pass
            results.append(error)
        
        return results
        
    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает недавние эпизоды"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM episodes 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            episode = dict(zip(columns, row))
            for field in ['perception', 'plan', 'action', 'result']:
                if episode.get(field):
                    try:
                        episode[field] = json.loads(episode[field])
                    except:
                        pass
            results.append(episode)
        
        return results
        
    def get_all_facts(self) -> List[Dict[str, Any]]:
        """Все факты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facts ORDER BY importance DESC")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
        
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Все навыки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills ORDER BY success_rate DESC")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            skill = dict(zip(columns, row))
            if skill.get('steps'):
                try:
                    skill['steps'] = json.loads(skill['steps'])
                except:
                    pass
            results.append(skill)
        return results
