# Imagen de la app. Multiarquitectura (amd64 en el portátil, arm64 en la Pi).
# Los datos (SQLite) viven en /app/data, que se monta desde el host.
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DATABASE_PATH=/app/data/library.db \
    FORWARDED_ALLOW_IPS="*"

WORKDIR /app

# Dependencias primero, para que cambiar el código no invalide esta capa.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

# Instalación editable: las plantillas y estáticos se resuelven desde src/.
COPY src ./src
RUN uv sync --frozen --no-dev

# Sin privilegios por defecto; docker run --user / compose `user:` lo ajusta
# a PUID:PGID para que los ficheros de /app/data sean del usuario del host.
USER 1000:1000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4)"]

CMD ["uvicorn", "personal_library.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
