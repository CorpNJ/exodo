<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, DateTime, func
from exodo.database import Base
=======
from sqlalchemy import Column, DateTime, Integer, String, func

from ..database import Base

>>>>>>> origin/main

class UsuarioBD(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
<<<<<<< HEAD
    contrasena_hash = Column(String(255), nullable=True)
=======
    contrasena_hash = Column(String(255))
>>>>>>> origin/main
    rol = Column(String(20), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())