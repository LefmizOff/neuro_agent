@echo off
chcp 65001 >nul
title Neuro Local - Установка

echo ============================================
echo   NEURO LOCAL - Установка
echo ============================================
echo.

:: Проверяем Python
echo [1/7] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.11+
    pause
    exit /b 1
)
python --version
echo.

:: Проверяем pip
echo [2/7] Проверка pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] pip не найден!
    pause
    exit /b 1
)
echo pip найден
echo.

:: Создаем виртуальное окружение
echo [3/7] Создание виртуального окружения...
if exist venv (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    echo Виртуальное окружение создано
)
echo.

:: Активируем и обновляем pip
echo [4/7] Обновление pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo.

:: Устанавливаем зависимости
echo [5/7] Установка зависимостей...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        pause
        exit /b 1
    )
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] requirements.txt не найден
)
echo.

:: Создаем директории
echo [6/7] Создание директорий...
if not exist data mkdir data
if not exist data\logs mkdir data\logs
if not exist data\memory mkdir data\memory
if not exist data\screenshots mkdir data\screenshots
if not exist data\improvements mkdir data\improvements
if not exist data\improvements\backups mkdir data\improvements\backups
echo Директории созданы
echo.

:: Копируем конфиги
echo [7/7] Копирование конфигурационных файлов...
if exist config\config.yaml.example (
    copy /Y config\config.yaml.example config\config.yaml >nul
    echo config.yaml создан
)
if exist .env.example (
    copy /Y .env.example .env >nul
    echo .env создан
)
echo.

:: Проверяем Ollama
echo ============================================
echo   Проверка Ollama
echo ============================================
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Ollama не найден!
    echo Установите с https://ollama.ai/
    echo Затем выполните:
    echo   ollama pull qwen2.5:7b-instruct
    echo   ollama pull qwen2.5vl:7b
) else (
    echo Ollama найден
    echo.
    echo Рекомендуемые модели для установки:
    echo   ollama pull qwen2.5:7b-instruct
    echo   ollama pull qwen2.5vl:7b
)
echo.

echo ============================================
echo   Установка завершена!
echo ============================================
echo.
echo Для запуска выполните: run.bat
echo.
pause
