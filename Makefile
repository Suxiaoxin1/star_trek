# ============================================
# 自动化竞品分析与市场情报系统 - Makefile
# ============================================

.PHONY: help up down restart build logs ps clean

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make up        启动所有服务"
	@echo "  make down      停止所有服务"
	@echo "  make restart   重启所有服务"
	@echo "  make build     重新构建镜像"
	@echo "  make logs      查看所有服务日志"
	@echo "  make ps        查看运行状态"
	@echo "  make clean     清理容器/卷/网络"
	@echo ""
	@echo "  make backend-logs   后端日志"
	@echo "  make frontend-logs  前端日志"
	@echo "  make db-shell       进入数据库"
	@echo "  make redis-cli      进入 Redis"
	@echo "  make migrate        运行数据库迁移"

# ==================== 基础操作 ====================
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

build:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

# ==================== 清理 ====================
clean:
	docker compose down -v --remove-orphans

clean-all: clean
	@echo "清理未使用的 Docker 资源..."
	docker system prune -f

# ==================== 单服务操作 ====================
backend-logs:
	docker compose logs -f backend

celery-logs:
	docker compose logs -f celery_worker

frontend-logs:
	docker compose logs -f frontend

nginx-logs:
	docker compose logs -f nginx

# ==================== 开发辅助 ====================
db-shell:
	docker compose exec postgres psql -U admin -d competitive_intel

redis-cli:
	docker compose exec redis redis-cli -a redispass

rabbitmq-ui:
	@echo "打开 http://localhost:15672 (admin/admin)"

# 后端依赖安装
backend-install:
	docker compose exec backend pip install -r requirements.txt

# 前端依赖安装
frontend-install:
	docker compose exec frontend pnpm install

# 数据库迁移 (Alembic)
migrate-init:
	docker compose exec backend alembic init -t async alembic

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

migrate-up:
	docker compose exec backend alembic upgrade head

migrate-down:
	docker compose exec backend alembic downgrade -1

# 运行测试
test-backend:
	docker compose exec backend pytest -v

test-backend-cov:
	docker compose exec backend pytest --cov=app --cov-report=term-missing
