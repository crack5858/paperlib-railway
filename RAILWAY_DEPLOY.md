# Paperlib MCP — Railway 云端部署指南

> 基于 **PyPI 官方包 `paperlib-mcp==0.1.5`**（已 `pip download` 实测入口 `paperlib-mcp -> paperlib_mcp.server:main`，
> FastMCP 3.4.5，原生 `mcp.run()` 为 stdio）。本目录已改造为 Railway 可直接部署的形态。
>
> 仓库原始 GitHub 地址已失效，故无法 `git clone`；如需接入 GitHub 自动部署，请把本目录内容推到你自己的仓库。

---

## 1. 架构（Railway 上 3 个服务）

```
┌────────────────────┐   内部网络    ┌────────────────────┐   内部网络    ┌────────────────────┐
│  paperlib-mcp      │◀────────────▶│  postgres (pgvector)│◀────────────▶│  minio (S3)        │
│  (本目录 Dockerfile)│   POSTGRES_*  │  postgres.Dockerfile │   S3_ENDPOINT │  minio/minio:latest │
│  暴露 :8000 /mcp   │               │  :5432 + vector 扩展  │              │  :9000 / :9001     │
└────────────────────┘               └────────────────────┘              └────────────────────┘
        │
   外部 HTTPS (Railway 域名) → WorkBuddy 远程 MCP (streamable-http)
```

- **paperlib-mcp**：从本目录 `Dockerfile` 构建，以 `streamable-http` 跑在 `$PORT`（端点 `/mcp`）。
- **postgres**：用 `postgres.Dockerfile`（基于 `pgvector/pgvector:pg16`），首次启动自动执行 `01-init.sql` 建 `vector` 扩展。
  - 持久卷挂载：`/var/lib/postgresql/data`
- **minio**：直接用官方镜像 `minio/minio:latest`，命令 `server /data --console-address :9001`。
  - 持久卷挂载：`/data`
  - 存储桶 `MINIO_BUCKET` 由 paperlib-mcp 启动时自动创建（见 `run_http.py`），无需额外 init 服务。

---

## 2. 真实环境变量（取自源码 `settings.py` / `config.py`，pydantic 大小写不敏感）

| 变量 | 说明 | 默认值 |
|---|---|---|
| `POSTGRES_HOST` | Postgres 主机（Railway 内部地址） | localhost |
| `POSTGRES_USER` | 用户名 | paper |
| `POSTGRES_PASSWORD` | 密码 | paper |
| `POSTGRES_DB` | 库名 | paperlib |
| `POSTGRES_PORT` | 端口 | 5432 |
| `S3_ENDPOINT` | MinIO/S3 端点（含 http:// 与端口） | http://localhost:9000 |
| `MINIO_ROOT_USER` | MinIO 访问 Key（同时作为 S3 access key） | minio |
| `MINIO_ROOT_PASSWORD` | MinIO 密钥（同时作为 S3 secret key） | minio123 |
| `MINIO_BUCKET` | 存储桶名 | papers |
| `OPENROUTER_API_KEY` | **必填**（否则嵌入/图谱/综述不可用） | 空 |
| `OPENROUTER_BASE_URL` | OpenRouter 基址 | https://openrouter.ai/api/v1 |
| `EMBEDDING_MODEL` | 嵌入模型 | openai/text-embedding-3-small |
| `LLM_MODEL` | 通用 LLM | openai/gpt-5-nano |
| `LLM_SUMMARIZE_MODEL` | 摘要专用 LLM（留空=用 LLM_MODEL） | 空 |
| `PORT` | streamable-http 监听端口（Railway 注入） | 8000 |

> 注意：`S3_BUCKET` 是**错误**变量名（源码字段为 `minio_bucket`），必须用 `MINIO_BUCKET`。

---

## 3. 前置条件

1. 一个 Railway 账户（https://railway.com ，注册可用 GitHub 登录）。
2. 一个 OpenRouter API Key：https://openrouter.ai/keys （免费额度即可）。
3. 本项目部署需 Railway 能访问本目录的 `Dockerfile` / `postgres.Dockerfile` / `01-init.sql` / `run_http.py`。
   - 方式一（推荐）：推到你自己的 GitHub 仓库，Railway 从 GitHub 部署。
   - 方式二：用 Railway CLI 从本地目录部署（需项目令牌）。

---

## 4. 方法 A：Railway Dashboard 部署（最直观）

1. 新建 Project → **Empty Project**。
2. **添加 Postgres 服务**：
   - 点 **New Service → Deploy from Dockerfile**，选择 `postgres.Dockerfile`。
   - 命名服务为 `postgres`。
   - Variables 里设置：`POSTGRES_USER=paper`、`POSTGRES_PASSWORD=paper`、`POSTGRES_DB=paperlib`。
   - 在 **Volumes** 里挂一个卷到 `/var/lib/postgresql/data`（保留数据）。
   - 记下该服务的**私有网络地址**（Networking 页，形如 `postgres.railway.internal`）。
3. **添加 MinIO 服务**：
   - **New Service → Deploy from Docker Image**，镜像填 `minio/minio:latest`。
   - 命名 `minio`。
   - Deploy 的 Start Command 填：`server /data --console-address :9001`。
   - Variables：`MINIO_ROOT_USER=minio`、`MINIO_ROOT_PASSWORD=minio123`。
   - Volumes 挂 `/data`。
   - 记下私有地址（如 `minio.railway.internal`）。
4. **添加 paperlib-mcp 服务**：
   - **New Service → Deploy from Dockerfile / GitHub**，指向本目录（或你推送的仓库，根目录 `Dockerfile`）。
   - Variables 设置：
     - `POSTGRES_HOST` = 上面记下的 postgres 私有地址（如 `postgres.railway.internal`）
     - `POSTGRES_USER=paper`、`POSTGRES_PASSWORD=paper`、`POSTGRES_DB=paperlib`
     - `S3_ENDPOINT` = `http://<minio私有地址>:9000`（如 `http://minio.railway.internal:9000`）
     - `MINIO_ROOT_USER=minio`、`MINIO_ROOT_PASSWORD=minio123`、`MINIO_BUCKET=paperlib`
     - `OPENROUTER_API_KEY` = 你的真实 key
   - 端口：Railway 会自动注入 `PORT`，无需手填。
   - 部署后点 **Generate Domain** 生成公网 HTTPS 域名（用于远程 MCP）。
5. 等待三个服务都变成 ✅ Healthy，打开 paperlib-mcp 的 Deploy Logs 应看到
   `starting paperlib-mcp (streamable-http) on 0.0.0.0:8000`。

---

## 5. 方法 B：Railway CLI 部署（需项目令牌）

> 沙箱内 `railway login` 走浏览器 OAuth 无法完成；请用 **Project Token** 以非交互方式部署。

1. 在 Railway 项目设置 → **Tokens → Project Tokens** 生成一个令牌（注意权限与过期时间）。
2. 把令牌设为环境变量：
   ```powershell
   $env:RAILWAY_TOKEN = "你的项目令牌"
   ```
3. 链接并部署（CLI 安装在 `C:\Users\Tommy\.workbuddy\binaries\node\workspace\node_modules\.bin\railway`）：
   ```powershell
   cd D:/paperlib-mcp
   railway link --project "<项目ID>"
   # 分别创建三个服务并部署（每个服务用各自目录/镜像）:
   #   postgres: railway service create postgres ; railway up --service postgres  (指向 postgres.Dockerfile)
   #   minio   : railway service create minio   ; (用镜像 minio/minio:latest，start command 见上)
   #   app     : railway service create paperlib ; railway up --service paperlib
   # 再用 `railway variables` / `railway variable set` 写入第 4 步的环境变量
   ```
   > 多服务 CLI 流程较繁琐，若不熟悉建议直接用方法 A 的 Dashboard。

---

## 6. 部署后验证

- **健康检查**：`curl https://<你的railway域名>/mcp` 应返回 `405 Method Not Allowed`（说明 streamable-http 服务在监听；GET 不被允许是正常的）。
- **工具自检**：在 WorkBuddy 里调用 paperlib-mcp 的 `health` 工具，应返回 `vector_enabled: true` 与 `connected: true`。

---

## 7. 接入 WorkBuddy（远程 MCP）

把下面片段合并进 `~/.workbuddy/mcp.json`（替换 `<railway域名>`）：

```json
{
  "mcpServers": {
    "paperlib-mcp": {
      "type": "streamable-http",
      "url": "https://<你的railway域名>/mcp"
    }
  }
}
```

> 若你的 WorkBuddy 版本只支持 `sse` 类型，可改用 `transport="sse"` 重新构建（改 `run_http.py` 一行即可），端点为 `/sse`。

---

## 8. 注意事项 / 已知点

- **OPENROUTER_API_KEY 必填**：没有它，数据库/对象存储可用，但嵌入、GraphRAG、综述等 LLM 功能会失败。
- **pgvector 扩展**：已通过 `01-init.sql` 在 postgres 首次初始化时自动创建；若你改用 Railway 官方 Postgres 插件而非本 `postgres.Dockerfile`，需确认其已包含 pgvector，否则要手动 `CREATE EXTENSION vector`。
- **私有网络地址**：Railway 各服务间用内部域名互访，postgres/minio 的服务名即其主机名；具体拼写以 Dashboard 的 Networking 页为准。
- **与本地 D 盘部署的关系**：两者共用同一套源码与 `.env` 变量语义；本地 `docker-compose.yml` 仍可用（command 被覆盖为 stdio 常驻），Railway 用 `Dockerfile` 默认 CMD（streamable-http）。
