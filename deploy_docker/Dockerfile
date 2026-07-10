FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖：ffmpeg（视频/音频处理）、中文字体（字幕渲染）
RUN apt-get update && apt-get install -y ffmpeg fonts-wqy-zenhei && rm -rf /var/lib/apt/lists/*

# 设置 pip 国内镜像（加速）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .
# 先安装 CPU 版 torch，避免误装 CUDA 版本
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建输出目录
RUN mkdir -p outputs

EXPOSE 7860

CMD ["python", "app.py"]