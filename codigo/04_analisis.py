# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import scipy
from scipy.stats import norm

import statsmodels
import statsmodels.api as sm

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor,
)

from statsmodels.stats.diagnostic import (
    het_breuschpagan,
)

import linearmodels
from linearmodels.panel import PanelOLS


# ============================================================
# 1. OBJETIVO
# ============================================================

"""
04_analisis.py

FINANZAS I - UNIDAD I

Tema 4:
Dolarización del crédito y de los depósitos
en el sistema financiero peruano.

OBJETIVO EMPÍRICO:

Analizar la relación entre:

Y  = dolarización del crédito (%)
X1 = dolarización de depósitos (%)
X2 = tasa activa de consumo MN (%)
X3 = tasa pasiva de ahorro MN (%)
X4 = inflación mensual (%)

para una muestra de 12 bancos del sistema financiero
peruano durante 2015-11 a 2025-12.

IMPORTANTE:

- El análisis identifica asociaciones estadísticas.
- NO se realizan afirmaciones causales.
- NO se modifica la base procesada.
- NO se interpola.
- NO se imputa.
- NO se extrapola.
- NO se incorporan efectos fijos completos por mes.

MODELOS:

1. OLS agrupado de referencia:
       HC3
       use_t=True

2. Modelo principal:
       Efectos fijos por banco
       Driscoll-Kraay
       kernel Bartlett
       bandwidth = 4

DIAGNÓSTICOS:

- VIF.
- Breusch-Pagan / Koenker studentizado.
- Wooldridge-Drukker para autocorrelación
  de primer orden en panel.
- Pesaran CD para dependencia transversal.
- F de poolability de los efectos bancarios.

Los diagnósticos NO se utilizan para escoger
posteriormente la covarianza del modelo principal.
Driscoll-Kraay está predefinido ex ante.
"""


# ============================================================
# 2. PARÁMETROS GENERALES
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

FECHA_INICIO = "2015-11"
FECHA_CORTE = "2025-12"

N_ESPERADO = 1458
BANCOS_ESPERADOS = 12
MESES_ESPERADOS = 122

ALPHA = 0.05

DK_KERNEL = "bartlett"
DK_BANDWIDTH = 4


VARIABLES = [
    "Y",
    "X1",
    "X2",
    "X3",
    "X4",
]

EXPLICATIVAS = [
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


ETIQUETAS_VARIABLES = {
    "Y": "Dolarización del crédito (%)",
    "X1": "Dolarización de depósitos (%)",
    "X2": "Tasa activa de consumo MN (%)",
    "X3": "Tasa pasiva de ahorro MN (%)",
    "X4": "Inflación mensual (%)",
}


# ============================================================
# 3. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

RUTA_BASE = (
    RAIZ
    / "datos_procesados"
    / f"datos_procesados_{CODIGO_ESTUDIANTE}.csv"
)

CARPETA_SALIDAS = (
    RAIZ
    / "salidas"
)

CARPETA_SALIDAS.mkdir(
    parents=True,
    exist_ok=True,
)


# ------------------------------------------------------------
# Tablas
# ------------------------------------------------------------

TABLA_01 = (
    CARPETA_SALIDAS
    / "tabla_01_estructura_muestra"
)

TABLA_02 = (
    CARPETA_SALIDAS
    / "tabla_02_estadisticos_descriptivos"
)

TABLA_03 = (
    CARPETA_SALIDAS
    / "tabla_03_descriptivos_por_banco"
)

TABLA_04 = (
    CARPETA_SALIDAS
    / "tabla_04_correlaciones_pearson"
)

TABLA_05 = (
    CARPETA_SALIDAS
    / "tabla_05_ols_agrupado"
)

TABLA_06 = (
    CARPETA_SALIDAS
    / "tabla_06_efectos_fijos_banco"
)

TABLA_07 = (
    CARPETA_SALIDAS
    / "tabla_07_diagnosticos"
)


# ------------------------------------------------------------
# Figuras
# ------------------------------------------------------------

FIGURA_01 = (
    CARPETA_SALIDAS
    / "figura_01_dolarizacion_credito_depositos.png"
)

FIGURA_02 = (
    CARPETA_SALIDAS
    / "figura_02_tasas_activa_pasiva.png"
)

FIGURA_03 = (
    CARPETA_SALIDAS
    / "figura_03_inflacion_mensual.png"
)

FIGURA_04 = (
    CARPETA_SALIDAS
    / "figura_04_dispersion_Y_X1.png"
)


# ------------------------------------------------------------
# Resumen
# ------------------------------------------------------------

RUTA_RESUMEN = (
    CARPETA_SALIDAS
    / "resumen_04_analisis.txt"
)


# ============================================================
# 4. CONTROL GENERAL
# ============================================================

def exigir(condicion, mensaje):

    if not condicion:

        raise RuntimeError(
            mensaje
        )


# ============================================================
# 5. GUARDAR TABLA CSV + LATEX
# ============================================================

def guardar_tabla(
    df,
    ruta_base,
    caption,
    label,
    index=False,
):

    ruta_csv = ruta_base.with_suffix(
        ".csv"
    )

    ruta_tex = ruta_base.with_suffix(
        ".tex"
    )

    df.to_csv(
        ruta_csv,
        index=index,
        encoding="utf-8-sig",
    )

    texto_latex = df.to_latex(
        index=index,
        escape=True,
        na_rep="",
        float_format=lambda x: f"{x:.4f}",
        caption=caption,
        label=label,
    )

    ruta_tex.write_text(
        texto_latex,
        encoding="utf-8",
    )


# ============================================================
# 6. LECTURA Y VALIDACIÓN DE LA BASE
# ============================================================

def leer_y_validar_base():

    if not RUTA_BASE.exists():

        raise FileNotFoundError(
            "No existe la base procesada oficial:\n"
            f"{RUTA_BASE}"
        )

    df = pd.read_csv(
        RUTA_BASE,
        encoding="utf-8-sig",
        dtype={
            "mes": "string",
            "banco_id": "string",
        },
    )

    columnas_esperadas = [
        "id_obs",
        "mes",
        "banco_id",
        "Y",
        "X1",
        "X2",
        "X3",
        "X4",
    ]

    exigir(
        df.columns.tolist()
        ==
        columnas_esperadas,
        "Las columnas de la base procesada "
        "no coinciden exactamente con las esperadas.\n"
        f"Esperadas: {columnas_esperadas}\n"
        f"Observadas: {df.columns.tolist()}",
    )

    # --------------------------------------------------------
    # Identificador correlativo de observación
    # --------------------------------------------------------

    exigir(
        df["id_obs"].notna().all(),
        "id_obs contiene valores faltantes.",
    )

    exigir(
        df["id_obs"].is_unique,
        "id_obs contiene valores duplicados.",
    )

    exigir(
        df["id_obs"].tolist() == list(range(1, N_ESPERADO + 1)),
        "id_obs debe ser la secuencia exacta 1, 2, ..., 1458.",
    )

    # --------------------------------------------------------
    # Mes
    # --------------------------------------------------------

    patron_mes = (
        df["mes"]
        .str.fullmatch(
            r"\d{4}-\d{2}",
            na=False,
        )
    )

    exigir(
        patron_mes.all(),
        "La columna mes contiene formatos "
        "distintos de YYYY-MM.",
    )

    # Convertir a fecha únicamente para análisis.
    df["fecha"] = pd.to_datetime(
        df["mes"] + "-01",
        format="%Y-%m-%d",
        errors="raise",
    )

    # Índice mensual numérico.
    # Facilita comprobar consecutividad real.
    df["periodo_num"] = (
        df["fecha"].dt.year
        *
        12
        +
        df["fecha"].dt.month
    )

    # --------------------------------------------------------
    # Variables numéricas
    # --------------------------------------------------------

    for variable in VARIABLES:

        df[variable] = pd.to_numeric(
            df[variable],
            errors="raise",
        )

    # --------------------------------------------------------
    # Controles de integridad
    # --------------------------------------------------------

    exigir(
        len(df)
        ==
        N_ESPERADO,
        "La base no contiene exactamente "
        f"{N_ESPERADO} observaciones. "
        f"Observadas: {len(df)}.",
    )

    exigir(
        df["banco_id"].nunique()
        ==
        BANCOS_ESPERADOS,
        "La base no contiene exactamente "
        f"{BANCOS_ESPERADOS} bancos.",
    )

    exigir(
        set(df["banco_id"])
        ==
        set(BANCOS_MUESTRA),
        "Los banco_id observados no coinciden "
        "con los 12 bancos aprobados.",
    )

    meses_esperados = [
        str(periodo)
        for periodo
        in pd.period_range(
            FECHA_INICIO,
            FECHA_CORTE,
            freq="M",
        )
    ]

    meses_observados = sorted(
        df["mes"]
        .unique()
        .tolist()
    )

    exigir(
        meses_observados
        ==
        meses_esperados,
        "La cobertura mensual no coincide "
        "exactamente con 2015-11 a 2025-12.",
    )

    exigir(
        len(meses_observados)
        ==
        MESES_ESPERADOS,
        "La base no contiene exactamente "
        "122 meses distintos.",
    )

    duplicados = int(
        df.duplicated(
            subset=[
                "mes",
                "banco_id",
            ],
            keep=False,
        ).sum()
    )

    exigir(
        duplicados == 0,
        "La base contiene duplicados "
        "mes + banco_id.",
    )

    faltantes = int(
        df[
            VARIABLES
        ]
        .isna()
        .sum()
        .sum()
    )

    exigir(
        faltantes == 0,
        "La base contiene faltantes "
        "en Y, X1, X2, X3 o X4.",
    )

    # --------------------------------------------------------
    # Todos los valores deben ser finitos.
    # --------------------------------------------------------

    matriz = (
        df[
            VARIABLES
        ]
        .to_numpy(
            dtype=float
        )
    )

    exigir(
        np.isfinite(
            matriz
        ).all(),
        "La base contiene valores "
        "infinitos o no finitos.",
    )

    # --------------------------------------------------------
    # Los 12 bancos fueron seleccionados porque
    # tenían presencia durante todo el periodo antes
    # de eliminar las 6 filas incompletas.
    #
    # En la muestra econométrica efectiva deben
    # conservar al menos 120 observaciones cada uno.
    # --------------------------------------------------------

    n_por_banco = (
        df.groupby(
            "banco_id"
        )
        .size()
    )

    exigir(
        int(
            n_por_banco.min()
        )
        >=
        120,
        "Algún banco tiene menos de "
        "120 observaciones efectivas.",
    )

    df = (
        df
        .sort_values(
            [
                "banco_id",
                "fecha",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# 7. TABLA 01 - ESTRUCTURA DE LA MUESTRA
# ============================================================

def construir_tabla_estructura(df):

    observaciones_por_banco = (
        df.groupby(
            "banco_id",
            sort=True,
        )
        .size()
    )

    tabla = pd.DataFrame(
        {
            "Indicador": [
                "Periodo inicial",
                "Periodo final",
                "Meses calendario",
                "Bancos",
                "Observaciones efectivas",
                "Mínimo de observaciones por banco",
                "Máximo de observaciones por banco",
                "Duplicados mes + banco_id",
                "Faltantes en Y-X4",
            ],
            "Valor": [
                FECHA_INICIO,
                FECHA_CORTE,
                MESES_ESPERADOS,
                df["banco_id"].nunique(),
                len(df),
                int(
                    observaciones_por_banco.min()
                ),
                int(
                    observaciones_por_banco.max()
                ),
                int(
                    df.duplicated(
                        [
                            "mes",
                            "banco_id",
                        ]
                    ).sum()
                ),
                int(
                    df[
                        VARIABLES
                    ]
                    .isna()
                    .sum()
                    .sum()
                ),
            ],
        }
    )

    return tabla


# ============================================================
# 8. TABLA 02 - ESTADÍSTICOS DESCRIPTIVOS
# ============================================================

def construir_tabla_descriptivos(df):

    filas = []

    for variable in VARIABLES:

        serie = df[
            variable
        ]

        filas.append(
            {
                "Variable": variable,
                "Definición":
                    ETIQUETAS_VARIABLES[
                        variable
                    ],
                "N": int(
                    serie.count()
                ),
                "Media":
                    serie.mean(),
                "Desv_estándar":
                    serie.std(
                        ddof=1
                    ),
                "Mínimo":
                    serie.min(),
                "P25":
                    serie.quantile(
                        0.25
                    ),
                "Mediana":
                    serie.median(),
                "P75":
                    serie.quantile(
                        0.75
                    ),
                "Máximo":
                    serie.max(),
            }
        )

    return pd.DataFrame(
        filas
    )


# ============================================================
# 9. TABLA 03 - DESCRIPTIVOS POR BANCO
# ============================================================

def construir_tabla_por_banco(df):

    tabla = (
        df
        .groupby(
            "banco_id",
            sort=True,
        )
        .agg(
            N=(
                "Y",
                "size",
            ),
            Media_Y=(
                "Y",
                "mean",
            ),
            Media_X1=(
                "X1",
                "mean",
            ),
            Media_X2=(
                "X2",
                "mean",
            ),
            Media_X3=(
                "X3",
                "mean",
            ),
        )
        .reset_index()
    )

    return tabla


# ============================================================
# 10. TABLA 04 - CORRELACIONES PEARSON
# ============================================================

def construir_correlaciones(df):

    """
    Matriz estrictamente descriptiva.

    Solo coeficientes Pearson.
    NO p-valores.
    NO estrellas.
    """

    correlaciones = (
        df[
            VARIABLES
        ]
        .corr(
            method="pearson"
        )
    )

    correlaciones.index.name = (
        "Variable"
    )

    return correlaciones


# ============================================================
# 11. FIGURA 01
#     DOLARIZACIÓN DEL CRÉDITO Y DEPÓSITOS
# ============================================================

def generar_figura_01(df):

    mensual = (
        df.groupby(
            "fecha",
            as_index=False,
        )
        .agg(
            Y_promedio=(
                "Y",
                "mean",
            ),
            X1_promedio=(
                "X1",
                "mean",
            ),
        )
    )

    fig, ax = plt.subplots(
        figsize=(
            11,
            6,
        )
    )

    ax.plot(
        mensual[
            "fecha"
        ],
        mensual[
            "Y_promedio"
        ],
        label=(
            "Dolarización "
            "del crédito"
        ),
        linewidth=1.7,
    )

    ax.plot(
        mensual[
            "fecha"
        ],
        mensual[
            "X1_promedio"
        ],
        label=(
            "Dolarización "
            "de depósitos"
        ),
        linewidth=1.7,
    )

    ax.set_title(
        "Dolarización del crédito y de los depósitos"
    )

    ax.set_xlabel(
        "Mes"
    )

    ax.set_ylabel(
        "Porcentaje"
    )

    ax.legend()

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    fig.savefig(
        FIGURA_01,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )


# ============================================================
# 12. FIGURA 02
#     TASAS ACTIVA Y PASIVA
# ============================================================

def generar_figura_02(df):

    mensual = (
        df.groupby(
            "fecha",
            as_index=False,
        )
        .agg(
            X2_promedio=(
                "X2",
                "mean",
            ),
            X3_promedio=(
                "X3",
                "mean",
            ),
        )
    )

    fig, ax = plt.subplots(
        figsize=(
            11,
            6,
        )
    )

    ax.plot(
        mensual[
            "fecha"
        ],
        mensual[
            "X2_promedio"
        ],
        label=(
            "Tasa activa "
            "de consumo MN"
        ),
        linewidth=1.7,
    )

    ax.plot(
        mensual[
            "fecha"
        ],
        mensual[
            "X3_promedio"
        ],
        label=(
            "Tasa pasiva "
            "de ahorro MN"
        ),
        linewidth=1.7,
    )

    ax.set_title(
        "Tasas activa y pasiva en moneda nacional"
    )

    ax.set_xlabel(
        "Mes"
    )

    ax.set_ylabel(
        "Porcentaje"
    )

    ax.legend()

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    fig.savefig(
        FIGURA_02,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )


# ============================================================
# 13. FIGURA 03
#     INFLACIÓN MENSUAL
# ============================================================

def generar_figura_03(df):

    # X4 debe ser única para todos los bancos
    # dentro de cada mes.

    conteo_valores_mes = (
        df.groupby(
            "mes"
        )[
            "X4"
        ]
        .nunique()
    )

    exigir(
        (
            conteo_valores_mes
            ==
            1
        ).all(),
        "X4 presenta más de un valor "
        "dentro del mismo mes.",
    )

    inflacion = (
        df[
            [
                "mes",
                "fecha",
                "X4",
            ]
        ]
        .drop_duplicates(
            subset=[
                "mes"
            ]
        )
        .sort_values(
            "fecha"
        )
    )

    exigir(
        len(inflacion)
        ==
        MESES_ESPERADOS,
        "La serie mensual de inflación "
        "no contiene 122 meses.",
    )

    fig, ax = plt.subplots(
        figsize=(
            11,
            6,
        )
    )

    ax.plot(
        inflacion[
            "fecha"
        ],
        inflacion[
            "X4"
        ],
        linewidth=1.7,
    )

    ax.axhline(
        y=0,
        linewidth=0.8,
    )

    ax.set_title(
        "Inflación mensual"
    )

    ax.set_xlabel(
        "Mes"
    )

    ax.set_ylabel(
        "Variación porcentual mensual"
    )

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    fig.savefig(
        FIGURA_03,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )


# ============================================================
# 14. FIGURA 04
#     DISPERSIÓN Y - X1
# ============================================================

def generar_figura_04(df):

    x = (
        df[
            "X1"
        ]
        .to_numpy(
            dtype=float
        )
    )

    y = (
        df[
            "Y"
        ]
        .to_numpy(
            dtype=float
        )
    )

    pendiente, intercepto = (
        np.polyfit(
            x,
            y,
            1,
        )
    )

    x_linea = np.linspace(
        x.min(),
        x.max(),
        200,
    )

    y_linea = (
        intercepto
        +
        pendiente
        *
        x_linea
    )

    fig, ax = plt.subplots(
        figsize=(
            8,
            6,
        )
    )

    ax.scatter(
        x,
        y,
        alpha=0.35,
        s=18,
        label="Observaciones banco-mes",
    )

    ax.plot(
        x_linea,
        y_linea,
        linewidth=1.8,
        label="Ajuste lineal descriptivo",
    )

    ax.set_title(
        "Dolarización del crédito y de los depósitos"
    )

    ax.set_xlabel(
        "Dolarización de depósitos (%)"
    )

    ax.set_ylabel(
        "Dolarización del crédito (%)"
    )

    ax.legend()

    ax.grid(
        alpha=0.25
    )

    fig.tight_layout()

    fig.savefig(
        FIGURA_04,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )


# ============================================================
# 15. OLS AGRUPADO DE REFERENCIA
# ============================================================

def estimar_ols_agrupado(df):

    X_ols = sm.add_constant(
        df[
            EXPLICATIVAS
        ],
        has_constant="add",
    )

    y_ols = df[
        "Y"
    ]

    modelo_ols = sm.OLS(
        y_ols,
        X_ols,
    )

    # --------------------------------------------------------
    # Corrección aprobada:
    #
    # HC3 + use_t=True
    #
    # De esta forma t, p-valores e intervalos
    # se reportan coherentemente como inferencia
    # basada en estadístico t.
    # --------------------------------------------------------

    resultado_ols = modelo_ols.fit(
        cov_type="HC3",
        use_t=True,
    )

    exigir(
        int(
            resultado_ols.nobs
        )
        ==
        N_ESPERADO,
        "OLS no utilizó exactamente "
        "1,458 observaciones.",
    )

    return (
        resultado_ols,
        X_ols,
    )


# ============================================================
# 16. TABLA OLS
# ============================================================

def construir_tabla_ols(
    resultado_ols,
):

    ic = resultado_ols.conf_int(
        alpha=ALPHA
    )

    filas = []

    for termino in (
        resultado_ols.params.index
    ):

        filas.append(
            {
                "Término":
                    termino,
                "Coeficiente":
                    resultado_ols.params[
                        termino
                    ],
                "Error_estándar_HC3":
                    resultado_ols.bse[
                        termino
                    ],
                "t":
                    resultado_ols.tvalues[
                        termino
                    ],
                "p_valor":
                    resultado_ols.pvalues[
                        termino
                    ],
                "IC95_inferior":
                    ic.loc[
                        termino,
                        0,
                    ],
                "IC95_superior":
                    ic.loc[
                        termino,
                        1,
                    ],
                "N":
                    int(
                        resultado_ols.nobs
                    ),
                "R2":
                    resultado_ols.rsquared,
                "R2_ajustado":
                    resultado_ols.rsquared_adj,
                "Covarianza":
                    "HC3",
                "Distribución_inferencia":
                    "t",
            }
        )

    return pd.DataFrame(
        filas
    )


# ============================================================
# 17. PREPARAR ÍNDICE PANEL
# ============================================================

def preparar_panel(df):

    panel = (
        df[
            [
                "banco_id",
                "fecha",
                "Y",
                "X1",
                "X2",
                "X3",
                "X4",
            ]
        ]
        .copy()
        .set_index(
            [
                "banco_id",
                "fecha",
            ]
        )
        .sort_index()
    )

    exigir(
        panel.index.is_unique,
        "El índice banco-fecha "
        "del panel no es único.",
    )

    return panel


# ============================================================
# 18. EFECTOS FIJOS POR BANCO
#     DRISCOLL-KRAAY PREDEFINIDO
# ============================================================

def estimar_efectos_fijos(panel):

    y_fe = panel[
        "Y"
    ]

    X_fe = panel[
        EXPLICATIVAS
    ]

    modelo_fe = PanelOLS(
        dependent=y_fe,
        exog=X_fe,
        entity_effects=True,
        time_effects=False,
        drop_absorbed=False,
        check_rank=True,
    )

    resultado_fe = modelo_fe.fit(
        cov_type="kernel",
        kernel=DK_KERNEL,
        bandwidth=DK_BANDWIDTH,
        debiased=True,
    )

    exigir(
        int(
            resultado_fe.nobs
        )
        ==
        N_ESPERADO,
        "El modelo FE no utilizó "
        "exactamente 1,458 observaciones.",
    )

    exigir(
        resultado_fe.model.entity_effects,
        "El modelo principal no contiene "
        "efectos fijos por banco.",
    )

    exigir(
        not
        resultado_fe.model.time_effects,
        "El modelo principal incluyó "
        "efectos fijos completos por mes, "
        "lo cual no está autorizado.",
    )

    return resultado_fe


# ============================================================
# 19. TABLA DE EFECTOS FIJOS
# ============================================================

def construir_tabla_fe(
    resultado_fe,
    df,
):

    ic = resultado_fe.conf_int(
        level=0.95
    )

    filas = []

    for termino in (
        resultado_fe.params.index
    ):

        filas.append(
            {
                "Término":
                    termino,
                "Coeficiente":
                    resultado_fe.params[
                        termino
                    ],
                "Error_estándar_DK":
                    resultado_fe.std_errors[
                        termino
                    ],
                "t":
                    resultado_fe.tstats[
                        termino
                    ],
                "p_valor":
                    resultado_fe.pvalues[
                        termino
                    ],
                "IC95_inferior":
                    ic.loc[
                        termino,
                        "lower",
                    ],
                "IC95_superior":
                    ic.loc[
                        termino,
                        "upper",
                    ],
                "N":
                    int(
                        resultado_fe.nobs
                    ),
                "Bancos":
                    df[
                        "banco_id"
                    ].nunique(),
                "R2_within":
                    resultado_fe.rsquared_within,
                "Efectos_fijos_banco":
                    "Sí",
                "Efectos_fijos_mes":
                    "No",
                "Covarianza":
                    "Driscoll-Kraay",
                "Kernel":
                    "Bartlett",
                "Bandwidth":
                    DK_BANDWIDTH,
            }
        )

    return pd.DataFrame(
        filas
    )


# ============================================================
# 20. VIF
# ============================================================

def calcular_vif(df):

    X_vif = sm.add_constant(
        df[
            EXPLICATIVAS
        ],
        has_constant="add",
    )

    resultados = []

    for variable in EXPLICATIVAS:

        indice = (
            X_vif.columns
            .get_loc(
                variable
            )
        )

        vif = (
            variance_inflation_factor(
                X_vif.to_numpy(
                    dtype=float
                ),
                indice,
            )
        )

        resultados.append(
            {
                "Variable":
                    variable,
                "VIF":
                    float(vif),
            }
        )

    return pd.DataFrame(
        resultados
    )


# ============================================================
# 21. BREUSCH-PAGAN / KOENKER
# ============================================================

def prueba_breusch_pagan(
    resultado_ols,
    X_ols,
):

    """
    Se usa explícitamente robust=True.

    Es el comportamiento por defecto de
    statsmodels. Corresponde a la versión
    studentizada de Koenker del diagnóstico
    Breusch-Pagan.

    H0:
        homocedasticidad.
    """

    (
        lm,
        lm_pvalue,
        fvalue,
        f_pvalue,
    ) = het_breuschpagan(
        resultado_ols.resid,
        X_ols,
        robust=True,
    )

    return {
        "lm":
            float(lm),
        "lm_pvalue":
            float(lm_pvalue),
        "f":
            float(fvalue),
        "f_pvalue":
            float(f_pvalue),
    }


# ============================================================
# 22. PRIMERAS DIFERENCIAS CON MESES CONSECUTIVOS
# ============================================================

def construir_primeras_diferencias(
    df,
):

    """
    Construye primeras diferencias únicamente cuando:

        mes_t - mes_(t-1) = 1 mes

    Esto es importante porque la muestra econométrica
    perdió únicamente seis banco-mes por falta de
    información de fuente.

    Nunca se toma, por ejemplo:

        marzo - enero

    como si fuese una primera diferencia mensual.
    """

    trabajo = (
        df[
            [
                "banco_id",
                "mes",
                "fecha",
                "periodo_num",
                "Y",
                "X1",
                "X2",
                "X3",
                "X4",
            ]
        ]
        .copy()
        .sort_values(
            [
                "banco_id",
                "fecha",
            ]
        )
    )

    grupo = trabajo.groupby(
        "banco_id",
        sort=False,
    )

    periodo_previo = (
        grupo[
            "periodo_num"
        ]
        .shift(1)
    )

    consecutivo = (
        trabajo[
            "periodo_num"
        ]
        -
        periodo_previo
        ==
        1
    )

    for variable in VARIABLES:

        nombre = (
            f"d_{variable}"
        )

        trabajo[
            nombre
        ] = (
            grupo[
                variable
            ]
            .diff()
        )

        trabajo.loc[
            ~consecutivo,
            nombre,
        ] = np.nan

    columnas_diferencias = [
        f"d_{variable}"
        for variable
        in VARIABLES
    ]

    diferencias = (
        trabajo
        .dropna(
            subset=
                columnas_diferencias
        )
        .copy()
    )

    exigir(
        not diferencias.empty,
        "No pudieron construirse "
        "primeras diferencias consecutivas.",
    )

    return diferencias


# ============================================================
# 23. WOOLDRIDGE-DRUKKER
# ============================================================

def prueba_wooldridge_drukker(
    df,
):

    """
    Procedimiento:

    1. Estimar en primeras diferencias:

       ΔY_it =
       β1ΔX1_it +
       β2ΔX2_it +
       β3ΔX3_it +
       β4ΔX4_it +
       e_it

       sin constante.

    2. Obtener los residuos e_it.

    3. Estimar:

       e_it = rho * e_i,t-1 + v_it

       sin constante y usando covarianza
       cluster por banco.

    4. Contrastar:

       H0: rho = -0.5

    Bajo ausencia de autocorrelación de primer
    orden en el error original del modelo panel,
    los residuos de la ecuación en primeras
    diferencias presentan esa correlación.

    Solo se utilizan pares de meses efectivamente
    consecutivos.
    """

    diferencias = (
        construir_primeras_diferencias(
            df
        )
    )

    y_fd = diferencias[
        "d_Y"
    ]

    X_fd = diferencias[
        [
            "d_X1",
            "d_X2",
            "d_X3",
            "d_X4",
        ]
    ]

    modelo_fd = sm.OLS(
        y_fd,
        X_fd,
    )

    resultado_fd = (
        modelo_fd.fit()
    )

    diferencias[
        "resid_fd"
    ] = resultado_fd.resid

    diferencias = (
        diferencias
        .sort_values(
            [
                "banco_id",
                "periodo_num",
            ]
        )
        .copy()
    )

    grupo = diferencias.groupby(
        "banco_id",
        sort=False,
    )

    diferencias[
        "resid_lag"
    ] = (
        grupo[
            "resid_fd"
        ]
        .shift(1)
    )

    diferencias[
        "periodo_lag"
    ] = (
        grupo[
            "periodo_num"
        ]
        .shift(1)
    )

    # --------------------------------------------------------
    # El residuo de t-1 debe corresponder realmente
    # al mes inmediatamente anterior.
    # --------------------------------------------------------

    mascara_pares = (
        diferencias[
            "resid_lag"
        ].notna()
        &
        (
            diferencias[
                "periodo_num"
            ]
            -
            diferencias[
                "periodo_lag"
            ]
            ==
            1
        )
    )

    auxiliar = (
        diferencias.loc[
            mascara_pares,
            [
                "banco_id",
                "resid_fd",
                "resid_lag",
            ],
        ]
        .copy()
    )

    exigir(
        len(auxiliar)
        >
        BANCOS_ESPERADOS,
        "No existen suficientes pares "
        "consecutivos para Wooldridge-Drukker.",
    )

    grupos_cluster = (
        pd.Categorical(
            auxiliar[
                "banco_id"
            ]
        )
        .codes
    )

    modelo_auxiliar = sm.OLS(
        auxiliar[
            "resid_fd"
        ],
        auxiliar[
            [
                "resid_lag"
            ]
        ],
    )

    resultado_auxiliar = (
        modelo_auxiliar.fit(
            cov_type="cluster",
            cov_kwds={
                "groups":
                    grupos_cluster,
            },
            use_t=True,
        )
    )

    rho = float(
        resultado_auxiliar.params[
            "resid_lag"
        ]
    )

    error_rho = float(
        resultado_auxiliar.bse[
            "resid_lag"
        ]
    )

    # --------------------------------------------------------
    # H0: rho = -0.5
    # --------------------------------------------------------

    prueba = (
        resultado_auxiliar.f_test(
            "resid_lag = -0.5"
        )
    )

    estadistico_f = float(
        np.asarray(
            prueba.fvalue
        ).squeeze()
    )

    p_valor = float(
        np.asarray(
            prueba.pvalue
        ).squeeze()
    )

    return {
        "rho":
            rho,
        "error_rho":
            error_rho,
        "f":
            estadistico_f,
        "p_valor":
            p_valor,
        "n_diferencias":
            int(
                len(
                    diferencias
                )
            ),
        "n_auxiliar":
            int(
                len(
                    auxiliar
                )
            ),
        "bancos":
            int(
                auxiliar[
                    "banco_id"
                ]
                .nunique()
            ),
    }


# ============================================================
# 24. PESARAN CD
# ============================================================

def prueba_pesaran_cd(
    resultado_fe,
):

    """
    Pesaran CD para panel ligeramente desbalanceado.

    Para cada pareja de bancos:

        - se alinean únicamente meses comunes;
        - se calcula la correlación de residuos;
        - T_ij es el número de meses comunes.

    Estadístico:

             sqrt(2)
    CD = ------------------ *
         sqrt(N(N - 1))

         sum_{i<j} sqrt(T_ij) * rho_ij

    equivalente a:

    sqrt(2 / [N(N-1)])
    * sum sqrt(T_ij) rho_ij

    H0:
        independencia transversal.
    """

    residuos = (
        resultado_fe.resids
        .rename(
            "residuo"
        )
        .reset_index()
    )

    # El índice del PanelOLS fue:
    # banco_id + fecha.

    exigir(
        {
            "banco_id",
            "fecha",
            "residuo",
        }.issubset(
            residuos.columns
        ),
        "No se pudo recuperar correctamente "
        "el índice de residuos del modelo FE.",
    )

    bancos = sorted(
        residuos[
            "banco_id"
        ]
        .unique()
        .tolist()
    )

    n_bancos = len(
        bancos
    )

    exigir(
        n_bancos
        ==
        BANCOS_ESPERADOS,
        "Pesaran CD no recibió "
        "los 12 bancos esperados.",
    )

    suma = 0.0
    pares_validos = 0

    detalle_pares = []

    for banco_i, banco_j in combinations(
        bancos,
        2,
    ):

        ri = (
            residuos.loc[
                residuos[
                    "banco_id"
                ]
                ==
                banco_i,
                [
                    "fecha",
                    "residuo",
                ],
            ]
            .rename(
                columns={
                    "residuo":
                        "residuo_i"
                }
            )
        )

        rj = (
            residuos.loc[
                residuos[
                    "banco_id"
                ]
                ==
                banco_j,
                [
                    "fecha",
                    "residuo",
                ],
            ]
            .rename(
                columns={
                    "residuo":
                        "residuo_j"
                }
            )
        )

        comun = ri.merge(
            rj,
            on="fecha",
            how="inner",
            validate="one_to_one",
        )

        tij = len(
            comun
        )

        exigir(
            tij >= 3,
            "Una pareja de bancos no posee "
            "suficientes periodos comunes "
            "para Pesaran CD.",
        )

        desv_i = (
            comun[
                "residuo_i"
            ]
            .std(
                ddof=1
            )
        )

        desv_j = (
            comun[
                "residuo_j"
            ]
            .std(
                ddof=1
            )
        )

        exigir(
            desv_i > 0
            and
            desv_j > 0,
            "Una pareja presenta residuos "
            "sin variación para Pesaran CD.",
        )

        rho_ij = float(
            comun[
                "residuo_i"
            ]
            .corr(
                comun[
                    "residuo_j"
                ]
            )
        )

        exigir(
            np.isfinite(
                rho_ij
            ),
            "Se obtuvo una correlación residual "
            "no finita en Pesaran CD.",
        )

        suma += (
            np.sqrt(
                tij
            )
            *
            rho_ij
        )

        pares_validos += 1

        detalle_pares.append(
            (
                banco_i,
                banco_j,
                tij,
                rho_ij,
            )
        )

    pares_esperados = (
        n_bancos
        *
        (
            n_bancos
            -
            1
        )
        //
        2
    )

    exigir(
        pares_validos
        ==
        pares_esperados,
        "Pesaran CD no utilizó "
        "todas las parejas de bancos.",
    )

    cd = (
        np.sqrt(
            2.0
            /
            (
                n_bancos
                *
                (
                    n_bancos
                    -
                    1
                )
            )
        )
        *
        suma
    )

    p_valor = (
        2.0
        *
        norm.sf(
            abs(
                cd
            )
        )
    )

    return {
        "cd":
            float(cd),
        "p_valor":
            float(p_valor),
        "bancos":
            n_bancos,
        "pares":
            pares_validos,
    }


# ============================================================
# 25. POOLABILITY
# ============================================================

def prueba_poolability(
    resultado_fe,
):

    """
    Prueba F conjunta de los efectos bancarios.

    H0:
        los efectos bancarios incluidos
        son conjuntamente iguales a cero.

    Esta prueba se reporta como diagnóstico
    complementario.

    NO determina la covarianza del modelo principal.
    """

    prueba = (
        resultado_fe.f_pooled
    )

    return {
        "f":
            float(
                prueba.stat
            ),
        "p_valor":
            float(
                prueba.pval
            ),
        "distribucion":
            str(
                prueba.dist_name
            ),
    }


# ============================================================
# 26. DECISIÓN DESCRIPTIVA AL 5 %
# ============================================================

def decision_pvalor(
    p_valor,
):

    if p_valor < ALPHA:

        return (
            "Rechazar H0 al 5%"
        )

    return (
        "No rechazar H0 al 5%"
    )


# ============================================================
# 27. TABLA 07 - DIAGNÓSTICOS
# ============================================================

def construir_tabla_diagnosticos(
    tabla_vif,
    bp,
    wooldridge,
    pesaran,
    poolability,
):

    filas = []

    # --------------------------------------------------------
    # VIF
    # --------------------------------------------------------

    for _, fila in (
        tabla_vif.iterrows()
    ):

        filas.append(
            {
                "Diagnóstico":
                    "VIF",
                "Variable":
                    fila[
                        "Variable"
                    ],
                "Estadístico":
                    fila[
                        "VIF"
                    ],
                "p_valor":
                    np.nan,
                "Hipótesis_nula":
                    "",
                "Decisión_5pct":
                    "",
                "Detalle":
                    (
                        "Factor de inflación "
                        "de la varianza"
                    ),
            }
        )

    # --------------------------------------------------------
    # Breusch-Pagan / Koenker
    # --------------------------------------------------------

    filas.append(
        {
            "Diagnóstico":
                "Breusch-Pagan/Koenker LM",
            "Variable":
                "",
            "Estadístico":
                bp[
                    "lm"
                ],
            "p_valor":
                bp[
                    "lm_pvalue"
                ],
            "Hipótesis_nula":
                "Homocedasticidad",
            "Decisión_5pct":
                decision_pvalor(
                    bp[
                        "lm_pvalue"
                    ]
                ),
            "Detalle":
                "Versión studentizada; robust=True",
        }
    )

    filas.append(
        {
            "Diagnóstico":
                "Breusch-Pagan/Koenker F",
            "Variable":
                "",
            "Estadístico":
                bp[
                    "f"
                ],
            "p_valor":
                bp[
                    "f_pvalue"
                ],
            "Hipótesis_nula":
                "Homocedasticidad",
            "Decisión_5pct":
                decision_pvalor(
                    bp[
                        "f_pvalue"
                    ]
                ),
            "Detalle":
                "Versión studentizada; robust=True",
        }
    )

    # --------------------------------------------------------
    # Wooldridge-Drukker
    # --------------------------------------------------------

    filas.append(
        {
            "Diagnóstico":
                "Wooldridge-Drukker",
            "Variable":
                "rho",
            "Estadístico":
                wooldridge[
                    "f"
                ],
            "p_valor":
                wooldridge[
                    "p_valor"
                ],
            "Hipótesis_nula":
                (
                    "No autocorrelación AR(1) "
                    "en el error original"
                ),
            "Decisión_5pct":
                decision_pvalor(
                    wooldridge[
                        "p_valor"
                    ]
                ),
            "Detalle":
                (
                    "H0: rho=-0.5; "
                    f"rho estimado="
                    f"{wooldridge['rho']:.6f}"
                ),
        }
    )

    # --------------------------------------------------------
    # Pesaran CD
    # --------------------------------------------------------

    filas.append(
        {
            "Diagnóstico":
                "Pesaran CD",
            "Variable":
                "",
            "Estadístico":
                pesaran[
                    "cd"
                ],
            "p_valor":
                pesaran[
                    "p_valor"
                ],
            "Hipótesis_nula":
                "Independencia transversal",
            "Decisión_5pct":
                decision_pvalor(
                    pesaran[
                        "p_valor"
                    ]
                ),
            "Detalle":
                (
                    f"{pesaran['pares']} "
                    "pares de bancos"
                ),
        }
    )

    # --------------------------------------------------------
    # Poolability
    # --------------------------------------------------------

    filas.append(
        {
            "Diagnóstico":
                "F de poolability",
            "Variable":
                "",
            "Estadístico":
                poolability[
                    "f"
                ],
            "p_valor":
                poolability[
                    "p_valor"
                ],
            "Hipótesis_nula":
                (
                    "Efectos bancarios "
                    "conjuntamente iguales a cero"
                ),
            "Decisión_5pct":
                decision_pvalor(
                    poolability[
                        "p_valor"
                    ]
                ),
            "Detalle":
                (
                    "Prueba complementaria; "
                    "la F convencional supone "
                    "homocedasticidad"
                ),
        }
    )

    return pd.DataFrame(
        filas
    )


# ============================================================
# 28. CONSTRUIR RESUMEN DE TEXTO
# ============================================================

def construir_resumen(
    df,
    resultado_ols,
    resultado_fe,
    tabla_vif,
    bp,
    wooldridge,
    pesaran,
    poolability,
):

    lineas = []

    lineas.append(
        "=" * 90
    )

    lineas.append(
        "04_ANALISIS - RESUMEN DE EJECUCIÓN"
    )

    lineas.append(
        "=" * 90
    )

    lineas.append("")

    lineas.append(
        "Tema:"
    )

    lineas.append(
        "Dolarización del crédito y de los depósitos "
        "en el sistema financiero peruano"
    )

    lineas.append("")

    lineas.append(
        "Alcance:"
    )

    lineas.append(
        "Análisis de asociaciones estadísticas. "
        "No se realizan afirmaciones causales."
    )

    lineas.append("")

    # --------------------------------------------------------
    # Base
    # --------------------------------------------------------

    lineas.append(
        "MUESTRA"
    )

    lineas.append(
        "-" * 90
    )

    lineas.append(
        f"Archivo: {RUTA_BASE}"
    )

    lineas.append(
        f"Periodo: {FECHA_INICIO} a {FECHA_CORTE}"
    )

    lineas.append(
        f"Meses calendario: {MESES_ESPERADOS}"
    )

    lineas.append(
        f"Bancos: {df['banco_id'].nunique()}"
    )

    lineas.append(
        f"Observaciones efectivas: {len(df)}"
    )

    lineas.append(
        "Interpolación: 0"
    )

    lineas.append(
        "Imputación: 0"
    )

    lineas.append(
        "Extrapolación: 0"
    )

    lineas.append("")

    # --------------------------------------------------------
    # OLS
    # --------------------------------------------------------

    lineas.append(
        "OLS AGRUPADO DE REFERENCIA"
    )

    lineas.append(
        "-" * 90
    )

    lineas.append(
        "Covarianza: HC3"
    )

    lineas.append(
        "use_t=True"
    )

    lineas.append(
        f"N: {int(resultado_ols.nobs)}"
    )

    lineas.append(
        f"R2: {resultado_ols.rsquared:.8f}"
    )

    lineas.append(
        "R2 ajustado: "
        f"{resultado_ols.rsquared_adj:.8f}"
    )

    lineas.append("")

    for termino in (
        resultado_ols.params.index
    ):

        lineas.append(
            (
                f"{termino}: "
                f"coef={resultado_ols.params[termino]:.8f}; "
                f"se={resultado_ols.bse[termino]:.8f}; "
                f"t={resultado_ols.tvalues[termino]:.8f}; "
                f"p={resultado_ols.pvalues[termino]:.8f}"
            )
        )

    lineas.append("")

    # --------------------------------------------------------
    # FE
    # --------------------------------------------------------

    lineas.append(
        "MODELO PRINCIPAL - EFECTOS FIJOS POR BANCO"
    )

    lineas.append(
        "-" * 90
    )

    lineas.append(
        "Efectos fijos por banco: Sí"
    )

    lineas.append(
        "Efectos fijos completos por mes: No"
    )

    lineas.append(
        "Covarianza: Driscoll-Kraay"
    )

    lineas.append(
        "Kernel: Bartlett"
    )

    lineas.append(
        f"Bandwidth: {DK_BANDWIDTH}"
    )

    lineas.append(
        f"N: {int(resultado_fe.nobs)}"
    )

    lineas.append(
        f"R2 within: {resultado_fe.rsquared_within:.8f}"
    )

    lineas.append("")

    for termino in (
        resultado_fe.params.index
    ):

        lineas.append(
            (
                f"{termino}: "
                f"coef={resultado_fe.params[termino]:.8f}; "
                f"se_DK={resultado_fe.std_errors[termino]:.8f}; "
                f"t={resultado_fe.tstats[termino]:.8f}; "
                f"p={resultado_fe.pvalues[termino]:.8f}"
            )
        )

    lineas.append("")

    # --------------------------------------------------------
    # Diagnósticos
    # --------------------------------------------------------

    lineas.append(
        "DIAGNÓSTICOS"
    )

    lineas.append(
        "-" * 90
    )

    lineas.append(
        "VIF:"
    )

    for _, fila in (
        tabla_vif.iterrows()
    ):

        lineas.append(
            (
                f"  {fila['Variable']}: "
                f"{fila['VIF']:.8f}"
            )
        )

    lineas.append("")

    lineas.append(
        (
            "Breusch-Pagan/Koenker LM: "
            f"{bp['lm']:.8f}; "
            f"p={bp['lm_pvalue']:.8f}"
        )
    )

    lineas.append(
        (
            "Breusch-Pagan/Koenker F: "
            f"{bp['f']:.8f}; "
            f"p={bp['f_pvalue']:.8f}"
        )
    )

    lineas.append(
        (
            "Wooldridge-Drukker: "
            f"rho={wooldridge['rho']:.8f}; "
            f"F={wooldridge['f']:.8f}; "
            f"p={wooldridge['p_valor']:.8f}"
        )
    )

    lineas.append(
        (
            "Pesaran CD: "
            f"CD={pesaran['cd']:.8f}; "
            f"p={pesaran['p_valor']:.8f}; "
            f"pares={pesaran['pares']}"
        )
    )

    lineas.append(
        (
            "F de poolability: "
            f"F={poolability['f']:.8f}; "
            f"p={poolability['p_valor']:.8f}; "
            f"distribución={poolability['distribucion']}"
        )
    )

    lineas.append("")

    lineas.append(
        "NOTA METODOLÓGICA:"
    )

    lineas.append(
        (
            "Los diagnósticos se reportan como evidencia "
            "sobre las propiedades del panel. "
            "No se utilizan para escoger ex post "
            "la covarianza del modelo principal."
        )
    )

    lineas.append(
        (
            "La covarianza Driscoll-Kraay, kernel Bartlett "
            "y bandwidth=4 fue definida antes de observar "
            "los resultados de las pruebas."
        )
    )

    lineas.append("")

    # --------------------------------------------------------
    # Versiones
    # --------------------------------------------------------

    lineas.append(
        "VERSIONES"
    )

    lineas.append(
        "-" * 90
    )

    lineas.append(
        f"numpy: {np.__version__}"
    )

    lineas.append(
        f"pandas: {pd.__version__}"
    )

    lineas.append(
        f"scipy: {scipy.__version__}"
    )

    lineas.append(
        f"statsmodels: {statsmodels.__version__}"
    )

    lineas.append(
        f"linearmodels: {linearmodels.__version__}"
    )

    lineas.append("")

    lineas.append(
        "ESTADO = ANALISIS_COMPLETO_VALIDADO"
    )

    return "\n".join(
        lineas
    )


# ============================================================
# 29. MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("04_ANALISIS")
    print("=" * 100)

    print()
    print(
        "Leyendo base oficial..."
    )

    # ========================================================
    # A. BASE
    # ========================================================

    df = leer_y_validar_base()

    print(
        "Base validada:"
    )

    print(
        f"  Observaciones: {len(df)}"
    )

    print(
        f"  Bancos: {df['banco_id'].nunique()}"
    )

    print(
        f"  Periodo: {FECHA_INICIO} a {FECHA_CORTE}"
    )

    # ========================================================
    # B. TABLAS DESCRIPTIVAS
    # ========================================================

    tabla_01 = (
        construir_tabla_estructura(
            df
        )
    )

    guardar_tabla(
        tabla_01,
        TABLA_01,
        (
            "Estructura de la "
            "muestra econométrica"
        ),
        "tab:estructura_muestra",
        index=False,
    )

    tabla_02 = (
        construir_tabla_descriptivos(
            df
        )
    )

    guardar_tabla(
        tabla_02,
        TABLA_02,
        "Estadísticos descriptivos",
        "tab:estadisticos_descriptivos",
        index=False,
    )

    tabla_03 = (
        construir_tabla_por_banco(
            df
        )
    )

    guardar_tabla(
        tabla_03,
        TABLA_03,
        "Estadísticos descriptivos por banco",
        "tab:descriptivos_banco",
        index=False,
    )

    # ========================================================
    # C. CORRELACIONES
    # ========================================================

    tabla_04 = (
        construir_correlaciones(
            df
        )
    )

    guardar_tabla(
        tabla_04,
        TABLA_04,
        (
            "Matriz de correlaciones "
            "de Pearson"
        ),
        "tab:correlaciones_pearson",
        index=True,
    )

    # ========================================================
    # D. FIGURAS
    # ========================================================

    generar_figura_01(
        df
    )

    generar_figura_02(
        df
    )

    generar_figura_03(
        df
    )

    generar_figura_04(
        df
    )

    # ========================================================
    # E. OLS AGRUPADO
    # ========================================================

    (
        resultado_ols,
        X_ols,
    ) = estimar_ols_agrupado(
        df
    )

    tabla_05 = (
        construir_tabla_ols(
            resultado_ols
        )
    )

    guardar_tabla(
        tabla_05,
        TABLA_05,
        (
            "OLS agrupado de referencia "
            "con errores estándar HC3"
        ),
        "tab:ols_agrupado",
        index=False,
    )

    # ========================================================
    # F. EFECTOS FIJOS
    # ========================================================

    panel = preparar_panel(
        df
    )

    resultado_fe = (
        estimar_efectos_fijos(
            panel
        )
    )

    tabla_06 = (
        construir_tabla_fe(
            resultado_fe,
            df,
        )
    )

    guardar_tabla(
        tabla_06,
        TABLA_06,
        (
            "Modelo de efectos fijos por banco "
            "con errores estándar Driscoll-Kraay"
        ),
        "tab:efectos_fijos_banco",
        index=False,
    )

    # ========================================================
    # G. DIAGNÓSTICOS
    # ========================================================

    tabla_vif = calcular_vif(
        df
    )

    bp = prueba_breusch_pagan(
        resultado_ols,
        X_ols,
    )

    wooldridge = (
        prueba_wooldridge_drukker(
            df
        )
    )

    pesaran = (
        prueba_pesaran_cd(
            resultado_fe
        )
    )

    poolability = (
        prueba_poolability(
            resultado_fe
        )
    )

    tabla_07 = (
        construir_tabla_diagnosticos(
            tabla_vif=tabla_vif,
            bp=bp,
            wooldridge=wooldridge,
            pesaran=pesaran,
            poolability=poolability,
        )
    )

    guardar_tabla(
        tabla_07,
        TABLA_07,
        "Pruebas diagnósticas",
        "tab:diagnosticos",
        index=False,
    )

    # ========================================================
    # H. RESUMEN
    # ========================================================

    resumen = construir_resumen(
        df=df,
        resultado_ols=resultado_ols,
        resultado_fe=resultado_fe,
        tabla_vif=tabla_vif,
        bp=bp,
        wooldridge=wooldridge,
        pesaran=pesaran,
        poolability=poolability,
    )

    RUTA_RESUMEN.write_text(
        resumen,
        encoding="utf-8",
    )

    # ========================================================
    # I. CONTROL DE ARCHIVOS GENERADOS
    # ========================================================

    archivos_esperados = [
        TABLA_01.with_suffix(".csv"),
        TABLA_01.with_suffix(".tex"),
        TABLA_02.with_suffix(".csv"),
        TABLA_02.with_suffix(".tex"),
        TABLA_03.with_suffix(".csv"),
        TABLA_03.with_suffix(".tex"),
        TABLA_04.with_suffix(".csv"),
        TABLA_04.with_suffix(".tex"),
        TABLA_05.with_suffix(".csv"),
        TABLA_05.with_suffix(".tex"),
        TABLA_06.with_suffix(".csv"),
        TABLA_06.with_suffix(".tex"),
        TABLA_07.with_suffix(".csv"),
        TABLA_07.with_suffix(".tex"),
        FIGURA_01,
        FIGURA_02,
        FIGURA_03,
        FIGURA_04,
        RUTA_RESUMEN,
    ]

    faltan_archivos = [
        ruta
        for ruta
        in archivos_esperados
        if not ruta.exists()
    ]

    exigir(
        len(
            faltan_archivos
        )
        ==
        0,
        "No se generaron todos los archivos "
        "esperados:\n"
        +
        "\n".join(
            str(ruta)
            for ruta
            in faltan_archivos
        ),
    )

    # ========================================================
    # J. RESUMEN FINAL EN TERMINAL
    # ========================================================

    print()
    print("=" * 100)
    print("RESULTADOS GENERADOS")
    print("=" * 100)

    print()
    print(
        f"N = {len(df)}"
    )

    print(
        "Bancos = "
        f"{df['banco_id'].nunique()}"
    )

    print(
        f"Periodo = {FECHA_INICIO} a {FECHA_CORTE}"
    )

    print()
    print(
        "OLS agrupado:"
    )

    print(
        "  Covarianza = HC3"
    )

    print(
        "  use_t = True"
    )

    print(
        f"  R2 = {resultado_ols.rsquared:.6f}"
    )

    print()
    print(
        "Modelo principal FE:"
    )

    print(
        "  Efectos fijos por banco = Sí"
    )

    print(
        "  Efectos fijos completos por mes = No"
    )

    print(
        "  Covarianza = Driscoll-Kraay"
    )

    print(
        "  Kernel = Bartlett"
    )

    print(
        f"  Bandwidth = {DK_BANDWIDTH}"
    )

    print(
        "  R2 within = "
        f"{resultado_fe.rsquared_within:.6f}"
    )

    print()
    print(
        "Diagnósticos:"
    )

    print(
        "  Breusch-Pagan/Koenker LM: "
        f"p={bp['lm_pvalue']:.6f}"
    )

    print(
        "  Wooldridge-Drukker: "
        f"p={wooldridge['p_valor']:.6f}"
    )

    print(
        "  Pesaran CD: "
        f"p={pesaran['p_valor']:.6f}"
    )

    print(
        "  Poolability: "
        f"p={poolability['p_valor']:.6f}"
    )

    print()
    print(
        "Archivos generados:"
    )

    for ruta in (
        archivos_esperados
    ):

        print(
            f"  {ruta}"
        )

    print()
    print(
        "Interpretación autorizada: asociación, no causalidad."
    )

    print()

    print(
        "ESTADO = ANALISIS_COMPLETO_VALIDADO"
    )


# ============================================================
# 30. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()