from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String, func
from exodo.database import Base

class VentaBD(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), unique=True)
    comprador_id = Column(Integer, ForeignKey("usuarios.id"))
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    monto_total = Column(Numeric(12, 2), nullable=False)
    fecha_venta = Column(DateTime, server_default=func.now())

class FacturaBD(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"), unique=True)
    codigo_factura = Column(String(50), unique=True, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_emision = Column(DateTime, server_default=func.now())