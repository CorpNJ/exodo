from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import VehiculoBD, VehiculoRegistro, VehiculoRespuesta

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])


# US-010: registrar un vehiculo
@router.post("/", status_code=status.HTTP_201_CREATED)
def agregar_vehiculo(vehiculo: VehiculoRegistro, db: Session = Depends(get_db)):
    nuevo = VehiculoBD(**vehiculo.model_dump(), estado="Disponible")
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {
        "mensaje": f"Vehículo {nuevo.marca} {nuevo.modelo} registrado correctamente",
        "vehiculo_id": nuevo.id,
        "estado": nuevo.estado,
    }


# US-015 (historia #15): listar y filtrar vehiculos
@router.get("/", response_model=list[VehiculoRespuesta])
def listar_vehiculos(
    marca: str | None = None,
    modelo: str | None = None,
    anio: int | None = None,
    estado: str | None = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(VehiculoBD)

    if marca:
        consulta = consulta.filter(func.lower(VehiculoBD.marca) == marca.lower())
    if modelo:
        consulta = consulta.filter(func.lower(VehiculoBD.modelo) == modelo.lower())
    if anio:
        consulta = consulta.filter(VehiculoBD.anio == anio)

    if estado:
        consulta = consulta.filter(func.lower(VehiculoBD.estado) == estado.lower())
    else:
        # Por defecto no se muestran los vehiculos dados de baja
        consulta = consulta.filter(VehiculoBD.estado.is_distinct_from("Inactivo"))

    return consulta.order_by(VehiculoBD.id).all()


# Detalle de un vehiculo (apoya la vista de cada carro en el front)
@router.get("/{vehiculo_id}", response_model=VehiculoRespuesta)
def obtener_vehiculo(vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.get(VehiculoBD, vehiculo_id)
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El vehículo con ID {vehiculo_id} no existe en el inventario.",
        )
    return vehiculo


# US-015: marcar como vendido tras una compra
@router.post("/modificarstock/{vehiculo_id}")
def modificar_stock(vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.get(VehiculoBD, vehiculo_id)

    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El vehículo con ID {vehiculo_id} no existe en el inventario.",
        )

    # C-015b: si ya esta vendido, bloquear
    if vehiculo.estado == "Vendido":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehículo no disponible",
        )

    # C-015a: marcar como Vendido
    vehiculo.estado = "Vendido"
    db.commit()
    db.refresh(vehiculo)
    return {
        "mensaje": f"Compra confirmada. El vehículo {vehiculo.marca} {vehiculo.modelo} "
                   f"(ID: {vehiculo_id}) ha sido marcado como Vendido.",
        "estado_nuevo": vehiculo.estado,
    }


# Baja logica: reemplaza la opcion "Eliminar vehiculo" del antiguo CLI
@router.delete("/{vehiculo_id}")
def dar_de_baja(vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.get(VehiculoBD, vehiculo_id)

    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El vehículo con ID {vehiculo_id} no existe en el inventario.",
        )

    if vehiculo.estado == "Vendido":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede dar de baja un vehículo vendido",
        )

    vehiculo.estado = "Inactivo"
    db.commit()
    return {
        "mensaje": f"Vehículo {vehiculo.marca} {vehiculo.modelo} (ID: {vehiculo_id}) dado de baja",
        "estado_nuevo": vehiculo.estado,
    }