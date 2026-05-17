# start-all.ps1
# Скрипт единого запуска всего проекта

$projectRoot = $PSScriptRoot

# Активируем виртуальное окружение
Write-Host "Активация виртуального окружения..." -ForegroundColor Cyan
. "$projectRoot\.venv\Scripts\Activate.ps1"

# 1. Основные Docker-сервисы
Write-Host "`n[1/5] Запуск основных Docker-контейнеров..." -ForegroundColor Yellow
Push-Location "$projectRoot\log"
docker-compose -f docker-compose.simple.yml up -d minio spark-master spark-worker-1 postgres airflow-webserver airflow-scheduler airflow-worker airflow-init init-airflow-connections clickhouse superset-init superset trino
Pop-Location

# 4. Docker-сервисы split-service (запускаем раньше, чтобы контейнеры успели подняться)
Write-Host "`n[2/5] Запуск split-service Docker-контейнеров..." -ForegroundColor Yellow
Push-Location "$projectRoot\split-service"
docker-compose up -d
Pop-Location

# 2. Backend основного сервиса (в новом окне)
Write-Host "`n[3/5] Запуск backend main-service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$projectRoot\main-service\backend\app'; . '$projectRoot\.venv\Scripts\Activate.ps1'; Write-Host 'main-service backend запущен'; python main.py"

# 3. Frontend (в новом окне)
Write-Host "`n[4/5] Запуск frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$projectRoot\main-service\frontend'; Write-Host 'npm start запущен'; npm start"

# 5. Backend split-service (в новом окне)
Write-Host "`n[5/5] Запуск backend split-service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$projectRoot\split-service'; . '$projectRoot\.venv\Scripts\Activate.ps1'; Write-Host 'split-service backend запущен'; python main.py"

Write-Host "`nВсе компоненты запускаются в отдельных окнах. Это окно можно закрыть." -ForegroundColor Green