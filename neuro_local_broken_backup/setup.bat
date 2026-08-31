@echo off
chcp 65001 >nul
echo ============================================
echo   Установка Neuro Local агента
echo ============================================
echo.

REM Проверка Python
echo [1/7] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.11+
    pause
    exit /b 1
)
python --version
echo.

REM Проверка pip
echo [2/7] Проверка pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] pip не найден
    pause
    exit /b 1
)
echo pip найден
echo.

REM Создание виртуального окружения
echo [3/7] Создание виртуального окружения...
if exist venv (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    echo Виртуальное окружение создано
)
echo.

REM Активация и установка зависимостей
echo [4/7] Установка зависимостей...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)
echo.

REM Создание директорий
echo [5/7] Создание директорий данных...
if not exist data mkdir data
if not exist data\logs mkdir data\logs
if not exist data\screenshots mkdir data\screenshots
if not exist data\improvements mkdir data\improvements
if not exist data\improvements\backups mkdir data\improvements\backups
echo Директории созданы
echo.

REM Копирование конфигов
echo [6/7] Копирование конфигурационных файлов...
if not exist config\config.yaml copy config\config.yaml.example config\config.yaml
if not exist .env copy .env.example .env
echo Конфигурационные файлы готовы
echo.

REM Проверка Ollama
echo [7/7] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Ollama не найден
    echo Скачайте с https://ollama.ai/
    echo Затем выполните:
    echo   ollama pull qwen2.5:7b-instruct
    echo   ollama pull qwen2.5vl:7b
) else (
    echo Ollama найден
    echo Проверка моделей...
    ollama list | findstr "qwen2.5" >nul 2>&1
    if errorlevel 1 (
        echo [ПРЕДУПРЕЖДЕНИЕ] Модели не найдены. Выполните:
        echo   ollama pull qwen2.5:7b-instruct
        echo   ollama pull qwen2.5vl:7b
    ) else (
        echo Модели найдены
    )
)
echo.

echo ============================================
echo   Установка завершена!
echo   Для запуска выполните: run.bat
echo ============================================
pause
