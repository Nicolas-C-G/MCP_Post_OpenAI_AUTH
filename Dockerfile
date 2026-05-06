FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin mcp
USER mcp

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "python", "-m", "app.main"]
