# BRICEÑO LEON CRYSTELL HIDEKI
# Código de matrícula: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 20/09/2026

import requests
import pandas as pd

# Periodo de estudio
FECHA_INICIO = "2003-1"
FECHA_CORTE = "2025-12"

# Series mensuales del BCRP
SERIES = {
    "credito_mn": "PN00496MM",
    "credito_me": "PN00499MM",
    "ratio_dolarizacion": "PN00511MM",
    "tipo_cambio": "PN01207PM",
    "tasa_mn": "PN07807NM",
    "tasa_me": "PN07827NM"
}

# Construir la URL de consulta a la API del BCRP
codigos = "-".join(SERIES.values())

URL_API = (
    f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"
    f"{codigos}/csv/{FECHA_INICIO}/{FECHA_CORTE}/esp"
)

print("URL de consulta:")
print(URL_API)

# Realizar la solicitud a la API del BCRP
respuesta = requests.get(URL_API, timeout=60)

print("Código de respuesta HTTP:", respuesta.status_code)

# Mostrar una pequeña parte de los datos recibidos
print("\nPrimeros datos recibidos del BCRP:")
print(respuesta.text[:1000])

# Guardar la respuesta original del BCRP sin modificar
with open("datos_crudos_2024200485D.csv", "w", encoding="utf-8-sig") as archivo:
    archivo.write(respuesta.text)

print("\nArchivo crudo guardado correctamente.")

# Contar las observaciones descargadas
lineas = respuesta.text.replace("<br>", "\n").strip().split("\n")

# Se resta 1 porque la primera línea corresponde a los encabezados
numero_observaciones = len(lineas) - 1

print("Número de observaciones descargadas:", numero_observaciones)