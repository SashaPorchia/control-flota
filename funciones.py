# ============================================================
# FUNCIONES.PY - Logica de negocio del sistema de control de flota
# Incluye verificacion de vencimientos, resumen de flota y registro de movimientos
# ============================================================

import datos                   # Para cargar/guardar los datos de la flota
from datetime import datetime  # Para manejar fechas de vencimiento


# ============================================================
# VERIFICACION DE VENCIMIENTO: Calcula cuantos dias faltan para una fecha
# Retorna: dias restantes (negativo si ya vencio, 999 si hay error)
# ============================================================
def verificar_vencimiento(fecha_str):
    try:
        fecha_vencimiento = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        fecha_actual = datetime.now().date()
        faltan = (fecha_vencimiento - fecha_actual).days
        return faltan
    except Exception:
        return 999


# ============================================================
# RESUMEN DE FLOTA (CONSOLA): Muestra el estado completo de todos los vehiculos
# Incluye: seguro, VTV, matafuego, aceite, choferes y finanzas
# Recibe flota como parametro (carga datos frescos por defecto)
# ============================================================
def mostrar_resumen_flota(flota=None):
    if flota is None:
        flota = datos.cargar_datos()
    print("\n" + "=" * 20 + " ESTADO DE LA FLOTA " + "=" * 20)
    for patente, d in flota.items():
        print(f"\n🚗 Patente: {patente} | {d['modelo']} | Cobro: {d['facturacion']}")
        
        # Control del Seguro
        dias_seguro = verificar_vencimiento(d['vencimiento_seguro'])
        if dias_seguro < 0:
            print(f"  ⚠️  📄 Póliza N°:       {d['nro_poliza']} | ¡ALERTA! SEGURO VENCIDO HACE {abs(dias_seguro)} DÍAS")
        elif dias_seguro <= 15:
            print(f"  ⏳ 📄 Póliza N°:       {d['nro_poliza']} | ¡OJO! Vence en {dias_seguro} días ({d['vencimiento_seguro']})")
        else:
            print(f"  > 📄 Póliza N°:       {d['nro_poliza']} (Vence: {d['vencimiento_seguro']})")
            
        # Control de la VTV
        dias_vtv = verificar_vencimiento(d['vencimiento_vtv'])
        if dias_vtv < 0:
            print(f"  ⚠️  🔍 VTV vence el:    {d['vencimiento_vtv']} | ¡ALERTA! VTV VENCIDA HACE {abs(dias_vtv)} DÍAS")
        elif dias_vtv <= 15:
            print(f"  ⏳ 🔍 VTV vence el:    {d['vencimiento_vtv']} | ¡OJO! Vence en {dias_vtv} días")
        else:
            print(f"  > 🔍 VTV vence el:    {d['vencimiento_vtv']}")
        
        # Control del Matafuego
        if 'vencimiento_matafuego' in d:
            dias_mata = verificar_vencimiento(d['vencimiento_matafuego'])
            if dias_mata < 0:
                print(f"  ⚠️  🧯 Matafuego vence: {d['vencimiento_matafuego']} | ¡ALERTA! MATAFUEGO VENCIDO HACE {abs(dias_mata)} DÍAS")
            elif dias_mata <= 30:
                print(f"  ⏳ 🧯 Matafuego vence: {d['vencimiento_matafuego']} | ¡OJO! Vence en {dias_mata} días")
            else:
                print(f"  > 🧯 Matafuego vence: {d['vencimiento_matafuego']}")
        
        # Aceite
        km_proximo = d['km_ultimo_cambio_aceite'] + d['frecuencia_aceite']
        km_restantes = km_proximo - d['km_actual']
        if km_restantes <= 0:
            print(f"  ⚠️  🛢️ ¡ALERTA ACEITE! Pasado por {abs(km_restantes)} km")
        elif km_restantes <= 1500:
            print(f"  ⏳ 🛢️ ¡OJO ACEITE! Quedan solo {km_restantes} km para el service")
        else:
            print(f"  > 🛢️ Próximo cambio de aceite en: {km_restantes} km")
        
        # Choferes activos
        if 'choferes' in d and d['choferes']:
            activos = [c for c in d['choferes'] if c['estado'] == 'alta']
            if activos:
                for c in activos:
                    lic_texto = ""
                    if 'vigencia_licencia' in c:
                        dias_lic = verificar_vencimiento(c['vigencia_licencia'])
                        if dias_lic < 0:
                            lic_texto = f" | 🚨 Licencia VENCIDA ({abs(dias_lic)} d)"
                        elif dias_lic <= 30:
                            lic_texto = f" | ⏳ Licencia vence en {dias_lic} d"
                        else:
                            lic_texto = f" | ✅ Lic: {c['vigencia_licencia']}"
                    print(f"  > 👤 Conductor: {c['nombre']} (Desde: {c['fecha_alta']}){lic_texto}")
            inactivos = [c for c in d['choferes'] if c['estado'] == 'baja']
            if inactivos:
                for c in inactivos:
                    print(f"  > 💤 Ex-conductor: {c['nombre']} (Hasta: {c.get('fecha_baja', 'N/A')})")
        else:
            print(f"  > 👤 Sin conductor asignado")
            
        # Finanzas
        gastos_fijos = sum(d['gastos_detalle'].values())
        gastos_libres = sum(d['otros_gastos'].values())
        total_gastos = gastos_fijos + gastos_libres
        balance = d['ingresos'] - total_gastos
        
        print(f"  > 💵 Finanzas: Total Facturado ${d['ingresos']} | Total Gastos ${total_gastos} | Balance: ${balance}")
        
        # Detalle Gastos Principales
        gf = d['gastos_detalle']
        print(f"    ├── Gastos Principales -> Nafta: ${gf['Combustible']} | Chofer: ${gf['Chofer']} | Seguro: ${gf['Seguro']} | Arreglos: ${gf['Arreglos']}")
        
        # Detalle Otros Gastos
        if d['otros_gastos']:
            detalles = [f"{concepto}: ${monto}" for concepto, monto in d['otros_gastos'].items()]
            print(f"    └── Otros Gastos -> {' | '.join(detalles)}")
            
    print("\n" + "=" * 60)


# ============================================================
# REGISTRO DE MOVIMIENTO (CONSOLA): Permite registrar ingresos o gastos
# para un vehiculo seleccionado, con categorias predefinidas o personalizadas
# Recibe flota como parametro (carga datos frescos por defecto)
# ============================================================
def registrar_movimiento(flota=None):
    if flota is None:
        flota = datos.cargar_datos()
    print("\n--- REGISTRAR MOVIMIENTO ---")
    print("Seleccioná el auto:")
    opciones = list(flota.keys())
    for i, patente in enumerate(opciones, 1):
        print(f"{i}. Patente: {patente} ({flota[patente]['modelo']})")
        
    eleccion = int(input("Número de auto: "))
    auto_elegido = opciones[eleccion - 1]
    
    tipo = input("¿Es un (I)ngreso o un (G)asto?: ").upper().strip()
    
    if tipo == "I":
        entrada = input("Ingresá el monto facturado (solo números): ")
        monto = float(entrada.strip())
        flota[auto_elegido]['ingresos'] += monto
        print(f"💰 ¡Ingreso de ${monto} registrado para la patente {auto_elegido}!")
        
    elif tipo == "G":
        print("\n¿Qué tipo de gasto es?")
        print("1. Combustible")
        print("2. Chofer")
        print("3. Seguro")
        print("4. Arreglos")
        print("5. Otro (Con título personalizado)")
        opc_gasto = input("Elegí una categoría (1-5): ").strip()
        
        entrada = input("Ingresá el monto del gasto (solo números): ")
        monto = float(entrada.strip())
        
        if opc_gasto == "1":
            flota[auto_elegido]['gastos_detalle']['Combustible'] += monto
            print(f"📉 ¡Gasto de Combustible (${monto}) registrado!")
        elif opc_gasto == "2":
            flota[auto_elegido]['gastos_detalle']['Chofer'] += monto
            print(f"📉 ¡Gasto de Chofer (${monto}) registrado!")
        elif opc_gasto == "3":
            flota[auto_elegido]['gastos_detalle']['Seguro'] += monto
            print(f"📉 ¡Gasto de Seguro (${monto}) registrado!")
        elif opc_gasto == "4":
            flota[auto_elegido]['gastos_detalle']['Arreglos'] += monto
            print(f"📉 ¡Gasto de Arreglos (${monto}) registrado!")
        elif opc_gasto == "5":
            concepto = input("Escribí el título del gasto (Ej: Cubiertas nuevas): ").strip()
            if not concepto:
                print("El título no puede estar vacío.")
                return
            if concepto in flota[auto_elegido]['otros_gastos']:
                flota[auto_elegido]['otros_gastos'][concepto] += monto
            else:
                flota[auto_elegido]['otros_gastos'][concepto] = monto
            print(f"📉 ¡Gasto en '{concepto}' (${monto}) registrado!")
        else:
            print("Categoría no válida.")
            return
    else:
        print("Opción no válida.")
        return
        
    datos.guardar_datos(flota)