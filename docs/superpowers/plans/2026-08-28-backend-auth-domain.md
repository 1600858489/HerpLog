# 后端认证域实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有核心基础设施之上实现多用户认证域，支持用户名/手机号/邮箱注册、密码登录、Access Token、落库 Refresh Token、刷新、登出和当前用户鉴权。

**Architecture:** 认证域遵循 `views → schemas → services/selectors → models` 单向依赖。Service 负责注册、登录、Token 轮换和撤销的业务规则与事务；Selector 只负责只读查询；View 只负责 HTTP 参数、依赖注入和 envelope。Access Token 使用用户公开 UUID 作为 subject，Refresh Token 使用随机原文、数据库只保存 hash，并通过轮换和撤销支持多设备会话。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 AsyncSession, SQLite + aiosqlite, Pydantic v2, bcrypt, PyJWT, pytest, pytest-asyncio, httpx.

## Global Constraints

- 直接在当前 `master` 分支开发，不创建 worktree，不使用 subagent，不推送远端。
- 后端使用 FastAPI；数据库访问使用 SQLAlchemy 2.0 `AsyncSession`。
- 所有业务模型继承 `IDMixin`、`TimestampMixin`、`SoftDeleteMixin`；内部使用自增 `id`，接口只暴露 `uuid`。
- 所有 `relationship()` 必须使用 `lazy="raise"`；Selector 查询需要的关系必须显式 `selectinload()`/`joinedload()`。
- API 请求/响应统一使用 snake_case；请求 Schema 继承 `BaseRequestSchema`，使用 `extra="forbid"`。
- 请求体不声明 `id`/`uuid`；资源目标 UUID 放在路径参数或 Token 中，不能从请求体接收数据库内部标识。
- 业务写入和事务只属于 Service；Selector 只读；View 不写业务逻辑、不管理事务、不使用 `try/except` 过滤预期错误。
- 业务失败使用 `BusinessError` 和集中 `ErrorCode`；客户端不接收 Python 异常文本或 traceback。
- 用户密码只存 bcrypt hash；Refresh Token 只存 hash，不存明文。
- 用户名、手机号、邮箱的唯一性在数据库约束和 Service 预检查两层保证；空手机号/邮箱不参与唯一性冲突。
- 所有业务查询必须按当前用户隔离。Refresh Token 在尚未识别用户前的凭证 hash 精确查询，是认证边界的特殊查询，不得作为普通业务资源查询复用。
- 路由统一使用 `/api/v1/` 前缀；微信登录只预留 `wechat_openid`，本计划不实现微信渠道登录。

## 文件结构映射

- Create: `backend/app/models/user.py` — User ORM 模型。
- Create: `backend/app/models/refresh_token.py` — RefreshToken ORM 模型。
- Modify: `backend/app/models/__init__.py` — 导出认证模型，保证 `create_all()` 注册表结构。
- Create: `backend/app/schemas/auth.py` — 注册、登录、刷新、登出请求和认证响应 Serializer/Deserializer。
- Modify: `backend/app/schemas/__init__.py` — 导出认证 Schema。
- Create: `backend/app/selectors/auth.py` — 用户和 Refresh Token 的只读查询。
- Create: `backend/app/selectors/__init__.py` — 通过包入口导出认证 Selector。
- Create: `backend/app/services/auth.py` — 注册、登录、Token 轮换、撤销和当前用户业务逻辑。
- Create: `backend/app/services/__init__.py` — 通过包入口导出认证 Service。
- Create: `backend/app/core/security/dependencies.py` — FastAPI 当前用户鉴权依赖。
- Modify: `backend/app/core/security/__init__.py` — 导出鉴权依赖。
- Create: `backend/app/views/auth.py` — `/api/v1/auth` 路由。
- Create: `backend/app/views/__init__.py` — 路由公共导出。
- Modify: `backend/main.py` — 挂载认证路由。
- Modify: `backend/tests/conftest.py` — 测试数据库、Session 覆盖和测试应用 fixture。
- Create: `backend/tests/test_auth_schemas.py` — 请求反序列化和响应序列化测试。
- Create: `backend/tests/test_auth_service.py` — 注册、登录、刷新、登出业务测试。
- Create: `backend/tests/test_auth_api.py` — 认证 API 和越权/异常响应测试。
- Modify: `README.md` — 只补充当前已实现的认证 API 启动和测试说明。

## API 契约

### 注册

`POST /api/v1/auth/register`

请求：

```json
{
  "username": "keeper",
  "phone": null,
  "email": null,
  "password": "strong-password"
}
```

规则：

- `username`、`phone`、`email` 至少提供一个作为注册标识。
- 如果没有 `username`，必须只提供 `phone` 或只提供 `email`，并将其规范化值自动写入 `username`。
- 如果提供 `username`，`phone`/`email` 可以为空，也可以作为注册时一并绑定的联系方式。
- `username`、`phone`、`email` 按各自字段唯一；email 比较时统一小写并去除首尾空白，文本字段统一去除首尾空白。
- 注册成功只返回用户信息，不自动签发 Token；登录是独立操作。

响应：HTTP 201，`ResponseEnvelope[UserResponse]`。

### 登录

`POST /api/v1/auth/login`

请求：

```json
{
  "identifier": "keeper",
  "password": "strong-password",
  "device_info": "ios-app"
}
```

`identifier` 可以匹配 username、phone 或 email。登录成功创建一条有效 RefreshToken，返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt",
    "refresh_token": "opaque-token",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "uuid": "public-user-uuid",
      "username": "keeper",
      "phone": null,
      "email": null
    }
  }
}
```

### 刷新 Token

`POST /api/v1/auth/refresh`

请求体只包含 `refresh_token`，不能包含 `id`/`uuid`。验证 token hash、未撤销、未过期且所属用户未软删除后：

1. 撤销旧 RefreshToken
2. 创建新的 RefreshToken
3. 签发新的 Access Token
4. 在同一事务中提交

返回新的 `AuthResponse`。旧 Refresh Token 不能重复使用。

### 登出

`POST /api/v1/auth/logout`

请求体包含 `refresh_token`，只撤销该 Refresh Token，不影响其他设备会话；响应为 `ResponseEnvelope[None]`。后续可增加“全部设备登出”，本计划不实现。

### 当前用户

`GET /api/v1/auth/me`

请求头：`Authorization: Bearer <access_token>`。

通过 `get_current_user` 解析 Access Token 的 subject（用户公开 UUID），Selector 按 UUID 查询未软删除用户，返回 `UserResponse`。无 token、无效 token、已删除用户统一返回自然语言错误 envelope。

## 错误码补充

沿用已有千位/百位分段，在实现中使用已定义错误码：

- `AUTHENTICATION_FAILED`（2201，401）：登录标识或密码错误，不区分“用户不存在”和“密码错误”。
- `REFRESH_TOKEN_INVALID`（2211，401）：刷新 token 缺失、无效、已撤销或已过期。
- `USER_CONFLICT`（2121，409）：用户名、手机号或邮箱已被使用。
- `USER_VALIDATION_FAILED`（2111，400）：注册身份组合不合法。
- `INVALID_ACCESS_TOKEN`（1030，401）：Access Token 无效或过期。
- `UNAUTHORIZED`（1020，401）：缺少认证凭证。

## 任务拆分

### Task 1: User 与 RefreshToken 模型

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/refresh_token.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/tests/test_auth_models.py`

**Interfaces:**
- Produces `User` 和 `RefreshToken` ORM 类。
- `User` 字段：`username`、`phone`、`email`、`password_hash`、`wechat_openid`。
- `RefreshToken` 字段：`user_id`、`token_hash`、`expires_at`、`revoked_at`、`device_info`。
- 两个模型均继承公共 Mixin；关系使用 `lazy="raise"`。
- 后续数据库 fixture 从 `app` 包导入模型 后可由 `Base.metadata.create_all` 建表。

- [ ] **Step 1: Write the failing test**

```python
from datetime import timedelta

from sqlalchemy import select

from app.models import RefreshToken, User
from app.utils.datetime import utc_now


async def test_auth_models_persist_public_uuid_and_relationship(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        session.add(
            RefreshToken(
                user_id=user.id,
                token_hash="token-hash",
                expires_at=utc_now() + timedelta(days=1),
            )
        )
        await session.commit()
        result = await session.execute(select(User).where(User.username == "keeper"))
        stored_user = result.scalar_one()
        assert stored_user.id > 0
        assert stored_user.uuid is not None
        assert stored_user.password_hash == "hashed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run --project .. pytest tests/test_auth_models.py::test_auth_models_persist_public_uuid_and_relationship -q`

Expected: FAIL because authentication models are not defined or not registered。

- [ ] **Step 3: Implement the models**

Use typed SQLAlchemy mappings. Add database-level unique constraints for username, phone, email, wechat_openid, token_hash; nullable contact fields must remain nullable. Define `User.refresh_tokens` and `RefreshToken.user` with `back_populates` and `lazy="raise"`; do not use ORM cascade to perform soft deletion.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run --project .. pytest tests/test_auth_models.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add backend/app/models backend/tests/test_auth_models.py
git commit -m "feat: 增加用户与刷新令牌模型"
```

### Task 2: 认证请求与响应 Serializer

**Files:**
- Create: `backend/app/schemas/auth.py`
- Modify: `backend/app/schemas/__init__.py`
- Create: `backend/tests/test_auth_schemas.py`

**Interfaces:**
- Produces `RegisterRequest`、`LoginRequest`、`RefreshRequest`、`LogoutRequest`、`UserResponse`、`AuthResponse`。
- 所有请求 Schema 继承 `BaseRequestSchema`；所有响应 Schema 不含内部 `id`。
- 产生密码、email、phone、identifier 的边界校验；不包含数据库查询或业务写入。

- [ ] **Step 1: Write failing tests**

```python
import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest


def test_register_rejects_request_without_any_identity() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(password="strong-password")


def test_register_derives_username_from_phone_or_email() -> None:
    request = RegisterRequest(phone=" 13800138000 ", password="strong-password")
    assert request.phone == "13800138000"
    assert request.username == "13800138000"


def test_register_normalizes_email_and_forbids_internal_ids() -> None:
    request = RegisterRequest(email=" Keeper@Example.COM ", password="strong-password")
    assert request.email == "keeper@example.com"
    assert request.username == "keeper@example.com"
    with pytest.raises(ValidationError):
        RegisterRequest(username="keeper", password="strong-password", id=1)


def test_login_requires_identifier_and_password() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(identifier="keeper", password="short")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run --project .. pytest tests/test_auth_schemas.py -q`

Expected: FAIL because auth schemas are missing。

- [ ] **Step 3: Implement request and response schemas**

Use Pydantic field validators for whitespace and email normalization. Register validation must reject no identity and reject a request without username that contains both phone and email; a username-based request may carry either or both optional contacts. Password minimum length is 8 characters. `UserResponse` includes only `uuid`, `username`, `phone`, `email`; `AuthResponse` includes token fields and `UserResponse`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run --project .. pytest tests/test_auth_schemas.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas backend/tests/test_auth_schemas.py
git commit -m "feat: 定义认证请求与响应序列化器"
```

### Task 3: 认证 Selector 与注册/登录 Service

**Files:**
- Create: `backend/app/selectors/auth.py`
- Create: `backend/app/selectors/__init__.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/tests/test_auth_service.py`

**Interfaces:**
- Produces `get_user_by_identifier(session, identifier) -> User | None`。
- Produces `get_user_by_uuid(session, user_uuid) -> User | None`。
- Produces `get_refresh_token_by_hash(session, token_hash) -> RefreshToken | None`，仅用于认证凭证精确查找，不作为普通资源查询。
- Produces `register_user(session, request) -> User`。
- Produces `AuthResult`，一个不可变 dataclass，字段为 `access_token: str`、`refresh_token: str`、`token_type: str`、`expires_in: int`、`user: User`。
- Produces `authenticate_user(session, request, device_info) -> AuthResult`。
- Produces `refresh_authentication(session, refresh_token) -> AuthResult`。
- Service 负责 `flush/commit`，不返回 HTTP response；预期失败抛 `BusinessError`。

- [ ] **Step 1: Write failing service tests**

```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import BusinessError, ErrorCode
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import authenticate_user, register_user


async def test_register_hashes_password_and_derives_username(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = await register_user(
            session,
            RegisterRequest(phone="13800138000", password="strong-password"),
        )
        await session.commit()
        assert user.username == "13800138000"
        assert user.password_hash != "strong-password"


async def test_register_rejects_duplicate_identity(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        assert error.value.error_code == ErrorCode.USER_CONFLICT


async def test_login_rejects_wrong_password_without_leaking_details(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await authenticate_user(session, LoginRequest(identifier="keeper", password="wrong-pass"), None)
        assert error.value.error_code == ErrorCode.AUTHENTICATION_FAILED
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run --project .. pytest tests/test_auth_service.py -q`

Expected: FAIL because auth selector/service modules do not exist。

- [ ] **Step 3: Implement selectors**

User identifier selector must query active users only and match username, phone, or email. UUID selector must query active user by public UUID. Every user-owned query accepts the relevant user identity; the credential-hash lookup is isolated to the auth boundary and matches one unique hash. No selector writes or commits.

- [ ] **Step 4: Implement registration service**

Normalize request values from Schema, check identity conflicts through Selector, hash password with existing `hash_password`, construct User, add to session, flush to assign internal ID/UUID, and return User. Do not catch `IntegrityError` as normal business control flow; the pre-check handles expected conflicts and the database constraint remains a last-resort integrity guard for concurrent requests.

- [ ] **Step 5: Implement authentication service**

Find user by identifier, verify bcrypt hash, create Access Token with the user UUID subject, generate and hash Refresh Token, create a RefreshToken row with configured expiry and optional device info, flush/commit in one transaction, and return a typed `AuthResult` containing the public token and user data. For a missing user or wrong password always raise the same `AUTHENTICATION_FAILED` code.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run --project .. pytest tests/test_auth_service.py -q`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/selectors backend/app/services backend/tests/test_auth_service.py
git commit -m "feat: 实现用户注册与登录服务"
```

### Task 4: Refresh Token 轮换、登出与当前用户依赖

**Files:**
- Modify: `backend/app/services/auth.py`
- Create: `backend/app/core/security/dependencies.py`
- Modify: `backend/app/core/security/__init__.py`
- Modify: `backend/tests/test_auth_service.py`
- Create: `backend/tests/test_auth_dependencies.py`

**Interfaces:**
- Produces `refresh_authentication(session, refresh_token) -> AuthResult`。
- Produces `logout_user(session, refresh_token) -> None`。
- Produces `get_current_user(credentials, session) -> User`，作为 FastAPI `Depends` 使用。

- [ ] **Step 1: Write failing tests**

```python
import pytest
from app.core.errors import BusinessError, ErrorCode
from app.core.security.dependencies import get_current_user
from app.services.auth import authenticate_user, refresh_authentication, logout_user


async def test_refresh_rotates_token_and_revokes_old_one(async_session_factory) -> None:
    async with async_session_factory() as session:
        auth_result = await authenticate_user(session, login_request, "android-app")
        rotated = await refresh_authentication(session, auth_result.refresh_token)
        assert rotated.refresh_token != auth_result.refresh_token
        with pytest.raises(BusinessError) as error:
            await refresh_authentication(session, auth_result.refresh_token)
        assert error.value.error_code == ErrorCode.REFRESH_TOKEN_INVALID


async def test_logout_revokes_only_selected_refresh_token(async_session_factory) -> None:
    async with async_session_factory() as session:
        auth_result = await authenticate_user(session, login_request, "web")
        await logout_user(session, auth_result.refresh_token)
        with pytest.raises(BusinessError):
            await refresh_authentication(session, auth_result.refresh_token)
```

The implementation test file must define `login_request` with `LoginRequest(identifier="keeper", password="strong-password")` and create the user before authentication.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run --project .. pytest tests/test_auth_service.py backend/tests/test_auth_dependencies.py -q`

Expected: FAIL because refresh/logout/dependency interfaces are missing。

- [ ] **Step 3: Implement refresh rotation**

Hash the presented opaque token, load the single token record, explicitly validate `revoked_at is None`, `expires_at > utc_now()`, and active user state. Mark the old row revoked, create a new row, issue a new Access Token, and commit all changes atomically. Do not use `try/except` to identify expired or revoked tokens.

- [ ] **Step 4: Implement logout**

Find the token by hash, raise `REFRESH_TOKEN_INVALID` if missing or already revoked, set `revoked_at=utc_now()`, and commit. Revoke only the specified session.

- [ ] **Step 5: Implement current-user dependency**

Use FastAPI `HTTPBearer(auto_error=False)`. Missing credentials raise `UNAUTHORIZED`; decode errors from existing JWT helper become `INVALID_ACCESS_TOKEN`; parse the subject as UUID and query active User by public UUID. The dependency returns a `User` ORM instance with no relationship access, so no implicit IO is introduced.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run --project .. pytest tests/test_auth_service.py backend/tests/test_auth_dependencies.py -q`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/auth.py backend/app/core/security backend/tests/test_auth_service.py backend/tests/test_auth_dependencies.py
git commit -m "feat: 增加刷新令牌轮换与用户鉴权依赖"
```

### Task 5: 认证 View 和 `/api/v1` 路由

**Files:**
- Create: `backend/app/views/auth.py`
- Create: `backend/app/views/__init__.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_auth_api.py`

**Interfaces:**
- Produces `auth_router`，由 `main`（从 `backend` 目录加载） 挂载为 `/api/v1/auth`。
- View endpoint 只接收 Schema、注入 AsyncSession/当前用户、调用 Service、序列化 ORM 返回 envelope。
- 端点：`register`、`login`、`refresh`、`logout`、`me`。

- [ ] **Step 1: Write failing API tests**

```python
async def test_register_returns_public_user_only(client) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "keeper"
    assert "id" not in body["data"]
    assert "password_hash" not in body["data"]


async def test_login_refresh_logout_and_me_flow(client) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "keeper", "password": "strong-password", "device_info": "test"},
    )
    assert login.status_code == 200
    auth = login.json()["data"]
    assert auth["token_type"] == "bearer"
    assert "id" not in auth["user"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "keeper"

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["refresh_token"] != auth["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed.json()["data"]["refresh_token"]},
    )
    assert logout.status_code == 200
    assert logout.json() == {"code": 0, "message": "success", "data": None}


async def test_auth_api_rejects_internal_id_and_hides_authentication_details(client) -> None:
    invalid = await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password", "id": 1},
    )
    assert invalid.status_code == 422
    assert "id" not in invalid.text

    failed = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "missing", "password": "wrong-pass"},
    )
    assert failed.status_code == 401
    assert failed.json()["code"] == 2201
    assert failed.json()["message"] == "用户名或密码错误"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run --project .. pytest tests/test_auth_api.py -q`

Expected: FAIL because auth router is not mounted。

- [ ] **Step 3: Implement thin View endpoints**

Use `Depends(get_db_session)`, `Depends(get_current_user)`, and request Schema types. Register uses status 201; login/refresh/me use 200; logout returns `success_response(None)`. Each response is generated by the corresponding response Schema before envelope construction. No View catches exceptions or constructs error messages.

- [ ] **Step 4: Mount versioned router**

Add `app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])` in `backend/main.py`; keep existing health endpoints unchanged. Import the router through the `app.views` package export, not an internal module path from other business domains.

- [ ] **Step 5: Configure test database override**

Update `conftest.py` with a per-test SQLite `StaticPool` engine, import all models before `create_all`, override `get_db_session`, and clear `app.dependency_overrides` after each test. The test client must use `ASGITransport(raise_app_exceptions=False)` and run lifespan initialization only against the configured test database.

- [ ] **Step 6: Run API tests**

Run: `cd backend && uv run --project .. pytest tests/test_auth_api.py -q`

Expected: PASS；随后运行 `cd backend && uv run --project .. pytest -q`，既有核心测试与认证测试全部通过。

- [ ] **Step 7: Commit**

```bash
git add backend/app/views backend/main.py backend/tests/conftest.py backend/tests/test_auth_api.py
git commit -m "feat: 暴露版本化认证 API"
```

### Task 6: 认证域集成验收和文档同步

**Files:**
- Modify: `README.md`
- Modify: `backend/tests/test_auth_api.py`
- Modify: `backend/tests/test_auth_service.py`

**Interfaces:**
- Produces可运行的认证 API，覆盖注册、登录、刷新、登出、当前用户和安全错误响应。
- 不引入微信登录、Redis 黑名单、数据库迁移或前端 API 接入。

- [ ] **Step 1: Add edge-case tests**

补充以下行为测试；每个测试都在自身内部完成注册和登录准备，不使用省略号或未定义 helper：

```python
async def test_refresh_token_cannot_be_reused_after_rotation(client) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "keeper", "password": "strong-password"},
    )
    old_refresh_token = login.json()["data"]["refresh_token"]
    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reused.status_code == 401
    assert reused.json()["code"] == 2211


async def test_missing_bearer_token_returns_safe_401(client) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["message"] == "请先登录"


async def test_expired_access_token_returns_safe_401(client) -> None:
    expired_token = create_access_token(
        "00000000-0000-0000-0000-000000000000",
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == 1030
    assert "Traceback" not in response.text
```

该测试需要在文件顶部导入 `timedelta` 和 `create_access_token`。过期 Token 在鉴权依赖中应先因过期被拒绝，不应进入用户查询。 

- [ ] **Step 2: Run complete verification**

Run:

```bash
cd backend && uv run --project .. pytest -q
uv run python -m compileall backend
uv run python -c "from main import app; print([route.path for route in app.routes if '/api/v1/auth' in route.path])"
git diff --check
```

Expected: 所有测试通过，编译和导入成功，输出五个认证路由，diff 检查无输出。

- [ ] **Step 3: Run startup smoke test**

使用临时 SQLite 文件和临时端口启动：

```bash
DATABASE_URL=sqlite+aiosqlite:////tmp/herplog-auth-smoke.db uv run cd backend && uv run --project .. uvicorn main:app --host 127.0.0.1 --port 18002
```

请求 `/health` 和注册/登录流程，确认真实 ASGI 服务可用；结束后不提交临时数据库文件。

- [ ] **Step 4: Synchronize README**

补充当前已实现的认证端点、请求体不接受 `id`、启动和测试命令；明确微信登录、Redis 黑名单、PG 迁移仍未实现。不得描述尚未存在的功能。

- [ ] **Step 5: Commit**

```bash
git add README.md backend/tests
git commit -m "docs: 补充认证 API 使用与验收说明"
```

## 计划自查

- 模型、Schema、Selector、Service、依赖、View、测试和路由均有对应任务。
- 认证流程的事务边界明确：注册一次写入；登录创建 RefreshToken；刷新撤销旧 token 并创建新 token；登出只撤销指定 token。
- 未把 Refresh Token 查找错误地复用为普通用户资源查询；该查询发生在认证凭证尚未解析出用户的边界，并仅按唯一 hash 精确查找。
- 注册规则明确区分用户名注册与手机号/邮箱注册；手机号和邮箱注册不能同时作为无 username 的双重身份，避免 username 自动派生歧义。
- 所有外部响应都经过 Schema 和 envelope；密码 hash、内部 id、异常文本不出现在响应中。
- 没有引入 JSON 字段、Alembic、Redis/S3/Celery 具体实现、微信登录或前端改造。
- Task 6 的示例中不得保留省略号；实施时必须替换成完整测试代码。
