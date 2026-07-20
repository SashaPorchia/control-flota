# ============================================================
# WSGI.PY - Punto de entrada para servidores WSGI (PythonAnywhere)
# ============================================================
# Este archivo es necesario para que PythonAnywhere pueda servir
# la aplicación web. Importa la función crear_app() y expone
# la variable 'application' que el servidor WSGI utiliza.
#
# No es necesario para ejecutar localmente (usar python app.py).
# ============================================================

import sys
import os

# Agregar el directorio del proyecto al path de Python
# para que pueda encontrar los módulos (database.py, auth.py, api.py)
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# También agregar templates/ y static/ al path
templates_path = os.path.join(path, 'templates')
static_path = os.path.join(path, 'static')
if templates_path not in sys.path:
    sys.path.append(templates_path)

# Importar la función que crea la aplicación Flask
from app import crear_app

# Crear la aplicación (esto también ejecuta la migración de datos
# si es la primera vez que se ejecuta)
application = crear_app()

# NOTA: PythonAnywhere busca la variable 'application' por defecto.
# Esta variable se usa para servir la web.
