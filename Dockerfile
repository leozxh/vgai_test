FROM python:3.11-slim

# 设置时区为中国标准时间
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 安装 Chrome 浏览器（直接下载 deb 包，避免 GPG key 问题）
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget curl unzip fonts-liberation \
       libasound2t64 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
       libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libxcomposite1 \
       libxdamage1 libxrandr2 xdg-utils \
    && curl -fsSL -o /tmp/google-chrome.deb \
       https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/google-chrome.deb \
    && rm /tmp/google-chrome.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version

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
