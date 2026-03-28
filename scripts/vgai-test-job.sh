#!/bin/bash
set -euo pipefail

cd /vol1/docker/vgai-test

# 拉取最新代码，有新提交才重建镜像
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] 检测到新代码，拉取并重建镜像..."
    git pull
    docker compose build
    docker compose up -d
    sleep 5
fi

# 容器没运行就先拉起
docker start vgai-test >/dev/null 2>&1 || true
docker exec -i vgai-test sh -lc '
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export NO_PROXY="localhost,127.0.0.1"
export PYTHONUNBUFFERED=1
mkdir -p /app/logs
python -u run/start.py 2>&1 | tee -a /app/logs/cron.log /proc/1/fd/1
'
