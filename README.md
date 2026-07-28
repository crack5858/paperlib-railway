# Paperlib MCP — D 盘 Docker 部署说明

> 目标：在 **D 盘** 部署 Paperlib MCP（文献管理与检索 MCP 服务器），可作为文献库接入 WorkBuddy / Claude / Cursor。
> 数据全部持久化在 `D:/paperlib-mcp/data/` 与 `D:/paperlib-mcp/papers/`。

## 一、为什么用这套方案
- 你选的是 **paperlib-mcp（文献 MCP）**；但其 GitHub 仓库地址在公开文档里是占位符 `your-org/paperlib-mcp`，真实仓库 `h-lu/paperlib-mcp` 已 404。
- 经核实，PyPI 上的官方包 **`paperlib-mcp==0.1.5`** 真实存在（"Paper Library MCP - 文献管理与检索 MCP 服务器"，需 Python>=3.11）。
- 本部署用 PyPI 包 `pip install paperlib-mcp` 构造 Docker 镜像，**等效还原**文档所述全部能力（PDF 导入、混合检索、知识图谱、文献综述生成）。

## 二、依赖组件
| 组件 | 镜像 | 用途 |
|---|---|---|
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` | 元数据 + 向量库 |
| MinIO | `minio/minio` | PDF / 对象存储 (S3 兼容) |
| Paperlib MCP | 本目录 Dockerfile (python:3.12-slim + paperlib-mcp) | MCP 服务(stdio) |

## 三、前置条件（需你本地完成，沙箱无法代装）
1. **安装 Docker Desktop（Windows, WSL2 后端）**
   - 已为你下载安装器到 `D:/DockerDesktopInstaller.exe`，**右键「以管理员身份运行」**完成安装并启动一次。
   - 或在官网下载：https://www.docker.com/products/docker-desktop/
2. **共享 D 盘**：Docker Desktop → Settings → Resources → File Sharing，勾选 **D:**（否则 D:/paperlib-mcp 卷挂载失败）。
3. **OpenRouter API Key**：到 https://openrouter.ai/keys 申请，填入 `D:/paperlib-mcp/.env` 的 `OPENROUTER_API_KEY`。

## 四、启动（管理员 PowerShell / CMD）
```powershell
cd D:/paperlib-mcp
docker compose up -d
docker compose ps
```
首次会构建 MCP 镜像（拉取 python:3.12-slim + pip 安装 paperlib-mcp，约 1–2 分钟）。

## 五、接入 WorkBuddy
把 `mcp-workbuddy.json` 里的 `paperlib-mcp` 条目合并进 `~/.workbuddy/mcp.json` 的 `mcpServers` 中，重启/刷新连接器即可。
之后可用自然语言让它「把这篇 PDF 导入文献库」「检索发酵食品质谱相关文献」「生成文献综述」等。

## 六、常用操作
- 导入 PDF：`docker exec -i paperlib-mcp python -m paperlib_mcp.server` 由 MCP 客户端调用 `import_pdf`
- 混合检索：MCP 工具 `search_hybrid`
- 知识图谱：`extract_graph_v1` / `build_communities_v1`
- 文献综述：`build_evidence_pack` → `draft_lit_review_v1`
- 停止(保留数据)：`docker compose down`
- 停止并清空：`docker compose down -v`
- MinIO 控制台：http://localhost:9001 （minio / minio123）

## 七、核验清单
- [ ] Docker Desktop 已以管理员安装并启动
- [ ] Docker Desktop 已共享 D: 盘
- [ ] `.env` 中 `OPENROUTER_API_KEY` 已填真实 Key
- [ ] `docker compose up -d` 后四个容器均 Up（postgres healthy、minio-init completed、paperlib-mcp 常驻）
