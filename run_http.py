"""Paperlib MCP 远程入口 (Railway / 云端)。

- paperlib-mcp 原生 mcp.run() 是 stdio，只能在本地 docker exec 里用。
- 云端部署需要 HTTP 传输，这里用 FastMCP 的 streamable-http 跑在 $PORT 上，
  端点为 /mcp，可供 WorkBuddy 等作为远程 MCP (streamable-http) 接入。
- 启动前自动确保 MinIO 桶存在（boto3 create_bucket），免去单独 init 服务。
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("paperlib_mcp.railway")

from paperlib_mcp import server
from paperlib_mcp.storage import get_s3_client, get_settings


def ensure_bucket():
    try:
        s = get_settings()
        client = get_s3_client()
        bn = s.s3_bucket
        try:
            client.head_bucket(Bucket=bn)
            logger.info("bucket already exists: %s", bn)
        except Exception:
            client.create_bucket(Bucket=bn)
            logger.info("bucket created: %s", bn)
    except Exception as e:  # 连接失败不要阻塞启动，重试几次
        logger.warning("bucket ensure failed (will retry): %s", e)
        raise


if __name__ == "__main__":
    for _ in range(10):
        try:
            ensure_bucket()
            break
        except Exception:
            time.sleep(3)

    port = int(os.environ.get("PORT", "8000"))
    logger.info("starting paperlib-mcp (streamable-http) on 0.0.0.0:%s", port)
    # FastMCP 3.x: transport="streamable-http" 挂载在 /mcp
    server.mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
