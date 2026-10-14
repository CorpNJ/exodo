<<<<<<< HEAD
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Numeric
from exodo.database import Base


# Modelo SQLAlchemy
=======
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, Integer, Numeric, String, Text

from ..database import Base


>>>>>>> origin/main
class VehiculoBD(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD
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
=======
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    kilometraje = Column(Integer, default=0)
    especificaciones = Column(Text, nullable=True)
    estado = Column(String(20), default="Disponible")


class VehiculoRegistro(BaseModel):
    """Entrada JSON para registrar un vehiculo (US-010)."""
    marca: str = Field(min_length=1, max_length=50)
    modelo: str = Field(min_length=1, max_length=50)
    anio: int = Field(ge=1900, le=2100)
    precio: float = Field(gt=0)
    kilometraje: int = Field(default=0, ge=0)
    especificaciones: str | None = None


class VehiculoRespuesta(BaseModel):
    """Salida JSON de un vehiculo (listado, filtros y detalle)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
>>>>>>> origin/main
    marca: str
    modelo: str
    anio: int
    precio: float
<<<<<<< HEAD
    kilometraje: int = 0
    especificaciones: str = ""
    fotos_url: str | None = None


class VehiculoRespuesta(VehiculoRegistro):
    id: int
    estado: str

    class Config:
        from_attributes = True
=======
    kilometraje: int | None
    especificaciones: str | None
    estado: str | None
>>>>>>> origin/main
