#!/usr/bin/env python3
"""
Основной скрипт Neuro Local агента.
С защитой от зацикливания, утечек памяти и некорректных координат.
"""
import argparse
import time
import signal
import sys
import gc
import json
from datetime import datetime
from typing import Dict, Any, Optional, Deque
from collections import deque
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from core.ollama_client import OllamaClient
    from core.config_loader import ConfigLoader
    from core.planner import Planner
    from core.safety_manager import SafetyManager
    from action.action_executor import ActionExecutor
    from perception.screen_capture import ScreenCapture
    from perception.ocr_engine import OCREngine
    from perception.ui_detector import UIDetector
    from memory.memory_manager import MemoryManager
    from speech.tts_engine import TTSEngine
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    sys.exit(1)


class NeuroLocalAgent:
    """Основной класс Neuro Local агента с защитой от зацикливания."""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        self.config = ConfigLoader(config_path)
        
        # Инициализация компонентов
        self.ollama_client = OllamaClient(
            host=self.config.get("ollama.host", "http://127.0.0.1:11434"),
            timeout=self.config.get("ollama.timeout", 120)
        )
        self.safety_manager = SafetyManager(self.emergency_stop)
        self.memory_manager = MemoryManager(self.ollama_client, self.config)
        self.planner = Planner(self.ollama_client, self.config, self.memory_manager)
        self.action_executor = ActionExecutor(
            dry_run=not self.config.get("actions.run_mode", False)
        )
        self.screen_capture = ScreenCapture()
        self.ocr_engine = OCREngine()
        self.ui_detector = UIDetector()
        self.tts_engine = TTSEngine()
        
        # Защита от зацикливания
        self.action_history: Deque[str] = deque(maxlen=10)
        self.consecutive_same_action = 0
        self.max_consecutive = 3
        
        # Лимиты
        self.max_iterations = self.config.get("limits.max_iterations", 100)
        self.current_iteration = 0
        
        # Режим работы
        self.running = False
        self.current_goal: Optional[str] = None
        
        # Обработчики сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("NeuroLocalAgent инициализирован")
        
    def signal_handler(self, signum, frame):
        """Обработчик системных сигналов."""
        logger.warning(f"Получен сигнал {signum}, останавливаю агента...")
        self.stop()
        
    def emergency_stop(self):
        """Аварийная остановка агента."""
        logger.critical("[АВАРИЙНАЯ ОСТАНОВКА] Агент остановлен по сигналу безопасности!")
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def start(self, goal: str = None):
        """Запускает агента с указанной целью."""
        if goal:
            self.current_goal = goal
        elif not self.current_goal:
            self.current_goal = input("Введите цель для агента: ").strip()
            
        if not self.current_goal:
            print("Цель не указана, завершение.")
            return
            
        logger.info(f"Агент запущен с целью: {self.current_goal}")
        print("Для аварийной остановки нажмите Ctrl+Alt+Q")
        
        self.running = True
        self.current_iteration = 0
        
        # Основной цикл агента
        while self.running:
            try:
                self.current_iteration += 1
                
                # Проверка лимита итераций
                if self.current_iteration > self.max_iterations:
                    logger.warning(f"Достигнут лимит итераций ({self.max_iterations})")
                    self.memory_manager.save_fact(
                        "limit_reached",
                        f"Лимит итераций {self.max_iterations} достигнут при цели: {self.current_goal}"
                    )
                    break
                
                self.step()
                
            except KeyboardInterrupt:
                logger.info("Остановлен пользователем")
                break
            except Exception as e:
                logger.exception(f"Ошибка в основном цикле: {e}")
                self.memory_manager.save_error(
                    error_type="agent_loop_error",
                    error_message=str(e),
                    context={"goal": self.current_goal, "iteration": self.current_iteration}
                )
                break
                
        self.stop()
        
    def step(self):
        """Один шаг работы агента с проверкой на зацикливание."""
        # 1. Восприятие окружающей среды
        perception_data = self.perceive_environment()
        
        # 2. Извлечение релевантных воспоминаний
        relevant_memories = self.memory_manager.retrieve_relevant_memories(
            self.current_goal, top_k=5
        )
        
        # 3. Планирование следующего действия
        action = self.planner.plan_next_action(
            goal=self.current_goal,
            current_state=perception_data,
            relevant_memories=relevant_memories
        )
        
        if action is None:
            logger.warning("Не удалось спланировать следующее действие")
            time.sleep(2)
            return
            
        # 4. Проверка на зацикливание
        action_signature = json.dumps(action.model_dump(), sort_keys=True)
        
        if len(self.action_history) > 0 and self.action_history[-1] == action_signature:
            self.consecutive_same_action += 1
            if self.consecutive_same_action >= self.max_consecutive:
                logger.error(
                    f"[LOOP DETECTED] Действие повторяется {self.consecutive_same_action} раз. Прерывание."
                )
                self.memory_manager.save_error(
                    "loop_detected",
                    "Agent stuck in loop",
                    {"action": action_signature, "count": self.consecutive_same_action}
                )
                self.tts_engine.speak("Обнаружено зацикливание. Останавливаюсь.")
                self.running = False
                return
        else:
            self.consecutive_same_action = 0
            
        self.action_history.append(action_signature)
        
        # 5. Проверка безопасности действия
        is_safe, reason = self.safety_manager.validate_and_filter_action(action)
        if not is_safe:
            logger.warning(f"Действие заблокировано: {reason}")
            return
            
        # 6. Выполнение действия
        execution_result = self.action_executor.execute(action)
        
        # 7. Сохранение эпизода в память
        self.memory_manager.save_episode(
            goal=self.current_goal,
            perception=perception_data,
            plan={},
            action=action.model_dump(),
            result=execution_result
        )
        
        # 8. Проверка завершения цели (упрощенная)
        if self._is_goal_completed(action, execution_result):
            logger.info(f"Цель достигнута: {self.current_goal}")
            self.tts_engine.speak("Задача выполнена успешно.")
            self.running = False
            
        # 9. Очистка памяти
        del perception_data
        gc.collect()
        
        # 10. Задержка между итерациями
        time.sleep(self.config.get("actions.default_delay", 0.5))
        
    def perceive_environment(self) -> Dict[str, Any]:
        """Воспринимает текущее состояние окружающей среды."""
        try:
            # Захват скриншота
            screenshot = self.screen_capture.take_screenshot()
            
            # Сохраняем скриншот для отладки
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"./data/screenshots/{timestamp}.png"
            screenshot.save(screenshot_path)
            
            # OCR
            ocr_text = self.ocr_engine.extract_text(screenshot)
            
            # Обнаружение UI-элементов
            ui_elements = self.ui_detector.detect_ui_elements(screenshot)
            
            # Получаем активное окно
            active_window = self._get_active_window()
            
            # Получаем позицию мыши
            import pyautogui
            mouse_pos = pyautogui.position()
            
            # Получаем последние действия из памяти
            recent_episodes = self.memory_manager.storage.get_recent_episodes(limit=5)
            recent_actions = [ep.get("action", {}) for ep in recent_episodes]
            
            perception_data = {
                "timestamp": datetime.now().isoformat(),
                "active_window": active_window,
                "mouse_position": {"x": mouse_pos.x, "y": mouse_pos.y},
                "ocr_text": ocr_text[:1000] if ocr_text else "",  # Ограничиваем размер
                "ui_elements": [elem.model_dump() for elem in ui_elements[:20]],  # Топ-20 элементов
                "recent_actions": recent_actions,
                "screenshot_path": screenshot_path
            }
            
            return perception_data
            
        except Exception as e:
            logger.exception(f"Ошибка восприятия: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        
    def _get_active_window(self) -> str:
        """Получает название активного окна."""
        try:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            return active_window.title if active_window else "unknown"
        except ImportError:
            logger.warning("pygetwindow не установлен")
            return "unknown_window"
        except Exception as e:
            logger.error(f"Ошибка получения активного окна: {e}")
            return "error"
            
    def _is_goal_completed(self, action, result) -> bool:
        """Проверяет, достигнута ли цель (упрощенная реализация)."""
        # В реальной системе здесь была бы более сложная логика
        return False
        
    def stop(self):
        """Останавливает агента."""
        logger.info("Останавливаю агента...")
        self.running = False
        self.cleanup()
        
    def cleanup(self):
        """Очистка ресурсов."""
        self.safety_manager.cleanup()
        gc.collect()
        logger.info("Ресурсы очищены")


def main():
    parser = argparse.ArgumentParser(description="Neuro Local - Локальный ИИ-агент")
    parser.add_argument("--run", action="store_true", help="Режим боевых действий")
    parser.add_argument("--goal", type=str, help="Цель для агента")
    parser.add_argument("--config", type=str, default="./config/config.yaml", help="Путь к конфигу")
    
    args = parser.parse_args()
    
    try:
        agent = NeuroLocalAgent(config_path=args.config)
        agent.start(goal=args.goal)
    except Exception as e:
        logger.exception(f"Ошибка при запуске агента: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
