# ForkliftCLI backend 镜像（本地/开发用）
# 显式安装 CPU 版 torch，避免拉取数 GB 的 CUDA 运行时；
# WeMM-Embedding 在容器内以 CPU 推理，首次使用会从 HuggingFace 下载模型权重。
FROM python:3.12-slim

WORKDIR /app

# torch CPU 推理需要 OpenMP 运行时
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 先装 CPU 版 torch，再装其余依赖；requirements 中 torch>=2.0.0 已满足则不会被替换
COPY requirements.txt ./
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

EXPOSE 8000

# 启动前执行迁移（幂等）；环境变量由 docker-compose 注入
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]