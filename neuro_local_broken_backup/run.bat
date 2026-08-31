@echo off
chcp 65001 >nul
echo ============================================
echo   Запуск Neuro Local агента
echo ============================================
echo.

REM Активация виртуального окружения
if not exist venv (
    echo [ОШИБКА] Виртуальное окружение не найдено
    echo Запустите setup.bat для установки
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Виртуальное окружение активировано
echo.

:MENU
echo Выберите режим запуска:
echo   1. Запуск в режиме симуляции (dry-run)
echo   2. Запуск в боевом режиме (реальные действия)
echo   3. Запуск мини-агента (симyляция)
echo   4. Запуск мини-агента (боевой режим)
echo   5. Анализ и улучшение
echo   6. Выход
echo.
set /p choice="Ваш выбор (1-6): "

if "%choice%"=="1" goto RUN_SIM
if "%choice%"=="2" goto RUN_REAL
if "%choice%"=="3" goto MINI_SIM
if "%choice%"=="4" goto MINI_REAL
if "%choice%"=="5" goto IMPROVE
if "%choice%"=="6" goto END

echo Неверный выбор
goto MENU

:RUN_SIM
echo.
echo [РЕЖИМ СИМУЛЯЦИИ] Действия не будут выполняться реально
echo Для аварийной остановки: Ctrl+Alt+Q
python main.py
goto MENU

:RUN_REAL
echo.
echo [БОЕВОЙ РЕЖИМ] Действия будут выполняться реально!
echo Для аварийной остановки: Ctrl+Alt+Q
set /p confirm="Подтвердите (да/нет): "
if "%confirm%"=="да" (
    python main.py --run
) else (
    echo Запуск отменен
)
goto MENU

:MINI_SIM
echo.
echo [МИНИ-АГЕНТ] Режим симуляции
python mini_agent.py
goto MENU

:MINI_REAL
echo.
echo [МИНИ-АГЕНТ] Боевой режим
set /p confirm="Подтвердите (да/нет): "
if "%confirm%"=="да" (
    python mini_agent.py --run
) else (
    echo Запуск отменен
)
goto MENU

:IMPROVE
echo.
echo [АНАЛИЗ И УЛУЧШЕНИЕ]
python -m evolution.improve
goto MENU

:END
echo.
echo Завершение работы
exit /b 0
