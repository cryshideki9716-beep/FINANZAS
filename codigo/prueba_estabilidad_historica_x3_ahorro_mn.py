# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from datetime import date, timedelta
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
    NoSuchWindowException,
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIPasivaDepositoEmpresa.aspx?tip=B"
)

# SOLO ESTOS SEIS PUNTOS HISTÓRICOS.
#
# Cada fecha es el punto inicial de búsqueda.
# SOLO si SBS responde SIN_INFORMACION se
# retrocede día por día dentro del mismo mes.
FECHAS_CONTROL = [
    date(2015, 11, 30),
    date(2016, 6, 30),
    date(2019, 6, 28),
    date(2020, 6, 30),
    date(2023, 6, 30),
    date(2025, 12, 31),
]

TIMEOUT = 60
TIMEOUT_MANUAL = 180

PAUSA_ENTRE_DIAS = 1.2

# Intento original + máximo un reintento técnico.
MAX_REINTENTOS_TECNICOS = 1


# ============================================================
# 2. ESTRUCTURA X3 VALIDADA EN 30/11/2015
# ============================================================

ID_TABLA_MN = (
    "ctl00_cphContent_rpgActualPrimTablaMn_OT"
)

ID_DATAZONE_MN = (
    "ctl00_cphContent_"
    "rpgActualPrimTablaMn_ctl00_DataZone_DT"
)


# ============================================================
# 3. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

CARPETA_EVIDENCIA = (
    CARPETA_SALIDA
    / "evidencia_estabilidad_x3"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "prueba_estabilidad_historica_x3_ahorro_mn.txt"
)

ARCHIVO_CSV = (
    CARPETA_SALIDA
    / "prueba_estabilidad_historica_x3_ahorro_mn.csv"
)


# ============================================================
# 4. SALIDA
# ============================================================

lineas_reporte = []


def escribir(texto=""):

    texto = str(texto)

    print(texto)

    lineas_reporte.append(
        texto
    )


def titulo(texto):

    escribir()
    escribir("=" * 122)
    escribir(texto)
    escribir("=" * 122)


def subtitulo(texto):

    escribir()
    escribir("-" * 122)
    escribir(texto)
    escribir("-" * 122)


# ============================================================
# 5. ERROR TÉCNICO
# ============================================================

class ErrorTecnicoX3(Exception):
    """
    Un error técnico o del parser nunca equivale
    a ausencia de información SBS.
    """
    pass


# ============================================================
# 6. UTILIDADES DE TEXTO
# ============================================================

def limpiar_texto(valor):

    if valor is None:
        return ""

    texto = str(valor)

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


def normalizar_texto(valor):

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

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def clave_semantica(valor):

    return re.sub(
        r"[^a-z0-9]",
        "",
        normalizar_texto(
            valor
        )
    )


# ============================================================
# 7. FECHAS
# ============================================================

def fecha_a_texto(fecha):

    return fecha.strftime(
        "%d/%m/%Y"
    )


def fecha_a_iso(fecha):

    return fecha.strftime(
        "%Y-%m-%d"
    )


def mes_a_texto(fecha):

    return fecha.strftime(
        "%Y-%m"
    )


def convertir_fecha(valor):

    if valor is None:
        return None

    texto = limpiar_texto(
        valor
    )

    if not texto:
        return None

    # DD/MM/YYYY
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})"
        r"(?!\d)",
        texto
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

    # YYYY-MM-DD o representación que la contenga.
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        texto
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
# 8. NAVEGADOR
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

        opciones.add_experimental_option(
            "excludeSwitches",
            ["enable-logging"]
        )

        navegador = webdriver.Chrome(
            options=opciones
        )

        navegador.set_page_load_timeout(
            TIMEOUT
        )

        return navegador

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo iniciar Chrome/Selenium: "
            f"{type(error).__name__}: {error}"
        ) from error


def esperar_documento(navegador):

    try:

        WebDriverWait(
            navegador,
            TIMEOUT
        ).until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            )
            == "complete"
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se completó la carga del documento: "
            f"{error}"
        ) from error


# ============================================================
# 9. INVENTARIO DE CONTROLES
# ============================================================

def obtener_controles(navegador):

    try:

        return navegador.execute_script(
            r"""
            const elementos =
                Array.from(
                    document.querySelectorAll(
                        'input,select,button'
                    )
                );

            return elementos.map(el => {

                const style =
                    window.getComputedStyle(el);

                const r =
                    el.getBoundingClientRect();

                return {
                    tag:
                        el.tagName || '',

                    id:
                        el.id || '',

                    name:
                        el.name || '',

                    type:
                        el.type || '',

                    value:
                        (
                            el.value !== undefined
                            ? String(el.value)
                            : ''
                        ),

                    visible:
                        (
                            style.display !== 'none'
                            &&
                            style.visibility !== 'hidden'
                            &&
                            r.width > 0
                            &&
                            r.height > 0
                        )
                };
            });
            """
        ) or []

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudieron leer controles SBS: "
            f"{error}"
        ) from error


def info_elemento(elemento):

    return {
        "id":
            limpiar_texto(
                elemento.get_attribute(
                    "id"
                )
            ),

        "name":
            limpiar_texto(
                elemento.get_attribute(
                    "name"
                )
            ),

        "type":
            limpiar_texto(
                elemento.get_attribute(
                    "type"
                )
            ),

        "value":
            limpiar_texto(
                elemento.get_attribute(
                    "value"
                )
            ),
    }


# ============================================================
# 10. DATEPICKER VISIBLE
# ============================================================

def localizar_fecha_visible(navegador):

    selectores = [
        "input[id*='rdpDate'][id$='_dateInput']",
        "input[name*='rdpDate'][name$='$dateInput']",
        "input[id*='Date'][id$='_dateInput']",
    ]

    for selector in selectores:

        elementos = navegador.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for elemento in elementos:

            try:

                if elemento.is_displayed():
                    return elemento

            except Exception:
                continue

    return None


# ============================================================
# 11. DATEPICKER INTERNO
# ============================================================

def localizar_fecha_interna(
    navegador,
    fecha_visible,
    fecha_objetivo
):

    info_visible = info_elemento(
        fecha_visible
    )

    candidatos = []

    id_visible = info_visible[
        "id"
    ]

    name_visible = info_visible[
        "name"
    ]

    if id_visible.endswith(
        "_dateInput"
    ):

        id_base = id_visible[
            :-len(
                "_dateInput"
            )
        ]

        candidatos.extend(
            navegador.find_elements(
                By.ID,
                id_base
            )
        )

    if name_visible.endswith(
        "$dateInput"
    ):

        name_base = name_visible[
            :-len(
                "$dateInput"
            )
        ]

        candidatos.extend(
            navegador.find_elements(
                By.NAME,
                name_base
            )
        )

    vistos = set()

    for elemento in candidatos:

        try:

            info = info_elemento(
                elemento
            )

            clave = (
                info[
                    "id"
                ],
                info[
                    "name"
                ],
            )

            if clave in vistos:
                continue

            vistos.add(
                clave
            )

            if convertir_fecha(
                info[
                    "value"
                ]
            ) is not None:

                return elemento

        except Exception:
            continue

    # Fallback dinámico.
    posibles = []

    for elemento in navegador.find_elements(
        By.CSS_SELECTOR,
        "input"
    ):

        try:

            if elemento == fecha_visible:
                continue

            info = info_elemento(
                elemento
            )

            combinado = clave_semantica(
                info[
                    "id"
                ]
                + " "
                + info[
                    "name"
                ]
            )

            if (
                "date" not in combinado
                and
                "fecha" not in combinado
            ):
                continue

            fecha = convertir_fecha(
                info[
                    "value"
                ]
            )

            if fecha is None:
                continue

            posibles.append(
                elemento
            )

        except Exception:
            continue

    objetivos = []

    for elemento in posibles:

        try:

            fecha = convertir_fecha(
                elemento.get_attribute(
                    "value"
                )
            )

            if fecha == fecha_objetivo:

                objetivos.append(
                    elemento
                )

        except Exception:
            continue

    if len(
        objetivos
    ) == 1:

        return objetivos[
            0
        ]

    if len(
        posibles
    ) == 1:

        return posibles[
            0
        ]

    return None


# ============================================================
# 12. CONTROL MONEDA / ENTIDAD
# ============================================================

def seleccionar_control_contexto(
    controles,
    tipo
):

    if tipo == "moneda":

        esperado = "MN"

        palabras = [
            "moneda",
            "tipomoneda",
            "currency",
        ]

    elif tipo == "entidad":

        esperado = "B"

        palabras = [
            "entidad",
            "tipoentidad",
            "entity",
        ]

    else:

        raise ValueError(
            "Tipo de control desconocido."
        )

    candidatos = []

    for control in controles:

        valor = limpiar_texto(
            control.get(
                "value",
                ""
            )
        ).upper()

        if valor != esperado:
            continue

        combinado = clave_semantica(
            control.get(
                "id",
                ""
            )
            + " "
            + control.get(
                "name",
                ""
            )
        )

        puntaje = 0

        for palabra in palabras:

            if clave_semantica(
                palabra
            ) in combinado:

                puntaje += 100

        if (
            limpiar_texto(
                control.get(
                    "type",
                    ""
                )
            ).lower()
            == "hidden"
        ):

            puntaje += 3

        candidatos.append({
            "control":
                control,

            "puntaje":
                puntaje,
        })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x:
        x[
            "puntaje"
        ],
        reverse=True
    )

    mejor = candidatos[
        0
    ]

    mejores = [
        item
        for item in candidatos
        if item[
            "puntaje"
        ]
        == mejor[
            "puntaje"
        ]
    ]

    if (
        mejor[
            "puntaje"
        ]
        > 0
        and
        len(
            mejores
        )
        == 1
    ):

        return mejor[
            "control"
        ]

    if len(
        candidatos
    ) == 1:

        return candidatos[
            0
        ][
            "control"
        ]

    return None


# ============================================================
# 13. BOTÓN CONSULTAR
# ============================================================

def localizar_boton_consultar(navegador):

    candidatos = []

    for elemento in navegador.find_elements(
        By.CSS_SELECTOR,
        "input,button"
    ):

        try:

            if not elemento.is_displayed():
                continue

            info = info_elemento(
                elemento
            )

            combinado = normalizar_texto(
                info[
                    "id"
                ]
                + " "
                + info[
                    "name"
                ]
                + " "
                + info[
                    "value"
                ]
                + " "
                + elemento.text
            )

            if (
                "consultar" in combinado
                or
                "btnconsultar" in combinado
            ):

                candidatos.append(
                    elemento
                )

        except Exception:
            continue

    if len(
        candidatos
    ) == 1:

        return candidatos[
            0
        ]

    return None


# ============================================================
# 14. PÁGINA SBS REAL
# ============================================================

def pagina_real(navegador):

    try:

        return (
            localizar_fecha_visible(
                navegador
            )
            is not None
            and
            localizar_boton_consultar(
                navegador
            )
            is not None
        )

    except Exception:
        return False


def asegurar_pagina_real(navegador):

    try:

        WebDriverWait(
            navegador,
            15
        ).until(
            lambda d:
            pagina_real(
                d
            )
        )

        return

    except TimeoutException:

        escribir()
        escribir(
            "Si SBS muestra una verificación "
            "de seguridad, complétala manualmente."
        )

        escribir()

        input(
            "Cuando aparezca la página real, "
            "presiona ENTER..."
        )

    try:

        WebDriverWait(
            navegador,
            TIMEOUT_MANUAL
        ).until(
            lambda d:
            pagina_real(
                d
            )
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se recuperó la página SBS real."
        ) from error


def cargar_base(navegador):

    try:

        navegador.get(
            URL
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo cargar SBS: "
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
# 15. ESTABLECER FECHA
# ============================================================

def establecer_fecha(
    navegador,
    fecha_objetivo
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_NO_LOCALIZADO"
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

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo escribir la fecha."
        ) from error

    time.sleep(
        1
    )

    campo = localizar_fecha_visible(
        navegador
    )

    interno = localizar_fecha_interna(
        navegador,
        campo,
        fecha_objetivo
    )

    fecha_visible = convertir_fecha(
        campo.get_attribute(
            "value"
        )
    )

    fecha_interna = None

    if interno is not None:

        fecha_interna = convertir_fecha(
            interno.get_attribute(
                "value"
            )
        )

    if (
        fecha_visible == fecha_objetivo
        and
        fecha_interna == fecha_objetivo
    ):

        return

    # ========================================================
    # FALLBACK TELERIK
    # ========================================================

    info = info_elemento(
        campo
    )

    id_visible = info[
        "id"
    ]

    if not id_visible.endswith(
        "_dateInput"
    ):

        raise ErrorTecnicoX3(
            "NO_PUEDE_DERIVARSE_PICKER_TELERIK"
        )

    id_picker = id_visible[
        :-len(
            "_dateInput"
        )
    ]

    try:

        resultado = navegador.execute_script(
            """
            try {

                if (
                    typeof $find === 'undefined'
                ) {
                    return 'NO_$find';
                }

                const picker =
                    $find(
                        arguments[0]
                    );

                if (!picker) {
                    return 'NO_PICKER';
                }

                const fecha =
                    new Date(
                        arguments[1],
                        arguments[2] - 1,
                        arguments[3]
                    );

                picker.set_selectedDate(
                    fecha
                );

                if (
                    picker.get_dateInput
                ) {

                    const entrada =
                        picker.get_dateInput();

                    if (
                        entrada
                        &&
                        entrada.set_value
                    ) {

                        entrada.set_value(
                            arguments[4]
                        );
                    }
                }

                return 'OK';

            } catch (e) {

                return (
                    'ERROR|' +
                    e.toString()
                );
            }
            """,
            id_picker,
            fecha_objetivo.year,
            fecha_objetivo.month,
            fecha_objetivo.day,
            texto_fecha,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "Falló fallback Telerik."
        ) from error

    if resultado != "OK":

        raise ErrorTecnicoX3(
            f"Telerik devolvió {resultado!r}"
        )

    time.sleep(
        1
    )


# ============================================================
# 16. VALIDAR CONTEXTO
# ============================================================

def validar_contexto(
    navegador,
    fecha_objetivo
):

    visible = localizar_fecha_visible(
        navegador
    )

    if visible is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_VISIBLE_NO_LOCALIZADO"
        )

    fecha_visible = convertir_fecha(
        visible.get_attribute(
            "value"
        )
    )

    interno = localizar_fecha_interna(
        navegador,
        visible,
        fecha_objetivo
    )

    if interno is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_INTERNO_NO_LOCALIZADO"
        )

    fecha_interna = convertir_fecha(
        interno.get_attribute(
            "value"
        )
    )

    if (
        fecha_visible != fecha_objetivo
        or
        fecha_interna != fecha_objetivo
    ):

        raise ErrorTecnicoX3(
            "FECHA_VISIBLE_O_INTERNA_INVALIDA"
        )

    controles = obtener_controles(
        navegador
    )

    moneda = seleccionar_control_contexto(
        controles,
        "moneda"
    )

    entidad = seleccionar_control_contexto(
        controles,
        "entidad"
    )

    if moneda is None:

        raise ErrorTecnicoX3(
            "CONTROL_MONEDA_NO_UNIVOCO"
        )

    if entidad is None:

        raise ErrorTecnicoX3(
            "CONTROL_ENTIDAD_NO_UNIVOCO"
        )

    if (
        limpiar_texto(
            moneda.get(
                "value",
                ""
            )
        ).upper()
        != "MN"
    ):

        raise ErrorTecnicoX3(
            "MONEDA_NO_ES_MN"
        )

    if (
        limpiar_texto(
            entidad.get(
                "value",
                ""
            )
        ).upper()
        != "B"
    ):

        raise ErrorTecnicoX3(
            "ENTIDAD_NO_ES_B"
        )


# ============================================================
# 17. CONFIRMACIÓN EXACTA DEL PERÍODO
# ============================================================

def buscar_confirmacion_periodo(
    navegador,
    fecha_objetivo
):

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    patron = re.compile(
        rf"\bal\s+"
        rf"{re.escape(texto_fecha)}\b",
        flags=re.IGNORECASE
    )

    try:

        elementos = navegador.execute_script(
            """
            const elementos = Array.from(
                document.querySelectorAll(
                    'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th,strong,b'
                )
            );

            const salida = [];

            for (const el of elementos) {

                const style =
                    window.getComputedStyle(el);

                const r =
                    el.getBoundingClientRect();

                if (
                    style.display === 'none'
                    ||
                    style.visibility === 'hidden'
                    ||
                    r.width <= 0
                    ||
                    r.height <= 0
                ) {
                    continue;
                }

                const texto =
                    (el.innerText || '')
                    .replace(/\\s+/g, ' ')
                    .trim();

                if (
                    texto
                    &&
                    texto.length <= 800
                ) {

                    salida.push({
                        tag:
                            el.tagName,

                        id:
                            el.id || '',

                        text:
                            texto
                    });
                }
            }

            return salida;
            """
        ) or []

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo inspeccionar "
            "el período SBS."
        ) from error

    confirmaciones = []

    vistos = set()

    for item in elementos:

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


def buscar_sin_informacion(navegador):

    try:

        texto = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo leer el cuerpo SBS."
        ) from error

    return (
        "no existe informacion "
        "para la fecha elegida"
        in
        normalizar_texto(
            texto
        )
    )


# ============================================================
# 18. CONSULTAR FECHA
# ============================================================

def consultar_fecha(
    navegador,
    fecha_objetivo
):

    boton = localizar_boton_consultar(
        navegador
    )

    if boton is None:

        raise ErrorTecnicoX3(
            "BOTON_CONSULTAR_NO_UNIVOCO"
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
            0.4
        )

        boton.click()

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo pulsar Consultar."
        ) from error

    inicio = time.time()

    while (
        time.time()
        -
        inicio
        <
        TIMEOUT
    ):

        sin_info = buscar_sin_informacion(
            navegador
        )

        confirmaciones = buscar_confirmacion_periodo(
            navegador,
            fecha_objetivo
        )

        # ====================================================
        # SIN_INFORMACION TIENE PRIORIDAD
        # ====================================================

        if sin_info:

            time.sleep(
                0.5
            )

            confirmaciones_finales = (
                buscar_confirmacion_periodo(
                    navegador,
                    fecha_objetivo
                )
            )

            return {
                "respuesta":
                    "SIN_INFORMACION",

                "periodo_confirmado":
                    len(
                        confirmaciones_finales
                    )
                    > 0,
            }

        if confirmaciones:

            time.sleep(
                1.5
            )

            # Revisión final.
            if buscar_sin_informacion(
                navegador
            ):

                return {
                    "respuesta":
                        "SIN_INFORMACION",

                    "periodo_confirmado":
                        True,
                }

            confirmaciones = buscar_confirmacion_periodo(
                navegador,
                fecha_objetivo
            )

            if confirmaciones:

                return {
                    "respuesta":
                        "PERIODO_CONFIRMADO",

                    "periodo_confirmado":
                        True,
                }

        time.sleep(
            0.25
        )

    raise ErrorTecnicoX3(
        "RESPUESTA_SBS_NO_CONFIRMADA"
    )


# ============================================================
# 19. EXTRACTOR X3
#
# MISMO EXTRACTOR VALIDADO EN 30/11/2015.
# SE MANTIENEN TODAS SUS PROTECCIONES.
# ============================================================

def extraer_ahorro_mn(
    navegador
):

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    // ========================================================
    // A. UTILIDADES
    // ========================================================

    function original(el) {

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

    function overlapHorizontal(
        a,
        b
    ) {

        const overlap =
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

        return overlap / base;
    }

    function overlapVertical(
        a,
        b
    ) {

        const overlap =
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

        return overlap / base;
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

    function esFaltanteExplicito(txt) {

        const n =
            normal(txt);

        const faltantes =
            new Set([
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

    function esValorTasa(txt) {

        return (
            esNumero(txt)
            ||
            esFaltante(txt)
        );
    }

    function terminalConTexto(
        elemento,
        textoNormal
    ) {

        const descendientes =
            Array.from(
                elemento.querySelectorAll(
                    'td,th,span,label,div'
                )
            );

        for (
            const hijo
            of descendientes
        ) {

            if (
                hijo === elemento
                ||
                !visible(hijo)
            ) {
                continue;
            }

            if (
                normal(
                    hijo.innerText
                    ||
                    hijo.textContent
                )
                ===
                textoNormal
            ) {

                return false;
            }
        }

        return true;
    }

    // ========================================================
    // B. TABLAS VALIDAS
    // ========================================================

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
                'TABLA_CONTENEDORA_MN_NO_EXISTE'
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
                'TABLA_CONTENEDORA_MN_NO_VISIBLE'
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

    const rectData =
        rectInfo(
            data
        );

    // ========================================================
    // C. EXACTAMENTE UNA ETIQUETA DEPÓSITOS DE AHORRO
    // ========================================================

    const etiquetasAhorro = [];

    const elementosOuter =
        Array.from(
            outer.querySelectorAll(
                'td,th,span,label,div'
            )
        );

    for (
        const el
        of elementosOuter
    ) {

        if (!visible(el)) {
            continue;
        }

        const texto =
            original(el);

        if (
            normal(texto)
            !==
            'depositos de ahorro'
        ) {
            continue;
        }

        if (
            !terminalConTexto(
                el,
                'depositos de ahorro'
            )
        ) {
            continue;
        }

        etiquetasAhorro.push({
            element:
                el,

            text:
                texto,

            tag:
                el.tagName,

            id:
                el.id || '',

            rect:
                rectInfo(el),

            tableId:
                (
                    el.closest('table')
                    &&
                    el.closest('table').id
                )
                ||
                ''
        });
    }

    if (
        etiquetasAhorro.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'DEPOSITOS_AHORRO_NO_UNIVOCO',

            ahorroCount:
                etiquetasAhorro.length
        };
    }

    const etiquetaAhorro =
        etiquetasAhorro[0];

    // ========================================================
    // D. FILAS NUMÉRICAS
    // ========================================================

    const filasDOM =
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
        i < filasDOM.length;
        i++
    ) {

        const fila =
            filasDOM[i];

        if (!visible(fila)) {
            continue;
        }

        const celdas =
            Array.from(
                fila.children
            )
            .filter(
                celda =>
                    (
                        celda.tagName === 'TD'
                        ||
                        celda.tagName === 'TH'
                    )
                    &&
                    visible(celda)
            );

        if (
            celdas.length < 2
        ) {
            continue;
        }

        const valores =
            celdas.map(
                celda =>
                    original(
                        celda
                    )
            );

        const todosValores =
            valores.every(
                valor =>
                    esValorTasa(
                        valor
                    )
            );

        const tieneContenidoInformativo =
            valores.some(
                valor =>
                    esNumero(
                        valor
                    )
                    ||
                    esFaltanteExplicito(
                        valor
                    )
            );

        if (
            todosValores
            &&
            tieneContenidoInformativo
        ) {

            filasNumericas.push({
                index:
                    i,

                element:
                    fila,

                cells:
                    celdas,

                values:
                    valores,

                rect:
                    rectInfo(
                        fila
                    )
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
                'NO_SE_DETECTARON_FILAS_NUMERICAS'
        };
    }

    // ========================================================
    // E. LOCALIZAR COLUMNA DEPÓSITOS DE AHORRO
    //    SIN OFFSET FIJO
    // ========================================================

    const mapeosColumna = [];

    for (
        const fila
        of filasNumericas
    ) {

        const candidatos = [];

        for (
            let j = 0;
            j < fila.cells.length;
            j++
        ) {

            const celda =
                fila.cells[j];

            const rect =
                rectInfo(
                    celda
                );

            const overlap =
                overlapHorizontal(
                    etiquetaAhorro.rect,
                    rect
                );

            const distancia =
                Math.abs(
                    etiquetaAhorro
                    .rect
                    .centerX
                    -
                    rect.centerX
                );

            const contieneCentro =
                (
                    etiquetaAhorro
                    .rect
                    .centerX
                    >=
                    rect.left
                    &&
                    etiquetaAhorro
                    .rect
                    .centerX
                    <=
                    rect.right
                );

            candidatos.push({
                index:
                    j,

                overlap:
                    overlap,

                distancia:
                    distancia,

                contieneCentro:
                    contieneCentro,

                rect:
                    rect
            });
        }

        candidatos.sort(
            (a, b) => {

                if (
                    Number(
                        b.contieneCentro
                    )
                    !==
                    Number(
                        a.contieneCentro
                    )
                ) {

                    return (
                        Number(
                            b.contieneCentro
                        )
                        -
                        Number(
                            a.contieneCentro
                        )
                    );
                }

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

        if (!mejor) {

            return {
                ok:
                    false,

                error:
                    'COLUMNA_AHORRO_NO_MAPEADA'
            };
        }

        if (
            !mejor.contieneCentro
            &&
            mejor.overlap < 0.25
        ) {

            return {
                ok:
                    false,

                error:
                    'ALINEACION_HORIZONTAL_AHORRO_INSUFICIENTE',

                fila:
                    fila.index,

                overlap:
                    mejor.overlap,

                distancia:
                    mejor.distancia
            };
        }

        // ====================================================
        // PROTECCIÓN DE AMBIGÜEDAD DEL EXTRACTOR VALIDADO
        // ====================================================

        if (
            candidatos.length > 1
        ) {

            const segundo =
                candidatos[1];

            const empateCentro =
                (
                    mejor.contieneCentro
                    ===
                    segundo.contieneCentro
                );

            const empateOverlap =
                Math.abs(
                    mejor.overlap
                    -
                    segundo.overlap
                )
                <
                0.000001;

            const empateDistancia =
                Math.abs(
                    mejor.distancia
                    -
                    segundo.distancia
                )
                <
                0.5;

            if (
                empateCentro
                &&
                empateOverlap
                &&
                empateDistancia
            ) {

                return {
                    ok:
                        false,

                    error:
                        'COLUMNA_AHORRO_AMBIGUA',

                    fila:
                        fila.index,

                    mejor:
                        {
                            index:
                                mejor.index,

                            contieneCentro:
                                mejor.contieneCentro,

                            overlap:
                                mejor.overlap,

                            distancia:
                                mejor.distancia
                        },

                    segundo:
                        {
                            index:
                                segundo.index,

                            contieneCentro:
                                segundo.contieneCentro,

                            overlap:
                                segundo.overlap,

                            distancia:
                                segundo.distancia
                        }
                };
            }
        }

        mapeosColumna.push({
            rowIndex:
                fila.index,

            columnIndex:
                mejor.index,

            value:
                fila.values[
                    mejor.index
                ],

            overlap:
                mejor.overlap,

            distance:
                mejor.distancia,

            containsCenter:
                mejor.contieneCentro
        });
    }

    // ========================================================
    // F. LA COLUMNA DEBE SER CONSISTENTE
    // ========================================================

    const indicesColumna =
        Array.from(
            new Set(
                mapeosColumna.map(
                    x =>
                        x.columnIndex
                )
            )
        );

    if (
        indicesColumna.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'INDICE_COLUMNA_AHORRO_INCONSISTENTE',

            columnIndices:
                indicesColumna,

            mappings:
                mapeosColumna
        };
    }

    const indiceColumnaAhorro =
        indicesColumna[0];

    // ========================================================
    // G. CANDIDATOS DE NOMBRE
    // ========================================================

    const excluidos =
        new Set([
            'depositos de ahorro',
            'depositos a plazo',
            'depositos cts',
            'hasta 30 dias',
            '31-90 dias',
            '91-180 dias',
            '181-360 dias',
            'mas de 360 dias',
            'moneda nacional',
            'moneda extranjera',
            'empresa',
            'empresas',
            'tasa',
            'tasas',
            '%'
        ]);

    const candidatosNombre = [];

    for (
        const el
        of elementosOuter
    ) {

        if (!visible(el)) {
            continue;
        }

        if (
            data.contains(
                el
            )
        ) {
            continue;
        }

        const texto =
            original(
                el
            );

        const n =
            normal(
                texto
            );

        if (!n) {
            continue;
        }

        if (
            excluidos.has(
                n
            )
        ) {
            continue;
        }

        if (
            n.includes(
                'tasas pasivas'
            )
            ||
            n.includes(
                'ultimos 30 dias'
            )
            ||
            n.includes(
                'tipo de deposito'
            )
        ) {
            continue;
        }

        if (
            !terminalConTexto(
                el,
                n
            )
        ) {
            continue;
        }

        if (
            esNumero(
                texto
            )
            ||
            esFaltante(
                texto
            )
        ) {
            continue;
        }

        const rect =
            rectInfo(
                el
            );

        const estaALaIzquierda =
            (
                rect.centerX
                <
                rectData.left
                +
                40
            );

        candidatosNombre.push({
            element:
                el,

            text:
                texto,

            normal:
                n,

            tag:
                el.tagName,

            id:
                el.id || '',

            rect:
                rect,

            estaALaIzquierda:
                estaALaIzquierda,

            tableId:
                (
                    el.closest('table')
                    &&
                    el.closest('table').id
                )
                ||
                ''
        });
    }

    if (
        candidatosNombre.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_HAY_CANDIDATOS_DE_NOMBRES'
        };
    }

    // ========================================================
    // H. MAPEAR FILA NUMÉRICA A NOMBRE
    // ========================================================

    const filasMapeadas = [];

    for (
        const fila
        of filasNumericas
    ) {

        const candidatos = [];

        for (
            const nombre
            of candidatosNombre
        ) {

            const overlap =
                overlapVertical(
                    fila.rect,
                    nombre.rect
                );

            if (
                overlap < 0.50
            ) {
                continue;
            }

            const distanciaVertical =
                Math.abs(
                    fila.rect.centerY
                    -
                    nombre.rect.centerY
                );

            const distanciaHorizontal =
                Math.max(
                    0,
                    rectData.left
                    -
                    nombre.rect.right
                );

            let score =
                overlap
                *
                1000;

            if (
                nombre.estaALaIzquierda
            ) {

                score += 100;
            }

            score -= (
                distanciaVertical
                *
                10
            );

            score -= (
                distanciaHorizontal
                /
                100
            );

            candidatos.push({
                nombre:
                    nombre,

                overlap:
                    overlap,

                distanciaVertical:
                    distanciaVertical,

                distanciaHorizontal:
                    distanciaHorizontal,

                score:
                    score
            });
        }

        candidatos.sort(
            (a, b) =>
                b.score
                -
                a.score
        );

        if (
            candidatos.length === 0
        ) {

            return {
                ok:
                    false,

                error:
                    'FILA_NUMERICA_SIN_NOMBRE',

                rowIndex:
                    fila.index
            };
        }

        const mejor =
            candidatos[0];

        // Mantener protección de ambigüedad
        // del mapeo vertical.
        if (
            candidatos.length > 1
        ) {

            const segundo =
                candidatos[1];

            if (
                Math.abs(
                    mejor.score
                    -
                    segundo.score
                )
                <
                0.001
            ) {

                return {
                    ok:
                        false,

                    error:
                        'NOMBRE_DE_FILA_AMBIGUO',

                    rowIndex:
                        fila.index,

                    candidato1:
                        mejor.nombre.text,

                    candidato2:
                        segundo.nombre.text
                };
            }
        }

        const valorAhorro =
            fila.values[
                indiceColumnaAhorro
            ];

        filasMapeadas.push({
            dataRowIndex:
                fila.index,

            banco_original:
                mejor.nombre.text,

            bancoTag:
                mejor.nombre.tag,

            bancoId:
                mejor.nombre.id,

            bancoTableId:
                mejor.nombre.tableId,

            verticalOverlap:
                mejor.overlap,

            tasa:
                valorAhorro,

            faltante:
                esFaltante(
                    valorAhorro
                ),

            esPromedio:
                normal(
                    mejor.nombre.text
                )
                ===
                'promedio'
        });
    }

    // ========================================================
    // I. NOMBRES ÚNICOS
    // ========================================================

    const clavesNombre =
        filasMapeadas.map(
            x =>
                normal(
                    x.banco_original
                )
        );

    const nombresUnicos =
        new Set(
            clavesNombre
        );

    if (
        nombresUnicos.size
        !==
        filasMapeadas.length
    ) {

        return {
            ok:
                false,

            error:
                'NOMBRES_MAPEADOS_NO_UNICOS',

            names:
                clavesNombre
        };
    }

    // ========================================================
    // J. PROMEDIO
    // ========================================================

    const promedios =
        filasMapeadas.filter(
            x =>
                x.esPromedio
        );

    if (
        promedios.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'PROMEDIO_NO_UNIVOCO',

            promedioCount:
                promedios.length
        };
    }

    const promedio =
        promedios[0];

    const bancos =
        filasMapeadas.filter(
            x =>
                !x.esPromedio
        );

    // ========================================================
    // K. VALIDACIONES DE CANTIDAD
    // ========================================================

    const totalValoresObjetivo =
        mapeosColumna.length;

    const totalFilasMapeadas =
        filasMapeadas.length;

    if (
        totalFilasMapeadas
        !==
        totalValoresObjetivo
    ) {

        return {
            ok:
                false,

            error:
                'NUMERO_NOMBRES_DISTINTO_DE_VALORES',

            totalNames:
                totalFilasMapeadas,

            totalValues:
                totalValoresObjetivo
        };
    }

    if (
        bancos.length
        +
        1
        !==
        totalValoresObjetivo
    ) {

        return {
            ok:
                false,

            error:
                'BANCOS_MAS_PROMEDIO_NO_COINCIDEN',

            bankCount:
                bancos.length,

            totalValues:
                totalValoresObjetivo
        };
    }

    // ========================================================
    // L. RESULTADO
    // ========================================================

    return {
        ok:
            true,

        outerId:
            outer.id,

        dataZoneId:
            data.id,

        ahorroLabelCount:
            etiquetasAhorro.length,

        ahorroLabelText:
            etiquetaAhorro.text,

        ahorroLabelId:
            etiquetaAhorro.id,

        ahorroLabelTableId:
            etiquetaAhorro.tableId,

        ahorroColumnIndex:
            indiceColumnaAhorro,

        numericRowCount:
            filasNumericas.length,

        targetValueCount:
            totalValoresObjetivo,

        mappedRowCount:
            totalFilasMapeadas,

        bankCount:
            bancos.length,

        missingBankCount:
            bancos.filter(
                x =>
                    x.faltante
            ).length,

        bancos:
            bancos,

        promedio:
            promedio,

        mappings:
            filasMapeadas,

        columnMappings:
            mapeosColumna
    };
    """

    try:

        resultado = navegador.execute_script(
            script,
            ID_TABLA_MN,
            ID_DATAZONE_MN,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "Falló el extractor geométrico X3: "
            f"{error}"
        ) from error

    if not resultado.get(
        "ok",
        False
    ):

        # Si tabla/DataZone estaban presentes y
        # llegamos hasta el parser, cualquier
        # fallo del extractor es técnico/parser.
        raise ErrorTecnicoX3(
            "El extractor geométrico X3 falló "
            "sobre una estructura presente. "
            f"Detalle={resultado}"
        )

    return resultado


# ============================================================
# 20. INSPECCIONAR ESTRUCTURA VALIDADA
# ============================================================

def inspeccionar_estructura_validada(
    navegador
):
    """
    Solo comprueba existencia y visibilidad de
    los dos IDs validados.

    NO intenta descubrir otra tabla alternativa.
    """

    try:

        resultado = navegador.execute_script(
            """
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

            const outer =
                document.getElementById(
                    arguments[0]
                );

            const data =
                document.getElementById(
                    arguments[1]
                );

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
                    : false
            };
            """,
            ID_TABLA_MN,
            ID_DATAZONE_MN,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo inspeccionar "
            "tabla/DataZone X3."
        ) from error

    return resultado


# ============================================================
# 21. EVALUAR UNA FECHA
# ============================================================

def evaluar_dia(
    navegador,
    fecha_objetivo
):
    """
    Posibles resultados NO técnicos:

      SIN_INFORMACION
      ESTRUCTURA_X3_NO_COMPATIBLE
      DISPONIBLE

    Regla fundamental:

      SOLO SIN_INFORMACION autoriza
      retroceder al día anterior.

    Si el período está confirmado pero
    la estructura validada no está presente,
    se devuelve ESTRUCTURA_X3_NO_COMPATIBLE.

    Si la estructura está presente y falla
    el parser geométrico, se lanza
    ErrorTecnicoX3.
    """

    cargar_base(
        navegador
    )

    establecer_fecha(
        navegador,
        fecha_objetivo
    )

    validar_contexto(
        navegador,
        fecha_objetivo
    )

    respuesta = consultar_fecha(
        navegador,
        fecha_objetivo
    )

    # ========================================================
    # A. SIN INFORMACIÓN
    #
    # ÚNICO ESTADO QUE PERMITE RETROCEDER.
    # ========================================================

    if (
        respuesta[
            "respuesta"
        ]
        ==
        "SIN_INFORMACION"
    ):

        return {
            "estado":
                "SIN_INFORMACION",

            "extraccion":
                None,

            "estructura":
                None,
        }

    # ========================================================
    # B. PERÍODO DEBE ESTAR CONFIRMADO
    # ========================================================

    if (
        respuesta[
            "respuesta"
        ]
        !=
        "PERIODO_CONFIRMADO"
        or
        not respuesta[
            "periodo_confirmado"
        ]
    ):

        raise ErrorTecnicoX3(
            "PERIODO_EXACTO_NO_CONFIRMADO"
        )

    # Confirmar otra vez fecha + MN + B
    # después del POST.
    validar_contexto(
        navegador,
        fecha_objetivo
    )

    # ========================================================
    # C. COMPROBAR ESTRUCTURA X3 VALIDADA
    # ========================================================

    estructura = inspeccionar_estructura_validada(
        navegador
    )

    estructura_compatible = (
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
    )

    if not estructura_compatible:

        # IMPORTANTE:
        # la fecha sí fue confirmada por SBS.
        #
        # Esto NO es SIN_INFORMACION.
        # Esto NO permite retroceder.
        return {
            "estado":
                "ESTRUCTURA_X3_NO_COMPATIBLE",

            "extraccion":
                None,

            "estructura":
                estructura,
        }

    # ========================================================
    # D. EXTRACTOR GEOMÉTRICO VALIDADO
    #
    # Si falla aquí → error técnico/parser.
    # NO se retrocede.
    # ========================================================

    extraccion = extraer_ahorro_mn(
        navegador
    )

    try:

        html = navegador.page_source

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo recuperar HTML "
            "de la fecha válida."
        ) from error

    sha256 = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    return {
        "estado":
            "DISPONIBLE",

        "extraccion":
            extraccion,

        "estructura":
            estructura,

        "html":
            html,

        "sha256":
            sha256,
    }


# ============================================================
# 22. REINTENTO TÉCNICO
# ============================================================

def evaluar_dia_con_reintento(
    navegador,
    fecha_objetivo
):

    errores = []

    total_intentos = (
        1
        +
        MAX_REINTENTOS_TECNICOS
    )

    for numero in range(
        total_intentos
    ):

        try:

            if numero > 0:

                escribir(
                    "    [REINTENTO TÉCNICO] "
                    f"{fecha_a_texto(fecha_objetivo)}"
                )

                time.sleep(
                    2
                )

            resultado = evaluar_dia(
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
            ErrorTecnicoX3,
            TimeoutException,
            WebDriverException,
            StaleElementReferenceException,
            NoSuchWindowException,
        ) as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            errores.append(
                detalle
            )

            escribir(
                f"    ERROR TÉCNICO "
                f"{numero + 1}/{total_intentos}: "
                f"{detalle}"
            )

            if (
                numero
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

            escribir(
                f"    ERROR TÉCNICO NO CLASIFICADO "
                f"{numero + 1}/{total_intentos}: "
                f"{detalle}"
            )

            if (
                numero
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
# 23. GUARDAR EVIDENCIA
# ============================================================

def guardar_evidencia(
    navegador,
    fecha_inicial,
    fecha_sbs,
    html
):

    CARPETA_EVIDENCIA.mkdir(
        parents=True,
        exist_ok=True
    )

    prefijo = (
        f"X3_{mes_a_texto(fecha_inicial)}_"
        f"{fecha_a_iso(fecha_sbs)}"
    )

    ruta_html = (
        CARPETA_EVIDENCIA
        /
        f"{prefijo}.html"
    )

    ruta_png = (
        CARPETA_EVIDENCIA
        /
        f"{prefijo}.png"
    )

    ruta_html.write_text(
        html,
        encoding="utf-8"
    )

    navegador.save_screenshot(
        str(
            ruta_png
        )
    )


# ============================================================
# 24. REGISTRO BASE PARA UN PUNTO
# ============================================================

def registro_base(
    fecha_inicial
):

    return {
        "mes":
            mes_a_texto(
                fecha_inicial
            ),

        "fecha_inicial":
            fecha_a_texto(
                fecha_inicial
            ),

        "fecha_sbs":
            "",

        "dias_retrocedidos":
            0,

        "tabla_mn":
            ID_TABLA_MN,

        "datazone_mn":
            ID_DATAZONE_MN,

        "cantidad_bancos":
            "",

        "cantidad_faltantes":
            "",

        "promedio":
            "",

        "estado":
            "",

        "sha256":
            "",

        "detalle":
            "",
    }


# ============================================================
# 25. PROCESAR UN PUNTO HISTÓRICO
# ============================================================

def procesar_fecha_control(
    navegador,
    fecha_inicial
):

    anio = fecha_inicial.year
    mes = fecha_inicial.month

    fecha_intento = fecha_inicial

    dias_retrocedidos = 0

    titulo(
        f"PRUEBA HISTÓRICA "
        f"{fecha_a_texto(fecha_inicial)}"
    )

    escribir(
        f"Mes = "
        f"{mes_a_texto(fecha_inicial)}"
    )

    escribir(
        f"Fecha inicial solicitada = "
        f"{fecha_a_texto(fecha_inicial)}"
    )

    escribir()
    escribir(
        "Regla:"
    )

    escribir(
        "  SOLO SIN_INFORMACION permite "
        "retroceder al día anterior."
    )

    escribir(
        "  ESTRUCTURA_X3_NO_COMPATIBLE "
        "detiene este punto."
    )

    escribir(
        "  ERROR_TECNICO/parser "
        "detiene la prueba."
    )

    while (
        fecha_intento.year == anio
        and
        fecha_intento.month == mes
    ):

        escribir()
        escribir(
            f"Probando: "
            f"{fecha_a_texto(fecha_intento)} "
            f"(retroceso={dias_retrocedidos})"
        )

        evaluacion = evaluar_dia_con_reintento(
            navegador,
            fecha_intento
        )

        # ====================================================
        # A. ERROR TÉCNICO
        # ====================================================

        if not evaluacion[
            "ok"
        ]:

            escribir()
            escribir(
                "ESTADO DEL PUNTO = "
                "ERROR_TECNICO"
            )

            salida = registro_base(
                fecha_inicial
            )

            salida.update({
                "fecha_sbs":
                    fecha_a_texto(
                        fecha_intento
                    ),

                "dias_retrocedidos":
                    dias_retrocedidos,

                "estado":
                    "ERROR_TECNICO",

                "detalle":
                    " || ".join(
                        evaluacion[
                            "errores"
                        ]
                    ),
            })

            return salida

        resultado = evaluacion[
            "resultado"
        ]

        estado = resultado[
            "estado"
        ]

        # ====================================================
        # B. DISPONIBLE
        # ====================================================

        if estado == "DISPONIBLE":

            extraccion = resultado[
                "extraccion"
            ]

            guardar_evidencia(
                navegador,
                fecha_inicial,
                fecha_intento,
                resultado[
                    "html"
                ]
            )

            escribir()
            escribir(
                "[OK] FECHA VÁLIDA ENCONTRADA"
            )

            escribir(
                f"Fecha SBS usada = "
                f"{fecha_a_texto(fecha_intento)}"
            )

            escribir(
                f"Tabla MN = "
                f"{extraccion['outerId']}"
            )

            escribir(
                f"DataZone MN = "
                f"{extraccion['dataZoneId']}"
            )

            escribir(
                f"Bancos = "
                f"{extraccion['bankCount']}"
            )

            escribir(
                f"Faltantes = "
                f"{extraccion['missingBankCount']}"
            )

            escribir(
                f"Promedio = "
                f"{extraccion['promedio']['tasa']!r}"
            )

            escribir(
                f"Total nombres/valores = "
                f"{extraccion['mappedRowCount']}"
            )

            escribir(
                f"Columna Ahorro detectada "
                f"dinámicamente = "
                f"{extraccion['ahorroColumnIndex']}"
            )

            escribir(
                "ESTADO DEL PUNTO = DISPONIBLE"
            )

            salida = registro_base(
                fecha_inicial
            )

            salida.update({
                "fecha_sbs":
                    fecha_a_texto(
                        fecha_intento
                    ),

                "dias_retrocedidos":
                    dias_retrocedidos,

                "tabla_mn":
                    extraccion[
                        "outerId"
                    ],

                "datazone_mn":
                    extraccion[
                        "dataZoneId"
                    ],

                "cantidad_bancos":
                    extraccion[
                        "bankCount"
                    ],

                "cantidad_faltantes":
                    extraccion[
                        "missingBankCount"
                    ],

                "promedio":
                    extraccion[
                        "promedio"
                    ][
                        "tasa"
                    ],

                "estado":
                    "DISPONIBLE",

                "sha256":
                    resultado[
                        "sha256"
                    ],

                "detalle":
                    (
                        f"nombres_valores="
                        f"{extraccion['mappedRowCount']}; "
                        f"columna_ahorro="
                        f"{extraccion['ahorroColumnIndex']}"
                    ),
            })

            return salida

        # ====================================================
        # C. ESTRUCTURA NO COMPATIBLE
        #
        # FECHA CONFIRMADA POR SBS.
        # NO RETROCEDER.
        # ====================================================

        if (
            estado
            ==
            "ESTRUCTURA_X3_NO_COMPATIBLE"
        ):

            estructura = resultado[
                "estructura"
            ]

            escribir()
            escribir(
                "[ATENCIÓN] SBS confirmó "
                f"'al {fecha_a_texto(fecha_intento)}', "
                "pero la estructura X3 validada "
                "no está disponible/visible."
            )

            escribir(
                f"Tabla existe = "
                f"{estructura['outerExists']}"
            )

            escribir(
                f"Tabla visible = "
                f"{estructura['outerVisible']}"
            )

            escribir(
                f"DataZone existe = "
                f"{estructura['dataExists']}"
            )

            escribir(
                f"DataZone visible = "
                f"{estructura['dataVisible']}"
            )

            escribir()
            escribir(
                "NO se retrocederá al día anterior."
            )

            escribir(
                "ESTADO DEL PUNTO = "
                "ESTRUCTURA_X3_NO_COMPATIBLE"
            )

            salida = registro_base(
                fecha_inicial
            )

            salida.update({
                "fecha_sbs":
                    fecha_a_texto(
                        fecha_intento
                    ),

                "dias_retrocedidos":
                    dias_retrocedidos,

                "estado":
                    "ESTRUCTURA_X3_NO_COMPATIBLE",

                "detalle":
                    (
                        f"periodo_confirmado=True; "
                        f"outerExists="
                        f"{estructura['outerExists']}; "
                        f"outerVisible="
                        f"{estructura['outerVisible']}; "
                        f"dataExists="
                        f"{estructura['dataExists']}; "
                        f"dataVisible="
                        f"{estructura['dataVisible']}"
                    ),
            })

            return salida

        # ====================================================
        # D. SIN INFORMACIÓN
        #
        # ÚNICO CASO QUE AUTORIZA RETROCEDER.
        # ====================================================

        if estado == "SIN_INFORMACION":

            escribir(
                "  SIN_INFORMACION"
            )

            escribir(
                "  → se autoriza retroceder "
                "un día dentro del mismo mes."
            )

            if fecha_intento.day == 1:

                break

            fecha_intento = (
                fecha_intento
                -
                timedelta(days=1)
            )

            dias_retrocedidos += 1

            time.sleep(
                PAUSA_ENTRE_DIAS
            )

            continue

        # ====================================================
        # E. CUALQUIER ESTADO DESCONOCIDO ES TÉCNICO
        # ====================================================

        raise ErrorTecnicoX3(
            f"Estado diario desconocido: "
            f"{estado}"
        )

    # ========================================================
    # MES SIN DATO
    #
    # SOLO SE LLEGA AQUÍ SI TODOS LOS DÍAS
    # PROBADOS HASTA EL DÍA 1 DEVOLVIERON
    # SIN_INFORMACION.
    # ========================================================

    escribir()
    escribir(
        "ESTADO DEL PUNTO = MES_SIN_DATO"
    )

    escribir(
        "Todos los días evaluados desde la "
        "fecha inicial hasta el día 1 "
        "respondieron SIN_INFORMACION."
    )

    salida = registro_base(
        fecha_inicial
    )

    salida.update({
        "dias_retrocedidos":
            dias_retrocedidos,

        "cantidad_bancos":
            0,

        "cantidad_faltantes":
            0,

        "estado":
            "MES_SIN_DATO",

        "detalle":
            (
                "Todos los días evaluados "
                "hasta el día 1 devolvieron "
                "SIN_INFORMACION."
            ),
    })

    return salida


# ============================================================
# 26. GUARDAR CSV
# ============================================================

def guardar_csv(resultados):

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    columnas = [
        "mes",
        "fecha_inicial",
        "fecha_sbs",
        "dias_retrocedidos",
        "tabla_mn",
        "datazone_mn",
        "cantidad_bancos",
        "cantidad_faltantes",
        "promedio",
        "estado",
        "sha256",
        "detalle",
    ]

    with ARCHIVO_CSV.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas
        )

        escritor.writeheader()

        for resultado in resultados:

            escritor.writerow(
                resultado
            )


# ============================================================
# 27. RESUMEN FINAL
# ============================================================

def mostrar_resumen(resultados):

    titulo(
        "RESUMEN DE ESTABILIDAD HISTÓRICA X3"
    )

    escribir(
        "mes | fecha_inicial | fecha_sbs | "
        "tabla | DataZone | bancos | "
        "faltantes | Promedio | estado"
    )

    for resultado in resultados:

        escribir(
            f"{resultado['mes']} | "
            f"{resultado['fecha_inicial']} | "
            f"{resultado['fecha_sbs']} | "
            f"{resultado['tabla_mn']} | "
            f"{resultado['datazone_mn']} | "
            f"{resultado['cantidad_bancos']} | "
            f"{resultado['cantidad_faltantes']} | "
            f"{resultado['promedio']} | "
            f"{resultado['estado']}"
        )

    disponibles = [
        r
        for r in resultados
        if r[
            "estado"
        ]
        == "DISPONIBLE"
    ]

    sin_dato = [
        r
        for r in resultados
        if r[
            "estado"
        ]
        == "MES_SIN_DATO"
    ]

    incompatibles = [
        r
        for r in resultados
        if r[
            "estado"
        ]
        == "ESTRUCTURA_X3_NO_COMPATIBLE"
    ]

    errores = [
        r
        for r in resultados
        if r[
            "estado"
        ]
        == "ERROR_TECNICO"
    ]

    subtitulo(
        "CONTROL GENERAL"
    )

    escribir(
        f"Puntos solicitados = "
        f"{len(FECHAS_CONTROL)}"
    )

    escribir(
        f"DISPONIBLE = "
        f"{len(disponibles)}"
    )

    escribir(
        f"MES_SIN_DATO = "
        f"{len(sin_dato)}"
    )

    escribir(
        f"ESTRUCTURA_X3_NO_COMPATIBLE = "
        f"{len(incompatibles)}"
    )

    escribir(
        f"ERROR_TECNICO = "
        f"{len(errores)}"
    )

    # ========================================================
    # ESTABILIDAD DE IDs ENTRE FECHAS DISPONIBLES
    # ========================================================

    if disponibles:

        tablas = {
            r[
                "tabla_mn"
            ]
            for r in disponibles
        }

        datazones = {
            r[
                "datazone_mn"
            ]
            for r in disponibles
        }

        escribir()
        escribir(
            f"Tablas MN distintas "
            f"entre puntos disponibles = "
            f"{len(tablas)}"
        )

        for tabla in sorted(
            tablas
        ):

            escribir(
                f"  - {tabla}"
            )

        escribir(
            f"DataZones MN distintas "
            f"entre puntos disponibles = "
            f"{len(datazones)}"
        )

        for datazone in sorted(
            datazones
        ):

            escribir(
                f"  - {datazone}"
            )

    escribir()
    escribir(
        "No se interpolaron faltantes."
    )

    escribir(
        "No se homologaron nombres bancarios."
    )

    escribir(
        "No se seleccionaron bancos."
    )

    escribir(
        "No se ejecutaron los 122 meses."
    )

    escribir(
        "Solo se probaron los seis puntos "
        "históricos solicitados."
    )

    # ========================================================
    # CLASIFICACIÓN FINAL
    # ========================================================

    titulo(
        "CLASIFICACIÓN FINAL"
    )

    if len(
        errores
    ) > 0:

        escribir(
            "ESTADO = "
            "ESTABILIDAD_HISTORICA_X3_CON_ERROR_TECNICO"
        )

        escribir()
        escribir(
            "Existe al menos un error técnico/parser."
        )

    elif (
        len(
            incompatibles
        )
        > 0
        or
        len(
            sin_dato
        )
        > 0
        or
        len(
            resultados
        )
        !=
        len(
            FECHAS_CONTROL
        )
    ):

        escribir(
            "ESTADO = "
            "ESTABILIDAD_HISTORICA_X3_REQUIERE_REVISION"
        )

        if incompatibles:

            escribir()
            escribir(
                "Existe al menos una fecha cuyo "
                "período fue confirmado por SBS "
                "pero cuya estructura no coincide "
                "con la estructura X3 validada."
            )

        if sin_dato:

            escribir()
            escribir(
                "Existe al menos un mes en el que "
                "todas las fechas evaluadas "
                "respondieron SIN_INFORMACION."
            )

    elif (
        len(
            disponibles
        )
        ==
        len(
            FECHAS_CONTROL
        )
    ):

        escribir(
            "ESTADO = "
            "ESTABILIDAD_HISTORICA_X3_VALIDADA"
        )

        escribir()
        escribir(
            "Los seis puntos pudieron extraerse "
            "con la estructura y metodología "
            "geométrica ya validada."
        )

    else:

        escribir(
            "ESTADO = "
            "ESTABILIDAD_HISTORICA_X3_REQUIERE_REVISION"
        )


# ============================================================
# 28. MAIN
# ============================================================

def main():

    navegador = None

    resultados = []

    error_pendiente = None

    try:

        CARPETA_SALIDA.mkdir(
            parents=True,
            exist_ok=True
        )

        CARPETA_EVIDENCIA.mkdir(
            parents=True,
            exist_ok=True
        )

        titulo(
            "PRUEBA DE ESTABILIDAD HISTÓRICA X3 "
            "- DEPÓSITOS DE AHORRO MN"
        )

        escribir(
            "Extractor:"
        )

        escribir(
            "  misma metodología validada "
            "en 30/11/2015."
        )

        escribir()
        escribir(
            "Fechas iniciales:"
        )

        for fecha in FECHAS_CONTROL:

            escribir(
                f"  - {fecha_a_texto(fecha)}"
            )

        escribir()
        escribir(
            "REGLA DE RETROCESO:"
        )

        escribir(
            "  SOLO SIN_INFORMACION autoriza "
            "retroceder al día anterior."
        )

        escribir(
            "  Si SBS confirma la fecha pero "
            "la estructura X3 no coincide, "
            "se registra "
            "ESTRUCTURA_X3_NO_COMPATIBLE."
        )

        escribir(
            "  Si la estructura existe pero "
            "falla el parser geométrico, "
            "es ERROR_TECNICO/parser."
        )

        escribir()
        escribir(
            "NO se interpolarán datos."
        )

        escribir(
            "NO se homologarán nombres."
        )

        escribir(
            "NO se seleccionarán bancos."
        )

        escribir(
            "NO se ejecutarán los 122 meses."
        )

        navegador = crear_navegador()

        for fecha_control in FECHAS_CONTROL:

            resultado = procesar_fecha_control(
                navegador,
                fecha_control
            )

            resultados.append(
                resultado
            )

            # Guardar avance después de cada punto.
            guardar_csv(
                resultados
            )

            # =================================================
            # ERROR TÉCNICO:
            # DETENER PRUEBA
            # =================================================

            if (
                resultado[
                    "estado"
                ]
                ==
                "ERROR_TECNICO"
            ):

                error_pendiente = ErrorTecnicoX3(
                    "La prueba histórica se detuvo "
                    f"en {resultado['mes']} "
                    "por ERROR_TECNICO."
                )

                break

            # =================================================
            # ESTRUCTURA INCOMPATIBLE:
            #
            # No es error Selenium/parser, por lo que
            # puede continuarse con los demás PUNTOS
            # históricos para diagnosticar estabilidad.
            #
            # Lo que NO se hace es retroceder dentro
            # de ese mismo mes.
            # =================================================

            if (
                resultado[
                    "estado"
                ]
                ==
                "ESTRUCTURA_X3_NO_COMPATIBLE"
            ):

                escribir()
                escribir(
                    "[CONTROL] No se retrocedió "
                    "dentro de ese mes. "
                    "Se continuará únicamente "
                    "con el siguiente punto "
                    "histórico solicitado."
                )

            time.sleep(
                PAUSA_ENTRE_DIAS
            )

        guardar_csv(
            resultados
        )

        mostrar_resumen(
            resultados
        )

        if error_pendiente is not None:

            raise error_pendiente

    except Exception as error:

        escribir()
        escribir(
            "=" * 122
        )

        escribir(
            "PRUEBA DETENIDA POR ERROR"
        )

        escribir(
            "=" * 122
        )

        escribir(
            f"{type(error).__name__}: "
            f"{error}"
        )

        try:

            guardar_csv(
                resultados
            )

        except Exception:

            pass

        raise

    finally:

        CARPETA_SALIDA.mkdir(
            parents=True,
            exist_ok=True
        )

        ARCHIVO_TXT.write_text(
            "\n".join(
                lineas_reporte
            ),
            encoding="utf-8"
        )

        if navegador is not None:

            try:

                navegador.quit()

                print()
                print(
                    "[OK] Chrome cerrado."
                )

            except Exception:

                pass

        print()
        print("=" * 122)
        print("PRUEBA HISTÓRICA X3 FINALIZADA")
        print("=" * 122)

        print()
        print(
            "TXT:"
        )

        print(
            ARCHIVO_TXT
        )

        print()
        print(
            "CSV:"
        )

        print(
            ARCHIVO_CSV
        )

        print()
        print(
            "Evidencia HTML/PNG:"
        )

        print(
            CARPETA_EVIDENCIA
        )


# ============================================================
# 29. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()