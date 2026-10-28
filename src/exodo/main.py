from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from exodo.routers import vehiculos, vistas

# Instancia única principal de FastAPI
app = FastAPI(title="SIVVE - Sistema de Inventario")

# Montar carpeta de archivos estáticos (para CSS, JS e imágenes locales)
app.mount("/static", StaticFiles(directory="src/exodo/static"), name="static")

# Incluir los routers del backend y del frontend web
app.include_router(vehiculos.router)
app.include_router(vistas.router)

@app.get("/")
def root():
    return {"mensaje": "API SIVVE Operativa. Ve a /web/catalogo para acceder a la interfaz gráfica."}