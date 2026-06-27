# 自动化竞品分析与市场情报系统

> Competitive Intelligence & Market Analysis Platform
>
> 帮助企业自动盯紧竞争对手、采集市场情报、用 AI 深度分析、及时预警，形成可决策的洞察。

---

## 目录

- [1. 项目概述](#1-项目概述)
  - [1.1 它解决什么问题](#11-它解决什么问题)
  - [1.2 核心能力一览](#12-核心能力一览)
  - [1.3 适用人群](#13-适用人群)
- [2. 技术架构](#2-技术架构)
  - [2.1 整体架构图](#21-整体架构图)
  - [2.2 技术栈](#22-技术栈)
  - [2.3 服务拓扑](#23-服务拓扑)
  - [2.4 数据模型](#24-数据模型)
- [3. 安装要求](#3-安装要求)
  - [3.1 硬件要求](#31-硬件要求)
  - [3.2 软件依赖](#32-软件依赖)
  - [3.3 目录结构](#33-目录结构)
- [4. 配置说明](#4-配置说明)
  - [4.1 环境变量](#41-环境变量)
  - [4.2 AI 大模型配置](#42-ai-大模型配置)
  - [4.3 端口规划](#43-端口规划)
- [5. 安装与启动](#5-安装与启动)
  - [5.1 首次部署（Docker Compose）](#51-首次部署docker-compose)
  - [5.2 常用运维命令](#52-常用运维命令)
  - [5.3 本地开发模式](#53-本地开发模式)
  - [5.4 数据库迁移](#54-数据库迁移)
- [6. 使用教程](#6-使用教程)
  - [6.1 登录与角色](#61-登录与角色)
  - [6.2 核心业务流程](#62-核心业务流程)
  - [6.3 竞品管理](#63-竞品管理)
  - [6.4 数据源与自动采集](#64-数据源与自动采集)
  - [6.5 市场情报](#65-市场情报)
  - [6.6 AI 智能分析](#66-ai-智能分析)
  - [6.7 分析报告](#67-分析报告)
  - [6.8 预警中心](#68-预警中心)
  - [6.9 大模型选型与配置（进阶）](#69-大模型选型与配置进阶)
- [7. 故障排除](#7-故障排除)
- [8. 常见问题 FAQ](#8-常见问题-faq)
- [9. 文档缺口与改进建议](#9-文档缺口与改进建议)

---

## 1. 项目概述

### 1.1 它解决什么问题

做产品/市场的人经常面临三个痛点：

1. **信息分散**：竞品动态散落在新闻、RSS、社交平台、公众号，手动盯不过来。
2. **分析耗时**：收集到的信息要人工阅读、提炼、写报告，效率低。
3. **响应滞后**：竞品发生大事（融资、调价、事故）时，往往事后才听说，错过最佳响应窗口。

本系统通过 **「自动采集 → 结构化整理 → AI 分析 → 智能预警」** 的闭环解决以上问题：

```
数据源配置 → 自动采集 → 市场情报 → AI 分析 → 分析报告
                              ↓
                         预警规则命中 → 自动告警
```

### 1.2 核心能力一览

| 模块 | 能力 | 说明 |
|---|---|---|
| 竞品管理 | 竞品档案、产品、功能特性、价格历史 | 多维度对比竞品实力 |
| 数据源管理 | RSS / API / 网页爬虫 / 社交媒体 | 可配置定时采集频率 |
| 采集数据 | 原始素材归档、去重、处理标记 | 采集到的原始内容池 |
| 市场情报 | 结构化动态、情感、重要度、分类 | 可筛选可统计的结构化情报 |
| AI 智能分析 | 情感分析、摘要、报告生成、竞品深度分析 | 调用 LLM 自动产出结论 |
| 分析报告 | Markdown 报告管理、状态流转 | AI 生成 + 人工编辑 |
| 预警中心 | 关键词规则、历史告警、已读已处理 | 自动触发 + 人工确认 |
| 大模型选型 | 多维评分、场景推荐、模型配置 | 辅助选择最合适的 LLM |

### 1.3 适用人群

- **产品经理 / 市场分析师**：日常跟踪竞品、产出分析报告
- **战略规划人员**：评估竞品威胁、制定应对策略
- **数据团队**：搭建自动化情报采集管道
- **企业管理者**：通过仪表盘和预警掌握市场动态

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        浏览器 / 终端                          │
│              http://localhost:5173 (前端)                    │
│              http://localhost:8000/docs (API 文档)           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                      Nginx 反向代理 (:8080)                  │
└─────┬────────────────────────────────────────┬──────────────┘
      │                                        │
┌─────▼──────────────┐              ┌──────────▼───────────────┐
│  Vue 3 前端 (:5173)│              │ FastAPI 后端 (:8000)      │
│  Vite + Element Plus│             │  REST API + SSE           │
│  Pinia + ECharts   │              │  JWT 鉴权 + RBAC          │
└────────────────────┘              └──┬────────────┬───────────┘
                                       │            │
                                       │ SQL        │ Celery 任务
                                       ▼            ▼
                           ┌────────────────┐  ┌─────────────────┐
                           │ PostgreSQL 16  │  │ Celery Worker   │
                           │ (:5432)        │  │ + Beat 调度     │
                           │ 12 张业务表     │  │ 异步采集/分析    │
                           └────────────────┘  └──┬──────────┬───┘
                                                 │          │
                                       ┌─────────▼───┐  ┌──▼──────────┐
                                       │ Redis 7     │  │ RabbitMQ 3.13│
                                       │ (:6379)     │  │ (:5672)      │
                                       │ 缓存/结果后端│  │ 消息队列      │
                                       └─────────────┘  └──────────────┘
                                                  
                           ┌────────────────────────────────────┐
                           │     外部 LLM API（OpenAI 兼容）      │
                           │  OpenAI / DeepSeek / 通义千问 等    │
                           └────────────────────────────────────┘
```

### 2.2 技术栈

**后端**（[backend/](backend/)）

| 分类 | 技术 | 版本 | 用途 |
|---|---|---|---|
| Web 框架 | FastAPI | 0.115.0 | REST API、自动文档 |
| ASGI 服务器 | uvicorn | 0.30.6 | 异步服务 |
| ORM | SQLAlchemy | 2.0.35 | 异步数据库访问 |
| 数据库驱动 | asyncpg / psycopg2 | 0.29 / 2.9.9 | PostgreSQL 异步/同步驱动 |
| 迁移工具 | Alembic | 1.13.2 | 数据库版本管理 |
| 数据校验 | Pydantic | 2.9.2 | 请求/响应模型 |
| 认证 | python-jose + passlib | 3.3.0 / 1.7.4 | JWT + bcrypt 密码 |
| 异步任务 | Celery | 5.4.0 | 定时采集、AI 分析 |
| 消息队列 | RabbitMQ | 3.13 | Celery broker |
| 缓存 | Redis | 7.x | 结果后端、缓存 |
| HTTP 采集 | httpx + beautifulsoup4 + feedparser | - | RSS/API/爬虫 |
| LLM 集成 | openai | >=1.40.0 | 兼容 OpenAI 接口 |
| 日志 | loguru | 0.7.2 | 结构化日志 |
| 测试 | pytest + pytest-asyncio | 8.3.3 / 0.24.0 | 单元/集成测试 |

**前端**（[frontend/](frontend/)）

| 分类 | 技术 | 版本 | 用途 |
|---|---|---|---|
| 框架 | Vue 3 | ^3.5.0 | 组合式 API |
| 构建 | Vite | ^5.4.0 | 开发服务器/打包 |
| 语言 | TypeScript | ^5.5.0 | 类型安全 |
| UI 库 | Element Plus | ^2.8.0 | 组件库 |
| 图表 | ECharts + vue-echarts | ^5.5 / ^7.0 | 数据可视化 |
| 状态管理 | Pinia | ^2.2.0 | 全局状态 |
| 路由 | vue-router | ^4.4.0 | SPA 路由 |
| HTTP | axios | ^1.7.0 | API 调用 |
| 日期 | dayjs | ^1.11.0 | 时间处理 |

**基础设施**

| 组件 | 镜像 | 用途 |
|---|---|---|
| PostgreSQL | postgres:16-alpine | 主数据库 |
| Redis | redis:7-alpine | 缓存、Celery 结果后端 |
| RabbitMQ | rabbitmq:3.13-management-alpine | Celery 消息队列 |
| Nginx | nginx:1.25-alpine | 反向代理 |

### 2.3 服务拓扑

[docker-compose.yml](docker-compose.yml) 定义了 8 个服务，依赖关系如下：

```
postgres ──┐
redis ─────┼──► backend ──┐
rabbitmq ──┤    celery_worker
           │    celery_beat
           │
           └──► frontend ──► nginx
```

- `backend`：FastAPI 主服务，对外提供 REST API
- `celery_worker`：执行异步任务（采集、AI 分析）
- `celery_beat`：定时调度器（按间隔触发采集）
- `frontend`：Vue 开发服务器（Vite）
- `nginx`：统一入口，将 `/api` 转发到 backend，其余到 frontend

### 2.4 数据模型

系统共 12 张表，核心 ER 关系（详见 [database/init.sql](database/init.sql) 与 [backend/app/models.py](backend/app/models.py)）：

```
Competitor（竞品）
  ├── Product（产品）
  ├── CompetitorFeature（功能特性）
  ├── PricingHistory（价格历史）
  ├── MarketIntelligence（市场情报）
  │       └── AnalysisReport（分析报告）
  └── SentimentData（舆情数据）

DataSource（数据源）
  └── CollectedData（采集数据）

AlertRule（预警规则）
  └── AlertHistory（预警历史）

User（用户）
```

字段设计要点：
- 主键统一使用 UUID（`gen_random_uuid()`）
- 标签/配置类字段使用 JSONB（如 `tags`、`metadata`、`crawl_config`）
- 软删除采用 `is_active` 标记，不物理删除
- 关键字段均建索引（name、tier、category、sentiment、created_at 等）

---

## 3. 安装要求

### 3.1 硬件要求

| 场景 | CPU | 内存 | 磁盘 | 说明 |
|---|---|---|---|---|
| 体验/开发 | 2 核 | 4 GB | 10 GB | 单机 Docker |
| 小团队 | 4 核 | 8 GB | 50 GB | 含历史数据归档 |
| 生产部署 | 8 核+ | 16 GB+ | 200 GB+ | 建议独立数据库 |

### 3.2 软件依赖

| 软件 | 最低版本 | 必需 | 说明 |
|---|---|---|---|
| Docker | 24.0 | 是 | 容器运行时 |
| Docker Compose | v2.20 | 是 | 服务编排（推荐 `docker compose` v2） |
| Git | 2.30 | 是 | 拉取代码 |
| Node.js | 20.x | 仅本地开发 | 不用 Docker 跑前端时需要 |
| Python | 3.11+ | 仅本地开发 | 不用 Docker 跑后端时需要 |

> 推荐使用 Docker Compose 一键部署，无需在本机安装 Node/Python。

### 3.3 目录结构

```
自动化竞品分析与市场情报系统/
├── backend/                    # 后端 FastAPI
│   ├── app/
│   │   ├── routes/             # 路由层（9 个模块）
│   │   ├── services/           # 业务服务（LLM、通知等）
│   │   ├── tasks/              # Celery 异步任务
│   │   ├── prompts/            # LLM 提示词模板
│   │   ├── models.py           # SQLAlchemy 模型
│   │   ├── schemas.py          # Pydantic 校验模型
│   │   ├── auth.py             # JWT 鉴权
│   │   ├── config.py           # 配置
│   │   └── main.py             # FastAPI 入口
│   ├── alembic/                # 数据库迁移
│   ├── tests/                  # 单元测试（12 个测试文件）
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # 前端 Vue 3
│   ├── src/
│   │   ├── api/                # API 调用层
│   │   ├── views/              # 页面（10 个视图）
│   │   ├── stores/             # Pinia 状态
│   │   ├── router/             # 路由
│   │   └── types/              # 类型定义
│   ├── Dockerfile
│   └── package.json
├── database/
│   └── init.sql                # 数据库初始化脚本
├── nginx/
│   └── nginx.conf              # Nginx 配置
├── docs/
│   └── GIT_FLOW.md             # Git 提交规范
├── docker-compose.yml          # 服务编排
├── .env.example                # 环境变量模板
├── Makefile                    # Linux/macOS 命令
├── dev.ps1                     # Windows PowerShell 命令
└── README.md                   # 本文档
```

---

## 4. 配置说明

### 4.1 环境变量

所有配置通过 `.env` 文件管理，模板见 [.env.example](.env.example)。复制后修改：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| **数据库** | | |
| `POSTGRES_USER` | admin | 数据库用户名 |
| `POSTGRES_PASSWORD` | change-me | **生产环境务必修改** |
| `POSTGRES_DB` | competitive_intel | 数据库名 |
| `POSTGRES_PORT` | 5432 | 宿主机映射端口 |
| **Redis** | | |
| `REDIS_PASSWORD` | redispass | Redis 密码 |
| `REDIS_PORT` | 6380 | 宿主机映射端口（默认 6380 避免冲突） |
| **RabbitMQ** | | |
| `RABBITMQ_USER` | admin | 管理用户名 |
| `RABBITMQ_PASSWORD` | admin | 管理密码 |
| `RABBITMQ_AMQP_PORT` | 5672 | AMQP 端口 |
| `RABBITMQ_MGMT_PORT` | 15672 | 管理界面端口 |
| **应用端口** | | |
| `BACKEND_PORT` | 8000 | 后端 API 端口 |
| `FRONTEND_PORT` | 5173 | 前端开发服务器端口 |
| `NGINX_PORT` | 8080 | Nginx 统一入口端口 |
| **安全** | | |
| `SECRET_KEY` | your-secret-key-here | **生产环境务必修改** |
| **AI 大模型** | | |
| `OPENAI_API_KEY` | - | LLM API Key（见 4.2） |
| `OPENAI_API_BASE` | - | 自定义 API 地址 |
| `OPENAI_MODEL` | gpt-4o-mini | 默认模型名 |

### 4.2 AI 大模型配置

系统兼容所有 OpenAI 接口格式的 LLM 提供商。常见配置方式：

**方案 A：使用 OpenAI 官方**

```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini
# OPENAI_API_BASE 留空
```

**方案 B：使用 DeepSeek**（性价比高，推荐国内用户）

```env
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**方案 C：使用通义千问**

```env
OPENAI_API_KEY=sk-your-dashscope-key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
```

> 未配置 `OPENAI_API_KEY` 时，系统其他功能正常，仅 AI 智能分析模块不可用（前端会提示「未配置」）。

### 4.3 端口规划

默认端口分配（如冲突可在 `.env` 修改）：

| 服务 | 端口 | 访问地址 | 说明 |
|---|---|---|---|
| 前端 | 5173 | http://localhost:5173 | Vite 开发服务器 |
| 后端 API | 8000 | http://localhost:8000/api/v1 | REST API |
| API 文档 | 8000 | http://localhost:8000/docs | Swagger UI |
| Nginx 入口 | 8080 | http://localhost:8080 | 统一入口 |
| PostgreSQL | 5432 | - | 数据库 |
| Redis | 6380 | - | 缓存 |
| RabbitMQ AMQP | 5672 | - | 消息队列 |
| RabbitMQ 管理 | 15672 | http://localhost:15672 | 管理界面（admin/admin） |

---

## 5. 安装与启动

### 5.1 首次部署（Docker Compose）

**前置**：已安装 Docker 与 Docker Compose v2。

```bash
# 1. 克隆代码
git clone <仓库地址>
cd 自动化竞品分析与市场情报系统

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少修改 POSTGRES_PASSWORD、SECRET_KEY、OPENAI_API_KEY

# 3. 构建并启动所有服务
docker compose up -d --build

# 4. 等待服务就绪（约 30-60 秒）
docker compose ps

# 5. 创建管理员账号（首次）
docker compose exec backend python -m app.init_admin
# 或直接访问前端注册页注册第一个 admin 用户
```

启动完成后：
- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- RabbitMQ 管理：http://localhost:15672（admin/admin）

### 5.2 常用运维命令

项目提供 [Makefile](Makefile)（Linux/macOS）和 [dev.ps1](dev.ps1)（Windows）两套命令，功能等价。

**Windows PowerShell**：

```powershell
.\dev.ps1 up              # 启动所有服务
.\dev.ps1 down            # 停止所有服务
.\dev.ps1 restart         # 重启
.\dev.ps1 logs            # 查看所有日志
.\dev.ps1 logs-backend    # 后端日志
.\dev.ps1 logs-celery     # Celery 日志
.\dev.ps1 ps              # 查看运行状态
.\dev.ps1 db-shell        # 进入 PostgreSQL
.\dev.ps1 redis-cli       # 进入 Redis
.\dev.ps1 rabbitmq-ui     # 打开 RabbitMQ 管理界面
.\dev.ps1 clean           # 清理容器/卷/网络（⚠️ 会删数据）
.\dev.ps1 test            # 运行后端测试
```

**Linux/macOS**：

```bash
make up           # 启动
make down         # 停止
make logs         # 日志
make ps           # 状态
make db-shell     # 数据库
make migrate-up   # 执行迁移
make test-backend # 测试
```

**直接用 docker compose**：

```bash
docker compose -p ci up -d        # -p ci 指定项目名
docker compose -p ci logs -f backend
docker compose -p ci ps
```

### 5.3 本地开发模式

不使用 Docker，直接在本机跑前后端（适合二次开发）。

**后端**：

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# 配置环境变量指向本地或 Docker 内的数据库
export DATABASE_URL="postgresql+asyncpg://admin:secret@localhost:5432/competitive_intel"
uvicorn app.main:app --reload --port 8000
```

**前端**：

```bash
cd frontend
npm install
npm run dev    # 默认 http://localhost:5173
```

> 本地开发时，[vite.config.ts](frontend/vite.config.ts) 已配置代理，将 `/api` 转发到 `http://backend:8000`。若后端不在 Docker 内，需把 `target` 改为 `http://localhost:8000`。

### 5.4 数据库迁移

项目使用 Alembic 管理数据库版本。首次启动时 [main.py](backend/app/main.py) 会自动 `create_all` 建表，但建议使用迁移以支持后续变更：

```bash
# 生成迁移脚本（修改模型后执行）
docker compose exec backend alembic revision --autogenerate -m "描述变更"

# 应用迁移
docker compose exec backend alembic upgrade head

# 回滚一步
docker compose exec backend alembic downgrade -1
```

迁移脚本位于 [backend/alembic/versions/](backend/alembic/versions/)。

---

## 6. 使用教程

### 6.1 登录与角色

系统采用 **JWT + RBAC** 鉴权，三种角色权限不同：

| 角色 | 权限 |
|---|---|
| `admin` 管理员 | 全部功能 + 用户管理 + AI 模型配置 |
| `analyst` 分析师 | 增删改查所有业务数据 + 使用 AI 分析 |
| `viewer` 查看者 | 仅查看，不能修改 |

**首次登录**：
1. 访问 http://localhost:5173
2. 点击「注册」创建账号（首个账号建议选 admin 角色）
3. 登录后系统将 JWT 存入 `localStorage`，后续请求自动携带

**Token 机制**：
- Access Token 有效期 60 分钟
- Refresh Token 有效期 7 天
- 401 时前端自动用 Refresh Token 刷新

### 6.2 核心业务流程

系统围绕「**盯谁 → 去哪采集 → 看情报 → AI 分析 → 出报告 → 出事预警**」展开：

```
① 竞品管理       ② 数据源管理        ③ 市场情报
   (盯谁)    →     (去哪采集)    →     (结构化动态)
                                              ↓
                                         ④ AI 智能分析
                                              ↓
                   ⑥ 预警中心   ←    ⑤ 分析报告
                   (自动告警)        (最终成果)
```

### 6.3 竞品管理

**路径**：侧边栏 → 竞品管理

**做什么**：建立竞争对手档案，记录产品、功能、价格。

**操作步骤**：

1. **新增竞品**：点击「新建」，填写名称、官网、规模、融资阶段、标签等
   - `tier` 字段：`direct`（直接竞品）/ `indirect`（间接）/ `potential`（潜在）
2. **管理产品**：进入竞品详情 → 产品页签，添加该竞品的产品（名称、定价模式、目标市场）
3. **功能对比**：详情 → 功能特性，按维度记录（如「长文本支持：full」「多模态：partial」）
   - `support_level`：`full` / `partial` / `none` / `unknown`
4. **价格历史**：详情 → 价格历史，记录调价记录（涨价/降价/新增/不变）

**API 示例**：

```bash
# 创建竞品
curl -X POST http://localhost:8000/api/v1/competitors/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"智谱 AI","tier":"direct","tags":["大模型"]}'
```

### 6.4 数据源与自动采集

**路径**：侧边栏 → 数据源管理

**做什么**：配置情报采集来源，系统按设定频率自动抓取。

**支持的类型**：

| 类型 | 说明 | 典型场景 |
|---|---|---|
| `rss` | RSS 订阅 | 36氪、机器之心、量子位 |
| `api` | 第三方 API | AI 新闻聚合、HuggingFace |
| `web_scraper` | 网页爬虫（BeautifulSoup） | 知乎专栏、公众号 |
| `social_media` | 社交媒体 | 微博话题 |

**配置步骤**：

1. 新增数据源，填写名称、类型、URL、采集间隔（分钟）
2. `crawl_config` 字段：爬虫选择器、过滤关键词等（JSON）
3. `api_config` 字段：API Key、请求头等（JSON）
4. 保存后，Celery Beat 会按间隔触发采集任务
5. 采集到的内容进入「采集数据」模块

**手动触发采集**：

```bash
# 触发单个数据源采集
curl -X POST http://localhost:8000/api/v1/datasources/{id}/crawl \
  -H "Authorization: Bearer $TOKEN"
```

**采集数据模块**：查看原始素材，可标记为「已处理」或删除。

### 6.5 市场情报

**路径**：侧边栏 → 市场情报

**做什么**：结构化的竞品动态，是 AI 分析的输入源。

**字段说明**：

| 字段 | 说明 | 取值 |
|---|---|---|
| `title` | 情报标题 | 自由文本 |
| `summary` | 摘要 | 自由文本 |
| `category` | 分类 | 融资/产品发布/价格变动/战略合作/市场表现/事故/舆情… |
| `sentiment` | 情感 | positive/negative/neutral |
| `importance` | 重要度 | 1-5 星 |
| `source_name` | 来源 | 36氪、官方公告等 |
| `published_at` | 发布时间 | ISO 日期 |
| `tags` | 标签 | JSON 数组 |
| `competitor_id` | 关联竞品 | 必填 |

**操作**：
- 手动新增情报
- 筛选：按竞品、分类、情感、重要度、时间范围
- 统计：页面顶部展示分类分布、情感分布、重要度分布图表
- 点击「AI 情感分析」：对单条情报自动判断情感
- 点击「AI 摘要」：自动提取关键要点

### 6.6 AI 智能分析

**路径**：侧边栏 → AI 智能分析

**前置**：已在 `.env` 配置 `OPENAI_API_KEY`（见 4.2）。页面顶部会显示 AI 服务状态。

**四大能力**：

| 功能 | 输入 | 输出 | 用途 |
|---|---|---|---|
| 情感分析 | 一段文本 | 情感标签 + 置信度 + 关键短语 + 推理 | 快速判断正负面 |
| 摘要提取 | 一段文本 | 摘要 + 关键点 + 影响等级 + 行动建议 | 压缩长文 |
| 报告生成 | 竞品 + 情报 | Markdown 分析报告（自动入库） | 周报/月报 |
| 竞品深度分析 | 竞品 ID | 优势/劣势/威胁/机会/战略建议 | SWOT 战略 |

**操作示例**：

1. **单条情感分析**：在输入框粘贴文本 → 点击「分析」 → 返回情感、置信度、关键短语
2. **情报级分析**：选择一条市场情报 → 点击「情感分析」 → 结果自动回写到情报的 `sentiment` 字段
3. **生成报告**：
   - 选择竞品 + 情报数量（如最近 5 条）
   - 填写报告标题
   - 点击「生成报告」 → AI 调用 LLM 生成完整 Markdown
   - 报告自动保存到「分析报告」模块
4. **流式生成**：支持 SSE 流式输出，实时看到生成内容

**API 示例**：

```bash
# 竞品深度分析
curl -X POST http://localhost:8000/api/v1/ai/competitor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"competitor_id":"<uuid>","intelligence_limit":5}'
```

### 6.7 分析报告

**路径**：侧边栏 → 分析报告

**做什么**：管理 AI 生成或人工撰写的分析报告。

**报告状态流转**：

```
draft（草稿）→ in_progress（进行中）→ completed（已完成）→ archived（已归档）
```

**操作**：
- 查看报告列表，按状态、类型筛选
- 点击查看完整 Markdown 内容（前端渲染）
- 修改状态、编辑内容
- 报告可关联一条市场情报（`intelligence_id`）

### 6.8 预警中心

**路径**：侧边栏 → 预警中心

**做什么**：定义预警规则，系统采集到命中情报时自动告警。

**预警规则字段**：

| 字段 | 说明 | 示例 |
|---|---|---|
| `name` | 规则名称 | 竞品价格大幅变动预警 |
| `keywords` | 关键词列表 | `["涨价","降价","调价"]` |
| `target_type` | 监控对象类型 | competitor/industry/social_media/market/technology |
| `severity` | 严重程度 | low/medium/high/critical |
| `notification_channels` | 通知渠道 | `["email","database","sse"]` |
| `is_active` | 是否启用 | true/false |

**预警历史**：
- 当采集情报命中关键词时，自动生成 `alert_history` 记录
- 可标记「已读」`is_read`
- 可标记「已处理」`is_resolved`
- 顶部统计：按严重程度、按未读数

### 6.9 大模型选型与配置（进阶）

**路径**：侧边栏底部 → 大模型选型 / LLM 配置

这两个模块面向技术决策者，辅助选择最合适的 LLM：

- **大模型选型**：多维度评分（性能/价格/上下文/多模态）、场景推荐
- **LLM 配置**：管理多个 LLM 提供商配置，支持切换默认模型

---

## 7. 故障排除

### 7.1 服务启动失败

**问题**：`docker compose up` 后某服务一直 restarting

**排查**：

```bash
# 查看具体服务日志
docker compose logs backend
docker compose logs postgres

# 常见原因
# 1. 端口被占用 → 修改 .env 中对应端口
# 2. 数据库密码不对 → 检查 .env 的 POSTGRES_PASSWORD
# 3. 依赖服务未就绪 → 等待 healthcheck 通过
```

### 7.2 前端页面 404 / 白屏

**问题**：访问 http://localhost:5173 显示其他项目或白屏

**原因**：5173 端口被其他 Vite 项目占用

**解决**：

```bash
# 查看占用进程
netstat -ano | findstr :5173        # Windows
lsof -i :5173                       # Linux/macOS

# 停止占用进程，或修改本项目端口
# 编辑 .env：FRONTEND_PORT=5174
docker compose up -d frontend
```

### 7.3 API 调用返回 401

**问题**：所有 API 返回 401 Unauthorized

**排查**：
1. 检查 `localStorage.ci_access_token` 是否存在
2. Token 是否过期（60 分钟）→ 重新登录
3. 后端 `SECRET_KEY` 是否变更（变更后旧 Token 失效）

### 7.4 AI 功能返回 500

**问题**：调用 `/ai/*` 接口报 500

**排查**：

```bash
# 查看后端日志
docker compose logs backend --tail 50

# 常见原因
# 1. OPENAI_API_KEY 未配置或无效 → 检查 .env
# 2. OPENAI_API_BASE 错误 → DeepSeek 应为 https://api.deepseek.com/v1
# 3. 网络无法访问 LLM 服务 → 检查出网
# 4. 模型名错误 → 确认 OPENAI_MODEL 与提供商匹配
```

**验证 AI 配置**：

```bash
curl http://localhost:8000/api/v1/ai/status \
  -H "Authorization: Bearer $TOKEN"
# 返回 available:true 表示已配置
```

### 7.5 Celery 任务不执行

**问题**：数据源配置了但没自动采集

**排查**：

```bash
# 检查 worker 与 beat 是否运行
docker compose ps celery_worker celery_beat

# 查看 worker 日志
docker compose logs celery_worker --tail 50

# 常见原因
# 1. worker 未启动 → docker compose up -d celery_worker
# 2. beat 未启动 → 定时任务不会触发
# 3. RabbitMQ 连接失败 → 检查 CELERY_BROKER_URL
```

### 7.6 数据库连接失败

**问题**：后端报「数据库连接失败」

**排查**：

```bash
# 检查 PostgreSQL 健康
docker compose ps postgres
docker compose exec postgres pg_isready -U admin

# 进入数据库验证
docker compose exec postgres psql -U admin -d competitive_intel -c "\dt"
```

### 7.7 中文显示乱码

**问题**：PowerShell 终端中文乱码

**原因**：PowerShell 默认 GBK 编码，数据库存储的是正确 UTF-8

**解决**：

```powershell
$env:PYTHONIOENCODING="utf-8"
chcp 65001
```

### 7.8 运行测试失败

**问题**：`pytest` 报导入错误

**排查**：

```bash
cd backend
python -m pytest tests/ -v --tb=short

# 常见依赖缺失
pip install feedparser celery[redis] loguru email-validator
```

---

## 8. 常见问题 FAQ

### Q1：必须配置 OpenAI 才能用吗？

**不必须**。未配置 `OPENAI_API_KEY` 时，竞品管理、数据采集、情报管理、预警等模块均可正常使用，仅「AI 智能分析」模块不可用。前端会显示「AI 服务未配置」提示。

### Q2：支持哪些 LLM 提供商？

所有兼容 OpenAI 接口格式的提供商，包括但不限于：
- OpenAI（GPT-4o、GPT-4o-mini）
- DeepSeek（deepseek-chat、deepseek-coder）
- 通义千问（qwen-plus、qwen-turbo）
- 智谱 GLM（glm-4）
- 月之暗面 Moonshot

只需配置 `OPENAI_API_BASE` 指向对应地址即可。

### Q3：数据会被删除吗？

**默认不会**。系统采用软删除（`is_active` 标记），竞品/数据源停用后数据仍在。`docker compose down` 不会删除数据卷，只有 `docker compose down -v` 或 `.\dev.ps1 clean` 才会清除数据。

### Q4：如何备份数据库？

```bash
# 备份
docker compose exec postgres pg_dump -U admin competitive_intel > backup.sql

# 恢复
docker compose exec -T postgres psql -U admin -d competitive_intel < backup.sql
```

### Q5：可以部署到生产环境吗？

当前版本主要面向开发与体验，生产部署需额外考虑：
- 修改所有默认密码（POSTGRES_PASSWORD、REDIS_PASSWORD、SECRET_KEY）
- 使用 HTTPS（配置 Nginx SSL 证书）
- 前端构建生产版本（`npm run build`）而非 dev 模式
- 数据库定期备份
- 配置日志收集与监控

### Q6：如何添加新的数据源类型？

数据采集逻辑位于 [backend/app/tasks/crawler.py](backend/app/tasks/crawler.py)。如需支持新的采集方式（如微信公众号、抖音），可在此扩展采集函数，并在 [schemas.py](backend/app/schemas.py) 的 `DataSourceType` 枚举中新增类型。

### Q7：如何自定义 AI 提示词？

LLM 提示词模板位于 [backend/app/prompts/](backend/app/prompts/)：
- `sentiment.txt` — 情感分析
- `summary.txt` — 摘要提取
- `report.txt` — 报告生成
- `competitor_analysis.txt` — 竞品分析

修改对应文件即可调整 AI 行为，无需改代码。

### Q8：测试账号是什么？

测试环境默认账号（如已注入测试数据）：

```
用户名: testadmin
密码:   Test123456
角色:   admin
```

首次部署无此账号，需通过注册页面创建。

### Q9：如何运行单元测试？

```bash
# Docker 内运行
docker compose exec backend pytest -v

# 本地运行
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v --tb=short

# 带覆盖率
python -m pytest --cov=app --cov-report=term-missing
```

测试文件位于 [backend/tests/](backend/tests/)，共 12 个测试文件，使用 SQLite 内存数据库隔离。

### Q10：端口冲突怎么改？

编辑 `.env` 文件，修改对应端口：

```env
FRONTEND_PORT=5174    # 前端
BACKEND_PORT=8001     # 后端
NGINX_PORT=8081       # Nginx
POSTGRES_PORT=5433    # 数据库
```

然后 `docker compose up -d` 即可。

---

## 9. 文档缺口与改进建议

基于对项目代码与现有文档的分析，识别出以下缺口，建议补充以提升可用性：

### 9.1 已识别的文档缺口

| 缺口 | 影响 | 建议补充内容 |
|---|---|---|
| **API 接口文档** | 开发者无法快速查阅接口 | 虽然 Swagger 自动生成（/docs），但缺少独立的 API 参考文档，建议补充每个端点的请求/响应示例 |
| **数据库 ER 图** | 新开发者难以理解表关系 | 建议生成可视化 ER 图（如用 dbdiagram.io），补充字段说明 |
| **部署到生产指南** | 用户不知如何上生产 | 补充生产环境配置清单：HTTPS、备份、监控、性能调优 |
| **前端二次开发指南** | 二次开发门槛高 | 补充组件目录结构、状态管理规范、API 调用约定 |
| **Celery 任务清单** | 不清楚有哪些异步任务 | 列出所有定时任务及其触发频率、输入输出 |
| **权限矩阵详表** | 角色权限不够细化 | 补充每个 API 端点对角色的要求（admin/analyst/viewer 分别能否访问） |
| **数据采集配置示例** | 用户不知如何配爬虫 | 为每种数据源类型提供完整的 `crawl_config` / `api_config` 配置示例 |
| **预警规则配置示例** | 用户不知如何写关键词 | 提供常见行业（AI、电商、SaaS）的预警规则模板 |
| **升级指南** | 版本升级有风险 | 补充数据库迁移、配置变更、兼容性说明的升级流程 |
| **性能基准** | 不知系统能扛多大负载 | 补充并发用户数、数据量、采集频率的性能基准测试结果 |

### 9.2 建议补充的文档

1. **CHANGELOG.md** — 版本变更记录，遵循语义化版本
2. **CONTRIBUTING.md** — 贡献指南（代码规范、PR 流程、测试要求）
3. **DEPLOYMENT.md** — 生产部署手册（含 Kubernetes 部署方案）
4. **API_REFERENCE.md** — 离线 API 参考文档
5. **SECURITY.md** — 安全配置指南（密钥管理、CORS、SQL 注入防护）
6. **screenshots/** — 各功能模块截图，降低新用户认知成本

### 9.3 文档维护建议

- **与代码同步**：每次修改接口/模型时同步更新文档，避免文档过时
- **版本化**：文档标注适用的代码版本号
- **多语言**：当前为中文，如需国际化建议补充英文版
- **可交互**：API 示例提供可复制的 curl/Postman 集合
- **反馈渠道**：在文档末尾提供问题反馈方式

---

## 附录

### A. 相关文档

- [docs/GIT_FLOW.md](docs/GIT_FLOW.md) — Git 提交规范（Conventional Commits）
- [database/init.sql](database/init.sql) — 数据库表结构定义
- [backend/app/models.py](backend/app/models.py) — SQLAlchemy 模型
- [backend/app/schemas.py](backend/app/schemas.py) — Pydantic 校验模型

### B. 常用 API 速查

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/login` | 登录获取 Token |
| GET | `/api/v1/auth/me` | 获取当前用户 |
| GET/POST | `/api/v1/competitors/` | 竞品列表/创建 |
| GET/POST | `/api/v1/intelligence/` | 情报列表/创建 |
| GET/POST | `/api/v1/reports/` | 报告列表/创建 |
| GET/POST | `/api/v1/alerts/rules` | 预警规则 |
| GET | `/api/v1/alerts/history` | 预警历史 |
| GET/POST | `/api/v1/datasources/` | 数据源 |
| GET | `/api/v1/collected-data/` | 采集数据 |
| GET | `/api/v1/ai/status` | AI 服务状态 |
| POST | `/api/v1/ai/sentiment` | 情感分析 |
| POST | `/api/v1/ai/summary` | 摘要提取 |
| POST | `/api/v1/ai/report/generate` | 生成报告 |
| POST | `/api/v1/ai/competitor` | 竞品深度分析 |
| GET | `/api/v1/ai/models` | 可用模型列表 |
| GET | `/api/v1/ai/usage` | 用量统计 |

完整接口文档：http://localhost:8000/docs（Swagger UI）

### C. 默认账号与端口

| 项 | 值 |
|---|---|
| 前端地址 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |
| Nginx 入口 | http://localhost:8080 |
| RabbitMQ 管理 | http://localhost:15672（admin/admin） |
| 测试账号 | testadmin / Test123456 |
| PostgreSQL | admin / 见 .env |
| Redis 密码 | redispass |

---

*本文档最后更新于 2026-06-27，适用于项目 v0.1.0 版本。*
