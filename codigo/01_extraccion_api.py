# BRICEÑO LEON CRYSTELL HIDEKI
# Código de matrícula: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 22/09/2026

import requests
from pathlib import Path

# ============================================================
# 1. PARÁMETROS FIJOS DEL ESTUDIO
# ============================================================

FECHA_INICIO = "2008-6"
FECHA_CORTE = "2025-12"

# Serie oficial del BCRP
# IPC Lima Metropolitana - Variación porcentual mensual
SERIE_INFLACION = "PN01271PM"

# ============================================================
# 2. CONSTRUIR URL DE LA API DEL BCRP
# ============================================================

URL_API = (
    "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"
    f"{SERIE_INFLACION}/csv/{FECHA_INICIO}/{FECHA_CORTE}/esp"
)

print("==========================================")
print("EXTRACCIÓN API - BCRP")
print("==========================================")
print("Variable: Inflación mensual (%)")
print("Serie:", SERIE_INFLACION)
print("Periodo:", FECHA_INICIO, "-", FECHA_CORTE)
print("\nURL consultada:")
print(URL_API)

# ============================================================
# 3. REALIZAR SOLICITUD
# ============================================================

respuesta = requests.get(URL_API, timeout=60)

print("\nCódigo HTTP:", respuesta.status_code)

# Detener el programa si la API devuelve un error
respuesta.raise_for_status()

# ============================================================
# 4. CREAR CARPETA PARA DATOS CRUDOS
# ============================================================

carpeta_crudos = Path("datos_crudos")
carpeta_crudos.mkdir(exist_ok=True)

archivo_salida = carpeta_crudos / "bcrp_inflacion.csv"

# ============================================================
# 5. GUARDAR RESPUESTA ORIGINAL SIN MODIFICAR
# ============================================================

with open(archivo_salida, "w", encoding="utf-8-sig") as archivo:
    archivo.write(respuesta.text)

print("\nArchivo crudo guardado en:")
print(archivo_salida)

# ============================================================
# 6. CONTAR REGISTROS RECIBIDOS
# ============================================================

lineas = [
    linea
    for linea in respuesta.text.replace("<br>", "\n").splitlines()
    if linea.strip()
]

numero_observaciones = max(len(lineas) - 1, 0)

print("\nObservaciones descargadas:", numero_observaciones)

print("\n==========================================")
print("EXTRACCIÓN FINALIZADA")
print("==========================================")