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
DIAGNÓSTICO DE COMPLETITUD DE LA MUESTRA ECONOMÉTRICA

Este script:

1. Lee Y, X1, X2, X3 y X4.
2. Aplica la homologación bancaria ya validada.
3. Integra las cinco variables exactamente con la misma
   metodología de diagnostico_integracion_panel.py.
4. Calcula cuántas filas tienen simultáneamente:

       Y, X1, X2, X3 y X4 no faltantes.

5. Resume por banco:
       - meses presentes;
       - filas completas;
       - filas incompletas;
       - porcentaje de completitud.

6. Muestra específicamente todas las filas incompletas de:
       - alfin
       - bbva
       - bcp
       - mibanco

   indicando:
       - mes
       - variables faltantes.

7. Comprueba si la muestra completa supera 1,000 observaciones.

Este script NO:

- interpola;
- extrapola;
- rellena faltantes;
- elimina bancos;
- selecciona bancos;
- modifica los CSV fuente;
- guarda un CSV final;
- escribe 03_limpieza_datos.py.
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
# 3. HOMOLOGACIÓN BANCARIA VALIDADA
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
# 4. VARIABLES DEL MODELO
# ============================================================

VARIABLES = [
    "Y",
    "X1",
    "X2",
    "X3",
    "X4",
]

BANCOS_DIAGNOSTICO = [
    "alfin",
    "bbva",
    "bcp",
    "mibanco",
]


# ============================================================
# 5. LECTURA DE CSV BANCARIOS
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
# 6. VALIDAR FORMATO YYYY-MM
# ============================================================

def validar_mes_yyyy_mm(
    serie,
    fuente,
):

    serie = serie.astype(
        "string"
    )

    valido = serie.str.fullmatch(
        r"\d{4}-\d{2}",
        na=False,
    )

    if not valido.all():

        invalidos = (
            serie.loc[
                ~valido
            ]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{fuente}: existen meses "
            f"con formato inválido: "
            f"{invalidos}"
        )

    return serie


# ============================================================
# 7. CONVERSIÓN NUMÉRICA SIN IMPUTACIÓN
# ============================================================

def convertir_numerico_sin_rellenar(
    serie,
    fuente,
    columna,
):

    """
    Solo convierte los valores numéricos para análisis.

    Marcadores explícitos de ausencia:

        ""
        "-"
        "—"
        "–"
        "s.i."

    se convierten a pd.NA ÚNICAMENTE EN MEMORIA.

    NO se convierten a cero.
    NO se interpolan.
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
            f"{fuente}: "
            f"{columna} contiene "
            "tokens no numéricos inesperados: "
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

    necesarias = {
        "mes",
        "banco_original",
        columna_variable,
    }

    faltantes = (
        necesarias
        -
        set(df.columns)
    )

    if faltantes:

        raise ValueError(
            f"{fuente}: faltan columnas: "
            f"{sorted(faltantes)}"
        )

    trabajo = df[
        [
            "mes",
            "banco_original",
            columna_variable,
        ]
    ].copy()

    trabajo["mes"] = (
        validar_mes_yyyy_mm(
            trabajo["mes"],
            fuente,
        )
    )

    # --------------------------------------------------------
    # Homologación aprobada.
    # --------------------------------------------------------

    trabajo["banco_id"] = (
        trabajo[
            "banco_original"
        ]
        .map(
            homologacion
        )
    )

    nombres_sin_mapeo = (
        trabajo.loc[
            trabajo[
                "banco_id"
            ].isna(),
            "banco_original",
        ]
        .drop_duplicates()
        .tolist()
    )

    if nombres_sin_mapeo:

        raise ValueError(
            f"{fuente}: nombres sin homologar: "
            f"{nombres_sin_mapeo}"
        )

    # --------------------------------------------------------
    # La homologación validada debe seguir generando
    # 0 colisiones banco_id + mes.
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

        raise ValueError(
            f"{fuente}: aparecieron "
            "colisiones banco_id + mes:\n"
            f"{detalle.to_string(index=False)}"
        )

    trabajo[
        nombre_variable
    ] = convertir_numerico_sin_rellenar(
        trabajo[
            columna_variable
        ],
        fuente,
        columna_variable,
    )

    return trabajo[
        [
            "mes",
            "banco_id",
            nombre_variable,
        ]
    ].copy()


# ============================================================
# 9. FUNCIONES PARA X4
# ============================================================

def quitar_tildes(texto):

    normalizado = (
        unicodedata.normalize(
            "NFKD",
            texto,
        )
    )

    return "".join(
        caracter
        for caracter
        in normalizado
        if not unicodedata.combining(
            caracter
        )
    )


def convertir_mes_bcrp(valor):

    if pd.isna(valor):

        raise ValueError(
            "X4: Mes/Año vacío."
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
            "X4: formato mensual "
            f"no reconocido: {repr(texto)}"
        )

    mes_texto = quitar_tildes(
        coincidencia.group(1)
    ).lower()

    anio = (
        coincidencia.group(2)
    )

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
            "X4: abreviatura de mes "
            f"no reconocida: {mes_texto}"
        )

    return (
        f"{anio}-"
        f"{mapa_meses[mes_texto]}"
    )


# ============================================================
# 10. LEER X4 SIN MODIFICAR CRUDO
# ============================================================

def leer_x4_bcrp(ruta):

    if not ruta.exists():

        raise FileNotFoundError(
            f"No existe X4: {ruta}"
        )

    raw = ruta.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    # <br> se sustituye SOLO EN MEMORIA.
    texto_memoria = raw.replace(
        "<br>",
        "\n",
    )

    df = pd.read_csv(
        StringIO(
            texto_memoria
        )
    )

    df.columns = [
        unescape(
            str(columna)
        ).strip()
        for columna
        in df.columns
    ]

    if len(df.columns) != 2:

        raise ValueError(
            "X4: se esperaban "
            "exactamente 2 columnas."
        )

    columna_mes = (
        df.columns[0]
    )

    columna_valor = (
        df.columns[1]
    )

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
        convertir_numerico_sin_rellenar(
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

        raise ValueError(
            "X4 contiene meses duplicados."
        )

    return trabajo[
        [
            "mes",
            "X4",
        ]
    ].copy()


# ============================================================
# 11. OBTENER PERIODO COMÚN
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
            "No existe periodo común."
        )

    return sorted(
        comunes
    )


# ============================================================
# 12. MAIN
# ============================================================

def main():

    # ========================================================
    # LECTURA
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
    # PREPARACIÓN EN MEMORIA
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
    # PERIODO COMÚN
    # ========================================================

    meses_comunes = (
        obtener_meses_comunes(
            y=y,
            x1=x1,
            x2=x2,
            x3=x3,
            x4=x4,
        )
    )

    inicio = (
        meses_comunes[0]
    )

    fin = (
        meses_comunes[-1]
    )

    total_meses_periodo = (
        len(meses_comunes)
    )

    # Filtrar únicamente al periodo común.
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
    # INTEGRACIÓN EXACTA DEL DIAGNÓSTICO ANTERIOR
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

    # ========================================================
    # CONTROL DUPLICADOS DEL PANEL
    # ========================================================

    duplicados = (
        panel.duplicated(
            subset=[
                "mes",
                "banco_id",
            ],
            keep=False,
        )
    )

    if duplicados.any():

        raise RuntimeError(
            "El panel integrado contiene "
            "duplicados mes + banco_id."
        )

    # ========================================================
    # DEFINIR FILA COMPLETA
    # ========================================================

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

    # ========================================================
    # 1. NÚMERO EXACTO DE FILAS COMPLETAS
    # ========================================================

    total_filas_panel = (
        len(panel)
    )

    total_filas_completas = int(
        panel[
            "fila_completa_5"
        ].sum()
    )

    total_filas_incompletas = (
        total_filas_panel
        -
        total_filas_completas
    )

    print()
    print("=" * 100)
    print("COMPLETITUD GLOBAL DE LA MUESTRA")
    print("=" * 100)

    print(
        f"Periodo común: "
        f"{inicio} a {fin}"
    )

    print(
        f"Meses del periodo común: "
        f"{total_meses_periodo}"
    )

    print(
        f"Filas totales del panel: "
        f"{total_filas_panel}"
    )

    print(
        "Filas con Y, X1, X2, X3 y X4 "
        "simultáneamente no faltantes: "
        f"{total_filas_completas}"
    )

    print(
        f"Filas incompletas: "
        f"{total_filas_incompletas}"
    )

    # ========================================================
    # 2. RESUMEN POR BANCO
    # ========================================================

    resumen_bancos = (
        panel
        .groupby(
            "banco_id",
            sort=True,
        )
        .agg(
            meses_presentes=(
                "mes",
                "nunique",
            ),
            filas_completas_5=(
                "fila_completa_5",
                "sum",
            ),
            filas_totales=(
                "mes",
                "size",
            ),
        )
        .reset_index()
    )

    resumen_bancos[
        "filas_completas_5"
    ] = (
        resumen_bancos[
            "filas_completas_5"
        ]
        .astype(int)
    )

    resumen_bancos[
        "filas_incompletas"
    ] = (
        resumen_bancos[
            "filas_totales"
        ]
        -
        resumen_bancos[
            "filas_completas_5"
        ]
    )

    resumen_bancos[
        "porcentaje_completitud"
    ] = (
        resumen_bancos[
            "filas_completas_5"
        ]
        /
        resumen_bancos[
            "filas_totales"
        ]
        *
        100
    )

    resumen_bancos[
        "porcentaje_completitud"
    ] = (
        resumen_bancos[
            "porcentaje_completitud"
        ]
        .round(2)
    )

    resumen_bancos = (
        resumen_bancos[
            [
                "banco_id",
                "meses_presentes",
                "filas_completas_5",
                "filas_incompletas",
                "porcentaje_completitud",
            ]
        ]
    )

    print()
    print("=" * 100)
    print("COMPLETITUD POR BANCO")
    print("=" * 100)

    print(
        resumen_bancos.to_string(
            index=False
        )
    )

    # ========================================================
    # 3. FILAS INCOMPLETAS DE BANCOS ESPECÍFICOS
    # ========================================================

    print()
    print("=" * 100)
    print(
        "FILAS INCOMPLETAS DE "
        "ALFIN, BBVA, BCP Y MIBANCO"
    )
    print("=" * 100)

    for banco in BANCOS_DIAGNOSTICO:

        sub = (
            panel.loc[
                panel[
                    "banco_id"
                ].eq(
                    banco
                )
                &
                ~panel[
                    "fila_completa_5"
                ],
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
                "mes"
            )
        )

        print()
        print("-" * 100)
        print(
            f"BANCO: {banco}"
        )
        print("-" * 100)

        if sub.empty:

            print(
                "No tiene filas incompletas."
            )

            continue

        # ----------------------------------------------------
        # Identificar exactamente qué variables faltan.
        # ----------------------------------------------------

        sub[
            "variables_faltantes"
        ] = (
            sub[
                VARIABLES
            ]
            .apply(
                lambda fila:
                ", ".join(
                    variable
                    for variable
                    in VARIABLES
                    if pd.isna(
                        fila[
                            variable
                        ]
                    )
                ),
                axis=1,
            )
        )

        print(
            sub[
                [
                    "mes",
                    "variables_faltantes",
                ]
            ]
            .to_string(
                index=False
            )
        )

        print()
        print(
            "Número de filas incompletas: "
            f"{len(sub)}"
        )

    # ========================================================
    # 4. COMPROBACIÓN DEL UMBRAL DE 1,000
    # ========================================================

    print()
    print("=" * 100)
    print("CONTROL DEL UMBRAL DE 1,000 OBSERVACIONES")
    print("=" * 100)

    print(
        "Observaciones completas disponibles: "
        f"{total_filas_completas}"
    )

    if total_filas_completas >= 1000:

        print(
            "SUPERA O IGUALA 1,000: SÍ"
        )

        print(
            "ESTADO = "
            "MUESTRA_COMPLETA_CUMPLE_UMBRAL_1000"
        )

    else:

        faltan = (
            1000
            -
            total_filas_completas
        )

        print(
            "SUPERA O IGUALA 1,000: NO"
        )

        print(
            "Observaciones completas adicionales "
            f"necesarias para llegar a 1,000: {faltan}"
        )

        print(
            "ESTADO = "
            "MUESTRA_COMPLETA_NO_CUMPLE_UMBRAL_1000"
        )


# ============================================================
# 13. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()