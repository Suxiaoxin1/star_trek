# ============================================
# 自动化竞品分析与市场情报系统 - PowerShell 命令脚本
# 用法: .\dev.ps1 <命令>
# 示例: .\dev.ps1 up    |   .\dev.ps1 logs   |   .\dev.ps1 help
# ============================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Show-Help {
    Write-Host ""
    Write-Host "可用命令:" -ForegroundColor Cyan
    Write-Host "  .\dev.ps1 up             启动所有服务"
    Write-Host "  .\dev.ps1 down           停止所有服务"
    Write-Host "  .\dev.ps1 restart        重启所有服务"
    Write-Host "  .\dev.ps1 build          重新构建镜像"
    Write-Host "  .\dev.ps1 logs           查看所有服务日志"
    Write-Host "  .\dev.ps1 ps             查看运行状态"
    Write-Host "  .\dev.ps1 clean          清理容器/卷/网络"
    Write-Host ""
    Write-Host "  .\dev.ps1 logs-backend    后端日志"
    Write-Host "  .\dev.ps1 logs-frontend   前端日志"
    Write-Host "  .\dev.ps1 logs-celery     Celery 日志"
    Write-Host "  .\dev.ps1 logs-nginx      Nginx 日志"
    Write-Host "  .\dev.ps1 db-shell        进入数据库"
    Write-Host "  .\dev.ps1 redis-cli       进入 Redis"
    Write-Host "  .\dev.ps1 rabbitmq-ui     打开 RabbitMQ 管理界面"
    Write-Host "  .\dev.ps1 backend-install 安装后端依赖"
    Write-Host "  .\dev.ps1 frontend-install 安装前端依赖"
    Write-Host "  .\dev.ps1 test            运行后端测试"
    Write-Host ""
}

switch ($Command) {
    "help"    { Show-Help }

    # ============ 基础操作 ============
    "up"      { docker compose up -d }
    "down"    { docker compose down }
    "restart" { docker compose down; docker compose up -d }
    "build"   { docker compose build --no-cache }
    "logs"    { docker compose logs -f --tail=100 }
    "ps"      { docker compose ps }

    # ============ 清理 ============
    "clean"   { docker compose down -v --remove-orphans }
    "clean-all" {
        docker compose down -v --remove-orphans
        docker system prune -f
    }

    # ============ 单服务日志 ============
    "logs-backend"  { docker compose logs -f backend }
    "logs-celery"   { docker compose logs -f celery_worker }
    "logs-frontend" { docker compose logs -f frontend }
    "logs-nginx"    { docker compose logs -f nginx }

    # ============ 开发辅助 ============
    "db-shell" {
        docker compose exec postgres psql -U admin -d competitive_intel
    }
    "redis-cli" {
        docker compose exec redis redis-cli -a redispass
    }
    "rabbitmq-ui" {
        Write-Host "打开 http://localhost:15672 (admin/admin)" -ForegroundColor Green
        Start-Process "http://localhost:15672"
    }
    "backend-install" {
        docker compose exec backend pip install -r requirements.txt
    }
    "frontend-install" {
        docker compose exec frontend pnpm install
    }

    # ============ 测试 ============
    "test" {
        docker compose exec backend pytest -v
    }
    "test-cov" {
        docker compose exec backend pytest --cov=app --cov-report=term-missing
    }

    # ============ 迁移 ============
    "migrate-init" {
        docker compose exec backend alembic init -t async alembic
    }
    "migrate-up" {
        docker compose exec backend alembic upgrade head
    }
    "migrate-down" {
        docker compose exec backend alembic downgrade -1
    }

    default {
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Show-Help
    }
}
