# HerpLog 后端 API 架构设计

## 目标

为 HerpLog 设计一套完整的后端分层架构：FastAPI + SQLAlchemy 2.0（异步）+ SQLite（开发）/ PostgreSQL（生产）。本次只做**代码分层、目录组织、数据模型、响应/异常规范、功能点清单**的设计，不编写具体实现代码，不编写数据库迁移脚本。

产品背景：HerpLog 从个人使用的爬宠饲养记录工具，扩展为支持多用户的服务，未来会接入微信小程序和手机 App（本轮只做接口预留，不实现微信登录等具体渠道逻辑）。产品核心卖点是"快速、多维度、简单地记录"，因此本轮范围包含文件上传能力。

## 范围

本次设计包含：

- 完整的分层目录结构（views / services / selectors / models / schemas / middlewares / core / infra / utils）
- 用户与鉴权、宠物、事件、文件四个业务域的数据库表结构
- 统一响应体 envelope、分页封装、业务错误码体系
- 异常传递与统一处理机制
- 多用户数据隔离的强制规则
- 异步 ORM 使用规范（`lazy="raise"`）
- Redis / 文件存储 / Celery 的基础设施抽象层（仅接口位置，不写实现）
- 本轮功能点清单（API 端点范围）

本次不包含：

- 具体的业务代码实现
- 数据库迁移脚本（当前用 SQLAlchemy `create_all()`，切换 PG 时再引入迁移工具）
- 微信小程序登录、对象存储、Celery 任务的具体实现（仅接口占位）
- 前端改造（前端命名规范调整、Mock 替换为真实 API 属于后续独立设计）

## 技术选型

- Web 框架：FastAPI
- ORM：SQLAlchemy 2.0，异步模式（`AsyncSession`）
- 开发数据库驱动：`aiosqlite`
- 生产数据库驱动：`asyncpg`（PostgreSQL）
- 密码哈希：`bcrypt`
- Token：JWT（Access Token，无状态）+ 落库的 Refresh Token
- 缓存/黑名单/限流/任务队列底层：Redis（本轮只设计抽象接口）
- 任务队列：Celery（本轮只做接口占位）

## 目录结构与分层职责

```text
backend/
  app/
    views/        # 路由 + 请求解析 + 调用 service + 返回封装响应
    services/     # 业务逻辑、事务边界、跨域协调、抛出 BusinessError
    selectors/    # 只读查询，强制带 user_id 过滤，显式声明预加载
    models/       # SQLAlchemy 2.0 ORM 模型
    schemas/      # Pydantic 请求/响应模型
    middlewares/  # cors.py / exception.py / logging.py / rate_limit.py
    core/         # config.py / errors.py / response.py / pagination.py / constants.py / security/
    infra/        # cache/ / storage/ / tasks/ / clients/
    utils/        # datetime.py / uuid.py / string.py / json.py
  main.py
```

### 各层职责边界

**views/**：只做请求参数解析、鉴权依赖注入、调用 service、把 service 返回结果交给 schema 序列化后封装为 envelope 返回。不写业务逻辑，不写 `try/except`（异常统一由中间件处理）。

**services/**：业务逻辑的唯一归属层。负责事务边界（一个业务操作的多个写操作要在同一个 DB 事务里完成）、跨域协调（比如创建 Event 时需要校验 Pet 是否存在、是否属于当前用户）、级联软删除的编排。业务规则被违反时直接 `raise BusinessError(ErrorCode.XXX)`。

**selectors/**：只读查询的唯一归属层。每个查询函数：
- 必须接收 `user_id` 参数，查询条件强制过滤到该用户名下数据，不提供无用户过滤的变体
- 按业务场景显式声明需要的预加载（`selectinload`/`joinedload`），不依赖隐式 IO
- 默认过滤 `deleted_at IS NULL`
- 返回 ORM 模型实例或轻量元组，不做任何面向前端的字段裁剪、重命名、嵌套组装（这些是 schemas 层职责）

**models/**：SQLAlchemy ORM 模型定义。所有 `relationship()` 强制设置 `lazy="raise"`。所有业务表继承 `IDMixin`、`TimestampMixin`、`SoftDeleteMixin`。模型不包含预加载策略常量、不调用 service/selector。

**schemas/**：唯一负责"数据库模型 ↔ API JSON"转换的层。职责包括：
- 响应 Schema 只暴露 `uuid`，不暴露自增 `id`
- 请求 Schema 统一继承 `BaseRequestSchema`（设置 `extra="forbid"`），永不声明 `id`/`uuid` 为可写字段
- 字段命名统一 snake_case，不做 camelCase 转换
- `model_validate()` 从 service 传入的 ORM 对象生成响应体

**middlewares/**：HTTP 请求生命周期挂钩，包括异常捕获 handler（`exception.py`）、请求日志（`logging.py`）、CORS（`cors.py`）、未来的限流中间件（`rate_limit.py`）。

**core/**：应用级、跨业务模块共享的核心协议与基础机制，包括错误码枚举、`BusinessError` 异常基类、响应 envelope 结构、分页参数/响应结构、应用配置（`Settings`）、安全子模块（`security/jwt.py`、`security/password.py`、`security/token.py`）。

**infra/**：外部系统/IO 资源的适配层，包括缓存客户端抽象（`cache/`）、文件存储抽象（`storage/`）、任务队列（`tasks/`）、第三方 API 客户端占位（`clients/`）。

**utils/**：无状态、无业务语义的通用工具，如 UUID 生成、日期计算、字符串处理，不包含安全/认证相关内容（那些归 `core/security/`）。

### 跨层与跨包调用规则

- 层内如果功能复杂，可以拆成包（例如 `services/pets/` 包含 `service.py`、`validators.py` 等内部模块），但对外必须通过该包的 `__init__.py` 统一导出
- 跨域调用只能引用目标包 `__init__.py` 导出的符号，禁止 `from services.pets.internal import xxx` 这种绕过 `__init__` 直接引用内部文件的写法
- 禁止出现循环导入；当两个域出现双向依赖需求时，应在更上层（service 组合、专门的协调函数）解决，不通过延迟导入掩盖问题

## 数据库表清单

### 公共 Mixin（所有业务表继承）

- `IDMixin`：`id`（自增主键，仅内部使用）+ `uuid`（对外暴露的唯一标识，唯一索引）
- `TimestampMixin`：`created_at`、`updated_at`（`onupdate` 自动维护）
- `SoftDeleteMixin`：`deleted_at`（可空，Selector 层默认过滤 `deleted_at IS NULL`）

前端/API 请求方永远不能获知、也不能传输自增 `id`；所有对外交互只使用 `uuid`。请求 Schema 的 `extra="forbid"` 约束天然阻断任何试图传 `id` 的请求。

### 用户与鉴权域

**`users`**

| 字段 | 说明 |
|---|---|
| `username` | 唯一，必填；手机号/邮箱注册时自动取该值 |
| `phone` | 可空，唯一（非空时） |
| `email` | 可空，唯一（非空时） |
| `password_hash` | bcrypt 哈希 |
| `wechat_openid` | 可空，唯一（非空时），预留字段，本轮不实现微信登录流程 |

**`refresh_tokens`**

| 字段 | 说明 |
|---|---|
| `user_id` | FK → users |
| `token_hash` | 存储哈希值而非明文 |
| `expires_at` | 过期时间 |
| `revoked_at` | 可空，登出/改密时置为撤销时间 |
| `device_info` | 可空，记录设备/客户端信息，为多端会话管理预留 |

### 宠物域

**`species`**（字典表，用户可自助新增，无需审核）

| 字段 | 说明 |
|---|---|
| `name` | 唯一 |

**`pets`**

| 字段 | 说明 |
|---|---|
| `user_id` | FK → users |
| `species_id` | FK → species |
| `name` | 宠物名称 |
| `morph` | 自由文本，可空（变异描述，组合多样不字典化） |
| `bloodline` | 自由文本，可空（血统描述） |
| `hatch_date` | 可空 |
| `source` | 可空 |
| `owner_note` | 可空 |

不包含状态字段（见 `pet_states`）、不包含护理规则字段（见 `pet_care_rules`）。

**`pet_care_rules`**（一对多，每种护理类型一行）

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `rule_type` | 枚举，如 feed / weigh / mist / uv，新增护理类型只需插入新行 |
| `interval_days` | 周期天数 |
| `note` | 可空 |

**`pet_states`**（正式历史表）

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `status` | 枚举：normal / observe / brumation |
| `started_at` | 状态起始时间 |
| `ended_at` | 可空，NULL 表示当前状态 |
| `note` | 可空 |

### 事件域

**`events`**（单表 + 可空列方案）

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `type` | 枚举：feed / weight / poop / shed / photo |
| `occurred_at` | 事件发生时间 |
| `note` | 可空 |
| `food` | 可空，喂食专属 |
| `amount_gram` | 可空，喂食专属 |
| `weight_gram` | 可空，体重专属 |
| `outcome` | 可空，枚举 ate / refused，喂食专属 |
| `condition` | 可空，枚举 normal / abnormal，排泄/蜕皮专属 |

### 文件域

**`files`**（通用文件记录，与业务表解耦）

| 字段 | 说明 |
|---|---|
| `storage_key` | 存储路径/键 |
| `mime_type` | 允许 image/jpeg、image/png、image/webp |
| `size` | 字节数，上限 10MB |
| `uploaded_by` | FK → users |

**`pet_avatars`**（一对一关联表，正规外键）

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets，唯一 |
| `file_id` | FK → files |

**`event_photos`**（一对多关联表，正规外键）

| 字段 | 说明 |
|---|---|
| `event_id` | FK → events |
| `file_id` | FK → files |

关联方式选择独立关联表（而非通用多态关联表），以保留数据库层面的外键引用完整性约束；代价是每新增一个"可挂图的实体"需要新建一张关联表，但换来不依赖 Service 层自行保证一致性。

### 级联软删除规则

- 软删除 `Pet` 时，同一事务内级联软删除其 `events`、`pet_care_rules`、`pet_states`
- 软删除 `Event` 时，级联软删除其 `event_photos` 关联记录（对应的 `files` 记录本身不删除，仅解除关联）
- 级联操作在 Service 层编排，保证任何时刻都不会查询到"父记录已删除、子记录未删除"的不一致数据

## 统一响应体与业务错误码体系

### 响应 Envelope（`core/response.py`）

```json
{
  "code": 0,
  "message": "success",
  "data": { }
}
```

`code` 是业务消息码，与 HTTP status 分开定义但存在映射关系；HTTP status 仍正常表达语义（200/400/401/403/404/409/500...）。

### 分页封装（`core/pagination.py`）

请求侧：`PaginationParams`，作为 FastAPI 依赖注入（`page` 默认 1，`page_size` 默认 20、上限 100），View 层通过 `Depends(PaginationParams)` 获取后传给 Selector 的通用分页查询函数。

响应侧：`data` 字段内层统一结构：

```json
{
  "items": [ ],
  "total": 137,
  "page": 1,
  "page_size": 20,
  "total_pages": 7
}
```

所有列表类接口必须使用该分页封装，不允许业务视图各自实现分页逻辑。

### 业务错误码体系（`core/errors.py` 的 `ErrorCode(IntEnum)`）

编码规则：千位分业务域，百位分子资源，十位/个位分错误类型。

| 段位 | 域 |
|---|---|
| `0` | 成功 |
| `1000-1999` | 通用/系统错误（未授权、参数校验失败、内部错误） |
| `2000-2999` | User / Auth 域 |
| `3000-3999` | Pet 域（`31xx`=Pet本身，`32xx`=CareRule，`33xx`=PetState，`34xx`=Species） |
| `4000-4999` | Event 域 |
| `5000-5999` | File / Attachment 域 |

错误类型在十位/个位区分，约定：`x0`=NotFound，`x1`=Validation，`x2`=Conflict，`x3`=Forbidden（每个域内按需扩展，不强制每个域都用满四种）。

示例：`3101`=Pet不存在，`3121`=CareRule校验失败，`2020`=用户名已存在（Conflict）。

每个 `ErrorCode` 成员与其默认 HTTP status、默认 message（自然语言文案）在同一处集中维护，View 层和 Service 层都不允许硬编码 message 字符串或 HTTP status。

### 异常传递机制

- `core/errors.py` 定义 `BusinessError(Exception)`，携带 `error_code: ErrorCode` 及可选上下文参数（如涉及的资源 uuid，用于排查但不透出给前端）
- Service/Selector 层发现业务规则被违反时，直接 `raise BusinessError(ErrorCode.XXX)`；业务判断走显式 if/else 主动抛出，而不是用 `try/except` 过滤预期内的情况
- `middlewares/exception.py` 注册全局 exception handler：
  - 捕获 `BusinessError` → 查码表取 HTTP status + message → 组装为 envelope 返回
  - 捕获兜底 `Exception`（未预期的系统异常）→ 生产环境下统一返回预定义的通用系统错误文案（对应 `code=1000` 段），绝不将 `str(exc)` 或堆栈信息透出给前端，防止实现细节穿透到用户层造成信息泄露
- View 层不写 `try/except`，异常处理完全集中在中间件层

## 鉴权与安全机制

### 密码与 Token（`core/security/`）

- `password.py`：bcrypt 哈希与校验
- `jwt.py`：Access Token（JWT，短时效，无状态、不落库）编解码；密钥/算法/过期时长走 `core/config.py` 的 `Settings`
- `token.py`：Refresh Token 生成、哈希后落库（`refresh_tokens` 表）、校验、撤销（登出/改密时撤销该用户全部或指定设备的 refresh token）

Access Token 短时效、无状态；Refresh Token 长时效、落库管理，以支持多端登出、踢下线等会话管理能力。

### 认证依赖注入

View 层通过 FastAPI `Depends(get_current_user)` 从 Access Token 解析出 `user_id`，注入到后续 Service 调用；未认证或 Token 过期统一走 `1000` 段错误码返回。

### 多用户数据隔离（强制点）

- Selector 层所有查询函数必须接收 `user_id` 参数，查询条件强制 join/filter 到该用户，**不提供**无用户过滤的查询函数变体
- Service 层不采用"先查出记录再比对 owner 是否匹配"的模式；越权访问在 Selector 层直接查不到数据（表现为 NotFound），从查询源头杜绝越权，而非依赖上层每次记得检查

### 多端预留

- `users.wechat_openid` 字段预留，本轮不实现微信登录（`wx.login` → code2Session 换 openid）的具体流程
- 所有路由统一挂载在 `/api/v1/` 前缀下，为未来 App 独立版本迭代留出兼容空间（Web 与小程序端预期与后端同步升级，不强依赖版本号隔离）

## 异步数据库层规范

- SQLAlchemy 2.0 `AsyncSession`；开发环境驱动 `aiosqlite`，生产环境驱动 `asyncpg`
- 所有 `relationship()` 声明强制设置 `lazy="raise"`：任何代码在没有显式 `selectinload()`/`joinedload()` 预加载的情况下访问关联属性，立即抛异常，而不是静默发起额外的隐式查询。这是杜绝 N+1 查询和随意隐式 IO 的硬性开发规范
- Selector 层每个查询函数按业务场景自行决定预加载哪些关联，不在 Model 层预定义"加载策略常量"（预加载需求属于调用场景的关注点，不应反向定义在 Model 层，否则容易与实际需要脱钩、造成过度加载）

## 基础设施抽象层（infra/）

本轮只定义接口位置和职责边界，不编写具体实现。

```text
infra/
  cache/
    base.py    # CacheClient 抽象基类：get / set / delete / expire
    redis.py   # 生产实现占位，本轮不写
  storage/
    base.py    # FileStorage 抽象基类：save / delete / exists / get_url
    local.py   # 开发环境本地磁盘实现
    s3.py      # 生产实现占位，本轮不写
  tasks/
    celery.py  # Celery app 实例占位，broker/backend 指向 Redis
    base.py    # 任务基类占位
  clients/     # 第三方 API 客户端占位目录（微信、对象存储等），本轮为空
```

### CacheClient 预留用途

Service 层通过依赖注入使用 `CacheClient` 抽象，具体实现（Redis）本轮不写：

- 缓存：Dashboard 统计结果等计算量较大的派生数据，减少重复计算
- Token 黑名单：配合 Refresh Token 撤销机制，使 Access Token 也能提前失效
- 限流：配合 `middlewares/rate_limit.py` 做接口级 rate limiting
- Celery broker/backend：未来异步任务队列的底层依赖（Redis 同时承担缓存与消息队列职责）

### 文件上传约束

- 单文件大小上限 10MB
- 允许 MIME 类型：`image/jpeg`、`image/png`、`image/webp`（本轮不支持视频）
- 本地存储路径规则：`{user_uuid}/{yyyy}/{mm}/{file_uuid}.{ext}`，按用户与年月分目录，避免单目录文件过多，便于按用户维度清理/迁移

## 序列化规范与字段命名

- API 请求/响应 JSON 统一使用 **snake_case**（与数据库、Python 代码一致）；前端接入本轮后端时自行做命名转换或改造领域模型，后端 Schema 层不做 camelCase 双向别名转换
- 所有请求 Schema 继承 `BaseRequestSchema`（`schemas/base.py`），统一设置 `extra="forbid"`：任何未声明字段（包括裸 `id`）直接触发 422 校验错误，不需要手写字段黑名单校验逻辑
- 请求 Schema 永不声明 `id`/`uuid` 作为可写字段；更新操作的目标资源标识从 URL 路径参数获取，不从请求体获取
- 响应 Schema 只暴露 `uuid`，不暴露数据库自增 `id`；`model_validate()` 从 Service 传入的 ORM 对象转换生成响应体
- Selector 返回的原始 ORM 数据不直接透出给 View 层，必须经过 Schema 转换

## 本轮功能点清单（API 端点范围）

### 认证域

- 注册（用户名 / 手机号 / 邮箱三种注册方式，手机号或邮箱注册时 `username` 自动取该值）
- 登录（返回 access token + refresh token）
- 刷新 token
- 登出（撤销 refresh token）

### 宠物域

- 宠物 CRUD：列表（分页）、详情、创建、更新、软删除
- 物种字典：查询列表、用户自助新增（记录宠物时输入即新建）
- 护理规则：增删改查（按 `rule_type` 维度管理）
- 宠物状态：新增状态记录（结束上一条、开启新一条）、查看状态历史

### 事件域

- 事件创建（feed / weight / poop / shed / photo 五种类型）
- 事件列表（分页，按宠物 / 类型筛选）
- 事件详情
- 事件软删除
- 事件关联图片上传（`event_photos`）

### 文件域

- 通用文件上传接口（落库 `files` + 调用 `infra/storage` 抽象）
- 宠物头像上传/更新（`pet_avatars`）

### 派生计算域（不建表，Service 层实时计算）

- CareTask 列表（今日待办，根据最近事件 + 护理规则实时计算提醒等级：正常/推荐/超期）
- Dashboard 概览统计（近 30 天记录数、喂食次数、体重变化、异常事件数、整体状态摘要）

本清单为本轮设计范围，后续根据实际开发情况和业务需求调整，不作为最终不可变契约。

## 未决问题与后续设计

以下内容明确不在本轮设计范围内，留待后续单独设计：

- 微信小程序登录（`wx.login` → code2Session）具体实现
- 对象存储（S3/OSS）具体实现
- Celery 具体任务与调度逻辑
- Redis 缓存/黑名单/限流的具体实现
- 数据库迁移工具选型与迁移脚本（切换到 PostgreSQL 时）
- 前端命名规范改造与真实 API 接入
- 视频类型的事件附件支持

