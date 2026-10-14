from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Numeric
from exodo.database import Base


# Modelo SQLAlchemy
class VehiculoBD(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(100), nullable=False)
    modelo = Column(String(100), nullable=False)
    anio = Column(Integer, nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    kilometraje = Column(Integer, default=0)
    especificaciones = Column(String(255), nullable=True)
    estado = Column(String(50), default="Disponible")
    fotos_url = Column(String(255), nullable=True)  # <-- Cambiado de imagen_url a fotos_url


# Esquema Pydantic
class VehiculoRegistro(BaseModel):
    marca: str
    modelo: str
    anio: int
    precio: float
    kilometraje: int = 0
    especificaciones: str = ""
    fotos_url: str | None = None


class VehiculoRespuesta(VehiculoRegistro):
    id: int
    estado: str

    class Config:
        from_attributes = True