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


# Auxiliar para verificar autenticación de Admin vía Cookies de sesión
def es_admin(request: Request) -> bool:
    return request.cookies.get("session_role") == "admin"


# 1. Catálogo Público (Oculta vehículos inactivos - US-011, US-026)
@router.get("/catalogo", response_class=HTMLResponse)
def ver_catalogo(request: Request, marca: str = None, estado: str = "Disponible", db: Session = Depends(get_db)):
    query = db.query(VehiculoBD).filter(VehiculoBD.estado != "Inactivo")
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
# 3. Formulario de Registro de Comprador (US-024)
@router.get("/comprar/{vehiculo_id}", response_class=HTMLResponse)
def vista_registro_comprador(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    
    # Si el vehículo no existe o no está disponible, redirigir al catálogo
    if not vehiculo or vehiculo.estado != "Disponible":
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        request,
        "comprar.html",
        {
            "vehiculo": vehiculo,
            "es_admin": es_admin(request)
        }
    )


# 4. Procesar Venta, Registro del Comprador y Factura (US-015, US-024)
@router.post("/comprar/{vehiculo_id}")
def procesar_compra(
    vehiculo_id: int,
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    comprador = db.query(UsuarioBD).filter((UsuarioBD.correo == correo) | (UsuarioBD.documento == documento)).first()
    if not comprador:
        comprador = UsuarioBD(nombre=nombre, documento=documento, correo=correo, rol="comprador")
        db.add(comprador)
        db.commit()
        db.refresh(comprador)

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id, VehiculoBD.estado == "Disponible").first()
    if not vehiculo:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo.estado = "Vendido"

    # Verificación defensiva contra duplicados de UNIQUE en Postgres
    venta = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo.id).first()
    if not venta:
        venta = VentaBD(vehiculo_id=vehiculo.id, comprador_id=comprador.id, monto_total=vehiculo.precio)
        db.add(venta)
        db.commit()
        db.refresh(venta)
    else:
        venta.comprador_id = comprador.id
        venta.monto_total = vehiculo.precio
        db.commit()

    factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
    if not factura:
        codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
        factura = FacturaBD(venta_id=venta.id, codigo_factura=codigo_factura, monto=vehiculo.precio)
        db.add(factura)
        db.commit()
        db.refresh(factura)

    return RedirectResponse(url=f"/web/factura/{factura.id}", status_code=status.HTTP_303_SEE_OTHER)
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

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id, VehiculoBD.estado == "Disponible").first()
    if not vehiculo:
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo.estado = "Vendido"

    nueva_venta = VentaBD(
        vehiculo_id=vehiculo.id,
        comprador_id=comprador.id,
        monto_total=vehiculo.precio
    )
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
    nueva_factura = FacturaBD(
        venta_id=nueva_venta.id,
        codigo_factura=codigo_factura,
        monto=vehiculo.precio
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

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


# 8. Formulario para Registrar Vehículo con Subida Local de Foto (US-010 / Solo Admin)
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

    try:
        ruta_imagen = None
        if foto and foto.filename:
            os.makedirs("src/exodo/static/img", exist_ok=True)
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

    except Exception as e:
        db.rollback()
        print(f"Error al registrar vehículo: {e}")
        return templates.TemplateResponse(
            request,
            "registro_vehiculo.html",
            {"error": "Error al guardar el vehículo. Verifica que el precio no exceda los rangos permitidos.", "es_admin": True}
        )
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    ruta_imagen = None
    if foto and foto.filename:
        os.makedirs("src/exodo/static/img", exist_ok=True)
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


# 9. Editar Ficha Técnica y Estado (US-025, US-026 / Solo Admin)
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
    especificaciones: str = Form(""),
    estado: str = Form(...),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if vehiculo:
        estado_anterior = vehiculo.estado
        
        vehiculo.marca = marca
        vehiculo.modelo = modelo
        vehiculo.anio = anio
        vehiculo.precio = precio
        vehiculo.especificaciones = especificaciones
        vehiculo.estado = estado
        db.commit()

        # Si el administrador cambia el estado a 'Vendido' y no existe factura previa
        if estado == "Vendido" and estado_anterior != "Vendido":
            # Verificar si ya existe una venta asociada
            venta_existente = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo.id).first()
            if not venta_existente:
                # Obtener usuario administrador actual o de sistema para asignar como vendedor/comprador genérico
                admin_user = db.query(UsuarioBD).filter(UsuarioBD.rol == "admin").first()
                comprador_id = admin_user.id if admin_user else 1

                nueva_venta = VentaBD(
                    vehiculo_id=vehiculo.id,
                    comprador_id=comprador_id,
                    vendedor_id=comprador_id,
                    monto_total=vehiculo.precio
                )
                db.add(nueva_venta)
                db.commit()
                db.refresh(nueva_venta)

                codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
                nueva_factura = FacturaBD(
                    venta_id=nueva_venta.id,
                    codigo_factura=codigo_factura,
                    monto=vehiculo.precio
                )
                db.add(nueva_factura)
                db.commit()
                db.refresh(nueva_factura)

                # Redirigir directamente a la factura generada
                return RedirectResponse(url=f"/web/factura/{nueva_factura.id}", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if vehiculo:
        vehiculo.marca = marca
        vehiculo.modelo = modelo
        vehiculo.anio = anio
        vehiculo.precio = precio
        vehiculo.especificaciones = especificaciones
        vehiculo.estado = estado
        db.commit()

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)


# 10. Reporte de Ventas Mensuales e Ingresos Gráficos (US-022, US-030 / Solo Admin)
@router.get("/admin/reportes", response_class=HTMLResponse)
@router.get("/admin/reporte_ventas", response_class=HTMLResponse)
def vista_reporte_ventas(request: Request, mes: str = None, anio: str = None, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    ahora = datetime.now()
    
    # Manejo seguro de conversión para evitar ValueError con strings vacíos o None
    try:
        mes_select = int(mes) if mes and str(mes).strip() != "" else ahora.month
    except ValueError:
        mes_select = ahora.month

    try:
        anio_select = int(anio) if anio and str(anio).strip() != "" else ahora.year
    except ValueError:
        anio_select = ahora.year

    # 1. Ventas filtradas del período seleccionado
    ventas = db.query(VentaBD).filter(
        extract('month', VentaBD.fecha_venta) == mes_select,
        extract('year', VentaBD.fecha_venta) == anio_select
    ).all()

    reporte = []
    total_ingresos = 0.0

    for v in ventas:
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == v.vehiculo_id).first()
        vendedor = db.query(UsuarioBD).filter(UsuarioBD.id == v.vendedor_id).first() if v.vendedor_id else None
        monto = float(v.monto_total or 0)
        total_ingresos += monto

        reporte.append({
            "venta_id": v.id,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "N/A",
            "vendedor": vendedor.nombre if vendedor else "Sistema / Directo",
            "monto": monto,
            "fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M") if v.fecha_venta else "N/A"
        })

    # 2. Sumatoria por mes para el Gráfico de Barras de Chart.js
    ingresos_por_mes = db.query(
        extract('month', VentaBD.fecha_venta).label('mes'),
        func.sum(VentaBD.monto_total).label('total')
    ).filter(extract('year', VentaBD.fecha_venta) == anio_select).group_by('mes').all()

    grafico_labels = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    grafico_data = [0] * 12
    for reg in ingresos_por_mes:
        if reg.mes:
            grafico_data[int(reg.mes) - 1] = float(reg.total or 0)

    lista_meses = [
        {"num": 1, "nombre": "Enero"}, {"num": 2, "nombre": "Febrero"},
        {"num": 3, "nombre": "Marzo"}, {"num": 4, "nombre": "Abril"},
        {"num": 5, "nombre": "Mayo"}, {"num": 6, "nombre": "Junio"},
        {"num": 7, "nombre": "Julio"}, {"num": 8, "nombre": "Agosto"},
        {"num": 9, "nombre": "Septiembre"}, {"num": 10, "nombre": "Octubre"},
        {"num": 11, "nombre": "Noviembre"}, {"num": 12, "nombre": "Diciembre"}
    ]
    lista_anios = list(range(2024, 2028))

    return templates.TemplateResponse(
        request,
        "reporte_ventas.html",
        {
            "reporte": reporte,
            "total_ingresos": total_ingresos,
            "total_ventas": len(reporte),
            "mes_actual": mes_select,
            "anio_actual": anio_select,
            "lista_meses": lista_meses,
            "lista_anios": lista_anios,
            "grafico_labels": grafico_labels,
            "grafico_data": grafico_data,
            "es_admin": True
        }
    )