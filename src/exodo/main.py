from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

from .database import get_db

app = FastAPI()

# Configuración del modelo SQLAlchemy para la tabla 'vehiculos'
Base = declarative_base()

class VehiculoBD(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    anio = Column(Integer, nullable=False)
    precio = Column(Numeric, nullable=False)
    kilometraje = Column(Integer, default=0)
    especificaciones = Column(String, nullable=True)
    estado = Column(String, default="Disponible")

# Esquema Pydantic para validar los datos del vehículo que entran por JSON (US-010)
class VehiculoRegistro(BaseModel):
    marca: str
    modelo: str
    anio: int
    precio: float
    kilometraje: int = 0
    especificaciones: str = ""

# 1. Endpoint POST para registrar un nuevo vehículo en la base de datos (US-010)
@app.post("/vehiculos/", status_code=status.HTTP_201_CREATED)
def agregar_vehiculo(vehiculo: VehiculoRegistro, db: Session = Depends(get_db)):
    nuevo_vehiculo = VehiculoBD(
        marca=vehiculo.marca,
        modelo=vehiculo.modelo,
        anio=vehiculo.anio,
        precio=vehiculo.precio,
        kilometraje=vehiculo.kilometraje,
        especificaciones=vehiculo.especificaciones,
        estado="Disponible"
    )
    
    db.add(nuevo_vehiculo)
    db.commit()
    db.refresh(nuevo_vehiculo)

    return {
        "mensaje": f"Vehículo {nuevo_vehiculo.marca} {nuevo_vehiculo.modelo} registrado correctamente",
        "vehiculo_id": nuevo_vehiculo.id,
        "estado": nuevo_vehiculo.estado
    }

# 2. Endpoint POST para actualizar automáticamente el stock tras una compra (US-015)
@app.post("/modificarstock/{vehiculo_id}")
def modificar_stock(vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()

    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"El vehículo con ID {vehiculo_id} no existe en el inventario."
        )

    # Criterio C-015b: Si el vehículo ya está vendido, bloquear la transacción
    if vehiculo.estado == "Vendido":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Vehículo no disponible"
        )

    # Criterio C-015a: Marcar el vehículo como 'Vendido' y guardar cambios
    vehiculo.estado = "Vendido"
    db.commit()
    db.refresh(vehiculo)

    return {
        "mensaje": f"Compra confirmada. El vehículo {vehiculo.marca} {vehiculo.modelo} (ID: {vehiculo_id}) ha sido marcado como Vendido.",
        "estado_nuevo": vehiculo.estado
    }