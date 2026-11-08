# Etapa 1: Construcción y resolución de dependencias
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Etapa 2: Imagen final ligera de producción
FROM python:3.12-slim
WORKDIR /app

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copiar código fuente y asegurar directorio para carga de fotos
COPY . .
RUN mkdir -p src/exodo/static/img

EXPOSE 6001

CMD ["uvicorn", "exodo.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "6001"]