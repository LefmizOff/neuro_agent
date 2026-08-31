"""
Сбор логов для анализа эволюции
"""
import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta


def collect_session_logs(logs_dir: str = "./data/logs", hours_back: int = 24) -> List[Dict[str, Any]]:
    """Собирает логи за указанный период"""
    logs = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    if not os.path.exists(logs_dir):
        return logs
    
    for filename in os.listdir(logs_dir):
        if not (filename.endswith('.jsonl') or filename.endswith('.log')):
            continue
            
        filepath = os.path.join(logs_dir, filename)
        
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mod_time < cutoff_time:
                continue
                
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if 'timestamp' in entry:
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time >= cutoff_time:
                                logs.append(entry)
                        else:
                            logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue
    
    logs.sort(key=lambda x: x.get('timestamp', ''))
    return logs


def collect_recent_sessions(logs_dir: str = "./data/logs", days_back: int = 7) -> List[List[Dict[str, Any]]]:
    """Группирует логи по сессиям"""
    all_logs = collect_session_logs(logs_dir, hours_back=days_back*24)
    
    sessions = []
    current_session = []
    
    for entry in all_logs:
        if current_session:
            try:
                prev_time = datetime.fromisoformat(current_session[-1]['timestamp'])
                curr_time = datetime.fromisoformat(entry['timestamp']) if 'timestamp' in entry else datetime.now()
                
                if (curr_time - prev_time).total_seconds() > 1800:  # 30 минут
                    sessions.append(current_session)
                    current_session = []
            except:
                pass
        
        current_session.append(entry)
    
    if current_session:
        sessions.append(current_session)
    
    return sessions
