# Postgres + pgvector 自定义镜像 (Railway 部署用)
# 官方 postgres 镜像会在首次初始化时自动执行 /docker-entrypoint-initdb.d/ 下的 .sql
FROM pgvector/pgvector:pg16

COPY 01-init.sql /docker-entrypoint-initdb.d/01-init.sql

# Railway 请把持久卷挂载到 /var/lib/postgresql/data 以保留数据
