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

本地未设置 `DATABASE_URL` 时后端默认使用 SQLite；设置后使用 PostgreSQL。启动时仍以 SQLAlchemy `create_all()` 建表。

运行后端检查：

```bash
uv run --project . pytest -q
uv run --project . python -m compileall backend
```

运行前端检查：

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

当前前端仍使用 Mock 数据；宠物档案 API 接入属于下一阶段工作。详见 [产品核心域路线图](../roadmap/product-core-roadmap.md)。
