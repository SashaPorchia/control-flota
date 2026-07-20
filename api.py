# ============================================================
# API.PY - Rutas de la API REST para el control de flota
# ============================================================
# Proporciona endpoints JSON para todas las operaciones CRUD:
# vehículos, movimientos financieros, aceite y choferes.
# Todas las rutas requieren autenticación.

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from database import db, Vehiculo, CambioAceite, Movimiento, Auditoria

# Blueprint para agrupar las rutas de la API
api_bp = Blueprint('api', __name__)


# ============================================================
# FUNCION AUXILIAR: Registra una entrada en el libro de auditoría
# Cada modificación importante queda registrada con: quién, qué,
# cuándo y sobre qué vehículo. Los socios pueden ver quién hizo cada cosa.
# ============================================================
def registrar_auditoria(accion, entidad, usuario_nombre=None, entidad_id=None, patente='', detalle=''):
    """Crea un registro de auditoría con la acción realizada.
    accion: 'crear', 'editar', 'eliminar', 'registrar'
    entidad: 'vehiculo', 'movimiento', 'aceite', 'chofer'
    usuario_nombre: nombre del usuario que realizó la acción
    entidad_id: ID del registro afectado (opcional)
    patente: patente del vehículo (opcional)
    detalle: descripción de lo que se hizo"""
    try:
        nombre = usuario_nombre or current_user.nombre
        usuario_id = current_user.id

        registro = Auditoria(
            usuario_id=usuario_id,
            usuario_nombre=nombre,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            patente=patente,
            detalle=detalle,
        )
        db.session.add(registro)
        # No hacer commit aquí porque se llama desde otras operaciones
        # que ya hacen commit. El flush asegura que se asigne ID.
        db.session.flush()
    except Exception as e:
        # Si falla la auditoría, no debe romper la operación principal
        print(f"[AUDITORIA] Error al registrar: {e}")


# ============================================================
# FUNCION AUXILIAR: Verifica si una fecha es válida
# Retorna True si el string tiene formato YYYY-MM-DD válido
# ============================================================
def fecha_valida(fecha_str):
    try:
        datetime.strptime(fecha_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


# ============================================================
# FUNCION AUXILIAR: Calcula días restantes para un vencimiento
# Retorna entero con días (negativo si vencido)
# ============================================================
def dias_restantes(fecha_str):
    if not fecha_str:
        return 999
    try:
        fecha_venc = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        return (fecha_venc - date.today()).days
    except (ValueError, TypeError):
        return 999


# ============================================================
# FUNCION AUXILIAR: Obtiene alertas de un vehículo
# Retorna lista de alertas ordenadas por gravedad
# ============================================================
def obtener_alertas(vehiculo):
    alertas = []

    # Verificar seguro (alerta si <= 30 días)
    ds = dias_restantes(vehiculo.vencimiento_seguro)
    if ds < 0:
        alertas.append({'tipo': 'SEGURO', 'texto': f'VENCIDO hace {abs(ds)} días', 'gravedad': 'rojo'})
    elif ds <= 30:
        alertas.append({'tipo': 'SEGURO', 'texto': f'Vence en {ds} días', 'gravedad': 'naranja'})

    # Verificar VTV (alerta si <= 30 días)
    dv = dias_restantes(vehiculo.vencimiento_vtv)
    if dv < 0:
        alertas.append({'tipo': 'VTV', 'texto': f'VENCIDA hace {abs(dv)} días', 'gravedad': 'rojo'})
    elif dv <= 30:
        alertas.append({'tipo': 'VTV', 'texto': f'Vence en {dv} días', 'gravedad': 'naranja'})

    # Verificar matafuego (alerta si <= 30 días)
    if vehiculo.vencimiento_matafuego:
        dm = dias_restantes(vehiculo.vencimiento_matafuego)
        if dm < 0:
            alertas.append({'tipo': 'MATAFUEGO', 'texto': f'VENCIDO hace {abs(dm)} días', 'gravedad': 'rojo'})
        elif dm <= 30:
            alertas.append({'tipo': 'MATAFUEGO', 'texto': f'Vence en {dm} días', 'gravedad': 'naranja'})

    # Verificar aceite (alerta si <= 1500 km restantes)
    kr = vehiculo.km_restantes_aceite
    if kr <= 0:
        alertas.append({'tipo': 'ACEITE', 'texto': f'PASADO por {abs(kr)} km', 'gravedad': 'rojo'})
    elif kr <= 1500:
        alertas.append({'tipo': 'ACEITE', 'texto': f'Quedan {kr} km', 'gravedad': 'naranja'})

    # Verificar licencia del chofer activo (alerta si <= 14 días = 2 semanas)
    for c in vehiculo.choferes:
        if c.get('estado') == 'alta' and c.get('vigencia_licencia'):
            dl = dias_restantes(c['vigencia_licencia'])
            if dl < 0:
                alertas.append({'tipo': 'LICENCIA', 'texto': f"{c['nombre']} VENCIDA hace {abs(dl)} días", 'gravedad': 'rojo'})
            elif dl <= 14:
                alertas.append({'tipo': 'LICENCIA', 'texto': f"{c['nombre']} vence en {dl} días", 'gravedad': 'naranja'})
            break  # Solo el primer chofer activo

    return alertas


# ============================================================
# ENDPOINT: Listar todos los vehículos con sus indicadores
# GET /api/vehiculos -> JSON con todos los vehículos
# ============================================================
@api_bp.route('/api/vehiculos')
@login_required
def listar_vehiculos():
    """API: Retorna todos los vehículos con datos resumidos"""
    vehiculos = Vehiculo.query.order_by(Vehiculo.patente).all()
    resultado = []
    for v in vehiculos:
        data = v.to_dict()
        data['alertas'] = obtener_alertas(v)
        resultado.append(data)
    return jsonify(resultado)


# ============================================================
# ENDPOINT: Obtener un vehículo por ID
# GET /api/vehiculos/<id> -> JSON con datos completos
# ============================================================
@api_bp.route('/api/vehiculos/<int:vehiculo_id>')
@login_required
def obtener_vehiculo(vehiculo_id):
    """API: Retorna los datos completos de un vehículo específico"""
    vehiculo = Vehiculo.query.get_or_404(vehiculo_id)
    data = vehiculo.to_dict()
    data['alertas'] = obtener_alertas(vehiculo)
    return jsonify(data)


# ============================================================
# ENDPOINT: Crear un nuevo vehículo
# POST /api/vehiculos -> JSON con el vehículo creado
# ============================================================
@api_bp.route('/api/vehiculos', methods=['POST'])
@login_required
def crear_vehiculo():
    """API: Crea un nuevo vehículo en la flota"""
    datos = request.get_json()

    # Validar campos obligatorios
    patente = datos.get('patente', '').upper().strip()
    if not patente:
        return jsonify({'error': 'La patente es obligatoria'}), 400

    # Verificar que no exista
    if Vehiculo.query.filter_by(patente=patente).first():
        return jsonify({'error': f'La patente {patente} ya existe'}), 409

    # Crear el vehículo
    vehiculo = Vehiculo(
        patente=patente,
        modelo=datos.get('modelo', ''),
        facturacion=datos.get('facturacion', 'Mensual'),
        nro_poliza=datos.get('nro_poliza', ''),
        vencimiento_seguro=datos.get('vencimiento_seguro', '2027-01-01'),
        vencimiento_vtv=datos.get('vencimiento_vtv', '2027-01-01'),
        vencimiento_matafuego=datos.get('vencimiento_matafuego', ''),
        km_actual=int(datos.get('km_actual', 0)),
        km_ultimo_cambio_aceite=int(datos.get('km_ultimo_cambio_aceite', 0)),
        ingresos=float(datos.get('ingresos', 0)),
        gastos_detalle={'Combustible': 0, 'Chofer': 0, 'Seguro': 0, 'Arreglos': 0},
        otros_gastos={},
        choferes=[],
    )

    # Registrar el cambio de aceite inicial en el historial
    km_aceite = vehiculo.km_ultimo_cambio_aceite
    if km_aceite > 0:
        cambio = CambioAceite(
            vehiculo_id=vehiculo.id,
            km_cambio=km_aceite,
            notas="Cambio inicial"
        )
        db.session.add(cambio)

    db.session.add(vehiculo)
    db.session.commit()

    # Registrar en auditoría
    registrar_auditoria(
        accion='crear', entidad='vehiculo',
        entidad_id=vehiculo.id, patente=vehiculo.patente,
        detalle=f"Creó vehículo {vehiculo.patente} ({vehiculo.modelo})"
    )
    db.session.commit()

    data = vehiculo.to_dict()
    data['alertas'] = obtener_alertas(vehiculo)
    return jsonify(data), 201


# ============================================================
# ENDPOINT: Actualizar un vehículo existente
# PUT /api/vehiculos/<id> -> JSON actualizado
# ============================================================
@api_bp.route('/api/vehiculos/<int:vehiculo_id>', methods=['PUT'])
@login_required
def actualizar_vehiculo(vehiculo_id):
    """API: Actualiza los datos de un vehículo existente"""
    vehiculo = Vehiculo.query.get_or_404(vehiculo_id)
    datos = request.get_json()

    # Actualizar todos los campos permitidos
    if 'modelo' in datos:
        vehiculo.modelo = datos['modelo']
    if 'facturacion' in datos:
        vehiculo.facturacion = datos['facturacion']
    if 'nro_poliza' in datos:
        vehiculo.nro_poliza = datos['nro_poliza']
    if 'vencimiento_seguro' in datos:
        vehiculo.vencimiento_seguro = datos['vencimiento_seguro']
    if 'vencimiento_vtv' in datos:
        vehiculo.vencimiento_vtv = datos['vencimiento_vtv']
    if 'vencimiento_matafuego' in datos:
        vehiculo.vencimiento_matafuego = datos['vencimiento_matafuego']
    if 'km_actual' in datos:
        vehiculo.km_actual = int(datos['km_actual'])
    if 'km_ultimo_cambio_aceite' in datos:
        vehiculo.km_ultimo_cambio_aceite = int(datos['km_ultimo_cambio_aceite'])

    # Detectar cambios en choferes para auditoría específica
    tiene_cambio_choferes = False
    detalle_chofer = ''
    if 'choferes' in datos:
        # Comparar arrays antes de modificarlos
        choferes_antes = vehiculo.choferes
        choferes_despues = datos['choferes']
        cant_antes = len(choferes_antes)
        cant_despues = len(choferes_despues)

        vehiculo.choferes = choferes_despues
        tiene_cambio_choferes = True

        if cant_despues > cant_antes:
            detalle_chofer = f"Agregó chofer a {vehiculo.patente}"
        elif cant_despues < cant_antes:
            detalle_chofer = f"Eliminó chofer de {vehiculo.patente}"
        else:
            # Misma cantidad: detectar cambios de estado (alta/baja)
            for c_despues in choferes_despues:
                for c_antes in choferes_antes:
                    if c_despues.get('nombre') == c_antes.get('nombre') and \
                       c_despues.get('estado') != c_antes.get('estado'):
                        detalle_chofer = f"Cambió estado de {c_despues.get('nombre')} a '{c_despues.get('estado')}' en {vehiculo.patente}"
                        break
                if detalle_chofer:
                    break
            if not detalle_chofer:
                detalle_chofer = f"Editó datos de chofer en {vehiculo.patente}"

    db.session.commit()

    # Registrar en auditoría según qué se modificó
    if tiene_cambio_choferes:
        registrar_auditoria(
            accion='registrar' if 'Agregó' in detalle_chofer or 'Eliminó' in detalle_chofer else 'editar',
            entidad='chofer',
            entidad_id=vehiculo.id, patente=vehiculo.patente,
            detalle=detalle_chofer
        )
        db.session.commit()
    else:
        # Auditoría normal de edición de vehículo
        cambios = []
        if 'modelo' in datos:
            cambios.append('modelo')
        for campo in ['km_actual', 'km_ultimo_cambio_aceite', 'vencimiento_seguro', 'vencimiento_vtv']:
            if campo in datos:
                cambios.append(campo)
        if cambios:
            detalle = f"Editó {vehiculo.patente}: {', '.join(cambios)}"
            registrar_auditoria(
                accion='editar', entidad='vehiculo',
                entidad_id=vehiculo.id, patente=vehiculo.patente,
                detalle=detalle
            )
            db.session.commit()

    data = vehiculo.to_dict()
    data['alertas'] = obtener_alertas(vehiculo)
    return jsonify(data)


# ============================================================
# ENDPOINT: Eliminar un vehículo
# DELETE /api/vehiculos/<id> -> mensaje de confirmación
# ============================================================
@api_bp.route('/api/vehiculos/<int:vehiculo_id>', methods=['DELETE'])
@login_required
def eliminar_vehiculo(vehiculo_id):
    """API: Elimina un vehículo y todos sus datos asociados"""
    vehiculo = Vehiculo.query.get_or_404(vehiculo_id)
    patente = vehiculo.patente
    modelo = vehiculo.modelo
    db.session.delete(vehiculo)
    db.session.commit()

    # Registrar en auditoría (después de eliminar, la patente ya se capturó)
    registrar_auditoria(
        accion='eliminar', entidad='vehiculo',
        patente=patente,
        detalle=f"Eliminó vehículo {patente} ({modelo}) con todos sus datos"
    )
    db.session.commit()

    return jsonify({'mensaje': f'Vehículo {patente} eliminado correctamente'})


# ============================================================
# ENDPOINT: Registrar un movimiento (ingreso o gasto)
# POST /api/movimientos -> JSON con el movimiento creado
# ============================================================
@api_bp.route('/api/movimientos', methods=['POST'])
@login_required
def registrar_movimiento():
    """API: Registra un ingreso o gasto para un vehículo y actualiza
    los totales acumulados en el vehículo."""
    datos = request.get_json()

    vehiculo_id = datos.get('vehiculo_id')
    if not vehiculo_id:
        return jsonify({'error': 'vehiculo_id requerido'}), 400

    vehiculo = Vehiculo.query.get(vehiculo_id)
    if not vehiculo:
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    tipo = datos.get('tipo', '').strip().lower()
    if tipo not in ('ingreso', 'gasto'):
        return jsonify({'error': 'Tipo debe ser "ingreso" o "gasto"'}), 400

    try:
        monto = float(datos.get('monto', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Monto inválido'}), 400

    if monto <= 0:
        return jsonify({'error': 'El monto debe ser positivo'}), 400

    categoria = datos.get('categoria', '')
    concepto = datos.get('concepto', '')

    if tipo == 'ingreso':
        categoria = 'Facturacion'
        vehiculo.ingresos += monto
    else:
        # Mapa de categorías de gasto
        categorias_validas = {'Combustible', 'Chofer', 'Seguro', 'Arreglos', 'Otro'}
        if categoria not in categorias_validas:
            return jsonify({'error': f'Categoría inválida: {categoria}'}), 400

        # Actualizar el acumulado en gastos_detalle u otros_gastos
        if categoria == 'Otro':
            if not concepto:
                return jsonify({'error': 'Se requiere un concepto para la categoría "Otro"'}), 400
            otros = vehiculo.otros_gastos
            otros[concepto] = otros.get(concepto, 0) + monto
            vehiculo.otros_gastos = otros
        else:
            detalle = vehiculo.gastos_detalle
            detalle[categoria] = detalle.get(categoria, 0) + monto
            vehiculo.gastos_detalle = detalle

    # Crear el registro de movimiento
    movimiento = Movimiento(
        vehiculo_id=vehiculo.id,
        tipo=tipo,
        categoria=categoria,
        monto=monto,
        concepto=concepto if categoria == 'Otro' else '',
    )
    db.session.add(movimiento)
    db.session.commit()

    # Registrar en auditoría
    tipo_texto = 'ingreso' if tipo == 'ingreso' else 'gasto'
    cat_texto = categoria if categoria != 'Otro' else f'Otro ({concepto})'
    registrar_auditoria(
        accion='registrar', entidad='movimiento',
        entidad_id=movimiento.id, patente=vehiculo.patente,
        detalle=f"Registró {tipo_texto} de ${monto:,.0f} en {vehiculo.patente} ({cat_texto})"
    )
    db.session.commit()

    return jsonify(movimiento.to_dict()), 201


# ============================================================
# ENDPOINT: Listar movimientos de un vehículo
# GET /api/movimientos?vehiculo_id=<id> -> lista de movimientos
# ============================================================
@api_bp.route('/api/movimientos')
@login_required
def listar_movimientos():
    """API: Retorna los movimientos de un vehículo, ordenados por fecha"""
    vehiculo_id = request.args.get('vehiculo_id', type=int)
    if not vehiculo_id:
        return jsonify({'error': 'vehiculo_id requerido'}), 400

    movimientos = Movimiento.query.filter_by(vehiculo_id=vehiculo_id)\
        .order_by(Movimiento.fecha.desc()).all()
    return jsonify([m.to_dict() for m in movimientos])


# ============================================================
# ENDPOINT: Registrar un cambio de aceite
# POST /api/cambios-aceite -> JSON con el cambio registrado
# Actualiza el km_ultimo_cambio_aceite del vehículo
# ============================================================
@api_bp.route('/api/cambios-aceite', methods=['POST'])
@login_required
def registrar_cambio_aceite():
    """API: Registra un cambio de aceite, guarda en el historial y
    actualiza el km_ultimo_cambio_aceite del vehículo."""
    datos = request.get_json()

    vehiculo_id = datos.get('vehiculo_id')
    if not vehiculo_id:
        return jsonify({'error': 'vehiculo_id requerido'}), 400

    vehiculo = Vehiculo.query.get(vehiculo_id)
    if not vehiculo:
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    try:
        km_cambio = int(datos.get('km_cambio', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'km_cambio debe ser un número entero'}), 400

    if km_cambio <= 0:
        return jsonify({'error': 'El kilometraje debe ser positivo'}), 400

    # Validar que el km no sea menor al último cambio registrado
    if km_cambio < vehiculo.km_ultimo_cambio_aceite:
        return jsonify({
            'error': f'El kilometraje ({km_cambio} km) no puede ser menor al último cambio registrado ({vehiculo.km_ultimo_cambio_aceite} km)'
        }), 400

    notas = datos.get('notas', '')

    # Crear el registro en el historial
    cambio = CambioAceite(
        vehiculo_id=vehiculo.id,
        km_cambio=km_cambio,
        fecha=date.today(),
        notas=notas,
    )

    # Actualizar el km del último cambio en el vehículo
    vehiculo.km_ultimo_cambio_aceite = km_cambio

    # Registrar cambio de aceite en auditoría
    km_proximo = km_cambio + 14000
    registrar_auditoria(
        accion='registrar', entidad='aceite',
        entidad_id=cambio.id, patente=vehiculo.patente,
        detalle=f"Registró cambio de aceite en {vehiculo.patente}: {km_cambio} km. Próximo: {km_proximo} km"
    )

    db.session.add(cambio)
    db.session.commit()

    return jsonify(cambio.to_dict()), 201


# ============================================================
# ENDPOINT: Obtener historial de cambios de aceite
# GET /api/cambios-aceite?vehiculo_id=<id> -> lista ordenada
# ============================================================
@api_bp.route('/api/cambios-aceite')
@login_required
def listar_cambios_aceite():
    """API: Retorna el historial de cambios de aceite de un vehículo"""
    vehiculo_id = request.args.get('vehiculo_id', type=int)
    if not vehiculo_id:
        return jsonify({'error': 'vehiculo_id requerido'}), 400

    cambios = CambioAceite.query.filter_by(vehiculo_id=vehiculo_id)\
        .order_by(CambioAceite.fecha.desc()).all()
    return jsonify([c.to_dict() for c in cambios])


# ============================================================
# ENDPOINT: Obtener todas las alertas de todos los vehículos
# GET /api/alertas -> lista de alertas ordenadas por urgencia
# ============================================================
@api_bp.route('/api/alertas')
@login_required
def obtener_alertas_globales():
    """API: Retorna todas las alertas de todos los vehículos,
    ordenadas por gravedad (rojo primero) y urgencia."""
    vehiculos = Vehiculo.query.all()
    todas_alertas = []

    for v in vehiculos:
        alertas = obtener_alertas(v)
        for a in alertas:
            a['patente'] = v.patente
            a['modelo'] = v.modelo
            todas_alertas.append(a)

    # Ordenar: rojo primero, luego naranja
    todas_alertas.sort(key=lambda x: (0 if x['gravedad'] == 'rojo' else 1))

    return jsonify(todas_alertas)


# ============================================================
# ENDPOINT: Obtener historial de auditoría
# GET /api/auditoria -> lista de acciones ordenadas por fecha
# Soporta paginación opcional con ?limite=N
# ============================================================
@api_bp.route('/api/auditoria')
@login_required
def listar_auditoria():
    """API: Retorna el historial de acciones de los usuarios,
    ordenado del más reciente al más antiguo.
    Parámetros opcionales:
    - limite: cantidad de registros a devolver (default 100)
    - patente: filtrar por patente de vehículo"""
    limite = request.args.get('limite', 100, type=int)
    patente_filtro = request.args.get('patente', '').strip().upper()

    consulta = Auditoria.query.order_by(Auditoria.id.desc())

    if patente_filtro:
        consulta = consulta.filter(Auditoria.patente == patente_filtro)

    registros = consulta.limit(limite).all()
    return jsonify([r.to_dict() for r in registros])
