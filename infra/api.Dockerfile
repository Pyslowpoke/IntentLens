FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY services ./services
COPY samples ./samples
ENV PATH="/app/.venv/bin:$PATH" WORKBENCH_DATA=/data
RUN useradd -m -u 10001 workbench && mkdir /data && chown workbench /data
USER workbench
CMD ["uvicorn","services.api.main:app","--host","0.0.0.0","--port","8000"]
