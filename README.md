# SIVVE - Sistema de Inventario y Venta de Vehículos

Plataforma web para la gestión centralizada de catálogo, control de stock en tiempo real, administración de ventas y generación automática de facturas para concesionarios de vehículos.

## Integrantes del Equipo
* Johan Quirama Acevedo
* Juan José Vélez Arias
* Nicolás Gómez

## Tecnologías y Versiones
* Python 3.12 / FastAPI 0.110.0
* SQLAlchemy 2.0 / PostgreSQL 16 (o Neon PostgreSQL)
* Docker & Docker Compose
* HTML5, Jinja2, Bootstrap 5, Chart.js
* Tablero GitHub Projects: [Tablero SIVVE](https://github.com/orgs/CorpNJ/projects/1)

## Instrucciones de Despliegue con Docker

Para levantar todo el sistema desde un clon limpio (backend, frontend y base de datos):

```bash
git clone [https://github.com/CorpNJ/exodo.git](https://github.com/CorpNJ/exodo.git)
cd exodo
docker compose up -d --build