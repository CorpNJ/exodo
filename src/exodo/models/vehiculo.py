from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Numeric, String, Text

from ..database import Base


class VehiculoBD(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    kilometraje = Column(Integer, default=0)
    especificaciones = Column(Text, nullable=True)
    estado = Column(String(20), default="Disponible")


class VehiculoRegistro(BaseModel):
    marca: str = Field(min_length=1, max_length=50)
    modelo: str = Field(min_length=1, max_length=50)
    anio: int = Field(ge=1900, le=2100)
    precio: float = Field(gt=0)
    kilometraje: int = Field(default=0, ge=0)
    especificaciones: str | None = None