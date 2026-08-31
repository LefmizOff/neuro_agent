"""
Клиент для взаимодействия с Ollama API
Исправлено: добавлены таймауты, обработка ошибок
"""
import requests
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin


class OllamaClient:
    """Клиент для работы с Ollama API"""
    def __init__(self, host: str = "http://127.0.0.1:11434", timeout: int = 120):
        self.host = host
        self.timeout = timeout
        self.session = requests.Session()
        
    def chat(self, model: str, messages: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> str:
        """
        Отправляет сообщения в модель и возвращает ответ
        
        Args:
            model: Название модели (например, "qwen2.5:7b-instruct")
            messages: Список сообщений в формате [{"role": "user", "content": "..."}, ...]
            options: Дополнительные параметры для модели
            
        Returns:
            Ответ модели в виде строки
        """
        url = urljoin(self.host, "/api/chat")
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        if options:
            payload["options"] = options
            
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if "message" not in result or "content" not in result["message"]:
                raise ValueError("Некорректный формат ответа от Ollama")
                
            return result["message"]["content"]
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama не ответила за {self.timeout} сек. Модель слишком тяжелая или сервер завис.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Не удалось соединиться с Ollama. Проверьте, запущен ли сервис.")
        except Exception as e:
            raise RuntimeError(f"Ошибка при запросе к Ollama: {str(e)}")
        
    def generate(self, model: str, prompt: str, system: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Генерирует текст на основе промпта
        
        Args:
            model: Название модели
            prompt: Входной промпт
            system: Системное сообщение (опционально)
            options: Дополнительные параметры
            
        Returns:
            Сгенерированный текст
        """
        url = urljoin(self.host, "/api/generate")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
            
        if options:
            payload["options"] = options
            
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result["response"]
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama не ответила за {self.timeout} сек.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Не удалось соединиться с Ollama.")
        except Exception as e:
            raise RuntimeError(f"Ошибка при генерации: {str(e)}")
        
    def models(self) -> List[Dict[str, Any]]:
        """Получает список доступных моделей"""
        url = urljoin(self.host, "/api/tags")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result["models"]
        except Exception as e:
            print(f"Ошибка получения списка моделей: {e}")
            return []
        
    def is_model_available(self, model_name: str) -> bool:
        """Проверяет, доступна ли модель"""
        models = self.models()
        available_models = [model["name"].split(":")[0] for model in models]
        return model_name.split(":")[0] in available_models
