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


# 3. Autenticación: Login y Logout de Administrador (US-023)
# GET: Muestra la pantalla del formulario de inicio de sesión
@router.get("/login", response_class=HTMLResponse)
def vista_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None, "es_admin": es_admin(request)})

# POST: Recibe las credenciales enviadas desde el formulario
@router.post("/login", response_class=HTMLResponse)
def procesar_login(
    request: Request, 
    correo: str = Form(...), 
    contrasena: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Validar contra la base de datos o variables de entorno
    usuario = db.query(UsuarioBD).filter(
        UsuarioBD.correo == correo, 
        UsuarioBD.contrasena_hash == contrasena, 
        UsuarioBD.rol == "admin"
    ).first()
    
    if not usuario:
        return templates.TemplateResponse(
            request, 
            "login.html", 
            {"error": "Credenciales inválidas o no autorizadas.", "es_admin": False}
        )

    response = RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="session_role", value="admin", httponly=True)
    return response


@router.get("/logout")
def cerrar_sesion():
    response = RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_role")
    return response


# 4. Formulario de Registro de Comprador (US-024)
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


# 5. Procesar Compra, Registro del Comprador, Actualización de BD y Generación de Factura (US-015, US-024)
@router.post("/comprar/{vehiculo_id}")
def procesar_compra(
    vehiculo_id: int,
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
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
            monto_total=vehiculo.precio,
            fecha_venta=datetime.now()
        )
        db.add(nueva_venta)
        db.commit()
        db.refresh(nueva_venta)

        codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
        nueva_factura = FacturaBD(
            venta_id=nueva_venta.id,
            codigo_factura=codigo_factura,
            monto=vehiculo.precio,
            fecha_emision=datetime.now()
        )
        db.add(nueva_factura)
        db.commit()
        db.refresh(nueva_factura)

        return RedirectResponse(url=f"/web/factura/{nueva_factura.id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        db.rollback()
        print(f"Error procesando compra: {e}")
        return RedirectResponse(url="/web/catalogo", status_code=status.HTTP_303_SEE_OTHER)


# 6. Ver Factura de Venta Generada (US-015)
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


# 7. Panel de Gestión de Inventario (Solo Admin - US-010, US-025, US-026)
@router.get("/admin/inventario", response_class=HTMLResponse)
def vista_admin_inventario(request: Request, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    vehiculos = db.query(VehiculoBD).all()
    return templates.TemplateResponse(request, "admin_inventario.html", {"vehiculos": vehiculos, "es_admin": True})


# 8. Registrar Vehículo en Inventario (Solo Admin - US-010)
@router.get("/admin/registro", response_class=HTMLResponse)
def vista_registro_vehiculo(request: Request):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "registro_vehiculo.html", {"es_admin": True})


@router.post("/admin/registro")
def procesar_registro_vehiculo(
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

    # Limitar valores maximos para evitar desbordamiento (Overflow) en la BD
    precio_validado = min(abs(precio), 9999999999.0)
    kilometraje_validado = min(abs(kilometraje), 2000000)

    foto_url = None
    if foto and foto.filename:
        extension = os.path.splitext(foto.filename)[1]
        nombre_foto = f"{uuid.uuid4()}{extension}"
        ruta_destino = os.path.join("src/exodo/static/img", nombre_foto)
        os.makedirs("src/exodo/static/img", exist_ok=True)
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        foto_url = f"/static/img/{nombre_foto}"

    try:
        nuevo_vehiculo = VehiculoBD(
            marca=marca,
            modelo=modelo,
            anio=anio,
            precio=precio_validado,
            kilometraje=kilometraje_validado,
            especificaciones=especificaciones,
            fotos_url=foto_url,
            estado="Disponible"
        )
        db.add(nuevo_vehiculo)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error registrando vehiculo: {e}")

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)


# 9. Editar Ficha Técnica y Estado de Vehículo (Solo Admin - US-025, US-026)
@router.get("/admin/editar/{vehiculo_id}", response_class=HTMLResponse)
def vista_editar_vehiculo(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
    if not vehiculo:
        return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(request, "editar_vehiculo.html", {"vehiculo": vehiculo, "es_admin": True})


@router.post("/admin/editar/{vehiculo_id}")
def procesar_editar_vehiculo(
    request: Request,
    vehiculo_id: int,
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: int = Form(...),
    precio: float = Form(...),
    kilometraje: int = Form(0),  # <-- CAMBIO CLAVE: Form(0) en lugar de Form(...) para hacerlo opcional
    especificaciones: str = Form(""),
    estado: str = Form(...),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
        if vehiculo:
            vehiculo.marca = marca
            vehiculo.modelo = modelo
            vehiculo.anio = anio
            vehiculo.precio = min(abs(precio), 9999999999.0)
            vehiculo.kilometraje = min(abs(kilometraje), 2000000)
            vehiculo.especificaciones = especificaciones
            vehiculo.estado = estado

            if foto and foto.filename:
                extension = os.path.splitext(foto.filename)[1]
                nombre_foto = f"{uuid.uuid4()}{extension}"
                ruta_destino = os.path.join("src/exodo/static/img", nombre_foto)
                os.makedirs("src/exodo/static/img", exist_ok=True)
                with open(ruta_destino, "wb") as buffer:
                    shutil.copyfileobj(foto.file, buffer)
                vehiculo.fotos_url = f"/static/img/{nombre_foto}"

            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error editando vehiculo {vehiculo_id}: {e}")

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)
# 10. Eliminar Vehículo de Forma Segura (Solo Admin)
@router.post("/admin/eliminar/{vehiculo_id}")
def eliminar_vehiculo_completo(request: Request, vehiculo_id: int, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
        if vehiculo:
            venta = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo.id).first()
            if venta:
                factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
                if factura:
                    db.delete(factura)
                    db.flush()

                db.delete(venta)
                db.flush()

            if vehiculo.fotos_url and vehiculo.fotos_url.startswith("/static/img/"):
                nombre_archivo = vehiculo.fotos_url.replace("/static/img/", "")
                ruta_disco = os.path.join("src/exodo/static/img", nombre_archivo)
                if os.path.exists(ruta_disco):
                    try:
                        os.remove(ruta_disco)
                    except Exception:
                        pass

            db.delete(vehiculo)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar vehículo {vehiculo_id}: {e}")

    return RedirectResponse(url="/web/admin/inventario", status_code=status.HTTP_303_SEE_OTHER)


# 11. Reporte de Ventas Mensuales y Gráfico (Solo Admin - US-022, US-030)
@router.get("/admin/reportes", response_class=HTMLResponse)
@router.get("/admin/reporte_ventas", response_class=HTMLResponse)
def vista_reporte_ventas(request: Request, mes: str = None, anio: str = None, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    ahora = datetime.now()
    try:
        mes_select = int(mes) if mes and str(mes).strip() != "" else ahora.month
    except ValueError:
        mes_select = ahora.month

    try:
        anio_select = int(anio) if anio and str(anio).strip() != "" else ahora.year
    except ValueError:
        anio_select = ahora.year

    ventas = db.query(VentaBD).filter(
        extract('month', VentaBD.fecha_venta) == mes_select,
        extract('year', VentaBD.fecha_venta) == anio_select
    ).all()

    reporte = []
    total_ingresos = 0.0

    for v in ventas:
        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == v.vehiculo_id).first()
        comprador = db.query(UsuarioBD).filter(UsuarioBD.id == v.comprador_id).first()
        monto = float(v.monto_total or 0)
        total_ingresos += monto

        reporte.append({
            "venta_id": v.id,
            "vehiculo_id": v.vehiculo_id,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "N/A",
            "comprador_id": v.comprador_id,
            "comprador": comprador.nombre if comprador else "N/A",
            "documento": comprador.documento if comprador else "N/A",
            "correo": comprador.correo if comprador else "",
            "monto": monto,
            "fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M") if v.fecha_venta else "N/A",
            "fecha_iso": v.fecha_venta.strftime("%Y-%m-%dT%H:%M") if v.fecha_venta else ""
        })

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
    todos_vehiculos = db.query(VehiculoBD).all()

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
            "todos_vehiculos": todos_vehiculos,
            "grafico_labels": grafico_labels,
            "grafico_data": grafico_data,
            "es_admin": True
        }
    )


# 12. Registrar Venta Manualmente (Solo Admin)
@router.post("/admin/venta/crear")
def crear_venta_manual(
    request: Request,
    vehiculo_id: int = Form(...),
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    monto: float = Form(...),
    fecha: str = Form(...),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
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
        else:
            comprador.nombre = nombre
            comprador.documento = documento
            comprador.correo = correo
            db.commit()

        try:
            if "T" in fecha:
                fecha_parsed = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
            else:
                fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            fecha_parsed = datetime.now()

        vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
        if vehiculo:
            vehiculo.estado = "Vendido"

        monto_validado = min(abs(monto), 9999999999.0)

        venta = db.query(VentaBD).filter(VentaBD.vehiculo_id == vehiculo_id).first()
        if not venta:
            venta = VentaBD(
                vehiculo_id=vehiculo_id,
                comprador_id=comprador.id,
                monto_total=monto_validado,
                fecha_venta=fecha_parsed
            )
            db.add(venta)
            db.commit()
            db.refresh(venta)
        else:
            venta.comprador_id = comprador.id
            venta.monto_total = monto_validado
            venta.fecha_venta = fecha_parsed
            db.commit()

        factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
        if not factura:
            codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
            factura = FacturaBD(
                venta_id=venta.id,
                codigo_factura=codigo_factura,
                monto=monto_validado,
                fecha_emision=fecha_parsed
            )
            db.add(factura)
            db.commit()
        else:
            factura.monto = monto_validado
            factura.fecha_emision = fecha_parsed
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error al registrar venta manual: {e}")

    return RedirectResponse(url="/web/admin/reportes", status_code=status.HTTP_303_SEE_OTHER)


# 13. Editar Venta y Factura Existente (Solo Admin)
@router.post("/admin/venta/editar/{venta_id}")
def editar_venta(
    request: Request,
    venta_id: int,
    vehiculo_id: int = Form(...),
    nombre: str = Form(...),
    documento: str = Form(...),
    correo: str = Form(...),
    monto: float = Form(...),
    fecha: str = Form(...),
    db: Session = Depends(get_db)
):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        venta = db.query(VentaBD).filter(VentaBD.id == venta_id).first()
        if venta:
            if venta.vehiculo_id != vehiculo_id:
                vehiculo_anterior = db.query(VehiculoBD).filter(VehiculoBD.id == venta.vehiculo_id).first()
                if vehiculo_anterior:
                    vehiculo_anterior.estado = "Disponible"

                vehiculo_nuevo = db.query(VehiculoBD).filter(VehiculoBD.id == vehiculo_id).first()
                if vehiculo_nuevo:
                    vehiculo_nuevo.estado = "Vendido"

                venta.vehiculo_id = vehiculo_id

            comprador = db.query(UsuarioBD).filter(UsuarioBD.id == venta.comprador_id).first()
            if comprador:
                comprador.nombre = nombre
                comprador.documento = documento
                comprador.correo = correo
            else:
                comprador = UsuarioBD(nombre=nombre, documento=documento, correo=correo, rol="comprador")
                db.add(comprador)
                db.flush()
                venta.comprador_id = comprador.id

            try:
                if "T" in fecha:
                    fecha_parsed = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
                else:
                    fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                fecha_parsed = venta.fecha_venta or datetime.now()

            monto_validado = min(abs(monto), 9999999999.0)
            venta.monto_total = monto_validado
            venta.fecha_venta = fecha_parsed

            factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
            if factura:
                factura.monto = monto_validado
                factura.fecha_emision = fecha_parsed
            else:
                codigo_factura = f"FACT-{uuid.uuid4().hex[:8].upper()}"
                factura = FacturaBD(
                    venta_id=venta.id,
                    codigo_factura=codigo_factura,
                    monto=monto_validado,
                    fecha_emision=fecha_parsed
                )
                db.add(factura)

            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error al editar venta {venta_id}: {e}")

    return RedirectResponse(url="/web/admin/reportes", status_code=status.HTTP_303_SEE_OTHER)


# 14. Eliminar Venta y Factura del Reporte (Solo Admin)
@router.post("/admin/venta/eliminar/{venta_id}")
def eliminar_venta(request: Request, venta_id: int, db: Session = Depends(get_db)):
    if not es_admin(request):
        return RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        venta = db.query(VentaBD).filter(VentaBD.id == venta_id).first()
        if venta:
            factura = db.query(FacturaBD).filter(FacturaBD.venta_id == venta.id).first()
            if factura:
                db.delete(factura)
                db.flush()

            vehiculo = db.query(VehiculoBD).filter(VehiculoBD.id == venta.vehiculo_id).first()
            if vehiculo:
                vehiculo.estado = "Disponible"

            db.delete(venta)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar la venta {venta_id}: {e}")

    return RedirectResponse(url="/web/admin/reportes", status_code=status.HTTP_303_SEE_OTHER)