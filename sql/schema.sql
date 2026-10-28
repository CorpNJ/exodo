  CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    documento VARCHAR(20) UNIQUE NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255),
    rol VARCHAR(20) CHECK (rol IN ('admin', 'comprador')) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehiculos (
    id SERIAL PRIMARY KEY,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    anio INT NOT NULL,
    precio NUMERIC(12, 2) NOT NULL,
    kilometraje INT DEFAULT 0,
    especificaciones TEXT,
    fotos_url TEXT,
    estado VARCHAR(20) CHECK (estado IN ('Disponible', 'Vendido', 'Inactivo')) DEFAULT 'Disponible',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    vehiculo_id INT UNIQUE REFERENCES vehiculos(id),
    comprador_id INT REFERENCES usuarios(id),
    vendedor_id INT REFERENCES usuarios(id),
    monto_total NUMERIC(12, 2) NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facturas (
    id SERIAL PRIMARY KEY,
    venta_id INT UNIQUE REFERENCES ventas(id),
    codigo_factura VARCHAR(50) UNIQUE NOT NULL,
    monto NUMERIC(12, 2) NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
