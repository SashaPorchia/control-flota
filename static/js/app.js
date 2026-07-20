// ============================================================
// APP.JS - Lógica principal del panel de control de flota
// ============================================================
// Maneja la interfaz de usuario: carga de datos, modales,
// eventos, notificaciones y todas las interacciones del usuario.

// Variable global para almacenar los vehículos en memoria
let vehiculos = [];


// ============================================================
// INICIALIZACION: Se ejecuta al cargar la página
// ============================================================
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Cargar datos del usuario actual
        const usuario = await API.request('GET', '/api/me');
        document.getElementById('nombre-usuario').textContent = `👤 ${usuario.nombre}`;

        // Cargar vehículos
        await cargarVehiculos();

        // Verificar alertas al iniciar
        await verificarAlertasInicio();

    } catch (error) {
        console.error('Error al inicializar:', error);
    }
});


// ============================================================
// TOAST: Sistema de notificaciones emergentes
// ============================================================
function mostrarToast(mensaje, tipo = 'info') {
    const contenedor = document.getElementById('toast-contenedor');
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.textContent = mensaje;
    contenedor.appendChild(toast);

    // Eliminar automáticamente después de 4 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


// ============================================================
// MODALES: Abrir, cerrar y gestionar ventanas modales
// ============================================================

// Abre un modal por su ID
function mostrarModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('abierto');
        document.body.style.overflow = 'hidden';  // Evitar scroll del fondo
    }
}

// Cierra un modal por su ID
function cerrarModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('abierto');
        document.body.style.overflow = '';
    }
}

// Cierra modal si se hace click fuera del contenido (en el overlay)
function cerrarModalExterno(event, id) {
    if (event.target === event.currentTarget) {
        cerrarModal(id);
    }
}

// Cerrar modal con tecla Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.abierto').forEach(modal => {
            modal.classList.remove('abierto');
        });
        document.body.style.overflow = '';
    }
});


// ============================================================
// VEHICULOS: Carga, renderizado y filtrado
// ============================================================

// Carga todos los vehículos desde la API y los renderiza
async function cargarVehiculos() {
    try {
        vehiculos = await API.obtenerVehiculos();
        renderizarVehiculos(vehiculos);
        actualizarSelectoresVehiculos();
    } catch (error) {
        document.getElementById('lista-vehiculos').innerHTML =
            `<div class="cargando">❌ Error al cargar vehículos: ${error.message}</div>`;
        mostrarToast('Error al cargar vehículos', 'error');
    }
}

// Renderiza la lista de tarjetas de vehículos
function renderizarVehiculos(lista) {
    const contenedor = document.getElementById('lista-vehiculos');

    if (lista.length === 0) {
        contenedor.innerHTML = `
            <div class="cargando">
                🚗 No hay vehículos registrados<br>
                <small>Haz clic en "Agregar Vehículo" para empezar</small>
            </div>
        `;
        return;
    }

    contenedor.innerHTML = lista.map(v => crearTarjetaVehiculo(v)).join('');

    // Actualizar contador de alertas
    actualizarContadorAlertas(lista);
}

// Crea el HTML de una tarjeta de vehículo
function crearTarjetaVehiculo(v) {
    // Determinar color del balance
    const balanceClase = v.balance >= 0 ? 'positivo' : 'negativo';
    const balanceFormato = formatoPesos(v.balance);

    // Determinar estado del aceite
    let aceiteClase = '';
    let aceiteTexto = `${formatoKm(v.km_restantes_aceite)}`;
    if (v.km_restantes_aceite <= 0) {
        aceiteClase = 'vencido';
        aceiteTexto = `⚠️ PASADO ${formatoKm(Math.abs(v.km_restantes_aceite))}`;
    } else if (v.km_restantes_aceite <= 1500) {
        aceiteClase = 'alerta';
        aceiteTexto = `⏳ ${formatoKm(v.km_restantes_aceite)}`;
    }

    // Indicadores de alertas
    let alertasHtml = '';
    if (v.alertas && v.alertas.length > 0) {
        const rojas = v.alertas.filter(a => a.gravedad === 'rojo').length;
        const naranjas = v.alertas.filter(a => a.gravedad === 'naranja').length;
        if (rojas > 0) alertasHtml += `<span class="alerta-punto rojo" title="${rojas} alerta(s) crítica(s)"></span>`;
        if (naranjas > 0) alertasHtml += `<span class="alerta-punto naranja" title="${naranjas} alerta(s) próxima(s)"></span>`;
    } else {
        alertasHtml = `<span class="alerta-punto sin-alertas" title="Todo en orden"></span>`;
    }

    // Obtener nombre del chofer activo
    const choferActivo = obtenerChoferActivo(v);

    return `
        <div class="vehiculo-tarjeta" data-patente="${v.patente}" data-modelo="${v.modelo}">
            <div class="vehiculo-header" onclick="mostrarDetalleVehiculo(${v.id})">
                <div>
                    <div class="vehiculo-patente">${v.patente}</div>
                    <div class="vehiculo-modelo">${v.modelo}</div>
                </div>
                <div class="vehiculo-alertas">${alertasHtml}</div>
            </div>

            <div class="vehiculo-body" onclick="mostrarDetalleVehiculo(${v.id})">
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">📊 KM Actual</span>
                    <span class="vehiculo-item-valor">${formatoKm(v.km_actual)}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">🛢️ Aceite</span>
                    <span class="vehiculo-item-valor ${aceiteClase}">${aceiteTexto}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">📈 Ingresos</span>
                    <span class="vehiculo-item-valor positivo">${formatoPesos(v.ingresos)}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">📉 Gastos</span>
                    <span class="vehiculo-item-valor">${formatoPesos(v.total_gastos)}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">⚖️ Balance</span>
                    <span class="vehiculo-item-valor ${balanceClase}">${balanceFormato}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">🛡️ Seguro</span>
                    <span class="vehiculo-item-valor ${obtenerClaseVencimiento(v, 'vencimiento_seguro')}">${formatoVencimiento(v, 'vencimiento_seguro')}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">🔍 VTV</span>
                    <span class="vehiculo-item-valor ${obtenerClaseVencimiento(v, 'vencimiento_vtv')}">${formatoVencimiento(v, 'vencimiento_vtv')}</span>
                </div>
                <div class="vehiculo-item">
                    <span class="vehiculo-item-label">🧯 Matafuego</span>
                    <span class="vehiculo-item-valor ${obtenerClaseVencimiento(v, 'vencimiento_matafuego')}">${formatoVencimiento(v, 'vencimiento_matafuego')}</span>
                </div>
            </div>                <div class="vehiculo-footer">
                <span class="vehiculo-chofer">👤 ${choferActivo}</span>
                <div class="vehiculo-acciones">
                    <span class="btn-tarjeta auditoria-link" onclick="event.stopPropagation();mostrarAuditoriaPatente('${v.patente}')" title="Ver actividad de este vehículo">📋</span>
                    <button class="btn-tarjeta editar" onclick="event.stopPropagation();editarVehiculo(${v.id})">✏️ Editar</button>
                    <button class="btn-tarjeta eliminar" onclick="event.stopPropagation();confirmarEliminar(${v.id}, '${v.patente}')">🗑️</button>
                </div>
            </div>
        </div>
    `;
}

// Filtra los vehículos según el texto del buscador
function filtrarVehiculos() {
    const texto = document.getElementById('buscador-input').value.toLowerCase().trim();
    const tarjetas = document.querySelectorAll('.vehiculo-tarjeta');

    tarjetas.forEach(tarjeta => {
        const patente = tarjeta.dataset.patente.toLowerCase();
        const modelo = tarjeta.dataset.modelo.toLowerCase();
        const coincide = !texto || patente.includes(texto) || modelo.includes(texto);
        tarjeta.classList.toggle('oculto', !coincide);
    });
}


// ============================================================
// FUNCIONES AUXILIARES: Formato, colores, etc.
// ============================================================

// Formatea un número como pesos argentinos
function formatoPesos(valor) {
    return '$' + Math.round(valor).toLocaleString('es-AR');
}

// Formatea un número como kilometraje
function formatoKm(valor) {
    return valor.toLocaleString('es-AR') + ' km';
}

// Obtiene el nombre del chofer activo de un vehículo
function obtenerChoferActivo(v) {
    if (v.choferes && v.choferes.length > 0) {
        for (const c of v.choferes) {
            if (c.estado === 'alta') return c.nombre;
        }
    }
    return 'Sin chofer';
}

// Obtiene la clase CSS para un vencimiento según su estado
function obtenerClaseVencimiento(v, campo) {
    const fecha = v[campo];
    if (!fecha) return '';
    const dias = calcularDiasRestantes(fecha);
    if (dias < 0) return 'vencido';
    if (dias <= 30) return 'alerta';
    return '';
}

// Formatea un vencimiento para mostrar
function formatoVencimiento(v, campo) {
    const fecha = v[campo];
    if (!fecha) return '-';
    const dias = calcularDiasRestantes(fecha);
    if (dias < 0) return `⚠️ VENCIDO`;
    if (dias <= 15) return `⏳ ${dias}d`;
    return fecha;
}

// Calcula los días restantes para una fecha (YYYY-MM-DD)
function calcularDiasRestantes(fechaStr) {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const fecha = new Date(fechaStr + 'T00:00:00');
    return Math.floor((fecha - hoy) / (1000 * 60 * 60 * 24));
}

// Actualiza el contador de alertas en el botón
function actualizarContadorAlertas(lista) {
    let total = 0;
    for (const v of lista) {
        if (v.alertas) total += v.alertas.length;
    }
    const badge = document.getElementById('contador-alertas');
    if (total > 0) {
        badge.textContent = total;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Actualiza todos los selectores de vehículos en los modales
function actualizarSelectoresVehiculos() {
    const selects = ['m-vehiculo', 'a-vehiculo', 'ch-vehiculo'];
    const opciones = vehiculos.map(v =>
        `<option value="${v.id}">${v.patente} - ${v.modelo}</option>`
    ).join('');

    selects.forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.innerHTML = opciones;
        }
    });
}


// ============================================================
// MODAL VEHICULO: Agregar y editar vehículos
// ============================================================

// Prepara el modal para agregar un nuevo vehículo
function mostrarFormularioAgregar() {
    document.getElementById('modal-vehiculo-titulo').textContent = '➕ Agregar Vehículo';
    document.getElementById('vehiculo-id').value = '';
    // Limpiar campos
    ['v-patente', 'v-modelo', 'v-poliza', 'v-km-actual', 'v-km-aceite'].forEach(id => {
        document.getElementById(id).value = '';
    });
    // Asegurar que la patente esté habilitada (por si venía de una edición)
    document.getElementById('v-patente').disabled = false;
    document.getElementById('v-facturacion').value = 'Mensual';
    // Fechas por defecto: +1 año
    const hoy = new Date();
    const unAno = new Date(hoy);
    unAno.setFullYear(hoy.getFullYear() + 1);
    document.getElementById('v-seguro').value = unAno.toISOString().split('T')[0];
    document.getElementById('v-vtv').value = unAno.toISOString().split('T')[0];
    document.getElementById('v-matafuego').value = '';
    document.getElementById('info-aceite-preview').style.display = 'none';

    mostrarModal('modal-vehiculo');
}

// Conecta el botón "Agregar Vehículo" de la barra de acciones
document.getElementById('btn-agregar-vehiculo')?.addEventListener('click', mostrarFormularioAgregar);

// Prepara el modal para editar un vehículo existente
async function editarVehiculo(id) {
    try {
        const v = await API.obtenerVehiculo(id);
        document.getElementById('modal-vehiculo-titulo').textContent = '✏️ Editar Vehículo';
        document.getElementById('vehiculo-id').value = v.id;
        document.getElementById('v-patente').value = v.patente;
        document.getElementById('v-patente').disabled = true; // No cambiar patente
        document.getElementById('v-modelo').value = v.modelo;
        document.getElementById('v-facturacion').value = v.facturacion;
        document.getElementById('v-poliza').value = v.nro_poliza;
        document.getElementById('v-seguro').value = v.vencimiento_seguro;
        document.getElementById('v-vtv').value = v.vencimiento_vtv;
        document.getElementById('v-matafuego').value = v.vencimiento_matafuego || '';
        document.getElementById('v-km-actual').value = v.km_actual;
        document.getElementById('v-km-aceite').value = v.km_ultimo_cambio_aceite;

        // Mostrar preview del aceite
        actualizarPreviewAceite();

        mostrarModal('modal-vehiculo');
    } catch (error) {
        mostrarToast('Error al cargar datos del vehículo', 'error');
    }
}

// Vista previa del aceite al editar/agregar
document.addEventListener('input', function(e) {
    if (e.target.id === 'v-km-actual' || e.target.id === 'v-km-aceite') {
        actualizarPreviewAceite();
    }
});

function actualizarPreviewAceite() {
    const kmActual = parseInt(document.getElementById('v-km-actual').value) || 0;
    const kmAceite = parseInt(document.getElementById('v-km-aceite').value) || 0;
    const preview = document.getElementById('info-aceite-preview');

    if (kmAceite > 0) {
        const proximo = kmAceite + 14000;
        const restante = proximo - kmActual;
        preview.style.display = 'flex';
        document.getElementById('preview-proximo-aceite').textContent = formatoKm(proximo);

        const alertaEl = document.getElementById('preview-restante-aceite');
        alertaEl.textContent = restante <= 0 ? `⚠️ PASADO por ${formatoKm(Math.abs(restante))}` : formatoKm(restante);
        alertaEl.className = 'info-valor' + (restante <= 0 ? ' info-alerta' : '');
    } else {
        preview.style.display = 'none';
    }
}

// Guarda el vehículo (crea o actualiza según corresponda)
async function guardarVehiculo() {
    const id = document.getElementById('vehiculo-id').value;
    const datos = {
        patente: document.getElementById('v-patente').value.toUpperCase().trim(),
        modelo: document.getElementById('v-modelo').value.trim(),
        facturacion: document.getElementById('v-facturacion').value,
        nro_poliza: document.getElementById('v-poliza').value.trim(),
        vencimiento_seguro: document.getElementById('v-seguro').value,
        vencimiento_vtv: document.getElementById('v-vtv').value,
        vencimiento_matafuego: document.getElementById('v-matafuego').value,
        km_actual: parseInt(document.getElementById('v-km-actual').value) || 0,
        km_ultimo_cambio_aceite: parseInt(document.getElementById('v-km-aceite').value) || 0,
    };

    // Validaciones básicas
    if (!datos.patente || !datos.modelo || !datos.vencimiento_seguro || !datos.vencimiento_vtv) {
        mostrarToast('Completa los campos obligatorios (*)', 'error');
        return;
    }

    try {
        if (id) {
            // Actualizar vehículo existente
            await API.actualizarVehiculo(parseInt(id), datos);
            mostrarToast('✅ Vehículo actualizado correctamente', 'success');
        } else {
            // Crear nuevo vehículo
            await API.crearVehiculo(datos);
            mostrarToast('✅ Vehículo agregado correctamente', 'success');
        }

        cerrarModal('modal-vehiculo');
        document.getElementById('v-patente').disabled = false;
        await cargarVehiculos();  // Recargar lista

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}

// Confirmar y eliminar un vehículo
async function confirmarEliminar(id, patente) {
    if (confirm(`¿Eliminar el vehículo ${patente}?\nSe borrarán todos sus datos (movimientos, historial, choferes).`)) {
        try {
            await API.eliminarVehiculo(id);
            mostrarToast(`✅ Vehículo ${patente} eliminado`, 'success');
            await cargarVehiculos();
        } catch (error) {
            mostrarToast(`❌ ${error.message}`, 'error');
        }
    }
}


// ============================================================
// MODAL MOVIMIENTO: Registrar ingresos y gastos
// ============================================================

// Cambia la interfaz según el tipo de movimiento seleccionado
function cambiarTipoMovimiento() {
    const tipo = document.querySelector('input[name="m-tipo"]:checked').value;
    const categoriaWrapper = document.getElementById('m-categoria-wrapper');
    const conceptoWrapper = document.getElementById('m-concepto-wrapper');

    if (tipo === 'ingreso') {
        categoriaWrapper.style.display = 'none';
        conceptoWrapper.style.display = 'none';
    } else {
        categoriaWrapper.style.display = 'block';
        // Mostrar concepto solo si la categoría es "Otro"
        const categoria = document.getElementById('m-categoria').value;
        conceptoWrapper.style.display = categoria === 'Otro' ? 'block' : 'none';
    }
}

// Mostrar/ocultar concepto según categoría
document.getElementById('m-categoria')?.addEventListener('change', function() {
    document.getElementById('m-concepto-wrapper').style.display =
        this.value === 'Otro' ? 'block' : 'none';
});

// Guarda un movimiento (ingreso o gasto)
async function guardarMovimiento() {
    const vehiculoId = document.getElementById('m-vehiculo').value;
    const tipo = document.querySelector('input[name="m-tipo"]:checked').value;
    const monto = parseFloat(document.getElementById('m-monto').value);
    const categoria = tipo === 'ingreso' ? 'Facturacion' : document.getElementById('m-categoria').value;
    const concepto = document.getElementById('m-concepto').value.trim();

    if (!vehiculoId) {
        mostrarToast('Selecciona un vehículo', 'error');
        return;
    }
    if (!monto || monto <= 0) {
        mostrarToast('Ingresa un monto válido', 'error');
        return;
    }
    if (tipo === 'gasto' && categoria === 'Otro' && !concepto) {
        mostrarToast('Ingresa un concepto para la categoría "Otro"', 'error');
        return;
    }

    try {
        await API.registrarMovimiento({
            vehiculo_id: parseInt(vehiculoId),
            tipo: tipo,
            categoria: categoria,
            monto: monto,
            concepto: concepto,
        });

        mostrarToast(`✅ ${tipo === 'ingreso' ? 'Ingreso' : 'Gasto'} registrado`, 'success');
        cerrarModal('modal-movimiento');
        document.getElementById('m-monto').value = '';
        document.getElementById('m-concepto').value = '';
        await cargarVehiculos();  // Recargar para ver cambios

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}


// ============================================================
// MODAL ACEITE: Registrar cambio de aceite y ver historial
// ============================================================

// Cargar datos del vehículo seleccionado en el modal de aceite
document.getElementById('a-vehiculo')?.addEventListener('change', async function() {
    const id = this.value;
    if (!id) return;

    try {
        const v = await API.obtenerVehiculo(parseInt(id));
        const preview = document.getElementById('a-preview');
        const kmAceite = v.km_ultimo_cambio_aceite;

        document.getElementById('a-km').placeholder = `Último cambio: ${formatoKm(kmAceite)}`;

        if (kmAceite > 0) {
            const proximo = kmAceite + 14000;
            preview.style.display = 'flex';
            document.getElementById('a-proximo-km').textContent = formatoKm(proximo);
        } else {
            preview.style.display = 'none';
        }

        // Cargar historial de cambios
        await cargarHistorialAceite(parseInt(id));

    } catch (error) {
        console.error('Error al cargar datos de aceite:', error);
    }
});

// Carga el historial de cambios de aceite de un vehículo
async function cargarHistorialAceite(vehiculoId) {
    const contenedor = document.getElementById('historial-aceite');
    const lista = document.getElementById('historial-aceite-lista');

    try {
        const cambios = await API.obtenerCambiosAceite(vehiculoId);

        if (cambios.length === 0) {
            contenedor.style.display = 'none';
            return;
        }

        contenedor.style.display = 'block';
        lista.innerHTML = cambios.map(c => `
            <div class="item-historial-aceite">
                <span class="km">🛢️ ${formatoKm(c.km_cambio)}</span>
                <span class="fecha">📅 ${c.fecha} ${c.notas ? '| ' + c.notas : ''}</span>
            </div>
        `).join('');

    } catch (error) {
        contenedor.style.display = 'none';
    }
}

// Guarda un nuevo cambio de aceite
async function guardarCambioAceite() {
    const vehiculoId = document.getElementById('a-vehiculo').value;
    const kmCambio = parseInt(document.getElementById('a-km').value);
    const notas = document.getElementById('a-notas').value.trim();

    if (!vehiculoId) {
        mostrarToast('Selecciona un vehículo', 'error');
        return;
    }
    if (!kmCambio || kmCambio <= 0) {
        mostrarToast('Ingresa un kilometraje válido', 'error');
        return;
    }

    try {
        await API.registrarCambioAceite({
            vehiculo_id: parseInt(vehiculoId),
            km_cambio: kmCambio,
            notas: notas,
        });

        mostrarToast('✅ Cambio de aceite registrado', 'success');
        cerrarModal('modal-aceite');
        document.getElementById('a-km').value = '';
        document.getElementById('a-notas').value = '';
        await cargarVehiculos();  // Recargar para ver cambios

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}


// ============================================================
// MODAL CHOFERES: Gestión de conductores
// ============================================================

// Carga los choferes del vehículo seleccionado
async function cargarChoferes() {
    const vehiculoId = document.getElementById('ch-vehiculo').value;
    const tbody = document.getElementById('tabla-choferes-body');

    if (!vehiculoId) {
        tbody.innerHTML = '<tr><td colspan="5" class="texto-centro">Selecciona un vehículo</td></tr>';
        return;
    }

    try {
        const v = await API.obtenerVehiculo(parseInt(vehiculoId));
        const choferes = v.choferes || [];

        if (choferes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="texto-centro">Sin choferes asignados</td></tr>';
            return;
        }

        tbody.innerHTML = choferes.map((c, idx) => {
            const estadoClase = c.estado === 'alta' ? 'estado-activo' : 'estado-inactivo';
            const estadoTexto = c.estado === 'alta' ? '✅ Activo' : '❌ Inactivo';
            const licencia = formatoLicencia(c);
            return `
                <tr>
                    <td>${c.nombre}</td>
                    <td><span class="${estadoClase}">${estadoTexto}</span></td>
                    <td>${licencia}</td>
                    <td>${c.fecha_alta || '-'}</td>
                    <td>
                        <button class="btn-tarjeta editar btn-sm" onclick="cambiarEstadoChofer(${v.id}, ${idx}, '${c.estado}')">
                            ${c.estado === 'alta' ? '🔴 Dar baja' : '🟢 Dar alta'}
                        </button>
                        <button class="btn-tarjeta eliminar btn-sm" onclick="eliminarChofer(${v.id}, ${idx}, '${c.nombre}')">
                            🗑️
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="5" class="texto-centro">Error al cargar choferes</td></tr>`;
    }
}

// Formatea la licencia del chofer para mostrar
// Alerta naranja cuando faltan 14 días o menos (2 semanas)
function formatoLicencia(c) {
    if (!c.vigencia_licencia) return '-';
    const dias = calcularDiasRestantes(c.vigencia_licencia);
    if (dias < 0) return `⚠️ VENCIDA`;
    if (dias <= 14) return `⏳ ${dias}d`;
    return c.vigencia_licencia;
}

// Cambia el estado de un chofer (alta ↔ baja)
async function cambiarEstadoChofer(vehiculoId, idx, estadoActual) {
    try {
        const v = await API.obtenerVehiculo(vehiculoId);
        const choferes = [...v.choferes];
        const nuevoEstado = estadoActual === 'alta' ? 'baja' : 'alta';

        choferes[idx].estado = nuevoEstado;
        if (nuevoEstado === 'baja') {
            choferes[idx].fecha_baja = new Date().toISOString().split('T')[0];
        } else {
            choferes[idx].fecha_alta = new Date().toISOString().split('T')[0];
            choferes[idx].fecha_baja = null;
        }

        await API.actualizarVehiculo(vehiculoId, { choferes: choferes });
        mostrarToast(`✅ Chofer cambiado a "${nuevoEstado}"`, 'success');
        await cargarChoferes();
        await cargarVehiculos();

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}

// Elimina un chofer del vehículo
async function eliminarChofer(vehiculoId, idx, nombre) {
    if (!confirm(`¿Eliminar a ${nombre} de la lista de choferes?`)) return;

    try {
        const v = await API.obtenerVehiculo(vehiculoId);
        const choferes = v.choferes.filter((_, i) => i !== idx);

        await API.actualizarVehiculo(vehiculoId, { choferes: choferes });
        mostrarToast(`✅ Chofer ${nombre} eliminado`, 'success');
        await cargarChoferes();
        await cargarVehiculos();

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}

// Agrega un nuevo chofer al vehículo seleccionado
async function agregarChofer() {
    const vehiculoId = document.getElementById('ch-vehiculo').value;
    const nombre = document.getElementById('ch-nombre').value.trim();
    const licencia = document.getElementById('ch-licencia').value;

    if (!vehiculoId) {
        mostrarToast('Selecciona un vehículo', 'error');
        return;
    }
    if (!nombre) {
        mostrarToast('Ingresa el nombre del chofer', 'error');
        return;
    }
    if (!licencia) {
        mostrarToast('Ingresa la vigencia de la licencia profesional', 'error');
        return;
    }

    try {
        const v = await API.obtenerVehiculo(parseInt(vehiculoId));
        const choferes = v.choferes || [];

        choferes.push({
            nombre: nombre,
            estado: 'alta',
            fecha_alta: new Date().toISOString().split('T')[0],
            fecha_baja: null,
            vigencia_licencia: licencia,
        });

        await API.actualizarVehiculo(parseInt(vehiculoId), { choferes: choferes });
        mostrarToast(`✅ Chofer ${nombre} agregado`, 'success');
        document.getElementById('ch-nombre').value = '';
        document.getElementById('ch-licencia').value = '';
        await cargarChoferes();
        await cargarVehiculos();

    } catch (error) {
        mostrarToast(`❌ ${error.message}`, 'error');
    }
}


// ============================================================
// MODAL DETALLE: Panel de control del vehículo
// ============================================================
async function mostrarDetalleVehiculo(id) {
    try {
        const v = await API.obtenerVehiculo(id);

        document.getElementById('detalle-titulo').textContent = `📊 ${v.patente} - ${v.modelo}`;

        const body = document.getElementById('detalle-body');
        body.innerHTML = `
            <div class="detalle-grid">
                <div class="detalle-tarjeta">
                    <h4>💰 Finanzas</h4>
                    <div class="detalle-item">
                        <span class="etiqueta">Facturado</span>
                        <span class="valor positivo">${formatoPesos(v.ingresos)}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">Gastos</span>
                        <span class="valor">${formatoPesos(v.total_gastos)}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">Balance</span>
                        <span class="valor ${v.balance >= 0 ? 'positivo' : 'negativo'}">${formatoPesos(v.balance)}</span>
                    </div>
                </div>

                <div class="detalle-tarjeta">
                    <h4>🛢️ Aceite</h4>
                    <div class="detalle-item">
                        <span class="etiqueta">Último cambio</span>
                        <span class="valor">${formatoKm(v.km_ultimo_cambio_aceite)}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">Próximo cambio (c/14.000 km)</span>
                        <span class="valor" style="color: var(--acento-verde)">${formatoKm(v.km_proximo_cambio_aceite)}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">KM restantes</span>
                        <span class="valor ${v.km_restantes_aceite <= 0 ? 'vencido' : v.km_restantes_aceite <= 1500 ? 'alerta' : ''}">
                            ${v.km_restantes_aceite <= 0 ? `⚠️ PASADO por ${formatoKm(Math.abs(v.km_restantes_aceite))}` : formatoKm(v.km_restantes_aceite)}
                        </span>
                    </div>
                </div>

                <div class="detalle-tarjeta">
                    <h4>📋 Vencimientos</h4>
                    <div class="detalle-item">
                        <span class="etiqueta">🛡️ Seguro</span>
                        <span class="valor ${obtenerClaseVencimiento(v, 'vencimiento_seguro')}">${formatoVencimiento(v, 'vencimiento_seguro')}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">🔍 VTV</span>
                        <span class="valor ${obtenerClaseVencimiento(v, 'vencimiento_vtv')}">${formatoVencimiento(v, 'vencimiento_vtv')}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">🧯 Matafuego</span>
                        <span class="valor ${obtenerClaseVencimiento(v, 'vencimiento_matafuego')}">${formatoVencimiento(v, 'vencimiento_matafuego')}</span>
                    </div>
                </div>

                <div class="detalle-tarjeta">
                    <h4>📄 Datos</h4>
                    <div class="detalle-item">
                        <span class="etiqueta">Póliza</span>
                        <span class="valor">${v.nro_poliza || '-'}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">Facturación</span>
                        <span class="valor">${v.facturacion}</span>
                    </div>
                    <div class="detalle-item">
                        <span class="etiqueta">KM Actual</span>
                        <span class="valor">${formatoKm(v.km_actual)}</span>
                    </div>
                </div>

                <div class="detalle-tarjeta full-width">
                    <h4>📊 Desglose de Gastos</h4>
                    ${renderizarDesgloseGastos(v)}
                </div>
            </div>
        `;

        mostrarModal('modal-detalle');

    } catch (error) {
        mostrarToast('Error al cargar detalle del vehículo', 'error');
    }
}

// Renderiza el desglose de gastos del vehículo
function renderizarDesgloseGastos(v) {
    const gastos = v.gastos_detalle || {};
    const otros = v.otros_gastos || {};

    let html = '';
    const categorias = [
        { clave: 'Combustible', icono: '⛽' },
        { clave: 'Chofer', icono: '🧑‍✈️' },
        { clave: 'Seguro', icono: '🛡️' },
        { clave: 'Arreglos', icono: '🔧' },
    ];

    for (const cat of categorias) {
        const monto = gastos[cat.clave] || 0;
        html += `
            <div class="detalle-item">
                <span class="etiqueta">${cat.icono} ${cat.clave}</span>
                <span class="valor">${formatoPesos(monto)}</span>
            </div>
        `;
    }

    for (const [concepto, monto] of Object.entries(otros)) {
        html += `
            <div class="detalle-item">
                <span class="etiqueta">📦 ${concepto}</span>
                <span class="valor">${formatoPesos(monto)}</span>
            </div>
        `;
    }

    return html || '<div class="texto-centro">Sin gastos registrados</div>';
}


// ============================================================
// MODAL ALERTAS: Muestra todas las alertas del sistema
// ============================================================
async function mostrarAlertas() {
    const body = document.getElementById('alertas-body');
    body.innerHTML = '<div class="cargando">Cargando alertas...</div>';
    mostrarModal('modal-alertas');

    try {
        const alertas = await API.obtenerAlertas();

        if (alertas.length === 0) {
            body.innerHTML = `
                <div class="texto-centro" style="padding:30px">
                    <span style="font-size:48px">✅</span>
                    <p style="margin-top:12px;color:var(--acento-verde);font-weight:700">Todo en orden</p>
                    <p style="color:var(--texto-oscuro);font-size:0.85rem">No hay vencimientos próximos ni alertas activas.</p>
                </div>
            `;
            return;
        }

        const rojas = alertas.filter(a => a.gravedad === 'rojo').length;
        const naranjas = alertas.filter(a => a.gravedad === 'naranja').length;

        let html = `
            <div style="text-align:center;margin-bottom:16px">
                <span style="color:var(--acento-rojo);font-weight:700">${rojas} crítica(s)</span>
                <span style="color:var(--texto-oscuro);margin:0 8px">|</span>
                <span style="color:var(--acento-naranja);font-weight:700">${naranjas} próxima(s)</span>
            </div>
        `;

        // Agrupar por patente
        const grupos = {};
        for (const a of alertas) {
            if (!grupos[a.patente]) grupos[a.patente] = { modelo: a.modelo, items: [] };
            grupos[a.patente].items.push(a);
        }

        for (const [patente, grupo] of Object.entries(grupos)) {
            html += `
                <div style="background:var(--fondo-carta);border-radius:8px;padding:10px 14px;margin-bottom:8px">
                    <div style="font-weight:700;color:var(--acento-oro);margin-bottom:6px;font-size:0.85rem">
                        ${patente} - ${grupo.modelo}
                    </div>
            `;

            for (const item of grupo.items) {
                const bg = item.gravedad === 'rojo' ? 'rgba(231,76,60,0.1)' : 'rgba(243,156,18,0.1)';
                const color = item.gravedad === 'rojo' ? 'var(--acento-rojo)' : 'var(--acento-naranja)';
                html += `
                    <div style="background:${bg};padding:6px 10px;border-radius:4px;margin-bottom:4px;font-size:0.8rem">
                        <span style="font-weight:700;color:${color}">${item.tipo}</span>
                        <span style="color:var(--texto-principal);margin-left:8px">${item.texto}</span>
                    </div>
                `;
            }

            html += `</div>`;
        }

        body.innerHTML = html;

    } catch (error) {
        body.innerHTML = `<div class="cargando">❌ Error al cargar alertas</div>`;
    }
}

// Verifica alertas al iniciar y muestra el modal si hay críticas
async function verificarAlertasInicio() {
    try {
        const alertas = await API.obtenerAlertas();
        const criticas = alertas.filter(a => a.gravedad === 'rojo').length;

        if (criticas > 0) {
            // Pequeña demora para que cargue bien la página
            setTimeout(() => mostrarAlertas(), 1000);
        }
    } catch (error) {
        // Silencioso - no molestar al usuario con errores de carga inicial
    }
}


// ============================================================
// AUDITORIA: Historial de actividad de los usuarios
// ============================================================

// Abre el modal de auditoría y carga los registros
async function mostrarAuditoria() {
    document.getElementById('aud-filtro-patente').value = '';  // Limpiar filtro
    mostrarModal('modal-auditoria');
    await recargarAuditoria();
}

// Abre el modal de auditoría filtrado para una patente específica
async function mostrarAuditoriaPatente(patente) {
    document.getElementById('aud-filtro-patente').value = patente;
    mostrarModal('modal-auditoria');
    await recargarAuditoria();
}

// Recarga la lista de registros de auditoría (con filtro opcional)
async function recargarAuditoria() {
    const contenedor = document.getElementById('auditoria-contenedor');
    const filtroPatente = document.getElementById('aud-filtro-patente').value.trim().toUpperCase();

    contenedor.innerHTML = '<div class="cargando">Cargando historial de actividad...</div>';

    try {
        const registros = await API.obtenerAuditoria(100, filtroPatente);

        if (registros.length === 0) {
            contenedor.innerHTML = `
                <div class="texto-centro" style="padding:30px">
                    <span style="font-size:36px">📋</span>
                    <p style="margin-top:8px;color:var(--texto-oscuro)">No hay actividad registrada aún.</p>
                </div>
            `;
            return;
        }

        // Generar tabla HTML
        let html = `
            <table class="tabla-auditoria">
                <thead>
                    <tr>
                        <th>Fecha/Hora</th>
                        <th>Usuario</th>
                        <th>Acción</th>
                        <th>Vehículo</th>
                        <th>Detalle</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const r of registros) {
            // Formatear fecha
            const fecha = new Date(r.created_at);
            const fechaStr = fecha.toLocaleDateString('es-AR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });

            // Icono según acción
            let iconoAccion = '';
            let claseAccion = '';
            if (r.accion === 'crear') { iconoAccion = '➕'; claseAccion = 'aud-crear'; }
            else if (r.accion === 'editar') { iconoAccion = '✏️'; claseAccion = 'aud-editar'; }
            else if (r.accion === 'eliminar') { iconoAccion = '🗑️'; claseAccion = 'aud-eliminar'; }
            else if (r.accion === 'registrar') { iconoAccion = '📝'; claseAccion = 'aud-registrar'; }

            // Icono según entidad
            let iconoEntidad = '';
            if (r.entidad === 'vehiculo') iconoEntidad = '🚗';
            else if (r.entidad === 'movimiento') iconoEntidad = '💰';
            else if (r.entidad === 'aceite') iconoEntidad = '🛢️';
            else if (r.entidad === 'chofer') iconoEntidad = '👤';

            const patente = r.patente || '-';

            html += `
                <tr class="${claseAccion}">
                    <td class="aud-fecha">${fechaStr}</td>
                    <td class="aud-usuario">👤 ${r.usuario_nombre}</td>
                    <td class="aud-accion">${iconoAccion} ${r.accion}</td>
                    <td class="aud-patente">${iconoEntidad} ${patente}</td>
                    <td class="aud-detalle">${r.detalle}</td>
                </tr>
            `;
        }

        html += `</tbody></table>`;
        html += `<div class="auditoria-total">Mostrando ${registros.length} registro(s)</div>`;

        contenedor.innerHTML = html;

    } catch (error) {
        contenedor.innerHTML = `<div class="cargando">❌ Error al cargar auditoría: ${error.message}</div>`;
    }
}
