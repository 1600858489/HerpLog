# 快速启动

## 前置条件

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 与 npm

## 后端

从仓库根目录安装 Python 依赖：

```bash
uv sync
```

启动 API：

```bash
cd backend
uv run --project .. uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

可访问：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

开发环境默认使用 SQLite，并在启动时以 SQLAlchemy `create_all()` 建表；正式迁移与 PostgreSQL 适配尚未实现。

运行后端检查：

```bash
cd backend
uv run --project .. pytest -q
uv run --project .. python -m compileall .
```

## 前端

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

运行前端检查：

```bash
npm run typecheck
npm test
npm run build
```

当前前端仍使用 Mock 数据；宠物档案 API 接入属于下一阶段工作。详见 [产品核心域路线图](../roadmap/product-core-roadmap.md)。
