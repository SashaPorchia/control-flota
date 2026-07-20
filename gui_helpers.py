# ============================================================
# GUI_HELPERS.PY - Funciones auxiliares para la interfaz grafica
# Estas funciones solo dependen de datos, no de widgets tkinter.
# Reciben la flota como parametro para ser independientes.
# ============================================================

import funciones  # Para verificar_vencimiento()


# ============================================================
# OBTENER ALERTAS: Genera un texto con todas las alertas de un vehiculo
# Revisa: seguro, VTV, matafuego, licencia de chofer y aceite
# Retorna: texto con alertas separadas por " | " o "OK" si todo esta bien
# ============================================================
def obtener_alertas(patente, d):
    alertas = []
    ds = funciones.verificar_vencimiento(d["vencimiento_seguro"])
    if ds < 0: alertas.append("SEGURO VENCIDO")
    elif ds <= 15: alertas.append("SEGURO POR VENCER")
    dv = funciones.verificar_vencimiento(d["vencimiento_vtv"])
    if dv < 0: alertas.append("VTV VENCIDA")
    elif dv <= 15: alertas.append("VTV POR VENCER")
    if "vencimiento_matafuego" in d:
        dm = funciones.verificar_vencimiento(d["vencimiento_matafuego"])
        if dm < 0: alertas.append("MATAFUEGO VENCIDO")
        elif dm <= 30: alertas.append("MATAFUEGO POR VENCER")
    if "choferes" in d:
        for c in d["choferes"]:
            if c["estado"] == "alta" and "vigencia_licencia" in c:
                dl = funciones.verificar_vencimiento(c["vigencia_licencia"])
                if dl < 0:
                    alertas.append("LIC VENCIDA")
                elif dl <= 30:
                    alertas.append("LIC POR VENCER")
                break
    kp = d["km_ultimo_cambio_aceite"] + d["frecuencia_aceite"]
    kr = kp - d["km_actual"]
    if kr <= 0: alertas.append("ACEITE PASADO")
    elif kr <= 1500: alertas.append("ACEITE CERCA")
    return " | ".join(alertas) if alertas else "OK"


# ============================================================
# OBTENER CHOFER ACTIVO: Busca el nombre del primer chofer dado de alta
# en el vehiculo especificado. Retorna "-" si no hay chofer activo.
# ============================================================
def obtener_chofer_activo(patente, flota):
    d = flota.get(patente, {})
    if "choferes" in d and d["choferes"]:
        for c in d["choferes"]:
            if c["estado"] == "alta":
                return c["nombre"]
    return "-"


# ============================================================
# INFO MATAFUEGO: Obtiene el estado del matafuego de un vehiculo
# Retorna: fecha de vencimiento, "VENC(Nd)" si vencido, "Nd" si proximo,
#          o "-" si no tiene el campo
# ============================================================
def info_mata(patente, flota):
    d = flota.get(patente, {})
    if "vencimiento_matafuego" in d:
        dias = funciones.verificar_vencimiento(d["vencimiento_matafuego"])
        if dias < 0: return "VENC(" + str(abs(dias)) + "d)"
        elif dias <= 30: return str(dias) + "d"
        else: return d["vencimiento_matafuego"]
    return "-"


# ============================================================
# INFO LICENCIA: Obtiene el estado de la licencia de conducir del chofer activo
# Retorna: fecha de vigencia, "LIC VENC(Nd)" si vencida, "Nd" si proxima,
#          o "-" si no hay chofer o no tiene licencia registrada
# ============================================================
def info_licencia(patente, flota):
    d = flota.get(patente, {})
    if "choferes" in d:
        for c in d["choferes"]:
            if c["estado"] == "alta" and "vigencia_licencia" in c:
                dias = funciones.verificar_vencimiento(c["vigencia_licencia"])
                if dias < 0:
                    return "LIC VENC(" + str(abs(dias)) + "d)"
                elif dias <= 30:
                    return str(dias) + "d"
                else:
                    return c["vigencia_licencia"]
    return "-"


# ============================================================
# COLOR INDICADOR: Determina texto y color para un indicador de vencimiento
# Segun los dias restantes y el umbral de alerta.
# Para fecha: VENC(Nd)/Nd/fecha_original | Para km: PAS(Nkm)/Nkm/Nkm
# Retorna tupla (texto, color_hex)
# ============================================================
def color_indicador(dias, fecha_original, umbral=15, es_km=False):
    if es_km:
        if dias <= 0:
            return "PAS(" + str(abs(dias)) + "km)", "#E74C3C"
        elif dias <= umbral:
            return str(dias) + "km", "#F39C12"
        else:
            return str(dias) + "km", "#2ECC71"
    else:
        if dias < 0:
            return "VENC(" + str(abs(dias)) + "d)", "#E74C3C"
        elif dias <= umbral:
            return str(dias) + "d", "#F39C12"
        else:
            return fecha_original, "#2ECC71"


# ============================================================
# CALCULAR GASTOS: Suma todos los gastos de un vehiculo
# (gastos_detalle + otros_gastos). Retorna el total.
# ============================================================
def calcular_gastos(d):
    gf = sum(d["gastos_detalle"].values())
    gl = sum(d["otros_gastos"].values())
    return gf + gl


# ============================================================
# CALCULAR BALANCE: Ingresos - Gastos totales del vehiculo
# ============================================================
def calcular_balance(d):
    return d["ingresos"] - calcular_gastos(d)
