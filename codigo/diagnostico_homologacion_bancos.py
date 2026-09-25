# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de diagnóstico: 2026-09-24

from pathlib import Path
import sys

import pandas as pd


# ============================================================
# 1. OBJETIVO DEL DIAGNÓSTICO
# ============================================================

"""
DIAGNÓSTICO DE HOMOLOGACIÓN BANCARIA

Este script:

1. Lee únicamente Y, X1, X2 y X3.
2. NO modifica ningún CSV.
3. NO escribe archivos nuevos.
4. NO homologa X4 porque inflación no tiene dimensión bancaria.
5. NO interpola.
6. NO elimina observaciones.
7. NO une las variables.
8. NO construye todavía 03_limpieza_datos.py.

Objetivos:

- Aplicar temporalmente la tabla explícita:

      fuente + nombre_original -> banco_id

- Comprobar que TODOS los nombres originales observados
  tengan un banco_id definido.

- Comprobar que la tabla no contenga nombres adicionales
  que no existan en el archivo correspondiente.

- Comprobar que el número de filas no cambie
  después de asignar banco_id.

- Detectar cualquier colisión por:

      ["banco_id", "mes"]

  dentro de cada fuente.

- Mostrar, si existiera una colisión:

      fuente
      mes
      banco_id
      nombre_original involucrado
      número de filas

Resultado exigido:

    Y  -> 0 filas duplicadas
    X1 -> 0 filas duplicadas
    X2 -> 0 filas duplicadas
    X3 -> 0 filas duplicadas
"""


# ============================================================
# 2. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS = {
    "Y": (
        RAIZ
        / "datos_procesados"
        / "Y_dolarizacion_credito_2024200485D.csv"
    ),
    "X1": (
        RAIZ
        / "datos_procesados"
        / "X1_dolarizacion_depositos_2024200485D.csv"
    ),
    "X2": (
        RAIZ
        / "datos_procesados"
        / "X2_tasa_activa_consumo_mn_2024200485D.csv"
    ),
    "X3": (
        RAIZ
        / "datos_procesados"
        / "X3_tasa_pasiva_ahorro_mn_2024200485D.csv"
    ),
}


# ============================================================
# 3. TABLA EXPLÍCITA DE HOMOLOGACIÓN
# ============================================================

"""
IMPORTANTE:

Las claves de estos diccionarios son LITERALES.

No se:

- eliminan asteriscos automáticamente;
- eliminan prefijos "B.";
- eliminan textos de sucursales;
- eliminan "Perú";
- corrigen espacios;
- corrigen tildes;
- corrigen puntuación;
- normalizan nombres por similitud.

Cada nombre debe coincidir exactamente con lo observado
en su fuente.

Santander Perú y Santander Consumer Bank se mantienen
deliberadamente como entidades separadas.
"""


HOMOLOGACION_Y = {

    # Alfin / antiguo Banco Azteca
    "Banco Azteca": "alfin",
    "Alfin Banco1/": "alfin",
    "Alfin Banco": "alfin",

    # BBVA / antiguo Banco Continental
    "Banco Continental": "bbva",
    "Banco BBVA Perú*": "bbva",
    "Banco BBVA Perú": "bbva",

    # BCI
    "Banco BCI Perú**": "bci",
    "Banco BCI Perú": "bci",

    # BIF
    "Banco Interamericano de Finanzas": "bif",
    "Banco Interamericano de Finanzas*": "bif",

    # Bancom / Banco de Comercio
    "Banco de Comercio": "bancom",
    "BANCOM": "bancom",

    # Bank of China
    "Bank of China*": "bank_of_china",
    "Bank of China": "bank_of_china",

    # Cencosud / CAT
    "B. Cencosud": "cencosud_cat",

    # Citibank
    "Citibank": "citibank",

    # Compartamos
    "Compartamos Banco*": "compartamos",
    "Compartamos Banco": "compartamos",

    # Banco de Crédito del Perú
    "Banco de Crédito del Perú": "bcp",

    # Deutsche
    "Deutsche Bank": "deutsche",

    # Falabella
    "Banco Falabella Perú": "falabella",

    # GNB
    "Banco GNB": "gnb",

    # ICBC
    "B. ICBC": "icbc",

    # Interbank
    "Interbank": "interbank",
    "Interbank **": "interbank",

    # Mibanco
    "Mibanco": "mibanco",

    # Pichincha / antiguo Banco Financiero
    "Banco Financiero": "pichincha",
    "Banco Pichincha": "pichincha",
    "Banco Pichincha*": "pichincha",
    "Banco Pichincha *": "pichincha",

    # Ripley
    "Banco Ripley": "ripley",

    # Santander Consumer Bank
    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

    # Santander Perú
    "Santander Perú S.A.": "santander_peru",

    # Scotiabank
    "Scotiabank Perú": "scotiabank",
}


HOMOLOGACION_X1 = {

    # Alfin / antiguo Banco Azteca
    "B. Azteca Perú": "alfin",
    "Alfin Banco 1/": "alfin",
    "Alfin Banco": "alfin",

    # BBVA / antiguo Banco Continental
    "B. Continental": "bbva",
    "B. BBVA Perú*": "bbva",
    "B. BBVA Perú": "bbva",

    # BCI
    "Banco BCI Perú*": "bci",
    "Banco BCI Perú": "bci",

    # BIF
    "B. Interamericano de Finanzas": "bif",

    # Bancom / Banco de Comercio
    "B. de Comercio": "bancom",
    "BANCOM": "bancom",

    # Bank of China
    "Bank of China*": "bank_of_china",
    "Bank of China": "bank_of_china",

    # Cencosud / CAT
    "B. Cencosud": "cencosud_cat",

    # Citibank
    "Citibank": "citibank",

    # Compartamos
    "Compartamos Banco": "compartamos",

    # Banco de Crédito del Perú
    "B. de Crédito del Perú (con sucursales en el exterior)": "bcp",

    # Deutsche
    "Deutsche Bank Perú": "deutsche",

    # Falabella
    "B. Falabella Perú .": "falabella",

    # Financiero / Pichincha
    "B. Financiero": "pichincha",
    "B. Pichincha*": "pichincha",
    "B. Pichincha": "pichincha",

    # GNB
    "B. GNB": "gnb",

    # ICBC
    "B. ICBC": "icbc",

    # Interbank
    "Interbank": "interbank",
    "Interbank (con sucursales en el exterior)": "interbank",

    # Mibanco
    "Mibanco": "mibanco",

    # Ripley
    "B. Ripley": "ripley",

    # Santander Perú
    "B. Santander Perú": "santander_peru",

    # Santander Consumer Bank
    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

    # Scotiabank
    "Scotiabank Perú (con sucursales en el exterior)": "scotiabank",
    "Scotiabank Perú¨*": "scotiabank",
    "Scotiabank Perú": "scotiabank",
}


HOMOLOGACION_X2 = {

    "Alfin": "alfin",
    "Azteca": "alfin",

    "BBVA": "bbva",
    "Continental": "bbva",

    "BCI": "bci",

    "BIF": "bif",

    "Bancom": "bancom",
    "Comercio": "bancom",

    "Bank of China": "bank_of_china",

    "CAT": "cencosud_cat",

    "Citibank": "citibank",

    "Compartamos": "compartamos",

    "Crédito": "bcp",

    "Deutsche": "deutsche",

    "Falabella": "falabella",

    "Financiero": "pichincha",
    "Pichincha": "pichincha",

    "GNB": "gnb",

    "ICBC": "icbc",

    "Interbank": "interbank",

    "Mibanco": "mibanco",

    "Ripley": "ripley",

    "Santander": "santander_peru",

    "Santander Cons. Bank": "santander_consumer",

    "Scotiabank": "scotiabank",
}


HOMOLOGACION_X3 = {

    "Alfin": "alfin",
    "Azteca": "alfin",

    "BBVA": "bbva",
    "Continental": "bbva",

    "BCI": "bci",

    "BIF": "bif",

    "Bancom": "bancom",
    "Comercio": "bancom",

    "Bank of China": "bank_of_china",

    "CAT": "cencosud_cat",

    "Citibank": "citibank",

    "Compartamos": "compartamos",

    "Crédito": "bcp",

    "Deutsche": "deutsche",

    "Falabella": "falabella",

    "Financiero": "pichincha",
    "Pichincha": "pichincha",

    "GNB": "gnb",

    "ICBC": "icbc",

    "Interbank": "interbank",

    "Mibanco": "mibanco",

    "Ripley": "ripley",

    "Santander": "santander_peru",

    "Santander Cons. Bank": "santander_consumer",

    "Scotiabank": "scotiabank",
}


HOMOLOGACIONES = {
    "Y": HOMOLOGACION_Y,
    "X1": HOMOLOGACION_X1,
    "X2": HOMOLOGACION_X2,
    "X3": HOMOLOGACION_X3,
}


# ============================================================
# 4. NÚMERO ESPERADO DE NOMBRES LITERALES
# ============================================================

NOMBRES_ESPERADOS = {
    "Y": 35,
    "X1": 34,
    "X2": 25,
    "X3": 25,
}


# ============================================================
# 5. LECTURA MÍNIMA DE CADA FUENTE
# ============================================================

def leer_fuente(fuente, ruta):
    """
    Lee únicamente las columnas necesarias para este diagnóstico.

    keep_default_na=False evita que cadenas de texto puedan
    transformarse automáticamente en NaN.

    No se realiza strip(), lower(), reemplazo de asteriscos
    ni ninguna normalización del nombre bancario.
    """

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo de {fuente}: {ruta}"
        )

    df = pd.read_csv(
        ruta,
        usecols=[
            "mes",
            "banco_original",
        ],
        dtype={
            "mes": "string",
            "banco_original": "string",
        },
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    return df


# ============================================================
# 6. MOSTRAR DIFERENCIAS DE COBERTURA
# ============================================================

def mostrar_lista(titulo, valores):

    print(titulo)

    if not valores:
        print("  Ninguno")
        return

    for valor in sorted(valores):
        print(f"  - {repr(valor)}")


# ============================================================
# 7. DIAGNOSTICAR UNA FUENTE
# ============================================================

def diagnosticar_fuente(fuente, ruta, homologacion):

    print()
    print("=" * 100)
    print(f"FUENTE: {fuente}")
    print("=" * 100)

    df = leer_fuente(
        fuente=fuente,
        ruta=ruta,
    )

    filas_antes = len(df)

    nombres_observados = set(
        df["banco_original"].tolist()
    )

    nombres_mapeados = set(
        homologacion.keys()
    )

    sin_mapeo = (
        nombres_observados
        - nombres_mapeados
    )

    mapeos_no_observados = (
        nombres_mapeados
        - nombres_observados
    )

    print(f"Archivo: {ruta}")
    print(f"Filas antes del mapeo: {filas_antes}")
    print(
        "Nombres originales observados: "
        f"{len(nombres_observados)}"
    )
    print(
        "Nombres incluidos en la tabla: "
        f"{len(nombres_mapeados)}"
    )

    print()

    mostrar_lista(
        "NOMBRES OBSERVADOS SIN MAPEO:",
        sin_mapeo,
    )

    print()

    mostrar_lista(
        "NOMBRES DE LA TABLA NO OBSERVADOS EN EL CSV:",
        mapeos_no_observados,
    )

    # --------------------------------------------------------
    # El diagnóstico exige coincidencia exacta entre:
    # nombres observados y nombres definidos en la tabla.
    # --------------------------------------------------------

    cobertura_exacta = (
        len(sin_mapeo) == 0
        and
        len(mapeos_no_observados) == 0
    )

    # --------------------------------------------------------
    # Aplicar banco_id SOLO EN MEMORIA.
    # --------------------------------------------------------

    df_mapeado = df.copy()

    df_mapeado["banco_id"] = (
        df_mapeado["banco_original"]
        .map(homologacion)
    )

    filas_despues = len(df_mapeado)

    banco_id_faltantes = int(
        df_mapeado["banco_id"]
        .isna()
        .sum()
    )

    print()
    print(
        "Filas después del mapeo: "
        f"{filas_despues}"
    )

    print(
        "Filas con banco_id faltante: "
        f"{banco_id_faltantes}"
    )

    print(
        "banco_id distintos: "
        f"{df_mapeado['banco_id'].nunique(dropna=False)}"
    )

    filas_conservadas = (
        filas_antes
        ==
        filas_despues
    )

    # --------------------------------------------------------
    # Detectar duplicados por banco_id + mes.
    # keep=False marca TODAS las filas involucradas.
    # --------------------------------------------------------

    mascara_duplicados = (
        df_mapeado.duplicated(
            subset=[
                "banco_id",
                "mes",
            ],
            keep=False,
        )
    )

    colisiones = (
        df_mapeado.loc[
            mascara_duplicados,
            [
                "mes",
                "banco_id",
                "banco_original",
            ],
        ]
        .copy()
    )

    numero_filas_duplicadas = len(
        colisiones
    )

    numero_claves_colisionadas = 0

    print()
    print("-" * 100)
    print("CONTROL DE COLISIONES")
    print("-" * 100)

    print(
        "Filas duplicadas por "
        "['banco_id', 'mes']: "
        f"{numero_filas_duplicadas}"
    )

    if numero_filas_duplicadas > 0:

        resumen_colisiones = (
            colisiones
            .groupby(
                [
                    "mes",
                    "banco_id",
                ],
                sort=True,
                dropna=False,
            )
            .agg(
                numero_filas=(
                    "banco_original",
                    "size",
                ),
                nombres_originales=(
                    "banco_original",
                    lambda serie: " | ".join(
                        repr(x)
                        for x in serie.tolist()
                    ),
                ),
            )
            .reset_index()
        )

        numero_claves_colisionadas = len(
            resumen_colisiones
        )

        resumen_colisiones.insert(
            0,
            "fuente",
            fuente,
        )

        print()
        print(
            "CLAVES banco_id + mes "
            "CON COLISIÓN:"
        )

        print(
            resumen_colisiones.to_string(
                index=False
            )
        )

        print()
        print(
            "FILAS INDIVIDUALES "
            "INVOLUCRADAS:"
        )

        detalle = (
            colisiones
            .sort_values(
                [
                    "mes",
                    "banco_id",
                    "banco_original",
                ]
            )
            .copy()
        )

        detalle.insert(
            0,
            "fuente",
            fuente,
        )

        print(
            detalle.to_string(
                index=False
            )
        )

    else:

        print(
            "No se detectaron colisiones "
            "banco_id + mes."
        )

    # --------------------------------------------------------
    # Resultado individual.
    # --------------------------------------------------------

    fuente_valida = all(
        [
            cobertura_exacta,
            banco_id_faltantes == 0,
            filas_conservadas,
            numero_filas_duplicadas == 0,
        ]
    )

    return {
        "fuente": fuente,
        "filas_antes": filas_antes,
        "filas_despues": filas_despues,
        "nombres_observados": len(
            nombres_observados
        ),
        "nombres_tabla": len(
            nombres_mapeados
        ),
        "sin_mapeo": len(
            sin_mapeo
        ),
        "mapeos_no_observados": len(
            mapeos_no_observados
        ),
        "banco_id_faltantes": banco_id_faltantes,
        "banco_id_distintos": int(
            df_mapeado["banco_id"]
            .nunique(
                dropna=False
            )
        ),
        "claves_colisionadas": (
            numero_claves_colisionadas
        ),
        "filas_duplicadas": (
            numero_filas_duplicadas
        ),
        "filas_conservadas": filas_conservadas,
        "cobertura_exacta": cobertura_exacta,
        "fuente_valida": fuente_valida,
    }


# ============================================================
# 8. VALIDAR LA PROPIA TABLA ANTES DE LEER LOS CSV
# ============================================================

def validar_tablas_homologacion():

    print("=" * 100)
    print("VALIDACIÓN INTERNA DE LAS TABLAS DE HOMOLOGACIÓN")
    print("=" * 100)

    errores = []

    for fuente in [
        "Y",
        "X1",
        "X2",
        "X3",
    ]:

        tabla = HOMOLOGACIONES[fuente]

        cantidad = len(tabla)

        esperado = NOMBRES_ESPERADOS[
            fuente
        ]

        print(
            f"{fuente}: "
            f"{cantidad} nombres definidos "
            f"(esperados: {esperado})"
        )

        if cantidad != esperado:

            errores.append(
                f"{fuente}: "
                f"tabla tiene {cantidad} nombres, "
                f"pero se esperaban {esperado}."
            )

        # Ningún banco_id debe estar vacío.
        ids_vacios = [
            nombre
            for nombre, banco_id
            in tabla.items()
            if not str(banco_id).strip()
        ]

        if ids_vacios:

            errores.append(
                f"{fuente}: "
                "hay banco_id vacíos."
            )

    if errores:

        print()
        print("ERRORES EN LA TABLA:")

        for error in errores:
            print(f"  - {error}")

        raise RuntimeError(
            "La tabla de homologación "
            "no pasó su control interno."
        )

    print()
    print(
        "Las cuatro tablas contienen "
        "el número esperado de nombres."
    )


# ============================================================
# 9. EJECUCIÓN PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 100)
    print("DIAGNÓSTICO DE HOMOLOGACIÓN BANCARIA")
    print("=" * 100)

    print()
    print(
        "Este diagnóstico NO modifica "
        "ningún archivo."
    )

    print(
        "La homologación existe únicamente "
        "en memoria durante esta ejecución."
    )

    print(
        "X4 no participa porque inflación "
        "no tiene banco."
    )

    print()

    validar_tablas_homologacion()

    resultados = []

    for fuente in [
        "Y",
        "X1",
        "X2",
        "X3",
    ]:

        resultado = diagnosticar_fuente(
            fuente=fuente,
            ruta=ARCHIVOS[fuente],
            homologacion=HOMOLOGACIONES[
                fuente
            ],
        )

        resultados.append(
            resultado
        )

    # --------------------------------------------------------
    # Resumen final.
    # --------------------------------------------------------

    resumen = pd.DataFrame(
        resultados
    )

    columnas_resumen = [
        "fuente",
        "filas_antes",
        "filas_despues",
        "nombres_observados",
        "nombres_tabla",
        "sin_mapeo",
        "mapeos_no_observados",
        "banco_id_faltantes",
        "banco_id_distintos",
        "claves_colisionadas",
        "filas_duplicadas",
        "filas_conservadas",
        "cobertura_exacta",
        "fuente_valida",
    ]

    resumen = resumen[
        columnas_resumen
    ]

    print()
    print("=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)
    print()

    print(
        resumen.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Exigencia final explícita:
    # Y, X1, X2 y X3 deben tener 0 filas duplicadas.
    # --------------------------------------------------------

    fuentes_con_fallo = (
        resumen.loc[
            ~resumen[
                "fuente_valida"
            ],
            "fuente",
        ]
        .tolist()
    )

    print()
    print("=" * 100)
    print("RESULTADO EXIGIDO")
    print("=" * 100)

    for resultado in resultados:

        print(
            f"{resultado['fuente']}: "
            "filas duplicadas por "
            "['banco_id', 'mes'] = "
            f"{resultado['filas_duplicadas']}"
        )

    print()

    if fuentes_con_fallo:

        print(
            "ESTADO = "
            "DIAGNOSTICO_HOMOLOGACION_FALLIDO"
        )

        print(
            "Fuentes con algún control "
            "no superado: "
            + ", ".join(
                fuentes_con_fallo
            )
        )

        sys.exit(1)

    print(
        "ESTADO = "
        "HOMOLOGACION_BANCOS_SIN_COLISIONES_VALIDADA"
    )

    print()
    print(
        "Y, X1, X2 y X3 tienen exactamente "
        "0 filas duplicadas por banco_id + mes."
    )

    print(
        "Todos los nombres originales están "
        "mapeados y ninguna fila fue eliminada."
    )


# ============================================================
# 10. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()