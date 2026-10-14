// Función para comprar un vehículo y actualizar stock (US-015)
async function comprarVehiculo(vehiculoId) {
    if (!confirm("¿Deseas confirmar la compra de este vehículo?")) return;

    try {
        const response = await fetch(`/vehiculos/modificarstock/${vehiculoId}`, {
            method: 'POST'
        });
        const data = await response.json();

        if (response.ok) {
            alert(data.mensaje);
            window.location.reload();
        } else {
            alert("Error: " + (data.detail || "No se pudo realizar la compra."));
        }
    } catch (error) {
        console.error("Error al procesar la compra:", error);
        alert("Ocurrió un error en la comunicación con el servidor.");
    }
}

// Operaciones asíncronas sin alertas flotantes del navegador
async function cambiarEstado(vehiculoId, nuevoEstado) {
    try {
        const response = await fetch(`/vehiculos/estado/${vehiculoId}?estado=${nuevoEstado}`, {
            method: 'PUT'
        });
        if (response.ok) {
            window.location.reload();
        }
    } catch (error) {
        console.error("Error al actualizar el estado:", error);
    }
}