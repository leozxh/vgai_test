FROM python:3.11-slim

# 设置时区为中国标准时间
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 安装 Chrome 浏览器 + 依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget gnupg2 curl unzip \
       libglib2.0-0 libnspr4 libnss3 libdbus-1-3 libxcb1 \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/chrome.deb; apt-get install -y -f \
    && rm -f /tmp/chrome.deb \
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
