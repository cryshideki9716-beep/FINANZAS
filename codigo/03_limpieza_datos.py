# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from io import StringIO
from html import unescape
import re
import unicodedata

import pandas as pd


# ============================================================
# 1. OBJETIVO
# ============================================================

"""
03_limpieza_datos.py

Objetivo:

Construir de forma reproducible:

1. Un panel integrado de trazabilidad que conserve
   todas las observaciones banco-mes disponibles y sus
   faltantes de fuente, sin imputación.

2. Una muestra econométrica formada por 12 bancos con
   presencia durante los 122 meses del periodo común,
   eliminando únicamente las filas donde alguna de las
   cinco variables del modelo esté ausente.

NO se:

- interpola;
- extrapola;
- imputa;
- reemplazan faltantes por cero;
- modifican los archivos fuente;
- modifican los nombres originales de los bancos;
- crean observaciones artificiales.

La homologación:

    fuente + banco_original -> banco_id

es exactamente la previamente diagnosticada y validada.

Variables:

Y  = dolarización del crédito (%)
X1 = dolarización de depósitos (%)
X2 = tasa activa Consumo MN
X3 = tasa pasiva Depósitos de Ahorro MN
X4 = inflación mensual (%)

Llave bancaria:

    mes + banco_id

X4 se incorpora solamente por:

    mes
"""


# ============================================================
# 2. PARÁMETROS GENERALES
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

FECHA_INICIO = "2015-11"
FECHA_CORTE = "2025-12"

MESES_ESPERADOS = 122

FILAS_PANEL_ESPERADAS = 2005
FILAS_COMPLETAS_UNIVERSO_ESPERADAS = 1482

BANCOS_SELECCIONADOS_ESPERADOS = 12
FILAS_POTENCIALES_12_BANCOS = 1464
FILAS_INCOMPLETAS_12_BANCOS = 6
FILAS_MUESTRA_FINAL_ESPERADAS = 1458


VARIABLES = [
    "Y",
    "X1",
    "X2",
    "X3",
    "X4",
]


BANCOS_MUESTRA = [
    "alfin",
    "bancom",
    "bbva",
    "bcp",
    "bif",
    "falabella",
    "gnb",
    "interbank",
    "mibanco",
    "pichincha",
    "ripley",
    "scotiabank",
]


# ============================================================
# 3. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_PROCESADOS = (
    RAIZ
    / "datos_procesados"
)

CARPETA_PROCESADOS.mkdir(
    parents=True,
    exist_ok=True,
)


RUTA_Y = (
    CARPETA_PROCESADOS
    / f"Y_dolarizacion_credito_{CODIGO_ESTUDIANTE}.csv"
)

RUTA_X1 = (
    CARPETA_PROCESADOS
    / f"X1_dolarizacion_depositos_{CODIGO_ESTUDIANTE}.csv"
)

RUTA_X2 = (
    CARPETA_PROCESADOS
    / f"X2_tasa_activa_consumo_mn_{CODIGO_ESTUDIANTE}.csv"
)

RUTA_X3 = (
    CARPETA_PROCESADOS
    / f"X3_tasa_pasiva_ahorro_mn_{CODIGO_ESTUDIANTE}.csv"
)

RUTA_X4 = (
    RAIZ
    / "datos_crudos"
    / "bcrp_inflacion.csv"
)


SALIDA_PANEL = (
    CARPETA_PROCESADOS
    / f"panel_integrado_trazabilidad_{CODIGO_ESTUDIANTE}.csv"
)

SALIDA_MUESTRA = (
    CARPETA_PROCESADOS
    / f"muestra_econometrica_12_bancos_{CODIGO_ESTUDIANTE}.csv"
)

# Archivo procesado principal exigido por la consigna.
# Debe ser idéntico a la muestra econométrica final.
SALIDA_DATOS_PROCESADOS = (
    CARPETA_PROCESADOS
    / f"datos_procesados_{CODIGO_ESTUDIANTE}.csv"
)


# ============================================================
# 4. HOMOLOGACIÓN VALIDADA - Y
# ============================================================

HOMOLOGACION_Y = {

    # Azteca -> Alfin
    "Banco Azteca": "alfin",
    "Alfin Banco1/": "alfin",
    "Alfin Banco": "alfin",

    # Continental -> BBVA
    "Banco Continental": "bbva",
    "Banco BBVA Perú*": "bbva",
    "Banco BBVA Perú": "bbva",

    # BCI
    "Banco BCI Perú**": "bci",
    "Banco BCI Perú": "bci",

    # BIF
    "Banco Interamericano de Finanzas": "bif",
    "Banco Interamericano de Finanzas*": "bif",

    # Comercio -> Bancom
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

    # BCP
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

    # Financiero -> Pichincha
    "Banco Financiero": "pichincha",
    "Banco Pichincha": "pichincha",
    "Banco Pichincha*": "pichincha",
    "Banco Pichincha *": "pichincha",

    # Ripley
    "Banco Ripley": "ripley",

    # Santander Perú
    "Santander Perú S.A.": "santander_peru",

    # Santander Consumer
    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

    # Scotiabank
    "Scotiabank Perú": "scotiabank",
}


# ============================================================
# 5. HOMOLOGACIÓN VALIDADA - X1
# ============================================================

HOMOLOGACION_X1 = {

    # Azteca -> Alfin
    "B. Azteca Perú": "alfin",
    "Alfin Banco 1/": "alfin",
    "Alfin Banco": "alfin",

    # Continental -> BBVA
    "B. Continental": "bbva",
    "B. BBVA Perú*": "bbva",
    "B. BBVA Perú": "bbva",

    # BCI
    "Banco BCI Perú*": "bci",
    "Banco BCI Perú": "bci",

    # BIF
    "B. Interamericano de Finanzas": "bif",

    # Comercio -> Bancom
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

    # BCP
    "B. de Crédito del Perú (con sucursales en el exterior)": "bcp",

    # Deutsche
    "Deutsche Bank Perú": "deutsche",

    # Falabella
    "B. Falabella Perú .": "falabella",

    # Financiero -> Pichincha
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

    # Santander Consumer
    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

    # Scotiabank
    "Scotiabank Perú (con sucursales en el exterior)": "scotiabank",
    "Scotiabank Perú¨*": "scotiabank",
    "Scotiabank Perú": "scotiabank",
}


# ============================================================
# 6. HOMOLOGACIÓN VALIDADA - X2
# ============================================================

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


# ============================================================
# 7. HOMOLOGACIÓN VALIDADA - X3
# ============================================================

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


# ============================================================
# 8. CONTROL GENERAL
# ============================================================

def exigir(condicion, mensaje):
    """
    Control explícito.

    Se utiliza RuntimeError en vez de assert para que
    los controles no puedan desactivarse mediante
    python -O.
    """

    if not condicion:
        raise RuntimeError(
            mensaje
        )


# ============================================================
# 9. LEER CSV BANCARIO SIN ALTERAR EL ARCHIVO
# ============================================================

def leer_csv_bancario(ruta, fuente):

    if not ruta.exists():
        raise FileNotFoundError(
            f"{fuente}: no existe el archivo:\n{ruta}"
        )

    # dtype="string" preserva literalmente los tokens
    # que vienen de la fuente.
    #
    # keep_default_na=False evita convertir automáticamente
    # determinados textos a NaN antes de aplicar nuestras
    # reglas explícitas.

    df = pd.read_csv(
        ruta,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    return df


# ============================================================
# 10. VALIDAR FORMATO DE MES
# ============================================================

def validar_mes_yyyy_mm(serie, fuente):

    texto = (
        serie
        .astype("string")
        .str.strip()
    )

    valido = texto.str.fullmatch(
        r"\d{4}-\d{2}",
        na=False,
    )

    if not valido.all():

        invalidos = (
            texto.loc[
                ~valido
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{fuente}: existen meses "
            f"con formato distinto de YYYY-MM: "
            f"{invalidos}"
        )

    return texto


# ============================================================
# 11. CONVERTIR VARIABLE NUMÉRICA SIN IMPUTAR
# ============================================================

def convertir_numerico_sin_imputar(
    serie,
    fuente,
    columna,
):

    """
    Convierte a valor numérico únicamente en memoria.

    Marcadores explícitos de faltante de fuente:

        ""
        "-"
        "—"
        "–"
        "s.i."

    Todos se convierten a pd.NA/NaN únicamente para
    trabajar con la base procesada.

    NUNCA se convierten en cero.

    Cualquier otro token no numérico provoca error.
    """

    texto = (
        serie
        .astype("string")
        .str.strip()
    )

    marcadores_faltante = {
        "",
        "-",
        "—",
        "–",
        "s.i.",
    }

    es_faltante = (
        texto.isna()
        |
        texto.isin(
            marcadores_faltante
        )
    )

    para_convertir = (
        texto
        .mask(
            es_faltante,
            pd.NA,
        )
        .str.replace(
            ",",
            ".",
            regex=False,
        )
    )

    numerico = pd.to_numeric(
        para_convertir,
        errors="coerce",
    )

    token_invalido = (
        ~es_faltante
        &
        numerico.isna()
    )

    if token_invalido.any():

        valores = (
            texto.loc[
                token_invalido
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{fuente}: la columna "
            f"{columna!r} contiene tokens "
            f"no numéricos no autorizados: "
            f"{valores}"
        )

    return numerico


# ============================================================
# 12. VALIDAR COBERTURA EXACTA DE HOMOLOGACIÓN
# ============================================================

def validar_homologacion_exacta(
    df,
    fuente,
    homologacion,
):

    if "banco_original" not in df.columns:
        raise ValueError(
            f"{fuente}: falta banco_original."
        )

    nombres_observados = set(
        df[
            "banco_original"
        ]
        .astype("string")
        .tolist()
    )

    nombres_tabla = set(
        homologacion.keys()
    )

    sin_mapeo = (
        nombres_observados
        -
        nombres_tabla
    )

    no_observados = (
        nombres_tabla
        -
        nombres_observados
    )

    if sin_mapeo or no_observados:

        raise RuntimeError(
            f"{fuente}: la tabla de homologación "
            "ya no coincide exactamente con el CSV.\n"
            f"Nombres sin mapeo: {sorted(sin_mapeo)}\n"
            "Nombres definidos pero no observados: "
            f"{sorted(no_observados)}"
        )


# ============================================================
# 13. PREPARAR FUENTE BANCARIA
# ============================================================

def preparar_fuente_bancaria(
    df,
    fuente,
    homologacion,
    columna_variable,
    nombre_variable,
    conservar_fecha_sbs=False,
):

    columnas_necesarias = {
        "mes",
        "banco_original",
        columna_variable,
    }

    if conservar_fecha_sbs:
        columnas_necesarias.add(
            "fecha_sbs"
        )

    faltan = (
        columnas_necesarias
        -
        set(df.columns)
    )

    if faltan:
        raise ValueError(
            f"{fuente}: faltan columnas requeridas: "
            f"{sorted(faltan)}"
        )

    validar_homologacion_exacta(
        df=df,
        fuente=fuente,
        homologacion=homologacion,
    )

    columnas_trabajo = [
        "mes",
        "banco_original",
        columna_variable,
    ]

    if conservar_fecha_sbs:
        columnas_trabajo.append(
            "fecha_sbs"
        )

    trabajo = df[
        columnas_trabajo
    ].copy()

    trabajo["mes"] = validar_mes_yyyy_mm(
        trabajo["mes"],
        fuente,
    )

    # --------------------------------------------------------
    # Banco_id aprobado.
    # --------------------------------------------------------

    trabajo["banco_id"] = (
        trabajo[
            "banco_original"
        ]
        .map(
            homologacion
        )
    )

    exigir(
        trabajo[
            "banco_id"
        ].notna().all(),
        f"{fuente}: quedaron bancos sin banco_id.",
    )

    # --------------------------------------------------------
    # Variable numérica.
    # --------------------------------------------------------

    trabajo[
        nombre_variable
    ] = convertir_numerico_sin_imputar(
        trabajo[
            columna_variable
        ],
        fuente,
        columna_variable,
    )

    # --------------------------------------------------------
    # Control de colisiones.
    # --------------------------------------------------------

    duplicados = (
        trabajo.duplicated(
            subset=[
                "mes",
                "banco_id",
            ],
            keep=False,
        )
    )

    if duplicados.any():

        detalle = (
            trabajo.loc[
                duplicados,
                [
                    "mes",
                    "banco_id",
                    "banco_original",
                ],
            ]
            .sort_values(
                [
                    "mes",
                    "banco_id",
                    "banco_original",
                ]
            )
        )

        raise RuntimeError(
            f"{fuente}: aparecieron colisiones "
            "mes + banco_id después de homologar:\n"
            f"{detalle.to_string(index=False)}"
        )

    # --------------------------------------------------------
    # Renombrar columnas de trazabilidad.
    # --------------------------------------------------------

    trabajo = trabajo.rename(
        columns={
            "banco_original":
                f"banco_original_{fuente}"
        }
    )

    columnas_salida = [
        "mes",
        "banco_id",
        f"banco_original_{fuente}",
        nombre_variable,
    ]

    if conservar_fecha_sbs:

        trabajo = trabajo.rename(
            columns={
                "fecha_sbs":
                    f"fecha_sbs_{fuente}"
            }
        )

        columnas_salida.insert(
            3,
            f"fecha_sbs_{fuente}",
        )

    return trabajo[
        columnas_salida
    ].copy()


# ============================================================
# 14. QUITAR TILDES PARA MES BCRP
# ============================================================

def quitar_tildes(texto):

    normalizado = unicodedata.normalize(
        "NFKD",
        texto,
    )

    return "".join(
        caracter
        for caracter
        in normalizado
        if not unicodedata.combining(
            caracter
        )
    )


# ============================================================
# 15. CONVERTIR MES BCRP A YYYY-MM
# ============================================================

def convertir_mes_bcrp(valor):

    if pd.isna(valor):
        raise ValueError(
            "X4: se encontró una fecha vacía."
        )

    texto = unescape(
        str(valor)
    ).strip()

    coincidencia = re.fullmatch(
        r"([A-Za-zÁÉÍÓÚÑáéíóúñ]+)\.(\d{4})",
        texto,
    )

    if coincidencia is None:
        raise ValueError(
            "X4: formato de fecha "
            f"no reconocido: {repr(texto)}"
        )

    mes_texto = quitar_tildes(
        coincidencia.group(1)
    ).lower()

    anio = coincidencia.group(2)

    mapa_meses = {
        "ene": "01",
        "feb": "02",
        "mar": "03",
        "abr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "sep": "09",
        "set": "09",
        "oct": "10",
        "nov": "11",
        "dic": "12",
    }

    if mes_texto not in mapa_meses:
        raise ValueError(
            "X4: abreviatura mensual "
            f"no reconocida: {repr(mes_texto)}"
        )

    return (
        f"{anio}-"
        f"{mapa_meses[mes_texto]}"
    )


# ============================================================
# 16. LEER X4 DESDE EL CRUDO ORIGINAL
# ============================================================

def leer_x4_bcrp(ruta):

    if not ruta.exists():
        raise FileNotFoundError(
            f"X4: no existe:\n{ruta}"
        )

    # --------------------------------------------------------
    # Se lee el archivo original como texto.
    # NO se modifica.
    # --------------------------------------------------------

    raw = ruta.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    # --------------------------------------------------------
    # <br> se sustituye únicamente en memoria.
    # --------------------------------------------------------

    texto_memoria = raw.replace(
        "<br>",
        "\n",
    )

    df = pd.read_csv(
        StringIO(
            texto_memoria
        ),
        dtype="string",
        keep_default_na=False,
    )

    # Decodificar entidades HTML del encabezado.
    df.columns = [
        unescape(
            str(columna)
        ).strip()
        for columna
        in df.columns
    ]

    columnas_esperadas = [
        "Mes/Año",
        (
            "Índice de precios Lima Metropolitana "
            "(var% mensual) - IPC"
        ),
    ]

    if df.columns.tolist() != columnas_esperadas:

        raise RuntimeError(
            "X4: el encabezado cambió.\n"
            "Esperado:\n"
            f"{columnas_esperadas}\n"
            "Observado:\n"
            f"{df.columns.tolist()}"
        )

    columna_mes = columnas_esperadas[0]
    columna_valor = columnas_esperadas[1]

    trabajo = df[
        [
            columna_mes,
            columna_valor,
        ]
    ].copy()

    trabajo["mes"] = (
        trabajo[
            columna_mes
        ]
        .apply(
            convertir_mes_bcrp
        )
        .astype(
            "string"
        )
    )

    trabajo["X4"] = (
        convertir_numerico_sin_imputar(
            trabajo[
                columna_valor
            ],
            "X4",
            columna_valor,
        )
    )

    duplicados = (
        trabajo.duplicated(
            subset=[
                "mes"
            ],
            keep=False,
        )
    )

    if duplicados.any():

        detalle = (
            trabajo.loc[
                duplicados,
                [
                    "mes",
                    columna_mes,
                    columna_valor,
                ],
            ]
        )

        raise RuntimeError(
            "X4: existen meses duplicados:\n"
            f"{detalle.to_string(index=False)}"
        )

    return trabajo[
        [
            "mes",
            "X4",
        ]
    ].copy()


# ============================================================
# 17. OBTENER PERIODO COMÚN
# ============================================================

def obtener_periodo_comun(
    y,
    x1,
    x2,
    x3,
    x4,
):

    conjuntos = [
        set(y["mes"]),
        set(x1["mes"]),
        set(x2["mes"]),
        set(x3["mes"]),
        set(x4["mes"]),
    ]

    comunes = sorted(
        set.intersection(
            *conjuntos
        )
    )

    esperados = [
        str(periodo)
        for periodo
        in pd.period_range(
            start=FECHA_INICIO,
            end=FECHA_CORTE,
            freq="M",
        )
    ]

    exigir(
        len(esperados)
        ==
        MESES_ESPERADOS,
        "La secuencia parametrizada "
        "no contiene 122 meses.",
    )

    exigir(
        comunes
        ==
        esperados,
        "El periodo común observado "
        "no coincide exactamente con "
        f"{FECHA_INICIO} a {FECHA_CORTE}.",
    )

    return comunes


# ============================================================
# 18. FILTRAR AL PERIODO COMÚN
# ============================================================

def filtrar_periodo(df, meses_comunes):

    return (
        df.loc[
            df[
                "mes"
            ].isin(
                meses_comunes
            )
        ]
        .copy()
    )


# ============================================================
# 19. CONSTRUIR PANEL INTEGRADO
# ============================================================

def construir_panel(
    y,
    x1,
    x2,
    x3,
    x4,
):

    # Y + X1
    panel = y.merge(
        x1,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    # + X2
    panel = panel.merge(
        x2,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    # + X3
    panel = panel.merge(
        x3,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    # X4 es mensual y se replica únicamente
    # sobre las filas banco-mes existentes.
    panel = panel.merge(
        x4,
        on="mes",
        how="left",
        validate="many_to_one",
    )

    panel = (
        panel
        .sort_values(
            [
                "banco_id",
                "mes",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return panel


# ============================================================
# 20. VALIDAR DUPLICADOS
# ============================================================

def contar_duplicados_llave(df):

    return int(
        df.duplicated(
            subset=[
                "mes",
                "banco_id",
            ],
            keep=False,
        ).sum()
    )


# ============================================================
# 21. GUARDAR CSV DE FORMA ATÓMICA
# ============================================================

def guardar_csv_atomico(df, ruta):

    temporal = ruta.with_suffix(
        ruta.suffix
        +
        ".tmp"
    )

    df.to_csv(
        temporal,
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    temporal.replace(
        ruta
    )


# ============================================================
# 22. EJECUCIÓN PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 100)
    print("03_LIMPIEZA_DATOS")
    print("=" * 100)

    print()
    print(
        "Metodología: sin interpolación, "
        "sin imputación y sin extrapolación."
    )

    # ========================================================
    # A. LEER FUENTES
    # ========================================================

    y_raw = leer_csv_bancario(
        RUTA_Y,
        "Y",
    )

    x1_raw = leer_csv_bancario(
        RUTA_X1,
        "X1",
    )

    x2_raw = leer_csv_bancario(
        RUTA_X2,
        "X2",
    )

    x3_raw = leer_csv_bancario(
        RUTA_X3,
        "X3",
    )

    x4 = leer_x4_bcrp(
        RUTA_X4
    )

    # ========================================================
    # B. HOMOLOGAR Y TIPIFICAR EN MEMORIA
    # ========================================================

    y = preparar_fuente_bancaria(
        df=y_raw,
        fuente="Y",
        homologacion=HOMOLOGACION_Y,
        columna_variable="dolcred_pct",
        nombre_variable="Y",
        conservar_fecha_sbs=False,
    )

    x1 = preparar_fuente_bancaria(
        df=x1_raw,
        fuente="X1",
        homologacion=HOMOLOGACION_X1,
        columna_variable="doldep_pct",
        nombre_variable="X1",
        conservar_fecha_sbs=False,
    )

    x2 = preparar_fuente_bancaria(
        df=x2_raw,
        fuente="X2",
        homologacion=HOMOLOGACION_X2,
        columna_variable=(
            "tasa_activa_consumo_mn"
        ),
        nombre_variable="X2",
        conservar_fecha_sbs=True,
    )

    x3 = preparar_fuente_bancaria(
        df=x3_raw,
        fuente="X3",
        homologacion=HOMOLOGACION_X3,
        columna_variable=(
            "tasa_pasiva_ahorro_mn"
        ),
        nombre_variable="X3",
        conservar_fecha_sbs=True,
    )

    # ========================================================
    # C. PERIODO COMÚN
    # ========================================================

    meses_comunes = obtener_periodo_comun(
        y=y,
        x1=x1,
        x2=x2,
        x3=x3,
        x4=x4,
    )

    y = filtrar_periodo(
        y,
        meses_comunes,
    )

    x1 = filtrar_periodo(
        x1,
        meses_comunes,
    )

    x2 = filtrar_periodo(
        x2,
        meses_comunes,
    )

    x3 = filtrar_periodo(
        x3,
        meses_comunes,
    )

    x4 = filtrar_periodo(
        x4,
        meses_comunes,
    )

    # ========================================================
    # D. INTEGRACIÓN
    # ========================================================

    panel = construir_panel(
        y=y,
        x1=x1,
        x2=x2,
        x3=x3,
        x4=x4,
    )

    # ========================================================
    # E. CONTROLES DEL PANEL INTEGRADO
    # ========================================================

    duplicados_panel = (
        contar_duplicados_llave(
            panel
        )
    )

    exigir(
        duplicados_panel == 0,
        "El panel integrado contiene "
        "duplicados mes + banco_id.",
    )

    meses_panel = sorted(
        panel[
            "mes"
        ]
        .drop_duplicates()
        .tolist()
    )

    exigir(
        len(meses_panel)
        ==
        MESES_ESPERADOS,
        "El panel integrado no contiene "
        "exactamente 122 meses.",
    )

    exigir(
        meses_panel[0]
        ==
        FECHA_INICIO,
        "El primer mes del panel "
        "no es 2015-11.",
    )

    exigir(
        meses_panel[-1]
        ==
        FECHA_CORTE,
        "El último mes del panel "
        "no es 2025-12.",
    )

    exigir(
        len(panel)
        ==
        FILAS_PANEL_ESPERADAS,
        "El panel integrado no contiene "
        "exactamente 2,005 filas. "
        f"Observadas: {len(panel)}.",
    )

    # --------------------------------------------------------
    # Fila completa en las cinco variables.
    # --------------------------------------------------------

    panel[
        "fila_completa_5"
    ] = (
        panel[
            VARIABLES
        ]
        .notna()
        .all(
            axis=1
        )
    )

    filas_completas_universo = int(
        panel[
            "fila_completa_5"
        ].sum()
    )

    exigir(
        filas_completas_universo
        ==
        FILAS_COMPLETAS_UNIVERSO_ESPERADAS,
        "El universo integrado no contiene "
        "exactamente 1,482 filas completas. "
        "Observadas: "
        f"{filas_completas_universo}.",
    )

    # ========================================================
    # F. CONSTRUIR SUBPANEL DE LOS 12 BANCOS ACORDADOS
    # ========================================================

    seleccion = (
        panel.loc[
            panel[
                "banco_id"
            ].isin(
                BANCOS_MUESTRA
            )
        ]
        .copy()
    )

    bancos_observados = set(
        seleccion[
            "banco_id"
        ].unique()
    )

    bancos_esperados = set(
        BANCOS_MUESTRA
    )

    exigir(
        bancos_observados
        ==
        bancos_esperados,
        "Los bancos seleccionados observados "
        "no coinciden exactamente con los "
        "12 banco_id aprobados.",
    )

    exigir(
        seleccion[
            "banco_id"
        ].nunique()
        ==
        BANCOS_SELECCIONADOS_ESPERADOS,
        "La selección no contiene "
        "exactamente 12 bancos.",
    )

    # --------------------------------------------------------
    # Cada uno de los 12 bancos debe estar presente
    # durante los 122 meses antes de eliminar faltantes.
    # --------------------------------------------------------

    cobertura_bancos = (
        seleccion
        .groupby(
            "banco_id"
        )
        .agg(
            filas=(
                "mes",
                "size",
            ),
            meses=(
                "mes",
                "nunique",
            ),
        )
    )

    cobertura_correcta = (
        (
            cobertura_bancos[
                "filas"
            ]
            ==
            MESES_ESPERADOS
        )
        &
        (
            cobertura_bancos[
                "meses"
            ]
            ==
            MESES_ESPERADOS
        )
    ).all()

    exigir(
        bool(
            cobertura_correcta
        ),
        "Al menos uno de los 12 bancos "
        "no tiene presencia en los "
        "122 meses esperados.",
    )

    exigir(
        len(seleccion)
        ==
        FILAS_POTENCIALES_12_BANCOS,
        "Los 12 bancos no generan exactamente "
        "1,464 banco-mes potenciales. "
        f"Observados: {len(seleccion)}.",
    )

    # ========================================================
    # G. IDENTIFICAR LAS 6 FILAS INCOMPLETAS
    # ========================================================

    mascara_incompleta = (
        seleccion[
            VARIABLES
        ]
        .isna()
        .any(
            axis=1
        )
    )

    numero_incompletas = int(
        mascara_incompleta.sum()
    )

    exigir(
        numero_incompletas
        ==
        FILAS_INCOMPLETAS_12_BANCOS,
        "Dentro de los 12 bancos no existen "
        "exactamente 6 filas incompletas. "
        f"Observadas: {numero_incompletas}.",
    )

    # ========================================================
    # H. MUESTRA ECONOMÉTRICA:
    #    SOLO CASOS COMPLETOS
    # ========================================================

    muestra = (
        seleccion.loc[
            ~mascara_incompleta,
            [
                "mes",
                "banco_id",
                "Y",
                "X1",
                "X2",
                "X3",
                "X4",
            ],
        ]
        .copy()
        .sort_values(
            [
                "banco_id",
                "mes",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # Identificador correlativo de cada observación efectiva.
    # No reemplaza la llave del panel (mes + banco_id).
    # Se asigna después del ordenamiento definitivo.
    muestra.insert(
        0,
        "id_obs",
        range(1, len(muestra) + 1),
    )

    exigir(
        muestra["id_obs"].tolist()
        ==
        list(range(1, FILAS_MUESTRA_FINAL_ESPERADAS + 1)),
        "id_obs no es una secuencia exacta de 1 a 1458.",
    )

    exigir(
        muestra["id_obs"].is_unique,
        "id_obs contiene valores duplicados.",
    )

    exigir(
        len(muestra)
        ==
        FILAS_MUESTRA_FINAL_ESPERADAS,
        "La muestra econométrica final "
        "no contiene exactamente "
        "1,458 observaciones. "
        f"Observadas: {len(muestra)}.",
    )

    duplicados_muestra = (
        contar_duplicados_llave(
            muestra
        )
    )

    exigir(
        duplicados_muestra == 0,
        "La muestra econométrica contiene "
        "duplicados mes + banco_id.",
    )

    faltantes_muestra = (
        muestra[
            VARIABLES
        ]
        .isna()
        .sum()
    )

    exigir(
        int(
            faltantes_muestra.sum()
        )
        ==
        0,
        "La muestra econométrica contiene "
        "faltantes en alguna de las "
        "cinco variables.",
    )

    exigir(
        len(muestra)
        >=
        1000,
        "La muestra econométrica "
        "no alcanza 1,000 observaciones.",
    )

    # ========================================================
    # I. ORDENAR PANEL DE TRAZABILIDAD
    # ========================================================

    columnas_panel = [
        "mes",
        "banco_id",

        "banco_original_Y",
        "banco_original_X1",

        "banco_original_X2",
        "fecha_sbs_X2",

        "banco_original_X3",
        "fecha_sbs_X3",

        "Y",
        "X1",
        "X2",
        "X3",
        "X4",

        "fila_completa_5",
    ]

    panel = (
        panel[
            columnas_panel
        ]
        .sort_values(
            [
                "banco_id",
                "mes",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # J. GUARDAR LOS TRES CSV PROCESADOS
    # ========================================================

    guardar_csv_atomico(
        panel,
        SALIDA_PANEL,
    )

    guardar_csv_atomico(
        muestra,
        SALIDA_MUESTRA,
    )

    guardar_csv_atomico(
        muestra,
        SALIDA_DATOS_PROCESADOS,
    )

    exigir(
        SALIDA_MUESTRA.read_bytes()
        ==
        SALIDA_DATOS_PROCESADOS.read_bytes(),
        "El archivo datos_procesados oficial "
        "no es idéntico a la muestra econométrica.",
    )

    # ========================================================
    # K. RESUMEN FINAL
    # ========================================================

    print()
    print("=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)

    print()
    print(
        f"Periodo: "
        f"{FECHA_INICIO} a {FECHA_CORTE}"
    )

    print(
        f"Meses: "
        f"{len(meses_comunes)}"
    )

    print()
    print(
        "PANEL INTEGRADO DE TRAZABILIDAD"
    )

    print(
        f"Filas: "
        f"{len(panel)}"
    )

    print(
        f"Duplicados mes + banco_id: "
        f"{duplicados_panel}"
    )

    print(
        "Filas con Y, X1, X2, X3 y X4 "
        "simultáneamente completas: "
        f"{filas_completas_universo}"
    )

    print()
    print(
        "MUESTRA DE 12 BANCOS"
    )

    print(
        "Bancos seleccionados: "
        f"{seleccion['banco_id'].nunique()}"
    )

    print(
        "Banco-mes potenciales: "
        f"{len(seleccion)}"
    )

    print(
        "Filas incompletas excluidas: "
        f"{numero_incompletas}"
    )

    print(
        "Observaciones econométricas finales: "
        f"{len(muestra)}"
    )

    print(
        "Duplicados mes + banco_id "
        f"en muestra: {duplicados_muestra}"
    )

    print(
        "Faltantes Y-X4 en muestra: "
        f"{int(faltantes_muestra.sum())}"
    )

    print(
        "Umbral >= 1,000 observaciones: SÍ"
    )

    print()
    print(
        "Descripción metodológica:"
    )

    print(
        "Panel de 12 bancos con cobertura "
        "2015-11 a 2025-12 y "
        "1,458 observaciones efectivas."
    )

    print(
        "La muestra econométrica NO se "
        "describe como panel balanceado."
    )

    print()
    print(
        "No se realizó interpolación, "
        "imputación ni extrapolación."
    )

    print()
    print(
        "ARCHIVO PANEL:"
    )

    print(
        SALIDA_PANEL
    )

    print()
    print(
        "ARCHIVO MUESTRA:"
    )

    print(
        SALIDA_MUESTRA
    )

    print()
    print(
        "ARCHIVO DATOS PROCESADOS OFICIAL:"
    )

    print(
        SALIDA_DATOS_PROCESADOS
    )

    print()
    print(
        "ESTADO = "
        "LIMPIEZA_DATOS_COMPLETA_VALIDADA"
    )


# ============================================================
# 23. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()
