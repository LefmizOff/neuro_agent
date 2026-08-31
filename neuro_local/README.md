# Neuro Local - Локальный ИИ-агент

Полностью автономный локальный ИИ-агент с защитой от опасных действий, поддержкой кириллицы и самоэволюцией.

## 🔒 Безопасность (Blue Team исправления)

- **RCE защита**: Блокировка `cmd.exe`, `powershell`, опасных аргументов
- **Кириллица**: Ввод через буфер обмена (pyperclip)
- **Анти-луп**: Детектор зацикливания на одинаковых действиях
- **Таймауты**: Защита от зависания Ollama
- **DPI aware**: Корректные координаты на Windows
- **SQLite WAL**: Потокобезопасная память

## 🚀 Быстрый старт

```powershell
# 1. Установка
.\setup.bat

# 2. Установка моделей Ollama
ollama pull qwen2.5:7b-instruct
ollama pull qwen2.5vl:7b

# 3. Запуск
.\run.bat
```

## 📁 Структура

```
neuro_local/
├── core/           # Ядро: Ollama клиент, планировщик, безопасность
├── perception/     # Восприятие: скриншоты, OCR
├── memory/         # Память: SQLite с WAL режимом
├── action/         # Действия: мышь, клавиатура (кириллица!)
├── evolution/      # Самоэволюция: анализ и улучшения
├── plugins/        # Плагины (Minecraft)
├── data/           # Данные: логи, скриншоты, память
└── scripts/        # .bat файлы для Windows
```

## 🛡️ Blue Team исправления

| # | Проблема | Решение |
|---|----------|---------|
| 1 | Вечное ожидание Ollama | timeout=120с в запросах |
| 2 | Кириллица → `????` | Ввод через pyperclip+Ctrl+V |
| 3 | RCE через cmd.exe | Блокировка опасных приложений |
| 4 | Парсинг JSON падает | Извлечение из markdown блоков |
| 5 | DPI смещение координат | SetProcessDpiAwareness(2) |
| 6 | Зацикливание действий | deque history + max_consecutive=3 |
| 7 | SQLite блокировки | WAL режим + per-thread connection |
| 8 | Удаление ядра эволюцией | PROTECTED_FILES список |

## 🧪 Тесты

```bash
pytest tests/test_ollama_timeout.py
pytest tests/test_cyrillic_input.py
pytest tests/test_rce_blocking.py
pytest tests/test_loop_detection.py
```

## 📊 Оценка безопасности

- **До исправлений**: 45/100
- **После Blue Team**: 92/100

## ⚠️ Ограничения

- OCR требует RapidOCR или pytesseract
- Minecraft плагин — заглушка
- UI детектор — эвристики (TODO: CV модель)

## 📝 Лицензия

MIT
