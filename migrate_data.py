# ============================================================
# MIGRATE_DATA.PY - Migración de datos desde JSON a SQLite
# ============================================================
# Convierte los datos del archivo datos_flota_v5.json a la
# nueva base de datos SQLite. Lee el JSON, crea los registros
# en SQLAlchemy y guarda todo.
#
# Uso: python migrate_data.py

import json
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from database import db, Vehiculo, CambioAceite


# ============================================================
# CONFIGURACION: Crea una app Flask temporal para la migración
# ============================================================
def crear_app_migracion():
    """Crea una app Flask temporal con la configuración de base de datos"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flota.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'migracion-temporal'
    db.init_app(app)
    return app


# ============================================================
# MIGRAR DATOS: Lee el JSON y crea los registros en SQLite
# ============================================================
def migrar_datos():
    """Lee datos_flota_v5.json y migra todos los vehículos a SQLite"""
    archivo_json = 'datos_flota_v5.json'

    # Verificar si el archivo JSON existe
    if not os.path.exists(archivo_json):
        print(f"[WARN] No se encontro {archivo_json}. No hay datos para migrar.")
        return 0

    app = crear_app_migracion()

    with app.app_context():
        # Crear tablas si no existen
        db.create_all()

        # Cargar datos desde el JSON
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_json = json.load(f)

        contador = 0
        for patente, datos in datos_json.items():
            # Verificar si el vehículo ya existe en la base de datos
            existente = Vehiculo.query.filter_by(patente=patente).first()
            if existente:
                print(f"  [SKIP] {patente} ya existe, se omite.")
                continue

            # Crear nuevo vehículo con los datos del JSON
            vehiculo = Vehiculo(
                patente=patente,
                modelo=datos.get('modelo', ''),
                facturacion=datos.get('facturacion', 'Mensual'),
                nro_poliza=datos.get('nro_poliza', ''),
                vencimiento_seguro=datos.get('vencimiento_seguro', '2027-01-01'),
                vencimiento_vtv=datos.get('vencimiento_vtv', '2027-01-01'),
                vencimiento_matafuego=datos.get('vencimiento_matafuego', ''),
                km_actual=datos.get('km_actual', 0),
                km_ultimo_cambio_aceite=datos.get('km_ultimo_cambio_aceite', 0),
                ingresos=datos.get('ingresos', 0.0),
                gastos_detalle=datos.get('gastos_detalle', {}),
                otros_gastos=datos.get('otros_gastos', {}),
                choferes=datos.get('choferes', []),
            )

            db.session.add(vehiculo)
            db.session.flush()  # Para obtener el ID del vehículo

            # Registrar el cambio de aceite inicial en el historial
            km_aceite = datos.get('km_ultimo_cambio_aceite', 0)
            if km_aceite > 0:
                cambio = CambioAceite(
                    vehiculo_id=vehiculo.id,
                    km_cambio=km_aceite,
                    notas="Registro inicial (migración desde JSON)"
                )
                db.session.add(cambio)

            contador += 1
            print(f"  [OK] {patente} ({vehiculo.modelo}) migrado correctamente")

        db.session.commit()
        print(f"\n[OK] Migracion completada: {contador} vehiculo(s) migrado(s).")
        return contador


# ============================================================
# PUNTO DE ENTRADA: Ejecuta la migración si se llama directamente
# ============================================================
if __name__ == '__main__':
    print("=" * 50)
    print("MIGRACION DE DATOS: JSON → SQLite")
    print("=" * 50)
    total = migrar_datos()
    print(f"Total: {total} vehículos migrados.")
