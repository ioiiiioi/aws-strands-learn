FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# dependency layer dulu supaya rebuild kode tidak mengulang resolve
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY main.py README.md ./
RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

# tanpa reloader; reloader hanya untuk APP_ENV=development di luar container
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
