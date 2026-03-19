FROM python:3.11-slim

# 安装 Chrome 浏览器 + 依赖 + cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg2 curl unzip cron \
    libglib2.0-0 libnspr4 libnss3 libdbus-1-3 libxcb1 \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb || true \
    && apt-get install -y -f \
    && rm -f /tmp/chrome.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目
COPY . .

# 创建必要目录
RUN mkdir -p logs reports screenshots

# 创建定时任务脚本（每 3 小时执行）
RUN echo '#!/bin/bash\ncd /app && git pull 2>/dev/null; python run/start.py >> /app/logs/cron.log 2>&1' > /app/run_test.sh \
    && chmod +x /app/run_test.sh

# 配置 cron：每 3 小时执行
RUN echo "0 */3 * * * /app/run_test.sh" > /etc/cron.d/vgai-cron \
    && chmod 0644 /etc/cron.d/vgai-cron \
    && crontab /etc/cron.d/vgai-cron

# 创建启动脚本：启动时先跑一次测试，然后 cron 常驻
RUN echo '#!/bin/bash\necho "=== vgai-test 容器启动 ===" \npython run/start.py 2>&1 | tee /app/logs/cron.log\necho "=== 首次测试完成，cron 定时任务已启动（每3小时执行）==="\ncron -f' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
