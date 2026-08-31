"""
Ollama клиент для работы с локальными моделями.

Поддерживает только две модели:
- qwen2.5vl:7b — для зрения (скриншоты, анализ визуала)
- qwen2.5:7b-instruct — для планирования, диалога, памяти
"""

import base64
import io
import logging
from typing import Optional, List, Dict, Any, Union
from PIL import Image
import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VisionModel(str):
    """Модель для анализа изображений."""
    QWEN_VL = "qwen2.5vl:7b"


class LLMModel(str):
    """Модель для текстовых задач."""
    QWEN_INSTRUCT = "qwen2.5:7b-instruct"


class OllamaMessage(BaseModel):
    """Сообщение для Ollama API."""
    role: str
    content: str
    images: Optional[List[str]] = None  # base64 encoded


class OllamaResponse(BaseModel):
    """Ответ от Ollama API."""
    model: str
    created_at: str
    message: OllamaMessage
    done: bool
    
    class Config:
        populate_by_name = True


class OllamaClient:
    """Клиент для локального Ollama API."""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        vision_model: str = VisionModel.QWEN_VL,
        llm_model: str = LLMModel.QWEN_INSTRUCT,
        timeout: int = 120
    ):
        """
        Инициализация клиента.
        
        Args:
            base_url: URL Ollama сервера
            vision_model: Модель для анализа изображений
            llm_model: Модель для текстовых задач
            timeout: Таймаут запросов в секундах
        """
        self.base_url = base_url.rstrip("/")
        self.vision_model = vision_model
        self.llm_model = llm_model
        self.timeout = timeout
        self.session = requests.Session()
        
        logger.info(f"OllamaClient инициализирован: vision={vision_model}, llm={llm_model}")
    
    def _image_to_base64(self, image: Union[Image.Image, str]) -> str:
        """
        Конвертирует изображение в base64 строку.
        
        Args:
            image: PIL Image или путь к файлу
            
        Returns:
            Base64 закодированное изображение
        """
        if isinstance(image, str):
            # Путь к файлу
            img = Image.open(image)
        else:
            img = image
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Сохраняем в буфер
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Кодируем в base64
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Отправляет запрос к LLM.
        
        Args:
            messages: Список сообщений в формате [{"role": "user|assistant|system", "content": "..."}]
            model: Модель (по умолчанию llm_model)
            stream: Стриминг ответа
            temperature: Температура генерации
            max_tokens: Максимум токенов
            
        Returns:
            Текстовый ответ модели
        """
        model = model or self.llm_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.ConnectionError:
            logger.error("Не удалось подключиться к Ollama. Убедитесь, что сервис запущен.")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут запроса к Ollama ({self.timeout}с)")
            raise
        except Exception as e:
            logger.error(f"Ошибка запроса к Ollama: {e}")
            raise
    
    def vision_chat(
        self,
        image: Union[Image.Image, str],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 1024
    ) -> str:
        """
        Отправляет изображение с запросом к VLM.
        
        Args:
            image: PIL Image или путь к файлу
            prompt: Вопрос/запрос к изображению
            system_prompt: Системный промпт
            temperature: Температура генерации
            max_tokens: Максимум токенов
            
        Returns:
            Текстовый ответ модели
        """
        # Кодируем изображение
        image_base64 = self._image_to_base64(image)
        
        # Формируем сообщения
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_base64]
        })
        
        return self.chat(
            messages=messages,
            model=self.vision_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def is_available(self) -> bool:
        """
        Проверяет доступность Ollama сервера.
        
        Returns:
            True если сервер доступен
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """
        Получает список доступных моделей.
        
        Returns:
            Список названий моделей
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return []
    
    def check_required_models(self) -> Dict[str, bool]:
        """
        Проверяет наличие требуемых моделей.
        
        Returns:
            Словарь {model_name: available}
        """
        available_models = self.list_models()
        return {
            self.vision_model: any(self.vision_model in m for m in available_models),
            self.llm_model: any(self.llm_model in m for m in available_models)
        }
