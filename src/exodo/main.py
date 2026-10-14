from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from exodo.routers import usuarios, vehiculos, vistas

app = FastAPI(title="SIVVE - Sistema de Inventario")

# Archivos estáticos (imágenes subidas, css, etc.)
app.mount("/static", StaticFiles(directory="src/exodo/static"), name="static")

# Routers: API del equipo + vistas HTML
app.include_router(usuarios.router)
app.include_router(vehiculos.router)
app.include_router(vistas.router)


@app.get("/")
def root():
    return {
        "mensaje": "API SIVVE operativa. Ve a /web/catalogo para la interfaz gráfica o a /docs para la API."
    }