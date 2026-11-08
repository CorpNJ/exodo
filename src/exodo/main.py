from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from exodo.database import engine, SessionLocal
from exodo.models.vehiculo import Base, VehiculoBD
from exodo.models.usuario import UsuarioBD
from exodo.routers import vehiculos, vistas

app = FastAPI(title="SIVVE - Sistema de Inventario y Venta de Vehículos")

# Precarga automática de tablas y datos de prueba al iniciar la app (Requisito Docker)
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Crear Administrador por defecto
        admin = db.query(UsuarioBD).filter(UsuarioBD.correo == "admin@sivve.com").first()
        if not admin:
            admin = UsuarioBD(
                nombre="Administrador SIVVE",
                documento="123456789",
                correo="admin@sivve.com",
                contrasena_hash="admin123",
                rol="admin"
            )
            db.add(admin)

        # 2. Crear Comprador de prueba
        comprador = db.query(UsuarioBD).filter(UsuarioBD.correo == "comprador@sivve.com").first()
        if not comprador:
            comprador = UsuarioBD(
                nombre="Carlos Ramírez",
                documento="1098765432",
                correo="comprador@sivve.com",
                contrasena_hash="comprador123",
                rol="comprador"
            )
            db.add(comprador)

        # 3. Crear Vehículos de prueba iniciales
        if not db.query(VehiculoBD).first():
            v1 = VehiculoBD(
                marca="Toyota",
                modelo="Corolla",
                anio=2023,
                precio=95000000,
                kilometraje=15000,
                especificaciones="Motor 2.0, Transmisión Automática CVT",
                estado="Disponible"
            )
            v2 = VehiculoBD(
                marca="Mazda",
                modelo="CX-5",
                anio=2024,
                precio=135000000,
                kilometraje=5000,
                especificaciones="Motor 2.5 Skyactiv-G AWD",
                estado="Disponible"
            )
            db.add_all([v1, v2])

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error cargando seed data: {e}")
    finally:
        db.close()

# Servir archivos estáticos (CSS, JS, imágenes subidas)
app.mount("/static", StaticFiles(directory="src/exodo/static"), name="static")

# Incluir routers del backend (JSON) y frontend (HTML)
app.include_router(vehiculos.router)
app.include_router(vistas.router)

@app.get("/")
def root():
    return {"mensaje": "API SIVVE Operativa. Ve a /web/catalogo para acceder al catálogo."}