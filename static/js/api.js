// ============================================================
// API.JS - Cliente para la API REST del Control de Flota
// ============================================================
// Proporciona funciones para comunicarse con el backend Flask
// usando fetch(). Todas las peticiones incluyen cookies de sesión.

const API = {
    // ============================================================
    // METODO GENERICO: Realiza una petición HTTP a la API
    // Maneja errores de red, respuestas no JSON y códigos HTTP
    // ============================================================
    async request(method, url, datos = null) {
        try {
            const opciones = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',  // Incluir cookies de sesión
            };

            if (datos && (method === 'POST' || method === 'PUT')) {
                opciones.body = JSON.stringify(datos);
            }

            const respuesta = await fetch(url, opciones);

            // Si la respuesta es 401 (no autorizado), redirigir al login
            if (respuesta.status === 401) {
                window.location.href = '/login';
                throw new Error('Sesión expirada. Redirigiendo al login...');
            }

            // Intentar parsear como JSON
            const texto = await respuesta.text();
            try {
                const datosJson = JSON.parse(texto);

                // Si hay error en la respuesta, lanzar excepción
                if (!respuesta.ok) {
                    throw new Error(datosJson.error || `Error ${respuesta.status}`);
                }

                return datosJson;
            } catch (e) {
                if (e instanceof SyntaxError) {
                    throw new Error(`Respuesta inválida del servidor (${respuesta.status})`);
                }
                throw e;
            }
        } catch (error) {
            console.error(`❌ Error en API ${method} ${url}:`, error);
            throw error;
        }
    },

    // ============================================================
    // VEHICULOS: Operaciones CRUD
    // ============================================================

    // Obtener todos los vehículos
    async obtenerVehiculos() {
        return await this.request('GET', '/api/vehiculos');
    },

    // Obtener un vehículo por ID
    async obtenerVehiculo(id) {
        return await this.request('GET', `/api/vehiculos/${id}`);
    },

    // Crear un nuevo vehículo
    async crearVehiculo(datos) {
        return await this.request('POST', '/api/vehiculos', datos);
    },

    // Actualizar un vehículo existente
    async actualizarVehiculo(id, datos) {
        return await this.request('PUT', `/api/vehiculos/${id}`, datos);
    },

    // Eliminar un vehículo
    async eliminarVehiculo(id) {
        return await this.request('DELETE', `/api/vehiculos/${id}`);
    },

    // ============================================================
    // MOVIMIENTOS: Ingresos y gastos
    // ============================================================

    // Registrar un movimiento (ingreso o gasto)
    async registrarMovimiento(datos) {
        return await this.request('POST', '/api/movimientos', datos);
    },

    // Obtener movimientos de un vehículo
    async obtenerMovimientos(vehiculoId) {
        return await this.request('GET', `/api/movimientos?vehiculo_id=${vehiculoId}`);
    },

    // ============================================================
    // ACEITE: Cambios de aceite
    // ============================================================

    // Registrar un cambio de aceite
    async registrarCambioAceite(datos) {
        return await this.request('POST', '/api/cambios-aceite', datos);
    },

    // Obtener historial de cambios de aceite
    async obtenerCambiosAceite(vehiculoId) {
        return await this.request('GET', `/api/cambios-aceite?vehiculo_id=${vehiculoId}`);
    },

    // ============================================================
    // ALERTAS: Obtener todas las alertas del sistema
    // ============================================================

    async obtenerAlertas() {
        return await this.request('GET', '/api/alertas');
    },

    // ============================================================
    // AUDITORIA: Historial de acciones de los usuarios
    // ============================================================

    async obtenerAuditoria(limite = 100, patente = '') {
        let url = `/api/auditoria?limite=${limite}`;
        if (patente) url += `&patente=${patente}`;
        return await this.request('GET', url);
    },
};
