#!/usr/bin/env python3
"""
Основной скрипт Neuro Local агента
С анти-луп детектом, безопасностью и управлением памятью
"""
import argparse
import signal
import sys
import time
import gc
import json
from datetime import datetime
from typing import Dict, Any, Optional, Deque
from collections import deque

from core.ollama_client import OllamaClient
from core.config_loader import ConfigLoader
from core.planner import Planner
from core.safety_manager import SafetyManager
from action.action_executor import ActionExecutor
from perception.screen_capture import ScreenCapture
from perception.ocr_engine import OCREngine
from memory.memory_manager import MemoryManager


class NeuroLocalAgent:
    """Основной агент с защитой от зацикливания"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        self.config = ConfigLoader(config_path)
        
        self.ollama = OllamaClient(
            host=self.config.get("ollama.host", "http://127.0.0.1:11434"),
            timeout=self.config.get("ollama.timeout", 120)
        )
        self.safety = SafetyManager(self.emergency_stop)
        self.memory = MemoryManager(self.ollama, self.config)
        self.planner = Planner(self.ollama, self.config, self.memory)
        self.executor = ActionExecutor(self.config)
        self.screen = ScreenCapture()
        self.ocr = OCREngine()
        
        self.running = False
        self.dry_run = self.config.get("actions.dry_run", True)
        self.current_goal: Optional[str] = None
        
        # Анти-луп детектор
        self.action_history: Deque[str] = deque(maxlen=10)
        self.consecutive_same = 0
        self.max_consecutive = 3
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print(f"\nСигнал {signum}, остановка...")
        self.stop()
        
    def emergency_stop(self):
        print("\n[АВАРИЙНАЯ ОСТАНОВКА]")
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def start(self, goal: Optional[str] = None):
        """Запуск агента"""
        self.current_goal = goal or input("Цель: ").strip()
        
        if not self.current_goal:
            print("Цель не указана")
            return
            
        print(f"Запуск с целью: {self.current_goal}")
        print(f"Режим: {'БОЕВОЙ' if not self.dry_run else 'СИМУЛЯЦИЯ'}")
        print("Аварийная остановка: Ctrl+Alt+Q")
        
        self.running = True
        self.executor.set_dry_run(self.dry_run)
        
        iteration = 0
        max_iterations = 100  # Лимит итераций
        
        while self.running and iteration < max_iterations:
            try:
                self.step()
                iteration += 1
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                self.memory.save_error("agent_error", str(e), {"iteration": iteration})
                break
        
        self.stop()
        
    def step(self):
        """Один шаг работы"""
        # Восприятие
        perception = self.perceive()
        
        # Поиск воспоминаний
        memories = self.memory.retrieve_relevant_memories(self.current_goal, top_k=3)
        
        # Планирование
        action = self.planner.plan_next_action(self.current_goal, perception, memories)
        
        if not action:
            print("Нет действия для выполнения")
            time.sleep(2)
            return
        
        # Проверка на зацикливание
        action_sig = str(action.model_dump())
        if self.action_history and self.action_history[-1] == action_sig:
            self.consecutive_same += 1
            if self.consecutive_same >= self.max_consecutive:
                print(f"[LOOP] Действие повторяется {self.consecutive_same} раз. Стоп.")
                self.memory.save_error("loop_detected", "Зацикливание", {"action": action_sig})
                self.running = False
                return
        else:
            self.consecutive_same = 0
        
        self.action_history.append(action_sig)
        
        # Безопасность
        is_safe, reason = self.safety.validate_and_filter_action(action)
        if not is_safe:
            print(f"[SAFETY] Заблокировано: {reason}")
            return
        
        # Выполнение
        result = self.executor.execute_action(action)
        
        # Сохранение эпизода
        self.memory.save_episode(
            goal=self.current_goal,
            perception=perception,
            plan={},
            action=action.model_dump(),
            result=result
        )
        
        # Логирование
        self.log_interaction(perception, action, result)
        
        # Очистка памяти
        del perception
        gc.collect()
        
        time.sleep(self.config.get("actions.default_delay", 0.5))
        
    def perceive(self) -> Dict[str, Any]:
        """Восприятие среды"""
        screenshot = self.screen.take_screenshot()
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot.save(f"./data/screenshots/{ts}.png")
        
        ocr_text = self.ocr.extract_text(screenshot)
        
        try:
            import pyautogui
            mouse_pos = pyautogui.position()
        except:
            mouse_pos = (0, 0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "mouse_position": {"x": mouse_pos[0], "y": mouse_pos[1]},
            "ocr_text": ocr_text[:1000] if ocr_text else "",
            "screenshot_path": f"./data/screenshots/{ts}.png"
        }
        
    def log_interaction(self, perception: Dict, action, result: Dict):
        """Логирование в JSONL"""
        logs_dir = self.config.get("paths.logs_dir", "./data/logs")
        import os
        os.makedirs(logs_dir, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "goal": self.current_goal,
            "perception": perception,
            "action": action.model_dump() if hasattr(action, 'model_dump') else str(action),
            "result": result
        }
        
        log_file = f"{logs_dir}/{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
    def stop(self):
        """Остановка"""
        print("Остановка...")
        self.running = False
        self.cleanup()
        
    def cleanup(self):
        """Очистка"""
        self.safety.cleanup()
        print("Ресурсы очищены")


def main():
    parser = argparse.ArgumentParser(description="Neuro Local Agent")
    parser.add_argument("--run", action="store_true", help="Боевой режим")
    parser.add_argument("--goal", type=str, help="Цель")
    parser.add_argument("--config", type=str, default="./config/config.yaml")
    
    args = parser.parse_args()
    
    agent = NeuroLocalAgent(config_path=args.config)
    agent.dry_run = not args.run
    
    try:
        agent.start(goal=args.goal)
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
