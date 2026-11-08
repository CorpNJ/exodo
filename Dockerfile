# -------------------------------------------------------------
# Dockerfile optimizado para FastAPI y Render / Docker Compose
# -------------------------------------------------------------
FROM python:3.12-slim

# Evitar que Python escriba archivos .pyc y forzar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# Copiar e instalar requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY src ./src

# Crear la estructura de carpetas estáticas para imágenes de vehículos
RUN mkdir -p /app/src/exodo/static/img

# Crear usuario no-root por seguridad
RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 6001

CMD ["uvicorn", "src.exodo.main:app", "--host", "0.0.0.0", "--port", "6001"]