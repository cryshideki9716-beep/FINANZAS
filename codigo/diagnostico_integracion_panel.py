# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de diagnóstico: 2026-09-24

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
DIAGNÓSTICO PREVIO A 03_limpieza_datos.py

Este script:

1. Lee Y, X1, X2, X3 y X4.
2. Aplica EN MEMORIA la tabla de homologación bancaria
   previamente validada.
3. NO modifica ningún CSV.
4. NO escribe ningún archivo nuevo.
5. NO interpola.
6. NO extrapola.
7. NO rellena faltantes.
8. NO elimina bancos.
9. NO selecciona bancos.
10. NO construye todavía la base final.
11. NO escribe 03_limpieza_datos.py.

La integración bancaria se realiza mediante:

    mes + banco_id

Y X4 (inflación) se incorpora únicamente mediante:

    mes

Para no perder observaciones bancarias, Y, X1, X2 y X3
se unen con OUTER JOIN.

X4 se incorpora después mediante LEFT JOIN sobre el panel
bancario resultante.

El diagnóstico muestra ÚNICAMENTE:

1. Dimensiones de cada fuente antes del merge.
2. Periodo común.
3. Número de filas del panel combinado.
4. Duplicados mes + banco_id.
5. Faltantes por cada una de las 5 variables.
6. Faltantes por banco.
7. Cantidad de meses por banco.
8. Bancos con las 5 variables completas durante TODO
   el periodo común.
"""


# ============================================================
# 2. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

RUTA_Y = (
    RAIZ
    / "datos_procesados"
    / "Y_dolarizacion_credito_2024200485D.csv"
)

RUTA_X1 = (
    RAIZ
    / "datos_procesados"
    / "X1_dolarizacion_depositos_2024200485D.csv"
)

RUTA_X2 = (
    RAIZ
    / "datos_procesados"
    / "X2_tasa_activa_consumo_mn_2024200485D.csv"
)

RUTA_X3 = (
    RAIZ
    / "datos_procesados"
    / "X3_tasa_pasiva_ahorro_mn_2024200485D.csv"
)

RUTA_X4 = (
    RAIZ
    / "datos_crudos"
    / "bcrp_inflacion.csv"
)


# ============================================================
# 3. TABLA DE HOMOLOGACIÓN APROBADA
# ============================================================

HOMOLOGACION_Y = {

    "Banco Azteca": "alfin",
    "Alfin Banco1/": "alfin",
    "Alfin Banco": "alfin",

    "Banco Continental": "bbva",
    "Banco BBVA Perú*": "bbva",
    "Banco BBVA Perú": "bbva",

    "Banco BCI Perú**": "bci",
    "Banco BCI Perú": "bci",

    "Banco Interamericano de Finanzas": "bif",
    "Banco Interamericano de Finanzas*": "bif",

    "Banco de Comercio": "bancom",
    "BANCOM": "bancom",

    "Bank of China*": "bank_of_china",
    "Bank of China": "bank_of_china",

    "B. Cencosud": "cencosud_cat",

    "Citibank": "citibank",

    "Compartamos Banco*": "compartamos",
    "Compartamos Banco": "compartamos",

    "Banco de Crédito del Perú": "bcp",

    "Deutsche Bank": "deutsche",

    "Banco Falabella Perú": "falabella",

    "Banco GNB": "gnb",

    "B. ICBC": "icbc",

    "Interbank": "interbank",
    "Interbank **": "interbank",

    "Mibanco": "mibanco",

    "Banco Financiero": "pichincha",
    "Banco Pichincha": "pichincha",
    "Banco Pichincha*": "pichincha",
    "Banco Pichincha *": "pichincha",

    "Banco Ripley": "ripley",

    "Santander Perú S.A.": "santander_peru",

    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

    "Scotiabank Perú": "scotiabank",
}


HOMOLOGACION_X1 = {

    "B. Azteca Perú": "alfin",
    "Alfin Banco 1/": "alfin",
    "Alfin Banco": "alfin",

    "B. Continental": "bbva",
    "B. BBVA Perú*": "bbva",
    "B. BBVA Perú": "bbva",

    "Banco BCI Perú*": "bci",
    "Banco BCI Perú": "bci",

    "B. Interamericano de Finanzas": "bif",

    "B. de Comercio": "bancom",
    "BANCOM": "bancom",

    "Bank of China*": "bank_of_china",
    "Bank of China": "bank_of_china",

    "B. Cencosud": "cencosud_cat",

    "Citibank": "citibank",

    "Compartamos Banco": "compartamos",

    "B. de Crédito del Perú (con sucursales en el exterior)": "bcp",

    "Deutsche Bank Perú": "deutsche",

    "B. Falabella Perú .": "falabella",

    "B. Financiero": "pichincha",
    "B. Pichincha*": "pichincha",
    "B. Pichincha": "pichincha",

    "B. GNB": "gnb",

    "B. ICBC": "icbc",

    "Interbank": "interbank",
    "Interbank (con sucursales en el exterior)": "interbank",

    "Mibanco": "mibanco",

    "B. Ripley": "ripley",

    "B. Santander Perú": "santander_peru",

    "Santander Consumer Bank*": "santander_consumer",
    "Santander Consumer Bank": "santander_consumer",

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


# ============================================================
# 4. VARIABLES FINALES DEL DIAGNÓSTICO
# ============================================================

VARIABLES = [
    "Y",
    "X1",
    "X2",
    "X3",
    "X4",
]


# ============================================================
# 5. LECTURA DE FUENTES BANCARIAS
# ============================================================

def leer_csv_bancario(ruta):

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {ruta}"
        )

    return pd.read_csv(
        ruta,
        encoding="utf-8-sig",
    )


# ============================================================
# 6. VALIDAR MES YYYY-MM
# ============================================================

def validar_mes_yyyy_mm(serie, fuente):

    serie = serie.astype("string")

    patron_valido = serie.str.fullmatch(
        r"\d{4}-\d{2}",
        na=False,
    )

    if not patron_valido.all():

        valores_invalidos = (
            serie.loc[
                ~patron_valido
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{fuente}: existen valores de mes "
            f"que no tienen formato YYYY-MM: "
            f"{valores_invalidos}"
        )

    return serie


# ============================================================
# 7. CONVERTIR VARIABLE NUMÉRICA SIN RELLENAR
# ============================================================

def convertir_numerico_sin_rellenar(
    serie,
    fuente,
    columna,
):
    """
    Convierte únicamente para poder diagnosticar faltantes.

    NO interpola.
    NO rellena.
    NO imputa.

    Marcadores explícitos de ausencia como:
        ""
        "-"
        "—"
        "–"

    se interpretan EN MEMORIA como pd.NA.

    Si aparece un texto no vacío que tampoco es numérico,
    el diagnóstico se detiene en vez de convertirlo
    silenciosamente en faltante.
    """

    texto = serie.astype("string")

    texto = texto.str.strip()

    marcadores_faltante = {
        "",
        "-",
        "—",
        "–",
        "s.i.",
    }

    es_faltante_explicito = (
        texto.isna()
        |
        texto.isin(
            marcadores_faltante
        )
    )

    para_convertir = (
        texto
        .mask(
            es_faltante_explicito,
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

    invalido = (
        ~es_faltante_explicito
        &
        numerico.isna()
    )

    if invalido.any():

        valores_invalidos = (
            texto.loc[
                invalido
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{fuente}: la columna {columna} "
            "contiene valores no numéricos "
            "que no son marcadores de faltante: "
            f"{valores_invalidos}"
        )

    return numerico


# ============================================================
# 8. PREPARAR FUENTE BANCARIA
# ============================================================

def preparar_fuente_bancaria(
    df,
    fuente,
    homologacion,
    columna_variable,
    nombre_variable,
):

    columnas_necesarias = {
        "mes",
        "banco_original",
        columna_variable,
    }

    faltan_columnas = (
        columnas_necesarias
        -
        set(df.columns)
    )

    if faltan_columnas:

        raise ValueError(
            f"{fuente}: faltan columnas requeridas: "
            f"{sorted(faltan_columnas)}"
        )

    trabajo = df[
        [
            "mes",
            "banco_original",
            columna_variable,
        ]
    ].copy()

    trabajo["mes"] = validar_mes_yyyy_mm(
        trabajo["mes"],
        fuente,
    )

    # --------------------------------------------------------
    # Homologación aprobada.
    # Solo se aplica en memoria.
    # --------------------------------------------------------

    trabajo["banco_id"] = (
        trabajo["banco_original"]
        .map(
            homologacion
        )
    )

    sin_mapeo = (
        trabajo.loc[
            trabajo["banco_id"].isna(),
            "banco_original",
        ]
        .drop_duplicates()
        .tolist()
    )

    if sin_mapeo:

        raise ValueError(
            f"{fuente}: existen nombres sin homologar: "
            f"{sin_mapeo}"
        )

    # --------------------------------------------------------
    # Control de duplicados previamente validado.
    # Se vuelve a exigir para proteger este diagnóstico.
    # --------------------------------------------------------

    duplicados = trabajo.duplicated(
        subset=[
            "mes",
            "banco_id",
        ],
        keep=False,
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

        raise ValueError(
            f"{fuente}: se detectaron colisiones "
            "mes + banco_id antes del merge:\n"
            f"{detalle.to_string(index=False)}"
        )

    trabajo[nombre_variable] = (
        convertir_numerico_sin_rellenar(
            trabajo[
                columna_variable
            ],
            fuente,
            columna_variable,
        )
    )

    return trabajo[
        [
            "mes",
            "banco_id",
            nombre_variable,
        ]
    ].copy()


# ============================================================
# 9. NORMALIZAR TEXTO DE MES BCRP
# ============================================================

def quitar_tildes(texto):

    normalizado = unicodedata.normalize(
        "NFKD",
        texto,
    )

    return "".join(
        caracter
        for caracter in normalizado
        if not unicodedata.combining(
            caracter
        )
    )


# ============================================================
# 10. CONVERTIR Mes/Año BCRP -> YYYY-MM
# ============================================================

def convertir_mes_bcrp(valor):

    if pd.isna(valor):
        raise ValueError(
            "X4: se encontró un Mes/Año vacío."
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
            "X4: formato de mes no reconocido: "
            f"{repr(texto)}"
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
            "X4: abreviatura mensual no reconocida: "
            f"{repr(mes_texto)}"
        )

    return (
        f"{anio}-"
        f"{mapa_meses[mes_texto]}"
    )


# ============================================================
# 11. LEER X4 BCRP DESDE EL CRUDO ORIGINAL
# ============================================================

def leer_x4_bcrp(ruta):

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo X4: {ruta}"
        )

    # --------------------------------------------------------
    # El archivo crudo NO se modifica.
    # <br> se sustituye únicamente en memoria.
    # --------------------------------------------------------

    raw = ruta.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    texto_memoria = raw.replace(
        "<br>",
        "\n",
    )

    df = pd.read_csv(
        StringIO(
            texto_memoria
        )
    )

    # --------------------------------------------------------
    # Decodificar entidades HTML SOLO en nombres de columnas.
    # Ejemplo:
    # Mes/A&ntilde;o -> Mes/Año
    # --------------------------------------------------------

    df.columns = [
        unescape(
            str(columna)
        ).strip()
        for columna in df.columns
    ]

    if len(df.columns) != 2:

        raise ValueError(
            "X4: se esperaban exactamente 2 columnas, "
            f"pero se encontraron {len(df.columns)}: "
            f"{df.columns.tolist()}"
        )

    columna_mes = df.columns[0]
    columna_valor = df.columns[1]

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
        .astype("string")
    )

    trabajo["X4"] = (
        convertir_numerico_sin_rellenar(
            trabajo[
                columna_valor
            ],
            "X4",
            columna_valor,
        )
    )

    # Un mes debe aparecer una sola vez en inflación.
    duplicados_mes = trabajo.duplicated(
        subset=["mes"],
        keep=False,
    )

    if duplicados_mes.any():

        detalle = (
            trabajo.loc[
                duplicados_mes,
                [
                    "mes",
                    columna_mes,
                    columna_valor,
                ],
            ]
            .sort_values(
                "mes"
            )
        )

        raise ValueError(
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
# 12. CALCULAR PERIODO COMÚN
# ============================================================

def obtener_meses_comunes(
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

    comunes = set.intersection(
        *conjuntos
    )

    if not comunes:

        raise ValueError(
            "No existe ningún mes común "
            "entre las cinco fuentes."
        )

    meses_comunes = sorted(
        comunes
    )

    return meses_comunes


# ============================================================
# 13. COMPROBAR CONTINUIDAD DEL PERIODO
# ============================================================

def periodo_es_continuo(
    meses_comunes,
):

    inicio = pd.Period(
        meses_comunes[0],
        freq="M",
    )

    fin = pd.Period(
        meses_comunes[-1],
        freq="M",
    )

    secuencia = [
        str(periodo)
        for periodo
        in pd.period_range(
            inicio,
            fin,
            freq="M",
        )
    ]

    return (
        meses_comunes
        ==
        secuencia
    )


# ============================================================
# 14. MAIN
# ============================================================

def main():

    # ========================================================
    # LECTURA ORIGINAL
    # ========================================================

    y_raw = leer_csv_bancario(
        RUTA_Y
    )

    x1_raw = leer_csv_bancario(
        RUTA_X1
    )

    x2_raw = leer_csv_bancario(
        RUTA_X2
    )

    x3_raw = leer_csv_bancario(
        RUTA_X3
    )

    x4 = leer_x4_bcrp(
        RUTA_X4
    )

    # ========================================================
    # 1. DIMENSIONES ANTES DEL MERGE
    # ========================================================

    print()
    print("=" * 90)
    print("1. DIMENSIONES DE CADA FUENTE ANTES DEL MERGE")
    print("=" * 90)

    dimensiones = pd.DataFrame(
        [
            {
                "fuente": "Y",
                "filas": y_raw.shape[0],
                "columnas": y_raw.shape[1],
            },
            {
                "fuente": "X1",
                "filas": x1_raw.shape[0],
                "columnas": x1_raw.shape[1],
            },
            {
                "fuente": "X2",
                "filas": x2_raw.shape[0],
                "columnas": x2_raw.shape[1],
            },
            {
                "fuente": "X3",
                "filas": x3_raw.shape[0],
                "columnas": x3_raw.shape[1],
            },
            {
                "fuente": "X4",
                "filas": x4.shape[0],
                "columnas": 2,
            },
        ]
    )

    print(
        dimensiones.to_string(
            index=False
        )
    )

    # ========================================================
    # HOMOLOGACIÓN Y VARIABLES EN MEMORIA
    # ========================================================

    y = preparar_fuente_bancaria(
        df=y_raw,
        fuente="Y",
        homologacion=HOMOLOGACION_Y,
        columna_variable="dolcred_pct",
        nombre_variable="Y",
    )

    x1 = preparar_fuente_bancaria(
        df=x1_raw,
        fuente="X1",
        homologacion=HOMOLOGACION_X1,
        columna_variable="doldep_pct",
        nombre_variable="X1",
    )

    x2 = preparar_fuente_bancaria(
        df=x2_raw,
        fuente="X2",
        homologacion=HOMOLOGACION_X2,
        columna_variable=(
            "tasa_activa_consumo_mn"
        ),
        nombre_variable="X2",
    )

    x3 = preparar_fuente_bancaria(
        df=x3_raw,
        fuente="X3",
        homologacion=HOMOLOGACION_X3,
        columna_variable=(
            "tasa_pasiva_ahorro_mn"
        ),
        nombre_variable="X3",
    )

    # ========================================================
    # 2. PERIODO COMÚN
    # ========================================================

    meses_comunes = obtener_meses_comunes(
        y=y,
        x1=x1,
        x2=x2,
        x3=x3,
        x4=x4,
    )

    inicio_comun = meses_comunes[0]
    fin_comun = meses_comunes[-1]

    continuo = periodo_es_continuo(
        meses_comunes
    )

    print()
    print("=" * 90)
    print("2. PERIODO COMÚN")
    print("=" * 90)

    print(
        f"Inicio: {inicio_comun}"
    )

    print(
        f"Fin: {fin_comun}"
    )

    print(
        f"Cantidad de meses comunes: "
        f"{len(meses_comunes)}"
    )

    print(
        "Periodo mensual continuo: "
        f"{continuo}"
    )

    # ========================================================
    # FILTRAR ÚNICAMENTE AL PERIODO COMÚN
    # ========================================================

    y = y.loc[
        y["mes"].isin(
            meses_comunes
        )
    ].copy()

    x1 = x1.loc[
        x1["mes"].isin(
            meses_comunes
        )
    ].copy()

    x2 = x2.loc[
        x2["mes"].isin(
            meses_comunes
        )
    ].copy()

    x3 = x3.loc[
        x3["mes"].isin(
            meses_comunes
        )
    ].copy()

    x4 = x4.loc[
        x4["mes"].isin(
            meses_comunes
        )
    ].copy()

    # ========================================================
    # MERGE OUTER DE LAS CUATRO FUENTES BANCARIAS
    # ========================================================

    panel = y.merge(
        x1,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    panel = panel.merge(
        x2,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    panel = panel.merge(
        x3,
        on=[
            "mes",
            "banco_id",
        ],
        how="outer",
        validate="one_to_one",
    )

    # ========================================================
    # INCORPORAR X4 POR MES
    # ========================================================

    panel = panel.merge(
        x4,
        on="mes",
        how="left",
        validate="many_to_one",
    )

    panel = panel.sort_values(
        [
            "banco_id",
            "mes",
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # 3. NÚMERO DE FILAS DEL PANEL COMBINADO
    # ========================================================

    print()
    print("=" * 90)
    print("3. NÚMERO DE FILAS DEL PANEL COMBINADO")
    print("=" * 90)

    print(
        f"Filas: {len(panel)}"
    )

    print(
        f"Bancos distintos: "
        f"{panel['banco_id'].nunique()}"
    )

    # ========================================================
    # 4. DUPLICADOS mes + banco_id
    # ========================================================

    mascara_duplicados = (
        panel.duplicated(
            subset=[
                "mes",
                "banco_id",
            ],
            keep=False,
        )
    )

    numero_filas_duplicadas = int(
        mascara_duplicados.sum()
    )

    print()
    print("=" * 90)
    print("4. DUPLICADOS mes + banco_id")
    print("=" * 90)

    print(
        f"Filas duplicadas: "
        f"{numero_filas_duplicadas}"
    )

    if numero_filas_duplicadas > 0:

        print()

        print(
            panel.loc[
                mascara_duplicados,
                [
                    "mes",
                    "banco_id",
                ],
            ]
            .sort_values(
                [
                    "mes",
                    "banco_id",
                ]
            )
            .to_string(
                index=False
            )
        )

    # ========================================================
    # 5. FALTANTES POR VARIABLE
    # ========================================================

    faltantes_variables = (
        panel[
            VARIABLES
        ]
        .isna()
        .sum()
        .rename(
            "faltantes"
        )
        .reset_index()
        .rename(
            columns={
                "index": "variable"
            }
        )
    )

    print()
    print("=" * 90)
    print("5. FALTANTES POR CADA UNA DE LAS 5 VARIABLES")
    print("=" * 90)

    print(
        faltantes_variables.to_string(
            index=False
        )
    )

    # ========================================================
    # 6. FALTANTES POR BANCO
    # ========================================================

    faltantes_banco = (
        panel
        .groupby(
            "banco_id",
            sort=True,
        )[VARIABLES]
        .apply(
            lambda grupo:
            grupo.isna().sum()
        )
    )

    faltantes_banco[
        "faltantes_total"
    ] = (
        faltantes_banco[
            VARIABLES
        ]
        .sum(
            axis=1
        )
    )

    faltantes_banco = (
        faltantes_banco
        .reset_index()
    )

    print()
    print("=" * 90)
    print("6. FALTANTES POR BANCO")
    print("=" * 90)

    print(
        faltantes_banco.to_string(
            index=False
        )
    )

    # ========================================================
    # 7. CANTIDAD DE MESES POR BANCO
    # ========================================================

    meses_por_banco = (
        panel
        .groupby(
            "banco_id",
            sort=True,
        )
        .agg(
            cantidad_meses=(
                "mes",
                "nunique",
            )
        )
        .reset_index()
    )

    print()
    print("=" * 90)
    print("7. CANTIDAD DE MESES POR BANCO")
    print("=" * 90)

    print(
        meses_por_banco.to_string(
            index=False
        )
    )

    # ========================================================
    # 8. BANCOS CON LAS 5 VARIABLES COMPLETAS
    # ========================================================

    """
    Criterio:

    Un banco se considera completamente observado
    únicamente si:

    A) aparece en TODOS los meses del periodo común; y

    B) no tiene ningún faltante en Y, X1, X2, X3 o X4
       durante esos meses.

    Esto NO elimina ni selecciona bancos.
    Solo los identifica descriptivamente.
    """

    resumen_completitud = (
        panel
        .groupby(
            "banco_id",
            sort=True,
        )
        .agg(
            cantidad_meses=(
                "mes",
                "nunique",
            ),
            filas_completas_5=(
                "mes",
                lambda serie: 0,
            ),
        )
        .reset_index()
    )

    # Calcular filas completas de las cinco variables.
    filas_completas = (
        panel[
            VARIABLES
        ]
        .notna()
        .all(
            axis=1
        )
    )

    conteo_filas_completas = (
        panel
        .assign(
            fila_completa_5=filas_completas
        )
        .groupby(
            "banco_id",
            sort=True,
        )[
            "fila_completa_5"
        ]
        .sum()
    )

    resumen_completitud[
        "filas_completas_5"
    ] = (
        resumen_completitud[
            "banco_id"
        ]
        .map(
            conteo_filas_completas
        )
        .astype(int)
    )

    total_meses_comunes = len(
        meses_comunes
    )

    bancos_completos = (
        resumen_completitud.loc[
            (
                resumen_completitud[
                    "cantidad_meses"
                ]
                ==
                total_meses_comunes
            )
            &
            (
                resumen_completitud[
                    "filas_completas_5"
                ]
                ==
                total_meses_comunes
            )
        ]
        .copy()
    )

    print()
    print("=" * 90)
    print("8. BANCOS CON LAS 5 VARIABLES COMPLETAS")
    print("=" * 90)

    print(
        "Criterio: presencia en todos los meses comunes "
        "y 0 faltantes en Y, X1, X2, X3 y X4."
    )

    print()

    print(
        f"Cantidad de bancos completos: "
        f"{len(bancos_completos)}"
    )

    if bancos_completos.empty:

        print(
            "Ningún banco cumple el criterio."
        )

    else:

        print()

        print(
            bancos_completos[
                [
                    "banco_id",
                    "cantidad_meses",
                    "filas_completas_5",
                ]
            ]
            .to_string(
                index=False
            )
        )

    # ========================================================
    # CONTROL FINAL INTERNO
    # ========================================================

    if numero_filas_duplicadas != 0:

        raise RuntimeError(
            "El panel combinado contiene duplicados "
            "por mes + banco_id."
        )


# ============================================================
# 15. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()