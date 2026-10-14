from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from exodo.routers import vehiculos, vistas

app = FastAPI(title="SIVVE - Sistema de Inventario")

# Montar carpeta de archivos estáticos
app.mount("/static", StaticFiles(directory="src/exodo/static"), name="static")

# Incluir los routers (API y Vistas HTML)
app.include_router(vehiculos.router)
app.include_router(vistas.router)

@app.get("/")
def root():
    return {"mensaje": "API SIVVE Operativa. Ve a /web/catalogo para acceder a la interfaz gráfica."}
from .routers import usuarios, vehiculos

app = FastAPI(title="Exodo API")

app.include_router(usuarios.router)
app.include_router(vehiculos.router)

@app.get("/")
def root():
    return {"message": "API de Exodo funcionando. Ve a /docs para probar."}
