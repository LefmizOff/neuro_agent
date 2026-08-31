@echo off
chcp 65001 >nul
title Neuro Local - Запуск

:MENU
cls
echo ============================================
echo   NEURO LOCAL - Меню запуска
echo ============================================
echo.
echo Выберите режим:
echo.
echo   1. Запуск в режиме симуляции (dry-run)
echo   2. Запуск в боевом режиме (--run)
echo   3. Запуск мини-агента (симуляция)
echo   4. Запуск мини-агента (боевой режим)
echo   5. Анализ и улучшение (evolution)
echo   6. Проверка статуса Ollama
echo   7. Выход
echo.
echo ============================================
set /p choice="Ваш выбор (1-7): "

if "%choice%"=="1" goto SIMULATION
if "%choice%"=="2" goto RUNMODE
if "%choice%"=="3" goto MINI_SIM
if "%choice%"=="4" goto MINI_RUN
if "%choice%"=="5" goto EVOLUTION
if "%choice%"=="6" goto STATUS
if "%choice%"=="7" goto END
goto MENU

:SIMULATION
echo.
echo [Запуск] Режим симуляции...
call venv\Scripts\activate.bat
python main.py
pause
goto MENU

:RUNMODE
echo.
echo [Запуск] БОЕВОЙ РЕЖИМ (--run)
echo ВНИМАНИЕ: Агент будет выполнять реальные действия!
echo Для аварийной остановки нажмите Ctrl+Alt+Q
echo.
set /p confirm="Подтвердить запуск (y/n): "
if /i not "%confirm%"=="y" goto MENU
call venv\Scripts\activate.bat
python main.py --run
pause
goto MENU

:MINI_SIM
echo.
echo [Запуск] Мини-агент (симуляция)...
call venv\Scripts\activate.bat
python mini_agent.py
pause
goto MENU

:MINI_RUN
echo.
echo [Запуск] Мини-агент (БОЕВОЙ РЕЖИМ)
set /p confirm="Подтвердить (y/n): "
if /i not "%confirm%"=="y" goto MENU
call venv\Scripts\activate.bat
python mini_agent.py --run
pause
goto MENU

:EVOLUTION
echo.
echo [Запуск] Анализ и улучшение...
call venv\Scripts\activate.bat
python -m evolution.improve
pause
goto MENU

:STATUS
echo.
echo [Статус] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo Ollama НЕ найден! Установите с https://ollama.ai/
) else (
    echo Ollama найден
    echo.
    echo Доступные модели:
    ollama list
)
echo.
pause
goto MENU

:END
echo.
echo До свидания!
exit /b 0
