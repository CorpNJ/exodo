from sqlalchemy import Column, DateTime, Integer, String, func

from ..database import Base


class UsuarioBD(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    contrasena_hash = Column(String(255))
    rol = Column(String(20), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())