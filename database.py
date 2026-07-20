# ============================================================
# DATABASE.PY - Modelos de base de datos SQLAlchemy
# ============================================================
# Define las tablas: Usuario, Vehiculo, CambioAceite, Movimiento, Auditoria
# Compatible con SQLite (Local) y PostgreSQL (Supabase / Vercel)

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date, timezone
import json

# Instancia global de la base de datos
db = SQLAlchemy()

# Función auxiliar para fechas UTC
def utc_now():
    return datetime.now(timezone.utc)


# ============================================================
# MODELO USUARIO
# ============================================================
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f'<Usuario {self.username}>'


# ============================================================
# MODELO VEHICULO
# ============================================================
class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True)
    patente = db.Column(db.String(20), unique=True, nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    facturacion = db.Column(db.String(50), default='Mensual')
    nro_poliza = db.Column(db.String(100), default='')

    # Vencimientos
    vencimiento_seguro = db.Column(db.String(10), nullable=False)
    vencimiento_vtv = db.Column(db.String(10), nullable=False)
    vencimiento_matafuego = db.Column(db.String(10), default='')

    # Kilometraje
    km_actual = db.Column(db.Integer, default=0)
    km_ultimo_cambio_aceite = db.Column(db.Integer, default=0)

    # Finanzas
    ingresos = db.Column(db.Float, default=0.0)

    # JSON almacenado como texto
    _gastos_detalle = db.Column('gastos_detalle', db.Text, default='{}')
    _otros_gastos = db.Column('otros_gastos', db.Text, default='{}')
    _choferes = db.Column('choferes', db.Text, default='[]')

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relaciones
    cambios_aceite = db.relationship('CambioAceite', backref='vehiculo',
                                     lazy='dynamic', cascade='all, delete-orphan')

    movimientos = db.relationship('Movimiento', backref='vehiculo',
                                  lazy='dynamic', cascade='all, delete-orphan')

    # Getters y Setters para JSON
    @property
    def gastos_detalle(self):
        return json.loads(self._gastos_detalle) if self._gastos_detalle else {}

    @gastos_detalle.setter
    def gastos_detalle(self, valor):
        self._gastos_detalle = json.dumps(valor)

    @property
    def otros_gastos(self):
        return json.loads(self._otros_gastos) if self._otros_gastos else {}

    @otros_gastos.setter
    def otros_gastos(self, valor):
        self._otros_gastos = json.dumps(valor)

    @property
    def choferes(self):
        return json.loads(self._choferes) if self._choferes else []

    @choferes.setter
    def choferes(self, valor):
        self._choferes = json.dumps(valor)

    @property
    def total_gastos(self):
        gf = sum(self.gastos_detalle.values()) if self.gastos_detalle else 0
        gl = sum(self.otros_gastos.values()) if self.otros_gastos else 0
        return gf + gl

    @property
    def balance(self):
        return self.ingresos - self.total_gastos

    @property
    def km_proximo_cambio_aceite(self):
        return self.km_ultimo_cambio_aceite + 14000

    @property
    def km_restantes_aceite(self):
        return self.km_proximo_cambio_aceite - self.km_actual

    def to_dict(self):
        return {
            'id': self.id,
            'patente': self.patente,
            'modelo': self.modelo,
            'facturacion': self.facturacion,
            'nro_poliza': self.nro_poliza,
            'vencimiento_seguro': self.vencimiento_seguro,
            'vencimiento_vtv': self.vencimiento_vtv,
            'vencimiento_matafuego': self.vencimiento_matafuego,
            'km_actual': self.km_actual,
            'km_ultimo_cambio_aceite': self.km_ultimo_cambio_aceite,
            'km_proximo_cambio_aceite': self.km_proximo_cambio_aceite,
            'km_restantes_aceite': self.km_restantes_aceite,
            'ingresos': self.ingresos,
            'total_gastos': self.total_gastos,
            'balance': self.balance,
            'gastos_detalle': self.gastos_detalle,
            'otros_gastos': self.otros_gastos,
            'choferes': self.choferes,
        }

    def __repr__(self):
        return f'<Vehiculo {self.patente}>'


# ============================================================
# MODELO CAMBIO ACEITE
# ============================================================
class CambioAceite(db.Model):
    __tablename__ = 'cambios_aceite'

    id = db.Column(db.Integer, primary_key=True)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    km_cambio = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, default=date.today)
    notas = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'vehiculo_id': self.vehiculo_id,
            'km_cambio': self.km_cambio,
            'fecha': self.fecha.isoformat() if self.fecha else '',
            'notas': self.notas,
        }


# ============================================================
# MODELO MOVIMIENTO
# ============================================================
class Movimiento(db.Model):
    __tablename__ = 'movimientos'

    id = db.Column(db.Integer, primary_key=True)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    concepto = db.Column(db.String(100), default='')
    fecha = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'vehiculo_id': self.vehiculo_id,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'monto': self.monto,
            'concepto': self.concepto,
            'fecha': self.fecha.isoformat() if self.fecha else '',
        }


# ============================================================
# MODELO AUDITORIA
# ============================================================
class Auditoria(db.Model):
    __tablename__ = 'auditoria'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario_nombre = db.Column(db.String(120), nullable=False)
    accion = db.Column(db.String(50), nullable=False)
    entidad = db.Column(db.String(50), nullable=False)
    entidad_id = db.Column(db.Integer, nullable=True)
    patente = db.Column(db.String(20), default='')
    detalle = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=utc_now)

    usuario = db.relationship('Usuario', backref='auditoria', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario_nombre,
            'accion': self.accion,
            'entidad': self.entidad,
            'entidad_id': self.entidad_id,
            'patente': self.patente,
            'detalle': self.detalle,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }

    def __repr__(self):
        return f'<Auditoria {self.usuario_nombre}: {self.accion} {self.entidad}>'


# ============================================================
# INICIALIZACION
# ============================================================
def init_db(app):
    """Vincula la base de datos a la aplicación y crea las tablas"""
    # Si la URL empieza con postgres:// lo corregimos a postgresql://
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgres://', 'postgresql://', 1)

    db.init_app(app)
    with app.app_context():
        db.create_all()