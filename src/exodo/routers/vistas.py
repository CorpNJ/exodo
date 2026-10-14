import os
import uuid
import shutil
from fastapi import APIRouter, Request, Response, Depends, status, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from exodo.database import get_db
from exodo.models.vehiculo import VehiculoBD
from exodo.models.usuario import UsuarioBD
from exodo.models.venta import VentaBD, FacturaBD

router = APIRouter(prefix="/web", tags=["Frontend Web"])
templates = Jinja2Templates(directory="src/exodo/templates")


# Auxiliar para verificar autenticación de Admin vía Cookies de sesión
def es_admin(request: Request) -> bool:
    return request.cookies.get("session_role") == "admin"


# 1. Catálogo Público (US-011)
@router.get("/catalogo", response_class=HTMLResponse)
def ver_catalogo(request: Request, marca: str = None, estado: str = "Disponible", db: Session = Depends(get_db)):
    query = db.query(VehiculoBD)
    if marca:
        query = query.filter(VehiculoBD.marca.ilike(f"%{marca}%"))
    if estado:
        query = query.filter(VehiculoBD.estado == estado)
    vehiculos = query.all()

    return templates.TemplateResponse(
        request,
        "catalogo.html",
        {
            "vehiculos": vehiculos,
            "marca_filtro": marca,
            "estado_filtro": estado,
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


# 3. Formulario de Registro de Comprador e Inicio de Proceso de Compra (US-024)
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


# 4. Procesar Venta, Registro del Comprador, Actualización de BD y Generación de Factura (US-015, US-024)
@router.post("/comprar/{vehiculo_id}")
def procesar_compra(
    vehiculo_id: int,
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    # A. Buscar o crear el comprador en la base de datos
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

    # B. Validar disponibilidad del vehículo
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id, VehiculoBD.estado == "Disponible").first()
    if not vehiculo:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    # C. Marcar Vehículo como Vendido (Criterio C-015a)
    vehiculo.estado = "Vendido"

    # D. Registrar Venta en BD
    nueva_venta = VentaBD(
        vehiculo_id=vehiculo.id,
        comprador_id=comprador.id,
        monto_total=vehiculo.precio
    )
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    # E. Generar Factura en BD
    codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
    nueva_factura = FacturaBD(
        venta_id=nueva_venta.id,
        codigo_factura=codigo_factura,
        monto=vehiculo.precio
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    # F. Redirigir a la vista de la factura
    return RedirectResponse(url=f"/web/factura/{nueva_factura.id}", status_code=status.HTTP_303_SEE_OTHER)


# 5. Vista e Impresión de Factura
@router.get("/factura/{factura_id}", response_class=HTMLResponse)
def ver_factura(request: Request, factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(FacturaBD).filter(FacturaBD.id == factura_id).first()
    if not factura:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)
    
    venta = db.query(VentaBD).filter(VentaBD.id == factura.venta_id).first()
    comprador = db.query(UsuarioBD).filter(UsuarioBD.id == venta.comprador_id).first()
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == venta.vehiculo_id).first()

    return templates.TemplateResponse(
        request,
        "factura.html",
        {
            "factura": factura,
            "venta": venta,
            "comprador": comprador,
            "vehiculo": vehiculo,
            "es_admin": es_admin(request)
        }
    )


# 6. Formulario de Inicio de Sesión Administrativo (US-023)
@router.get("/login", response_class=HTMLResponse)
def vista_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None, "es_admin": es_admin(request)})


@router.post("/login")
def procesar_login(
    request: Request,
    response: Response,
    usuario: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")

    if admin_user and admin_pass and usuario == admin_user and password == admin_pass:
        res = RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)
        res.set_cookie(key="session_role", value="admin")
        return res

    admin_bd = db.query(UsuarioBD).filter(
        (UsuarioBD.correo == usuario) | (UsuarioBD.nombre == usuario) | (UsuarioBD.documento == usuario),
        UsuarioBD.contrasena_hash == password,
        UsuarioBD.rol == "admin"
    ).first()

    if admin_bd:
        res = RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)
        res.set_cookie(key="session_role", value="admin")
        return res

    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "Usuario o contraseña de administrador incorrectos", "es_admin": False}
    )


@router.get("/logout")
def cerrar_sesion():
    res = RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie("session_role")
    return res


# 7. Panel Administrativo de Inventario (US-031 / Protegido)
@router.get("/admin/inventario", response_class=HTMLResponse)
def vista_admin_inventario(request: Request, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)
    
    vehiculos = db.query(VehiculoBD).all()
    return templates.TemplateResponse(
        request,
        "admin_inventario.html",
        {"vehiculos": vehiculos, "es_admin": True}
    )


# 8. Formulario para Registrar Vehículo (US-010 / Solo Admin)
@router.get("/registro", response_class=HTMLResponse)
def vista_registro(request: Request):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(request, "registro_vehiculo.html", {"es_admin": True})


@router.post("/registro")
def procesar_registro(
    request: Request,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: int = Form(...),
    precio: float = Form(...),
    kilometraje: int = Form(0),
    especificaciones: str = Form(""),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    ruta_imagen = None
    if foto and foto.filename:
        extension = foto.filename.split(".")[-1]
        nombre_unico = f"{uuid.uuid4().hex[:8]}.{extension}"
        destino = f"src/exodo/static/img/{nombre_unico}"
        
        with open(destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
            
        ruta_imagen = f"/static/img/{nombre_unico}"

    nuevo = VehiculoBD(
        marca=marca,
        modelo=modelo,
        anio=anio,
        precio=precio,
        kilometraje=kilometraje,
        especificaciones=especificaciones,
        estado="Disponible",
        fotos_url=ruta_imagen
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)


# 9. Editar Vehículo (US-025 / Solo Admin)
@router.get("/admin/editar/{vehiculo_id}", response_class=HTMLResponse)
def vista_editar_vehiculo(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)
    
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if not vehiculo:
        return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "editar_vehiculo.html",
        {"vehiculo": vehiculo, "es_admin": True}
    )


@router.post("/admin/editar/{vehiculo_id}")
def procesar_editar_vehiculo(
    request: Request,
    vehiculo_id: int,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: int = Form(...),
    precio: float = Form(...),
    estado: str = Form(...),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if vehiculo:
        vehiculo.marca = marca
        vehiculo.modelo = modelo
        vehiculo.anio = anio
        vehiculo.precio = precio
        vehiculo.estado = estado
        db.commit()

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)


# 10. Reporte de Ventas (US-030 / Solo Admin)
@router.get("/admin/reportes", response_class=HTMLResponse)
def vista_reporte_ventas(request: Request, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    ventas = db.query(VentaBD).all()
    reporte = []
    total_ingresos = 0

    for v in ventas:
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == v.vehiculo_id).first()
        comprador = db.query(UsuarioBD).filter(UsuarioBD.id == v.comprador_id).first()
        total_ingresos += float(v.monto_total or 0)
        reporte.append({
            "venta_id": v.id,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "N/A",
            "comprador": comprador.nombre if comprador else "N/A",
            "documento": comprador.documento if comprador else "N/A",
            "monto": v.monto_total,
            "fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M") if v.fecha_venta else "N/A"
        })

    return templates.TemplateResponse(
        request,
        "reporte_ventas.html",
        {
            "reporte": reporte,
            "total_ingresos": total_ingresos,
            "es_admin": True
        }
    )