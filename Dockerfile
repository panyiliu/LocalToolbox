# 使用官方 Playwright Python 镜像，内置 Chromium，满足「HTML 转图片」工具
# 标签需与 requirements.txt 中 playwright 主版本大致一致
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

ARG APP_VERSION=dev
ARG APP_BUILD_TIME=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=false \
    PIP_NO_CACHE_DIR=1 \
    APP_VERSION=${APP_VERSION} \
    APP_BUILD_TIME=${APP_BUILD_TIME}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

COPY . .

RUN mkdir -p uploads logs

EXPOSE 5000

CMD ["sh", "-c", "python scripts/preflight.py --skip-port-check && python app.py"]
