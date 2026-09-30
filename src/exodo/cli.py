from vehiculo import Vehiculo
from inventario import Inventario

def mostrar_menu():
    print("\nSIVVE - Sistema de Inventario")
    print("1. Registrar vehículo")
    print("2. Buscar vehículo")
    print("3. Mostrar inventario")
    print("4. Eliminar vehículo")
    print("5. Salir")
    return input("Seleccione una opción: ")

def ejecutar_programa():
    inventario = Inventario()

    while True:
        opcion = mostrar_menu()

        if opcion == "1":
            vin = input("VIN: ")
            placa = input("Placa: ")
            marca = input("Marca: ")
            modelo = input("Modelo: ")
            anio = input("Año: ")
            precio = input("Precio: ")

            auto = Vehiculo(vin, placa, marca, modelo, anio, precio)
            inventario.registrar_vehiculo(auto)

        elif opcion == "2":
            criterio = input("Buscar por (vin, placa, marca, modelo, anio, estado): ").lower()
            valor = input(f"Ingrese el valor para {criterio}: ")
            
            resultados = inventario.filtrar_vehiculos(criterio, valor)
            
            if resultados:
                for auto in resultados:
                    print(auto)
            else:
                print("No se encontraron resultados.")

        elif opcion == "3":
            inventario.mostrar_inventario()

        elif opcion == "4":
            vin_eliminar = input("Ingrese el VIN del vehículo a eliminar: ")
            inventario.eliminar_vehiculo(vin_eliminar)

        elif opcion == "5":
            print("Saliendo del sistema.")
            break

        else:
            print("Opción inválida.")

if __name__ == "__main__":
    ejecutar_programa()