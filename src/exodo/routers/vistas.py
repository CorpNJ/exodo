import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Request, Response, Depends, status, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from exodo.database import get_db
from exodo.models.vehiculo import VehiculoBD
from exodo.models.usuario import UsuarioBD
from exodo.models.venta import VentaBD, FacturaBD

router = APIRouter(prefix="/web", tags=["Frontend Web"])
templates = Jinja2Templates(directory="src/exodo/templates")


# Auxiliar per a verificar autenticació d'Administrador via Cookies
def es_admin(request: Request) -> bool:
    return request.cookies.get("session_role") == "admin"


# 1. Catálogo Público (US-011)
@router.get("/catalogo", response_class=HTMLResponse)
def ver_catalogo(request: Request, marca: str = None, estado: str = "Disponible", db: Session = Depends(get_db)):
    query = db.query(VehiculoBD).filter(VehiculoBD.estado != "Inactivo")
    if marca and marca.strip() != "":
        query = query.filter(VehiculoBD.marca.ilike(f"%{marca}%"))
    if estado and estado.strip() != "":
        query = query.filter(VehiculoBD.estado == estado)
    vehiculos = query.all()

    return templates.TemplateResponse(
        request,
        "catalogo.html",
        {
            "vehiculos": vehiculos,
            "marca_filtro": marca or "",
            "estado_filtro": estado or "",
            "es_admin": es_admin(request)
        }
    )


# 2. Vista de Detalle / Ficha Técnica del Vehículo (US-027)
@router.get("/vehiculo/{vehiculo_id}", response_class=HTMLResponse)
def ver_detalle(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if not vehiculo:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "detalle.html",
        {
            "vehiculo": vehiculo,
            "es_admin": es_admin(request)
        }
    )


# 3. Formulario de Registro de Comprador (US-024)
@router.get("/comprar/{vehiculo_id}", response_class=HTMLResponse)
def vista_registro_comprador(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id, VehiculoBD.estado == "Disponible").first()
    if not vehiculo:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "comprar.html",
        {
            "vehiculo": vehiculo,
            "es_admin": es_admin(request)
        }
    )


# 4. Procesar Venta, Registro del Comprador y Generación de Factura (US-015, US-024)
@router.post("/comprar/{vehiculo_id}")
def procesar_compra(
    vehiculo_id: int,
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # A. Crear o reutilitzar el comprador
        comprador = db.query(UsuarioBD).filter((UsuarioBD.correo == correo) | (UsuarioBD.documento == documento)).first()
        if not comprador:
            comprador = UsuarioBD(
                nombre=nombre,
                documento=documento,
                correo=correo,
                rol="comprador"
            )
            db.add(comprador)
            db.commit()
            db.refresh(comprador)

        # B. Validar disponibilitat del vehicle
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id, VehiculoBD.estado == "Disponible").first()
        if not vehiculo:
            return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

        # C. Marcar vehicle com a Vendido
        vehiculo.estado = "Vendido"

        # D. Registrar la venda
        venta = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo.id).first()
        if not venta:
            venta = VentaBD(
                vehiculo_id=vehiculo.id,
                comprador_id=comprador.id,
                monto_total=vehiculo.precio,
                fecha_venta=datetime.now()
            )
            db.add(venta)
            db.commit()
            db.refresh(venta)
        else:
            venta.comprador_id = comprador.id
            venta.monto_total = vehiculo.precio
            db.commit()

        # E. Generar la factura
        factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
        if not factura:
            codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
            factura = FacturaBD(
                venta_id=venta.id,
                codigo_factura=codigo_factura,
                monto=vehiculo.precio,
                fecha_emision=datetime.now()
            )
            db.add(factura)
            db.commit()
            db.refresh(factura)

        return RedirectResponse(url=f"/web/factura/{factura.id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        db.rollback()
        print(f"Error procesando compra: {e}")
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)


# 5. Vista de Factura (US-015)
@router.get("/factura/{factura_id}", response_class=HTMLResponse)
def ver_factura(request: Request, factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(FacturaBD).filter(FacturaBD.id == factura_id).first()
    if not factura:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    venta = db.query(VentaBD).filter(VentaBD.id == factura.venta_id).first()
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == venta.vehiculo_id).first() if venta else None
    comprador = db.query(UsuarioBD).filter(UsuarioBD.id == venta.comprador_id).first() if venta else None

    return templates.TemplateResponse(
        request,
        "factura.html",
        {
            "factura": factura,
            "venta": venta,
            "vehiculo": vehiculo,
            "comprador": comprador,
            "es_admin": es_admin(request)
        }
    )


# 6. Redirecció des de l'Inventari per a veure la factura d'un vehicle venut
@router.get("/admin/factura_vehiculo/{vehiculo_id}")
def ver_factura_por_vehiculo(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    venta = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo_id).first()
    if not venta:
        return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)

    factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
    if not factura:
        return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url=f"/web/factura/{factura.id}", status_code=status.HTTP_303_SEE_OTHER)    