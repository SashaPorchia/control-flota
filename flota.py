# PROGRAMA PRINCIPAL - CONTROL DE FLOTA MODULAR
import funciones

while True:
    print("\n=== SISTEMA CONTROL DE FLOTA ===")
    print("1. Ver resumen de la flota")
    print("2. Registrar Ingreso o Gasto")
    print("3. Salir")
    
    opcion = input("Elegí una opción (1-3): ")
    
    if opcion == "1":
        funciones.mostrar_resumen_flota()  # Llamamos a la función que está en funciones.py
    elif opcion == "2":
        funciones.registrar_movimiento()   # Llamamos a la otra función
    elif opcion == "3":
        print("¡Gracias por usar el sistema! Saliendo...")
        break
    else:
        print("Opción incorrecta, probá de nuevo.")