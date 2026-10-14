SIVVE — Sistema de Inventario y Venta de Vehículos CorpNJ

📋 Descripción del proyecto

SIVVE centraliza el catálogo de vehículos de un concesionario, elimina la gestión manual, y automatiza el registro de ventas y la generación de facturas.

El sistema resuelve dos problemas críticos del proceso actual:

Doble venta: el inventario se actualiza en tiempo real al confirmar una compra, evitando que un mismo vehículo se venda dos veces. Descuadres de inventario: toda entrada, salida y cambio de estado de un vehículo queda registrada y trazada.

Funcionalidades principales:

Registro y edición de vehículos (ficha técnica, fotos, precio, estado) — acceso de vendedores mediante login. Catálogo público de consulta y filtrado (marca, precio, año) para compradores. Confirmación de compra con actualización automática del stock (< 3 segundos). Generación automática de factura al confirmar la venta. Reporte mensual de ventas por vehículo, vendedor y monto.

👥 Integrantes

Johan Quirama Acevedo

Juan Jose Vélez Arias

Nicolas Gomez

Backend: Java + Spring Boot (API REST)

Frontend: Angular

Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>

cd sivve

Levantar el backend (API + base de datos)
cd backend

./mvnw spring-boot:run

Levantar el frontend (en otra terminal)
cd frontend

npm install

ng serve

La aplicación Angular quedará disponible en http://localhost:4200 y se conectará al backend mediante la configuración de environment.ts (por defecto apuntando a http://localhost:8080/api).
