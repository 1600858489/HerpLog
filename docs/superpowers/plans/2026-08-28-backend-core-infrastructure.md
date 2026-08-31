# 后端核心基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 HerpLog 后端可复用的 FastAPI 核心基础设施，使后续认证、宠物、事件和文件业务都在统一的异步数据库、响应、错误、鉴权和基础设施抽象上实现。

**Architecture:** 使用横向分层结构。`views` 只处理 HTTP，`core` 定义应用协议和安全机制，`models` 提供 ORM 基类与公共 Mixin，`selectors`/`services` 留给后续业务域；数据库通过异步 `AsyncSession` 显式注入，所有关系默认 `lazy="raise"`。开发阶段使用 SQLite + `aiosqlite` 和本地文件存储，Redis/S3/Celery 只落抽象接口与配置边界，不提前实现生产适配器。

**Tech Stack:** Python 3.12+, FastAPI 0.115+, SQLAlchemy 2.0 async ORM, aiosqlite, Pydantic v2, pydantic-settings, PyJWT, bcrypt, pytest, pytest-asyncio, httpx.

## Global Constraints

- 后端使用 FastAPI；数据库使用 SQLAlchemy 2.0 `AsyncSession`，开发驱动为 `aiosqlite`，生产驱动预留 `asyncpg`。
- 当前使用 SQLite `create_all()`，不创建 Alembic 或其他迁移文件。
- 所有业务模型继承 `IDMixin`、`TimestampMixin`、`SoftDeleteMixin`；内部使用自增 `id`，对外只使用唯一 `uuid`。
- 所有 `relationship()` 必须设置 `lazy="raise"`；查询必须通过显式 `selectinload()`/`joinedload()` 预加载关联。
- API 请求/响应统一使用 snake_case；响应 Schema 不暴露 `id`，请求 Schema 不接受 `id`/`uuid` 可写字段。
- 所有请求 Schema 继承 `BaseRequestSchema`，`extra="forbid"`；预期业务错误通过业务逻辑抛出，不用 `try/except` 过滤。
- 业务错误统一由 `BusinessError` 表达，由全局 handler 转为自然语言 envelope；不得向前端透出 Python 异常文本或 traceback。
- HTTP status 与业务 `code` 分离；业务 code 按千位分域、百位分子资源、十位/个位分错误类型。
- 所有列表接口后续必须使用统一 `PaginationParams` 与分页响应结构；本计划只实现通用组件，不实现业务列表接口。
- 外部资源适配统一放在 `infra/`；`utils/` 仅放无状态、无业务语义的通用函数。
- 不修改前端，不删除现有前端 Mock 测试；前端替换为 API 后另行调整测试。

---

## 文件结构映射

本计划结束时新增或修改以下文件。每个文件只承担一个明确职责：

- Modify: `pyproject.toml` — 增加后端运行依赖和测试开发依赖。
- Modify: `backend/main.py` — 创建 FastAPI 应用、注册中间件和异常处理、提供 envelope 格式的健康检查。
- Modify: `backend/app/__init__.py` — 导出应用包公共对象（如有必要），保持包入口轻量。
- Create: `backend/app/core/config.py` — Pydantic Settings 配置与环境变量边界。
- Create: `backend/app/core/constants.py` — 应用级常量、文件类型/大小和分页默认值。
- Create: `backend/app/core/errors.py` — 业务错误码、错误元数据和 `BusinessError`。
- Create: `backend/app/core/response.py` — 成功/错误 envelope 的 Pydantic 响应结构和构造函数。
- Create: `backend/app/core/pagination.py` — 分页请求依赖、分页结果结构和通用封装函数。
- Create: `backend/app/core/security/password.py` — bcrypt 密码哈希和校验。
- Create: `backend/app/core/security/jwt.py` — Access Token 的签发和验证。
- Create: `backend/app/core/security/token.py` — Refresh Token 的随机值生成与哈希工具；数据库撤销由后续认证 Service 负责。
- Create: `backend/app/core/security/__init__.py` — 统一导出安全模块公共接口。
- Create: `backend/app/models/base.py` — SQLAlchemy Declarative Base、公共 Mixin 和 metadata 导出。
- Create: `backend/app/infra/database.py` — 异步 Engine、`async_sessionmaker`、请求级 Session 依赖和建表初始化函数。
- Create: `backend/app/infra/cache/base.py` — CacheClient 抽象协议。
- Create: `backend/app/infra/storage/base.py` — FileStorage 抽象协议及文件元数据结构。
- Create: `backend/app/infra/tasks/celery.py` — Celery 配置边界占位，不初始化生产任务逻辑。
- Create: `backend/app/infra/tasks/base.py` — 任务基类边界占位。
- Create: `backend/app/middlewares/exception.py` — FastAPI 全局异常处理器注册。
- Create: `backend/app/middlewares/cors.py` — CORS 配置注册。
- Create: `backend/app/middlewares/logging.py` — 请求日志中间件，只记录请求元数据和耗时，不记录敏感信息。
- Create: `backend/app/middlewares/rate_limit.py` — 限流中间件接口边界；本计划不执行 Redis 限流。
- Create: `backend/app/middlewares/__init__.py` — 统一导出中间件注册函数。
- Create: `backend/app/utils/datetime.py` — 时区明确的日期时间工具。
- Create: `backend/app/utils/uuid.py` — UUID 生成工具。
- Create: `backend/app/utils/string.py` — 无业务语义的字符串规范化工具。
- Create: `backend/tests/test_core.py` — 错误、响应、分页、安全和工具测试。
- Create: `backend/tests/test_database.py` — SQLite 异步数据库和 Mixin 行为测试。
- Create: `backend/tests/test_app.py` — FastAPI 健康检查、校验错误和未预期异常响应测试。
- Create: `backend/tests/conftest.py` — 测试应用、异步 Session 和 HTTP 客户端 fixture。

---

### Task 1: 配置依赖与测试基础

**Files:**
- Modify: `pyproject.toml`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces `Settings` 所需依赖和可运行的 pytest/pytest-asyncio 测试环境。
- 后续任务使用 `pytest`、`pytest_asyncio`、`httpx.AsyncClient`，不在业务代码中自行创建测试数据库。

- [ ] **Step 1: Write the failing test**

先创建最小测试，验证测试运行器已经可用：

```python
# backend/tests/test_core.py

def test_test_runner_is_configured() -> None:
    assert True
```

- [ ] **Step 2: Run test to verify it fails for the expected environment reason**

Run: `uv run pytest backend/tests/test_core.py::test_test_runner_is_configured -q`

Expected before依赖安装: 命令可能因 `pytest` 未安装失败；不得通过修改测试绕过依赖问题。

- [ ] **Step 3: Add exact dependencies and pytest configuration**

在 `pyproject.toml` 中保留现有 FastAPI/uvicorn 依赖，并增加：

```toml
"SQLAlchemy>=2.0.0",
"aiosqlite>=0.20.0",
"pydantic-settings>=2.0.0",
"PyJWT>=2.8.0",
"bcrypt>=4.0.0",
```

增加开发依赖：

```toml
[dependency-groups]
dev = [
    "httpx>=0.27.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
testpaths = ["backend/tests"]
```

使用 `uv lock` 更新锁文件，不能手写锁文件内容。

- [ ] **Step 4: Add shared test fixtures**

`backend/tests/conftest.py` 先提供后续测试使用的异步客户端 fixture 约定；在应用尚未完成前，只保留 fixture 工厂，不引用不存在的业务模型。最终 fixture 必须使用：

```python
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_core.py::test_test_runner_is_configured -q`

Expected: `1 passed`。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock backend/tests/test_core.py backend/tests/conftest.py
git commit -m "build: configure async backend test dependencies"
```

---

### Task 2: 应用配置、常量和纯工具

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/constants.py`
- Create: `backend/app/utils/datetime.py`
- Create: `backend/app/utils/uuid.py`
- Create: `backend/app/utils/string.py`
- Modify: `backend/tests/test_core.py`

**Interfaces:**
- Produces `get_settings() -> Settings`。
- `Settings` 至少提供 `app_name`、`environment`、`database_url`、`jwt_secret_key`、`jwt_algorithm`、`access_token_expire_minutes`、`refresh_token_expire_days`、`upload_dir`、`allowed_origins`。
- Produces `generate_uuid() -> UUID`、`utc_now() -> datetime`、`normalize_optional_text(value: str | None) -> str | None`。
- 所有生产敏感配置只从环境变量读取；测试通过 `Settings` 构造或环境变量注入，不在仓库提交真实密钥。

- [ ] **Step 1: Write the failing tests**

```python
from datetime import timezone
from uuid import UUID

from backend.app.utils.datetime import utc_now
from backend.app.utils.string import normalize_optional_text
from backend.app.utils.uuid import generate_uuid


def test_generate_uuid_returns_uuid() -> None:
    assert isinstance(generate_uuid(), UUID)


def test_utc_now_is_timezone_aware() -> None:
    assert utc_now().tzinfo == timezone.utc


def test_normalize_optional_text_trims_and_converts_blank_to_none() -> None:
    assert normalize_optional_text("  gecko  ") == "gecko"
    assert normalize_optional_text("   ") is None
    assert normalize_optional_text(None) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: FAIL with import errors because the utility modules do not exist。

- [ ] **Step 3: Implement configuration and constants**

`Settings` 使用 `pydantic_settings.BaseSettings`，默认开发数据库 URL 为 `sqlite+aiosqlite:///./herplog.db`，默认环境为 `development`，JWT 密钥默认值只允许测试/开发使用且生产启动时必须通过配置校验拒绝不安全默认值。常量集中定义 `DEFAULT_PAGE=1`、`DEFAULT_PAGE_SIZE=20`、`MAX_PAGE_SIZE=100`、`MAX_UPLOAD_SIZE=10 * 1024 * 1024` 和三个允许图片 MIME 类型。

`get_settings()` 使用 `@lru_cache`，避免每次依赖注入重复读取环境变量。

- [ ] **Step 4: Implement utilities**

`utc_now()` 必须返回 UTC aware datetime；`generate_uuid()` 使用 `uuid4()`；字符串工具只做 trim/空值归一化，不引入业务判断。

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: `4 passed` 或更多（含原始 runner 测试）。

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/config.py backend/app/core/constants.py backend/app/utils backend/tests/test_core.py
 git commit -m "feat: add backend configuration and utility foundations"
```

---

### Task 3: 数据库 Base、公共 Mixin 与异步 Session

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/infra/database.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_database.py`

**Interfaces:**
- Produces `Base`、`IDMixin`、`TimestampMixin`、`SoftDeleteMixin`。
- `IDMixin` 暴露数据库内部 `id: int` 和对外 `uuid: UUID`，`uuid` 有唯一约束且由 ORM 默认生成。
- Produces `engine`、`async_session_factory`、`get_db_session()`、`create_all_tables()`。
- `get_db_session()` 是 FastAPI 异步依赖；请求结束后释放 Session，异常时回滚由依赖边界处理，业务层不依赖隐式事务。
- 测试使用临时 SQLite 数据库，不依赖项目根目录数据库文件。

- [ ] **Step 1: Write the failing database model test**

测试使用一个仅存在于测试文件的 `ExampleRecord`，避免提前创建业务模型：

```python
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, IDMixin, SoftDeleteMixin, TimestampMixin


class ExampleRecord(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "example_records"
    name: Mapped[str] = mapped_column(String(100))


async def test_create_all_and_public_mixins(async_session_factory) -> None:
    async with async_session_factory() as session:
        record = ExampleRecord(name="sample")
        session.add(record)
        await session.commit()
        await session.refresh(record)

        assert isinstance(record.id, int)
        assert isinstance(record.uuid, UUID)
        assert record.created_at.tzinfo is not None
        assert record.updated_at.tzinfo is not None
        assert record.deleted_at is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_database.py::test_create_all_and_public_mixins -q`

Expected: FAIL because the Base and async test database fixture are not implemented。

- [ ] **Step 3: Implement Base and Mixins**

使用 SQLAlchemy 2.0 typed declarative mapping。`IDMixin` 的 `id` 为 `Integer` 主键自增，`uuid` 为字符串或原生 UUID 兼容字段并建立唯一约束；SQLite 与 PostgreSQL 的类型差异必须由 SQLAlchemy 类型处理，不在 Service 层转换。`TimestampMixin` 统一使用 UTC 时间默认值和更新值；`SoftDeleteMixin` 只提供 nullable `deleted_at` 字段，不自动覆盖 ORM delete。

模型中的每个 `relationship()` 后续都必须在声明处写 `lazy="raise"`；本任务可以用注释/测试约束说明，但不创建没有业务意义的关系模型。

- [ ] **Step 4: Implement async database infrastructure**

`infra/database.py` 根据 `Settings.database_url` 创建 async engine 和 sessionmaker，提供：

```python
async def get_db_session() -> AsyncIterator[AsyncSession]: ...
async def create_all_tables() -> None: ...
```

`create_all_tables()` 使用 `await connection.run_sync(Base.metadata.create_all)`，不包含迁移逻辑。生产 PostgreSQL URL 通过配置切换为 `postgresql+asyncpg://...`，本任务不连接生产数据库。

- [ ] **Step 5: Add temporary database fixture**

`conftest.py` 提供 `async_session_factory` fixture，使用 `sqlite+aiosqlite:///:memory:` 或临时文件，并在 fixture 建表/清理。测试不得使用全局生产 engine。

- [ ] **Step 6: Run database tests**

Run: `uv run pytest backend/tests/test_database.py -q`

Expected: PASS，且可确认数据库内部 `id` 与 API 对外 `uuid` 的职责不同。

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/base.py backend/app/infra/database.py backend/tests/conftest.py backend/tests/test_database.py
git commit -m "feat: add async database base and shared mixins"
```

---

### Task 4: 统一响应 Envelope、错误码和分页

**Files:**
- Create: `backend/app/core/errors.py`
- Create: `backend/app/core/response.py`
- Create: `backend/app/core/pagination.py`
- Modify: `backend/tests/test_core.py`

**Interfaces:**
- Produces `ErrorCode(IntEnum)` 和集中维护的错误元数据：业务 code、HTTP status、自然语言 message。
- Produces `BusinessError(error_code: ErrorCode, context: Mapping[str, object] | None = None)`。
- Produces `ResponseEnvelope[T]`、`success_response(data: T | None) -> ResponseEnvelope[T]`、`error_response(...) -> ResponseEnvelope[None]`。
- Produces `PaginationParams(page: int = 1, page_size: int = 20)`，page 从 1 开始，page_size 最大 100。
- Produces `PaginationData[T]` 与 `build_pagination(items, total, params) -> PaginationData[T]`。
- `ErrorCode` 至少覆盖通用认证/校验/系统错误、User/Auth、Pet、Event、File 资源段；具体业务域可以在后续业务计划中继续增加，但不得改变已有编码规则。

- [ ] **Step 1: Write failing tests**

```python
import pytest
from pydantic import ValidationError

from backend.app.core.errors import BusinessError, ErrorCode, get_error_metadata
from backend.app.core.pagination import PaginationParams, build_pagination
from backend.app.core.response import success_response


def test_business_error_metadata_contains_http_status_and_message() -> None:
    metadata = get_error_metadata(ErrorCode.PET_NOT_FOUND)
    assert metadata.http_status == 404
    assert metadata.message


def test_response_envelope_contains_code_message_and_data() -> None:
    response = success_response({"uuid": "public-id"})
    assert response.code == 0
    assert response.message == "success"
    assert response.data == {"uuid": "public-id"}


def test_pagination_rejects_page_zero_and_page_size_over_limit() -> None:
    with pytest.raises(ValidationError):
        PaginationParams(page=0)
    with pytest.raises(ValidationError):
        PaginationParams(page_size=101)


def test_pagination_builds_total_pages() -> None:
    result = build_pagination(["a", "b"], total=7, params=PaginationParams(page=2, page_size=2))
    assert result.items == ["a", "b"]
    assert result.total == 7
    assert result.total_pages == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: FAIL because response, error and pagination modules do not exist。

- [ ] **Step 3: Implement error code metadata**

定义不可变错误元数据结构，例如：

```python
@dataclass(frozen=True)
class ErrorMetadata:
    http_status: int
    message: str
```

用集中映射表维护每个 `ErrorCode` 的 metadata，不能在 View/Service 中写 message 或 HTTP status。系统兜底 code 使用通用系统错误，前端只看到固定自然语言文案。

- [ ] **Step 4: Implement typed response models**

`ResponseEnvelope` 字段固定为 `code`、`message`、`data`；成功 code 为 `0`。错误 envelope 的 `data` 为 `None`。使用 Pydantic 泛型，使后续业务响应可以声明 `ResponseEnvelope[PetResponse]` 或 `ResponseEnvelope[PaginationData[PetResponse]]`。

- [ ] **Step 5: Implement pagination**

使用 Pydantic Field 约束 `page >= 1`、`1 <= page_size <= 100`。`build_pagination()` 只负责根据已查出的 items、total 和参数计算 `total_pages=ceil(total/page_size)`，不执行数据库查询；数据库分页查询属于后续 Selector 层。

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/errors.py backend/app/core/response.py backend/app/core/pagination.py backend/tests/test_core.py
git commit -m "feat: add response error and pagination contracts"
```

---

### Task 5: 密码、JWT 与 Refresh Token 基础安全组件

**Files:**
- Create: `backend/app/core/security/password.py`
- Create: `backend/app/core/security/jwt.py`
- Create: `backend/app/core/security/token.py`
- Create: `backend/app/core/security/__init__.py`
- Modify: `backend/tests/test_core.py`

**Interfaces:**
- Produces `hash_password(password: str) -> str`、`verify_password(password: str, password_hash: str) -> bool`。
- Produces `create_access_token(subject: str, expires_delta: timedelta | None = None) -> str`、`decode_access_token(token: str) -> dict[str, object]`。
- Produces `generate_refresh_token() -> str`、`hash_refresh_token(token: str) -> str`。
- Access Token 使用 JWT、短时效、只存 subject/类型/签发与过期信息，不落库；Refresh Token 使用密码学安全随机值，服务层只持久化其 hash。
- 无效 JWT、过期 JWT、错误 token 类型必须转换为 `BusinessError`，不能将 PyJWT 异常文本直接向上抛到 API。

- [ ] **Step 1: Write failing tests**

```python
from datetime import timedelta

from backend.app.core.security.jwt import create_access_token, decode_access_token
from backend.app.core.security.password import hash_password, verify_password
from backend.app.core.security.token import generate_refresh_token, hash_refresh_token


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")
    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong", password_hash)


def test_access_token_round_trip() -> None:
    token = create_access_token("user-uuid")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-uuid"
    assert payload["type"] == "access"


def test_refresh_token_is_random_and_only_hash_is_persisted() -> None:
    token = generate_refresh_token()
    assert token != generate_refresh_token()
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: FAIL with missing security module imports。

- [ ] **Step 3: Implement bcrypt functions**

直接使用 `bcrypt` 生成带 salt 的 hash；校验函数返回 bool。密码值和 hash 不写日志。密码输入校验长度属于认证请求 Schema/Service 的边界，本任务不把业务规则塞进工具函数。

- [ ] **Step 4: Implement JWT functions**

从 `Settings` 读取 secret、algorithm 和 access token 默认时长；payload 至少包括 `sub`、`type="access"`、`iat`、`exp`。捕获库异常只在安全模块内转换为 `BusinessError(ErrorCode.INVALID_ACCESS_TOKEN)`；异常处理不得返回 PyJWT 原始内容。

- [ ] **Step 5: Implement refresh token helpers**

使用 `secrets.token_urlsafe()` 生成随机原文，使用 SHA-256 或等价单向摘要生成数据库存储值。Refresh Token 的数据库写入、过期判断、撤销和轮换属于后续认证 Service，不在本任务伪造模型。

- [ ] **Step 6: Run security tests**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/security backend/tests/test_core.py
git commit -m "feat: add password and token security primitives"
```

---

### Task 6: 基础设施抽象（Cache、FileStorage、Celery）

**Files:**
- Create: `backend/app/infra/cache/base.py`
- Create: `backend/app/infra/storage/base.py`
- Create: `backend/app/infra/tasks/celery.py`
- Create: `backend/app/infra/tasks/base.py`
- Modify: `backend/tests/test_core.py`

**Interfaces:**
- Produces `CacheClient` 抽象接口，至少定义异步 `get(key)`, `set(key, value, ttl_seconds=None)`, `delete(key)`, `expire(key, ttl_seconds)`。
- Produces `FileStorage` 抽象接口，至少定义异步 `save(file, storage_key)`, `delete(storage_key)`, `exists(storage_key)`, `get_url(storage_key)`；并定义文件元数据结构，包含 storage_key、mime_type、size。
- Produces Celery 配置工厂/边界，不在开发环境连接 Redis、不启动 worker、不创建具体业务任务。
- 抽象接口不依赖 Service、Model 或 Selector，后续 Redis/S3/本地实现必须实现同一接口。

- [ ] **Step 1: Write failing interface contract tests**

```python
import inspect

from backend.app.infra.cache.base import CacheClient
from backend.app.infra.storage.base import FileStorage


def test_cache_contract_is_async_abstract_interface() -> None:
    assert inspect.isabstract(CacheClient)
    assert inspect.iscoroutinefunction(CacheClient.get)
    assert inspect.iscoroutinefunction(CacheClient.set)


def test_storage_contract_is_async_abstract_interface() -> None:
    assert inspect.isabstract(FileStorage)
    assert inspect.iscoroutinefunction(FileStorage.save)
    assert inspect.iscoroutinefunction(FileStorage.get_url)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: FAIL because infra contracts do not exist。

- [ ] **Step 3: Implement CacheClient contract**

使用 `ABC` 或 `Protocol` 明确方法签名。抽象层不实现内存 fallback，不吞异常，不将 Redis 连接细节混入业务代码。Redis 实现和限流实现属于后续计划。

- [ ] **Step 4: Implement FileStorage contract**

文件保存接口接收二进制流或异步文件对象时，签名必须明确调用方责任；接口只表达保存、删除、存在性检查和 URL 获取，不决定业务关联表。文件大小、MIME 和目录键规则由文件 Service/Schema 使用 `core.constants` 执行。

- [ ] **Step 5: Add Celery boundary**

提供读取 broker/backend 配置的 Celery 配置函数和任务基类导出位置，但不导入 Redis 客户端、不创建业务任务、不在应用启动时初始化 worker。

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest backend/tests/test_core.py -q`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/infra/cache backend/app/infra/storage backend/app/infra/tasks backend/tests/test_core.py
git commit -m "feat: define external infrastructure contracts"
```

---

### Task 7: HTTP 异常处理、中间件和健康检查

**Files:**
- Create: `backend/app/middlewares/exception.py`
- Create: `backend/app/middlewares/cors.py`
- Create: `backend/app/middlewares/logging.py`
- Create: `backend/app/middlewares/rate_limit.py`
- Create: `backend/app/middlewares/__init__.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_app.py`

**Interfaces:**
- Produces `register_exception_handlers(app: FastAPI) -> None`。
- Produces中间件注册函数，CORS 使用 Settings.allowed_origins；日志记录 method/path/status/duration/request_id 等非敏感元数据，不记录 token、cookie、密码、完整个人信息或异常堆栈到用户响应。
- 所有 `/api/v1/` 业务路由预留；本任务保留 `/` 和 `/health`，健康检查响应也使用统一 envelope。
- `GET /health` 返回 HTTP 200 和 `{"code": 0, "message": "success", "data": {"status": "ok"}}`。
- `RequestValidationError` 返回统一自然语言错误 envelope；`BusinessError` 返回映射的 HTTP status/code/message；未预期异常返回固定系统错误文案。
- 不在 View 或中间件中捕获后继续执行；中间件只负责把异常转换为安全响应并记录服务端日志。

- [ ] **Step 1: Write failing API tests**

```python
from fastapi import APIRouter

from backend.app.core.errors import BusinessError, ErrorCode
from backend.app.core.response import ResponseEnvelope


async def test_health_uses_response_envelope(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }


async def test_business_error_is_safe_and_mapped(client) -> None:
    router = APIRouter()

    @router.get("/test-business-error")
    async def raise_business_error() -> None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)

    client.app.include_router(router)
    response = await client.get("/test-business-error")
    assert response.status_code == 404
    assert response.json()["code"] == int(ErrorCode.PET_NOT_FOUND)
    assert response.json()["message"]
    assert "Traceback" not in response.text


async def test_unexpected_error_does_not_leak_python_text(client) -> None:
    router = APIRouter()

    @router.get("/test-unexpected-error")
    async def raise_unexpected_error() -> None:
        raise RuntimeError("database password leaked")

    client.app.include_router(router)
    response = await client.get("/test-unexpected-error")
    assert response.status_code == 500
    assert response.json()["message"]
    assert "database password leaked" not in response.text
    assert "Traceback" not in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest backend/tests/test_app.py -q`

Expected: FAIL because health still returns the旧格式，且异常 handler 尚未注册。

- [ ] **Step 3: Implement exception handlers**

注册 FastAPI handlers for `BusinessError`, `RequestValidationError`, `HTTPException` and generic `Exception`。每种 handler 都调用 `error_response()` 使用集中 metadata；422 校验错误只返回自然语言的通用参数错误，字段细节可以返回安全的字段名/规则信息，但不能把 Python traceback 或底层异常字符串放入 message。

注意 generic handler 必须 `logger.exception(...)` 在服务端记录上下文，同时给客户端返回固定系统错误；测试环境也不要把原始异常文本放进 JSON。

- [ ] **Step 4: Implement middleware registration**

CORS 的 allowed origins 从 Settings 读取；请求日志 middleware 生成或传递 request id，使用 finally 记录耗时，但不通过 `try/except` 把错误变成成功响应。`rate_limit.py` 只定义未来接入 `CacheClient` 的依赖边界，当前默认不限制请求，避免伪造 Redis 行为。

- [ ] **Step 5: Update main.py**

将现有 `/`、`/health` 路由改为 `async def`，统一返回 `ResponseEnvelope`；应用创建时按顺序注册异常 handler、CORS、日志中间件，并保留 `/api/v1` 路由挂载位置。不要在 main.py 内写业务异常映射表。

- [ ] **Step 6: Run API tests**

Run: `uv run pytest backend/tests/test_app.py -q`

Expected: PASS。再运行 `uv run pytest`，Expected: 全部 backend tests PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/app/middlewares backend/tests/test_app.py
git commit -m "feat: add safe API error handling and middleware foundation"
```

---

### Task 8: 核心基础设施集成验收与文档同步

**Files:**
- Modify: `README.md`（只更新后端启动/测试/API 响应说明）
- Modify: `backend/app/__init__.py`（仅在需要时补充公共导出）
- Test: `backend/tests/test_core.py`
- Test: `backend/tests/test_database.py`
- Test: `backend/tests/test_app.py`

**Interfaces:**
- Produces一个可通过 `uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000` 启动的核心后端骨架。
- `GET /health`、核心模块导入、SQLite 建表、统一异常响应和安全工具均有自动化验证。
- 后续业务计划可以直接依赖 `get_db_session`、`Base`/Mixins、`ResponseEnvelope`、`BusinessError`、`PaginationParams`、security API 和 infra 抽象，不需要重建基础设施。

- [ ] **Step 1: Run the complete backend test suite**

Run: `uv run pytest -q`

Expected: 所有 backend tests PASS。

- [ ] **Step 2: Run static/import checks**

Run: `uv run python -c "from backend.main import app; print(app.title)"`

Expected: 输出 `HerpLog API`，不出现循环导入错误。

- [ ] **Step 3: Run type/lint checks available in repository**

先检查 `pyproject.toml` 是否已有对应命令；若没有，不新增未约定的工具。至少运行：

```bash
uv run python -m compileall backend
```

Expected: 命令成功完成，不产生语法错误。

- [ ] **Step 4: Build/run smoke check**

Run: `uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000`，用独立 HTTP 客户端请求 `/health` 后正常停止进程。不得把真实密钥、数据库文件或上传文件提交到 Git。

Expected: `/health` 返回 HTTP 200 的统一 envelope。

- [ ] **Step 5: Synchronize README**

只补充当前真实行为：安装/运行命令、`/health` 的 envelope 示例、SQLite `create_all()` 说明和 pytest 命令；删除或修正“前端已经请求后端 `/health`”这类与当前代码不一致的描述。不要在 README 中承诺尚未实现的认证或业务 API。

- [ ] **Step 6: Run final verification**

Run:

```bash
uv run pytest -q
uv run python -m compileall backend
 git diff --check
```

Expected: 测试全部通过、编译无错误、`git diff --check` 无输出。

- [ ] **Step 7: Commit**

```bash
git add README.md backend/app/__init__.py backend/tests
git commit -m "docs: document backend foundation and verification"
```

---

## 计划自查

- **规范覆盖**：目录分层、异步 SQLAlchemy、SQLite `create_all`、公共 Mixin、统一 envelope、分页、业务码、异常防泄漏、bcrypt/JWT/Refresh Token、CORS/日志/限流边界、Cache/FileStorage/Celery 抽象、多端 `/api/v1` 预留均有对应任务。
- **业务边界**：本计划不创建 User/Pet/Event/File 业务模型，不实现业务 API；这些内容分别属于后续认证、宠物、事件、文件计划，避免交叉开发。
- **Serializer 边界**：本计划只建立通用响应 envelope，不创建业务 Serializer；业务 Schema 与序列化在对应业务计划中实现。
- **Selector/Service 边界**：本计划不创建业务 Selector/Service；数据库 Session 和公共模型基础只为后续层提供依赖。
- **错误安全**：预期错误通过显式业务逻辑与 `BusinessError`，只有未预期异常由全局兜底 handler 处理；客户端不接收异常文本或 traceback。
- **占位符检查**：没有待定标记或要求实现者自行补充的模糊步骤；Redis/S3/Celery 的“不实现”是明确范围约束，不是未完成项。
- **类型一致性**：后续任务依赖的名称已在前序任务 Interfaces 中定义；测试 fixture 使用 `async_session_factory` 和 `client`，分别由 Task 3、Task 1/Task 7 提供。
