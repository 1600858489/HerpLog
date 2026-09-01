# HerpLog 宠物域后端设计

## 目标

在现有 FastAPI 异步基础设施和认证 API 之上，设计面向个人玩家的宠物管理域。系统需要同时支持宠物个体管理、混养环境管理、批量操作、成长阶段追踪、转移历史、个人分类资料和高级基因信息，但不引入企业养殖场式的组织层级或社区数据。

## 范围

本设计包含：

- 用户私有的物种、学名和完整科学分类
- 用户私有的基因/变异字典和多选关联
- 用户私有的识别标签
- 可选名称、系统编号和固定性别选项
- 扁平管理单元及系统/用户自定义类型
- 宠物与管理单元的历史分配和转移
- 宠物成长阶段历史
- 父本、母本、商家来源和基因凭证
- 宠物、分类资料、管理单元、历史记录的分页检索
- Serializer、Selector、Service、View 分层
- 通用 CRUD、分页和软删除复用
- 用户数据隔离和业务错误处理

不包含：

- 社区生态、公共基因库、公共物种库
- 企业养殖场、房间/区域/场区层级
- 事件域的批量操作记录实现（只定义宠物域提供的目标检索接口）
- 文件实际上传实现（来源照片/基因凭证通过后续文件域关联）
- Redis、Celery、PostgreSQL 生产适配

## 业务原则

1. 宠物资料默认属于用户私有数据；未来社区数据使用独立模型，不复用本域个人资料。
2. 结构化字段优先。能复用和选择的数据不重复要求用户输入；自由文本只用于备注和不可预见的补充内容。
3. 科学分类字段全部可选，普通玩家只填写常用名也能完成宠物管理。
4. 宠物 `name` 可选；系统 `pet_code` 必填且用户范围内唯一，用于不命名场景下稳定识别个体。
5. 管理单元是辅助管理主体，不是宠物存在的前提；宠物可以没有管理单元。
6. 管理单元扁平表示池、缸、单独格、育苗盒等实际管理对象，不建立上级空间层级。
7. 个体操作和管理单元批量操作共存；批量操作的历史目标必须固化发生时的个体快照。
8. 宠物移动、成长阶段变更和来源资料都必须保留历史，不能通过覆盖当前字段造成记录断层。

## 数据模型

### 用户私有分类

#### `personal_species`

物种资料属于用户，不建立全局共享字典。

| 字段 | 约束/说明 |
|---|---|
| `user_id` | FK → users，必填 |
| `common_name` | 常用名，必填 |
| `scientific_name` | 学名，可选 |
| `kingdom` | 界，可选 |
| `phylum` | 门，可选 |
| `class_name` | 纲，可选，避免与 Python `class` 冲突 |
| `order_name` | 目，可选 |
| `family` | 科，可选 |
| `genus` | 属，可选 |
| `species_name` | 种，可选，避免与表名混淆 |
| `subspecies` | 亚种，可选 |
| `note` | 补充说明，可选 |

唯一约束为 `(user_id, common_name)`，科学字段不强制完整，普通用户只填写常用名即可。

#### `personal_genes` / `pet_genes`

`personal_genes` 是用户私有可复用基因字典；`pet_genes` 是宠物与基因的多对多关联表。

| `personal_genes` 字段 | 说明 |
|---|---|
| `user_id` | FK → users |
| `name` | 基因/变异名称，必填 |
| `phenotype` | 表现型，可选 |
| `genotype` | 遗传型，可选 |
| `inheritance_mode` | 显性、隐性、不完全显性、共显性、未知，可选 |
| `note` | 可选 |

普通用户可以完全不创建基因记录；高级用户可以复用同一基因选项并为宠物多选。

#### `personal_identification_tags` / `pet_identification_tags`

识别标签是用户私有的可复用选项，用于颜色、花纹、体表特征等快速识别。

- `personal_identification_tags(user_id, name)`：同一用户内名称唯一
- `pet_identification_tags(pet_id, tag_id)`：正规多对多关联，两个外键组成唯一约束

### 管理单元

#### `management_unit_types`

同时支持系统内置选项和用户自定义选项：

| 字段 | 说明 |
|---|---|
| `user_id` | 系统类型为 NULL；用户类型绑定创建者 |
| `name` | 类型名称 |
| `is_system` | 是否系统内置 |
| `deleted_at` | 软删除；系统类型不可删除 |

系统默认类型可包括育苗盒、单独格、混养池、水族箱、生态缸、外塘；用户可新增、修改和软删除自己的类型。系统类型名称全局唯一，用户类型名称在用户范围内唯一。

#### `management_units`

扁平表示一个实际饲养环境或批量管理对象，例如龟池、守宫架、生态缸。

| 字段 | 说明 |
|---|---|
| `user_id` | FK → users |
| `type_id` | FK → management_unit_types |
| `unit_code` | 用户范围内唯一，系统生成且可修改 |
| `name` | 可选 |
| `note` | 可选 |

不设计房间、区域、养殖场等上级层级。

### 宠物个体

#### `pets`

| 字段 | 约束/说明 |
|---|---|
| `user_id` | FK → users |
| `species_id` | FK → personal_species，必填 |
| `pet_code` | 用户范围内唯一，系统生成且可修改 |
| `name` | 可选，不作为身份唯一依据 |
| `sex` | 固定选项：male / female / unknown / not_applicable |
| `identification_note` | 可选补充识别信息 |
| `owner_note` | 可选 |

`pet_code` 是不命名场景下的稳定识别标识；`name` 不强制填写。

### 管理单元分配与成长阶段

#### `pet_management_assignments`

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `management_unit_id` | FK → management_units |
| `started_at` | 必填 |
| `ended_at` | 可空，NULL 表示当前分配 |
| `life_stage` | 当时阶段快照，可选 |
| `transfer_reason` | 转移原因，可选 |
| `note` | 可选 |

一只宠物同一时间最多一个有效分配，但可以暂时没有分配。当前管理单元从 `ended_at IS NULL` 的记录推导，不在 `pets` 表冗余保存 `current_management_unit_id`。

#### `pet_life_stages`

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `stage` | 系统阶段或用户阶段名称，必填 |
| `started_at` | 必填 |
| `ended_at` | 可空 |
| `change_reason` | 可选 |
| `note` | 可选 |

阶段历史独立于管理单元分配历史。系统阶段可包括幼体、亚成体、成体、老年；用户可增加自定义阶段。

### 来源与谱系

#### `pet_origins`

| 字段 | 说明 |
|---|---|
| `pet_id` | FK → pets |
| `origin_type` | self_bred / breeder / purchased / unknown |
| `parent_role` | sire / dam / unspecified |
| `parent_pet_id` | 可空，仅可关联当前用户自己的宠物 |
| `breeder_name` | 可选 |
| `external_name` | 商家提供的名称，可选 |
| `genetic_note` | 可选 |
| `confidence` | confirmed / probable / unknown |
| `note` | 可选 |

不在 `pets` 表设置固定 `father_id`/`mother_id`。玩家自繁时可关联自己的父本/母本；商家繁育可只记录商家、外部名称、基因信息或未知来源；照片、报告等凭证通过后续文件域关联。

### 公共字段与关系约束

所有表继承 `IDMixin`、`TimestampMixin`、`SoftDeleteMixin`。所有关系设置 `lazy="raise"`，删除由 Service 编排软删除，不使用 ORM cascade 代替业务删除。

数据库层至少建立以下外键和唯一约束：

- 所有用户私有表的 `user_id` 外键
- 分类项、宠物编码、管理单元编码的用户范围唯一约束
- 多对多关联表的复合唯一约束
- 状态/分配表的宠物外键
- 父本/母本的宠物外键

时间重叠约束由 Service 显式校验；PostgreSQL 阶段可再增加数据库级排他约束。

## Selector 检索设计

Selector 只负责只读数据库查询，不创建、更新、删除、不提交事务，也不负责前端字段裁剪。所有用户私有资源查询必须接收当前用户的内部 `user_id`，并在查询条件中完成隔离；通过 UUID 定位资源时，必须同时绑定用户条件，不能先查资源再由 Service 比对归属。

### 用户私有分类

```python
get_species_list(
    session: AsyncSession,
    user_id: int,
    pagination: PaginationParams,
    keyword: str | None = None,
) -> tuple[list[PersonalSpecies], int]
```

查询条件固定包含 `deleted_at IS NULL` 和 `user_id = current_user.id`，可按 `common_name`/`scientific_name` 关键词检索并按稳定字段排序。基因、识别标签使用相同的用户隔离规则。

管理单元类型查询是唯一的混合范围查询：返回未删除的系统类型，或当前用户自己的自定义类型；系统类型不能通过用户条件误过滤。

### 宠物

```python
get_pet_by_uuid(session: AsyncSession, user_id: int, pet_uuid: UUID) -> Pet | None
list_pets(
    session: AsyncSession,
    user_id: int,
    pagination: PaginationParams,
    filters: PetListFilters,
) -> tuple[list[Pet], int]
```

宠物列表支持分页、物种、性别、管理单元、是否已分配、识别标签和 `pet_code`/`name` 关键词筛选。列表和详情都默认排除软删除宠物。

### 关系预加载

不同使用场景使用不同 Selector 查询，不在 Model 中定义预加载常量：

- 宠物列表：显式加载个人物种、当前有效分配、识别标签
- 宠物详情：显式加载个人物种、基因、识别标签、来源、成长阶段、完整分配历史
- 分配历史：显式加载管理单元和类型
- 分类项列表：只加载当前查询所需字段，不加载宠物集合

关联查询必须使用 `selectinload()` 或 `joinedload()`。由于所有关系统一 `lazy="raise"`，未显式加载的关系被访问时立即报错。

### 历史检索

以下接口均分页：

- 管理单元分配历史
- 成长阶段历史
- 来源/谱系记录
- 管理单元成员列表
- 用户私有分类项列表

历史查询必须先通过父级资源的当前用户条件建立边界，再过滤历史记录自身的 `deleted_at IS NULL`。批量操作的个体快照属于事件域，但宠物域提供当前有效成员 ID 的只读查询接口。

### 跨包导出

复杂 Selector 可拆为包，但跨域调用只能从 `selectors/__init__.py` 导出的公共接口进入；禁止引用 Selector 内部文件实现路径。Selector 不依赖 View 或 Serializer。

## Service 与事务设计

### 宠物创建

`PetService.create_pet()` 在一个事务中完成：

1. 校验 `species_uuid` 属于当前用户且未软删除
2. 校验可选基因、识别标签和管理单元均属于当前用户且有效
3. 生成用户范围内唯一的 `pet_code`
4. 创建宠物
5. 按请求创建初始成长阶段、管理单元分配和来源记录
6. 提交事务并返回 ORM 宠物

宠物不依赖管理单元才能创建；没有分配时不创建 assignment。

### 宠物更新

普通 PATCH 只更新宠物基础字段：`name`、`pet_code`、`species_uuid`、`sex`、`identification_note`、`owner_note`。`pet_code` 仍需保证用户范围唯一。

管理单元变更、基因关联替换、识别标签关联替换、成长阶段切换和来源维护分别使用明确 Service，不通过普通 PATCH 隐式修改，避免历史关系被覆盖。

### 管理单元操作

提供管理单元和类型 CRUD，以及：

- 向管理单元添加宠物
- 将宠物移出管理单元
- 将宠物转移到其他管理单元
- 清空并删除管理单元

转移事务为：锁定/读取宠物当前有效分配 → 结束旧分配 → 创建新分配 → 记录转移时间、阶段和原因 → 提交。单元测试和 Service 检查保证同一宠物的有效分配不重叠。

删除管理单元只允许显式执行 `clear-and-delete`：结束所有当前分配、保留分配历史、软删除管理单元，宠物本身不删除并变为未分配。

### 成长阶段

阶段切换结束当前阶段并创建新阶段；阶段历史独立于管理单元分配。阶段可用系统选项或用户自定义项，科学/高级信息不阻塞普通饲养流程。

### 来源与谱系

来源 Service 允许新增、修改、软删除来源记录。父本/母本关联必须通过当前用户的宠物 UUID 校验；不得关联其他用户、软删除宠物或自身形成非法谱系。商家来源不要求存在父本/母本。

### 级联软删除

- 删除宠物：同一事务级联软删除管理单元分配、成长阶段、来源、基因关联和识别标签关联
- 移出管理单元：只结束分配，不删除宠物或历史
- 删除分类选项：已被历史记录使用时保留记录并停止新建选择
- 管理单元清空删除：只结束分配和删除单元，不删除宠物

### 批量操作目标

事件域后续通过宠物域公开：

```python
get_active_pet_ids_by_management_unit(
    session: AsyncSession,
    user_id: int,
    management_unit_uuid: UUID,
) -> list[int]
```

事件 Service 创建管理单元整体操作时，固化当时全部有效成员；部分操作时校验所选宠物均属于该用户且当前属于目标单元。转移不会修改已保存的快照。

## API 与 Serializer 设计

所有路由使用 `/api/v1/`，所有响应使用 `ResponseEnvelope`，所有列表使用统一分页。

### 宠物基础 API

```text
GET    /api/v1/pets
POST   /api/v1/pets
GET    /api/v1/pets/{pet_uuid}
PATCH  /api/v1/pets/{pet_uuid}
DELETE /api/v1/pets/{pet_uuid}
```

创建时仅 `species_uuid` 必填；`sex` 默认 `unknown`。`pet_code` 系统生成，`name`、基因、标签、管理单元、来源和成长阶段全部可选。

### 用户私有分类 API

```text
GET    /api/v1/species
POST   /api/v1/species
PATCH  /api/v1/species/{species_uuid}
DELETE /api/v1/species/{species_uuid}

GET    /api/v1/genes
POST   /api/v1/genes
PATCH  /api/v1/genes/{gene_uuid}
DELETE /api/v1/genes/{gene_uuid}

GET    /api/v1/identification-tags
POST   /api/v1/identification-tags
PATCH  /api/v1/identification-tags/{tag_uuid}
DELETE /api/v1/identification-tags/{tag_uuid}
```

### 管理单元 API

```text
GET    /api/v1/management-unit-types
POST   /api/v1/management-unit-types
PATCH  /api/v1/management-unit-types/{type_uuid}
DELETE /api/v1/management-unit-types/{type_uuid}

GET    /api/v1/management-units
POST   /api/v1/management-units
GET    /api/v1/management-units/{unit_uuid}
PATCH  /api/v1/management-units/{unit_uuid}
DELETE /api/v1/management-units/{unit_uuid}
POST   /api/v1/management-units/{unit_uuid}/clear-and-delete
```

### 分配、阶段和来源 API

```text
GET  /api/v1/pets/{pet_uuid}/management-assignments
POST /api/v1/pets/{pet_uuid}/management-assignments/move
POST /api/v1/pets/{pet_uuid}/management-assignments/remove

GET  /api/v1/pets/{pet_uuid}/life-stages
POST /api/v1/pets/{pet_uuid}/life-stages
PATCH /api/v1/pets/{pet_uuid}/life-stages/{stage_uuid}
POST /api/v1/pets/{pet_uuid}/life-stages/{stage_uuid}/end

GET    /api/v1/pets/{pet_uuid}/origins
POST   /api/v1/pets/{pet_uuid}/origins
PATCH  /api/v1/pets/{pet_uuid}/origins/{origin_uuid}
DELETE /api/v1/pets/{pet_uuid}/origins/{origin_uuid}
```

### Serializer 规则

- 请求 Schema 全部继承 `BaseRequestSchema`，拒绝未声明字段
- 请求不接受 `id`、`uuid` 作为可写字段；路径资源标识只接受 UUID
- 响应只暴露 UUID，不暴露内部自增 ID
- 列表响应只返回必要字段，详情响应才展开基因、来源、阶段和分配历史
- 分类资料使用结构化嵌套对象，不拼接成不可查询的展示字符串
- 业务逻辑不直接返回 ORM 给 View，必须先经过 Response Schema

## 通用 CRUD 与复用设计

抽象只服务于真实稳定的共同行为，不建立承载所有业务的“大 CRUD Service”。

### `BaseSelector`

可复用：

- 当前用户范围内按 UUID 查询
- 用户范围列表分页
- 默认软删除过滤
- 公共排序和分页计算

实际 Selector 必须显式提供用户归属字段/关联路径、排序、过滤条件和预加载选项，基类不能猜测不同模型的权限关系。

### `BaseCRUDService`

可复用普通创建、更新、软删除模板，但业务 Service 必须明确实现：

- Schema 到 Model 的字段映射
- 用户归属设置
- 用户范围唯一性检查
- 关联资源归属检查
- 事务边界
- 删除级联和状态变化

`PersonalSpecies`、`PersonalGene`、`IdentificationTag` 可以共享基础分类 CRUD；`ManagementUnitType` 需要处理系统类型与用户类型；`Pet` 需要独立 Service；分配、阶段、来源和清空删除只能复用公共查询/软删除基础，不直接套普通 CRUD。

View 不通过反射或动态路由自动生成 CRUD。每个路由明确声明请求 Schema、Service 和响应 Schema，保证 OpenAPI 契约清晰。

## 错误码与权限

在已有 `3000-3999` Pet 域内按子资源分段：

```text
3100-3199  Pet
3200-3299  CareRule
3300-3399  PetState / LifeStage
3400-3499  PersonalSpecies
3500-3599  PersonalGene
3600-3699  IdentificationTag
3700-3799  ManagementUnit
3800-3899  ManagementUnitType
3900-3999  Origin / Assignment
```

错误类型按十位/个位区分：`x0` NotFound、`x1` Validation、`x2` Conflict、`x3` Forbidden、`x4` InvalidState。

示例：

```text
3101  宠物不存在
3111  宠物信息无效
3121  pet_code 已存在
3141  宠物状态转换无效
3401  物种资料不存在
3721  管理单元仍有有效分配
3803  无权修改系统管理单元类型
3941  宠物已有重叠分配
```

权限规则：

- 所有私有数据按当前用户过滤，其他用户资源统一表现为 NotFound
- 请求体不接受 `user_id`
- 用户只能修改和软删除自己的分类项、管理单元和宠物
- 系统管理单元类型不可修改、删除
- 创建宠物时引用的物种、基因、标签、管理单元必须属于当前用户且未删除
- 父本/母本只能关联当前用户自己的有效宠物
- 不允许引用已软删除或已移出目标管理单元的资源

## 测试设计

### 模型测试

- 所有模型继承公共 Mixin，UUID 对外字段可用，自增 ID 仅内部存在
- 所有外键、用户范围唯一约束和关联表复合唯一约束生效
- 所有关系的 `lazy="raise"` 生效
- 科学分类字段全部可为空
- 宠物名称可为空，系统编号必填

### Selector 测试

- 物种、基因、标签、管理单元和宠物查询均过滤当前用户
- 查询不到其他用户资源
- 默认排除软删除记录
- 列表分页、关键词和组合筛选正确
- 详情按场景显式预加载所需关系
- 未预加载关系访问抛出 SQLAlchemy 约束异常
- 当前分配只返回 `ended_at IS NULL` 记录，历史查询返回完整时间线

### Service 测试

- 创建普通宠物、无名称宠物和未分配管理单元宠物
- 自动生成并允许修改用户范围唯一的 `pet_code`
- 分类项重复、编号重复和非法关联被拒绝
- 系统管理单元类型不可修改或删除
- 用户自定义类型允许修改和软删除
- 管理单元可添加、移出和转移宠物
- 同一宠物有效分配不得重叠
- 删除管理单元必须走清空并删除，宠物保留为未分配
- 成长阶段切换保留历史，管理单元转移不覆盖阶段历史
- 自繁可关联父本/母本，商家来源不要求父母
- 父本/母本不能关联其他用户、软删除宠物或自身
- 删除宠物级联软删除其历史关系和多对多关联
- 管理单元整体成员查询与部分成员校验正确
- 多对象状态操作事务失败时不留下半成品记录

### API 测试

- 所有端点需要认证，跨用户访问返回统一 NotFound envelope
- 请求和响应使用 snake_case
- 请求传入 `id`/`uuid` 返回 422
- 响应不暴露内部 `id`、密码或数据库关系细节
- 所有列表返回统一分页结构
- 普通宠物列表只返回必要字段，详情才展开完整历史
- 业务错误返回集中定义的 HTTP status、code 和自然语言 message
- 不返回 Python 异常文本或 traceback
- 管理单元整体和部分个体操作的目标校验正确

## 后续事件域接口边界

宠物域只提供事件域所需的只读公共接口：

```python
get_active_pet_ids_by_management_unit(
    session: AsyncSession,
    user_id: int,
    management_unit_uuid: UUID,
) -> list[int]
```

事件域负责保存批量事件及其个体快照；宠物域不提前创建事件模型，也不把批量事件逻辑放入宠物 Service。

## 设计结论

采用管理主体与宠物个体分离的方案：管理单元保持扁平且可选，宠物个体独立存在，个体和批量操作均可记录；所有分类和基因资料为用户私有结构化数据；转移、成长和来源信息采用历史模型保存；普通 CRUD 使用有限、明确的基础抽象，特殊业务流程保持独立。
       