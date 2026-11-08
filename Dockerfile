# -------------------------------------------------------------
# Dockerfile optimizado para FastAPI, PostgreSQL y Render
# -------------------------------------------------------------
FROM python:3.12-slim

# Evitar archivos .pyc y forzar salida inmediata en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Instalar dependencias esenciales del sistema operativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# Copiar e instalar las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY src ./src

# Crear físicamente las carpetas estáticas requeridas para las imágenes
RUN mkdir -p /app/src/exodo/static/img

# Configurar usuario no-root por seguridad en producción
RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 6001

CMD ["uvicorn", "src.exodo.main:app", "--host", "0.0.0.0", "--port", "6001"]