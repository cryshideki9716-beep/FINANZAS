# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from datetime import datetime
import csv
import hashlib
import os
import re
import subprocess
import sys


# ============================================================
# 1. OBJETIVO
# ============================================================

"""
02_scraping_web.py
FINANZAS I - UNIDAD I

SCRIPT OFICIAL DE EXTRACCIÓN SBS

Este archivo es el punto de entrada oficial para reproducir
las cuatro variables obtenidas desde la SBS:

Y:
    Dolarización del crédito (%)

X1:
    Dolarización de depósitos (%)

X2:
    Tasa activa de Consumo en Moneda Nacional (%)

X3:
    Tasa pasiva de Depósitos de Ahorro
    en Moneda Nacional (%)

PERIODO:
    2015-11 a 2025-12
    122 meses

IMPORTANTE
==========

La lógica de extracción ya fue desarrollada, diagnosticada y
validada en tres motores de producción separados.

Para evitar:

- duplicar miles de líneas de código;
- introducir diferencias entre parsers;
- modificar fórmulas ya validadas;
- alterar controles de estructura;
- alterar reglas de reanudación;
- alterar la forma de conservar los datos crudos;

este archivo NO reimplementa esos algoritmos.

En cambio, los ejecuta secuencialmente como motores internos:

1. extraccion_produccion_Y_X1_2024200485D.py
2. extraccion_mensual_x2_consumo_mn.py
3. extraccion_mensual_x3_ahorro_mn.py

Después de ejecutarlos, este script:

- valida sus cuatro CSV principales;
- comprueba el periodo completo;
- comprueba el número de filas;
- comprueba 0 duplicados mes + banco_original;
- comprueba las auditorías;
- comprueba existencia de datos crudos;
- calcula SHA-256 de las salidas;
- genera / actualiza log_ejecucion.txt.

Este script NO:

- homologa nombres bancarios;
- integra Y, X1, X2, X3 con X4;
- interpola;
- imputa;
- extrapola;
- selecciona bancos;
- modifica 03_limpieza_datos.py;
- ejecuta 03_limpieza_datos.py;
- modifica 04_analisis.py;
- ejecuta 04_analisis.py.

X4 (inflación) pertenece al flujo de
01_extraccion_api.py y NO se extrae aquí.
"""


# ============================================================
# 2. IDENTIFICACIÓN Y PERIODO
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

FECHA_INICIO = "2015-11"
FECHA_CORTE = "2025-12"

MESES_ESPERADOS = 122


# ============================================================
# 3. RESULTADOS YA VALIDADOS DE LOS EXTRACTORES SBS
# ============================================================

# Estos controles NO cambian la metodología.
#
# Sirven para impedir que una futura modificación accidental
# de una fuente o parser produzca silenciosamente una base
# distinta de la previamente validada.

FILAS_ESPERADAS = {
    "Y": 2005,
    "X1": 2005,
    "X2": 2004,
    "X3": 2004,
}


# ============================================================
# 4. DIRECTORIOS
# ============================================================

RAIZ = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CARPETA_CODIGO = (
    RAIZ
    / "codigo"
)

CARPETA_CRUDOS = (
    RAIZ
    / "datos_crudos"
)

CARPETA_PROCESADOS = (
    RAIZ
    / "datos_procesados"
)

CARPETA_DIAGNOSTICOS = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

LOG_EJECUCION = (
    RAIZ
    / "log_ejecucion.txt"
)


# ============================================================
# 5. MOTORES DE EXTRACCIÓN VALIDADOS
# ============================================================

SCRIPT_Y_X1 = (
    CARPETA_CODIGO
    / (
        "extraccion_produccion_"
        "Y_X1_2024200485D.py"
    )
)

SCRIPT_X2 = (
    CARPETA_CODIGO
    / "extraccion_mensual_x2_consumo_mn.py"
)

SCRIPT_X3 = (
    CARPETA_CODIGO
    / "extraccion_mensual_x3_ahorro_mn.py"
)


ETAPAS = [
    {
        "clave": "Y_X1",
        "nombre": (
            "Y + X1 - Créditos y depósitos SBS"
        ),
        "script": SCRIPT_Y_X1,
    },
    {
        "clave": "X2",
        "nombre": (
            "X2 - Tasa activa Consumo MN"
        ),
        "script": SCRIPT_X2,
    },
    {
        "clave": "X3",
        "nombre": (
            "X3 - Tasa pasiva Ahorro MN"
        ),
        "script": SCRIPT_X3,
    },
]


# ============================================================
# 6. FUENTES OFICIALES Y METADATOS DE EXTRACCIÓN
# ============================================================

FUENTES = {

    "Y": {
        "fuente": "SBS",
        "reporte": (
            "Créditos Directos por Tipo, "
            "Modalidad y Moneda"
        ),
        "codigo": "B-2359",
        "url": (
            "https://www.sbs.gob.pe/app/stats_net/"
            "stats/"
            "EstadisticaSistemaFinancieroResultados.aspx"
            "?c=B-2359"
        ),
        "metodo": (
            "requests + BeautifulSoup + "
            "descarga programática XLS"
        ),
        "selector": (
            "enlaces HTML <a href> que contienen "
            "el identificador mensual B-2359"
        ),
        "pausa_segundos": 1.2,
        "user_agent": (
            "TrabajoAcademicoUNCP/1.0; "
            "Finanzas-I; 2024200485D"
        ),
    },

    "X1": {
        "fuente": "SBS",
        "reporte": (
            "Movimiento de los Depósitos"
        ),
        "codigo": "B-2318",
        "url": (
            "https://www.sbs.gob.pe/app/stats_net/"
            "stats/"
            "EstadisticaSistemaFinancieroResultados.aspx"
            "?c=B-2318"
        ),
        "metodo": (
            "requests + BeautifulSoup + "
            "descarga programática XLS"
        ),
        "selector": (
            "enlaces HTML <a href> que contienen "
            "el identificador mensual B-2318"
        ),
        "pausa_segundos": 1.2,
        "user_agent": (
            "TrabajoAcademicoUNCP/1.0; "
            "Finanzas-I; 2024200485D"
        ),
    },

    "X2": {
        "fuente": "SBS",
        "reporte": (
            "Tasas de Interés por Tipo de "
            "Crédito y Empresa Bancaria"
        ),
        "codigo": "tip=B",
        "url": (
            "https://www.sbs.gob.pe/app/pp/"
            "EstadisticasSAEEPortal/Paginas/"
            "TIActivaTipoCreditoEmpresa.aspx?tip=B"
        ),
        "metodo": (
            "Selenium / Chrome visible"
        ),
        "selector_tabla_mn": (
            "ctl00_cphContent_rpgActualMn_OT"
        ),
        "selector_datazone_mn": (
            "ctl00_cphContent_"
            "rpgActualMn_ctl00_DataZone_DT"
        ),
        "concepto": "Consumo",
        "moneda": "MN",
        "pausa_segundos": 1.2,
        "user_agent": (
            "AcademicResearch-UNCP-FinanzasI-"
            "2024200485D/1.0"
        ),
    },

    "X3": {
        "fuente": "SBS",
        "reporte": (
            "Tasas de Interés Pasivas por "
            "Empresa Bancaria"
        ),
        "codigo": "tip=B",
        "url": (
            "https://www.sbs.gob.pe/app/pp/"
            "EstadisticasSAEEPortal/Paginas/"
            "TIPasivaDepositoEmpresa.aspx?tip=B"
        ),
        "metodo": (
            "Selenium / Chrome visible"
        ),
        "selector_tabla_mn": (
            "ctl00_cphContent_"
            "rpgActualPrimTablaMn_OT"
        ),
        "selector_datazone_mn": (
            "ctl00_cphContent_"
            "rpgActualPrimTablaMn_ctl00_DataZone_DT"
        ),
        "concepto": "Depósitos de Ahorro",
        "moneda": "MN",
        "pausa_segundos": 1.2,
        "user_agent": (
            "User-Agent nativo de Chrome/WebDriver; "
            "el extractor X3 validado no lo sobrescribe"
        ),
    },
}


# ============================================================
# 7. ARCHIVOS PRINCIPALES ESPERADOS
# ============================================================

CSV_Y = (
    CARPETA_PROCESADOS
    / f"Y_dolarizacion_credito_{CODIGO_ESTUDIANTE}.csv"
)

CSV_X1 = (
    CARPETA_PROCESADOS
    / (
        "X1_dolarizacion_depositos_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)

CSV_X2 = (
    CARPETA_PROCESADOS
    / (
        "X2_tasa_activa_consumo_mn_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)

CSV_X3 = (
    CARPETA_PROCESADOS
    / (
        "X3_tasa_pasiva_ahorro_mn_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)


# ============================================================
# 8. AUDITORÍAS ESPERADAS
# ============================================================

AUDITORIA_Y = (
    CARPETA_DIAGNOSTICOS
    / (
        "auditoria_Y_dolarizacion_credito_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)

AUDITORIA_X1 = (
    CARPETA_DIAGNOSTICOS
    / (
        "auditoria_X1_dolarizacion_depositos_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)

AUDITORIA_X2 = (
    CARPETA_DIAGNOSTICOS
    / (
        "auditoria_X2_consumo_mn_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)

AUDITORIA_X3 = (
    CARPETA_DIAGNOSTICOS
    / (
        "auditoria_X3_ahorro_mn_"
        f"{CODIGO_ESTUDIANTE}.csv"
    )
)


# ============================================================
# 9. CARPETAS DE DATOS CRUDOS DE PRODUCCIÓN
# ============================================================

CRUDOS_Y = (
    CARPETA_CRUDOS
    / f"Y_B2359_{CODIGO_ESTUDIANTE}"
)

CRUDOS_X1 = (
    CARPETA_CRUDOS
    / f"X1_B2318_{CODIGO_ESTUDIANTE}"
)

CRUDOS_X2 = (
    CARPETA_CRUDOS
    / f"X2_consumo_mn_{CODIGO_ESTUDIANTE}"
)

CRUDOS_X3 = (
    CARPETA_CRUDOS
    / f"X3_ahorro_mn_{CODIGO_ESTUDIANTE}"
)


# ============================================================
# 10. COLUMNAS EXACTAS ESPERADAS
# ============================================================

COLUMNAS_ESPERADAS = {

    "Y": [
        "mes",
        "banco_original",
        "mn_soles_miles",
        "me_usd_miles",
        "total_soles_miles",
        "dolcred_pct",
        "problemas",
    ],

    "X1": [
        "mes",
        "banco_original",
        "banco_original_me",
        "saldo_final_mn",
        "saldo_final_me",
        "doldep_pct",
        "problemas",
    ],

    "X2": [
        "mes",
        "fecha_sbs",
        "banco_original",
        "tasa_activa_consumo_mn",
    ],

    "X3": [
        "mes",
        "fecha_sbs",
        "banco_original",
        "tasa_pasiva_ahorro_mn",
    ],
}


# ============================================================
# 11. UTILIDADES GENERALES
# ============================================================

def ahora():

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def exigir(
    condicion,
    mensaje,
):

    if not condicion:

        raise RuntimeError(
            mensaje
        )


def sha256_archivo(
    ruta,
):

    hash_obj = hashlib.sha256()

    with ruta.open(
        "rb"
    ) as archivo:

        while True:

            bloque = archivo.read(
                1024 * 1024
            )

            if not bloque:
                break

            hash_obj.update(
                bloque
            )

    return hash_obj.hexdigest()


# ============================================================
# 12. GENERAR LOS 122 MESES ESPERADOS
# ============================================================

def generar_meses():

    anio = 2015
    mes = 11

    salida = []

    while (
        anio,
        mes,
    ) <= (
        2025,
        12,
    ):

        salida.append(
            f"{anio:04d}-{mes:02d}"
        )

        if mes == 12:

            anio += 1
            mes = 1

        else:

            mes += 1

    exigir(
        len(salida)
        ==
        MESES_ESPERADOS,
        (
            "Error interno: el periodo "
            "2015-11 a 2025-12 no generó "
            "exactamente 122 meses."
        ),
    )

    exigir(
        salida[0]
        ==
        FECHA_INICIO,
        "Error en FECHA_INICIO.",
    )

    exigir(
        salida[-1]
        ==
        FECHA_CORTE,
        "Error en FECHA_CORTE.",
    )

    return salida


MESES_OBJETIVO = generar_meses()


# ============================================================
# 13. REGISTRO DE CONSOLA + LOG
# ============================================================

def escribir(
    log,
    texto="",
):

    texto = str(
        texto
    )

    print(
        texto,
        flush=True,
    )

    log.write(
        texto
        +
        "\n"
    )

    log.flush()


def escribir_evento(
    log,
    texto,
):

    escribir(
        log,
        f"[{ahora()}] {texto}",
    )


# ============================================================
# 14. LEER CSV
# ============================================================

def leer_csv(
    ruta,
):

    exigir(
        ruta.exists(),
        f"No existe el archivo esperado: {ruta}",
    )

    with ruta.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as archivo:

        lector = csv.DictReader(
            archivo
        )

        columnas = (
            lector.fieldnames
            or
            []
        )

        filas = list(
            lector
        )

    return (
        columnas,
        filas,
    )


# ============================================================
# 15. VALIDAR CSV PRINCIPAL DE UNA VARIABLE
# ============================================================

def validar_csv_principal(
    clave,
    ruta,
):

    columnas, filas = leer_csv(
        ruta
    )

    esperado_columnas = (
        COLUMNAS_ESPERADAS[
            clave
        ]
    )

    exigir(
        columnas
        ==
        esperado_columnas,
        (
            f"{clave}: columnas distintas "
            "de las validadas.\n"
            f"Esperadas: {esperado_columnas}\n"
            f"Observadas: {columnas}"
        ),
    )

    esperado_filas = (
        FILAS_ESPERADAS[
            clave
        ]
    )

    exigir(
        len(filas)
        ==
        esperado_filas,
        (
            f"{clave}: número de filas "
            "distinto del validado. "
            f"Esperado={esperado_filas}; "
            f"observado={len(filas)}."
        ),
    )

    meses = {
        fila[
            "mes"
        ].strip()
        for fila
        in filas
    }

    exigir(
        meses
        ==
        set(
            MESES_OBJETIVO
        ),
        (
            f"{clave}: los meses del CSV "
            "no coinciden exactamente con "
            "2015-11 a 2025-12."
        ),
    )

    claves = []

    for fila in filas:

        mes = (
            fila.get(
                "mes",
                ""
            )
            .strip()
        )

        banco = (
            fila.get(
                "banco_original",
                ""
            )
            .strip()
        )

        exigir(
            mes != "",
            f"{clave}: existe una fila sin mes.",
        )

        exigir(
            banco != "",
            (
                f"{clave}: existe una fila "
                "sin banco_original."
            ),
        )

        claves.append(
            (
                mes,
                banco,
            )
        )

    duplicados = (
        len(claves)
        -
        len(
            set(
                claves
            )
        )
    )

    exigir(
        duplicados
        ==
        0,
        (
            f"{clave}: existen "
            f"{duplicados} duplicados "
            "mes + banco_original."
        ),
    )

    # --------------------------------------------------------
    # En X2 y X3 el Promedio se guarda por separado.
    # --------------------------------------------------------

    if clave in {
        "X2",
        "X3",
    }:

        promedios_en_principal = [
            fila
            for fila
            in filas
            if (
                fila[
                    "banco_original"
                ]
                .strip()
                .lower()
                ==
                "promedio"
            )
        ]

        exigir(
            len(
                promedios_en_principal
            )
            ==
            0,
            (
                f"{clave}: se encontró "
                "'Promedio' dentro del "
                "CSV bancario principal."
            ),
        )

    return {
        "clave":
            clave,
        "ruta":
            ruta,
        "filas":
            len(
                filas
            ),
        "meses":
            len(
                meses
            ),
        "duplicados":
            duplicados,
        "sha256":
            sha256_archivo(
                ruta
            ),
    }


# ============================================================
# 16. VALIDAR AUDITORÍA MENSUAL
# ============================================================

def validar_auditoria(
    clave,
    ruta,
):

    columnas, filas = leer_csv(
        ruta
    )

    exigir(
        "mes"
        in
        columnas,
        f"{clave}: auditoría sin columna mes.",
    )

    exigir(
        "estado"
        in
        columnas,
        f"{clave}: auditoría sin columna estado.",
    )

    exigir(
        len(filas)
        ==
        MESES_ESPERADOS,
        (
            f"{clave}: la auditoría debe "
            "tener exactamente 122 filas; "
            f"tiene {len(filas)}."
        ),
    )

    meses = [
        fila[
            "mes"
        ].strip()
        for fila
        in filas
    ]

    exigir(
        len(
            set(
                meses
            )
        )
        ==
        MESES_ESPERADOS,
        (
            f"{clave}: la auditoría "
            "contiene meses duplicados."
        ),
    )

    exigir(
        set(
            meses
        )
        ==
        set(
            MESES_OBJETIVO
        ),
        (
            f"{clave}: los meses de "
            "auditoría no coinciden con "
            "el periodo objetivo."
        ),
    )

    estados = {
        fila[
            "estado"
        ].strip()
        for fila
        in filas
    }

    # --------------------------------------------------------
    # Para esta producción ya validada, todos los meses
    # deben estar disponibles.
    # --------------------------------------------------------

    exigir(
        estados
        ==
        {
            "DISPONIBLE"
        },
        (
            f"{clave}: existen estados "
            "distintos de DISPONIBLE "
            f"en la auditoría: "
            f"{sorted(estados)}"
        ),
    )

    return {
        "clave":
            clave,
        "filas_auditoria":
            len(
                filas
            ),
        "estados":
            sorted(
                estados
            ),
        "sha256":
            sha256_archivo(
                ruta
            ),
    }


# ============================================================
# 17. VALIDAR CRUDOS Y / X1
# ============================================================

def validar_crudos_excel():

    exigir(
        CRUDOS_Y.exists(),
        f"No existe la carpeta de crudos Y: {CRUDOS_Y}",
    )

    exigir(
        CRUDOS_X1.exists(),
        f"No existe la carpeta de crudos X1: {CRUDOS_X1}",
    )

    faltantes_y = []

    faltantes_x1 = []

    for mes in MESES_OBJETIVO:

        ruta_y = (
            CRUDOS_Y
            /
            (
                f"Y_B-2359_"
                f"{CODIGO_ESTUDIANTE}_"
                f"{mes}.xls"
            )
        )

        ruta_x1 = (
            CRUDOS_X1
            /
            (
                f"X1_B-2318_"
                f"{CODIGO_ESTUDIANTE}_"
                f"{mes}.xls"
            )
        )

        if not ruta_y.exists():

            faltantes_y.append(
                mes
            )

        if not ruta_x1.exists():

            faltantes_x1.append(
                mes
            )

    exigir(
        not faltantes_y,
        (
            "Faltan archivos crudos Y "
            f"para: {faltantes_y}"
        ),
    )

    exigir(
        not faltantes_x1,
        (
            "Faltan archivos crudos X1 "
            f"para: {faltantes_x1}"
        ),
    )

    return {
        "Y":
            MESES_ESPERADOS,
        "X1":
            MESES_ESPERADOS,
    }


# ============================================================
# 18. EXTRAER MESES DESDE HTML CRUDOS X2 / X3
# ============================================================

def meses_html_disponibles(
    carpeta,
    prefijo,
):

    exigir(
        carpeta.exists(),
        f"No existe la carpeta: {carpeta}",
    )

    patron = re.compile(
        rf"^{re.escape(prefijo)}"
        r"_(\d{4}-\d{2})_"
        r"\d{4}-\d{2}-\d{2}\.html$"
    )

    meses = set()

    archivos_reconocidos = 0

    for ruta in carpeta.glob(
        "*.html"
    ):

        coincidencia = patron.match(
            ruta.name
        )

        if coincidencia:

            meses.add(
                coincidencia.group(
                    1
                )
            )

            archivos_reconocidos += 1

    return {
        "meses":
            meses,
        "archivos":
            archivos_reconocidos,
    }


# ============================================================
# 19. VALIDAR CRUDOS HTML X2 / X3
# ============================================================

def validar_crudos_html():

    x2 = meses_html_disponibles(
        CRUDOS_X2,
        (
            "X2_consumo_mn_"
            f"{CODIGO_ESTUDIANTE}"
        ),
    )

    x3 = meses_html_disponibles(
        CRUDOS_X3,
        (
            "X3_ahorro_mn_"
            f"{CODIGO_ESTUDIANTE}"
        ),
    )

    exigir(
        x2[
            "meses"
        ]
        ==
        set(
            MESES_OBJETIVO
        ),
        (
            "Los HTML crudos X2 no cubren "
            "exactamente los 122 meses."
        ),
    )

    exigir(
        x3[
            "meses"
        ]
        ==
        set(
            MESES_OBJETIVO
        ),
        (
            "Los HTML crudos X3 no cubren "
            "exactamente los 122 meses."
        ),
    )

    return {
        "X2":
            x2[
                "archivos"
            ],
        "X3":
            x3[
                "archivos"
            ],
    }


# ============================================================
# 20. EJECUTAR MOTOR DE EXTRACCIÓN
# ============================================================

def ejecutar_etapa(
    etapa,
    log,
):

    ruta_script = (
        etapa[
            "script"
        ]
    )

    exigir(
        ruta_script.exists(),
        (
            "No existe el motor "
            f"de extracción requerido:\n"
            f"{ruta_script}"
        ),
    )

    escribir(
        log
    )

    escribir(
        log,
        "=" * 100,
    )

    escribir_evento(
        log,
        (
            "INICIO ETAPA "
            f"{etapa['clave']} - "
            f"{etapa['nombre']}"
        ),
    )

    escribir(
        log,
        (
            "Script: "
            f"{ruta_script}"
        ),
    )

    escribir(
        log,
        (
            "SHA256 script: "
            f"{sha256_archivo(ruta_script)}"
        ),
    )

    escribir(
        log,
        "=" * 100,
    )

    entorno = os.environ.copy()

    # --------------------------------------------------------
    # Fuerza salida Python UTF-8 para que la captura del log
    # sea consistente también en Windows.
    # --------------------------------------------------------

    entorno[
        "PYTHONIOENCODING"
    ] = "utf-8"

    entorno[
        "PYTHONUTF8"
    ] = "1"

    comando = [
        sys.executable,
        "-u",
        str(
            ruta_script
        ),
    ]

    escribir(
        log,
        (
            "Comando: "
            +
            " ".join(
                comando
            )
        ),
    )

    proceso = subprocess.Popen(
        comando,
        cwd=str(
            RAIZ
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=entorno,
    )

    exigir(
        proceso.stdout
        is not None,
        (
            "No se pudo capturar "
            "la salida del proceso."
        ),
    )

    for linea in proceso.stdout:

        linea = linea.rstrip(
            "\r\n"
        )

        print(
            linea,
            flush=True,
        )

        log.write(
            f"[{etapa['clave']}] "
            f"{linea}\n"
        )

        log.flush()

    codigo_salida = (
        proceso.wait()
    )

    escribir_evento(
        log,
        (
            "FIN ETAPA "
            f"{etapa['clave']} - "
            f"código_salida={codigo_salida}"
        ),
    )

    exigir(
        codigo_salida
        ==
        0,
        (
            f"La etapa {etapa['clave']} "
            "terminó con código distinto "
            f"de cero: {codigo_salida}"
        ),
    )


# ============================================================
# 21. VALIDACIÓN FINAL DE TODA LA EXTRACCIÓN SBS
# ============================================================

def validar_resultado_total(
    log,
):

    escribir(
        log
    )

    escribir(
        log,
        "=" * 100,
    )

    escribir(
        log,
        "VALIDACIÓN FINAL OFICIAL SBS",
    )

    escribir(
        log,
        "=" * 100,
    )

    resultados_csv = {}

    for clave, ruta in [
        (
            "Y",
            CSV_Y,
        ),
        (
            "X1",
            CSV_X1,
        ),
        (
            "X2",
            CSV_X2,
        ),
        (
            "X3",
            CSV_X3,
        ),
    ]:

        resultado = (
            validar_csv_principal(
                clave,
                ruta,
            )
        )

        resultados_csv[
            clave
        ] = resultado

        escribir(
            log,
            (
                f"{clave}: "
                f"filas={resultado['filas']} | "
                f"meses={resultado['meses']} | "
                f"duplicados={resultado['duplicados']} | "
                f"sha256={resultado['sha256']}"
            ),
        )

    escribir(
        log
    )

    escribir(
        log,
        "AUDITORÍAS",
    )

    resultados_auditoria = {}

    for clave, ruta in [
        (
            "Y",
            AUDITORIA_Y,
        ),
        (
            "X1",
            AUDITORIA_X1,
        ),
        (
            "X2",
            AUDITORIA_X2,
        ),
        (
            "X3",
            AUDITORIA_X3,
        ),
    ]:

        resultado = (
            validar_auditoria(
                clave,
                ruta,
            )
        )

        resultados_auditoria[
            clave
        ] = resultado

        escribir(
            log,
            (
                f"{clave}: "
                f"meses_auditados="
                f"{resultado['filas_auditoria']} | "
                f"estados="
                f"{resultado['estados']} | "
                f"sha256="
                f"{resultado['sha256']}"
            ),
        )

    escribir(
        log
    )

    escribir(
        log,
        "DATOS CRUDOS",
    )

    crudos_excel = (
        validar_crudos_excel()
    )

    crudos_html = (
        validar_crudos_html()
    )

    escribir(
        log,
        (
            "Y B-2359: "
            f"{crudos_excel['Y']} "
            "meses con archivo crudo."
        ),
    )

    escribir(
        log,
        (
            "X1 B-2318: "
            f"{crudos_excel['X1']} "
            "meses con archivo crudo."
        ),
    )

    escribir(
        log,
        (
            "X2 Consumo MN: "
            f"{crudos_html['X2']} "
            "HTML crudos reconocidos; "
            "cobertura mensual=122."
        ),
    )

    escribir(
        log,
        (
            "X3 Ahorro MN: "
            f"{crudos_html['X3']} "
            "HTML crudos reconocidos; "
            "cobertura mensual=122."
        ),
    )

    return {
        "csv":
            resultados_csv,
        "auditoria":
            resultados_auditoria,
    }


# ============================================================
# 22. MOSTRAR METODOLOGÍA EN EL LOG
# ============================================================

def registrar_metodologia(
    log,
):

    escribir(
        log,
        "FUENTES Y PROCEDIMIENTOS",
    )

    escribir(
        log,
        "-" * 100,
    )

    for clave in [
        "Y",
        "X1",
        "X2",
        "X3",
    ]:

        fuente = FUENTES[
            clave
        ]

        escribir(
            log,
            f"{clave}:",
        )

        for campo, valor in (
            fuente.items()
        ):

            escribir(
                log,
                (
                    f"  {campo}: "
                    f"{valor}"
                ),
            )

        escribir(
            log
        )


# ============================================================
# 23. MAIN
# ============================================================

def main():

    CARPETA_PROCESADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    CARPETA_DIAGNOSTICOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # El log es acumulativo.
    #
    # Así una nueva ejecución no borra la evidencia
    # de ejecuciones anteriores.
    # --------------------------------------------------------

    with LOG_EJECUCION.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as log:

        escribir(
            log
        )

        escribir(
            log,
            "#" * 100,
        )

        escribir_evento(
            log,
            (
                "INICIO 02_SCRAPING_WEB "
                "- EXTRACCIÓN SBS OFICIAL"
            ),
        )

        escribir(
            log,
            (
                "Estudiante: "
                "BRICEÑO LEON CRYSTELL HIDEKI"
            ),
        )

        escribir(
            log,
            (
                "Código: "
                f"{CODIGO_ESTUDIANTE}"
            ),
        )

        escribir(
            log,
            (
                "Periodo: "
                f"{FECHA_INICIO} a {FECHA_CORTE}"
            ),
        )

        escribir(
            log,
            (
                "Meses esperados: "
                f"{MESES_ESPERADOS}"
            ),
        )

        escribir(
            log,
            (
                "Python: "
                f"{sys.version}"
            ),
        )

        escribir(
            log,
            "#" * 100,
        )

        registrar_metodologia(
            log
        )

        try:

            # =================================================
            # A. EJECUTAR LOS TRES MOTORES YA VALIDADOS
            # =================================================

            for etapa in ETAPAS:

                ejecutar_etapa(
                    etapa,
                    log,
                )

            # =================================================
            # B. VALIDACIÓN CENTRAL DEL 02 OFICIAL
            # =================================================

            resultados = (
                validar_resultado_total(
                    log
                )
            )

            # =================================================
            # C. RESUMEN FINAL
            # =================================================

            escribir(
                log
            )

            escribir(
                log,
                "=" * 100,
            )

            escribir(
                log,
                "RESUMEN FINAL 02_SCRAPING_WEB",
            )

            escribir(
                log,
                "=" * 100,
            )

            escribir(
                log,
                (
                    "Periodo validado: "
                    f"{FECHA_INICIO} "
                    f"a {FECHA_CORTE}"
                ),
            )

            escribir(
                log,
                (
                    "Meses validados: "
                    f"{MESES_ESPERADOS}"
                ),
            )

            escribir(
                log,
                (
                    "Y: "
                    f"{resultados['csv']['Y']['filas']} "
                    "filas."
                ),
            )

            escribir(
                log,
                (
                    "X1: "
                    f"{resultados['csv']['X1']['filas']} "
                    "filas."
                ),
            )

            escribir(
                log,
                (
                    "X2: "
                    f"{resultados['csv']['X2']['filas']} "
                    "filas."
                ),
            )

            escribir(
                log,
                (
                    "X3: "
                    f"{resultados['csv']['X3']['filas']} "
                    "filas."
                ),
            )

            escribir(
                log,
                (
                    "Duplicados mes + banco_original: "
                    "0 en Y, X1, X2 y X3."
                ),
            )

            escribir(
                log,
                (
                    "Auditorías: "
                    "122 meses DISPONIBLE "
                    "en Y, X1, X2 y X3."
                ),
            )

            escribir(
                log,
                (
                    "Crudos: cobertura completa "
                    "2015-11 a 2025-12."
                ),
            )

            escribir(
                log,
                (
                    "No se realizó homologación "
                    "bancaria en 02."
                ),
            )

            escribir(
                log,
                (
                    "No se realizó interpolación, "
                    "imputación ni extrapolación."
                ),
            )

            escribir(
                log,
                (
                    "03_limpieza_datos.py: "
                    "NO ejecutado."
                ),
            )

            escribir(
                log,
                (
                    "04_analisis.py: "
                    "NO ejecutado."
                ),
            )

            escribir(
                log
            )

            escribir_evento(
                log,
                (
                    "FIN 02_SCRAPING_WEB "
                    "- EJECUCIÓN COMPLETA"
                ),
            )

            escribir(
                log
            )

            escribir(
                log,
                (
                    "ESTADO = "
                    "EXTRACCION_SBS_COMPLETA_VALIDADA"
                ),
            )

        except Exception as error:

            escribir(
                log
            )

            escribir(
                log,
                "=" * 100,
            )

            escribir(
                log,
                "02_SCRAPING_WEB DETENIDO",
            )

            escribir(
                log,
                "=" * 100,
            )

            escribir_evento(
                log,
                (
                    "ERROR: "
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

            escribir(
                log,
                (
                    "ESTADO = "
                    "EXTRACCION_SBS_NO_VALIDADA"
                ),
            )

            # Repropagar:
            # el proceso oficial debe terminar
            # con código de error real.
            raise


# ============================================================
# 24. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()