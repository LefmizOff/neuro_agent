# Neuro Local - Локальный автономный ИИ-агент

Полноценный локальный ИИ-агент, работающий исключительно на вашем компьютере без облачных API.

## Требования

- **ОС**: Windows 10/11
- **Python**: 3.11+
- **Ollama**: http://127.0.0.1:11434
- **Модели**: 
  - `qwen2.5vl:7b` — для зрения (скриншоты, анализ визуала)
  - `qwen2.5:7b-instruct` — для планирования, диалога, памяти

## Установка

### 1. Установка Ollama и моделей

```powershell
# Скачайте и установите Ollama с https://ollama.ai

# Pull нужных моделей
ollama pull qwen2.5vl:7b
ollama pull qwen2.5:7b-instruct
```

### 2. Установка зависимостей Python

```powershell
cd neuro_local
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Настройка конфигурации

```powershell
# Скопируйте пример конфигурации
copy config\config.yaml.example config\config.yaml
copy .env.example .env

# Отредактируйте config.yaml под ваши нужды
```

## Запуск

### Минимальный агент (быстрый старт)

```powershell
python mini_agent.py --dry-run
python mini_agent.py --run  # боевой режим
```

### Полный агент

```powershell
python main.py --dry-run
python main.py --run  # боевой режим
```

### Minecraft плагин

```powershell
python -m plugins.minecraft.demo --dry-run
```

### Эволюция и улучшение

```powershell
# Сбор логов за последнюю сессию
python evolution/collect_logs.py

# Анализ и предложения улучшений
python evolution/improve.py

# Применение улучшений (только после проверки!)
python evolution/improve.py --apply
```

## Структура проекта

```
neuro_local/
├── core/               # Ядро: Ollama-клиент, планировщик, шина событий
├── perception/         # Восприятие: скриншоты, OCR, UI-элементы
├── memory/             # Память: SQLite + LLM-reranker
├── speech/             # Речь: TTS (pyttsx3), текстовый ввод
├── action/             # Действия: мышь, клавиатура, приложения
├── skills/             # Навыки: реестр, YAML-навыки
├── plugins/minecraft/  # Minecraft плагин
├── evolution/          # Эволюция: логи, анализ, улучшения
├── api/                # FastAPI сервер (опционально)
├── tests/              # Тесты pytest
├── scripts/            # PowerShell скрипты установки и запуска
├── config/             # Конфигурация YAML
├── persona/            # Персона агента
├── data/               # Данные: логи, память, скриншоты
├── main.py             # Точка входа полного агента
├── mini_agent.py       # Минимальный рабочий агент
├── requirements.txt    # Зависимости
└── README.md           # Этот файл
```

## Безопасность

- **dry-run по умолчанию**: Все действия сначала показываются в логе без выполнения
- **Аварийный стоп**: Ctrl+Alt+Q немедленно останавливает агента
- **Подтверждение опасных действий**: Удаление файлов, URL, системные настройки требуют подтверждения
- **pyautogui.FAILSAFE**: Поднимите курсор в левый верхний угол для экстренной остановки

## Конфигурация

### config.yaml

Основные настройки:
- Модели Ollama
- Горячие клавиши
- Настройки Minecraft
- Параметры безопасности

### persona.yaml

Характер агента:
- Имя
- Стиль речи
- Предпочтения
- Ограничения поведения

## Память

Агент использует гибридную систему памяти:

1. **SQLite** — структурированное хранение:
   - Эпизоды (что видел/сделал)
   - Факты (предпочтения, имена)
   - Навыки (успешные последовательности)
   - Ошибки

2. **Текстовый поиск** — быстрый поиск по ключевым словам (LIKE %query%)

3. **LLM-reranker** — qwen2.5:7b-instruct выбирает наиболее релевантные воспоминания из топ-5 кандидатов

**Никаких векторных эмбеддингов!** Только текст и LLM.

## Формат действий

Все действия агента строго типизированы через Pydantic:

```json
{
  "action_type": "click",
  "target": {"x": 100, "y": 200},
  "button": "left",
  "reason": "Нажать кнопку 'Сохранить'"
}
```

Типы действий: `click`, `double_click`, `right_click`, `move`, `drag`, `type`, `press_key`, `hotkey`, `wait`, `scroll`, `launch_app`, `close_window`.

## Логирование

Все сессии логируются в JSONL формате (`data/logs/`):

```json
{"timestamp": "...", "goal": "...", "perception": {...}, "plan": "...", "action": {...}, "result": "...", "error": null}
```

## Известные ограничения

1. **Только Windows**: pydirectinput и некоторые функции работают только на Windows
2. **Требует Ollama**: Необходим локальный запуск Ollama с указанными моделями
3. **Нет STT по умолчанию**: Голосовой ввод опционален через vosk
4. **OCR может быть медленным**: RapidOCR работает локально, но требует ресурсов
5. **Minecraft только в одиночной игре**: Никаких античит-обходов

## План развития

- [ ] Интеграция Vosk для STT
- [ ] Больше навыков в реестре
- [ ] Улучшенные OpenCV шаблоны для Minecraft
- [ ] Веб-интерфейс через FastAPI
- [ ] Экспорт/импорт воспоминаний
- [ ] Мультиязычность

## Лицензия

MIT License
