# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from datetime import date
import csv
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
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIPasivaDepositoEmpresa.aspx?tip=B"
)

# ÚNICA FECHA DE ESTA PRUEBA
FECHA_OBJETIVO = date(
    2015,
    11,
    30
)

FECHA_TEXTO = "30/11/2015"

TIMEOUT = 60
TIMEOUT_MANUAL = 180


# ============================================================
# 2. IDS REALES OBSERVADOS EN EL DIAGNÓSTICO X3
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

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "prueba_extraccion_x3_ahorro_mn_2015.txt"
)

ARCHIVO_CSV = (
    CARPETA_SALIDA
    / "prueba_extraccion_x3_ahorro_mn_2015.csv"
)

ARCHIVO_HTML = (
    CARPETA_SALIDA
    / "prueba_extraccion_x3_ahorro_mn_2015.html"
)

ARCHIVO_PNG = (
    CARPETA_SALIDA
    / "prueba_extraccion_x3_ahorro_mn_2015.png"
)


# ============================================================
# 4. SALIDA TXT
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
    escribir("=" * 120)
    escribir(texto)
    escribir("=" * 120)


def subtitulo(texto):

    escribir()
    escribir("-" * 120)
    escribir(texto)
    escribir("-" * 120)


# ============================================================
# 5. TEXTO
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


def normalizar_texto(valor):

    """
    Solo se utiliza para comparar etiquetas.

    NO modifica banco_original.
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
# 6. FECHAS
# ============================================================

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

    # YYYY-MM-DD
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
# 7. NAVEGADOR
# ============================================================

def crear_navegador():

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


def esperar_documento(
    navegador
):

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


# ============================================================
# 8. CONTROLES DINÁMICOS
# ============================================================

def obtener_controles(
    navegador
):

    return navegador.execute_script(
        r"""
        const elementos =
            Array.from(
                document.querySelectorAll(
                    'input,select,button'
                )
            );

        const salida = [];

        for (const el of elementos) {

            const style =
                window.getComputedStyle(el);

            const rect =
                el.getBoundingClientRect();

            salida.push({
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
                        rect.width > 0
                        &&
                        rect.height > 0
                    )
            });
        }

        return salida;
        """
    ) or []


def info_elemento(
    elemento
):

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
# 9. DATEPICKER VISIBLE
# ============================================================

def localizar_fecha_visible(
    navegador
):

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

            except (
                WebDriverException,
                StaleElementReferenceException
            ):

                continue

    return None


# ============================================================
# 10. DATEPICKER INTERNO
# ============================================================

def localizar_fecha_interna(
    navegador,
    fecha_visible
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

    # --------------------------------------------------------
    # Buscar hermano real derivado del ID observado.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Fallback dinámico.
    # --------------------------------------------------------

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

            if convertir_fecha(
                elemento.get_attribute(
                    "value"
                )
            ) == FECHA_OBJETIVO:

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
# 11. MONEDA / ENTIDAD
# ============================================================

def seleccionar_control_contexto(
    controles,
    tipo
):

    if tipo == "moneda":

        valor_esperado = "MN"

        palabras = [
            "moneda",
            "tipomoneda",
            "currency",
        ]

    elif tipo == "entidad":

        valor_esperado = "B"

        palabras = [
            "entidad",
            "tipoentidad",
            "entity",
        ]

    else:

        raise ValueError(
            f"Tipo inválido: {tipo}"
        )

    candidatos = []

    for control in controles:

        valor = limpiar_texto(
            control.get(
                "value",
                ""
            )
        ).upper()

        if valor != valor_esperado:

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

    empatados = [
        x
        for x in candidatos
        if x[
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
            empatados
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
# 12. VALIDAR ESTADO DEL FORMULARIO
# ============================================================

def validar_contexto(
    navegador,
    etapa
):

    subtitulo(
        f"VALIDACIÓN DE CONTEXTO - {etapa}"
    )

    visible = localizar_fecha_visible(
        navegador
    )

    if visible is None:

        raise RuntimeError(
            "DATEPICKER_VISIBLE_NO_LOCALIZADO"
        )

    info_visible = info_elemento(
        visible
    )

    fecha_visible = convertir_fecha(
        info_visible[
            "value"
        ]
    )

    escribir(
        f"Fecha visible ID = "
        f"{info_visible['id']!r}"
    )

    escribir(
        f"Fecha visible valor = "
        f"{info_visible['value']!r}"
    )

    if fecha_visible != FECHA_OBJETIVO:

        raise RuntimeError(
            f"{etapa}: fecha visible "
            "distinta de 30/11/2015."
        )

    interno = localizar_fecha_interna(
        navegador,
        visible
    )

    if interno is None:

        raise RuntimeError(
            "DATEPICKER_INTERNO_NO_LOCALIZADO"
        )

    info_interno = info_elemento(
        interno
    )

    fecha_interna = convertir_fecha(
        info_interno[
            "value"
        ]
    )

    escribir(
        f"Fecha interna ID = "
        f"{info_interno['id']!r}"
    )

    escribir(
        f"Fecha interna valor = "
        f"{info_interno['value']!r}"
    )

    if fecha_interna != FECHA_OBJETIVO:

        raise RuntimeError(
            f"{etapa}: fecha interna "
            "distinta de 30/11/2015."
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

        raise RuntimeError(
            "CONTROL_MONEDA_NO_UNIVOCO"
        )

    if entidad is None:

        raise RuntimeError(
            "CONTROL_ENTIDAD_NO_UNIVOCO"
        )

    escribir(
        f"Moneda ID = "
        f"{moneda.get('id')!r}"
    )

    escribir(
        f"Moneda name = "
        f"{moneda.get('name')!r}"
    )

    escribir(
        f"Moneda value = "
        f"{moneda.get('value')!r}"
    )

    escribir(
        f"Entidad ID = "
        f"{entidad.get('id')!r}"
    )

    escribir(
        f"Entidad name = "
        f"{entidad.get('name')!r}"
    )

    escribir(
        f"Entidad value = "
        f"{entidad.get('value')!r}"
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

        raise RuntimeError(
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

        raise RuntimeError(
            "ENTIDAD_NO_ES_B"
        )

    escribir(
        "[OK] fecha visible = 30/11/2015"
    )

    escribir(
        "[OK] fecha interna = 30/11/2015 equivalente"
    )

    escribir(
        "[OK] moneda = MN"
    )

    escribir(
        "[OK] entidad = B"
    )


# ============================================================
# 13. BOTÓN CONSULTAR
# ============================================================

def localizar_boton_consultar(
    navegador
):

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
# 14. PÁGINA REAL
# ============================================================

def pagina_real(
    navegador
):

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


def asegurar_pagina_real(
    navegador
):

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
            "Si Chrome muestra una "
            "verificación SBS, "
            "complétala manualmente."
        )

        escribir()

        input(
            "Cuando aparezca la página real, "
            "presiona ENTER aquí..."
        )

    WebDriverWait(
        navegador,
        TIMEOUT_MANUAL
    ).until(
        lambda d:
        pagina_real(
            d
        )
    )


# ============================================================
# 15. ESTABLECER FECHA
# ============================================================

def establecer_fecha(
    navegador
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise RuntimeError(
            "DATEPICKER_NO_LOCALIZADO"
        )

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
        FECHA_TEXTO
    )

    campo.send_keys(
        Keys.TAB
    )

    time.sleep(
        1
    )

    campo = localizar_fecha_visible(
        navegador
    )

    interno = localizar_fecha_interna(
        navegador,
        campo
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
        fecha_visible == FECHA_OBJETIVO
        and
        fecha_interna == FECHA_OBJETIVO
    ):

        return

    # ========================================================
    # FALLBACK TELERIK BASADO EN ID REAL
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

        raise RuntimeError(
            "NO_PUEDE_DERIVARSE_PICKER_TELERIK"
        )

    id_picker = id_visible[
        :-len(
            "_dateInput"
        )
    ]

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
                    2015,
                    10,
                    30
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
                        '30/11/2015'
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
        id_picker
    )

    escribir(
        f"Fallback Telerik = "
        f"{resultado!r}"
    )

    time.sleep(
        1
    )


# ============================================================
# 16. CONFIRMAR PERÍODO SBS
# ============================================================

def buscar_confirmacion_periodo(
    navegador
):

    return navegador.execute_script(
        r"""
        const patron =
            /\bal\s+30\/11\/2015\b/i;

        const salida = [];
        const vistos = new Set();

        const elementos =
            Array.from(
                document.querySelectorAll(
                    'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th,strong,b'
                )
            );

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
                .replace(/\s+/g, ' ')
                .trim();

            if (
                !texto
                ||
                texto.length > 800
                ||
                !patron.test(texto)
            ) {
                continue;
            }

            const clave = [
                el.tagName,
                el.id || '',
                texto
            ].join('|');

            if (
                vistos.has(
                    clave
                )
            ) {
                continue;
            }

            vistos.add(
                clave
            );

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
    ) or []


def buscar_sin_informacion(
    navegador
):

    texto = navegador.find_element(
        By.TAG_NAME,
        "body"
    ).text

    return (
        "no existe informacion "
        "para la fecha elegida"
        in
        normalizar_texto(
            texto
        )
    )


# ============================================================
# 17. CONSULTAR
# ============================================================

def consultar(
    navegador
):

    boton = localizar_boton_consultar(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "BOTON_CONSULTAR_NO_UNIVOCO"
        )

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
            navegador
        )

        # SIN_INFORMACION tiene prioridad.
        if sin_info:

            time.sleep(
                0.5
            )

            return {
                "respuesta":
                    "SIN_INFORMACION",

                "confirmaciones":
                    buscar_confirmacion_periodo(
                        navegador
                    ),
            }

        if confirmaciones:

            time.sleep(
                2
            )

            if buscar_sin_informacion(
                navegador
            ):

                return {
                    "respuesta":
                        "SIN_INFORMACION",

                    "confirmaciones":
                        buscar_confirmacion_periodo(
                            navegador
                        ),
                }

            confirmaciones = buscar_confirmacion_periodo(
                navegador
            )

            if confirmaciones:

                return {
                    "respuesta":
                        "PERIODO_CONFIRMADO",

                    "confirmaciones":
                        confirmaciones,
                }

        time.sleep(
            0.25
        )

    raise RuntimeError(
        "RESPUESTA_SBS_NO_CONFIRMADA"
    )


# ============================================================
# 18. EXTRACCIÓN GEOMÉTRICA X3
# ============================================================

def extraer_ahorro_mn(
    navegador
):
    """
    Utiliza EXCLUSIVAMENTE:

      ctl00_cphContent_rpgActualPrimTablaMn_OT

      ctl00_cphContent_
      rpgActualPrimTablaMn_ctl00_DataZone_DT

    No usa offsets fijos.

    Lógica:

      Depósitos de Ahorro
             ↓
      alineación horizontal
             ↓
      columna numérica

      cada fila numérica
             ←
      alineación vertical
             ←
      nombre de banco
    """

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

        return (
            overlap
            /
            base
        );
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

        return (
            overlap
            /
            base
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
    // B. TABLAS REALES OBSERVADAS
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
    // D. FILAS NUMÉRICAS DE DATAZONE
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

        /*
        Evita confundir una fila estructural
        totalmente vacía con una fila real.
        */

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
    // E. LOCALIZAR DINÁMICAMENTE LA COLUMNA AHORRO
    //
    // Para cada fila:
    //   etiqueta Depósitos de Ahorro
    //             ↓
    //   mejor celda por alineación horizontal
    //
    // No existe índice fijo.
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
                        fila.index
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
    // F. EXIGIR MISMA COLUMNA DINÁMICAMENTE EN TODAS LAS FILAS
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
    // G. CANDIDATOS DE NOMBRES EXTERNOS
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

        /*
        Nombres bancarios deben estar
        fuera de la DataZone numérica.
        */

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
            ||
            n.includes(
                'al 30/11/2015'
            )
        ) {
            continue;
        }

        /*
        Evitar duplicar un TD y un DIV hijo
        con exactamente el mismo texto.
        */

        if (
            !terminalConTexto(
                el,
                n
            )
        ) {
            continue;
        }

        /*
        No usar textos numéricos como nombres.
        */

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

        /*
        La zona de nombres debe estar
        fundamentalmente a la izquierda
        de la DataZone, según la relación
        estructural observada.
        */

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
    // H. MAPEAR CADA FILA NUMÉRICA CON SU NOMBRE
    //
    // Sin offset fijo.
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

            /*
            Mayor score:
              - más solapamiento vertical;
              - estar a la izquierda;
              - menor distancia vertical;
              - razonablemente cerca del grid.
            */

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
    // I. VALIDAR NOMBRES ÚNICOS
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
    // K. VALIDACIONES DE CANTIDADES
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

    except WebDriverException as error:

        raise RuntimeError(
            "ERROR_SELENIUM_EN_EXTRACCION_GEOMETRICA: "
            f"{error}"
        ) from error

    if not resultado.get(
        "ok",
        False
    ):

        raise RuntimeError(
            "EXTRACCION_GEOMETRICA_NO_VALIDADA: "
            f"{resultado}"
        )

    return resultado


# ============================================================
# 19. MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    resultado
):

    titulo(
        "VALIDACIÓN ESTRUCTURAL DE LA EXTRACCIÓN X3"
    )

    escribir(
        f"Tabla MN utilizada = "
        f"{resultado['outerId']}"
    )

    escribir(
        f"DataZone MN utilizada = "
        f"{resultado['dataZoneId']}"
    )

    escribir()
    escribir(
        f"Etiquetas exactas "
        f"'Depósitos de Ahorro' = "
        f"{resultado['ahorroLabelCount']}"
    )

    escribir(
        f"Texto etiqueta = "
        f"{resultado['ahorroLabelText']!r}"
    )

    escribir(
        f"Tabla inmediata de etiqueta = "
        f"{resultado['ahorroLabelTableId']!r}"
    )

    escribir()
    escribir(
        "Columna localizada dinámicamente:"
    )

    escribir(
        f"  índice interno detectado = "
        f"{resultado['ahorroColumnIndex']}"
    )

    escribir(
        "  IMPORTANTE: este índice fue "
        "inferido por geometría; "
        "no está fijado en el código."
    )

    escribir()
    escribir(
        f"Filas numéricas detectadas = "
        f"{resultado['numericRowCount']}"
    )

    escribir(
        f"Valores de Ahorro detectados = "
        f"{resultado['targetValueCount']}"
    )

    escribir(
        f"Filas mapeadas a nombres = "
        f"{resultado['mappedRowCount']}"
    )

    escribir(
        f"Bancos = "
        f"{resultado['bankCount']}"
    )

    escribir(
        f"Faltantes entre bancos = "
        f"{resultado['missingBankCount']}"
    )

    # ========================================================
    # TABLA BANCO → TASA
    # ========================================================

    titulo(
        "TASA PASIVA DEPÓSITOS DE AHORRO MN "
        "- 30/11/2015"
    )

    escribir(
        "banco_original | tasa_pasiva_ahorro_mn"
    )

    escribir(
        "-" * 100
    )

    for registro in resultado[
        "bancos"
    ]:

        banco = registro[
            "banco_original"
        ]

        valor = registro[
            "tasa"
        ]

        # Solo para visualizar un vacío en el TXT.
        # El valor bruto sigue siendo "".
        if valor == "":

            visible = "<VACIO>"

        else:

            visible = valor

        escribir(
            f"{banco} | {visible}"
        )

    # ========================================================
    # PROMEDIO
    # ========================================================

    subtitulo(
        "PROMEDIO - SEPARADO DE LOS BANCOS"
    )

    promedio = resultado[
        "promedio"
    ]

    promedio_valor = promedio[
        "tasa"
    ]

    if promedio_valor == "":

        promedio_visible = "<VACIO>"

    else:

        promedio_visible = promedio_valor

    escribir(
        f"Promedio | {promedio_visible}"
    )

    # ========================================================
    # FALTANTES
    # ========================================================

    subtitulo(
        "CONTROL DE FALTANTES"
    )

    faltantes = [
        fila
        for fila in resultado[
            "bancos"
        ]
        if fila[
            "faltante"
        ]
    ]

    escribir(
        f"Cantidad de faltantes = "
        f"{len(faltantes)}"
    )

    if faltantes:

        for fila in faltantes:

            valor = fila[
                "tasa"
            ]

            if valor == "":

                valor = "<VACIO>"

            escribir(
                f"  {fila['banco_original']} "
                f"→ {valor}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )

    # ========================================================
    # VALIDACIONES
    # ========================================================

    subtitulo(
        "VALIDACIONES DE CANTIDAD"
    )

    escribir(
        f"Nombres totales mapeados = "
        f"{resultado['mappedRowCount']}"
    )

    escribir(
        f"Valores totales encontrados = "
        f"{resultado['targetValueCount']}"
    )

    escribir(
        f"Bancos + Promedio = "
        f"{resultado['bankCount'] + 1}"
    )

    if (
        resultado[
            "mappedRowCount"
        ]
        !=
        resultado[
            "targetValueCount"
        ]
    ):

        raise RuntimeError(
            "NOMBRES_Y_VALORES_NO_COINCIDEN"
        )

    if (
        resultado[
            "bankCount"
        ]
        + 1
        !=
        resultado[
            "targetValueCount"
        ]
    ):

        raise RuntimeError(
            "BANCOS_MAS_PROMEDIO_NO_COINCIDEN"
        )

    escribir(
        "[OK] un nombre por cada valor."
    )

    escribir(
        "[OK] bancos + Promedio "
        "= total de valores."
    )


# ============================================================
# 20. GUARDAR CSV DE LA PRUEBA
# ============================================================

def guardar_csv_prueba(
    resultado
):

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    with ARCHIVO_CSV.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=[
                "fecha_sbs",
                "banco_original",
                "tasa_pasiva_ahorro_mn",
            ]
        )

        escritor.writeheader()

        for registro in resultado[
            "bancos"
        ]:

            escritor.writerow({
                "fecha_sbs":
                    FECHA_TEXTO,

                "banco_original":
                    registro[
                        "banco_original"
                    ],

                "tasa_pasiva_ahorro_mn":
                    registro[
                        "tasa"
                    ],
            })


# ============================================================
# 21. MAIN
# ============================================================

def main():

    navegador = None

    try:

        CARPETA_SALIDA.mkdir(
            parents=True,
            exist_ok=True
        )

        titulo(
            "PRUEBA DE EXTRACCIÓN X3 "
            "- DEPÓSITOS DE AHORRO MN"
        )

        escribir(
            "Fecha única consultada: "
            "30/11/2015"
        )

        escribir()
        escribir(
            "IDs provenientes del "
            "diagnóstico real:"
        )

        escribir(
            f"  Tabla MN = {ID_TABLA_MN}"
        )

        escribir(
            f"  DataZone MN = {ID_DATAZONE_MN}"
        )

        escribir()
        escribir(
            "NO se consultarán otros meses."
        )

        escribir(
            "NO se interpolarán faltantes."
        )

        escribir(
            "NO se homologarán nombres."
        )

        escribir(
            "NO se seleccionarán bancos."
        )

        # ====================================================
        # ABRIR SBS
        # ====================================================

        navegador = crear_navegador()

        navegador.get(
            URL
        )

        esperar_documento(
            navegador
        )

        time.sleep(
            2
        )

        asegurar_pagina_real(
            navegador
        )

        # ====================================================
        # ESTABLECER FECHA
        # ====================================================

        titulo(
            "ESTABLECER FECHA"
        )

        establecer_fecha(
            navegador
        )

        validar_contexto(
            navegador,
            "ANTES DE CONSULTAR"
        )

        # ====================================================
        # CONSULTAR
        # ====================================================

        titulo(
            "CONSULTA SBS"
        )

        respuesta = consultar(
            navegador
        )

        escribir(
            f"Respuesta = "
            f"{respuesta['respuesta']}"
        )

        if (
            respuesta[
                "respuesta"
            ]
            ==
            "SIN_INFORMACION"
        ):

            raise RuntimeError(
                "SIN_INFORMACION_30_11_2015"
            )

        if (
            respuesta[
                "respuesta"
            ]
            !=
            "PERIODO_CONFIRMADO"
        ):

            raise RuntimeError(
                "PERIODO_NO_CONFIRMADO"
            )

        escribir(
            "[OK] SBS confirmó explícitamente "
            "'al 30/11/2015'."
        )

        for confirmacion in respuesta[
            "confirmaciones"
        ]:

            escribir(
                f"  id="
                f"{confirmacion.get('id')!r} | "
                f"text="
                f"{confirmacion.get('text')!r}"
            )

        # ====================================================
        # VALIDACIÓN DESPUÉS DEL POST
        # ====================================================

        validar_contexto(
            navegador,
            "DESPUÉS DE CONSULTAR"
        )

        # ====================================================
        # VERIFICAR IDS REALES OBSERVADOS
        # ====================================================

        titulo(
            "VERIFICACIÓN DE LAS TABLAS X3"
        )

        tabla = navegador.find_elements(
            By.ID,
            ID_TABLA_MN
        )

        datazone = navegador.find_elements(
            By.ID,
            ID_DATAZONE_MN
        )

        escribir(
            f"Tabla contenedora encontrada = "
            f"{len(tabla)}"
        )

        escribir(
            f"DataZone encontrada = "
            f"{len(datazone)}"
        )

        if len(
            tabla
        ) != 1:

            raise RuntimeError(
                "TABLA_MN_NO_UNIVOCA"
            )

        if len(
            datazone
        ) != 1:

            raise RuntimeError(
                "DATAZONE_MN_NO_UNIVOCA"
            )

        escribir(
            "[OK] Se utilizará únicamente "
            "la estructura MN observada."
        )

        # ====================================================
        # EXTRACCIÓN
        # ====================================================

        titulo(
            "MAPEO GEOMÉTRICO "
            "DEPÓSITOS DE AHORRO"
        )

        resultado = extraer_ahorro_mn(
            navegador
        )

        mostrar_resultado(
            resultado
        )

        # ====================================================
        # GUARDAR EVIDENCIA
        # ====================================================

        guardar_csv_prueba(
            resultado
        )

        ARCHIVO_HTML.write_text(
            navegador.page_source,
            encoding="utf-8"
        )

        navegador.save_screenshot(
            str(
                ARCHIVO_PNG
            )
        )

        # ====================================================
        # CLASIFICACIÓN FINAL
        # ====================================================

        titulo(
            "CLASIFICACIÓN FINAL"
        )

        escribir(
            "ESTADO = "
            "EXTRACCION_X3_AHORRO_MN_2015_VALIDADA"
        )

        escribir()
        escribir(
            "Validaciones cumplidas:"
        )

        escribir(
            "1. fecha única 30/11/2015;"
        )

        escribir(
            "2. período SBS confirmado "
            "explícitamente;"
        )

        escribir(
            "3. moneda = MN;"
        )

        escribir(
            "4. entidad = B;"
        )

        escribir(
            "5. tabla MN real utilizada;"
        )

        escribir(
            "6. DataZone MN real utilizada;"
        )

        escribir(
            "7. exactamente una etiqueta "
            "'Depósitos de Ahorro';"
        )

        escribir(
            "8. columna localizada "
            "geométricamente sin offset fijo;"
        )

        escribir(
            "9. cada fila numérica fue "
            "mapeada a su nombre sin offset fijo;"
        )

        escribir(
            "10. número de nombres "
            "= número de valores;"
        )

        escribir(
            "11. Promedio quedó separado;"
        )

        escribir(
            "12. faltantes preservados;"
        )

        escribir(
            "13. nombres originales preservados;"
        )

        escribir(
            "14. no hubo interpolación;"
        )

        escribir(
            "15. no hubo selección "
            "de bancos."
        )

    except Exception as error:

        titulo(
            "ERROR DE LA PRUEBA X3"
        )

        escribir(
            f"Tipo = "
            f"{type(error).__name__}"
        )

        escribir(
            f"Detalle = "
            f"{repr(error)}"
        )

        escribir()
        escribir(
            "La prueba NO debe considerarse "
            "validada mientras este error exista."
        )

        escribir(
            "El error NO debe interpretarse "
            "automáticamente como ausencia "
            "de información SBS."
        )

        # Conservar la evidencia disponible.
        if navegador is not None:

            try:

                ARCHIVO_HTML.write_text(
                    navegador.page_source,
                    encoding="utf-8"
                )

            except Exception:

                pass

            try:

                navegador.save_screenshot(
                    str(
                        ARCHIVO_PNG
                    )
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
        print("=" * 120)
        print("PRUEBA X3 FINALIZADA")
        print("=" * 120)

        print()
        print(
            "TXT:"
        )

        print(
            ARCHIVO_TXT
        )

        print()
        print(
            "CSV de prueba:"
        )

        print(
            ARCHIVO_CSV
        )

        print()
        print(
            "HTML:"
        )

        print(
            ARCHIVO_HTML
        )

        print()
        print(
            "PNG:"
        )

        print(
            ARCHIVO_PNG
        )


# ============================================================
# 22. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()