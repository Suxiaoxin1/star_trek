# ============================================
# 自动化竞品分析与市场情报系统 - PowerShell 命令脚本
# 用法: .\dev.ps1 <命令>
# ============================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# 项目名（避免中文路径问题）
$DC = "docker compose -p ci"

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
    Write-Host "  .\dev.ps1 db-shell        进入数据库"
    Write-Host "  .\dev.ps1 redis-cli       进入 Redis"
    Write-Host "  .\dev.ps1 rabbitmq-ui     打开 RabbitMQ 管理界面"
    Write-Host ""
}

switch ($Command) {
    "help"    { Show-Help }

    # ============ 基础操作 ============
    "up"      { Invoke-Expression "$DC up -d" }
    "down"    { Invoke-Expression "$DC down" }
    "restart" { Invoke-Expression "$DC down"; Invoke-Expression "$DC up -d" }
    "build"   { Invoke-Expression "$DC build --no-cache" }
    "logs"    { Invoke-Expression "$DC logs -f --tail=100" }
    "ps"      { Invoke-Expression "$DC ps" }

    # ============ 清理 ============
    "clean"   { Invoke-Expression "$DC down -v --remove-orphans" }

    # ============ 单服务日志 ============
    "logs-backend"  { Invoke-Expression "$DC logs -f backend" }
    "logs-celery"   { Invoke-Expression "$DC logs -f celery_worker" }
    "logs-frontend" { Invoke-Expression "$DC logs -f frontend" }
    "logs-nginx"    { Invoke-Expression "$DC logs -f nginx" }

    # ============ 开发辅助 ============
    "db-shell" {
        Invoke-Expression "$DC exec postgres psql -U admin -d competitive_intel"
    }
    "redis-cli" {
        Invoke-Expression "$DC exec redis redis-cli -a redispass -p 6379"
    }
    "rabbitmq-ui" {
        Write-Host "打开 http://localhost:15672 (admin/admin)" -ForegroundColor Green
        Start-Process "http://localhost:15672"
    }
    "backend-install" {
        Invoke-Expression "$DC exec backend pip install -r requirements.txt"
    }
    "frontend-install" {
        Invoke-Expression "$DC exec frontend pnpm install"
    }
    "test" {
        Invoke-Expression "$DC exec backend pytest -v"
    }
    "test-cov" {
        Invoke-Expression "$DC exec backend pytest --cov=app --cov-report=term-missing"
    }

    default {
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Show-Help
    }
}
