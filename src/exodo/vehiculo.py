class Vehiculo:
    def __init__(self, vin, placa, marca, modelo, anio, precio, estado="Disponible"):
        self.vin = vin
        self.placa = placa
        self.marca = marca
        self.modelo = modelo
        self.anio = anio
        self.precio = precio
        self.estado = estado

    def __str__(self):
        return f"[{self.placa}] {self.marca} {self.modelo} ({self.anio}) - ${self.precio} - {self.estado}"