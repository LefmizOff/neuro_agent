# Neuro Local - Скрипт установки
# Запускать в PowerShell от имени обычного пользователя

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Neuro Local - Установка" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Проверка Python
Write-Host "`n[1/5] Проверка Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Найдено: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ОШИБКА: Python не найден!" -ForegroundColor Red
    Write-Host "  Установите Python 3.11+ с https://python.org" -ForegroundColor Red
    exit 1
}

# Создание виртуального окружения
Write-Host "`n[2/5] Создание виртуального окружения..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  venv уже существует, пропускаем" -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "  venv создано" -ForegroundColor Green
}

# Активация venv
Write-Host "`n[3/5] Активация виртуального окружения..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Установка зависимостей
Write-Host "`n[4/5] Установка зависимостей..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Копирование конфигов
Write-Host "`n[5/5] Настройка конфигурации..." -ForegroundColor Yellow
if (-not (Test-Path "config\config.yaml")) {
    Copy-Item "config\config.yaml.example" "config\config.yaml"
    Write-Host "  config.yaml создан" -ForegroundColor Green
} else {
    Write-Host "  config.yaml уже существует" -ForegroundColor Gray
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  .env создан" -ForegroundColor Green
} else {
    Write-Host "  .env уже существует" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Установка завершена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nСледующие шаги:" -ForegroundColor Yellow
Write-Host "  1. Установите Ollama: https://ollama.ai"
Write-Host "  2. Pull моделей:"
Write-Host "     ollama pull qwen2.5vl:7b"
Write-Host "     ollama pull qwen2.5:7b-instruct"
Write-Host "  3. Запустите агента:"
Write-Host "     .\scripts\run.ps1"
Write-Host ""
