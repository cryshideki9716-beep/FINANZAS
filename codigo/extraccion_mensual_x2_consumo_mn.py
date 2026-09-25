# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-23

from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict
import csv
import hashlib
import re
import time
import unicodedata

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
    NoSuchElementException,
    NoSuchWindowException,
)


# ============================================================
# 1. IDENTIFICACIÓN
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

TEMA = (
    "Dolarización del crédito y de los depósitos "
    "en el sistema financiero peruano"
)

VARIABLE = (
    "X2 - Tasa activa de Consumo "
    "en Moneda Nacional (%)"
)


# ============================================================
# 2. FUENTE SBS
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

ID_DATAZONE_MN = (
    "ctl00_cphContent_rpgActualMn_ctl00_DataZone_DT"
)


# ============================================================
# 3. CONTROLES DE LA PÁGINA
# ============================================================

NAME_FECHA_VISIBLE = (
    "ctl00$cphContent$rdpDate$dateInput"
)

ID_FECHA_VISIBLE = (
    "ctl00_cphContent_rdpDate_dateInput"
)

NAME_FECHA_INTERNA = (
    "ctl00$cphContent$rdpDate"
)

ID_FECHA_INTERNA = (
    "ctl00_cphContent_rdpDate"
)

NAME_BOTON = (
    "ctl00$cphContent$btnConsultar"
)

ID_BOTON = (
    "ctl00_cphContent_btnConsultar"
)

NAME_MONEDA = (
    "ctl00$cphContent$hdTipoMoneda"
)

ID_MONEDA = (
    "ctl00_cphContent_hdTipoMoneda"
)

NAME_ENTIDAD = (
    "ctl00$cphContent$hdTipoEntidad"
)

ID_ENTIDAD = (
    "ctl00_cphContent_hdTipoEntidad"
)

ID_PICKER_TELERIK = (
    "ctl00_cphContent_rdpDate"
)


# ============================================================
# 4. PERÍODO
# ============================================================

FECHA_INICIO = date(
    2015,
    11,
    1
)

FECHA_CORTE = date(
    2025,
    12,
    31
)


# ============================================================
# 5. CONFIGURACIÓN TÉCNICA
# ============================================================

TIMEOUT = 45

TIMEOUT_MANUAL = 180

PAUSA_ENTRE_CONSULTAS = 1.2

MAX_REINTENTOS_TECNICOS = 1

REANUDAR = True

GUARDAR_HTML_CRUDO = True

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36 "
    "AcademicResearch-UNCP-FinanzasI-"
    "2024200485D/1.0"
)


# ============================================================
# 6. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_DATOS_CRUDOS = (
    RAIZ
    / "datos_crudos"
    / f"X2_consumo_mn_{CODIGO_ESTUDIANTE}"
)

CARPETA_DATOS_PROCESADOS = (
    RAIZ
    / "datos_procesados"
)

CARPETA_DIAGNOSTICOS = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

CSV_DATOS = (
    CARPETA_DATOS_PROCESADOS
    / f"X2_tasa_activa_consumo_mn_{CODIGO_ESTUDIANTE}.csv"
)

CSV_PROMEDIO = (
    CARPETA_DATOS_PROCESADOS
    / f"X2_promedio_consumo_mn_{CODIGO_ESTUDIANTE}.csv"
)

CSV_AUDITORIA = (
    CARPETA_DIAGNOSTICOS
    / f"auditoria_X2_consumo_mn_{CODIGO_ESTUDIANTE}.csv"
)

TXT_RESUMEN = (
    CARPETA_DIAGNOSTICOS
    / f"resumen_X2_consumo_mn_{CODIGO_ESTUDIANTE}.txt"
)


# ============================================================
# 7. COLUMNAS DE SALIDA
# ============================================================

COLUMNAS_DATOS = [
    "mes",
    "fecha_sbs",
    "banco_original",
    "tasa_activa_consumo_mn",
]

COLUMNAS_PROMEDIO = [
    "mes",
    "fecha_sbs",
    "promedio_consumo_mn",
]

COLUMNAS_AUDITORIA = [
    "mes",
    "fecha_calendario_final",
    "fecha_sbs",
    "dias_retrocedidos",
    "estado",
    "cantidad_bancos",
    "cantidad_faltantes_bancos",
    "promedio",
    "html_sha256",
    "fecha_hora_extraccion",
    "detalle",
]


# ============================================================
# 8. ERROR TÉCNICO EXPLÍCITO
# ============================================================

class ErrorTecnicoExtraccion(Exception):
    """
    Un error técnico jamás debe convertirse
    automáticamente en ausencia de datos SBS.
    """

    pass


# ============================================================
# 9. UTILIDADES DE TEXTO
# ============================================================

def limpiar_texto(valor):

    if valor is None:
        return ""

    texto = str(
        valor
    )

    texto = texto.replace(
        "\xa0",
        " "
    )

    texto = texto.replace(
        "\r",
        " "
    )

    texto = texto.replace(
        "\n",
        " "
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def normalizar_solo_comparacion(
    valor
):
    """
    ÚNICAMENTE para comparar etiquetas.

    No se usa para modificar banco_original.
    """

    texto = limpiar_texto(
        valor
    ).lower()

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

    return re.sub(
        r"\s+",
        " ",
        texto
    ).strip()


# ============================================================
# 10. FECHAS Y MESES
# ============================================================

def fecha_a_texto(
    fecha
):

    return fecha.strftime(
        "%d/%m/%Y"
    )


def mes_a_texto(
    anio,
    mes
):

    return (
        f"{anio:04d}-{mes:02d}"
    )


def ultimo_dia_mes(
    anio,
    mes
):

    if mes == 12:

        siguiente = date(
            anio + 1,
            1,
            1
        )

    else:

        siguiente = date(
            anio,
            mes + 1,
            1
        )

    return (
        siguiente
        -
        timedelta(days=1)
    )


def generar_meses(
    inicio,
    corte
):

    meses = []

    anio = inicio.year
    mes = inicio.month

    while (
        anio < corte.year
        or
        (
            anio == corte.year
            and
            mes <= corte.month
        )
    ):

        meses.append(
            (
                anio,
                mes
            )
        )

        if mes == 12:

            anio += 1
            mes = 1

        else:

            mes += 1

    return meses


MESES_A_EXTRAER = generar_meses(
    FECHA_INICIO,
    FECHA_CORTE
)

if len(
    MESES_A_EXTRAER
) != 122:

    raise RuntimeError(
        "El rango noviembre 2015 - diciembre 2025 "
        "debe contener exactamente 122 meses. "
        f"Se obtuvieron {len(MESES_A_EXTRAER)}."
    )


def convertir_fecha(
    valor
):

    if valor is None:
        return None

    valor = limpiar_texto(
        valor
    )

    if not valor:
        return None

    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})"
        r"(?!\d)",
        valor
    )

    if coincidencia:

        try:

            return date(
                int(
                    coincidencia.group(3)
                ),
                int(
                    coincidencia.group(2)
                ),
                int(
                    coincidencia.group(1)
                ),
            )

        except ValueError:

            return None

    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        valor
    )

    if coincidencia:

        try:

            return date(
                int(
                    coincidencia.group(1)
                ),
                int(
                    coincidencia.group(2)
                ),
                int(
                    coincidencia.group(3)
                ),
            )

        except ValueError:

            return None

    return None


# ============================================================
# 11. CSV ATÓMICO / CHECKPOINT
# ============================================================

def leer_csv(
    ruta
):

    if not ruta.exists():

        return []

    with ruta.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        return list(
            csv.DictReader(
                archivo
            )
        )


def escribir_csv_atomico(
    ruta,
    columnas,
    filas
):

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporal = ruta.with_suffix(
        ruta.suffix
        + ".tmp"
    )

    with temporal.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
            extrasaction="ignore"
        )

        escritor.writeheader()

        for fila in filas:

            escritor.writerow(
                fila
            )

    temporal.replace(
        ruta
    )


def cargar_checkpoint():

    datos_por_mes = defaultdict(
        list
    )

    for fila in leer_csv(
        CSV_DATOS
    ):

        datos_por_mes[
            fila.get(
                "mes",
                ""
            )
        ].append(
            fila
        )

    promedio_por_mes = {}

    for fila in leer_csv(
        CSV_PROMEDIO
    ):

        mes = fila.get(
            "mes",
            ""
        )

        if mes:

            promedio_por_mes[
                mes
            ] = fila

    auditoria_por_mes = {}

    for fila in leer_csv(
        CSV_AUDITORIA
    ):

        mes = fila.get(
            "mes",
            ""
        )

        if mes:

            auditoria_por_mes[
                mes
            ] = fila

    return (
        datos_por_mes,
        promedio_por_mes,
        auditoria_por_mes,
    )


# ============================================================
# 12. CHECKPOINT ROBUSTO
# ============================================================

def checkpoint_mes_completo(
    mes,
    datos_por_mes,
    promedio_por_mes,
    auditoria_por_mes
):
    """
    Un checkpoint solo se considera completo
    si su contenido es internamente coherente.

    MES_SIN_DATO:
      - 0 filas bancarias;
      - no existe Promedio.

    DISPONIBLE:
      - cantidad_bancos > 0;
      - número de filas == cantidad_bancos;
      - Promedio existe;
      - todas las filas tienen el mismo mes
        y fecha_sbs de la auditoría;
      - el Promedio tiene también el mismo
        mes y fecha_sbs.

    ERROR_TECNICO:
      - siempre False.
    """

    auditoria = auditoria_por_mes.get(
        mes
    )

    if auditoria is None:

        return False

    estado = limpiar_texto(
        auditoria.get(
            "estado",
            ""
        )
    )

    filas_mes = datos_por_mes.get(
        mes,
        []
    )

    # ========================================================
    # ERROR TÉCNICO
    # ========================================================

    if estado == "ERROR_TECNICO":

        return False

    # ========================================================
    # MES SIN DATO
    # ========================================================

    if estado == "MES_SIN_DATO":

        return (
            len(
                filas_mes
            )
            == 0
            and
            mes not in promedio_por_mes
        )

    # ========================================================
    # DISPONIBLE
    # ========================================================

    if estado == "DISPONIBLE":

        cantidad_bancos_texto = limpiar_texto(
            auditoria.get(
                "cantidad_bancos",
                ""
            )
        )

        try:

            cantidad_bancos = int(
                cantidad_bancos_texto
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        # Debe ser estrictamente positivo.
        if cantidad_bancos <= 0:

            return False

        # Debe haber exactamente una fila
        # por cada banco reportado.
        if (
            len(
                filas_mes
            )
            !=
            cantidad_bancos
        ):

            return False

        # Promedio obligatorio.
        if mes not in promedio_por_mes:

            return False

        fecha_sbs_auditoria = limpiar_texto(
            auditoria.get(
                "fecha_sbs",
                ""
            )
        )

        # Un mes DISPONIBLE debe tener fecha SBS.
        if not fecha_sbs_auditoria:

            return False

        # ----------------------------------------------------
        # Todas las filas bancarias deben coincidir
        # exactamente con el mes y fecha_sbs auditados.
        # ----------------------------------------------------

        for fila in filas_mes:

            if (
                limpiar_texto(
                    fila.get(
                        "mes",
                        ""
                    )
                )
                !=
                mes
            ):

                return False

            if (
                limpiar_texto(
                    fila.get(
                        "fecha_sbs",
                        ""
                    )
                )
                !=
                fecha_sbs_auditoria
            ):

                return False

        # ----------------------------------------------------
        # El Promedio debe corresponder exactamente
        # al mismo mes y fecha SBS.
        # ----------------------------------------------------

        fila_promedio = promedio_por_mes[
            mes
        ]

        if (
            limpiar_texto(
                fila_promedio.get(
                    "mes",
                    ""
                )
            )
            !=
            mes
        ):

            return False

        if (
            limpiar_texto(
                fila_promedio.get(
                    "fecha_sbs",
                    ""
                )
            )
            !=
            fecha_sbs_auditoria
        ):

            return False

        return True

    # Cualquier otro estado no constituye
    # un checkpoint completo.
    return False


def guardar_checkpoint(
    datos_por_mes,
    promedio_por_mes,
    auditoria_por_mes
):

    filas_datos = []

    for mes in sorted(
        datos_por_mes
    ):

        filas_datos.extend(
            datos_por_mes[
                mes
            ]
        )

    filas_promedio = [
        promedio_por_mes[
            mes
        ]
        for mes in sorted(
            promedio_por_mes
        )
    ]

    filas_auditoria = [
        auditoria_por_mes[
            mes
        ]
        for mes in sorted(
            auditoria_por_mes
        )
    ]

    escribir_csv_atomico(
        CSV_DATOS,
        COLUMNAS_DATOS,
        filas_datos
    )

    escribir_csv_atomico(
        CSV_PROMEDIO,
        COLUMNAS_PROMEDIO,
        filas_promedio
    )

    escribir_csv_atomico(
        CSV_AUDITORIA,
        COLUMNAS_AUDITORIA,
        filas_auditoria
    )


# ============================================================
# 13. NAVEGADOR
# ============================================================

def crear_navegador():

    try:

        opciones = webdriver.ChromeOptions()

        opciones.add_argument(
            "--start-maximized"
        )

        opciones.add_argument(
            "--lang=es-PE"
        )

        opciones.add_argument(
            f"--user-agent={USER_AGENT}"
        )

        opciones.add_experimental_option(
            "excludeSwitches",
            [
                "enable-logging"
            ]
        )

        navegador = webdriver.Chrome(
            options=opciones
        )

        navegador.set_page_load_timeout(
            TIMEOUT
        )

        return navegador

    except Exception as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo iniciar Selenium/Chrome: "
            f"{type(error).__name__}: {error}"
        ) from error


def esperar_documento(
    navegador,
    timeout=TIMEOUT
):

    try:

        WebDriverWait(
            navegador,
            timeout
        ).until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            )
            == "complete"
        )

    except TimeoutException as error:

        raise ErrorTecnicoExtraccion(
            "Timeout esperando "
            "document.readyState=complete."
        ) from error

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Error Selenium esperando "
            "la carga del documento: "
            f"{error}"
        ) from error


# ============================================================
# 14. COMPROBAR PÁGINA SBS REAL
# ============================================================

def pagina_base_real(
    navegador
):

    try:

        fecha = navegador.find_elements(
            By.ID,
            ID_FECHA_VISIBLE
        )

        boton = navegador.find_elements(
            By.ID,
            ID_BOTON
        )

        return (
            len(
                fecha
            )
            > 0
            and
            len(
                boton
            )
            > 0
        )

    except WebDriverException:

        return False


def asegurar_pagina_real(
    navegador
):

    try:

        WebDriverWait(
            navegador,
            12
        ).until(
            lambda d:
            pagina_base_real(
                d
            )
        )

        return

    except TimeoutException:

        print()
        print(
            "La aplicación SBS real "
            "todavía no fue detectada."
        )

        print(
            "Si Chrome muestra una "
            "verificación de seguridad, "
            "complétala manualmente."
        )

        print(
            "No cierres Chrome."
        )

        print()

        input(
            "Cuando veas la página SBS real, "
            "presiona ENTER aquí..."
        )

    try:

        WebDriverWait(
            navegador,
            TIMEOUT_MANUAL
        ).until(
            lambda d:
            pagina_base_real(
                d
            )
        )

    except TimeoutException as error:

        raise ErrorTecnicoExtraccion(
            "No se recuperó la página SBS real "
            "después de la verificación manual."
        ) from error


def cargar_base(
    navegador
):

    try:

        navegador.get(
            URL
        )

    except TimeoutException as error:

        raise ErrorTecnicoExtraccion(
            "Timeout al cargar la URL SBS."
        ) from error

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Error Selenium cargando SBS: "
            f"{error}"
        ) from error

    esperar_documento(
        navegador
    )

    time.sleep(
        1.5
    )

    asegurar_pagina_real(
        navegador
    )


# ============================================================
# 15. DATEPICKER
# ============================================================

def localizar_fecha_visible(
    navegador
):

    candidatos = [
        (
            By.NAME,
            NAME_FECHA_VISIBLE
        ),
        (
            By.ID,
            ID_FECHA_VISIBLE
        ),
    ]

    try:

        for metodo, valor in candidatos:

            encontrados = navegador.find_elements(
                metodo,
                valor
            )

            if encontrados:

                return encontrados[
                    0
                ]

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Error Selenium buscando "
            "el DatePicker: "
            f"{error}"
        ) from error

    return None


def leer_fecha_visible(
    navegador
):

    elemento = localizar_fecha_visible(
        navegador
    )

    if elemento is None:

        return None

    try:

        return limpiar_texto(
            elemento.get_attribute(
                "value"
            )
        )

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo leer "
            "la fecha visible: "
            f"{error}"
        ) from error


def leer_fecha_interna(
    navegador
):

    candidatos = [
        (
            By.NAME,
            NAME_FECHA_INTERNA
        ),
        (
            By.ID,
            ID_FECHA_INTERNA
        ),
    ]

    try:

        for metodo, valor in candidatos:

            encontrados = navegador.find_elements(
                metodo,
                valor
            )

            if encontrados:

                return limpiar_texto(
                    encontrados[
                        0
                    ].get_attribute(
                        "value"
                    )
                )

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo leer "
            "la fecha interna: "
            f"{error}"
        ) from error

    return None


def leer_control(
    navegador,
    nombre,
    identificador
):

    candidatos = [
        (
            By.NAME,
            nombre
        ),
        (
            By.ID,
            identificador
        ),
    ]

    try:

        for metodo, valor in candidatos:

            encontrados = navegador.find_elements(
                metodo,
                valor
            )

            if encontrados:

                return limpiar_texto(
                    encontrados[
                        0
                    ].get_attribute(
                        "value"
                    )
                )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo leer "
            "un control SBS: "
            f"{error}"
        ) from error

    return None


def validar_mn_b(
    navegador
):

    moneda = leer_control(
        navegador,
        NAME_MONEDA,
        ID_MONEDA
    )

    entidad = leer_control(
        navegador,
        NAME_ENTIDAD,
        ID_ENTIDAD
    )

    if moneda != "MN":

        raise ErrorTecnicoExtraccion(
            "Se esperaba "
            "hdTipoMoneda='MN' "
            f"y se obtuvo {moneda!r}."
        )

    if entidad != "B":

        raise ErrorTecnicoExtraccion(
            "Se esperaba "
            "hdTipoEntidad='B' "
            f"y se obtuvo {entidad!r}."
        )


def estado_fecha(
    navegador,
    fecha_objetivo
):

    visible_texto = leer_fecha_visible(
        navegador
    )

    interna_texto = leer_fecha_interna(
        navegador
    )

    visible = convertir_fecha(
        visible_texto
    )

    interna = convertir_fecha(
        interna_texto
    )

    return {
        "visible_texto":
            visible_texto,

        "interna_texto":
            interna_texto,

        "visible":
            visible,

        "interna":
            interna,

        "ambas_ok":
            (
                visible
                ==
                fecha_objetivo
                and
                interna
                ==
                fecha_objetivo
            ),
    }


def cambiar_fecha_teclado(
    navegador,
    fecha_objetivo
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise ErrorTecnicoExtraccion(
            "No se encontró "
            "el DatePicker visible."
        )

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    try:

        navegador.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center'
            });
            """,
            campo
        )

        campo.click()

        campo.send_keys(
            Keys.CONTROL,
            "a"
        )

        campo.send_keys(
            Keys.BACKSPACE
        )

        campo.send_keys(
            texto_fecha
        )

        campo.send_keys(
            Keys.TAB
        )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Fallo escribiendo "
            "la fecha en el DatePicker: "
            f"{error}"
        ) from error

    time.sleep(
        0.8
    )


def cambiar_fecha_telerik(
    navegador,
    fecha_objetivo
):

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    try:

        resultado = navegador.execute_script(
            """
            try {

                if (
                    typeof $find === 'undefined'
                ) {
                    return 'NO_$find';
                }

                var picker = $find(
                    arguments[0]
                );

                if (!picker) {
                    return 'NO_PICKER';
                }

                if (
                    typeof picker.set_selectedDate
                    !== 'function'
                ) {
                    return 'NO_set_selectedDate';
                }

                var nuevaFecha = new Date(
                    arguments[1],
                    arguments[2] - 1,
                    arguments[3]
                );

                picker.set_selectedDate(
                    nuevaFecha
                );

                var input = null;

                if (
                    typeof picker.get_dateInput
                    === 'function'
                ) {

                    input =
                        picker.get_dateInput();
                }

                if (
                    input
                    &&
                    typeof input.set_value
                    === 'function'
                ) {

                    input.set_value(
                        arguments[4]
                    );
                }

                return 'OK';

            } catch (e) {

                return (
                    'ERROR: '
                    + e.toString()
                );
            }
            """,
            ID_PICKER_TELERIK,
            fecha_objetivo.year,
            fecha_objetivo.month,
            fecha_objetivo.day,
            texto_fecha,
        )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Falló la API Telerik: "
            f"{error}"
        ) from error

    time.sleep(
        0.8
    )

    return resultado


def establecer_fecha(
    navegador,
    fecha_objetivo
):

    cambiar_fecha_teclado(
        navegador,
        fecha_objetivo
    )

    estado = estado_fecha(
        navegador,
        fecha_objetivo
    )

    if estado[
        "ambas_ok"
    ]:

        return

    resultado_telerik = cambiar_fecha_telerik(
        navegador,
        fecha_objetivo
    )

    estado = estado_fecha(
        navegador,
        fecha_objetivo
    )

    if not estado[
        "ambas_ok"
    ]:

        raise ErrorTecnicoExtraccion(
            "DatePicker no quedó en "
            f"{fecha_a_texto(fecha_objetivo)}. "
            f"Telerik={resultado_telerik!r}; "
            f"visible={estado['visible_texto']!r}; "
            f"interna={estado['interna_texto']!r}."
        )


# ============================================================
# 16. BOTÓN CONSULTAR
# ============================================================

def localizar_boton(
    navegador
):

    candidatos = [
        (
            By.NAME,
            NAME_BOTON
        ),
        (
            By.ID,
            ID_BOTON
        ),
    ]

    try:

        for metodo, valor in candidatos:

            encontrados = navegador.find_elements(
                metodo,
                valor
            )

            if encontrados:

                return encontrados[
                    0
                ]

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Error Selenium buscando "
            "Consultar: "
            f"{error}"
        ) from error

    return None


# ============================================================
# 17. ESTADO DEL RESULTADO
# ============================================================

def buscar_sin_informacion(
    navegador
):

    try:

        texto = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except (
        WebDriverException,
        NoSuchElementException
    ) as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo leer "
            "el texto de la página: "
            f"{error}"
        ) from error

    normal = normalizar_solo_comparacion(
        texto
    )

    return (
        "no existe informacion "
        "para la fecha elegida"
        in normal
    )


def buscar_confirmacion_periodo(
    navegador,
    fecha_objetivo
):

    fecha_texto = fecha_a_texto(
        fecha_objetivo
    )

    patron = re.compile(
        rf"\bal\s+"
        rf"{re.escape(fecha_texto)}\b",
        flags=re.IGNORECASE
    )

    try:

        resultados = navegador.execute_script(
            """
            const elementos = Array.from(
                document.querySelectorAll(
                    'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th,strong,b'
                )
            );

            const salida = [];

            for (const el of elementos) {

                const estilo =
                    window.getComputedStyle(el);

                if (
                    estilo.display === 'none'
                    ||
                    estilo.visibility === 'hidden'
                ) {
                    continue;
                }

                const rect =
                    el.getBoundingClientRect();

                if (
                    rect.width <= 0
                    ||
                    rect.height <= 0
                ) {
                    continue;
                }

                const texto =
                    (el.innerText || '')
                    .replace(/\\s+/g, ' ')
                    .trim();

                if (
                    !texto
                    ||
                    texto.length > 600
                ) {
                    continue;
                }

                salida.push({
                    tag:
                        el.tagName,

                    id:
                        el.id || '',

                    text:
                        texto
                });
            }

            return salida;
            """
        )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Falló la inspección "
            "del período mostrado: "
            f"{error}"
        ) from error

    confirmaciones = []

    vistos = set()

    for item in resultados or []:

        texto = limpiar_texto(
            item.get(
                "text",
                ""
            )
        )

        if not patron.search(
            texto
        ):

            continue

        clave = (
            item.get(
                "tag",
                ""
            ),
            item.get(
                "id",
                ""
            ),
            texto,
        )

        if clave in vistos:

            continue

        vistos.add(
            clave
        )

        confirmaciones.append(
            item
        )

    return confirmaciones


def inspeccionar_estado_resultado(
    navegador,
    fecha_objetivo
):

    confirmaciones = buscar_confirmacion_periodo(
        navegador,
        fecha_objetivo
    )

    sin_info = buscar_sin_informacion(
        navegador
    )

    periodo_confirmado = (
        len(
            confirmaciones
        )
        > 0
    )

    if sin_info:

        respuesta = (
            "SIN_INFORMACION"
        )

    elif periodo_confirmado:

        respuesta = (
            "PERIODO_CONFIRMADO"
        )

    else:

        respuesta = (
            "RESPUESTA_NO_CONFIRMADA"
        )

    return {
        "respuesta":
            respuesta,

        "periodo_confirmado":
            periodo_confirmado,

        "sin_info":
            sin_info,

        "confirmaciones":
            confirmaciones,
    }


def sha_html(
    navegador
):

    try:

        html = navegador.page_source

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "No se pudo recuperar "
            "el HTML actual: "
            f"{error}"
        ) from error

    sha = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    return (
        html,
        sha
    )


def consultar_fecha(
    navegador,
    fecha_objetivo
):

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise ErrorTecnicoExtraccion(
            "No se encontró "
            "el botón Consultar."
        )

    _, sha_antes = sha_html(
        navegador
    )

    try:

        navegador.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center'
            });
            """,
            boton
        )

        time.sleep(
            0.3
        )

        boton.click()

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Falló el click "
            "en Consultar: "
            f"{error}"
        ) from error

    inicio = time.time()

    cambio_detectado_en = None

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        estado = inspeccionar_estado_resultado(
            navegador,
            fecha_objetivo
        )

        if estado[
            "sin_info"
        ]:

            time.sleep(
                0.5
            )

            return inspeccionar_estado_resultado(
                navegador,
                fecha_objetivo
            )

        if estado[
            "periodo_confirmado"
        ]:

            time.sleep(
                1.5
            )

            return inspeccionar_estado_resultado(
                navegador,
                fecha_objetivo
            )

        _, sha_actual = sha_html(
            navegador
        )

        if (
            sha_actual
            !=
            sha_antes
        ):

            if cambio_detectado_en is None:

                cambio_detectado_en = (
                    time.time()
                )

            if (
                time.time()
                - cambio_detectado_en
                >= 4.0
            ):

                break

        time.sleep(
            0.25
        )

    estado = inspeccionar_estado_resultado(
        navegador,
        fecha_objetivo
    )

    if (
        estado[
            "respuesta"
        ]
        ==
        "RESPUESTA_NO_CONFIRMADA"
    ):

        raise ErrorTecnicoExtraccion(
            "SBS no confirmó ni "
            f"'al {fecha_a_texto(fecha_objetivo)}' "
            "ni SIN_INFORMACION. "
            "La respuesta es ambigua y no "
            "se tratará como ausencia de datos."
        )

    return estado


# ============================================================
# 18. ESTRUCTURA BÁSICA
# ============================================================

def inspeccionar_estructura_basica(
    navegador
):

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    function limpio(txt) {

        return (txt || '')
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normal(txt) {

        return limpio(txt)
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase();
    }

    function visible(el) {

        if (!el) {
            return false;
        }

        let actual = el;

        while (actual) {

            const estilo =
                window.getComputedStyle(
                    actual
                );

            if (
                estilo.display === 'none'
                ||
                estilo.visibility === 'hidden'
                ||
                Number(estilo.opacity) === 0
            ) {
                return false;
            }

            actual =
                actual.parentElement;
        }

        const r =
            el.getBoundingClientRect();

        return (
            r.width > 0
            &&
            r.height > 0
        );
    }

    const outer =
        document.getElementById(
            OUTER_ID
        );

    const data =
        document.getElementById(
            DATA_ID
        );

    let consumoCount = 0;

    if (outer) {

        const celdas =
            Array.from(
                outer.querySelectorAll(
                    'td,th'
                )
            );

        for (
            const celda
            of celdas
        ) {

            if (!visible(celda)) {
                continue;
            }

            if (
                data
                &&
                data.contains(celda)
            ) {
                continue;
            }

            if (
                celda.querySelector('table')
            ) {
                continue;
            }

            const texto =
                limpio(
                    celda.innerText
                    ||
                    celda.textContent
                );

            if (
                normal(texto)
                === 'consumo'
            ) {

                consumoCount++;
            }
        }
    }

    return {
        outerExists:
            outer !== null,

        outerVisible:
            outer
            ? visible(outer)
            : false,

        dataExists:
            data !== null,

        dataVisible:
            data
            ? visible(data)
            : false,

        consumoCount:
            consumoCount
    };
    """

    try:

        return navegador.execute_script(
            script,
            ID_TABLA_MN_EXTERNA,
            ID_DATAZONE_MN,
        )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Falló la inspección "
            "de la estructura MN: "
            f"{error}"
        ) from error


# ============================================================
# 19. EXTRACCIÓN GEOMÉTRICA
# ============================================================

def extraer_consumo_mn(
    navegador
):

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    function textoOriginal(el) {

        if (!el) {
            return '';
        }

        return (
            el.innerText
            ||
            el.textContent
            ||
            ''
        )
        .replace(/\u00a0/g, ' ')
        .trim();
    }

    function compacto(txt) {

        return (txt || '')
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normal(txt) {

        return compacto(txt)
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase();
    }

    function visible(el) {

        if (!el) {
            return false;
        }

        let actual = el;

        while (actual) {

            const style =
                window.getComputedStyle(
                    actual
                );

            if (
                style.display === 'none'
                ||
                style.visibility === 'hidden'
                ||
                Number(style.opacity) === 0
            ) {
                return false;
            }

            actual =
                actual.parentElement;
        }

        const r =
            el.getBoundingClientRect();

        return (
            r.width > 0
            &&
            r.height > 0
        );
    }

    function rectInfo(el) {

        const r =
            el.getBoundingClientRect();

        return {
            top:
                r.top,

            bottom:
                r.bottom,

            left:
                r.left,

            right:
                r.right,

            width:
                r.width,

            height:
                r.height,

            centerX:
                (
                    r.left
                    +
                    r.right
                ) / 2,

            centerY:
                (
                    r.top
                    +
                    r.bottom
                ) / 2
        };
    }

    function overlapVertical(
        a,
        b
    ) {

        const solapamiento =
            Math.max(
                0,
                Math.min(
                    a.bottom,
                    b.bottom
                )
                -
                Math.max(
                    a.top,
                    b.top
                )
            );

        const base =
            Math.min(
                a.height,
                b.height
            );

        if (
            base <= 0
        ) {
            return 0;
        }

        return (
            solapamiento
            /
            base
        );
    }

    function overlapHorizontal(
        a,
        b
    ) {

        const solapamiento =
            Math.max(
                0,
                Math.min(
                    a.right,
                    b.right
                )
                -
                Math.max(
                    a.left,
                    b.left
                )
            );

        const base =
            Math.min(
                a.width,
                b.width
            );

        if (
            base <= 0
        ) {
            return 0;
        }

        return (
            solapamiento
            /
            base
        );
    }

    function esFaltante(txt) {

        const n =
            normal(txt);

        const faltantes =
            new Set([
                '',
                '-',
                '–',
                '—',
                's.i.',
                's.i',
                'n.d.',
                'n.d',
                'nd',
                'n/a',
                'na',
                'n.i.',
                'n.i',
                's/d',
                'sd'
            ]);

        return faltantes.has(
            n
        );
    }

    function esNumero(txt) {

        const t =
            compacto(txt);

        if (!t) {
            return false;
        }

        const numero =
            t
            .replace(/%/g, '')
            .replace(/,/g, '.')
            .trim();

        return (
            /^[-+]?\d+(?:\.\d+)?$/
            .test(numero)
        );
    }

    function esValorTasa(txt) {

        return (
            esNumero(txt)
            ||
            esFaltante(txt)
        );
    }

    const outer =
        document.getElementById(
            OUTER_ID
        );

    const data =
        document.getElementById(
            DATA_ID
        );

    if (!outer) {

        return {
            ok:
                false,

            error:
                'TABLA_MN_NO_EXISTE'
        };
    }

    if (!data) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_EXISTE'
        };
    }

    if (!visible(outer)) {

        return {
            ok:
                false,

            error:
                'TABLA_MN_NO_VISIBLE'
        };
    }

    if (!visible(data)) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_VISIBLE'
        };
    }

    // ========================================================
    // 1. ETIQUETA EXTERNA CONSUMO
    // ========================================================

    const etiquetasConsumo = [];

    const celdasOuter =
        Array.from(
            outer.querySelectorAll(
                'td,th'
            )
        );

    for (
        const celda
        of celdasOuter
    ) {

        if (!visible(celda)) {
            continue;
        }

        if (
            data.contains(
                celda
            )
        ) {
            continue;
        }

        if (
            celda.querySelector(
                'table'
            )
        ) {
            continue;
        }

        const original =
            textoOriginal(
                celda
            );

        if (
            normal(original)
            !== 'consumo'
        ) {
            continue;
        }

        const fila =
            celda.closest(
                'tr'
            );

        if (
            !fila
            ||
            !visible(fila)
        ) {
            continue;
        }

        etiquetasConsumo.push({
            text:
                original,

            row:
                fila,

            rowRect:
                rectInfo(fila)
        });
    }

    if (
        etiquetasConsumo.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'CONSUMO_EXTERNO_NO_UNIVOCO',

            consumoCount:
                etiquetasConsumo.length
        };
    }

    const etiquetaConsumo =
        etiquetasConsumo[0];

    // ========================================================
    // 2. FILAS NUMÉRICAS
    // ========================================================

    const filasData =
        Array.from(
            data.querySelectorAll(
                'tr'
            )
        )
        .filter(
            fila =>
                fila.closest('table')
                === data
        );

    const filasNumericas = [];

    for (
        let i = 0;
        i < filasData.length;
        i++
    ) {

        const fila =
            filasData[i];

        if (!visible(fila)) {
            continue;
        }

        const celdas =
            Array.from(
                fila.children
            )
            .filter(
                el =>
                    (
                        el.tagName === 'TD'
                        ||
                        el.tagName === 'TH'
                    )
                    &&
                    visible(el)
            );

        if (
            celdas.length < 2
        ) {
            continue;
        }

        const valoresOriginales =
            celdas.map(
                celda =>
                    textoOriginal(
                        celda
                    )
            );

        const todosValores =
            valoresOriginales.every(
                valor =>
                    esValorTasa(
                        valor
                    )
            );

        const alMenosUnNumero =
            valoresOriginales.some(
                valor =>
                    esNumero(
                        valor
                    )
            );

        if (
            todosValores
            &&
            alMenosUnNumero
        ) {

            filasNumericas.push({
                originalIndex:
                    i,

                element:
                    fila,

                rect:
                    rectInfo(fila),

                cells:
                    celdas,

                values:
                    valoresOriginales
            });
        }
    }

    if (
        filasNumericas.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_HAY_FILAS_NUMERICAS'
        };
    }

    // ========================================================
    // 3. MAPEO VERTICAL
    // ========================================================

    const candidatos = [];

    for (
        const fila
        of filasNumericas
    ) {

        const overlap =
            overlapVertical(
                etiquetaConsumo.rowRect,
                fila.rect
            );

        const distancia =
            Math.abs(
                etiquetaConsumo
                .rowRect
                .centerY
                -
                fila.rect.centerY
            );

        candidatos.push({
            fila:
                fila,

            overlap:
                overlap,

            distancia:
                distancia
        });
    }

    candidatos.sort(
        (a, b) => {

            if (
                b.overlap
                !==
                a.overlap
            ) {

                return (
                    b.overlap
                    -
                    a.overlap
                );
            }

            return (
                a.distancia
                -
                b.distancia
            );
        }
    );

    const mejor =
        candidatos[0];

    if (
        !mejor
        ||
        mejor.overlap < 0.50
    ) {

        return {
            ok:
                false,

            error:
                'CONSUMO_NO_MAPEADO_GEOMETRICAMENTE',

            overlap:
                mejor
                ? mejor.overlap
                : null
        };
    }

    if (
        candidatos.length > 1
    ) {

        const segundo =
            candidatos[1];

        const mismoOverlap =
            Math.abs(
                mejor.overlap
                -
                segundo.overlap
            )
            < 0.000001;

        const mismaDistancia =
            Math.abs(
                mejor.distancia
                -
                segundo.distancia
            )
            < 0.5;

        if (
            mismoOverlap
            &&
            mismaDistancia
        ) {

            return {
                ok:
                    false,

                error:
                    'MAPEO_CONSUMO_AMBIGUO'
            };
        }
    }

    const filaConsumo =
        mejor.fila;

    const N =
        filaConsumo.cells.length;

    if (
        N < 2
    ) {

        return {
            ok:
                false,

            error:
                'FILA_CONSUMO_SIN_COLUMNAS_SUFICIENTES'
        };
    }

    // ========================================================
    // 4. ENCABEZADOS DINÁMICOS
    // ========================================================

    const rectsValores =
        filaConsumo.cells.map(
            celda =>
                rectInfo(celda)
        );

    const candidatosHeader = [];

    for (
        let i = 0;
        i < filasData.length;
        i++
    ) {

        const fila =
            filasData[i];

        if (!visible(fila)) {
            continue;
        }

        const rectFila =
            rectInfo(fila);

        if (
            rectFila.bottom
            >
            filaConsumo.rect.top
            + 1
        ) {
            continue;
        }

        const celdas =
            Array.from(
                fila.children
            )
            .filter(
                el =>
                    (
                        el.tagName === 'TD'
                        ||
                        el.tagName === 'TH'
                    )
                    &&
                    visible(el)
            );

        const items = [];

        for (
            const celda
            of celdas
        ) {

            if (
                celda.querySelector(
                    'table'
                )
            ) {
                continue;
            }

            const original =
                textoOriginal(
                    celda
                );

            if (!compacto(original)) {
                continue;
            }

            if (
                esNumero(original)
                ||
                esFaltante(original)
            ) {
                continue;
            }

            items.push({
                original:
                    original,

                rect:
                    rectInfo(celda)
            });
        }

        if (
            items.length === 0
        ) {
            continue;
        }

        const headers = [];

        let matches = 0;

        for (
            const rectValor
            of rectsValores
        ) {

            let mejorHeader = null;

            for (
                const item
                of items
            ) {

                const overlap =
                    overlapHorizontal(
                        rectValor,
                        item.rect
                    );

                const distancia =
                    Math.abs(
                        rectValor.centerX
                        -
                        item.rect.centerX
                    );

                const candidato = {
                    original:
                        item.original,

                    overlap:
                        overlap,

                    distancia:
                        distancia
                };

                if (
                    mejorHeader === null
                    ||
                    candidato.overlap
                    >
                    mejorHeader.overlap
                    ||
                    (
                        candidato.overlap
                        ===
                        mejorHeader.overlap
                        &&
                        candidato.distancia
                        <
                        mejorHeader.distancia
                    )
                ) {

                    mejorHeader =
                        candidato;
                }
            }

            if (
                mejorHeader
                &&
                mejorHeader.overlap
                >= 0.50
            ) {

                headers.push(
                    mejorHeader.original
                );

                matches++;

            } else {

                headers.push(
                    null
                );
            }
        }

        const normalizados =
            headers
            .filter(
                h => h !== null
            )
            .map(
                h => normal(h)
            );

        const unicos =
            new Set(
                normalizados
            ).size;

        candidatosHeader.push({
            rowIndex:
                i,

            headers:
                headers,

            matchedCount:
                matches,

            uniqueCount:
                unicos,

            distanceAbove:
                filaConsumo.rect.top
                -
                rectFila.bottom
        });
    }

    if (
        candidatosHeader.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_HAY_CANDIDATOS_DE_ENCABEZADO'
        };
    }

    candidatosHeader.sort(
        (a, b) => {

            if (
                b.matchedCount
                !==
                a.matchedCount
            ) {

                return (
                    b.matchedCount
                    -
                    a.matchedCount
                );
            }

            if (
                b.uniqueCount
                !==
                a.uniqueCount
            ) {

                return (
                    b.uniqueCount
                    -
                    a.uniqueCount
                );
            }

            return (
                a.distanceAbove
                -
                b.distanceAbove
            );
        }
    );

    const header =
        candidatosHeader[0];

    if (
        header.matchedCount
        !== N
    ) {

        return {
            ok:
                false,

            error:
                'ENCABEZADOS_NO_COMPLETOS',

            headerCount:
                header.matchedCount,

            valueCount:
                N
        };
    }

    if (
        header.headers.length
        !== N
    ) {

        return {
            ok:
                false,

            error:
                'ENCABEZADOS_VALORES_LONGITUD_DISTINTA',

            headerCount:
                header.headers.length,

            valueCount:
                N
        };
    }

    if (
        header.uniqueCount
        !== N
    ) {

        return {
            ok:
                false,

            error:
                'ENCABEZADOS_NO_UNIVOCOS',

            uniqueHeaders:
                header.uniqueCount,

            totalHeaders:
                N
        };
    }

    // ========================================================
    // 5. EMPAREJAR
    // ========================================================

    const registros = [];

    let promedio = null;

    for (
        let i = 0;
        i < N;
        i++
    ) {

        const bancoOriginal =
            header.headers[i];

        const valorOriginal =
            filaConsumo.values[i];

        const registro = {
            index:
                i,

            banco_original:
                bancoOriginal,

            valor:
                valorOriginal,

            faltante:
                esFaltante(
                    valorOriginal
                ),

            es_promedio:
                normal(
                    bancoOriginal
                )
                === 'promedio'
        };

        registros.push(
            registro
        );

        if (
            registro.es_promedio
        ) {

            if (
                promedio !== null
            ) {

                return {
                    ok:
                        false,

                    error:
                        'PROMEDIO_MULTIPLE'
                };
            }

            promedio =
                registro;
        }
    }

    if (
        promedio === null
    ) {

        return {
            ok:
                false,

            error:
                'PROMEDIO_NO_DETECTADO'
        };
    }

    const bancos =
        registros.filter(
            r =>
                !r.es_promedio
        );

    return {
        ok:
            true,

        consumoCount:
            etiquetasConsumo.length,

        consumoDataRowIndex:
            filaConsumo.originalIndex,

        verticalOverlap:
            mejor.overlap,

        verticalDistance:
            mejor.distancia,

        headerRowIndex:
            header.rowIndex,

        totalHeaders:
            header.headers.length,

        totalValues:
            filaConsumo.values.length,

        bankCount:
            bancos.length,

        missingBankCount:
            bancos.filter(
                r =>
                    r.faltante
            ).length,

        bancos:
            bancos,

        promedio:
            promedio
    };
    """

    try:

        resultado = navegador.execute_script(
            script,
            ID_TABLA_MN_EXTERNA,
            ID_DATAZONE_MN,
        )

    except WebDriverException as error:

        raise ErrorTecnicoExtraccion(
            "Falló el mapeo geométrico "
            "de Consumo: "
            f"{error}"
        ) from error

    if not resultado.get(
        "ok",
        False
    ):

        raise ErrorTecnicoExtraccion(
            "La página tiene estructura válida, "
            "pero el extractor no pudo mapear "
            "Consumo de forma segura. "
            f"Detalle={resultado}"
        )

    if (
        resultado[
            "totalHeaders"
        ]
        !=
        resultado[
            "totalValues"
        ]
    ):

        raise ErrorTecnicoExtraccion(
            "Encabezados y valores "
            "no tienen la misma longitud."
        )

    if (
        resultado[
            "bankCount"
        ]
        + 1
        !=
        resultado[
            "totalHeaders"
        ]
    ):

        raise ErrorTecnicoExtraccion(
            "La separación bancos + Promedio "
            "no coincide con el número "
            "total de columnas."
        )

    return resultado


# ============================================================
# 20. GUARDAR HTML CRUDO
# ============================================================

def guardar_html_crudo(
    mes,
    fecha_sbs,
    html
):

    if not GUARDAR_HTML_CRUDO:

        return None

    CARPETA_DATOS_CRUDOS.mkdir(
        parents=True,
        exist_ok=True
    )

    patron = (
        f"X2_consumo_mn_"
        f"{CODIGO_ESTUDIANTE}_"
        f"{mes}_*.html"
    )

    for viejo in CARPETA_DATOS_CRUDOS.glob(
        patron
    ):

        try:

            viejo.unlink()

        except OSError:

            pass

    nombre = (
        f"X2_consumo_mn_"
        f"{CODIGO_ESTUDIANTE}_"
        f"{mes}_"
        f"{fecha_sbs.strftime('%Y-%m-%d')}.html"
    )

    ruta = (
        CARPETA_DATOS_CRUDOS
        /
        nombre
    )

    ruta.write_text(
        html,
        encoding="utf-8"
    )

    return ruta


# ============================================================
# 21. EVALUAR UNA FECHA
# ============================================================

def evaluar_fecha(
    navegador,
    fecha_objetivo
):

    cargar_base(
        navegador
    )

    validar_mn_b(
        navegador
    )

    establecer_fecha(
        navegador,
        fecha_objetivo
    )

    validar_mn_b(
        navegador
    )

    resultado_post = consultar_fecha(
        navegador,
        fecha_objetivo
    )

    if (
        resultado_post[
            "respuesta"
        ]
        ==
        "SIN_INFORMACION"
    ):

        return {
            "estado":
                "SIN_INFORMACION",

            "periodo_confirmado":
                resultado_post[
                    "periodo_confirmado"
                ],

            "estructura":
                None,

            "extraccion":
                None,
        }

    if (
        resultado_post[
            "respuesta"
        ]
        !=
        "PERIODO_CONFIRMADO"
    ):

        raise ErrorTecnicoExtraccion(
            "Estado del POST no reconocido: "
            f"{resultado_post}"
        )

    estructura = inspeccionar_estructura_basica(
        navegador
    )

    estructura_valida = (
        estructura[
            "outerExists"
        ]
        and
        estructura[
            "outerVisible"
        ]
        and
        estructura[
            "dataExists"
        ]
        and
        estructura[
            "dataVisible"
        ]
        and
        estructura[
            "consumoCount"
        ]
        == 1
    )

    if not estructura_valida:

        return {
            "estado":
                "ESTRUCTURA_NO_VALIDA",

            "periodo_confirmado":
                True,

            "estructura":
                estructura,

            "extraccion":
                None,
        }

    extraccion = extraer_consumo_mn(
        navegador
    )

    return {
        "estado":
            "DISPONIBLE",

        "periodo_confirmado":
            True,

        "estructura":
            estructura,

        "extraccion":
            extraccion,
    }


# ============================================================
# 22. REINTENTO TÉCNICO
# ============================================================

def evaluar_fecha_con_reintento(
    navegador,
    fecha_objetivo
):

    errores = []

    total_intentos = (
        1
        +
        MAX_REINTENTOS_TECNICOS
    )

    for numero_intento in range(
        total_intentos
    ):

        try:

            if numero_intento > 0:

                print(
                    "      ↳ reintento técnico "
                    f"{numero_intento}/"
                    f"{MAX_REINTENTOS_TECNICOS}"
                )

                time.sleep(
                    2
                )

            resultado = evaluar_fecha(
                navegador,
                fecha_objetivo
            )

            return {
                "ok":
                    True,

                "resultado":
                    resultado,

                "errores":
                    errores,
            }

        except (
            ErrorTecnicoExtraccion,
            TimeoutException,
            WebDriverException,
            StaleElementReferenceException,
            NoSuchWindowException,
        ) as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )

            errores.append(
                detalle
            )

            print(
                "      [ERROR TÉCNICO] "
                f"{detalle}"
            )

            if (
                numero_intento
                <
                total_intentos - 1
            ):

                continue

            return {
                "ok":
                    False,

                "resultado":
                    None,

                "errores":
                    errores,
            }

        except Exception as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{repr(error)}"
            )

            errores.append(
                detalle
            )

            print(
                "      [ERROR TÉCNICO "
                "NO CLASIFICADO] "
                f"{detalle}"
            )

            if (
                numero_intento
                <
                total_intentos - 1
            ):

                continue

            return {
                "ok":
                    False,

                "resultado":
                    None,

                "errores":
                    errores,
            }

    return {
        "ok":
            False,

        "resultado":
            None,

        "errores":
            errores,
    }


# ============================================================
# 23. PROCESAR UN MES
# ============================================================

def procesar_mes(
    navegador,
    anio,
    mes
):

    clave_mes = mes_a_texto(
        anio,
        mes
    )

    fecha_final = ultimo_dia_mes(
        anio,
        mes
    )

    fecha_intento = fecha_final

    dias_retrocedidos = 0

    print()
    print(
        "=" * 80
    )

    print(
        f"MES {clave_mes}"
    )

    print(
        "=" * 80
    )

    print(
        "  Último día calendario: "
        f"{fecha_a_texto(fecha_final)}"
    )

    while (
        fecha_intento.year == anio
        and
        fecha_intento.month == mes
    ):

        print(
            "  Probando "
            f"{fecha_a_texto(fecha_intento)} "
            f"(retroceso={dias_retrocedidos})"
        )

        evaluacion = evaluar_fecha_con_reintento(
            navegador,
            fecha_intento
        )

        # ====================================================
        # ERROR TÉCNICO
        # ====================================================

        if not evaluacion[
            "ok"
        ]:

            return {
                "estado":
                    "ERROR_TECNICO",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    None,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "bancos":
                    [],

                "promedio":
                    None,

                "cantidad_bancos":
                    None,

                "cantidad_faltantes":
                    None,

                "html":
                    None,

                "sha256":
                    None,

                "detalle":
                    " || ".join(
                        evaluacion[
                            "errores"
                        ]
                    ),
            }

        resultado = evaluacion[
            "resultado"
        ]

        estado_dia = resultado[
            "estado"
        ]

        # ====================================================
        # FECHA VÁLIDA
        # ====================================================

        if estado_dia == "DISPONIBLE":

            extraccion = resultado[
                "extraccion"
            ]

            html, sha = sha_html(
                navegador
            )

            print(
                "      [DISPONIBLE] "
                f"{fecha_a_texto(fecha_intento)}"
            )

            print(
                "      Bancos: "
                f"{extraccion['bankCount']}"
            )

            print(
                "      Faltantes: "
                f"{extraccion['missingBankCount']}"
            )

            return {
                "estado":
                    "DISPONIBLE",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    fecha_intento,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "bancos":
                    extraccion[
                        "bancos"
                    ],

                "promedio":
                    extraccion[
                        "promedio"
                    ],

                "cantidad_bancos":
                    extraccion[
                        "bankCount"
                    ],

                "cantidad_faltantes":
                    extraccion[
                        "missingBankCount"
                    ],

                "html":
                    html,

                "sha256":
                    sha,

                "detalle":
                    (
                        "Consumo mapeado "
                        "geométricamente; "
                        f"fila={extraccion['consumoDataRowIndex']}; "
                        f"headers={extraccion['totalHeaders']}; "
                        f"valores={extraccion['totalValues']}."
                    ),
            }

        # ====================================================
        # DÍA SIN DATO VÁLIDO
        # ====================================================

        if estado_dia == "SIN_INFORMACION":

            print(
                "      SIN_INFORMACION"
            )

        elif estado_dia == "ESTRUCTURA_NO_VALIDA":

            estructura = resultado[
                "estructura"
            ]

            print(
                "      ESTRUCTURA_NO_VALIDA | "
                f"tabla={estructura['outerVisible']} | "
                f"datazone={estructura['dataVisible']} | "
                f"consumo={estructura['consumoCount']}"
            )

        else:

            return {
                "estado":
                    "ERROR_TECNICO",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    None,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "bancos":
                    [],

                "promedio":
                    None,

                "cantidad_bancos":
                    None,

                "cantidad_faltantes":
                    None,

                "html":
                    None,

                "sha256":
                    None,

                "detalle":
                    (
                        "Estado diario no reconocido: "
                        f"{estado_dia}"
                    ),
            }

        if fecha_intento.day == 1:

            break

        fecha_intento = (
            fecha_intento
            -
            timedelta(days=1)
        )

        dias_retrocedidos += 1

        time.sleep(
            PAUSA_ENTRE_CONSULTAS
        )

    # ========================================================
    # MES COMPLETO SIN FECHA VÁLIDA
    # ========================================================

    print(
        "      [MES_SIN_DATO]"
    )

    return {
        "estado":
            "MES_SIN_DATO",

        "mes":
            clave_mes,

        "fecha_calendario_final":
            fecha_final,

        "fecha_sbs":
            None,

        "dias_retrocedidos":
            fecha_final.day - 1,

        "bancos":
            [],

        "promedio":
            None,

        "cantidad_bancos":
            0,

        "cantidad_faltantes":
            0,

        "html":
            None,

        "sha256":
            None,

        "detalle":
            (
                "Se evaluó el mes completo "
                "hasta el día 1 sin hallar "
                "una fecha válida."
            ),
    }


# ============================================================
# 24. CONVERTIR RESULTADO DE MES A FILAS
# ============================================================

def construir_filas_datos(
    resultado_mes
):

    if (
        resultado_mes[
            "estado"
        ]
        !=
        "DISPONIBLE"
    ):

        return []

    mes = resultado_mes[
        "mes"
    ]

    fecha_sbs = fecha_a_texto(
        resultado_mes[
            "fecha_sbs"
        ]
    )

    filas = []

    for registro in resultado_mes[
        "bancos"
    ]:

        filas.append({
            "mes":
                mes,

            "fecha_sbs":
                fecha_sbs,

            "banco_original":
                registro[
                    "banco_original"
                ],

            "tasa_activa_consumo_mn":
                registro[
                    "valor"
                ],
        })

    return filas


def construir_fila_promedio(
    resultado_mes
):

    if (
        resultado_mes[
            "estado"
        ]
        !=
        "DISPONIBLE"
    ):

        return None

    promedio = resultado_mes[
        "promedio"
    ]

    return {
        "mes":
            resultado_mes[
                "mes"
            ],

        "fecha_sbs":
            fecha_a_texto(
                resultado_mes[
                    "fecha_sbs"
                ]
            ),

        "promedio_consumo_mn":
            promedio[
                "valor"
            ],
    }


def construir_fila_auditoria(
    resultado_mes
):

    fecha_sbs = ""

    if resultado_mes[
        "fecha_sbs"
    ] is not None:

        fecha_sbs = fecha_a_texto(
            resultado_mes[
                "fecha_sbs"
            ]
        )

    promedio = ""

    if resultado_mes[
        "promedio"
    ] is not None:

        promedio = resultado_mes[
            "promedio"
        ][
            "valor"
        ]

    cantidad_bancos = ""

    if resultado_mes[
        "cantidad_bancos"
    ] is not None:

        cantidad_bancos = str(
            resultado_mes[
                "cantidad_bancos"
            ]
        )

    cantidad_faltantes = ""

    if resultado_mes[
        "cantidad_faltantes"
    ] is not None:

        cantidad_faltantes = str(
            resultado_mes[
                "cantidad_faltantes"
            ]
        )

    return {
        "mes":
            resultado_mes[
                "mes"
            ],

        "fecha_calendario_final":
            fecha_a_texto(
                resultado_mes[
                    "fecha_calendario_final"
                ]
            ),

        "fecha_sbs":
            fecha_sbs,

        "dias_retrocedidos":
            str(
                resultado_mes[
                    "dias_retrocedidos"
                ]
            ),

        "estado":
            resultado_mes[
                "estado"
            ],

        "cantidad_bancos":
            cantidad_bancos,

        "cantidad_faltantes_bancos":
            cantidad_faltantes,

        "promedio":
            promedio,

        "html_sha256":
            (
                resultado_mes[
                    "sha256"
                ]
                or
                ""
            ),

        "fecha_hora_extraccion":
            datetime.now(
            ).astimezone(
            ).isoformat(
                timespec="seconds"
            ),

        "detalle":
            resultado_mes[
                "detalle"
            ],
    }


# ============================================================
# 25. RESUMEN TXT
# ============================================================

def escribir_resumen_txt(
    auditoria_por_mes,
    datos_por_mes
):

    CARPETA_DIAGNOSTICOS.mkdir(
        parents=True,
        exist_ok=True
    )

    lineas = []

    lineas.append(
        "EXTRACCIÓN X2 - TASA ACTIVA DE CONSUMO MN"
    )

    lineas.append(
        "Estudiante: BRICEÑO LEON CRYSTELL HIDEKI"
    )

    lineas.append(
        f"Código: {CODIGO_ESTUDIANTE}"
    )

    lineas.append(
        "Período objetivo: 2015-11 a 2025-12"
    )

    lineas.append(
        f"Meses objetivo: {len(MESES_A_EXTRAER)}"
    )

    lineas.append(
        ""
    )

    disponibles = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "DISPONIBLE"
    ]

    sin_dato = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "MES_SIN_DATO"
    ]

    errores = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "ERROR_TECNICO"
    ]

    lineas.append(
        f"Meses DISPONIBLE: {len(disponibles)}"
    )

    lineas.append(
        f"Meses MES_SIN_DATO: {len(sin_dato)}"
    )

    lineas.append(
        f"Meses ERROR_TECNICO: {len(errores)}"
    )

    total_filas = sum(
        len(
            filas
        )
        for filas in datos_por_mes.values()
    )

    lineas.append(
        f"Filas banco-mes extraídas: {total_filas}"
    )

    lineas.append(
        ""
    )

    lineas.append(
        "mes | fecha_sbs | estado | bancos | faltantes"
    )

    for mes in sorted(
        auditoria_por_mes
    ):

        fila = auditoria_por_mes[
            mes
        ]

        lineas.append(
            f"{mes} | "
            f"{fila.get('fecha_sbs', '')} | "
            f"{fila.get('estado', '')} | "
            f"{fila.get('cantidad_bancos', '')} | "
            f"{fila.get('cantidad_faltantes_bancos', '')}"
        )

    TXT_RESUMEN.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8"
    )


# ============================================================
# 26. MAIN
# ============================================================

def main():

    navegador = None

    (
        datos_por_mes,
        promedio_por_mes,
        auditoria_por_mes,
    ) = cargar_checkpoint()

    try:

        print(
            "=" * 80
        )

        print(
            "EXTRACCIÓN MENSUAL COMPLETA X2"
        )

        print(
            "=" * 80
        )

        print(
            "Variable:"
        )

        print(
            VARIABLE
        )

        print()

        print(
            "Período:"
        )

        print(
            "noviembre 2015 - diciembre 2025"
        )

        print(
            f"Meses esperados: "
            f"{len(MESES_A_EXTRAER)}"
        )

        print()

        print(
            "No se seleccionarán bancos."
        )

        print(
            "No se normalizarán nombres."
        )

        print(
            "No se interpolarán faltantes."
        )

        print(
            "Promedio se guardará por separado."
        )

        navegador = crear_navegador()

        for indice, (
            anio,
            mes
        ) in enumerate(
            MESES_A_EXTRAER,
            start=1
        ):

            clave_mes = mes_a_texto(
                anio,
                mes
            )

            print()
            print(
                f"[{indice:03d}/"
                f"{len(MESES_A_EXTRAER):03d}] "
                f"{clave_mes}"
            )

            # =================================================
            # REANUDACIÓN SEGURA
            # =================================================

            if (
                REANUDAR
                and
                checkpoint_mes_completo(
                    clave_mes,
                    datos_por_mes,
                    promedio_por_mes,
                    auditoria_por_mes
                )
            ):

                print(
                    "  [CHECKPOINT VÁLIDO] "
                    "Mes ya completado y "
                    "coherente. Se omite."
                )

                continue

            # =================================================
            # PROCESAR MES
            # =================================================

            resultado_mes = procesar_mes(
                navegador,
                anio,
                mes
            )

            # Eliminar cualquier versión previa
            # de este mes antes de guardar
            # el resultado recién obtenido.
            datos_por_mes[
                clave_mes
            ] = []

            promedio_por_mes.pop(
                clave_mes,
                None
            )

            # =================================================
            # DISPONIBLE
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                ==
                "DISPONIBLE"
            ):

                filas_datos = construir_filas_datos(
                    resultado_mes
                )

                fila_promedio = construir_fila_promedio(
                    resultado_mes
                )

                if (
                    len(
                        filas_datos
                    )
                    !=
                    resultado_mes[
                        "cantidad_bancos"
                    ]
                ):

                    raise ErrorTecnicoExtraccion(
                        f"{clave_mes}: número de filas "
                        "de bancos no coincide con "
                        "cantidad_bancos."
                    )

                datos_por_mes[
                    clave_mes
                ] = filas_datos

                promedio_por_mes[
                    clave_mes
                ] = fila_promedio

                guardar_html_crudo(
                    clave_mes,
                    resultado_mes[
                        "fecha_sbs"
                    ],
                    resultado_mes[
                        "html"
                    ]
                )

            # =================================================
            # AUDITORÍA
            # =================================================

            auditoria_por_mes[
                clave_mes
            ] = construir_fila_auditoria(
                resultado_mes
            )

            # =================================================
            # CHECKPOINT DESPUÉS DE CADA MES
            # =================================================

            guardar_checkpoint(
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            )

            escribir_resumen_txt(
                auditoria_por_mes,
                datos_por_mes
            )

            # =================================================
            # VERIFICAR QUE EL MES RECIÉN GUARDADO
            # SEA COHERENTE SI NO ES ERROR_TECNICO
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                in {
                    "DISPONIBLE",
                    "MES_SIN_DATO",
                }
                and
                not checkpoint_mes_completo(
                    clave_mes,
                    datos_por_mes,
                    promedio_por_mes,
                    auditoria_por_mes
                )
            ):

                raise ErrorTecnicoExtraccion(
                    f"{clave_mes}: el checkpoint "
                    "recién guardado no supera "
                    "la validación de coherencia."
                )

            # =================================================
            # ERROR TÉCNICO:
            # DETENER TODA LA EXTRACCIÓN
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                ==
                "ERROR_TECNICO"
            ):

                raise ErrorTecnicoExtraccion(
                    "La extracción se detuvo "
                    f"en {clave_mes} por "
                    "ERROR_TECNICO. "
                    "Lo extraído hasta este punto "
                    "quedó guardado. "
                    "Al volver a ejecutar, "
                    "REANUDAR=True retomará "
                    "desde el mes pendiente."
                )

            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

        # ====================================================
        # VALIDACIÓN FINAL DE LOS 122 MESES
        # ====================================================

        meses_finalizados = []

        for anio, mes in MESES_A_EXTRAER:

            clave_mes = mes_a_texto(
                anio,
                mes
            )

            if checkpoint_mes_completo(
                clave_mes,
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            ):

                meses_finalizados.append(
                    clave_mes
                )

        print()
        print(
            "=" * 80
        )

        print(
            "VALIDACIÓN FINAL"
        )

        print(
            "=" * 80
        )

        print(
            "Meses objetivo: "
            f"{len(MESES_A_EXTRAER)}"
        )

        print(
            "Meses completados y coherentes: "
            f"{len(meses_finalizados)}"
        )

        if (
            len(
                meses_finalizados
            )
            !=
            len(
                MESES_A_EXTRAER
            )
        ):

            raise ErrorTecnicoExtraccion(
                "La ejecución terminó pero "
                "no están completos y coherentes "
                "los 122 meses esperados."
            )

        total_filas = sum(
            len(
                filas
            )
            for filas in datos_por_mes.values()
        )

        print(
            "Filas banco-mes extraídas: "
            f"{total_filas}"
        )

        print()
        print(
            "CSV PRINCIPAL:"
        )

        print(
            CSV_DATOS
        )

        print()
        print(
            "PROMEDIOS:"
        )

        print(
            CSV_PROMEDIO
        )

        print()
        print(
            "AUDITORÍA:"
        )

        print(
            CSV_AUDITORIA
        )

        print()
        print(
            "RESUMEN:"
        )

        print(
            TXT_RESUMEN
        )

        print()
        print(
            "ESTADO = "
            "EXTRACCION_X2_COMPLETA"
        )

    except Exception as error:

        print()
        print(
            "=" * 80
        )

        print(
            "EXTRACCIÓN DETENIDA"
        )

        print(
            "=" * 80
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        print()
        print(
            "Antes de finalizar se intentará "
            "conservar el último checkpoint "
            "y el resumen."
        )

        # ====================================================
        # GUARDADO PREVENTIVO ANTES DE PROPAGAR EL ERROR
        # ====================================================

        try:

            guardar_checkpoint(
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            )

            escribir_resumen_txt(
                auditoria_por_mes,
                datos_por_mes
            )

            print()
            print(
                "[OK] CSV/checkpoints y resumen "
                "conservados antes de salir."
            )

        except Exception as error_guardado:

            print()
            print(
                "[ADVERTENCIA] También ocurrió "
                "un problema durante el guardado "
                "preventivo:"
            )

            print(
                f"{type(error_guardado).__name__}: "
                f"{error_guardado}"
            )

            print(
                "Se mantiene como error principal "
                "el que detuvo la extracción."
            )

        # IMPORTANTE:
        # no absorber la excepción.
        #
        # El bloque finally se ejecutará primero,
        # cerrando Chrome, y después esta misma
        # excepción continuará hacia el sistema
        # operativo / terminal.
        raise

    finally:

        # ====================================================
        # CIERRE GARANTIZADO DE CHROME
        # ====================================================

        if navegador is not None:

            try:

                navegador.quit()

                print()
                print(
                    "[OK] Chrome cerrado correctamente."
                )

            except Exception as error_cierre:

                print()
                print(
                    "[ADVERTENCIA] No se pudo cerrar "
                    "Chrome limpiamente:"
                )

                print(
                    f"{type(error_cierre).__name__}: "
                    f"{error_cierre}"
                )


# ============================================================
# 27. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()