# ============================================================
# AUTH.PY - Rutas de autenticación de usuarios
# ============================================================
# Maneja registro de nuevos usuarios, inicio de sesión y cierre
# Usa Flask-Login para manejar sesiones y Werkzeug para hashear
# contraseñas con bcrypt (seguro contra robos de datos)

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, Usuario

# Blueprint para agrupar rutas de autenticación
auth_bp = Blueprint('auth', __name__)


# ============================================================
# RUTA LOGIN: Muestra el formulario de inicio de sesión
# GET: Devuelve la página de login
# POST: Valida credenciales e inicia sesión
# ============================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión. GET muestra el formulario,
    POST procesa las credenciales."""
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Buscar usuario en la base de datos
        usuario = Usuario.query.filter_by(username=username).first()

        # Verificar credenciales
        if usuario and check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            flash(f'Bienvenido, {usuario.nombre}!', 'success')
            # Redirigir a la página solicitada originalmente o al dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('login.html')


# ============================================================
# RUTA REGISTRO: Permite crear un nuevo usuario
# Solo accesible vía POST desde el formulario de login
# No requiere estar logueado (primer usuario se crea así)
# ============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario en el sistema.
    Valida que el username no exista y que las contraseñas coincidan."""
    username = request.form.get('username', '').strip()
    nombre = request.form.get('nombre', '').strip()
    password = request.form.get('password', '')
    confirmar = request.form.get('confirm_password', '')

    # Validaciones
    if not username or not nombre or not password:
        flash('Todos los campos son obligatorios.', 'error')
        return redirect(url_for('auth.login'))

    if password != confirmar:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('auth.login'))

    if len(password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres.', 'error')
        return redirect(url_for('auth.login'))

    # Verificar que el username no exista
    if Usuario.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe.', 'error')
        return redirect(url_for('auth.login'))

    # Verificar si es el primer usuario (será admin)
    es_admin = Usuario.query.count() == 0

    # Crear el nuevo usuario con contraseña hasheada
    nuevo_usuario = Usuario(
        username=username,
        nombre=nombre,
        password_hash=generate_password_hash(password),
        es_admin=es_admin,
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    flash(f'Usuario {nombre} creado correctamente. Ya puedes iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))


# ============================================================
# RUTA LOGOUT: Cierra la sesión del usuario actual
# Redirige al login después de cerrar sesión
# ============================================================
@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual y redirige al login."""
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


# ============================================================
# API: VERIFICAR SESION (para frontend JavaScript)
# Devuelve los datos del usuario autenticado en formato JSON
# ============================================================
@auth_bp.route('/api/me')
@login_required
def api_me():
    """API: Devuelve los datos del usuario actual en formato JSON"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'nombre': current_user.nombre,
        'es_admin': current_user.es_admin,
    })
