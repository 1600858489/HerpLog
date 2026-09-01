# 后端宠物域实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有认证和核心基础设施之上，实现面向个人玩家的结构化宠物管理 API，支持个体管理、扁平管理单元、批量目标、分类资料、谱系来源、成长阶段和转移历史。

**Architecture:** 使用横向分层：`views → schemas → services/selectors → models`。用户私有数据均由当前用户内部 `user_id` 隔离，外部资源只使用 UUID；Selector 只读且显式预加载关系，Service 负责写入、状态转换、事务和软删除。仅对 PersonalSpecies、PersonalGene、IdentificationTag 等字段和生命周期一致的资源抽取有限通用 CRUD，宠物转移、清空并删除、阶段切换、来源谱系等特殊流程保持专用 Service。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 AsyncSession, SQLite + aiosqlite, Pydantic v2, pytest, pytest-asyncio, httpx.

## Global Constraints

- 直接在当前 `master` 分支开发，不创建 worktree、不使用 subagent、不推送远端。
- 后端从 `backend` 目录运行：`uv run --project .. uvicorn main:app`、`uv run --project .. pytest -q`。
- `backend/main.py` 使用 `app.*` 导入；`backend/app/` 内部使用包内相对导入；标准库和第三方库使用绝对导入。
- 所有业务模型继承 `IDMixin`、`TimestampMixin`、`SoftDeleteMixin`；内部自增 `id` 只用于数据库关系，API 只暴露 `uuid`。
- 所有关系使用 `lazy="raise"`；Selector 按场景显式使用 `selectinload()` 或 `joinedload()`。
- 所有私有资源查询必须绑定当前用户；跨用户访问表现为 NotFound，不在 Service 中先查出再比较 owner。
- 请求 Schema 继承 `BaseRequestSchema`，使用 `extra="forbid"`；请求体不声明或接受 `id`、`uuid`、`user_id`。
- API 请求/响应使用 snake_case；所有列表使用 `PaginationParams` 和 `PaginationData`；所有响应使用 `ResponseEnvelope`。
- 业务错误使用已有 `BusinessError` 和集中 `ErrorCode`，新增 Pet 域错误码按 31xx–39xx 分配。
- 预期业务错误通过显式条件处理，不用 `try/except` 过滤；未预期错误由全局 handler 处理且不得向客户端泄露 Python 文本或 traceback。
- 个人分类数据不建立全局公共字典；未来社区生态使用独立模型。
- 管理单元保持扁平且可选；宠物不取名时使用系统生成且用户范围唯一的 `pet_code`。
- 文件上传和事件记录属于后续计划；本计划只为事件域提供管理单元当前成员的只读接口。

---

## 文件结构映射

- Create: `backend/app/core/crud/base_selector.py` — 有限的用户范围通用只读查询模板。
- Create: `backend/app/core/crud/base_service.py` — 有限的普通创建/更新/软删除模板。
- Create: `backend/app/core/crud/__init__.py` — 通用 CRUD 公共导出。
- Create: `backend/app/models/pet_domain.py` — 宠物域所有 ORM 模型和枚举。
- Modify: `backend/app/models/__init__.py` — 导出宠物域模型。
- Create: `backend/app/schemas/pet.py` — 宠物域请求/响应 Serializer。
- Modify: `backend/app/schemas/__init__.py` — 导出宠物域 Schema。
- Create: `backend/app/selectors/pet.py` — 宠物域只读查询与分页。
- Modify: `backend/app/selectors/__init__.py` — 导出宠物域 Selector 公共接口。
- Create: `backend/app/services/pet.py` — 宠物创建、更新、删除和关联校验。
- Create: `backend/app/services/classification.py` — 物种、基因、识别标签 CRUD。
- Create: `backend/app/services/management.py` — 管理单元、类型和清空删除。
- Create: `backend/app/services/lifecycle.py` — 管理单元分配、转移、成长阶段、来源谱系。
- Modify: `backend/app/services/__init__.py` — 导出宠物域 Service 公共接口。
- Modify: `backend/app/core/errors.py` — 增加 Pet 域错误码和错误文案。
- Create: `backend/app/views/pet.py` — 宠物、分类和管理单元路由。
- Modify: `backend/app/views/__init__.py` — 导出宠物域 Router。
- Modify: `backend/main.py` — 挂载 `/api/v1/pets` 等路由。
- Modify: `backend/tests/conftest.py` — 导入宠物域模型，确保测试建表。
- Create: `backend/tests/test_pet_models.py` — ORM、约束和关系策略测试。
- Create: `backend/tests/test_pet_schemas.py` — Serializer/Deserializer 测试。
- Create: `backend/tests/test_pet_selectors.py` — 用户隔离、分页、预加载测试。
- Create: `backend/tests/test_pet_services.py` — 分类、管理单元、宠物和生命周期 Service 测试。
- Create: `backend/tests/test_pet_api.py` — 宠物域 API 端到端测试。
- Modify: `README.md` — 补充当前已实现的宠物 API。

## 资源和错误码接口

### Pet 域错误码

在 `backend/app/core/errors.py` 中增加并集中配置：

```text
3101 PET_NOT_FOUND
3111 PET_VALIDATION_FAILED
3121 PET_CONFLICT
3131 PET_FORBIDDEN
3141 PET_INVALID_STATE

3401 SPECIES_NOT_FOUND
3411 SPECIES_VALIDATION_FAILED
3421 SPECIES_CONFLICT

3501 GENE_NOT_FOUND
3511 GENE_VALIDATION_FAILED
3521 GENE_CONFLICT

3601 IDENTIFICATION_TAG_NOT_FOUND
3611 IDENTIFICATION_TAG_VALIDATION_FAILED
3621 IDENTIFICATION_TAG_CONFLICT

3701 MANAGEMENT_UNIT_NOT_FOUND
3711 MANAGEMENT_UNIT_VALIDATION_FAILED
3721 MANAGEMENT_UNIT_CONFLICT
3731 MANAGEMENT_UNIT_FORBIDDEN
3741 MANAGEMENT_UNIT_INVALID_STATE

3801 MANAGEMENT_UNIT_TYPE_NOT_FOUND
3811 MANAGEMENT_UNIT_TYPE_VALIDATION_FAILED
3821 MANAGEMENT_UNIT_TYPE_CONFLICT
3831 MANAGEMENT_UNIT_TYPE_FORBIDDEN

3901 ORIGIN_OR_ASSIGNMENT_NOT_FOUND
3911 ORIGIN_OR_ASSIGNMENT_VALIDATION_FAILED
3921 ORIGIN_OR_ASSIGNMENT_CONFLICT
3931 ORIGIN_OR_ASSIGNMENT_FORBIDDEN
3941 ORIGIN_OR_ASSIGNMENT_INVALID_STATE
```

### API 资源范围

```text
/api/v1/pets
/api/v1/species
/api/v1/genes
/api/v1/identification-tags
/api/v1/management-unit-types
/api/v1/management-units
/api/v1/pets/{pet_uuid}/management-assignments
/api/v1/pets/{pet_uuid}/life-stages
/api/v1/pets/{pet_uuid}/origins
```

---

### Task 1: 增加有限通用 CRUD 抽象

**Files:**
- Create: `backend/app/core/crud/base_selector.py`
- Create: `backend/app/core/crud/base_service.py`
- Create: `backend/app/core/crud/__init__.py`
- Create: `backend/tests/test_crud.py`

**Interfaces:**
- `BaseSelector[ModelT]`：提供用户范围 UUID 查询、分页查询的可复用协议。
- `BaseCRUDService[ModelT, CreateSchemaT, UpdateSchemaT]`：提供普通创建、更新和软删除的生命周期模板。
- 基类不猜测用户归属字段、不猜测预加载、不自动反射生成路由；具体资源通过显式参数或覆写钩子提供这些差异。

- [ ] **Step 1: Write the failing test**

```python
from uuid import UUID

from backend.app.core.crud import BaseCRUDService, BaseSelector


def test_crud_abstractions_define_explicit_extension_points() -> None:
    assert BaseSelector.__parameters__
    assert BaseCRUDService.__parameters__
    assert hasattr(BaseSelector, "get_by_uuid")
    assert hasattr(BaseSelector, "list_paginated")
    assert hasattr(BaseCRUDService, "create")
    assert hasattr(BaseCRUDService, "update")
    assert hasattr(BaseCRUDService, "soft_delete")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project .. pytest tests/test_crud.py -q`

Expected: FAIL because `app.core.crud` does not exist。

- [ ] **Step 3: Implement the minimal abstractions**

`BaseSelector` 接受显式 `model`, `owner_column` 和 `load_options`，将 `deleted_at IS NULL`、owner 过滤、UUID 过滤、offset/limit 和 count 查询封装起来；不访问关系，不返回 Schema。

`BaseCRUDService` 只提供依赖 `session`、`selector`、`model` 的普通操作模板；提供显式 `build_model` 和 `apply_update` 方法供业务 Service 实现。软删除只设置 `deleted_at=utc_now()`，不代替宠物域的级联或状态操作。

两个基类都使用完整泛型和公开类型注解，不使用 `Any` 承载核心业务数据。基类不捕获数据库异常、不创建 HTTP 响应。

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project .. pytest tests/test_crud.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/core/crud tests/test_crud.py
git commit -m "feat: 增加有限通用 CRUD 抽象"
```

---

### Task 2: 宠物域 ORM 模型和错误码

**Files:**
- Create: `backend/app/models/pet_domain.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/core/errors.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_pet_models.py`

**Interfaces:**
- Produces枚举：`PetSex`、`ManagementUnitTypeScope`、`PetOriginType`、`PetParentRole`、`ConfidenceLevel`、`InheritanceMode`。
- Produces模型：`PersonalSpecies`、`PersonalGene`、`IdentificationTag`、`Pet`、`PetGene`、`PetIdentificationTag`、`ManagementUnitType`、`ManagementUnit`、`PetManagementAssignment`、`PetLifeStage`、`PetOrigin`。
- 每个模型继承公共 Mixin；所有关系 `lazy="raise"`；所有用户私有模型包含 `user_id` 外键。

- [ ] **Step 1: Write failing model tests**

```python
from datetime import datetime, timezone

from sqlalchemy import select

from app.models import (
    IdentificationTag,
    ManagementUnit,
    ManagementUnitType,
    PersonalGene,
    PersonalSpecies,
    Pet,
    PetLifeStage,
)


async def test_pet_domain_models_support_optional_classification_and_unnamed_pets(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        species = PersonalSpecies(user_id=1, common_name="豹纹守宫")
        session.add(species)
        await session.flush()
        pet = Pet(user_id=1, species_id=species.id, sex="unknown")
        session.add(pet)
        await session.commit()
        await session.refresh(pet)
        assert pet.name is None
        assert pet.pet_code
        assert pet.uuid


async def test_management_unit_type_and_history_models_have_relationships(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        unit_type = ManagementUnitType(name="生态缸", is_system=False, user_id=1)
        session.add(unit_type)
        await session.flush()
        unit = ManagementUnit(user_id=1, type_id=unit_type.id, unit_code="TANK-001")
        session.add(unit)
        await session.commit()
        assert unit.uuid
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_models.py -q`

Expected: FAIL because the pet-domain model module and tables are missing。

- [ ] **Step 3: Implement the models**

使用 SQLAlchemy typed mapping：

- `PersonalSpecies`：完整可选分类字段 `kingdom`、`phylum`、`class_name`、`order_name`、`family`、`genus`、`species_name`、`subspecies`，`common_name` 必填，`(user_id, common_name)` 唯一。
- `PersonalGene`：`name` 必填，phenotype/genotype/inheritance_mode/note 可选，`(user_id, name)` 唯一。
- `IdentificationTag`：`name` 必填，`(user_id, name)` 唯一。
- `Pet`：`user_id`、`species_id`、`pet_code`、可选 name、固定 sex、identification_note、owner_note；`(user_id, pet_code)` 唯一；不保存 `current_management_unit_id`。
- `PetGene`、`PetIdentificationTag`：两个外键的复合主键或复合唯一约束。
- `ManagementUnitType`：系统类型 `user_id=NULL`、自定义类型绑定用户；`is_system` 与 user_id 组合表达范围。
- `ManagementUnit`：`user_id`、`type_id`、`unit_code`、可选 name/note，`(user_id, unit_code)` 唯一。
- `PetManagementAssignment`：pet_id、management_unit_id、started_at、ended_at、可选 life_stage/transfer_reason/note。
- `PetLifeStage`：pet_id、stage、started_at、ended_at、change_reason、note。
- `PetOrigin`：pet_id、origin_type、parent_role、可选 parent_pet_id/breeder_name/external_name/genetic_note/confidence/note。

父本/母本关联使用同一 `Pet` 表的外键；关系声明使用 `foreign_keys` 明确自引用方向，并设置 `lazy="raise"`。不要使用 ORM cascade 代替 Service 软删除。

模型导出必须通过 `models/__init__.py`；测试 fixture 在建表前导入 `app.models`，确保 metadata 注册所有宠物域表。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_models.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/models app/core/errors.py tests/conftest.py tests/test_pet_models.py
git commit -m "feat: 增加宠物域数据模型"
```

---

### Task 3: 宠物域请求/响应 Serializer

**Files:**
- Create: `backend/app/schemas/pet.py`
- Modify: `backend/app/schemas/__init__.py`
- Create: `backend/tests/test_pet_schemas.py`

**Interfaces:**
- Produces分类项 Schema：`SpeciesCreateRequest`、`SpeciesUpdateRequest`、`SpeciesResponse`、`GeneCreateRequest`、`GeneUpdateRequest`、`GeneResponse`、`TagCreateRequest`、`TagUpdateRequest`、`TagResponse`。
- Produces管理单元 Schema：`ManagementUnitTypeCreateRequest`、`ManagementUnitTypeUpdateRequest`、`ManagementUnitTypeResponse`、`ManagementUnitCreateRequest`、`ManagementUnitUpdateRequest`、`ManagementUnitResponse`。
- Produces宠物 Schema：`PetCreateRequest`、`PetUpdateRequest`、`PetResponse`、`PetListResponse`。
- Produces历史 Schema：`AssignmentCreateRequest`、`AssignmentMoveRequest`、`AssignmentResponse`、`LifeStageCreateRequest`、`LifeStageUpdateRequest`、`LifeStageResponse`、`OriginCreateRequest`、`OriginUpdateRequest`、`OriginResponse`。
- 所有请求继承 `BaseRequestSchema`；所有响应只包含 uuid，不包含 id/user_id/password 等内部字段。

- [ ] **Step 1: Write failing schema tests**

```python
import pytest
from pydantic import ValidationError

from app.schemas.pet import PetCreateRequest, SpeciesCreateRequest


def test_pet_create_requires_species_but_allows_unnamed_pet() -> None:
    request = PetCreateRequest(species_uuid="00000000-0000-0000-0000-000000000001")
    assert request.name is None
    assert request.sex == "unknown"


def test_pet_request_forbids_internal_identifiers() -> None:
    with pytest.raises(ValidationError):
        PetCreateRequest(species_uuid="00000000-0000-0000-0000-000000000001", id=1)
    with pytest.raises(ValidationError):
        PetCreateRequest(species_uuid="00000000-0000-0000-0000-000000000001", user_id=1)


def test_species_scientific_fields_are_optional() -> None:
    request = SpeciesCreateRequest(common_name="豹纹守宫")
    assert request.scientific_name is None
    assert request.kingdom is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_schemas.py -q`

Expected: FAIL because pet-domain schemas are missing。

- [ ] **Step 3: Implement typed request and response schemas**

UUID 输入字段使用 `UUID` 类型；`PetCreateRequest.species_uuid` 必填，`sex` 默认 `unknown`；name、pet_code、classification、gene、tag、management unit、origin 和 life stage 均按设计可选。科学分类字段不设置必填链式校验。

列表响应只返回 `PetListResponse` 的必要信息：uuid、pet_code、name、species 摘要、sex、current_management_unit 摘要、identification_tags；详情 Schema 才包含基因、来源、成长阶段和分配历史。请求 Schema 不允许 id、uuid、user_id 等额外字段。

`UserResponse` 风格的 ORM 序列化使用 `ConfigDict(from_attributes=True)`；不要让响应 Schema 继承 `BaseRequestSchema`。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_schemas.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/schemas tests/test_pet_schemas.py
git commit -m "feat: 定义宠物域序列化器"
```

---

### Task 4: Pet Selector、分类 Selector 和用户隔离

**Files:**
- Create: `backend/app/selectors/pet.py`
- Modify: `backend/app/selectors/__init__.py`
- Create: `backend/tests/test_pet_selectors.py`

**Interfaces:**
- `get_species_by_uuid(session, user_id, species_uuid) -> PersonalSpecies | None`
- `list_species(session, user_id, params, keyword) -> tuple[list[PersonalSpecies], int]`
- `get_gene_by_uuid(session, user_id, gene_uuid) -> PersonalGene | None`
- `get_tag_by_uuid(session, user_id, tag_uuid) -> IdentificationTag | None`
- `get_management_unit_by_uuid(session, user_id, unit_uuid) -> ManagementUnit | None`
- `get_pet_by_uuid(session, user_id, pet_uuid, detail=False) -> Pet | None`
- `list_pets(session, user_id, params, filters) -> tuple[list[Pet], int]`
- `list_pet_assignments(session, user_id, pet_uuid, params) -> tuple[list[PetManagementAssignment], int]`
- `list_pet_life_stages(session, user_id, pet_uuid, params) -> tuple[list[PetLifeStage], int]`
- `list_pet_origins(session, user_id, pet_uuid, params) -> tuple[list[PetOrigin], int]`
- `get_active_pet_ids_by_management_unit(session, user_id, management_unit_uuid) -> list[int]`

- [ ] **Step 1: Write failing selector tests**

```python
from uuid import uuid4

from app.models import PersonalSpecies, Pet
from app.selectors.pet import get_pet_by_uuid, list_pets
from app.schemas.pet import PetListFilters
from app.core.pagination import PaginationParams


async def test_pet_selector_cannot_return_another_users_pet(async_session_factory) -> None:
    async with async_session_factory() as session:
        species = PersonalSpecies(user_id=1, common_name="龟")
        session.add(species)
        await session.flush()
        pet = Pet(user_id=1, species_id=species.id, sex="unknown")
        session.add(pet)
        await session.commit()
        assert await get_pet_by_uuid(session, 2, pet.uuid) is None


async def test_pet_list_returns_pagination_count(async_session_factory) -> None:
    async with async_session_factory() as session:
        species = PersonalSpecies(user_id=1, common_name="龟")
        session.add(species)
        await session.flush()
        session.add_all([Pet(user_id=1, species_id=species.id, sex="unknown") for _ in range(3)])
        await session.commit()
        items, total = await list_pets(
            session, 1, PaginationParams(page=1, page_size=2), PetListFilters()
        )
        assert len(items) == 2
        assert total == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_selectors.py -q`

Expected: FAIL because selectors are missing。

- [ ] **Step 3: Implement selectors**

每个用户私有查询的 where 条件同时包含 owner 和 `deleted_at IS NULL`；UUID 查询直接在 SQL 中绑定两个条件。宠物列表按 `created_at DESC, id DESC` 稳定排序，支持 species、sex、management_unit、assigned/unassigned、tag 和 pet_code/name 关键词筛选。

列表查询显式加载：

- Pet list：`species`、当前有效 assignment、identification tags
- Pet detail：`species`、genes、tags、origins、life_stages、assignments
- Assignment history：management unit 和 management unit type
- 分类列表：不加载宠物反向集合

管理单元类型查询只返回未删除系统类型或当前用户自定义类型。`get_active_pet_ids_by_management_unit` 通过管理单元 owner、宠物 owner、assignment 当前有效条件联合过滤，返回内部 pet id 供事件域保存快照，不暴露给 API。

Selector 内不 commit、不写模型、不做 Serializer 转换；所有公共函数从 `selectors/__init__.py` 导出。测试验证未显式预加载的关系访问会触发 `lazy="raise"`。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_selectors.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/selectors tests/test_pet_selectors.py
 git commit -m "feat: 增加宠物域隔离检索"
```

---

### Task 5: 分类资料 Service

**Files:**
- Create: `backend/app/services/classification.py`
- Modify: `backend/app/services/__init__.py`
- Modify: `backend/app/core/errors.py`
- Create: `backend/tests/test_pet_classification_services.py`

**Interfaces:**
- `create_species(session, user_id, request) -> PersonalSpecies`
- `update_species(session, user_id, species_uuid, request) -> PersonalSpecies`
- `soft_delete_species(session, user_id, species_uuid) -> None`
- `create_gene/update_gene/soft_delete_gene`
- `create_tag/update_tag/soft_delete_tag`
- 所有写入属于当前用户，所有冲突抛出对应 `BusinessError`。

- [ ] **Step 1: Write failing service tests**

```python
import pytest

from app.core.errors import BusinessError, ErrorCode
from app.schemas.pet import SpeciesCreateRequest
from app.services.classification import create_species


async def test_species_is_private_and_duplicate_name_is_rejected(async_session_factory) -> None:
    async with async_session_factory() as session:
        first = await create_species(session, 1, SpeciesCreateRequest(common_name="龟"))
        await session.commit()
        assert first.common_name == "龟"
        with pytest.raises(BusinessError) as error:
            await create_species(session, 1, SpeciesCreateRequest(common_name="龟"))
        assert error.value.error_code == ErrorCode.SPECIES_CONFLICT


async def test_different_users_can_have_same_species_name(async_session_factory) -> None:
    async with async_session_factory() as session:
        first = await create_species(session, 1, SpeciesCreateRequest(common_name="龟"))
        second = await create_species(session, 2, SpeciesCreateRequest(common_name="龟"))
        await session.commit()
        assert first.uuid != second.uuid
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_classification_services.py -q`

Expected: FAIL because classification Service is missing。

- [ ] **Step 3: Implement classification Service**

使用 Selector 查询用户范围冲突；normalize text 后创建/更新。删除已被宠物或基因关联使用的分类项时，不物理删除，只设置 `deleted_at`，并在后续创建关联时拒绝已删除项。基因和标签按同样模式实现，但保持各自错误码和 Schema，不创建过度通用的动态 Service。

Service 负责 commit，业务 View 不管理事务。跨模块只从 `selectors`/`services` 的 `__init__.py` 导入。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_classification_services.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/services/classification.py app/services/__init__.py app/core/errors.py tests/test_pet_classification_services.py
git commit -m "feat: 实现用户私有宠物分类资料"
```

---

### Task 6: 管理单元和类型 Service

**Files:**
- Create: `backend/app/services/management.py`
- Create: `backend/tests/test_management_services.py`

**Interfaces:**
- `create_management_unit_type(session, user_id, request) -> ManagementUnitType`
- `update_management_unit_type(session, user_id, type_uuid, request) -> ManagementUnitType`
- `soft_delete_management_unit_type(session, user_id, type_uuid) -> None`
- `create_management_unit(session, user_id, request) -> ManagementUnit`
- `update_management_unit(session, user_id, unit_uuid, request) -> ManagementUnit`
- `clear_and_delete_management_unit(session, user_id, unit_uuid) -> None`
- `get_management_unit_members(session, user_id, unit_uuid, params) -> tuple[list[Pet], int]`

- [ ] **Step 1: Write failing tests**

```python
import pytest
from datetime import timedelta

from app.core.errors import BusinessError, ErrorCode
from app.models import ManagementUnit, ManagementUnitType, PersonalSpecies, Pet, PetManagementAssignment, User
from app.schemas.pet import ManagementUnitTypeUpdateRequest
from app.services.management import clear_and_delete_management_unit, update_management_unit_type
from app.utils.datetime import utc_now


async def test_system_management_unit_type_cannot_be_modified(async_session_factory) -> None:
    async with async_session_factory() as session:
        system_type = ManagementUnitType(name="生态缸", is_system=True, user_id=None)
        session.add(system_type)
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await update_management_unit_type(
                session, 1, system_type.uuid, ManagementUnitTypeUpdateRequest(name="修改")
            )
        assert error.value.error_code == ErrorCode.MANAGEMENT_UNIT_TYPE_FORBIDDEN


async def test_clear_and_delete_leaves_pets_unassigned(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        species = PersonalSpecies(user=user, common_name="龟")
        unit_type = ManagementUnitType(user=user, name="龟池", is_system=False)
        session.add_all([user, species, unit_type])
        await session.flush()
        unit = ManagementUnit(user_id=user.id, type_id=unit_type.id, unit_code="POOL-001")
        pet = Pet(user_id=user.id, species_id=species.id, pet_code="PET-001", sex="unknown")
        session.add_all([unit, pet])
        await session.flush()
        session.add(
            PetManagementAssignment(
                pet_id=pet.id,
                management_unit_id=unit.id,
                started_at=utc_now() - timedelta(days=1),
            )
        )
        await session.commit()
        await clear_and_delete_management_unit(session, user.id, unit.uuid)
        assert pet.deleted_at is None
```

测试文件需要定义完整的 `create_management_unit_for_test` 和 `create_pet_assigned_for_test` fixture/helper，不能使用未定义占位符；helper 只负责准备真实模型，不写入生产代码。

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_management_services.py -q`

Expected: FAIL because management Service is missing。

- [ ] **Step 3: Implement management Service**

系统类型只能查询和选择，不能由普通用户修改/软删除；用户自定义类型允许修改和软删除。类型名称按系统全局或用户范围检查冲突。

管理单元创建必须校验 type 属于系统范围或当前用户；unit_code 由 Service 生成并保证用户范围唯一，显式传入时也必须检查冲突。普通删除接口不调用清空逻辑；唯一删除流程 `clear_and_delete_management_unit` 在一个事务中：加载当前用户单元 → 结束所有有效 assignment → 设置管理单元 deleted_at → 保留宠物和全部历史。

如果清空过程中任何业务校验失败，Service 不提交部分状态。成员列表只返回当前有效 assignment 的宠物，所有查询绑定用户。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_management_services.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/services/management.py tests/test_management_services.py
git commit -m "feat: 实现扁平管理单元服务"
```

---

### Task 7: 宠物核心 Service 和生命周期 Service

**Files:**
- Create: `backend/app/services/pet.py`
- Create: `backend/app/services/lifecycle.py`
- Modify: `backend/app/services/__init__.py`
- Create: `backend/tests/test_pet_services.py`

**Interfaces:**
- `create_pet(session, user_id, request) -> Pet`
- `update_pet(session, user_id, pet_uuid, request) -> Pet`
- `soft_delete_pet(session, user_id, pet_uuid) -> None`
- `move_pet(session, user_id, pet_uuid, request) -> PetManagementAssignment`
- `remove_pet_from_management_unit(session, user_id, pet_uuid, ended_at) -> None`
- `create_life_stage(session, user_id, pet_uuid, request) -> PetLifeStage`
- `end_life_stage(session, user_id, pet_uuid, stage_uuid, ended_at) -> PetLifeStage`
- `create_origin/update_origin/soft_delete_origin`
- `create_assignment(session, user_id, pet_uuid, request) -> PetManagementAssignment`

- [ ] **Step 1: Write failing Service tests**

```python
from datetime import timedelta

import pytest

from app.core.errors import BusinessError, ErrorCode
from app.models import ManagementUnit, ManagementUnitType, PersonalSpecies, Pet, PetManagementAssignment, User
from app.schemas.pet import AssignmentMoveRequest, PetCreateRequest
from app.services.lifecycle import move_pet
from app.services.pet import create_pet, soft_delete_pet
from app.utils.datetime import utc_now


async def test_create_pet_allows_no_name_and_no_management_unit(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        species = PersonalSpecies(user=user, common_name="龟")
        session.add_all([user, species])
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        assert pet.name is None
        assert pet.pet_code


async def test_pet_delete_soft_deletes_history(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        species = PersonalSpecies(user=user, common_name="龟")
        session.add_all([user, species])
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        unit_type = ManagementUnitType(user_id=user.id, name="龟池", is_system=False)
        session.add(unit_type)
        await session.flush()
        unit = ManagementUnit(user_id=user.id, type_id=unit_type.id, unit_code="POOL-001")
        session.add(unit)
        await session.flush()
        assignment = PetManagementAssignment(
            pet_id=pet.id,
            management_unit_id=unit.id,
            started_at=utc_now() - timedelta(days=1),
        )
        session.add(assignment)
        await session.commit()
        await soft_delete_pet(session, user.id, pet.uuid)
        assert pet.deleted_at is not None
        assert assignment.deleted_at is not None


async def test_overlapping_management_assignment_is_rejected(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        species = PersonalSpecies(user=user, common_name="龟")
        first_type = ManagementUnitType(user=user, name="龟池一", is_system=False)
        second_type = ManagementUnitType(user=user, name="龟池二", is_system=False)
        session.add_all([user, species, first_type, second_type])
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        first_unit = ManagementUnit(user_id=user.id, type_id=first_type.id, unit_code="POOL-001")
        second_unit = ManagementUnit(user_id=user.id, type_id=second_type.id, unit_code="POOL-002")
        session.add_all([first_unit, second_unit])
        await session.flush()
        session.add(
            PetManagementAssignment(
                pet_id=pet.id,
                management_unit_id=first_unit.id,
                started_at=utc_now() - timedelta(days=1),
            )
        )
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await move_pet(
                session,
                user.id,
                pet.uuid,
                AssignmentMoveRequest(management_unit_uuid=first_unit.uuid),
            )
        assert error.value.error_code == ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE
```

测试中所有 helper 必须在测试文件内完整定义或改为 pytest fixture；不得保留 `_for_test` 未定义调用。测试需使用真实模型和临时 SQLite，不 mock Selector/数据库。

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_services.py -q`

Expected: FAIL because pet/lifecycle Service is missing。

- [ ] **Step 3: Implement Pet Service**

创建宠物时：

1. 通过 UUID Selector 校验 species 属于当前用户且未删除
2. 校验可选 genes/tags/management unit 属于当前用户且未删除
3. 生成用户范围唯一 `pet_code`
4. 创建 Pet，默认 sex 为 unknown
5. 按请求可选创建初始 stage、assignment、origin
6. 同一事务提交

更新基础资料只修改 name、pet_code、species、sex、identification_note、owner_note；管理单元、基因、标签、阶段和来源走专用接口。删除宠物在同一事务中软删除 assignment、life stage、origin、pet_gene、pet_tag 关联记录，宠物本身保留。

### Lifecycle Service 规则

- 添加/转移 assignment 前校验 Pet 和目标 unit 同属当前用户且有效
- 结束当前 assignment，再创建新 assignment
- 同一宠物有效 assignment 不得重叠，空窗期允许
- remove 只结束当前 assignment，宠物保留为未分配
- 阶段切换结束旧阶段并创建新阶段，阶段历史独立于 assignment
- 来源记录允许 self_bred/breeder/purchased/unknown
- parent_pet_id 只能关联当前用户有效宠物，不能是自身；商家来源不强制父母关系
- `parent_role` 表达 sire/dam/unspecified，不在 Pet 表创建 father_id/mother_id

所有时间比较使用 UTC aware datetime。所有状态变更由单一 Service 事务边界完成，不通过异常捕获判断重叠或不存在。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_services.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/services/pet.py app/services/lifecycle.py app/services/__init__.py tests/test_pet_services.py
git commit -m "feat: 实现宠物个体与生命周期服务"
```

---

### Task 8: 宠物域 View、路由和分页响应

**Files:**
- Create: `backend/app/views/pet.py`
- Modify: `backend/app/views/__init__.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_pet_api.py`

**Interfaces:**
- Produces `pet_router`，挂载到 `/api/v1`。
- View 使用 `Depends(get_current_user)` 和 `Depends(get_db_session)`；只解析 Schema、调用 Service/Selector、序列化响应和构造 envelope。
- 不在 View 中写业务判断、owner 比较、事务或 `try/except`。

- [ ] **Step 1: Write failing API tests**

```python
async def test_create_and_list_unnamed_pet(client) -> None:
    species = await create_species_via_api(client, "豹纹守宫")
    response = await client.post(
        "/api/v1/pets",
        headers=auth_headers,
        json={"species_uuid": species["uuid"]},
    )
    assert response.status_code == 201
    assert response.json()["data"]["name"] is None
    assert response.json()["data"]["pet_code"]
    assert "id" not in response.text


async def test_pet_list_is_paginated(client) -> None:
    response = await client.get(
        "/api/v1/pets?page=1&page_size=20",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["page"] == 1
    assert "items" in response.json()["data"]
```

测试文件必须定义完整的认证注册/登录 fixture 和 `create_species_via_api`、`auth_headers`，不使用省略号或未定义 helper。

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project .. pytest tests/test_pet_api.py -q`

Expected: FAIL because pet router is not mounted。

- [ ] **Step 3: Implement View and route registration**

实现以下端点并为每个端点声明明确 response_model：

```text
GET/POST/PATCH/DELETE /api/v1/pets
GET /api/v1/pets/{pet_uuid}
GET/POST/PATCH/DELETE /api/v1/species
GET/POST/PATCH/DELETE /api/v1/genes
GET/POST/PATCH/DELETE /api/v1/identification-tags
GET/POST/PATCH/DELETE /api/v1/management-unit-types
GET/POST/PATCH/DELETE /api/v1/management-units
POST /api/v1/management-units/{unit_uuid}/clear-and-delete
GET /api/v1/pets/{pet_uuid}/management-assignments
POST /api/v1/pets/{pet_uuid}/management-assignments/move
POST /api/v1/pets/{pet_uuid}/management-assignments/remove
GET/POST /api/v1/pets/{pet_uuid}/life-stages
PATCH/POST /api/v1/pets/{pet_uuid}/life-stages/{stage_uuid}
GET/POST/PATCH/DELETE /api/v1/pets/{pet_uuid}/origins
```

列表接口将 Selector 返回的 `(items, total)` 通过 `build_pagination` 转为 `PaginationData`，每个 ORM 对象先经过对应 Response Schema。状态操作返回更新后的历史记录或 `None` envelope。

挂载方式：`app.include_router(pet_router, prefix="/api/v1", tags=["pets"])`，入口从 `app.views` 公共导出导入。

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project .. pytest tests/test_pet_api.py -q`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/views app/main.py main.py tests/test_pet_api.py
 git commit -m "feat: 暴露宠物域版本化 API"
```

注意实际文件为 `backend/main.py`，提交命令不得加入不存在的 `app/main.py`；应使用：

```bash
git add app/views ../main.py tests/test_pet_api.py
```

---

### Task 9: 宠物域集成验收和文档

**Files:**
- Modify: `README.md`
- Modify: `backend/tests/test_pet_api.py`
- Modify: `backend/tests/test_pet_selectors.py`
- Modify: `backend/tests/test_pet_services.py`

**Interfaces:**
- 产出可从 `backend` 目录启动的宠物域 API。
- 完成跨用户隔离、未命名宠物、分页、分类资料、管理单元清空删除、转移历史、成长阶段、来源谱系和安全错误响应验收。

- [ ] **Step 1: Add complete edge-case tests**

必须补充以下完整测试，不得使用省略号：

```python
async def test_other_user_cannot_read_pet(client) -> None:
    owner = await register_and_login(client, "owner", "strong-password")
    other = await register_and_login(client, "other", "strong-password")
    species_response = await client.post(
        "/api/v1/species",
        headers=owner.headers,
        json={"common_name": "龟"},
    )
    pet_response = await client.post(
        "/api/v1/pets",
        headers=owner.headers,
        json={"species_uuid": species_response.json()["data"]["uuid"]},
    )
    response = await client.get(
        f"/api/v1/pets/{pet_response.json()['data']['uuid']}",
        headers=other.headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == 3101


async def test_invalid_pet_request_rejects_internal_fields(client) -> None:
    user = await register_and_login(client, "owner", "strong-password")
    response = await client.post(
        "/api/v1/pets",
        headers=user.headers,
        json={
            "species_uuid": "00000000-0000-0000-0000-000000000001",
            "id": 1,
            "user_id": 1,
        },
    )
    assert response.status_code == 422
    assert "password_hash" not in response.text
    assert "Traceback" not in response.text
```

测试 helper `register_and_login` 必须在测试文件中完整实现并返回带 `headers` 的 typed fixture result。

- [ ] **Step 2: Run complete backend verification**

从 `backend` 目录运行：

```bash
uv run --project .. pytest -q
uv run --project .. python -m compileall .
uv run --project .. python -c 'from main import app; print(app.title); print(sorted(app.openapi()["paths"]))'
if rg -n 'backend\.app|backend\.main' app tests --glob '*.py'; then exit 1; else echo 'no legacy imports'; fi
git -C .. diff --check
```

Expected：所有测试通过、编译成功、输出宠物域路由、没有旧绝对导入、diff 检查无输出。

- [ ] **Step 3: Run real startup smoke test**

```bash
DATABASE_URL=sqlite+aiosqlite:////tmp/herplog-pet-smoke.db \
  uv run --project .. uvicorn main:app --host 127.0.0.1 --port 18005
```

请求 `/health`、注册、创建用户私有 species、创建无名称 pet、分页列表和跨用户读取；结束服务后删除临时数据库文件。启动必须从 `backend` 目录执行。

- [ ] **Step 4: Synchronize README**

只记录已经实现的宠物域路由、`cd backend` 启动命令、测试命令和私有数据隔离规则。明确社区公共资料、文件上传、事件域和生产 Redis/PG 适配仍未实现。

- [ ] **Step 5: Run final verification**

```bash
uv run --project .. pytest -q
uv run --project .. python -m compileall .
git -C .. diff --check
git -C .. status --short
```

Expected：测试全部通过、编译成功、diff 检查无输出；确认没有临时数据库、上传文件或真实密钥被纳入工作区。

- [ ] **Step 6: Commit**

```bash
git add ../README.md tests/test_pet_api.py tests/test_pet_selectors.py tests/test_pet_services.py
git commit -m "docs: 补充宠物域 API 使用与验收说明"
```

## 计划自查

- **设计覆盖**：用户私有完整科学分类、基因多选、识别标签、无名称宠物、固定性别、扁平管理单元、系统/自定义类型、整体/部分批量目标接口、分配历史、成长阶段、来源谱系、用户隔离、分页、Serializer、Selector、Service、View、错误码和测试均有对应任务。
- **抽象边界**：通用 CRUD 只封装普通 UUID 查询、用户范围分页、创建/更新/软删除模板；宠物转移、清空删除、阶段切换、来源谱系不套通用流程。
- **数据边界**：不建立全局 Species/基因库，不引入社区、企业养殖场、文件上传和事件表；个人数据始终绑定用户。
- **导入规范**：实现代码从 `backend` 目录加载；入口使用 `app.*`，`app` 内部使用相对导入，测试使用 `app.*`。
- **事务规则**：所有写入和状态转换由 Service 管理；Selector 不写入、不提交；View 不管理事务。
- **预加载规则**：所有关系 `lazy="raise"`，列表/详情 Selector 显式决定预加载内容。
- **错误安全**：预期错误由业务条件和 `BusinessError` 表达；错误码、HTTP status 和自然语言 message 集中维护；未预期异常不向前端暴露堆栈。
- **无占位符要求**：实施时必须把测试 helper 写成完整代码，不能保留 `...`、未定义 fixture、未定义 route 或“适当处理”等模糊步骤。
- **修正注意**：Task 2 测试中的 `user_id=1` 需要使用真实已存在用户 ID；实施时测试 fixture 必须先创建 User，不能违反外键约束。Task 8 的提交命令以实际仓库路径为准，不添加不存在的 `app/main.py`。
