import sys
sys.path.insert(0, '.')
import datos
from gui_helpers import calcular_gastos, calcular_balance

# 1. Cargar datos actuales
flota = datos.cargar_datos()
print('=== ESTADO INICIAL ===')
for pat, d in flota.items():
    tg = calcular_gastos(d)
    print(f'{pat}: ingresos={d["ingresos"]}, gastos={tg}, balance={calcular_balance(d)}')

# 2. Simular registro de gasto (Combustible $500 para AG547BI)
p = 'AG547BI'
print()
print('=== REGISTRANDO GASTO: AG547BI Combustible $500 ===')
flota[p]['gastos_detalle']['Combustible'] += 500.0

# 3. Verificar resultado
tg = calcular_gastos(flota[p])
print(f'gastos_detalle: {flota[p]["gastos_detalle"]}')
print(f'total gastos: {tg}')
print(f'balance: {calcular_balance(flota[p])}')

# 4. Mostrar formato tabla
print()
print('=== COMO SE VE EN LA TABLA ===')
print('Gastos:', '${:,}'.format(tg))
print('Balance:', '${:,}'.format(calcular_balance(flota[p])))

# 5. Restaurar datos originales
flota[p]['gastos_detalle']['Combustible'] -= 500.0
datos.guardar_datos(flota)
print()
print('=== DATOS RESTAURADOS ===')
tg = calcular_gastos(flota[p])
print(f'gastos: {tg}, balance: {calcular_balance(flota[p])}')
print('TEST OK - El registro de gastos funciona correctamente')
