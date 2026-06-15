# ==================================
# Git Flow 工作流规范
# ==================================

---

## 一、分支模型总览

```
main       ──●────────────●──────────────●──────── 生产版本
              │\          │\            │\
release    ─── │ \──●────  │ \──●─────   │ \──●──   发布候选
              │  \    \    │  \    \     │  \
develop    ──●───●──●─●───●───●──●─●────●───●───  开发主线
                 │\   \       │\   \         │\
feature/*  ───── │ \──●      │ \──●        │ \──●  功能分支
                 │            │             │
hotfix/*   ────── ●───────────●─────────────●─────  紧急修复
```

**核心原则**: `main` 只存生产代码；`develop` 是集成分支；所有新功能从 `develop` 拉分支，通过 PR 合并回去。

---

## 二、分支命名规范

### Feature 分支
```
feature/<模块>-<简短描述>
```
| 示例 | 说明 |
|------|------|
| `feature/crawler-rss-engine` | 爬虫模块 RSS 引擎 |
| `feature/backend-api-auth` | 后端 API 认证 |
| `feature/frontend-dashboard-chart` | 前端仪表盘图表 |

### Bugfix 分支
```
bugfix/<问题编号>-<简短描述>
```
| 示例 | 说明 |
|------|------|
| `bugfix/42-crawler-timeout` | #42 爬虫超时问题 |
| `bugfix/dashboard-date-format` | 仪表盘日期格式 |

### Release 分支
```
release/v<major>.<minor>.<patch>
```
| 示例 | 说明 |
|------|------|
| `release/v0.1.0` | 首个内测版本 |
| `release/v1.0.0` | 正式发布版本 |

### Hotfix 分支
```
hotfix/v<version>-<简短描述>
```
| 示例 | 说明 |
|------|------|
| `hotfix/v0.1.1-db-connection-leak` | 数据库连接泄漏 |
| `hotfix/v1.0.1-celery-crash` | Celery 崩溃修复 |

---

## 三、Commit Message 规范

采用 **Conventional Commits** 格式：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type 定义

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(crawler): add RSS source parser` |
| `fix` | 修复 bug | `fix(api): correct competitor query filter` |
| `refactor` | 重构（非功能改动） | `refactor(db): extract base repository` |
| `perf` | 性能优化 | `perf(query): add index for competitor search` |
| `test` | 测试 | `test(crawler): add unit tests for parser` |
| `docs` | 文档 | `docs(readme): update deployment guide` |
| `style` | 代码风格（不影响逻辑） | `style(backend): apply ruff formatting` |
| `chore` | 构建/工具/依赖 | `chore(deps): bump fastapi to 0.115` |
| `ci` | CI/CD 配置 | `ci: add GitHub Actions workflow` |

### Scope 定义

| Scope | 对应模块 |
|-------|---------|
| `crawler` | 数据采集模块 |
| `api` | 后端 API |
| `db` | 数据库/模型 |
| `tasks` | Celery 异步任务 |
| `frontend` | 前端 Vue 页面 |
| `alerts` | 预警通知 |
| `analysis` | AI 分析 |
| `config` | 配置变更 |
| `docs` | 文档 |

### 规则

- **subject 用中文**（本次项目约定），不超过 50 字符
- **不加句号**
- **Imperative mood**（祈使句）
- **Breaking change**: 在 footer 加 `BREAKING CHANGE: 说明`

### 正确示例

```
feat(crawler): 增加竞品官网变化检测功能

支持基于页面哈希和选择器对比的方式检测官网更新，
发现变化后自动生成 market_intelligence 记录。

Closes #15
```

```
fix(db): 修复 pricing_history 外键级联删除错误

之前 ON DELETE CASCADE 在跨 schema 场景下不生效，
改为应用层先删除子记录再删除父记录。

BREAKING CHANGE: Competitor.delete() 现在需要显式处理关联数据
```

---

## 四、工作流操作 SOP

### 4.1 开始新功能

```bash
# 1. 切换到 develop 并更新
git checkout develop
git pull origin develop

# 2. 创建 feature 分支
git checkout -b feature/<module>-<short-desc>

# 3. 开发 + 频繁提交
git add .
git commit -m "feat(scope): 描述"

# 4. 推送远程（尽早 push，防止丢失）
git push -u origin feature/<module>-<short-desc>
```

### 4.2 提交 Pull Request

```bash
# 1. 确保分支已推送且与 develop 同步
git checkout develop && git pull
git checkout feature/<branch>
git rebase develop          # 推荐 rebase，保持历史干净

# 2. 解决冲突后推送
git push --force-with-lease

# 3. 在 Git 平台创建 PR：
#    base: develop  ←  compare: feature/<branch>
```

### PR 模板要求：

```
## 变更说明
[简要描述本次变更]

## 关联 Issue
Closes #XX

## 变更类型
- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 重构 (refactor)
- [ ] 文档 (docs)
- [ ] 其他

## 测试检查
- [ ] 本地 Docker Compose 测试通过
- [ ] 单元测试通过
- [ ] 数据库迁移无问题
- [ ] 无新增 lint 警告

## Review 备注
[需要 reviewer 特别关注的点]
```

### 4.3 发布流程

```bash
# 1. 从 develop 创建 release 分支
git checkout develop
git checkout -b release/v0.1.0

# 2. 在 release 分支上做发布前最后的修复（只修 bug）
#    版本号在 __init__.py / package.json 中更新

# 3. 合并到 main（打 tag）和 develop
git checkout main
git merge release/v0.1.0 --no-ff
git tag -a v0.1.0 -m "Release v0.1.0: 首个内测版本"
git push origin main --tags

git checkout develop
git merge release/v0.1.0 --no-ff
git push origin develop

# 4. 删除 release 分支
git branch -d release/v0.1.0
git push origin --delete release/v0.1.0
```

### 4.4 紧急修复

```bash
# 1. 从 main 创建 hotfix
git checkout main
git checkout -b hotfix/v0.1.1-<desc>

# 2. 修复 + 测试
git commit -m "fix(scope): 描述"

# 3. 合并到 main（打 tag）和 develop
git checkout main
git merge hotfix/v0.1.1-<desc> --no-ff
git tag -a v0.1.1 -m "Hotfix v0.1.1"
git push origin main --tags

git checkout develop
git merge hotfix/v0.1.1-<desc> --no-ff
git push origin develop

# 4. 删除 hotfix
git branch -d hotfix/v0.1.1-<desc>
```

---

## 五、分支保护规则

| 分支 | 直接 Push | PR 必需 | Review 人数 | CI 通过 |
|------|----------|---------|-------------|---------|
| `main` | ❌ 禁止 | ✅ 必须 | ≥ 1 | ✅ |
| `develop` | ❌ 禁止 | ✅ 必须 | ≥ 1 | ✅ |
| `release/*` | ❌ 禁止 | ✅ 必须 | ≥ 1 | ✅ |
| `feature/*` | ✅ 允许 | — (向 develop 提 PR) | — | — |
| `hotfix/*` | ✅ 允许 | — (向 main 提 PR) | — | — |

---

## 六、Tag 命名（语义化版本）

```
v<MAJOR>.<MINOR>.<PATCH>[-<pre-release>]

v0.1.0        # 首个功能版本
v0.2.0-alpha  # 预发布
v1.0.0-rc1    # 候选发布
v1.0.0        # 正式版本
```

Tag 打在 `main` 分支的 merge commit 上。

---

## 七、禁止事项

| 禁止 | 原因 |
|------|------|
| 直接 push 到 `main`/`develop` | 破坏代码审查流程 |
| `git push --force` 到共享分支 | 覆盖他人代码 |
| 提交 `.env` / 密钥 / 证书 | 安全风险 |
| 提交 `node_modules` / `__pycache__` | 仓库膨胀 |
| 在 feature 分支上做不相关改动 | 一次只做一件事 |
| Merge commit 满天飞（rebase 优先） | 保持历史线整洁 |
| 超大 PR（>500 行变更） | 降低 review 质量 |
