# Etapa 1: Construcción y dependencias
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: Imagen final de producción
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser src/exodo/static/img ./src/exodo/static/img 2>/dev/null || true

RUN mkdir -p /app/src/exodo/static/img && chown -R appuser:appuser /app/src/exodo/static

USER appuser

EXPOSE 6001

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:6001/web/catalogo')" || exit 1

CMD ["uvicorn", "exodo.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "6001"]