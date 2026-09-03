# 本地启动与容器化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提供后台一键本地启动、前台单服务启动，以及可通过 `dev` 和 `prod` profile 运行的 PostgreSQL、Redis 与完整生产测试栈。

**Architecture:** 根目录脚本负责本地开发进程：一键脚本把 PID 和日志写入 `tmp/`，单服务脚本保持前台。Compose 将开发依赖服务与生产测试服务拆成互不共享端口、容器名或数据卷的两组 profile；生产前端由 Nginx 托管 SPA 并同源代理 `/api/` 至 FastAPI。

**Tech Stack:** Bash、uv、FastAPI、SQLAlchemy async + asyncpg、React/Vite、Docker Compose、PostgreSQL 17、Redis 7、Nginx。

## Global Constraints

- 根目录 `start.sh` 默认后台启动两项本地服务，日志和 PID 只写入忽略的 `tmp/`。
- `start.sh --stop` 必须幂等停止一键脚本启动的服务；单服务脚本不得读写这些 PID 文件。
- `start-backend.sh`、`start-frontend.sh` 必须在前台运行，并由各自终端的 Ctrl+C 停止。
- `dev` profile 只启动 `postgres-dev` 与 `redis-dev`；`prod` profile 只启动 `postgres`、`redis`、`backend`、`frontend`。
- PostgreSQL 和 Redis 各 profile 使用独立命名卷；生产 profile 不发布数据库或 Redis 端口。
- 所有数据库初始化凭据和生产 JWT 密钥均从未提交的 `.env` 获取；Compose 文件中不得提供密码默认值。
- 保持 SQLite 为未配置 `DATABASE_URL` 时的本地后端默认值；仅添加 PostgreSQL 异步驱动，不在本次改动接入 Redis 业务功能。
- 不创建 git 提交，除非用户明确要求。

---

## 文件结构

| 文件 | 责任 |
| --- | --- |
| `.gitignore` | 忽略运行时 `tmp/`。 |
| `.env.example` | 列出必须填写的本地 PostgreSQL/Redis 与生产 JWT、HTTP 端口配置。 |
| `pyproject.toml`、`uv.lock` | 声明并锁定 `asyncpg`。 |
| `backend/tests/test_core.py` | 验证 `DATABASE_URL` 可覆盖为 PostgreSQL async URL。 |
| `start-backend.sh` | 前台安装并启动后端。 |
| `start-frontend.sh` | 前台安装并启动前端。 |
| `start.sh` | 后台协调启动、日志/PID 管理和 `--stop`。 |
| `tests/test_start_scripts.py` | 在临时模拟项目中验证脚本后台生命周期与前台接口。 |
| `docker/backend.Dockerfile` | 构建无重载的 FastAPI 运行镜像。 |
| `docker/frontend.Dockerfile` | 构建 Vite 产物并运行 Nginx。 |
| `docker/nginx.conf` | SPA history fallback 与 `/api/` 反向代理。 |
| `docker/compose.yaml` | 声明 `dev` 依赖 profile 和 `prod` 完整 profile。 |
| `docs/guides/quick-start.md` | 说明三种本地脚本、Compose profile、环境变量和停止方式。 |

### Task 1: 支持可配置的 PostgreSQL 异步连接

**Files:**
- Modify: `pyproject.toml:6-15`
- Modify: `uv.lock`
- Modify: `backend/tests/test_core.py:1-24`

**Interfaces:**
- Consumes: `Settings(database_url: str = ...)` 与 SQLAlchemy `create_async_engine(url)`。
- Produces: 安装后可加载 `postgresql+asyncpg://user:password@host:5432/database` 的异步 SQLAlchemy 引擎。

- [ ] **Step 1: 在核心测试中写出 PostgreSQL URL 覆盖测试**

在 `backend/tests/test_core.py` 的现有配置测试后添加：

```python
from sqlalchemy.ext.asyncio import create_async_engine


def test_database_url_can_be_overridden_with_postgres_asyncpg_url(monkeypatch) -> None:
    database_url = "postgresql+asyncpg://herplog:secret@localhost:5432/herplog"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()
    engine = create_async_engine(settings.database_url)

    assert settings.database_url == database_url
    assert engine.url.drivername == "postgresql+asyncpg"
    engine.sync_engine.dispose()
```

调整导入顺序，使 `create_async_engine` 位于第三方导入组，并使用 SQLAlchemy 的同步底层 `dispose()` 释放这个未连接引擎。

- [ ] **Step 2: 运行测试，确认当前缺少驱动**

Run: `uv run --project . pytest backend/tests/test_core.py::test_database_url_can_be_overridden_with_postgres_asyncpg_url -q`

Expected: FAIL，错误包含 `asyncpg` 未安装或 PostgreSQL asyncpg dialect 无法加载。

- [ ] **Step 3: 添加并锁定 asyncpg**

在 `pyproject.toml` 的 `dependencies` 中紧随 `aiosqlite` 添加：

```toml
    "asyncpg>=0.30.0",
```

运行：

```bash
uv lock
uv sync --locked
```

保留 `uv.lock` 由该命令生成的精确解析结果，不手工编辑锁文件。

- [ ] **Step 4: 重新运行核心测试与完整后端测试**

Run: `uv run --project . pytest backend/tests/test_core.py::test_database_url_can_be_overridden_with_postgres_asyncpg_url -q && uv run --project . pytest -q`

Expected: 两个命令均 PASS；现有 SQLite 测试保持可用。

### Task 2: 实现本地前台与后台启动脚本

**Files:**
- Create: `start-backend.sh`
- Create: `start-frontend.sh`
- Create: `start.sh`
- Create: `tests/test_start_scripts.py`
- Modify: `.gitignore:35-38`

**Interfaces:**
- Consumes: 项目根目录的 `.venv/`、`frontend/node_modules/`、可执行的 `uv` 与 `npm`，可选根目录 `.env`。
- Produces: `./start-backend.sh`、`./start-frontend.sh`、`./start.sh` 和 `./start.sh --stop`；后台状态文件为 `tmp/backend.pid`、`tmp/frontend.pid`、`tmp/backend.log`、`tmp/frontend.log`。

- [ ] **Step 1: 先添加脚本行为测试**

创建 `tests/test_start_scripts.py`，通过临时目录模拟项目根目录、假 `uv` 与假 `npm`，不启动真实服务。测试必须覆盖：

```python
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def create_fake_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "backend").mkdir(parents=True)
    (project / "frontend" / "node_modules").mkdir(parents=True)
    (project / ".venv").mkdir()
    for script_name in ("start.sh", "start-backend.sh", "start-frontend.sh"):
        (project / script_name).write_text((PROJECT_ROOT / script_name).read_text())
        (project / script_name).chmod(0o755)
    return project


def test_start_script_writes_pid_and_log_files_then_stops_services(tmp_path: Path) -> None:
    project = create_fake_project(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_executable(bin_dir / "uv", "#!/usr/bin/env bash\nexec sleep 600\n")
    write_executable(bin_dir / "npm", "#!/usr/bin/env bash\nif [ \"$1\" = \"run\" ]; then exec sleep 600; fi\n")
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}

    started = subprocess.run([str(project / "start.sh")], cwd=project, env=env, text=True, capture_output=True)
    assert started.returncode == 0, started.stderr
    assert (project / "tmp/backend.pid").is_file()
    assert (project / "tmp/frontend.pid").is_file()
    assert (project / "tmp/backend.log").is_file()
    assert (project / "tmp/frontend.log").is_file()

    stopped = subprocess.run([str(project / "start.sh"), "--stop"], cwd=project, env=env, text=True, capture_output=True)
    assert stopped.returncode == 0, stopped.stderr
    assert not (project / "tmp/backend.pid").exists()
    assert not (project / "tmp/frontend.pid").exists()
```

再补充两个参数化测试：以相同 fake PATH 运行每个单服务脚本并传入不支持的参数，断言返回非零并包含 `Usage:`；这确保它们不会意外实现后台/PID 控制接口。

- [ ] **Step 2: 运行测试确认脚本尚不存在**

Run: `uv run --project . pytest tests/test_start_scripts.py -q`

Expected: FAIL，错误包含无法读取根目录 `start.sh`、`start-backend.sh` 或 `start-frontend.sh`。

- [ ] **Step 3: 添加忽略规则及前台单服务脚本**

在 `.gitignore` 的 FastAPI/Uvicorn 本地文件段落添加：

```gitignore
tmp/
```

创建 `start-backend.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install uv before starting the backend.\n' >&2
  exit 1
fi

if [[ ! -d "$root_dir/.venv" ]]; then
  (cd "$root_dir" && uv sync)
fi

env_file_args=()
if [[ -f "$root_dir/.env" ]]; then
  env_file_args=(--env-file "$root_dir/.env")
fi

cd "$root_dir/backend"
exec uv run --project "$root_dir" uvicorn main:app --host 127.0.0.1 --port 8000 --reload "${env_file_args[@]}"
```

创建 `start-frontend.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'npm is required. Install Node.js and npm before starting the frontend.\n' >&2
  exit 1
fi

if [[ ! -d "$root_dir/frontend/node_modules" ]]; then
  (cd "$root_dir/frontend" && npm install)
fi

cd "$root_dir/frontend"
exec npm run dev
```

- [ ] **Step 4: 添加后台一键脚本**

创建 `start.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp_dir="$root_dir/tmp"
backend_pid_file="$tmp_dir/backend.pid"
frontend_pid_file="$tmp_dir/frontend.pid"
backend_log_file="$tmp_dir/backend.log"
frontend_log_file="$tmp_dir/frontend.log"

usage() {
  printf 'Usage: %s [--stop]\n' "$0" >&2
}

is_running() {
  [[ -f "$1" ]] && kill -0 "$(<"$1")" 2>/dev/null
}

stop_service() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    printf '%s is not running.\n' "$name"
    return
  fi

  local pid
  pid="$(<"$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    wait "$pid" 2>/dev/null || true
    printf 'Stopped %s (PID %s).\n' "$name" "$pid"
  else
    printf '%s PID file was stale.\n' "$name"
  fi
  rm -f "$pid_file"
}

if [[ $# -eq 1 && "$1" == "--stop" ]]; then
  stop_service backend "$backend_pid_file"
  stop_service frontend "$frontend_pid_file"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  usage
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install uv before starting the backend.\n' >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  printf 'npm is required. Install Node.js and npm before starting the frontend.\n' >&2
  exit 1
fi

mkdir -p "$tmp_dir"
if is_running "$backend_pid_file" || is_running "$frontend_pid_file"; then
  printf 'HerpLog is already running. Run %s --stop first.\n' "$0" >&2
  exit 1
fi
rm -f "$backend_pid_file" "$frontend_pid_file"

if [[ ! -d "$root_dir/.venv" ]]; then
  (cd "$root_dir" && uv sync)
fi
if [[ ! -d "$root_dir/frontend/node_modules" ]]; then
  (cd "$root_dir/frontend" && npm install)
fi

env_file_args=()
if [[ -f "$root_dir/.env" ]]; then
  env_file_args=(--env-file "$root_dir/.env")
fi

(
  cd "$root_dir/backend"
  exec uv run --project "$root_dir" uvicorn main:app --host 127.0.0.1 --port 8000 --reload "${env_file_args[@]}"
) >"$backend_log_file" 2>&1 &
printf '%s\n' "$!" >"$backend_pid_file"

(
  cd "$root_dir/frontend"
  exec npm run dev
) >"$frontend_log_file" 2>&1 &
printf '%s\n' "$!" >"$frontend_pid_file"

printf 'Backend started (PID %s): %s\n' "$(<"$backend_pid_file")" "$backend_log_file"
printf 'Frontend started (PID %s): %s\n' "$(<"$frontend_pid_file")" "$frontend_log_file"
```

使三个脚本可执行：

```bash
chmod +x start.sh start-backend.sh start-frontend.sh
```

- [ ] **Step 5: 运行脚本单元测试和语法检查**

Run: `uv run --project . pytest tests/test_start_scripts.py -q && bash -n start.sh start-backend.sh start-frontend.sh`

Expected: PASS；所有三份脚本无语法错误。

- [ ] **Step 6: 用真实本地开发进程做人工冒烟测试**

Run: `./start.sh && curl --fail http://127.0.0.1:8000/health && curl --fail http://127.0.0.1:5173/ && ./start.sh --stop && ./start.sh --stop`

Expected: 两个 HTTP 请求成功；第一次停止输出两个服务已停止，第二次输出两个服务未运行；`tmp/backend.pid` 与 `tmp/frontend.pid` 不存在，日志文件保留。

### Task 3: 添加生产镜像、Nginx 和 profile 化 Compose

**Files:**
- Create: `docker/backend.Dockerfile`
- Create: `docker/frontend.Dockerfile`
- Create: `docker/nginx.conf`
- Create: `docker/compose.yaml`
- Create: `.env.example`

**Interfaces:**
- Consumes: 根目录构建上下文、`pyproject.toml`、`uv.lock`、`backend/`、`frontend/package-lock.json` 与 `.env` 变量。
- Produces: `docker compose --env-file .env -f docker/compose.yaml --profile dev up -d` 和 `--profile prod up --build -d` 命令。

- [ ] **Step 1: 编写失败前的 Compose 配置验证命令**

在填充 `.env` 前，创建本地未跟踪 `.env`（禁止提交）并至少设置：

```dotenv
POSTGRES_USER=herplog
POSTGRES_PASSWORD=replace-with-a-local-secret
POSTGRES_DB=herplog
DATABASE_URL=postgresql+asyncpg://herplog:replace-with-a-local-secret@127.0.0.1:5432/herplog
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET_KEY=replace-with-a-long-random-local-secret
APP_PORT=8080
```

Run: `docker compose --env-file .env -f docker/compose.yaml --profile dev config`

Expected: FAIL，因为 `docker/compose.yaml` 尚不存在。

- [ ] **Step 2: 编写后端生产镜像**

创建 `docker/backend.Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend ./backend

WORKDIR /app/backend
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

该镜像只通过 Compose 环境变量接收生产数据库、Redis 和 JWT 配置，不复制 `.env`。

- [ ] **Step 3: 编写前端生产镜像与 Nginx 配置**

创建 `docker/frontend.Dockerfile`：

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
```

创建 `docker/nginx.conf`：

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 4: 编写 Compose services、profile、卷和健康检查**

创建 `docker/compose.yaml`：

```yaml
services:
  postgres-dev:
    image: postgres:17-alpine
    profiles: [dev]
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?set POSTGRES_USER in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
      POSTGRES_DB: ${POSTGRES_DB:?set POSTGRES_DB in .env}
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis-dev:
    image: redis:7-alpine
    profiles: [dev]
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  postgres:
    image: postgres:17-alpine
    profiles: [prod]
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?set POSTGRES_USER in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
      POSTGRES_DB: ${POSTGRES_DB:?set POSTGRES_DB in .env}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    profiles: [prod]
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    image: herplog-backend:local
    profiles: [prod]
    build:
      context: ..
      dockerfile: docker/backend.Dockerfile
    environment:
      ENVIRONMENT: production
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?set JWT_SECRET_KEY in .env}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    image: herplog-frontend:local
    profiles: [prod]
    build:
      context: ..
      dockerfile: docker/frontend.Dockerfile
    ports:
      - "${APP_PORT:?set APP_PORT in .env}:80"
    depends_on:
      backend:
        condition: service_started

volumes:
  postgres_dev_data:
  redis_dev_data:
  postgres_data:
  redis_data:
```

- [ ] **Step 5: 添加可复制的环境模板**

创建 `.env.example`：

```dotenv
# Docker PostgreSQL initialization; choose a non-default password in .env.
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# Used by locally started backend scripts after `--profile dev` publishes ports.
DATABASE_URL=
REDIS_URL=redis://127.0.0.1:6379/0

# Required only by the production test profile.
JWT_SECRET_KEY=
APP_PORT=8080
```

- [ ] **Step 6: 验证 Compose 结构和镜像构建**

Run:

```bash
docker compose --env-file .env -f docker/compose.yaml --profile dev config
docker compose --env-file .env -f docker/compose.yaml --profile prod config
docker compose --env-file .env -f docker/compose.yaml --profile prod build
```

Expected: 三条命令均成功；`dev config` 只列出 `postgres-dev`、`redis-dev`，`prod config` 只列出 `postgres`、`redis`、`backend`、`frontend`。

- [ ] **Step 7: 做 profile 与反向代理集成验证**

Run:

```bash
docker compose --env-file .env -f docker/compose.yaml --profile dev up -d
docker compose --env-file .env -f docker/compose.yaml --profile dev ps
docker compose --env-file .env -f docker/compose.yaml --profile dev down
docker compose --env-file .env -f docker/compose.yaml --profile prod up --build -d
curl --fail http://127.0.0.1:${APP_PORT}/
curl --fail http://127.0.0.1:${APP_PORT}/api/v1/pets
docker compose --env-file .env -f docker/compose.yaml --profile prod down
docker compose --env-file .env -f docker/compose.yaml --profile prod up -d
docker compose --env-file .env -f docker/compose.yaml --profile prod down
```

Expected: `dev ps` 只有两个 `*-dev` 服务；生产首页返回 200，`/api/v1/pets` 到达后端（即使未授权也不得为 Nginx 502/404）；两次 `prod up` 都复用 `postgres_data`、`redis_data` 命名卷。

### Task 4: 更新项目启动文档并跑完整验证

**Files:**
- Modify: `docs/guides/quick-start.md:1-64`

**Interfaces:**
- Consumes: 三个启动脚本、`.env.example`、Compose profile 命令和实际服务地址。
- Produces: 可由新开发者直接执行的本地开发与生产测试运行说明。

- [ ] **Step 1: 在快速启动文档中写入使用验收清单**

在 `docs/guides/quick-start.md` 添加以下可验证内容：

```markdown
## 本地前后端启动

复制 `.env.example` 为 `.env`，填写 `POSTGRES_*`、`DATABASE_URL` 和生产用 `JWT_SECRET_KEY`。先启动本地依赖：

```bash
docker compose --env-file .env -f docker/compose.yaml --profile dev up -d
```

后台启动前后端：

```bash
./start.sh
# 日志：tmp/backend.log、tmp/frontend.log
./start.sh --stop
```

或者在两个终端分别前台启动：

```bash
./start-backend.sh
./start-frontend.sh
```

## 生产测试栈

```bash
docker compose --env-file .env -f docker/compose.yaml --profile prod up --build -d
```

访问 `http://127.0.0.1:${APP_PORT}`。生产测试栈仅发布前端 HTTP 端口；PostgreSQL 和 Redis 数据保存在命名卷中。停止容器但保留数据：

```bash
docker compose --env-file .env -f docker/compose.yaml --profile prod down
```
```

同时保留原有服务地址、检查命令及“前端仍使用 Mock 数据”的事实说明；将“正式迁移与 PostgreSQL 适配尚未实现”的旧描述替换为“本地默认 SQLite，Compose 通过 `DATABASE_URL` 使用 PostgreSQL；数据库建表仍由现有 `create_all()` 完成”。

- [ ] **Step 2: 运行后端、前端和脚本完整检查**

Run:

```bash
uv run --project . pytest -q
cd frontend && npm run typecheck && npm test && npm run build
cd .. && bash -n start.sh start-backend.sh start-frontend.sh
```

Expected: 所有测试、类型检查、构建和 Shell 语法检查均 PASS。

- [ ] **Step 3: 审阅最终变更范围**

Run: `git diff --check && git status --short`

Expected: 无空白错误；变更仅包含本计划列出的启动脚本、配置/依赖、容器文件、测试、忽略规则和快速启动文档；`.env` 与 `tmp/` 未被跟踪。
