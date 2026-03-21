FROM python:3.11-slim

# 设置时区为中国标准时间
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 安装 Chromium 浏览器（从 Debian 官方源安装，无需访问 Google）
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && chromium --version

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目
COPY . .

# 创建必要目录
RUN mkdir -p logs reports screenshots

# 容器保持运行，定时任务由宿主机 crontab 通过 docker exec 触发
CMD ["tail", "-f", "/dev/null"]
