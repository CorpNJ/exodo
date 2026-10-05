from fastapi import FastAPI
from .routers import usuarios, vehiculos

app = FastAPI(title="Exodo API")

app.include_router(usuarios.router)
app.include_router(vehiculos.router)

@app.get("/")
def root():
    return {"message": "API de Exodo funcionando. Ve a /docs para probar."}