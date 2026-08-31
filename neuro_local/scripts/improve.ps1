# Neuro Local - Скрипт улучшения агента
# Анализ логов и предложения улучшений через LLM

param(
    [string]$Session,   # Дата сессии (YYYY-MM-DD)
    [switch]$Apply      # Применить улучшения
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Neuro Local - Улучшение" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($Apply) {
    Write-Host "`n[*] Применение улучшений..." -ForegroundColor Yellow
    python evolution/improve.py --apply $(if ($Session) { "--session $Session" })
} else {
    Write-Host "`n[*] Анализ последней сессии..." -ForegroundColor Yellow
    $result = python evolution/improve.py $(if ($Session) { "--session $Session" })
    
    Write-Host "`n[*] Результаты анализа:" -ForegroundColor Yellow
    Write-Host $result
}

Write-Host ""
