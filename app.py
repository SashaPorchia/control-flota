# ============================================================
# APP.PY - Aplicación principal del Control de Flota Web
# ============================================================
# Punto de entrada del servidor web. Configura Flask, la base
# de datos, la autenticación y las rutas API.

import os
import sys
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user

# Importar módulos del proyecto
from database import db, init_db, Usuario, Vehiculo, CambioAceite
from auth import auth_bp
from api import api_bp


# ============================================================
# CREACION DE LA APLICACION: Configuración inicial de Flask
# ============================================================
def crear_app():
    """Crea y configura la aplicación Flask con todos los módulos"""
    app = Flask(__name__)

    # ============================================================
    # CONFIGURACION: Clave secreta y Base de datos
    # Lee DATABASE_URL de las variables de entorno (Supabase / Vercel).
    # Si no existe, usa la base local SQLite (flota.db).
    # ============================================================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-segura-cambio-en-produccion-2024')
    
    # URL de la base de datos desde la nube o local
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///flota.db')
    
    # Compatibilidad para sintaxis antigua de PostgreSQL (postgres:// -> postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar base de datos
    init_db(app)

    # Migrar datos del JSON si la base de datos está vacía
    with app.app_context():
        try:
            if Vehiculo.query.count() == 0:
                importar_json_a_sqlite()
        except Exception as e:
            print(f"[INFO] No se pudo verificar la tabla de vehículos al iniciar: {e}")

    # ============================================================
    # CONFIGURACION DE LOGIN: Flask-Login
    # ============================================================
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # ============================================================
    # REGISTRO DE BLUEPRINTS
    # ============================================================
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # ============================================================
    # RUTAS
    # ============================================================
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    return app


# ============================================================
# FUNCION AUXILIAR: Importa datos del JSON a la base de datos
# ============================================================
def importar_json_a_sqlite():
    import json
    import os

    archivo_json = 'datos_flota_v5.json'
    if not os.path.exists(archivo_json):
        print("  [INFO] No se encontro archivo JSON para migrar.")
        return

    print("[...] Primera ejecucion: migrando datos desde JSON...")
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos_json = json.load(f)

        for patente, datos in datos_json.items():
            if Vehiculo.query.filter_by(patente=patente).first():
                continue

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
            db.session.flush()

            km_aceite = datos.get('km_ultimo_cambio_aceite', 0)
            if km_aceite > 0:
                db.session.add(CambioAceite(
                    vehiculo_id=vehiculo.id,
                    km_cambio=km_aceite,
                    notas="Registro inicial (migración desde JSON)"
                ))

            print(f"  [OK] {patente} ({vehiculo.modelo}) migrado")

        db.session.commit()
        print(f"[OK] Migracion completada exitosamente.")

    except Exception as e:
        db.session.rollback()
        print(f"  [WARN] No se pudieron migrar los datos: {e}")


# Instancia requerida para Vercel Serverless
app = crear_app()

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("CONTROL DE FLOTA - Servidor web iniciado")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
