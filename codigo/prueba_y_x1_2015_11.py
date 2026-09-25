# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from urllib.parse import urljoin, urlparse
from decimal import Decimal, ROUND_HALF_UP
import csv
import hashlib
import math
import re
import time
import unicodedata

import requests
from bs4 import BeautifulSoup
import xlrd
from openpyxl import load_workbook


# ============================================================
# 1. OBJETIVO DE ESTA PRUEBA
# ============================================================

"""
PRUEBA ÚNICA: 2015-11

Y:
    Dolarización del crédito (%)
    SBS B-2359
    Créditos Directos por Tipo, Modalidad y Moneda

X1:
    Dolarización de depósitos (%)
    SBS B-2318
    Movimiento de los Depósitos

IMPORTANTE:

- Solo se consulta 2015-11.
- No se recorren los 122 meses.
- No se homologan nombres históricos.
- No se seleccionan bancos.
- No se interpolan faltantes.
- Se conservan los nombres originales SBS.
- Los archivos crudos se conservan sin conversión.
- No se modifica datos_procesados.

CONTROL Y:
- La suma de bancos se calcula con math.fsum().
- NO se usa una abs_tol económica.
- Se lee la precisión mostrada por Excel
  en la celda TOTAL BANCA MÚLTIPLE.
- La comparación usa Decimal + ROUND_HALF_UP.
"""


# ============================================================
# 2. IDENTIFICACIÓN
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

YEAR = 2015
MONTH = 11

MES = "2015-11"


# ============================================================
# 3. TOLERANCIA EXISTENTE
#
# SE CONSERVA EXCLUSIVAMENTE PORQUE X1 DEBE
# QUEDAR SIN MODIFICACIONES.
#
# Y / B-2359 YA NO USA ESTAS TOLERANCIAS.
# ============================================================

REL_TOL = 1e-14
ABS_TOL = 1e-6


# ============================================================
# 4. FUENTES OFICIALES SBS
# ============================================================

URL_REPORTE = (
    "https://www.sbs.gob.pe/app/stats_net/stats/"
    "EstadisticaSistemaFinancieroResultados.aspx?c={codigo}"
)

REPORTES = {

    "Y": {
        "clave": "creditos",
        "codigo": "B-2359",
        "nombre": (
            "Créditos Directos por Tipo, "
            "Modalidad y Moneda"
        ),
    },

    "X1": {
        "clave": "depositos",
        "codigo": "B-2318",
        "nombre": "Movimiento de los Depósitos",
    },
}


# ============================================================
# 5. CÓDIGOS DE MES SBS
# ============================================================

CODIGO_MES = {
    1: "en",
    2: "fe",
    3: "ma",
    4: "ab",
    5: "my",
    6: "jn",
    7: "jl",
    8: "ag",
    9: "se",
    10: "oc",
    11: "no",
    12: "di",
}


# ============================================================
# 6. RUTAS
# ============================================================

RAIZ = Path(
    __file__
).resolve().parent.parent


CARPETA_CRUDOS = (
    RAIZ
    / "datos_crudos"
    / "prueba_Y_X1_2015_11"
)


CARPETA_DIAGNOSTICOS = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)


CARPETA_CRUDOS.mkdir(
    parents=True,
    exist_ok=True
)


CARPETA_DIAGNOSTICOS.mkdir(
    parents=True,
    exist_ok=True
)


ARCHIVO_CREDITO = (
    CARPETA_CRUDOS
    / (
        f"Y_B-2359_"
        f"{YEAR}_{MONTH:02d}_"
        f"{CODIGO_ESTUDIANTE}.xls"
    )
)


ARCHIVO_DEPOSITOS = (
    CARPETA_CRUDOS
    / (
        f"X1_B-2318_"
        f"{YEAR}_{MONTH:02d}_"
        f"{CODIGO_ESTUDIANTE}.xls"
    )
)


CSV_Y = (
    CARPETA_DIAGNOSTICOS
    / "prueba_Y_dolcred_2015_11.csv"
)


CSV_X1 = (
    CARPETA_DIAGNOSTICOS
    / "prueba_X1_doldep_2015_11.csv"
)


TXT_RESULTADO = (
    CARPETA_DIAGNOSTICOS
    / "prueba_Y_X1_2015_11.txt"
)


# ============================================================
# 7. SESIÓN HTTP
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; TrabajoAcademicoUNCP/1.0; "
        "Finanzas-I; "
        "2024200485D)"
    )

})


# ============================================================
# 8. SALIDA TXT
# ============================================================

lineas_reporte = []


def escribir(texto=""):

    texto = str(
        texto
    )

    print(
        texto
    )

    lineas_reporte.append(
        texto
    )


def titulo(texto):

    escribir()
    escribir("=" * 110)
    escribir(texto)
    escribir("=" * 110)


def subtitulo(texto):

    escribir()
    escribir("-" * 110)
    escribir(texto)
    escribir("-" * 110)


# ============================================================
# 9. UTILIDADES DE TEXTO
# ============================================================

def normalizar_texto(valor):
    """
    Normalización ligera usada por
    los parsers validados.

    NO se utiliza para modificar
    banco_original.
    """

    if valor is None:
        return ""

    texto = str(
        valor
    )

    texto = texto.replace(
        "\n",
        " "
    )

    texto = texto.replace(
        "\r",
        " "
    )

    texto = texto.replace(
        "\xa0",
        " "
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip().lower()


def normalizar_comparacion(valor):
    """
    Normalización usada exclusivamente
    para emparejar MN y ME dentro del
    MISMO archivo B-2318.

    NO es homologación histórica.

    El nombre SBS original permanece
    guardado por separado.
    """

    texto = normalizar_texto(
        valor
    )

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(
            caracter
        )
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def sin_tildes(valor):

    return normalizar_comparacion(
        valor
    )


# ============================================================
# 10. CONVERTIR NÚMEROS
# ============================================================

def convertir_numero(valor):

    if valor is None:
        return None

    if isinstance(
        valor,
        (int, float)
    ):

        return float(
            valor
        )

    texto = str(
        valor
    ).strip()

    if texto == "":
        return None

    if texto.lower() in {
        "-",
        "s.i.",
        "s.i",
        "n.d.",
        "n.d",
        "nd",
        "n/a",
        "na",
    }:

        return None

    try:

        return float(
            texto.replace(
                ",",
                ""
            )
        )

    except ValueError:

        return None


# ============================================================
# 11. CONTROL NUMÉRICO ORIGINAL
#
# SE MANTIENE PARA X1 SIN MODIFICACIONES.
# Y NO UTILIZA ESTA FUNCIÓN.
# ============================================================

def comparar_con_total_sbs(
    nombre_control,
    suma_bancos,
    total_sbs
):

    diferencia = (
        suma_bancos
        -
        total_sbs
    )

    diferencia_absoluta = abs(
        diferencia
    )

    coincide = math.isclose(
        suma_bancos,
        total_sbs,
        rel_tol=REL_TOL,
        abs_tol=ABS_TOL
    )

    estado = (
        "OK"
        if coincide
        else "ERROR"
    )

    return {
        "control":
            nombre_control,

        "suma_bancos":
            suma_bancos,

        "total_sbs":
            total_sbs,

        "diferencia":
            diferencia,

        "diferencia_absoluta":
            diferencia_absoluta,

        "estado":
            estado,
    }


def registrar_control_total(
    control
):

    escribir(
        f"Control: {control['control']}"
    )

    escribir(
        f"  Suma bancos = "
        f"{control['suma_bancos']}"
    )

    escribir(
        f"  Total SBS = "
        f"{control['total_sbs']}"
    )

    escribir(
        f"  Diferencia absoluta = "
        f"{control['diferencia_absoluta']}"
    )

    escribir(
        f"  Resultado = "
        f"{control['estado']}"
    )


# ============================================================
# 12. CONSULTAR PÁGINA DEL REPORTE
# ============================================================

def consultar_reporte(
    codigo
):

    url = URL_REPORTE.format(
        codigo=codigo
    )

    respuesta = session.get(
        url,
        timeout=45
    )

    respuesta.raise_for_status()

    soup = BeautifulSoup(
        respuesta.text,
        "lxml"
    )

    return (
        url,
        soup,
        respuesta.status_code,
    )


# ============================================================
# 13. LOCALIZAR ENLACES XLS
# ============================================================

def localizar_enlaces_xls(
    url_pagina,
    soup
):

    enlaces = []

    urls_vistas = set()

    for enlace in soup.find_all(
        "a",
        href=True
    ):

        href = enlace.get(
            "href",
            ""
        ).strip()

        if ".xls" not in href.lower():
            continue

        url_xls = urljoin(
            url_pagina,
            href
        )

        if url_xls in urls_vistas:
            continue

        urls_vistas.add(
            url_xls
        )

        enlaces.append({
            "texto":
                enlace.get_text(
                    " ",
                    strip=True
                ),

            "href_original":
                href,

            "url":
                url_xls,
        })

    return enlaces


# ============================================================
# 14. IDENTIFICADOR SBS DEL MES
# ============================================================

def identificador_mes(
    codigo_reporte,
    year,
    month
):

    codigo_mes = CODIGO_MES[
        month
    ]

    return (
        f"{codigo_reporte}-"
        f"{codigo_mes}{year}"
    ).lower()


# ============================================================
# 15. BUSCAR EL XLS DEL MES
# ============================================================

def buscar_mes(
    enlaces,
    codigo_reporte,
    year,
    month
):

    esperado = identificador_mes(
        codigo_reporte,
        year,
        month
    )

    coincidencias = []

    for item in enlaces:

        contenido = (
            item[
                "url"
            ]
            + " "
            + item[
                "href_original"
            ]
        ).lower()

        if esperado in contenido:

            coincidencias.append(
                item
            )

    return coincidencias


# ============================================================
# 16. LOCALIZAR ARCHIVO OFICIAL
# ============================================================

def localizar_archivo_oficial(
    configuracion
):

    codigo = configuracion[
        "codigo"
    ]

    nombre = configuracion[
        "nombre"
    ]

    url_pagina, soup, http = (
        consultar_reporte(
            codigo
        )
    )

    escribir(
        f"Página oficial: {url_pagina}"
    )

    escribir(
        f"HTTP página: {http}"
    )

    texto_pagina = sin_tildes(
        soup.get_text(
            " ",
            strip=True
        )
    )

    if codigo == "B-2359":

        controles = [
            "creditos",
            "modalidad",
            "moneda",
        ]

    elif codigo == "B-2318":

        controles = [
            "movimiento",
            "depositos",
        ]

    else:

        controles = []

    encontrados = [
        palabra
        for palabra in controles
        if palabra in texto_pagina
    ]

    escribir(
        "Palabras de control encontradas: "
        f"{encontrados}"
    )

    if (
        controles
        and
        len(
            encontrados
        )
        == 0
    ):

        raise RuntimeError(
            "La página obtenida no contiene "
            f"evidencia del reporte esperado: {nombre}"
        )

    enlaces = localizar_enlaces_xls(
        url_pagina,
        soup
    )

    coincidencias = buscar_mes(
        enlaces,
        codigo,
        YEAR,
        MONTH
    )

    esperado = identificador_mes(
        codigo,
        YEAR,
        MONTH
    )

    escribir(
        f"Identificador esperado: {esperado}"
    )

    escribir(
        f"Coincidencias encontradas: "
        f"{len(coincidencias)}"
    )

    for coincidencia in coincidencias:

        escribir(
            "  -> "
            + coincidencia[
                "url"
            ]
        )

    if len(
        coincidencias
    ) != 1:

        raise RuntimeError(
            f"{codigo}: se esperaba exactamente "
            "un archivo para 2015-11 y se "
            f"encontraron {len(coincidencias)}."
        )

    return coincidencias[
        0
    ]


# ============================================================
# 17. DESCARGAR ARCHIVO CRUDO
# ============================================================

def descargar_archivo(
    url,
    destino
):

    respuesta = session.get(
        url,
        timeout=60
    )

    respuesta.raise_for_status()

    contenido = respuesta.content

    content_type = respuesta.headers.get(
        "Content-Type",
        ""
    )

    inicio = contenido[
        :300
    ].lower()

    if (
        b"<html" in inicio
        or
        b"<!doctype html" in inicio
    ):

        raise RuntimeError(
            "La SBS devolvió HTML "
            "en lugar del archivo Excel."
        )

    temporal = destino.with_suffix(
        destino.suffix
        + ".tmp"
    )

    with temporal.open(
        "wb"
    ) as archivo:

        archivo.write(
            contenido
        )

    temporal.replace(
        destino
    )

    sha256 = hashlib.sha256(
        contenido
    ).hexdigest()

    nombre_origen = Path(
        urlparse(
            url
        ).path
    ).name

    return {
        "http":
            respuesta.status_code,

        "content_type":
            content_type,

        "bytes":
            len(
                contenido
            ),

        "sha256":
            sha256,

        "nombre_origen":
            nombre_origen,

        "ruta":
            destino,
    }


# ============================================================
# 18. DETECTAR FORMATO REAL
# ============================================================

def detectar_formato(
    ruta
):

    with ruta.open(
        "rb"
    ) as archivo:

        cabecera = archivo.read(
            8
        )

    firma_ole = bytes.fromhex(
        "D0CF11E0A1B11AE1"
    )

    firmas_zip = (
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
    )

    if cabecera == firma_ole:

        return "XLS_OLE"

    if cabecera.startswith(
        firmas_zip
    ):

        return "XLSX_ZIP"

    return "DESCONOCIDO"


# ============================================================
# 19. LEER XLS/OLE
# ============================================================

def leer_xls(
    ruta
):

    libro = xlrd.open_workbook(
        filename=str(
            ruta
        ),
        on_demand=True
    )

    hojas = []

    for nombre in libro.sheet_names():

        hoja = libro.sheet_by_name(
            nombre
        )

        filas = []

        for i in range(
            hoja.nrows
        ):

            fila = [
                hoja.cell_value(
                    i,
                    j
                )
                for j in range(
                    hoja.ncols
                )
            ]

            filas.append(
                fila
            )

        hojas.append({
            "nombre":
                nombre,

            "filas":
                filas,
        })

    libro.release_resources()

    return hojas


# ============================================================
# 20. LEER XLSX/ZIP
# ============================================================

def leer_xlsx(
    ruta
):

    with ruta.open(
        "rb"
    ) as archivo_binario:

        libro = load_workbook(
            archivo_binario,
            read_only=True,
            data_only=True
        )

        hojas = []

        for nombre in libro.sheetnames:

            hoja = libro[
                nombre
            ]

            filas = [
                list(
                    fila
                )
                for fila in hoja.iter_rows(
                    values_only=True
                )
            ]

            hojas.append({
                "nombre":
                    nombre,

                "filas":
                    filas,
            })

        libro.close()

    return hojas


# ============================================================
# 21. LEER EXCEL SBS
# ============================================================

def leer_archivo(
    ruta
):

    formato = detectar_formato(
        ruta
    )

    if formato == "XLS_OLE":

        hojas = leer_xls(
            ruta
        )

    elif formato == "XLSX_ZIP":

        hojas = leer_xlsx(
            ruta
        )

    else:

        raise RuntimeError(
            "Formato binario no reconocido: "
            f"{ruta.name}"
        )

    return (
        formato,
        hojas,
    )


# ============================================================
# PARTE A
# Y = DOLARIZACIÓN DEL CRÉDITO
# SBS B-2359
# ============================================================


# ============================================================
# 22. RECONOCER MN / ME / TOTAL
# ============================================================

def es_mn(
    valor
):

    texto = normalizar_texto(
        valor
    )

    return (
        texto.startswith(
            "mn"
        )
        and
        "mil" in texto
    )


def es_me(
    valor
):

    texto = normalizar_texto(
        valor
    )

    return (
        texto.startswith(
            "me"
        )
        and
        "mil" in texto
    )


def es_total(
    valor
):

    texto = normalizar_texto(
        valor
    )

    return texto.startswith(
        "total"
    )


# ============================================================
# 23. ENCONTRAR FILA DE ENCABEZADOS CREDITICIOS
# ============================================================

def encontrar_fila_encabezados_creditos(
    filas
):

    candidatos = []

    for numero_fila, fila in enumerate(
        filas
    ):

        bloques = []

        for columna in range(
            max(
                0,
                len(fila) - 2
            )
        ):

            if (
                es_mn(
                    fila[
                        columna
                    ]
                )
                and
                es_me(
                    fila[
                        columna + 1
                    ]
                )
                and
                es_total(
                    fila[
                        columna + 2
                    ]
                )
            ):

                bloques.append(
                    columna
                )

        if bloques:

            candidatos.append({
                "fila":
                    numero_fila,

                "bloques":
                    bloques,
            })

    if not candidatos:

        return None

    return max(
        candidatos,
        key=lambda x:
        len(
            x[
                "bloques"
            ]
        )
    )


# ============================================================
# 24. OBTENER NOMBRE ORIGINAL DEL BANCO
# ============================================================

def obtener_nombre_banco_creditos(
    filas,
    fila_bancos,
    columna_inicio
):

    if (
        fila_bancos < 0
        or
        fila_bancos >= len(
            filas
        )
    ):

        return ""

    fila = filas[
        fila_bancos
    ]

    for desplazamiento in (
        0,
        1,
        2,
    ):

        columna = (
            columna_inicio
            +
            desplazamiento
        )

        if columna >= len(
            fila
        ):
            continue

        valor = fila[
            columna
        ]

        if normalizar_texto(
            valor
        ):

            return str(
                valor
            ).strip()

    return ""


# ============================================================
# 25. DETECTAR ESTRUCTURA DE CRÉDITOS
# ============================================================

def detectar_estructura_creditos(
    filas
):

    encabezado = encontrar_fila_encabezados_creditos(
        filas
    )

    if encabezado is None:

        return None

    fila_encabezados = encabezado[
        "fila"
    ]

    fila_bancos = (
        fila_encabezados
        -
        1
    )

    bloques = []

    for columna_inicio in encabezado[
        "bloques"
    ]:

        banco = obtener_nombre_banco_creditos(
            filas,
            fila_bancos,
            columna_inicio
        )

        bloques.append({
            "banco_original":
                banco,

            "columna_mn":
                columna_inicio,

            "columna_me":
                columna_inicio + 1,

            "columna_total":
                columna_inicio + 2,
        })

    return {
        "fila_bancos":
            fila_bancos,

        "fila_encabezados":
            fila_encabezados,

        "bloques":
            bloques,
    }


# ============================================================
# 26. ELEGIR HOJA PRINCIPAL B-2359
# ============================================================

def elegir_hoja_principal_creditos(
    hojas
):

    candidatos = []

    for hoja in hojas:

        estructura = detectar_estructura_creditos(
            hoja[
                "filas"
            ]
        )

        if estructura is None:
            continue

        candidatos.append({
            "hoja":
                hoja,

            "estructura":
                estructura,
        })

    if not candidatos:

        return None

    return max(
        candidatos,
        key=lambda x:
        len(
            x[
                "estructura"
            ][
                "bloques"
            ]
        )
    )


# ============================================================
# 27. BUSCAR "TOTAL CRÉDITOS:"
# ============================================================

def buscar_fila_total_creditos(
    filas
):

    for numero_fila, fila in enumerate(
        filas
    ):

        for valor in fila:

            texto = sin_tildes(
                valor
            )

            if (
                "total creditos"
                in texto
            ):

                return numero_fila

    return None


# ============================================================
# 28. IDENTIFICAR TOTAL BANCA MÚLTIPLE
# ============================================================

def es_agregado_creditos(
    nombre
):

    texto = sin_tildes(
        nombre
    )

    return (
        "total banca multiple"
        in texto
    )


# ============================================================
# 29. EXTRAER Y
#
# PARSER Y DOLCRED SIN CAMBIOS.
# ============================================================

def extraer_y_creditos(
    ruta
):

    formato, hojas = leer_archivo(
        ruta
    )

    seleccionado = elegir_hoja_principal_creditos(
        hojas
    )

    if seleccionado is None:

        raise RuntimeError(
            "B-2359: no se encontró "
            "la estructura MN|ME|Total."
        )

    hoja = seleccionado[
        "hoja"
    ]

    estructura = seleccionado[
        "estructura"
    ]

    filas = hoja[
        "filas"
    ]

    fila_total = buscar_fila_total_creditos(
        filas
    )

    if fila_total is None:

        raise RuntimeError(
            "B-2359: no se encontró "
            "la fila 'Total Créditos:'."
        )

    fila = filas[
        fila_total
    ]

    registros = []

    for bloque in estructura[
        "bloques"
    ]:

        banco = bloque[
            "banco_original"
        ]

        col_mn = bloque[
            "columna_mn"
        ]

        col_me = bloque[
            "columna_me"
        ]

        col_total = bloque[
            "columna_total"
        ]

        mn = (
            convertir_numero(
                fila[
                    col_mn
                ]
            )
            if col_mn < len(
                fila
            )
            else None
        )

        me = (
            convertir_numero(
                fila[
                    col_me
                ]
            )
            if col_me < len(
                fila
            )
            else None
        )

        total = (
            convertir_numero(
                fila[
                    col_total
                ]
            )
            if col_total < len(
                fila
            )
            else None
        )

        problemas = []

        if not banco:

            problemas.append(
                "BANCO_SIN_NOMBRE"
            )

        if mn is None:

            problemas.append(
                "MN_FALTANTE"
            )

        if me is None:

            problemas.append(
                "ME_FALTANTE"
            )

        if total is None:

            problemas.append(
                "TOTAL_FALTANTE"
            )

        if (
            mn is not None
            and
            mn < 0
        ):

            problemas.append(
                "MN_NEGATIVO"
            )

        if (
            me is not None
            and
            me < 0
        ):

            problemas.append(
                "ME_NEGATIVO"
            )

        if (
            total is not None
            and
            total <= 0
        ):

            problemas.append(
                "TOTAL_NO_POSITIVO"
            )

        componente_me_soles = None
        dolcred = None
        tc_implicito = None

        if (
            mn is not None
            and
            total is not None
        ):

            if total < mn:

                problemas.append(
                    "TOTAL_MENOR_QUE_MN"
                )

            componente_me_soles = (
                total
                -
                mn
            )

        # ====================================================
        # FÓRMULA DOLCRED VALIDADA - SIN CAMBIOS
        # ====================================================

        if (
            total is not None
            and
            total > 0
            and
            mn is not None
        ):

            dolcred = (
                (
                    total
                    -
                    mn
                )
                /
                total
                *
                100
            )

            if not (
                0
                <=
                dolcred
                <=
                100
            ):

                problemas.append(
                    "DOLCRED_FUERA_RANGO"
                )

        if (
            mn is not None
            and
            me is not None
            and
            total is not None
            and
            me > 0
        ):

            tc_implicito = (
                (
                    total
                    -
                    mn
                )
                /
                me
            )

            if tc_implicito <= 0:

                problemas.append(
                    "TC_NO_POSITIVO"
                )

        agregado = es_agregado_creditos(
            banco
        )

        registros.append({
            "mes":
                MES,

            "archivo":
                ruta.name,

            "formato":
                formato,

            "hoja":
                hoja[
                    "nombre"
                ],

            "fila_total_creditos":
                fila_total,

            "banco_original":
                banco,

            "mn_soles_miles":
                mn,

            "me_usd_miles":
                me,

            "total_soles_miles":
                total,

            "componente_me_soles":
                componente_me_soles,

            "tc_implicito":
                tc_implicito,

            "dolcred_pct":
                dolcred,

            "es_agregado":
                agregado,

            "problemas":
                problemas,
        })

    return {
        "formato":
            formato,

        "hoja":
            hoja[
                "nombre"
            ],

        "fila_encabezados":
            estructura[
                "fila_encabezados"
            ],

        "fila_bancos":
            estructura[
                "fila_bancos"
            ],

        "fila_total_creditos":
            fila_total,

        "cantidad_bloques":
            len(
                estructura[
                    "bloques"
                ]
            ),

        "registros":
            registros,
    }


# ============================================================
# 30. INFERIR DECIMALES DEL FORMATO EXCEL
#
# NUEVO CONTROL EXCLUSIVO PARA Y.
# ============================================================

def inferir_decimales_formato_excel(
    formato
):

    if formato is None:

        return None

    texto = str(
        formato
    ).strip()

    if not texto:

        return None

    if texto.lower() == "general":

        return None

    # Primera sección:
    # positivo;negativo;cero;texto
    seccion = texto.split(
        ";"
    )[0]

    # Retirar textos literales.
    seccion = re.sub(
        r'"[^"]*"',
        "",
        seccion
    )

    # Retirar condiciones y colores.
    seccion = re.sub(
        r"\[[^\]]*\]",
        "",
        seccion
    )

    coincidencia = re.search(
        r"\.([0#?]+)",
        seccion
    )

    if coincidencia:

        return len(
            coincidencia.group(1)
        )

    # Existe formato numérico pero sin
    # parte decimal visible.
    if re.search(
        r"[0#?]",
        seccion
    ):

        return 0

    return None


# ============================================================
# 31. REDONDEO TIPO EXCEL
#
# Decimal + ROUND_HALF_UP
# ============================================================

def redondear_excel_half_up(
    valor,
    decimales
):

    if valor is None:

        raise ValueError(
            "No puede redondearse un valor None."
        )

    if decimales is None:

        raise ValueError(
            "No se conoce el número de decimales."
        )

    if decimales < 0:

        raise ValueError(
            "Número de decimales inválido."
        )

    numero = Decimal(
        str(
            valor
        )
    )

    if decimales == 0:

        cuantizador = Decimal(
            "1"
        )

    else:

        cuantizador = Decimal(
            "1"
        ).scaleb(
            -decimales
        )

    return numero.quantize(
        cuantizador,
        rounding=ROUND_HALF_UP
    )


# ============================================================
# 32. LOCALIZAR EL BLOQUE TOTAL BANCA MÚLTIPLE
#
# Reutiliza la estructura ya detectada.
# NO modifica el parser.
# ============================================================

def localizar_bloque_agregado_y(
    ruta,
    resultado
):

    formato, hojas = leer_archivo(
        ruta
    )

    seleccionado = elegir_hoja_principal_creditos(
        hojas
    )

    if seleccionado is None:

        raise RuntimeError(
            "B-2359: no pudo recuperarse "
            "la estructura para inspeccionar "
            "el formato del agregado."
        )

    hoja = seleccionado[
        "hoja"
    ]

    estructura = seleccionado[
        "estructura"
    ]

    if (
        hoja[
            "nombre"
        ]
        !=
        resultado[
            "hoja"
        ]
    ):

        raise RuntimeError(
            "B-2359: la hoja detectada para "
            "inspeccionar el agregado no coincide "
            "con la hoja usada por el parser."
        )

    agregados = [
        bloque
        for bloque in estructura[
            "bloques"
        ]
        if es_agregado_creditos(
            bloque[
                "banco_original"
            ]
        )
    ]

    if len(
        agregados
    ) != 1:

        raise RuntimeError(
            "B-2359: no pudo localizarse "
            "exactamente un bloque "
            "Total Banca Múltiple para "
            "inspeccionar su formato Excel."
        )

    return agregados[
        0
    ]


# ============================================================
# 33. LEER FORMATO AGREGADO Y - XLS/OLE
# ============================================================

def leer_formato_agregado_y_xls(
    ruta,
    resultado,
    bloque_agregado
):

    try:

        libro = xlrd.open_workbook(
            filename=str(
                ruta
            ),
            formatting_info=True,
            on_demand=True
        )

    except Exception as error:

        raise RuntimeError(
            "B-2359: xlrd no pudo abrir el XLS "
            "con formatting_info=True."
        ) from error

    try:

        hoja = libro.sheet_by_name(
            resultado[
                "hoja"
            ]
        )

        fila = resultado[
            "fila_total_creditos"
        ]

        salida = {}

        for variable, columna in (
            (
                "MN",
                bloque_agregado[
                    "columna_mn"
                ]
            ),
            (
                "ME",
                bloque_agregado[
                    "columna_me"
                ]
            ),
            (
                "TOTAL",
                bloque_agregado[
                    "columna_total"
                ]
            ),
        ):

            celda = hoja.cell(
                fila,
                columna
            )

            try:

                xf_index = hoja.cell_xf_index(
                    fila,
                    columna
                )

            except Exception as error:

                raise RuntimeError(
                    f"B-2359 {variable}: no pudo "
                    "obtenerse xf_index de la "
                    "celda agregada."
                ) from error

            if (
                xf_index is None
                or
                xf_index < 0
                or
                xf_index >= len(
                    libro.xf_list
                )
            ):

                raise RuntimeError(
                    f"B-2359 {variable}: xf_index "
                    "inválido para la celda agregada."
                )

            xf = libro.xf_list[
                xf_index
            ]

            format_key = getattr(
                xf,
                "format_key",
                None
            )

            if format_key is None:

                raise RuntimeError(
                    f"B-2359 {variable}: no pudo "
                    "determinarse format_key."
                )

            formato_obj = libro.format_map.get(
                format_key
            )

            if formato_obj is None:

                raise RuntimeError(
                    f"B-2359 {variable}: no pudo "
                    "recuperarse el formato Excel "
                    "desde format_key={format_key}."
                )

            format_str = getattr(
                formato_obj,
                "format_str",
                None
            )

            decimales = inferir_decimales_formato_excel(
                format_str
            )

            if (
                format_str is None
                or
                decimales is None
            ):

                raise RuntimeError(
                    f"B-2359 {variable}: no puede "
                    "determinarse de forma segura "
                    "la precisión mostrada del "
                    "Total Banca Múltiple. "
                    f"format_str={format_str!r}"
                )

            salida[
                variable
            ] = {
                "valor_raw_celda":
                    celda.value,

                "valor_raw_celda_repr":
                    repr(
                        celda.value
                    ),

                "xf_index":
                    xf_index,

                "format_key":
                    format_key,

                "format_str":
                    format_str,

                "decimales_mostrados":
                    decimales,
            }

        return salida

    finally:

        libro.release_resources()


# ============================================================
# 34. LEER FORMATO AGREGADO Y - XLSX/ZIP
# ============================================================

def leer_formato_agregado_y_xlsx(
    ruta,
    resultado,
    bloque_agregado
):

    try:

        with ruta.open(
            "rb"
        ) as archivo_binario:

            libro = load_workbook(
                archivo_binario,
                read_only=False,
                data_only=True
            )

            try:

                hoja = libro[
                    resultado[
                        "hoja"
                    ]
                ]

                fila = (
                    resultado[
                        "fila_total_creditos"
                    ]
                    +
                    1
                )

                salida = {}

                for variable, columna_0based in (
                    (
                        "MN",
                        bloque_agregado[
                            "columna_mn"
                        ]
                    ),
                    (
                        "ME",
                        bloque_agregado[
                            "columna_me"
                        ]
                    ),
                    (
                        "TOTAL",
                        bloque_agregado[
                            "columna_total"
                        ]
                    ),
                ):

                    celda = hoja.cell(
                        row=fila,
                        column=columna_0based + 1
                    )

                    format_str = (
                        celda.number_format
                    )

                    decimales = (
                        inferir_decimales_formato_excel(
                            format_str
                        )
                    )

                    if (
                        format_str is None
                        or
                        decimales is None
                    ):

                        raise RuntimeError(
                            f"B-2359 {variable}: no puede "
                            "determinarse de forma segura "
                            "la precisión mostrada del "
                            "Total Banca Múltiple. "
                            f"format_str={format_str!r}"
                        )

                    salida[
                        variable
                    ] = {
                        "valor_raw_celda":
                            celda.value,

                        "valor_raw_celda_repr":
                            repr(
                                celda.value
                            ),

                        "xf_index":
                            celda.style_id,

                        "format_key":
                            "",

                        "format_str":
                            format_str,

                        "decimales_mostrados":
                            decimales,
                    }

                return salida

            finally:

                libro.close()

    except RuntimeError:

        raise

    except Exception as error:

        raise RuntimeError(
            "B-2359: no pudo inspeccionarse "
            "el formato XLSX del agregado."
        ) from error


# ============================================================
# 35. LEER FORMATO REAL DE TOTAL BANCA MÚLTIPLE
#
# SOLO PARA EL CONTROL Y.
# ============================================================

def obtener_formatos_agregado_y(
    ruta,
    resultado
):

    bloque_agregado = localizar_bloque_agregado_y(
        ruta,
        resultado
    )

    formato = resultado[
        "formato"
    ]

    if formato == "XLS_OLE":

        return leer_formato_agregado_y_xls(
            ruta,
            resultado,
            bloque_agregado
        )

    if formato == "XLSX_ZIP":

        return leer_formato_agregado_y_xlsx(
            ruta,
            resultado,
            bloque_agregado
        )

    raise RuntimeError(
        "B-2359: formato no compatible con "
        "la inspección de precisión Excel."
    )


# ============================================================
# 36. CONTROL TOTAL BANCA MÚLTIPLE - Y
#
# NUEVA REGLA:
#
#   1. math.fsum()
#   2. total raw SBS
#   3. diferencia absoluta/raw
#   4. diferencia relativa/raw
#   5. formato Excel del agregado
#   6. decimales mostrados
#   7. Decimal + ROUND_HALF_UP
#
# NO USA abs_tol.
# NO USA math.isclose().
# ============================================================

def validar_agregado_creditos(
    ruta,
    resultado,
    registros
):

    agregados = [
        registro
        for registro in registros
        if registro[
            "es_agregado"
        ]
    ]

    bancos = [
        registro
        for registro in registros
        if not registro[
            "es_agregado"
        ]
    ]

    if len(
        agregados
    ) != 1:

        raise RuntimeError(
            "B-2359: se esperaba exactamente "
            "un 'Total Banca Múltiple'."
        )

    agregado = agregados[
        0
    ]

    formatos = obtener_formatos_agregado_y(
        ruta,
        resultado
    )

    configuracion = [
        (
            "MN",
            "mn_soles_miles"
        ),
        (
            "ME",
            "me_usd_miles"
        ),
        (
            "TOTAL",
            "total_soles_miles"
        ),
    ]

    controles = []

    subtitulo(
        "CONTROL TOTAL BANCA MÚLTIPLE - Y / B-2359"
    )

    escribir(
        f"Cantidad de bancos individuales = "
        f"{len(bancos)}"
    )

    for variable, campo in configuracion:

        valores = [
            registro[
                campo
            ]
            for registro in bancos
        ]

        bancos_faltantes = [
            registro[
                "banco_original"
            ]
            for registro in bancos
            if registro[
                campo
            ]
            is None
        ]

        if bancos_faltantes:

            raise RuntimeError(
                f"B-2359 {variable}: no puede "
                "realizarse el control agregado "
                "porque existen valores faltantes: "
                f"{bancos_faltantes}"
            )

        total_sbs = agregado[
            campo
        ]

        if total_sbs is None:

            raise RuntimeError(
                f"B-2359 {variable}: la celda "
                "Total Banca Múltiple está vacía."
            )

        # ====================================================
        # SUMA ROBUSTA
        # ====================================================

        suma_bancos = math.fsum(
            valores
        )

        # ====================================================
        # DIFERENCIAS RAW
        # ====================================================

        diferencia_raw = (
            suma_bancos
            -
            total_sbs
        )

        diferencia_absoluta_raw = abs(
            diferencia_raw
        )

        if total_sbs != 0:

            diferencia_relativa_raw = (
                diferencia_absoluta_raw
                /
                abs(
                    total_sbs
                )
            )

        else:

            diferencia_relativa_raw = None

        metadata = formatos[
            variable
        ]

        format_str = metadata[
            "format_str"
        ]

        decimales = metadata[
            "decimales_mostrados"
        ]

        if (
            format_str is None
            or
            decimales is None
        ):

            raise RuntimeError(
                f"B-2359 {variable}: "
                "no puede determinarse la "
                "precisión mostrada del agregado. "
                "Se requiere revisión manual."
            )

        # ====================================================
        # CONTROL ADICIONAL:
        # VALOR RAW LEÍDO PARA METADATOS
        # ====================================================

        valor_raw_celda = metadata[
            "valor_raw_celda"
        ]

        valor_raw_celda_numerico = convertir_numero(
            valor_raw_celda
        )

        if valor_raw_celda_numerico is None:

            raise RuntimeError(
                f"B-2359 {variable}: el valor raw "
                "de la celda agregada no pudo "
                "interpretarse numéricamente."
            )

        # Debe ser el mismo valor que ya usó
        # el parser. No se usa tolerancia económica.
        if (
            Decimal(
                str(
                    valor_raw_celda_numerico
                )
            )
            !=
            Decimal(
                str(
                    total_sbs
                )
            )
        ):

            raise RuntimeError(
                f"B-2359 {variable}: el valor raw "
                "de la celda Total Banca Múltiple "
                "no coincide con el valor utilizado "
                "por el parser. "
                f"parser={total_sbs!r}; "
                f"raw={valor_raw_celda!r}"
            )

        # ====================================================
        # REDONDEO A PRECISIÓN MOSTRADA
        #
        # NO usar round() de Python.
        # Se usa ROUND_HALF_UP.
        # ====================================================

        suma_redondeada = redondear_excel_half_up(
            suma_bancos,
            decimales
        )

        total_redondeado = redondear_excel_half_up(
            total_sbs,
            decimales
        )

        coincide_precision_mostrada = (
            suma_redondeada
            ==
            total_redondeado
        )

        estado = (
            "OK"
            if coincide_precision_mostrada
            else "ERROR"
        )

        control = {
            "control":
                f"Y / B-2359 / {variable}",

            "variable":
                variable,

            "cantidad_bancos":
                len(
                    bancos
                ),

            "suma_fsum":
                suma_bancos,

            "total_sbs_raw":
                total_sbs,

            "valor_raw_celda":
                valor_raw_celda,

            "diferencia_raw":
                diferencia_raw,

            "diferencia_absoluta_raw":
                diferencia_absoluta_raw,

            "diferencia_relativa_raw":
                diferencia_relativa_raw,

            "format_str":
                format_str,

            "decimales_mostrados":
                decimales,

            "suma_redondeada":
                suma_redondeada,

            "total_redondeado":
                total_redondeado,

            "estado":
                estado,
        }

        controles.append(
            control
        )

        escribir()
        escribir(
            f"Control: {control['control']}"
        )

        escribir(
            f"  Cantidad bancos = "
            f"{control['cantidad_bancos']}"
        )

        escribir(
            f"  Suma math.fsum() = "
            f"{control['suma_fsum']!r}"
        )

        escribir(
            f"  Total SBS raw = "
            f"{control['total_sbs_raw']!r}"
        )

        escribir(
            f"  Valor raw celda Excel = "
            f"{metadata['valor_raw_celda_repr']}"
        )

        escribir(
            f"  Diferencia raw = "
            f"{control['diferencia_raw']!r}"
        )

        escribir(
            f"  Diferencia absoluta raw = "
            f"{control['diferencia_absoluta_raw']!r}"
        )

        escribir(
            f"  Diferencia relativa raw = "
            f"{control['diferencia_relativa_raw']!r}"
        )

        escribir(
            f"  Formato Excel agregado = "
            f"{control['format_str']!r}"
        )

        escribir(
            f"  Decimales mostrados = "
            f"{control['decimales_mostrados']}"
        )

        escribir(
            "  Suma redondeada "
            "ROUND_HALF_UP = "
            f"{control['suma_redondeada']}"
        )

        escribir(
            "  Total SBS redondeado "
            "ROUND_HALF_UP = "
            f"{control['total_redondeado']}"
        )

        escribir(
            f"  Resultado = "
            f"{control['estado']}"
        )

    controles_error = [
        control
        for control in controles
        if control[
            "estado"
        ]
        != "OK"
    ]

    if controles_error:

        raise RuntimeError(
            "B-2359: uno o más controles "
            "Total Banca Múltiple no coinciden "
            "a la precisión oficialmente "
            "mostrada por el Excel SBS. "
            "Controles ERROR: "
            f"{[x['variable'] for x in controles_error]}"
        )

    return {
        "agregado":
            agregado,

        "bancos":
            bancos,

        "controles":
            controles,
    }


# ============================================================
# 37. VALIDAR Y
# ============================================================

def validar_y_creditos(
    resultado,
    ruta
):

    registros = resultado[
        "registros"
    ]

    # ========================================================
    # NUEVO CONTROL DE PRECISIÓN SBS
    # ========================================================

    control_agregado = validar_agregado_creditos(
        ruta,
        resultado,
        registros
    )

    agregados = [
        registro
        for registro in registros
        if registro[
            "es_agregado"
        ]
    ]

    bancos = [
        registro
        for registro in registros
        if not registro[
            "es_agregado"
        ]
    ]

    problemas_estructurales = []

    problemas_permitidos_dato = {
        "TOTAL_NO_POSITIVO",
    }

    for registro in bancos:

        problemas_graves = [
            problema
            for problema in registro[
                "problemas"
            ]
            if problema not in
            problemas_permitidos_dato
        ]

        if problemas_graves:

            problemas_estructurales.append({
                "banco":
                    registro[
                        "banco_original"
                    ],

                "problemas":
                    problemas_graves,
            })

    if problemas_estructurales:

        raise RuntimeError(
            "B-2359: existen problemas "
            "estructurales/económicos no esperados: "
            f"{problemas_estructurales}"
        )

    dolcred_validos = [
        registro[
            "dolcred_pct"
        ]
        for registro in bancos
        if registro[
            "dolcred_pct"
        ]
        is not None
    ]

    faltantes = [
        registro
        for registro in bancos
        if registro[
            "dolcred_pct"
        ]
        is None
    ]

    return {
        "bancos":
            bancos,

        "agregado":
            agregados[
                0
            ],

        "controles_agregado":
            control_agregado[
                "controles"
            ],

        "cantidad_bancos":
            len(
                bancos
            ),

        "cantidad_dolcred_validos":
            len(
                dolcred_validos
            ),

        "cantidad_faltantes":
            len(
                faltantes
            ),

        "faltantes":
            faltantes,
    }


# ============================================================
# PARTE B
# X1 = DOLARIZACIÓN DE DEPÓSITOS
# SBS B-2318
#
# DESDE AQUÍ X1 SE MANTIENE SIN CAMBIOS.
# ============================================================


# ============================================================
# 38. DETECTAR ENCABEZADO DE TABLA B-2318
# ============================================================

def detectar_encabezado_depositos(
    filas
):

    candidatos = []

    for numero_fila, fila in enumerate(
        filas
    ):

        columna_empresa = None
        columna_saldo_final = None

        for numero_columna, valor in enumerate(
            fila
        ):

            texto = normalizar_comparacion(
                valor
            )

            if (
                texto in {
                    "empresa",
                    "empresas",
                }
                or
                texto.startswith(
                    "empresas "
                )
            ):

                columna_empresa = (
                    numero_columna
                )

            if (
                "saldo final"
                in texto
            ):

                columna_saldo_final = (
                    numero_columna
                )

        if (
            columna_empresa is not None
            and
            columna_saldo_final is not None
        ):

            candidatos.append({
                "fila_encabezado":
                    numero_fila,

                "columna_empresa":
                    columna_empresa,

                "columna_saldo_final":
                    columna_saldo_final,
            })

    if not candidatos:

        return None

    return candidatos[
        0
    ]


# ============================================================
# 39. CONTEXTO SUPERIOR
# ============================================================

def obtener_contexto_superior(
    filas,
    fila_encabezado,
    max_filas=8
):

    inicio = max(
        0,
        fila_encabezado
        -
        max_filas
    )

    textos = []

    for fila in filas[
        inicio:fila_encabezado
    ]:

        for valor in fila:

            texto = normalizar_comparacion(
                valor
            )

            if texto:

                textos.append(
                    texto
                )

    return " ".join(
        textos
    )


# ============================================================
# 40. CLASIFICAR MN / ME
# ============================================================

def clasificar_moneda_depositos(
    filas,
    encabezado
):

    contexto = obtener_contexto_superior(
        filas,
        encabezado[
            "fila_encabezado"
        ]
    )

    tiene_mn = (
        "moneda nacional"
        in contexto
    )

    tiene_me = (
        "moneda extranjera"
        in contexto
    )

    if (
        tiene_mn
        and
        not tiene_me
    ):

        return "MN"

    if (
        tiene_me
        and
        not tiene_mn
    ):

        return "ME"

    return None


# ============================================================
# 41. DETECTAR TABLAS MONETARIAS
# ============================================================

def detectar_tablas_monetarias(
    hojas
):

    candidatos = []

    for hoja in hojas:

        encabezado = detectar_encabezado_depositos(
            hoja[
                "filas"
            ]
        )

        if encabezado is None:
            continue

        moneda = clasificar_moneda_depositos(
            hoja[
                "filas"
            ],
            encabezado
        )

        if moneda is None:
            continue

        candidatos.append({
            "moneda":
                moneda,

            "nombre_hoja":
                hoja[
                    "nombre"
                ],

            "filas":
                hoja[
                    "filas"
                ],

            "encabezado":
                encabezado,
        })

    tablas_mn = [
        item
        for item in candidatos
        if item[
            "moneda"
        ]
        == "MN"
    ]

    tablas_me = [
        item
        for item in candidatos
        if item[
            "moneda"
        ]
        == "ME"
    ]

    return (
        tablas_mn,
        tablas_me,
    )


# ============================================================
# 42. AGREGADO DE DEPÓSITOS
# ============================================================

def es_agregado_depositos(
    nombre
):

    texto = normalizar_comparacion(
        nombre
    )

    return (
        "total banca multiple"
        in texto
    )


# ============================================================
# 43. EXTRAER SALDO FINAL
# ============================================================

def extraer_saldos(
    tabla
):

    filas = tabla[
        "filas"
    ]

    encabezado = tabla[
        "encabezado"
    ]

    fila_inicio = (
        encabezado[
            "fila_encabezado"
        ]
        +
        1
    )

    col_empresa = encabezado[
        "columna_empresa"
    ]

    col_saldo = encabezado[
        "columna_saldo_final"
    ]

    registros = []

    for numero_fila in range(
        fila_inicio,
        len(
            filas
        )
    ):

        fila = filas[
            numero_fila
        ]

        if (
            col_empresa >= len(
                fila
            )
            or
            col_saldo >= len(
                fila
            )
        ):

            continue

        nombre = fila[
            col_empresa
        ]

        saldo = convertir_numero(
            fila[
                col_saldo
            ]
        )

        nombre_texto = (
            str(
                nombre
            ).strip()
            if nombre is not None
            else ""
        )

        if not normalizar_texto(
            nombre_texto
        ):

            continue

        if saldo is None:

            continue

        registros.append({
            "fila_origen":
                numero_fila,

            "banco_original":
                nombre_texto,

            "banco_clave":
                normalizar_comparacion(
                    nombre_texto
                ),

            "saldo_final":
                saldo,

            "es_agregado":
                es_agregado_depositos(
                    nombre_texto
                ),
        })

    return registros


# ============================================================
# 44. DICCIONARIO DE BANCOS
# ============================================================

def crear_diccionario_bancos(
    registros
):

    resultado = {}

    duplicados = []

    for registro in registros:

        if registro[
            "es_agregado"
        ]:

            continue

        clave = registro[
            "banco_clave"
        ]

        if clave in resultado:

            duplicados.append(
                clave
            )

        else:

            resultado[
                clave
            ] = registro

    return (
        resultado,
        duplicados,
    )


# ============================================================
# 45. EMPAREJAR MN Y ME
# ============================================================

def emparejar_monedas(
    registros_mn,
    registros_me
):

    dic_mn, duplicados_mn = crear_diccionario_bancos(
        registros_mn
    )

    dic_me, duplicados_me = crear_diccionario_bancos(
        registros_me
    )

    claves_mn = set(
        dic_mn.keys()
    )

    claves_me = set(
        dic_me.keys()
    )

    comunes = sorted(
        claves_mn
        &
        claves_me
    )

    solo_mn = sorted(
        claves_mn
        -
        claves_me
    )

    solo_me = sorted(
        claves_me
        -
        claves_mn
    )

    emparejados = []

    for clave in comunes:

        reg_mn = dic_mn[
            clave
        ]

        reg_me = dic_me[
            clave
        ]

        mn = reg_mn[
            "saldo_final"
        ]

        me = reg_me[
            "saldo_final"
        ]

        total_depositos = (
            mn
            +
            me
        )

        problemas = []

        if mn < 0:

            problemas.append(
                "MN_NEGATIVO"
            )

        if me < 0:

            problemas.append(
                "ME_NEGATIVO"
            )

        if total_depositos <= 0:

            problemas.append(
                "TOTAL_NO_POSITIVO"
            )

            doldep = None

        else:

            doldep = (
                me
                /
                total_depositos
                *
                100
            )

            if not (
                0
                <=
                doldep
                <=
                100
            ):

                problemas.append(
                    "DOLDEP_FUERA_RANGO"
                )

        emparejados.append({
            "mes":
                MES,

            "banco_clave":
                clave,

            "banco_original_mn":
                reg_mn[
                    "banco_original"
                ],

            "banco_original_me":
                reg_me[
                    "banco_original"
                ],

            "saldo_final_mn":
                mn,

            "saldo_final_me":
                me,

            "total_depositos":
                total_depositos,

            "doldep_pct":
                doldep,

            "problemas":
                problemas,
        })

    return {
        "emparejados":
            emparejados,

        "solo_mn":
            solo_mn,

        "solo_me":
            solo_me,

        "duplicados_mn":
            duplicados_mn,

        "duplicados_me":
            duplicados_me,
    }


# ============================================================
# 46. VALIDAR TOTAL BANCA MÚLTIPLE - X1
#
# SIN CAMBIOS.
# ============================================================

def validar_agregado_depositos(
    registros,
    moneda
):

    individuales = [
        registro
        for registro in registros
        if not registro[
            "es_agregado"
        ]
    ]

    agregados = [
        registro
        for registro in registros
        if registro[
            "es_agregado"
        ]
    ]

    if len(
        agregados
    ) != 1:

        raise RuntimeError(
            f"B-2318 {moneda}: se esperaba "
            "exactamente un TOTAL BANCA MÚLTIPLE."
        )

    suma_bancos = sum(
        registro[
            "saldo_final"
        ]
        for registro in individuales
    )

    total_sbs = agregados[
        0
    ][
        "saldo_final"
    ]

    control = comparar_con_total_sbs(
        f"X1 / B-2318 / {moneda}",
        suma_bancos,
        total_sbs
    )

    registrar_control_total(
        control
    )

    if control[
        "estado"
    ] != "OK":

        raise RuntimeError(
            f"B-2318 {moneda}: la suma de bancos "
            "individuales no reproduce "
            "TOTAL BANCA MÚLTIPLE dentro "
            "de la tolerancia puramente numérica."
        )

    return {
        "moneda":
            moneda,

        "cantidad_bancos":
            len(
                individuales
            ),

        "suma_bancos":
            suma_bancos,

        "total_sbs":
            total_sbs,

        "diferencia":
            control[
                "diferencia"
            ],

        "diferencia_absoluta":
            control[
                "diferencia_absoluta"
            ],

        "estado":
            control[
                "estado"
            ],

        "agregado":
            agregados[
                0
            ],
    }


# ============================================================
# 47. EXTRAER X1
# ============================================================

def extraer_x1_depositos(
    ruta
):

    formato, hojas = leer_archivo(
        ruta
    )

    tablas_mn, tablas_me = detectar_tablas_monetarias(
        hojas
    )

    if (
        len(
            tablas_mn
        )
        != 1
        or
        len(
            tablas_me
        )
        != 1
    ):

        raise RuntimeError(
            "B-2318: se esperaba exactamente "
            "una tabla MN y una tabla ME. "
            f"MN={len(tablas_mn)}, "
            f"ME={len(tablas_me)}."
        )

    tabla_mn = tablas_mn[
        0
    ]

    tabla_me = tablas_me[
        0
    ]

    registros_mn = extraer_saldos(
        tabla_mn
    )

    registros_me = extraer_saldos(
        tabla_me
    )

    subtitulo(
        "CONTROL TOTAL BANCA MÚLTIPLE - X1 / B-2318"
    )

    control_mn = validar_agregado_depositos(
        registros_mn,
        "MN"
    )

    control_me = validar_agregado_depositos(
        registros_me,
        "ME"
    )

    emparejamiento = emparejar_monedas(
        registros_mn,
        registros_me
    )

    return {
        "formato":
            formato,

        "hojas":
            [
                hoja[
                    "nombre"
                ]
                for hoja in hojas
            ],

        "tabla_mn":
            tabla_mn,

        "tabla_me":
            tabla_me,

        "registros_mn":
            registros_mn,

        "registros_me":
            registros_me,

        "control_mn":
            control_mn,

        "control_me":
            control_me,

        "emparejamiento":
            emparejamiento,
    }


# ============================================================
# 48. VALIDAR X1
# ============================================================

def validar_x1_depositos(
    resultado
):

    emp = resultado[
        "emparejamiento"
    ]

    if emp[
        "duplicados_mn"
    ]:

        raise RuntimeError(
            "B-2318: existen bancos duplicados "
            f"en MN: {emp['duplicados_mn']}"
        )

    if emp[
        "duplicados_me"
    ]:

        raise RuntimeError(
            "B-2318: existen bancos duplicados "
            f"en ME: {emp['duplicados_me']}"
        )

    if emp[
        "solo_mn"
    ]:

        raise RuntimeError(
            "B-2318: existen bancos solo en MN. "
            "No se forzará emparejamiento: "
            f"{emp['solo_mn']}"
        )

    if emp[
        "solo_me"
    ]:

        raise RuntimeError(
            "B-2318: existen bancos solo en ME. "
            "No se forzará emparejamiento: "
            f"{emp['solo_me']}"
        )

    problemas_graves = []

    for registro in emp[
        "emparejados"
    ]:

        problemas_no_permitidos = [
            problema
            for problema in registro[
                "problemas"
            ]
            if problema
            !=
            "TOTAL_NO_POSITIVO"
        ]

        if problemas_no_permitidos:

            problemas_graves.append({
                "banco":
                    registro[
                        "banco_original_mn"
                    ],

                "problemas":
                    problemas_no_permitidos,
            })

    if problemas_graves:

        raise RuntimeError(
            "B-2318: existen problemas "
            f"no esperados: {problemas_graves}"
        )

    faltantes = [
        registro
        for registro in emp[
            "emparejados"
        ]
        if registro[
            "doldep_pct"
        ]
        is None
    ]

    return {
        "bancos":
            emp[
                "emparejados"
            ],

        "cantidad_bancos":
            len(
                emp[
                    "emparejados"
                ]
            ),

        "cantidad_faltantes":
            len(
                faltantes
            ),

        "faltantes":
            faltantes,
    }


# ============================================================
# 49. GUARDAR CSV Y
# ============================================================

def guardar_csv_y(
    bancos
):

    columnas = [
        "mes",
        "banco_original",
        "mn_soles_miles",
        "me_usd_miles",
        "total_soles_miles",
        "dolcred_pct",
        "problemas",
    ]

    with CSV_Y.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas
        )

        escritor.writeheader()

        for registro in bancos:

            escritor.writerow({
                "mes":
                    MES,

                "banco_original":
                    registro[
                        "banco_original"
                    ],

                "mn_soles_miles":
                    (
                        ""
                        if registro[
                            "mn_soles_miles"
                        ]
                        is None
                        else registro[
                            "mn_soles_miles"
                        ]
                    ),

                "me_usd_miles":
                    (
                        ""
                        if registro[
                            "me_usd_miles"
                        ]
                        is None
                        else registro[
                            "me_usd_miles"
                        ]
                    ),

                "total_soles_miles":
                    (
                        ""
                        if registro[
                            "total_soles_miles"
                        ]
                        is None
                        else registro[
                            "total_soles_miles"
                        ]
                    ),

                "dolcred_pct":
                    (
                        ""
                        if registro[
                            "dolcred_pct"
                        ]
                        is None
                        else registro[
                            "dolcred_pct"
                        ]
                    ),

                "problemas":
                    "|".join(
                        registro[
                            "problemas"
                        ]
                    ),
            })


# ============================================================
# 50. GUARDAR CSV X1
# ============================================================

def guardar_csv_x1(
    bancos
):

    columnas = [
        "mes",
        "banco_original_mn",
        "banco_original_me",
        "saldo_final_mn",
        "saldo_final_me",
        "doldep_pct",
        "problemas",
    ]

    with CSV_X1.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas
        )

        escritor.writeheader()

        for registro in bancos:

            escritor.writerow({
                "mes":
                    MES,

                "banco_original_mn":
                    registro[
                        "banco_original_mn"
                    ],

                "banco_original_me":
                    registro[
                        "banco_original_me"
                    ],

                "saldo_final_mn":
                    registro[
                        "saldo_final_mn"
                    ],

                "saldo_final_me":
                    registro[
                        "saldo_final_me"
                    ],

                "doldep_pct":
                    (
                        ""
                        if registro[
                            "doldep_pct"
                        ]
                        is None
                        else registro[
                            "doldep_pct"
                        ]
                    ),

                "problemas":
                    "|".join(
                        registro[
                            "problemas"
                        ]
                    ),
            })


# ============================================================
# 51. MOSTRAR RESULTADOS DE Y
# ============================================================

def mostrar_y(
    resultado,
    validacion
):

    titulo(
        "Y = DOLARIZACIÓN DEL CRÉDITO (%)"
    )

    escribir(
        "Reporte SBS: B-2359"
    )

    escribir(
        f"Formato real: "
        f"{resultado['formato']}"
    )

    escribir(
        f"Hoja elegida dinámicamente: "
        f"{resultado['hoja']!r}"
    )

    escribir(
        f"Fila encabezados MN|ME|Total: "
        f"{resultado['fila_encabezados']}"
    )

    escribir(
        f"Fila de bancos: "
        f"{resultado['fila_bancos']}"
    )

    escribir(
        f"Fila 'Total Créditos:': "
        f"{resultado['fila_total_creditos']}"
    )

    escribir(
        f"Bloques totales detectados: "
        f"{resultado['cantidad_bloques']}"
    )

    escribir(
        f"Bancos individuales: "
        f"{validacion['cantidad_bancos']}"
    )

    escribir(
        f"DOLCRED válidos: "
        f"{validacion['cantidad_dolcred_validos']}"
    )

    escribir(
        f"DOLCRED faltantes/no utilizables: "
        f"{validacion['cantidad_faltantes']}"
    )

    subtitulo(
        "BANCO ORIGINAL → DOLCRED (%)"
    )

    for registro in validacion[
        "bancos"
    ]:

        valor = registro[
            "dolcred_pct"
        ]

        if valor is None:
            valor_mostrar = "<FALTANTE>"
        else:
            valor_mostrar = valor

        escribir(
            f"{registro['banco_original']} "
            f"→ {valor_mostrar}"
        )

        if registro[
            "problemas"
        ]:

            escribir(
                "    problemas = "
                f"{registro['problemas']}"
            )

    subtitulo(
        "AGREGADO DE CONTROL - NO ES BANCO"
    )

    agregado = validacion[
        "agregado"
    ]

    escribir(
        f"Nombre: "
        f"{agregado['banco_original']!r}"
    )

    escribir(
        f"DOLCRED agregado: "
        f"{agregado['dolcred_pct']}"
    )


# ============================================================
# 52. MOSTRAR RESULTADOS DE X1
# ============================================================

def mostrar_x1(
    resultado,
    validacion
):

    titulo(
        "X1 = DOLARIZACIÓN DE DEPÓSITOS (%)"
    )

    escribir(
        "Reporte SBS: B-2318"
    )

    escribir(
        f"Formato real: "
        f"{resultado['formato']}"
    )

    tabla_mn = resultado[
        "tabla_mn"
    ]

    tabla_me = resultado[
        "tabla_me"
    ]

    escribir(
        f"Hoja MN detectada: "
        f"{tabla_mn['nombre_hoja']!r}"
    )

    escribir(
        "  fila encabezado = "
        f"{tabla_mn['encabezado']['fila_encabezado']}"
    )

    escribir(
        "  columna Empresas = "
        f"{tabla_mn['encabezado']['columna_empresa']}"
    )

    escribir(
        "  columna Saldo Final = "
        f"{tabla_mn['encabezado']['columna_saldo_final']}"
    )

    escribir(
        f"Hoja ME detectada: "
        f"{tabla_me['nombre_hoja']!r}"
    )

    escribir(
        "  fila encabezado = "
        f"{tabla_me['encabezado']['fila_encabezado']}"
    )

    escribir(
        "  columna Empresas = "
        f"{tabla_me['encabezado']['columna_empresa']}"
    )

    escribir(
        "  columna Saldo Final = "
        f"{tabla_me['encabezado']['columna_saldo_final']}"
    )

    escribir(
        f"Bancos emparejados MN/ME: "
        f"{validacion['cantidad_bancos']}"
    )

    escribir(
        f"DOLDEP faltantes/no utilizables: "
        f"{validacion['cantidad_faltantes']}"
    )

    emp = resultado[
        "emparejamiento"
    ]

    escribir(
        f"Solo MN: "
        f"{emp['solo_mn']}"
    )

    escribir(
        f"Solo ME: "
        f"{emp['solo_me']}"
    )

    escribir(
        f"Duplicados MN: "
        f"{emp['duplicados_mn']}"
    )

    escribir(
        f"Duplicados ME: "
        f"{emp['duplicados_me']}"
    )

    subtitulo(
        "RESUMEN DE CONTROLES TOTAL BANCA MÚLTIPLE"
    )

    for control in (
        resultado[
            "control_mn"
        ],
        resultado[
            "control_me"
        ],
    ):

        escribir(
            f"{control['moneda']}: "
            f"suma bancos={control['suma_bancos']} | "
            f"total SBS={control['total_sbs']} | "
            f"diferencia absoluta="
            f"{control['diferencia_absoluta']} | "
            f"resultado={control['estado']}"
        )

    subtitulo(
        "BANCO ORIGINAL → DOLDEP (%)"
    )

    for registro in validacion[
        "bancos"
    ]:

        valor = registro[
            "doldep_pct"
        ]

        if valor is None:
            valor_mostrar = "<FALTANTE>"
        else:
            valor_mostrar = valor

        escribir(
            f"{registro['banco_original_mn']} "
            f"→ {valor_mostrar}"
        )

        if (
            registro[
                "banco_original_mn"
            ]
            !=
            registro[
                "banco_original_me"
            ]
        ):

            escribir(
                "    nombre original ME = "
                f"{registro['banco_original_me']!r}"
            )

        if registro[
            "problemas"
        ]:

            escribir(
                "    problemas = "
                f"{registro['problemas']}"
            )


# ============================================================
# 53. MAIN
# ============================================================

def main():

    estado_y = None
    estado_x1 = None

    try:

        titulo(
            "PRUEBA ÚNICA Y + X1 - SBS 2015-11"
        )

        escribir(
            "Mes único: 2015-11"
        )

        escribir(
            "No se ejecutarán los 122 meses."
        )

        escribir(
            "No se homologarán nombres históricos."
        )

        escribir(
            "No se seleccionarán bancos."
        )

        escribir(
            "No se interpolarán datos."
        )

        escribir()
        escribir(
            "CONTROL Y / B-2359:"
        )

        escribir(
            "  No utiliza abs_tol."
        )

        escribir(
            "  Utiliza math.fsum()."
        )

        escribir(
            "  Utiliza la precisión visible "
            "de la celda Total Banca Múltiple."
        )

        escribir(
            "  El redondeo se realiza con "
            "Decimal + ROUND_HALF_UP."
        )

        # ====================================================
        # A. LOCALIZAR Y DESCARGAR Y
        # ====================================================

        titulo(
            "LOCALIZACIÓN Y DESCARGA - Y / B-2359"
        )

        enlace_y = localizar_archivo_oficial(
            REPORTES[
                "Y"
            ]
        )

        info_y = descargar_archivo(
            enlace_y[
                "url"
            ],
            ARCHIVO_CREDITO
        )

        escribir(
            f"Archivo origen SBS: "
            f"{info_y['nombre_origen']}"
        )

        escribir(
            f"Archivo crudo local: "
            f"{info_y['ruta']}"
        )

        escribir(
            f"HTTP: {info_y['http']}"
        )

        escribir(
            f"Bytes: {info_y['bytes']}"
        )

        escribir(
            f"SHA-256: {info_y['sha256']}"
        )

        escribir(
            f"Formato real: "
            f"{detectar_formato(ARCHIVO_CREDITO)}"
        )

        time.sleep(
            1.2
        )

        # ====================================================
        # B. LOCALIZAR Y DESCARGAR X1
        # ====================================================

        titulo(
            "LOCALIZACIÓN Y DESCARGA - X1 / B-2318"
        )

        enlace_x1 = localizar_archivo_oficial(
            REPORTES[
                "X1"
            ]
        )

        info_x1 = descargar_archivo(
            enlace_x1[
                "url"
            ],
            ARCHIVO_DEPOSITOS
        )

        escribir(
            f"Archivo origen SBS: "
            f"{info_x1['nombre_origen']}"
        )

        escribir(
            f"Archivo crudo local: "
            f"{info_x1['ruta']}"
        )

        escribir(
            f"HTTP: {info_x1['http']}"
        )

        escribir(
            f"Bytes: {info_x1['bytes']}"
        )

        escribir(
            f"SHA-256: {info_x1['sha256']}"
        )

        escribir(
            f"Formato real: "
            f"{detectar_formato(ARCHIVO_DEPOSITOS)}"
        )

        # ====================================================
        # C. EXTRAER Y
        # ====================================================

        resultado_y = extraer_y_creditos(
            ARCHIVO_CREDITO
        )

        # IMPORTANTE:
        # Si cualquiera de MN / ME / TOTAL falla
        # en el control por precisión visible,
        # esta llamada hace raise y X1 NO continúa.
        validacion_y = validar_y_creditos(
            resultado_y,
            ARCHIVO_CREDITO
        )

        mostrar_y(
            resultado_y,
            validacion_y
        )

        guardar_csv_y(
            validacion_y[
                "bancos"
            ]
        )

        estado_y = (
            "PRUEBA_Y_2015_11_VALIDADA"
        )

        escribir()
        escribir(
            f"ESTADO Y = {estado_y}"
        )

        # ====================================================
        # D. EXTRAER X1
        #
        # SOLO SE LLEGA AQUÍ SI Y SUPERÓ
        # LOS TRES CONTROLES.
        # ====================================================

        resultado_x1 = extraer_x1_depositos(
            ARCHIVO_DEPOSITOS
        )

        validacion_x1 = validar_x1_depositos(
            resultado_x1
        )

        mostrar_x1(
            resultado_x1,
            validacion_x1
        )

        guardar_csv_x1(
            validacion_x1[
                "bancos"
            ]
        )

        estado_x1 = (
            "PRUEBA_X1_2015_11_VALIDADA"
        )

        escribir()
        escribir(
            f"ESTADO X1 = {estado_x1}"
        )

        # ====================================================
        # E. CONTROL FINAL
        # ====================================================

        titulo(
            "RESUMEN FINAL"
        )

        escribir(
            f"Y: {estado_y}"
        )

        escribir(
            f"X1: {estado_x1}"
        )

        escribir()

        escribir(
            "Archivo Y:"
        )

        escribir(
            CSV_Y
        )

        escribir()

        escribir(
            "Archivo X1:"
        )

        escribir(
            CSV_X1
        )

        escribir()

        escribir(
            "Los archivos de prueba están "
            "en salidas/diagnosticos."
        )

        escribir(
            "datos_procesados NO fue modificado."
        )

        titulo(
            "CLASIFICACIÓN"
        )

        if (
            estado_y
            ==
            "PRUEBA_Y_2015_11_VALIDADA"
            and
            estado_x1
            ==
            "PRUEBA_X1_2015_11_VALIDADA"
        ):

            escribir(
                "ESTADO = "
                "PRUEBA_Y_X1_2015_11_VALIDADA"
            )

        else:

            escribir(
                "ESTADO = "
                "PRUEBA_Y_X1_2015_11_REQUIERE_REVISION"
            )

    except Exception as error:

        titulo(
            "ERROR EN LA PRUEBA"
        )

        escribir(
            f"Tipo: "
            f"{type(error).__name__}"
        )

        escribir(
            f"Detalle: "
            f"{repr(error)}"
        )

        escribir()

        escribir(
            "No se debe continuar todavía "
            "con los 122 meses."
        )

        escribir(
            "ESTADO = "
            "PRUEBA_Y_X1_2015_11_ERROR"
        )

        raise

    finally:

        CARPETA_DIAGNOSTICOS.mkdir(
            parents=True,
            exist_ok=True
        )

        TXT_RESULTADO.write_text(
            "\n".join(
                lineas_reporte
            ),
            encoding="utf-8"
        )

        print()
        print("=" * 110)
        print("PRUEBA FINALIZADA")
        print("=" * 110)

        print()
        print(
            "TXT:"
        )

        print(
            TXT_RESULTADO
        )

        print()
        print(
            "CSV Y:"
        )

        print(
            CSV_Y
        )

        print()
        print(
            "CSV X1:"
        )

        print(
            CSV_X1
        )

        print()
        print(
            "Archivos SBS crudos:"
        )

        print(
            CARPETA_CRUDOS
        )


# ============================================================
# 54. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()