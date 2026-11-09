# 🚗 Éxodo - Sistema Integrado de Venta de Vehículos (SIVVE)

Éxodo (SIVVE) es una plataforma web desarrollada con FastAPI, Jinja2 y PostgreSQL para la gestión integral del inventario de vehículos usados, registro directo de compradores, emisión de facturas y visualización de reportes de ventas con gráficos analíticos para administradores.

## 👥 Integrantes del Equipo
* **Juan José Vélez Arias** - Código: *(Tu código)*
* *Johan Qurirama Acevedo* - Código: *(Código)*
* *Nicolas Gomez Olea* - Código: *(Código)*

## 🛠️ Tecnologías Utilizadas
* **Backend & Web:** Python 3.11 / FastAPI / Jinja2 / SQLAlchemy ORM
* **Base de Datos:** PostgreSQL 18 (Neon Cloud)
* **Interfaz Grafica:** HTML5 / Bootstrap 5 / JavaScript (ES6) / Chart.js
* **Contenerización:** Docker & Docker Compose
* **Gestión del Proyecto:** [Tablero en GitHub Projects](https://github.com/orgs/CorpNJ/projects) *(Ajustar enlace)*

---

## 🚀 Instrucciones de Ejecución con Docker

### Prerrequisitos
* Tener instalado Docker Desktop y Docker Compose.

Paso 1:
### Paso 1: Clonar el repositorio
```bash
git clone [https://github.com/CorpNJ/exodo.git](https://github.com/CorpNJ/exodo.git)
cd exodo
Paso 2: Configurar Variables de Entorno

Cree un archivo .env en la raíz del proyecto con la variable de conexión a Neon PostgreSQL:
Fragmento de código

DATABASE_URL=postgresql://neondb_owner:npg_Q2WCl0ZtEkhV@ep-dark-shadow-34072833-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
SESSION_SECRET_KEY=secret_key_exodo_2026

Paso 3: Construir y levantar el sistema
Bash

docker compose up -d --build