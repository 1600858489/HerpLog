# 快速启动

## 前置条件

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 与 npm

## 开发依赖

复制环境模板并填写 PostgreSQL 密码：

```bash
cp .env.example .env
```

在 `.env` 中设置以下值：

```dotenv
POSTGRES_USER=herplog
POSTGRES_PASSWORD=replace-with-a-local-secret
POSTGRES_DB=herplog
DATABASE_URL=postgresql+asyncpg://herplog:replace-with-a-local-secret@127.0.0.1:5432/herplog
REDIS_URL=redis://127.0.0.1:6379/0
```

启动 PostgreSQL 与 Redis：

```bash
docker compose --env-file .env -f docker/compose.yaml --profile dev up -d --wait
```

停止依赖服务但保留数据卷：

```bash
docker compose --env-file .env -f docker/compose.yaml --profile dev down
```

后端只支持 PostgreSQL。数据库结构由 Alembic 管理；Redis 仅在应用启动时初始化连接并验证可用性，当前没有业务读写 Redis，Redis 不可用不阻止后端启动。

## 数据库迁移

执行迁移（应用或更新数据库结构，启动后端前必须处于最新状态）：

```bash
uv run --project . alembic upgrade head
```

`./start-backend.sh` 会在启动 Uvicorn 前自动执行上述迁移。

查看当前迁移状态：

```bash
uv run --project . alembic current
```

修改 ORM 模型后生成新的迁移脚本：

```bash
uv run --project . alembic revision --autogenerate -m "描述本次变更"
```

生成后检查 `migrations/versions/` 中新生成的脚本内容，确认无误后再执行 `alembic upgrade head` 应用。

## 本地前后端

一键后台启动前后端，日志分别写入 `tmp/backend.log` 与 `tmp/frontend.log`：

```bash
./start.sh
./start.sh --stop
```

或者在两个终端以前台方式分别启动：

```bash
./start-backend.sh
./start-frontend.sh
```

前台进程使用 Ctrl+C 停止。

可访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:5173
```

本地后端通过 `.env` 中的 `DATABASE_URL` 连接 PostgreSQL，`DATABASE_URL` 必须使用 `postgresql+asyncpg://`。表结构只通过 Alembic 迁移创建，不再依赖运行时建表。

运行后端检查（使用独立测试库 `herplog_test`，避免写入开发数据）：

```bash
docker exec docker-postgres-dev-1 createdb -U "$POSTGRES_USER" herplog_test 2>/dev/null || true
set -a; . ./.env; set +a
export DATABASE_URL="$TEST_DATABASE_URL"
uv run --project . alembic upgrade head
uv run --project . pytest -q
uv run --project . python -m compileall backend migrations
```

运行前端检查：

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

当前前端仍使用 Mock 数据；宠物档案 API 接入属于下一阶段工作。详见 [产品核心域路线图](../roadmap/product-core-roadmap.md)。
