#!/usr/bin/env python3
"""
Минимальный рабочий агент: скриншот → qwen2.5vl:7b → JSON-действие → dry-run/--run
С исправлениями: таймауты, кириллица, безопасность, парсинг JSON
"""
import argparse
import json
import base64
from io import BytesIO
from PIL import Image
import pyautogui

from core.ollama_client import OllamaClient
from core.config_loader import ConfigLoader
from core.actions_schema import Action
from perception.screen_capture import ScreenCapture
from perception.ocr_engine import OCREngine
from action.action_executor import ActionExecutor


def extract_json_from_response(response: str):
    """Извлекает JSON из ответа модели"""
    if not response:
        return None
    
    import re
    # Ищем в markdown блоках
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        start = response.find('{')
        end = response.rfind('}')
        if start == -1 or end == -1:
            return None
        json_str = response[start:end+1]
    
    try:
        data = json.loads(json_str)
        return data if isinstance(data, dict) else None
    except:
        return None


def main():
    parser = argparse.ArgumentParser(description="Mini Agent Neuro Local")
    parser.add_argument("--run", action="store_true", help="Боевой режим (по умолчанию dry-run)")
    args = parser.parse_args()

    print("=" * 50)
    print("  NEURO LOCAL - Мини Агент")
    print("=" * 50)
    print(f"Режим: {'БОЕВОЙ' if args.run else 'СИМУЛЯЦИЯ (dry-run)'}")
    print()

    # Инициализация
    config = ConfigLoader()
    ollama = OllamaClient(timeout=config.get("ollama.timeout", 120))
    screen = ScreenCapture()
    ocr = OCREngine()
    executor = ActionExecutor(config)
    executor.set_dry_run(not args.run)

    pyautogui.FAILSAFE = True

    # 1. Скриншот
    print("[1/4] Делаю скриншот...")
    screenshot = screen.take_screenshot()
    screenshot.save("./data/screenshots/latest.png")
    print(f"  Размер: {screenshot.size}")

    # 2. OCR
    print("[2/4] Распознаю текст (OCR)...")
    ocr_text = ocr.extract_text(screenshot)
    print(f"  Найдено символов: {len(ocr_text)}")

    # 3. Анализ через VLM
    print("[3/4] Анализирую экран (qwen2.5vl:7b)...")
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    vision_prompt = f"Опиши экран. Что видишь? Есть ли кнопки, поля, окна? OCR текст: {ocr_text[:500]}"
    
    try:
        vision_response = ollama.chat(
            model="qwen2.5vl:7b",
            messages=[
                {"role": "user", "content": vision_prompt},
                {"role": "user", "images": [img_b64]}
            ]
        )
        print(f"  Анализ: {vision_response[:200]}...")
    except Exception as e:
        print(f"  Ошибка VLM: {e}")
        vision_response = "Не удалось проанализировать"

    # 4. Планирование действия
    print("[4/4] Планирую действие (qwen2.5:7b-instruct)...")
    mouse_pos = pyautogui.position()
    
    plan_prompt = f"""Цель: тестирование агента
Экран: {vision_response[:300]}
Мышь: {mouse_pos}
OCR: {ocr_text[:200]}

Верни JSON действия (type, position для мыши, text/key для клавиатуры):"""

    try:
        action_response = ollama.chat(
            model="qwen2.5:7b-instruct",
            messages=[{"role": "user", "content": plan_prompt}]
        )
        
        action_dict = extract_json_from_response(action_response)
        
        if action_dict:
            print(f"  Действие: {action_dict}")
            
            try:
                action = Action.model_validate(action_dict)
                
                if args.run:
                    print("\n[ВЫПОЛНЕНИЕ] Реальное действие...")
                    result = executor.execute_action(action)
                    print(f"  Результат: {result}")
                else:
                    print("\n[DRY-RUN] Действие не выполнено (симуляция)")
                    
            except Exception as e:
                print(f"  Ошибка валидации: {e}")
        else:
            print(f"  Не удалось распарсить JSON из: {action_response[:200]}")
            
    except Exception as e:
        print(f"  Ошибка планирования: {e}")

    print("\n" + "=" * 50)
    print("Завершено")
    print("=" * 50)


if __name__ == "__main__":
    main()
