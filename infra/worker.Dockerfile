FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && uv run playwright install --with-deps chromium
ENV PATH="/app/.venv/bin:$PATH" WORKBENCH_DATA=/data PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN uv run playwright install chromium
COPY services ./services
COPY apps/web/public/echarts.min.js ./apps/web/public/echarts.min.js
RUN useradd -m -u 10001 workbench && mkdir /data && chown workbench /data
USER workbench
CMD ["python","-m","services.worker.main"]
