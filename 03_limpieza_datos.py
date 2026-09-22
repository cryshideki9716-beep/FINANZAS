# BRICEÑO LEON CRYSTELL HIDEKI
# Código de matrícula: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de procesamiento: 20/09/2026

import pandas as pd
import numpy as np
from io import StringIO

# Leer el archivo crudo descargado del BCRP
with open("datos_crudos_2024200485D.csv", "r", encoding="utf-8-sig") as archivo:
    contenido = archivo.read()

# Convertir los <br> del BCRP en filas
contenido = contenido.replace("<br>", "\n")

# Leer los datos como tabla
df = pd.read_csv(StringIO(contenido))

print("Datos cargados correctamente.")
print("Número de filas:", len(df))
print("Número de columnas:", len(df.columns))
print("\nNombres de las columnas:")
print(df.columns.tolist())

# Renombrar las columnas para facilitar el análisis
df.columns = [
    "fecha",
    "credito_mn",
    "credito_me",
    "ratio_dolarizacion",
    "tipo_cambio",
    "tasa_mn",
    "tasa_me"
]

print("\nColumnas renombradas correctamente:")
print(df.columns.tolist())

# Convertir las tasas a valores numéricos
df["tasa_mn"] = pd.to_numeric(df["tasa_mn"], errors="coerce")
df["tasa_me"] = pd.to_numeric(df["tasa_me"], errors="coerce")

# Calcular el diferencial de tasas
df["diferencial_tasas"] = df["tasa_mn"] - df["tasa_me"]

print("\nDiferencial de tasas calculado correctamente.")
print(df[["fecha", "tasa_mn", "tasa_me", "diferencial_tasas"]].head())

# Convertir el tipo de cambio a valor numérico
df["tipo_cambio"] = pd.to_numeric(df["tipo_cambio"], errors="coerce")

# Calcular la variación porcentual mensual del tipo de cambio
df["variacion_tc"] = df["tipo_cambio"].pct_change() * 100

# Calcular la volatilidad cambiaria móvil de 12 meses
df["volatilidad_cambiaria"] = df["variacion_tc"].rolling(window=12).std()

print("\nVolatilidad cambiaria calculada correctamente.")
print(df[["fecha", "tipo_cambio", "variacion_tc", "volatilidad_cambiaria"]].head(15))

# Guardar la base de datos procesada
df.to_csv(
    "datos_procesados_2024200485D.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nBase procesada guardada correctamente.")
print("Observaciones totales:", len(df))
print("Columnas totales:", len(df.columns))