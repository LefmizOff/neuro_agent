# Neuro Local - Скрипт запуска
# Запускать после активации venv: .\venv\Scripts\Activate.ps1

param(
    [switch]$Run,      # Боевой режим (выполнять действия)
    [switch]$Once,     # Один цикл и выйти
    [string]$Goal     # Цель для выполнения
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Neuro Local Agent" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$mode = if ($Run) { "БОЕВОЙ РЕЖИМ" } else { "DRY-RUN (просмотр)" }
Write-Host "Режим: $mode" -ForegroundColor $(if ($Run) { "Red" } else { "Green" })
Write-Host ""

# Проверка Ollama
Write-Host "[*] Проверка Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 -UseBasicParsing
    Write-Host "  Ollama доступен" -ForegroundColor Green
    
    $models = ($response.Content | ConvertFrom-Json).models
    if ($models) {
        Write-Host "  Доступные модели:" -ForegroundColor Gray
        foreach ($m in $models) {
            Write-Host "    - $($m.name)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  ОШИБКА: Ollama не доступен!" -ForegroundColor Red
    Write-Host "  Запустите: ollama serve" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Запуск агента
if ($Once) {
    Write-Host "[*] Запуск одного цикла..." -ForegroundColor Yellow
    if ($Goal) {
        python mini_agent.py --once $(if ($Run) { "--run" }) --goal "$Goal"
    } else {
        python mini_agent.py --once $(if ($Run) { "--run" })
    }
} else {
    Write-Host "[*] Запуск интерактивного режима..." -ForegroundColor Yellow
    python mini_agent.py $(if ($Run) { "--run" })
}

Write-Host ""
Write-Host "Агент остановлен" -ForegroundColor Cyan
