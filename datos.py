# ============================================================
# DATOS.PY - Persistencia de datos de la flota
# ============================================================

import json  # Para leer/escribir archivos JSON
import os    # Para verificar si el archivo existe

# Nombre del archivo donde se guardan todos los datos de la flota
ARCHIVO_DATOS = "datos_flota_v5.json"

# ============================================================
# DATOS INICIALES: Vehiculos precargados la primera vez que se ejecuta el programa
# Cada vehiculo tiene: modelo, facturacion, poliza de seguro,
# vencimientos (seguro, VTV, matafuego), kilometraje, finanzas y choferes
# ============================================================
datos_iniciales = {
    "AG547BI": {
        "modelo": "Fiat Cronos 2024",
        "facturacion": "Mensual",
        "nro_poliza": "PROF SEGUROS POL-1.721.632",
        "vencimiento_seguro": "2026-08-08",
        "vencimiento_vtv": "2027-05-07",
        "vencimiento_matafuego": "2027-01-15",
        "km_actual": 208000,
        "km_ultimo_cambio_aceite": 199000,
        "frecuencia_aceite": 14000,
        "ingresos": 0,
        "gastos_detalle": {"Combustible": 0, "Chofer": 0, "Seguro": 0, "Arreglos": 0},
        "otros_gastos": {},
        "choferes": []
    },
    "AF509DB": {
        "modelo": "Fiat Cronos 1.3 Drive 2022",
        "facturacion": "Mensual",
        "nro_poliza": "PROF SEGUROS POL-1.634.357",
        "vencimiento_seguro": "2026-08-25",
        "vencimiento_vtv": "2026-01-21",
        "vencimiento_matafuego": "2026-11-20",
        "km_actual": 270658,
        "km_ultimo_cambio_aceite": 266367,
        "frecuencia_aceite": 14000,
        "ingresos": 0,
        "gastos_detalle": {"Combustible": 0, "Chofer": 0, "Seguro": 0, "Arreglos": 0},
        "otros_gastos": {},
        "choferes": []
    },
    "AF456WS": {
        "modelo": "Fiat Cronos 1.8 Precision 2022",
        "facturacion": "Mensual",
        "nro_poliza": "PROF SEGUROS POL-1.774.412",
        "vencimiento_seguro": "2026-10-07",
        "vencimiento_vtv": "2027-06-30",
        "vencimiento_matafuego": "2027-03-10",
        "km_actual": 103000,
        "km_ultimo_cambio_aceite": 92260,
        "frecuencia_aceite": 14000,
        "ingresos": 0,
        "gastos_detalle": {"Combustible": 0, "Chofer": 0, "Seguro": 0, "Arreglos": 0},
        "otros_gastos": {},
        "choferes": []
    }
}


# ============================================================
# CARGA DE DATOS: Lee el archivo JSON si existe, sino crea los datos iniciales
# ============================================================
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r") as archivo:
            return json.load(archivo)
    else:
        with open(ARCHIVO_DATOS, "w") as archivo:
            json.dump(datos_iniciales, archivo, indent=4)
        return datos_iniciales


# ============================================================
# GUARDADO DE DATOS: Escribe toda la flota al archivo JSON
# ============================================================
def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w") as archivo:
        json.dump(datos, archivo, indent=4)