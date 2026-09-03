# 本地启动与容器化设计

## 目标

提供两种互不冲突的运行方式：

- 根目录 `start.sh` 用于本地前后端开发，自动安装缺失依赖并并发运行服务。
- `docker/compose.yaml` 用于容器化依赖服务或完整生产测试栈，通过 Compose profile 区分模式。

本次接入 PostgreSQL 与 Redis 容器作为开发和测试基础设施。Redis 只初始化连接池并验证可用性，不承载当前业务、缓存、限流或认证状态；Redis 不可用时不阻止后端启动。

## 本地启动脚本

新增根目录 `start.sh`、`start-backend.sh` 与 `start-frontend.sh`。三个脚本均以自身位置作为项目根目录，避免从不同工作目录调用时失败。

### 一键脚本

`start.sh` 默认在后台启动前后端，必须：

1. 检查 `uv` 和 `npm` 是否可用；缺失时明确报错并退出，不尝试安装系统级工具。
2. 后端虚拟环境不存在时，在项目根目录执行 `uv sync`；前端依赖目录不存在时，在 `frontend/` 执行 `npm install`。
3. 创建根目录 `tmp/`（该目录不提交），从 `backend/` 启动绑定 `127.0.0.1:8000` 且启用重载的 Uvicorn，并从 `frontend/` 启动现有配置绑定 `127.0.0.1:5173` 的 Vite。
4. 将后端和前端的标准输出、标准错误分别写入 `tmp/backend.log` 与 `tmp/frontend.log`；将对应 PID 分别写入 `tmp/backend.pid` 与 `tmp/frontend.pid`。
5. 启动成功后立即退出，保留两个服务在后台运行。
6. 接受唯一的 `--stop` 参数：读取 PID 文件，终止仍在运行的后端和前端进程，等待其回收，并删除 PID 文件；服务已停止或 PID 文件不存在时保持幂等并给出明确提示。
7. 拒绝其他参数并输出用法。再次执行默认启动时，如果已有对应 PID 且进程仍运行，则不重复启动并退出报错；失效 PID 文件必须先清理后再启动。

### 单服务脚本

- `start-backend.sh` 仅执行后端的工具检查、依赖安装和 Uvicorn 启动。
- `start-frontend.sh` 仅执行前端的工具检查、依赖安装和 Vite 启动。
- 两个脚本都不将服务转入后台：开发者在两个独立终端分别执行它们，服务日志保留在各自的前台终端，并由 Ctrl+C 停止。
- 单服务脚本不读取、写入或停止一键脚本的 PID 文件，避免影响后台运行的服务。

三个脚本都不启动 PostgreSQL 或 Redis。开发者需先执行 Compose 的 `dev` profile，再运行任一启动方式。

## 后端容器

新增 `docker/backend.Dockerfile`，从项目根目录作为构建上下文构建。

- 使用与 `pyproject.toml` 兼容的 Python 基础镜像。
- 安装项目运行依赖，不复制或依赖本地虚拟环境。
- 后端工作目录为 `/app/backend`，以项目现有 `main:app` 入口启动 Uvicorn。
- 服务监听容器内 `8000`，不启用开发重载。
- 后端数据库连接由环境变量提供，使用 PostgreSQL 异步驱动；现有 SQLAlchemy 异步实现保持不变。

配置层要求通过环境变量提供 PostgreSQL `postgresql+asyncpg://` 连接字符串，开发和测试均不再支持 SQLite。依赖清单移除 `aiosqlite` 并保留 PostgreSQL 异步驱动 `asyncpg`。后端通过 Alembic 管理数据库结构，启动时不执行 `create_all()`。首次部署和测试环境初始化前执行 `alembic upgrade head`。数据库引擎显式配置 `pool_size`、`max_overflow`、`pool_timeout`、`pool_recycle` 与 `pool_pre_ping`，应用关闭时调用 `engine.dispose()`。前端本地和生产 profile 继续通过各自的环境配置访问后端。 

## 前端容器与反向代理

新增 `docker/frontend.Dockerfile`，采用多阶段构建：

1. Node 构建阶段安装锁定的前端依赖并执行 Vite 生产构建。
2. Nginx 运行阶段只复制构建产物和 Nginx 配置。

Nginx：

- 对单页应用回退到 `index.html`。
- 将 `/api/` 请求反向代理到 Compose 内部的后端服务。
- 对外监听容器内 `80`。

浏览器请求同源 `/api`，因此前端不需要构建时的 API 地址变量，也不会将容器内部主机名暴露给浏览器。

## Compose

新增 `docker/compose.yaml`，应可从仓库根目录通过 `docker compose --env-file .env -f docker/compose.yaml` 运行。

### 开发依赖服务

`postgres-dev` 与 `redis-dev` 仅属于 `dev` profile：

- PostgreSQL 使用官方镜像，凭 `.env` 的 `POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB` 初始化，并提供健康检查。
- Redis 使用官方镜像。
- 两者分别使用开发专属命名卷持久化数据。
- PostgreSQL 的 `5432` 和 Redis 的 `6379` 发布给宿主机，供本地运行的后端连接。

### 开发 profile

`docker compose --env-file .env -f docker/compose.yaml --profile dev up -d` 只创建 `postgres-dev` 和 `redis-dev`。前后端不在 Compose 中运行，开发者执行 `./start.sh` 启动它们。

本地后端通过 `.env` 中的 `DATABASE_URL` 和 `REDIS_URL` 分别连接 `localhost:5432` 与 `localhost:6379`。

### 生产测试服务与 profile

`postgres`、`redis`、`backend` 和 `frontend` 仅属于 `prod` profile。`postgres` 与 `redis` 使用不同于开发 profile 的生产测试专属命名卷，且不向宿主机发布端口。

`docker compose --env-file .env -f docker/compose.yaml --profile prod up --build -d` 启动完整四服务栈：

- 后端由 Compose 覆盖 `DATABASE_URL` 与 `REDIS_URL`，分别连接服务名 `postgres` 和 `redis`。
- 后端依赖 PostgreSQL 健康检查通过后启动。
- 前端依赖后端启动，并将宿主机 HTTP 端口发布到前端 Nginx。
- 只有前端 HTTP 服务向宿主机发布应用访问端口。

Compose 文件中的镜像标签、端口和卷名称固定且显式。所有机密或初始化值来自 `.env`，不得提供弱默认密码。

## 数据库迁移与连接池

### PostgreSQL

- Alembic 使用现有 SQLAlchemy `Base.metadata` 自动生成初始 revision，并通过 `alembic upgrade head` 执行迁移。
- 应用 lifespan 不负责建表；数据库结构变更只通过 Alembic 管理。
- 每个后端进程持有一个 SQLAlchemy async engine 和连接池；连接池容量由环境变量配置，默认值适用于单进程开发环境。
- 请求通过 `async_sessionmaker` 获取短生命周期的请求级 `AsyncSession`，请求结束后释放回连接池。
- 应用 shutdown 调用 `engine.dispose()`，避免 reload、测试和优雅停机时遗留连接。

### Redis

- 使用 `redis.asyncio.Redis.from_url()` 创建进程级 Redis client；client 内部持有连接池，不为每个请求创建连接。
- Redis client 在 FastAPI lifespan 初始化，并执行一次 `PING`；初始化失败只记录日志，不影响后端启动，因为当前没有 Redis 强依赖业务。
- 应用 shutdown 调用 `Redis.aclose()`，释放 Redis 连接池。
- 业务层暂不读取 Redis；后续缓存、限流或 Token 黑名单接入时，统一复用该 client，并通过依赖或基础设施接口访问。
- Redis 连接池的最大连接数、连接超时、操作超时和健康检查间隔通过配置提供。

## 测试环境

- 测试使用已启动的 PostgreSQL 开发容器，但通过独立测试数据库或 schema 与开发数据隔离，不再创建 SQLite 内存数据库。
- 测试开始前执行 Alembic migration，测试结束清理测试数据。连接池、engine 和 session 生命周期独立于开发进程。 
- 测试 fixture 创建独立的 SQLAlchemy engine/session，并在结束时 `dispose()`。
- Redis 测试使用已启动的 Redis 容器；为测试 key 使用专用前缀，测试结束清理自身 key，不执行全库清空。
- 默认业务测试即使当前不调用 Redis，也验证 Redis 基础设施可以初始化和关闭；Redis 故障场景验证后端仍可启动。

## 环境文件

新增 `.env.example`，包含无敏感值的必填变量：

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`，指向开发 profile 发布到宿主机的 PostgreSQL
- `REDIS_URL`，指向开发 profile 发布到宿主机的 Redis
- `JWT_SECRET_KEY`，供生产测试 profile 启动后端使用，且不得为开发默认值
- `APP_PORT`，供生产测试 profile 发布前端 HTTP 服务端口

`.env` 保持忽略，不提交真实凭据。README 明确要求复制 `.env.example` 为 `.env` 后填写数据库密码。

## 文档

README 增加：

- 一键与分别前台启动方式、自动依赖安装和服务地址。
- `dev` profile 启动依赖服务的命令。
- 本地应用连接该依赖服务所需的 `.env` 配置。
- `prod` profile 构建并启动全量服务的命令与访问地址。
- `start.sh --stop`、后台日志路径与命名卷会保留数据库和 Redis 数据的说明。

## 验证

实施完成后验证：

1. 三个脚本均通过 Shell 语法检查；一键脚本在后台启动两个服务，分别产生日志与 PID 文件，`--stop` 幂等停止两项服务；两个单服务脚本分别以前台启动对应服务，并由各自 Ctrl+C 停止。
2. 后端依赖解析和测试通过，且 PostgreSQL URL 可被配置加载。
3. 前端类型检查、测试和生产构建通过。
4. Compose 配置插值及 profile 解析通过。
5. `dev` profile 只创建 PostgreSQL 和 Redis；`prod` profile 构建并启动完整四服务栈。
6. 生产前端页面与 `/api` 反向代理均可访问，重启容器后 PostgreSQL 与 Redis 数据卷仍被复用。
