FROM python:3.12-slim

WORKDIR /app

# 官方 PyPI 包 (文献管理与检索 MCP 服务器)
RUN pip install --no-cache-dir paperlib-mcp

COPY run_http.py /app/run_http.py

RUN mkdir -p /app/papers

# 云端以 streamable-http 暴露 (端点 /mcp)，本地 docker-compose 会覆盖 CMD 仍为 stdio 常驻
EXPOSE 8000
ENV PORT=8000
CMD ["python", "/app/run_http.py"]
