from vehiculo import Vehiculo

class Inventario:
    def __init__(self):
        self.lista_vehiculos = []

    def registrar_vehiculo(self, vehiculo):
        for v in self.lista_vehiculos:
            if v.vin == vehiculo.vin:
                print(f"Error: El VIN {vehiculo.vin} ya está registrado.")
                return False
        
        self.lista_vehiculos.append(vehiculo)
        print(f"Vehículo {vehiculo.marca} {vehiculo.modelo} registrado correctamente.")
        return True

    def filtrar_vehiculos(self, criterio, valor):
        resultados = []
        for v in self.lista_vehiculos:
            if str(getattr(v, criterio, "")).lower() == str(valor).lower():
                resultados.append(v)
        return resultados

    def mostrar_inventario(self):
        if not self.lista_vehiculos:
            print("El inventario está vacío.")
            return
            
        for v in self.lista_vehiculos:
            print(v)

    def eliminar_vehiculo(self, vin):
        for v in self.lista_vehiculos:
            if v.vin == vin:
                self.lista_vehiculos.remove(v)
                print(f"Vehículo con VIN {vin} eliminado del inventario.")
                return True
        
        print(f"No se encontró ningún vehículo con el VIN {vin}.")
        return False