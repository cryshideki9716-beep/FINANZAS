# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico de confirmación de período SBS - Tasa activa - 30/06/2020

from pathlib import Path
from datetime import datetime
import base64
import hashlib
import re
import time
import unicodedata

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# SOLO ESTA FECHA
FECHA_OBJETIVO = "30/06/2020"

TIMEOUT = 45
TIMEOUT_MANUAL = 180

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "diagnostico_confirmacion_periodo_tasa_activa_2020.txt"
)

SCREENSHOT_ANTES = (
    CARPETA_SALIDA
    / "tasa_activa_2020_antes.png"
)

SCREENSHOT_DESPUES = (
    CARPETA_SALIDA
    / "tasa_activa_2020_despues.png"
)


# ============================================================
# 2. CONTROLES SBS CONOCIDOS
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

# Grid MN completo
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# DataZone del grid MN
ID_TABLA_MN_INTERNA = (
    "ctl00_cphContent_rpgActualMn_ctl00_DataZone_DT"
)


# ============================================================
# 3. SALIDA
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
    escribir("=" * 118)
    escribir(texto)
    escribir("=" * 118)


def subtitulo(texto):

    escribir()
    escribir("-" * 118)
    escribir(texto)
    escribir("-" * 118)


# ============================================================
# 4. NORMALIZACIÓN
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


# ============================================================
# 5. CREAR CHROME
# ============================================================

def crear_navegador():

    opciones = webdriver.ChromeOptions()

    # Chrome visible.
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


# ============================================================
# 6. ESPERAR DOCUMENTO
# ============================================================

def esperar_documento(
    navegador,
    timeout=TIMEOUT
):

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


# ============================================================
# 7. PÁGINA SBS REAL
# ============================================================

def pagina_sbs_real(
    navegador
):

    try:

        texto = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text.lower()

    except Exception:

        return False

    return (
        "moneda nacional" in texto
        or
        "consumo" in texto
    )


# ============================================================
# 8. VERIFICACIÓN MANUAL
# ============================================================

def asegurar_pagina_real(
    navegador
):

    try:

        WebDriverWait(
            navegador,
            12
        ).until(
            lambda d:
            pagina_sbs_real(d)
        )

        escribir(
            "[OK] Página SBS real cargada."
        )

        return True

    except TimeoutException:

        escribir()
        escribir(
            "La aplicación SBS todavía "
            "no fue detectada."
        )

        escribir(
            "Si Chrome muestra una verificación "
            "de seguridad, complétala manualmente."
        )

        escribir(
            "No cierres Chrome."
        )

        escribir()

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
            pagina_sbs_real(d)
        )

        escribir(
            "[OK] Página SBS real detectada."
        )

        return True

    except TimeoutException:

        return False


# ============================================================
# 9. CONVERTIR TEXTO A FECHA
# ============================================================

def convertir_fecha(valor):

    if valor is None:
        return None

    valor = limpiar_texto(
        valor
    )

    if not valor:
        return None

    # DD/MM/YYYY
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})"
        r"(?!\d)",
        valor
    )

    if coincidencia:

        dia = int(
            coincidencia.group(1)
        )

        mes = int(
            coincidencia.group(2)
        )

        year = int(
            coincidencia.group(3)
        )

        try:

            return datetime(
                year,
                mes,
                dia
            ).date()

        except ValueError:

            return None

    # YYYY-MM-DD
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        valor
    )

    if coincidencia:

        year = int(
            coincidencia.group(1)
        )

        mes = int(
            coincidencia.group(2)
        )

        dia = int(
            coincidencia.group(3)
        )

        try:

            return datetime(
                year,
                mes,
                dia
            ).date()

        except ValueError:

            return None

    return None


# ============================================================
# 10. LOCALIZAR FECHA VISIBLE
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

    for metodo, valor in candidatos:

        elementos = navegador.find_elements(
            metodo,
            valor
        )

        if elementos:

            return elementos[0]

    return None


# ============================================================
# 11. LEER FECHA VISIBLE
# ============================================================

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

    except Exception:

        return None


# ============================================================
# 12. LEER FECHA INTERNA
# ============================================================

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

    for metodo, valor in candidatos:

        elementos = navegador.find_elements(
            metodo,
            valor
        )

        if elementos:

            try:

                return limpiar_texto(
                    elementos[
                        0
                    ].get_attribute(
                        "value"
                    )
                )

            except Exception:

                return None

    return None


# ============================================================
# 13. LEER CONTROL GENÉRICO
# ============================================================

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

    for metodo, valor in candidatos:

        elementos = navegador.find_elements(
            metodo,
            valor
        )

        if elementos:

            try:

                return limpiar_texto(
                    elementos[
                        0
                    ].get_attribute(
                        "value"
                    )
                )

            except Exception:

                return None

    return None


# ============================================================
# 14. LEER TODOS LOS lblMensajeFecha*
# ============================================================

def leer_mensajes_fecha(
    navegador
):
    """
    Detecta dinámicamente IDs como:

        ctl00_cphContent_lblMensajeFecha
        ctl00_cphContent_lblMensajeFecha2
        etc.

    Esto incorpora el hallazgo del diagnóstico 2015.
    """

    try:

        resultados = navegador.execute_script(
            """
            const elementos = Array.from(
                document.querySelectorAll(
                    '[id*="lblMensajeFecha"]'
                )
            );

            return elementos.map(el => ({
                tag:
                    el.tagName,

                id:
                    el.id || '',

                visibleText:
                    (el.innerText || '')
                    .replace(/\\s+/g, ' ')
                    .trim(),

                textContent:
                    (el.textContent || '')
                    .replace(/\\s+/g, ' ')
                    .trim(),

                display:
                    window.getComputedStyle(el).display,

                visibility:
                    window.getComputedStyle(el).visibility
            }));
            """
        )

        return resultados or []

    except Exception:

        return []


# ============================================================
# 15. ESTADO DEL DATEPICKER
# ============================================================

def obtener_estado_fecha(
    navegador,
    fecha_objetivo
):

    objetivo = convertir_fecha(
        fecha_objetivo
    )

    visible_texto = leer_fecha_visible(
        navegador
    )

    interna_texto = leer_fecha_interna(
        navegador
    )

    visible_fecha = convertir_fecha(
        visible_texto
    )

    interna_fecha = convertir_fecha(
        interna_texto
    )

    return {
        "objetivo":
            objetivo,

        "visible_texto":
            visible_texto,

        "interna_texto":
            interna_texto,

        "visible_fecha":
            visible_fecha,

        "interna_fecha":
            interna_fecha,

        "visible_ok":
            visible_fecha == objetivo,

        "interna_ok":
            interna_fecha == objetivo,

        "ambas_ok":
            (
                visible_fecha == objetivo
                and
                interna_fecha == objetivo
            ),
    }


# ============================================================
# 16. MOSTRAR ESTADO FECHA
# ============================================================

def mostrar_estado_fecha(
    estado
):

    escribir(
        f"Fecha objetivo: "
        f"{estado['objetivo']}"
    )

    escribir(
        f"Fecha visible texto: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"Fecha visible interpretada: "
        f"{estado['visible_fecha']}"
    )

    escribir(
        f"Fecha interna texto: "
        f"{estado['interna_texto']!r}"
    )

    escribir(
        f"Fecha interna interpretada: "
        f"{estado['interna_fecha']}"
    )

    escribir(
        f"Visible exacta: "
        f"{estado['visible_ok']}"
    )

    escribir(
        f"Interna exacta: "
        f"{estado['interna_ok']}"
    )


# ============================================================
# 17. CAMBIAR FECHA POR TECLADO
# ============================================================

def cambiar_fecha_teclado(
    navegador,
    fecha
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise RuntimeError(
            "No existe el control visible "
            "del DatePicker."
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
        fecha
    )

    campo.send_keys(
        Keys.TAB
    )

    time.sleep(
        1
    )


# ============================================================
# 18. FALLBACK TELERIK
# ============================================================

def cambiar_fecha_telerik(
    navegador,
    fecha
):

    objetivo = datetime.strptime(
        fecha,
        "%d/%m/%Y"
    )

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

            var dateInput = null;

            if (
                typeof picker.get_dateInput
                === 'function'
            ) {

                dateInput =
                    picker.get_dateInput();
            }

            if (
                dateInput
                &&
                typeof dateInput.set_value
                === 'function'
            ) {

                dateInput.set_value(
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
        objetivo.year,
        objetivo.month,
        objetivo.day,
        fecha,
    )

    time.sleep(
        1
    )

    return resultado


# ============================================================
# 19. ESTABLECER FECHA ESTRICTAMENTE
# ============================================================

def establecer_fecha(
    navegador,
    fecha
):

    subtitulo(
        "ESTABLECER FECHA"
    )

    cambiar_fecha_teclado(
        navegador,
        fecha
    )

    estado = obtener_estado_fecha(
        navegador,
        fecha
    )

    escribir(
        "Después del teclado:"
    )

    mostrar_estado_fecha(
        estado
    )

    if estado[
        "ambas_ok"
    ]:

        escribir()
        escribir(
            "[OK] Fecha visible e interna "
            "coinciden exactamente."
        )

        return estado

    escribir()
    escribir(
        "Visible e interna no coinciden ambas."
    )

    escribir(
        "Usando API RadDatePicker..."
    )

    resultado = cambiar_fecha_telerik(
        navegador,
        fecha
    )

    escribir(
        f"Resultado Telerik: "
        f"{resultado!r}"
    )

    estado = obtener_estado_fecha(
        navegador,
        fecha
    )

    escribir()
    escribir(
        "Después de Telerik:"
    )

    mostrar_estado_fecha(
        estado
    )

    if not estado[
        "ambas_ok"
    ]:

        raise RuntimeError(
            "FECHA_PRECONSULTA_INVALIDA: "
            "visible e interna no corresponden "
            "exactamente a 30/06/2020."
        )

    escribir()
    escribir(
        "[OK] Fecha validada estrictamente."
    )

    return estado


# ============================================================
# 20. VALIDAR MN Y B
# ============================================================

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

    escribir(
        f"hdTipoMoneda = {moneda!r}"
    )

    escribir(
        f"hdTipoEntidad = {entidad!r}"
    )

    if moneda != "MN":

        raise RuntimeError(
            "CONFIGURACION_MONEDA_INVALIDA: "
            f"se esperaba 'MN' y se obtuvo "
            f"{moneda!r}."
        )

    if entidad != "B":

        raise RuntimeError(
            "CONFIGURACION_ENTIDAD_INVALIDA: "
            f"se esperaba 'B' y se obtuvo "
            f"{entidad!r}."
        )


# ============================================================
# 21. BUSCAR SUBTÍTULOS "al DD/MM/YYYY"
# ============================================================

def buscar_subtitulos_fecha(
    navegador
):
    """
    Busca únicamente texto visible del resultado.

    El DatePicker NO forma parte de esta prueba.
    """

    try:

        resultados = navegador.execute_script(
            r"""
            const selector = [
                'span',
                'label',
                'div',
                'p',
                'h1',
                'h2',
                'h3',
                'h4',
                'h5',
                'h6',
                'td',
                'th',
                'strong',
                'b'
            ].join(',');

            const patron =
                /\bal\s+\d{1,2}\/\d{1,2}\/\d{4}\b/i;

            const elementos =
                Array.from(
                    document.querySelectorAll(
                        selector
                    )
                );

            const salida = [];
            const vistos = new Set();

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
                    rect.width === 0
                    &&
                    rect.height === 0
                ) {
                    continue;
                }

                const texto =
                    (el.innerText || '')
                    .replace(/\s+/g, ' ')
                    .trim();

                if (!texto) {
                    continue;
                }

                if (
                    texto.length > 400
                ) {
                    continue;
                }

                if (!patron.test(texto)) {
                    continue;
                }

                const clave = [
                    el.tagName,
                    el.id || '',
                    texto
                ].join('|');

                if (
                    vistos.has(clave)
                ) {
                    continue;
                }

                vistos.add(clave);

                salida.push({
                    tag:
                        el.tagName,

                    id:
                        el.id || '',

                    className:
                        typeof el.className === 'string'
                        ? el.className
                        : '',

                    text:
                        texto
                });
            }

            return salida;
            """
        )

        return resultados or []

    except Exception:

        return []


# ============================================================
# 22. CONFIRMAR FECHA REAL DEL RESULTADO
# ============================================================

def confirmar_fecha_resultado(
    navegador
):
    """
    Criterio decisivo:

    Debe aparecer explícitamente:

        al 30/06/2020

    en:

      - algún lblMensajeFecha*
      - o encabezado/subtítulo visible.

    El DatePicker NO confirma el período.
    """

    patron_objetivo = re.compile(
        r"\bal\s+30/06/2020\b",
        flags=re.IGNORECASE
    )

    mensajes = leer_mensajes_fecha(
        navegador
    )

    subtitulos = buscar_subtitulos_fecha(
        navegador
    )

    fuentes_confirmatorias = []

    # --------------------------------------------------------
    # lblMensajeFecha*
    # --------------------------------------------------------

    for mensaje in mensajes:

        textos = [
            mensaje.get(
                "visibleText",
                ""
            ),
            mensaje.get(
                "textContent",
                ""
            ),
        ]

        for texto in textos:

            texto = limpiar_texto(
                texto
            )

            if (
                texto
                and
                patron_objetivo.search(
                    texto
                )
            ):

                fuentes_confirmatorias.append({
                    "fuente":
                        mensaje.get(
                            "id",
                            ""
                        ),

                    "texto":
                        texto,
                })

    # --------------------------------------------------------
    # Encabezados visibles
    # --------------------------------------------------------

    for item in subtitulos:

        texto = limpiar_texto(
            item.get(
                "text",
                ""
            )
        )

        if patron_objetivo.search(
            texto
        ):

            fuentes_confirmatorias.append({
                "fuente":
                    (
                        f"{item.get('tag')} "
                        f"id={item.get('id')!r}"
                    ),

                "texto":
                    texto,
            })

    # Eliminar duplicados
    unicos = []

    vistos = set()

    for item in fuentes_confirmatorias:

        clave = (
            item[
                "fuente"
            ],
            item[
                "texto"
            ],
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        unicos.append(
            item
        )

    return {
        "confirmado":
            len(unicos) > 0,

        "mensajes":
            mensajes,

        "subtitulos":
            subtitulos,

        "fuentes_confirmatorias":
            unicos,
    }


# ============================================================
# 23. HTML + SHA256
# ============================================================

def obtener_html_y_hash(
    navegador
):

    html = navegador.page_source

    sha256 = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    return html, sha256


# ============================================================
# 24. SCREENSHOT
# ============================================================

def guardar_screenshot_completo(
    navegador,
    ruta
):

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        resultado = navegador.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format":
                    "png",

                "captureBeyondViewport":
                    True,

                "fromSurface":
                    True,
            }
        )

        datos = base64.b64decode(
            resultado[
                "data"
            ]
        )

        ruta.write_bytes(
            datos
        )

        return (
            True,
            "CDP_FULL_PAGE"
        )

    except Exception as error:

        try:

            navegador.save_screenshot(
                str(
                    ruta
                )
            )

            return (
                True,
                "SELENIUM_VIEWPORT_FALLBACK"
            )

        except Exception as error2:

            return (
                False,
                (
                    f"CDP={error!r}; "
                    f"fallback={error2!r}"
                )
            )


# ============================================================
# 25. ¿PARECE NÚMERO?
# ============================================================

def parece_numerico(
    valor
):

    texto = limpiar_texto(
        valor
    )

    if not texto:
        return False

    if normalizar_texto(
        texto
    ) in {
        "-",
        "s.i.",
        "s.i",
        "nd",
        "n.d.",
        "n/a",
    }:

        return True

    numero = (
        texto
        .replace(
            "%",
            ""
        )
        .replace(
            ",",
            "."
        )
        .strip()
    )

    try:

        float(
            numero
        )

        return True

    except ValueError:

        return False


# ============================================================
# 26. ENCABEZADOS SEMÁNTICOS
# ============================================================

def obtener_encabezados_semanticos(
    tabla
):

    if tabla is None:
        return []

    candidatos = []

    # TH reales
    for elemento in tabla.find_all(
        "th"
    ):

        texto = limpiar_texto(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if (
            texto
            and
            not parece_numerico(
                texto
            )
        ):

            candidatos.append(
                texto
            )

    # TD que tengan apariencia de encabezado
    for elemento in tabla.find_all(
        "td"
    ):

        clases = " ".join(
            elemento.get(
                "class",
                []
            )
        )

        identificador = str(
            elemento.get(
                "id",
                ""
            )
        )

        scope = str(
            elemento.get(
                "scope",
                ""
            )
        )

        cadena = (
            clases
            + " "
            + identificador
            + " "
            + scope
        ).lower()

        if not re.search(
            r"(header|column|rgheader|rpgheader)",
            cadena
        ):

            continue

        texto = limpiar_texto(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if (
            texto
            and
            not parece_numerico(
                texto
            )
        ):

            candidatos.append(
                texto
            )

    unicos = []
    vistos = set()

    for texto in candidatos:

        clave = normalizar_texto(
            texto
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        unicos.append(
            texto
        )

    return unicos


# ============================================================
# 27. FILA CANDIDATA DE ENCABEZADOS
# ============================================================

def obtener_candidatos_encabezados(
    tabla
):
    """
    Busca la fila con más textos no numéricos.

    Se usa solo para diagnóstico de nombres
    visibles de bancos/encabezados.

    NO se extraen tasas.
    """

    if tabla is None:

        return {
            "fila":
                None,

            "textos":
                [],

            "cantidad":
                0,
        }

    mejor = {
        "fila":
            None,

        "textos":
            [],

        "cantidad":
            0,
    }

    filas = tabla.find_all(
        "tr"
    )

    for numero_fila, fila in enumerate(
        filas
    ):

        celdas = fila.find_all(
            ["th", "td"],
            recursive=False
        )

        if not celdas:

            continue

        textos = []

        for celda in celdas:

            # Evitar celdas que solo contienen
            # otra tabla interna.
            if celda.find(
                "table"
            ) is not None:

                continue

            texto = limpiar_texto(
                celda.get_text(
                    " ",
                    strip=True
                )
            )

            if not texto:
                continue

            if parece_numerico(
                texto
            ):
                continue

            textos.append(
                texto
            )

        unicos = []
        vistos = set()

        for texto in textos:

            clave = normalizar_texto(
                texto
            )

            if clave in vistos:
                continue

            vistos.add(
                clave
            )

            unicos.append(
                texto
            )

        if len(
            unicos
        ) > mejor[
            "cantidad"
        ]:

            mejor = {
                "fila":
                    numero_fila,

                "textos":
                    unicos,

                "cantidad":
                    len(
                        unicos
                    ),
            }

    return mejor


# ============================================================
# 28. DIAGNÓSTICO DEL GRID MN
# ============================================================

def diagnosticar_grid_mn(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tabla_externa = soup.find(
        id=ID_TABLA_MN_EXTERNA
    )

    tabla_interna = soup.find(
        id=ID_TABLA_MN_INTERNA
    )

    return {
        "existe_externa":
            tabla_externa
            is not None,

        "existe_interna":
            tabla_interna
            is not None,

        "encabezados_semanticos_externa":
            obtener_encabezados_semanticos(
                tabla_externa
            ),

        "encabezados_semanticos_interna":
            obtener_encabezados_semanticos(
                tabla_interna
            ),

        "fila_candidata_externa":
            obtener_candidatos_encabezados(
                tabla_externa
            ),

        "fila_candidata_interna":
            obtener_candidatos_encabezados(
                tabla_interna
            ),
    }


# ============================================================
# 29. MOSTRAR GRID MN
# ============================================================

def mostrar_grid_mn(
    diagnostico
):

    escribir(
        f"Tabla MN externa existe: "
        f"{diagnostico['existe_externa']}"
    )

    escribir(
        f"Tabla MN interna/DataZone existe: "
        f"{diagnostico['existe_interna']}"
    )

    escribir()
    escribir(
        "Encabezados semánticos "
        "tabla externa:"
    )

    if diagnostico[
        "encabezados_semanticos_externa"
    ]:

        for texto in diagnostico[
            "encabezados_semanticos_externa"
        ]:

            escribir(
                f"  {texto!r}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )

    escribir()
    escribir(
        "Fila candidata de encabezados "
        "tabla externa:"
    )

    escribir(
        f"  Fila: "
        f"{diagnostico['fila_candidata_externa']['fila']}"
    )

    if diagnostico[
        "fila_candidata_externa"
    ][
        "textos"
    ]:

        for texto in diagnostico[
            "fila_candidata_externa"
        ][
            "textos"
        ]:

            escribir(
                f"  {texto!r}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )

    escribir()
    escribir(
        "Encabezados semánticos DataZone:"
    )

    if diagnostico[
        "encabezados_semanticos_interna"
    ]:

        for texto in diagnostico[
            "encabezados_semanticos_interna"
        ]:

            escribir(
                f"  {texto!r}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )

    escribir()
    escribir(
        "Fila candidata de encabezados "
        "DataZone:"
    )

    escribir(
        f"  Fila: "
        f"{diagnostico['fila_candidata_interna']['fila']}"
    )

    if diagnostico[
        "fila_candidata_interna"
    ][
        "textos"
    ]:

        for texto in diagnostico[
            "fila_candidata_interna"
        ][
            "textos"
        ]:

            escribir(
                f"  {texto!r}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )


# ============================================================
# 30. CONSUMO DENTRO DE TABLA MN EXTERNA
# ============================================================

def contar_consumo_en_mn(
    html
):
    """
    Solo cuenta Consumo en la tabla MN externa.

    NO extrae tasas.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tabla = soup.find(
        id=ID_TABLA_MN_EXTERNA
    )

    if tabla is None:

        return {
            "tabla_existe":
                False,

            "cantidad_consumo":
                0,
        }

    coincidencias = 0

    for celda in tabla.find_all(
        ["th", "td"]
    ):

        # Evitar duplicados producidos por
        # tablas anidadas.
        if celda.find(
            "table"
        ) is not None:

            continue

        texto = normalizar_texto(
            celda.get_text(
                " ",
                strip=True
            )
        )

        if texto == "consumo":

            coincidencias += 1

    return {
        "tabla_existe":
            True,

        "cantidad_consumo":
            coincidencias,
    }


# ============================================================
# 31. TEXTO VISIBLE
# ============================================================

def obtener_texto_visible(
    navegador
):

    try:

        return navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except Exception:

        return ""


# ============================================================
# 32. SNAPSHOT COMPLETO
# ============================================================

def tomar_snapshot(
    navegador,
    nombre_momento,
    screenshot_ruta
):

    html, sha256 = obtener_html_y_hash(
        navegador
    )

    estado_fecha = obtener_estado_fecha(
        navegador,
        FECHA_OBJETIVO
    )

    mensajes_fecha = leer_mensajes_fecha(
        navegador
    )

    subtitulos_fecha = buscar_subtitulos_fecha(
        navegador
    )

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

    grid = diagnosticar_grid_mn(
        html
    )

    consumo = contar_consumo_en_mn(
        html
    )

    texto_visible = obtener_texto_visible(
        navegador
    )

    screenshot_ok, screenshot_metodo = (
        guardar_screenshot_completo(
            navegador,
            screenshot_ruta
        )
    )

    return {
        "momento":
            nombre_momento,

        "url":
            navegador.current_url,

        "titulo":
            navegador.title,

        "html":
            html,

        "sha256":
            sha256,

        "estado_fecha":
            estado_fecha,

        "mensajes_fecha":
            mensajes_fecha,

        "subtitulos_fecha":
            subtitulos_fecha,

        "moneda":
            moneda,

        "entidad":
            entidad,

        "grid":
            grid,

        "consumo":
            consumo,

        "texto_visible":
            texto_visible,

        "screenshot_ok":
            screenshot_ok,

        "screenshot_metodo":
            screenshot_metodo,

        "screenshot_ruta":
            screenshot_ruta,
    }


# ============================================================
# 33. MOSTRAR SNAPSHOT
# ============================================================

def mostrar_snapshot(
    snapshot
):

    titulo(
        f"SNAPSHOT {snapshot['momento']}"
    )

    escribir(
        f"URL: "
        f"{snapshot['url']}"
    )

    escribir(
        f"Título: "
        f"{snapshot['titulo']!r}"
    )

    escribir(
        f"SHA-256 HTML: "
        f"{snapshot['sha256']}"
    )

    subtitulo(
        "DATEPICKER"
    )

    mostrar_estado_fecha(
        snapshot[
            "estado_fecha"
        ]
    )

    subtitulo(
        "ELEMENTOS lblMensajeFecha*"
    )

    if snapshot[
        "mensajes_fecha"
    ]:

        for item in snapshot[
            "mensajes_fecha"
        ]:

            escribir(
                f"id={item.get('id')!r} | "
                f"visibleText={item.get('visibleText')!r} | "
                f"textContent={item.get('textContent')!r} | "
                f"display={item.get('display')!r} | "
                f"visibility={item.get('visibility')!r}"
            )

    else:

        escribir(
            "<NINGUNO>"
        )

    subtitulo(
        'ENCABEZADOS/SUBTÍTULOS "al DD/MM/YYYY"'
    )

    if snapshot[
        "subtitulos_fecha"
    ]:

        for item in snapshot[
            "subtitulos_fecha"
        ]:

            escribir(
                f"tag={item.get('tag')!r} | "
                f"id={item.get('id')!r} | "
                f"class={item.get('className')!r} | "
                f"text={item.get('text')!r}"
            )

    else:

        escribir(
            "<NINGUNO>"
        )

    subtitulo(
        "CONFIGURACIÓN MN / B"
    )

    escribir(
        f"hdTipoMoneda: "
        f"{snapshot['moneda']!r}"
    )

    escribir(
        f"hdTipoEntidad: "
        f"{snapshot['entidad']!r}"
    )

    subtitulo(
        "GRID MN / ENCABEZADOS"
    )

    mostrar_grid_mn(
        snapshot[
            "grid"
        ]
    )

    subtitulo(
        "CONSUMO DENTRO DE TABLA MN EXTERNA"
    )

    escribir(
        f"Tabla externa existe: "
        f"{snapshot['consumo']['tabla_existe']}"
    )

    escribir(
        f"Celdas exactas 'Consumo': "
        f"{snapshot['consumo']['cantidad_consumo']}"
    )

    subtitulo(
        "SCREENSHOT"
    )

    escribir(
        f"Guardado: "
        f"{snapshot['screenshot_ok']}"
    )

    escribir(
        f"Método: "
        f"{snapshot['screenshot_metodo']}"
    )

    escribir(
        f"Ruta: "
        f"{snapshot['screenshot_ruta']}"
    )


# ============================================================
# 34. BOTÓN CONSULTAR
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

    for metodo, valor in candidatos:

        elementos = navegador.find_elements(
            metodo,
            valor
        )

        if elementos:

            return elementos[0]

    return None


# ============================================================
# 35. ESPERAR RESPUESTA TÉCNICA
# ============================================================

def pulsar_y_esperar_respuesta(
    navegador,
    sha_antes
):
    """
    Espera alguna señal técnica del POST.

    IMPORTANTE:
    ninguna señal técnica confirma por sí
    sola que la tabla sea de junio de 2020.

    La fecha real se validará aparte mediante
    "al 30/06/2020".
    """

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se encontró el botón Consultar."
        )

    mensajes_antes = leer_mensajes_fecha(
        navegador
    )

    subtitulos_antes = buscar_subtitulos_fecha(
        navegador
    )

    firma_mensajes_antes = {
        (
            item.get("id"),
            item.get("visibleText"),
            item.get("textContent"),
        )
        for item in mensajes_antes
    }

    firma_subtitulos_antes = {
        (
            item.get("tag"),
            item.get("id"),
            item.get("text"),
        )
        for item in subtitulos_antes
    }

    try:

        time_origin_antes = (
            navegador.execute_script(
                """
                return (
                    performance
                    &&
                    performance.timeOrigin
                )
                ? performance.timeOrigin
                : null;
                """
            )
        )

    except Exception:

        time_origin_antes = None

    navegador.execute_script(
        """
        arguments[0].scrollIntoView({
            block: 'center'
        });
        """,
        boton
    )

    time.sleep(
        0.5
    )

    boton.click()

    inicio = time.time()

    evidencias = []

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        # ----------------------------------------------------
        # HTML cambió
        # ----------------------------------------------------

        try:

            _, sha_actual = obtener_html_y_hash(
                navegador
            )

            if (
                sha_actual != sha_antes
                and
                "HTML_CAMBIO"
                not in evidencias
            ):

                evidencias.append(
                    "HTML_CAMBIO"
                )

        except Exception:

            pass

        # ----------------------------------------------------
        # Navegación / postback
        # ----------------------------------------------------

        try:

            time_origin_actual = (
                navegador.execute_script(
                    """
                    return (
                        performance
                        &&
                        performance.timeOrigin
                    )
                    ? performance.timeOrigin
                    : null;
                    """
                )
            )

            if (
                time_origin_antes
                is not None
                and
                time_origin_actual
                is not None
                and
                time_origin_actual
                != time_origin_antes
                and
                "NAVEGACION_POSTBACK"
                not in evidencias
            ):

                evidencias.append(
                    "NAVEGACION_POSTBACK"
                )

        except Exception:

            pass

        # ----------------------------------------------------
        # Cambiaron lblMensajeFecha*
        # ----------------------------------------------------

        mensajes_actuales = leer_mensajes_fecha(
            navegador
        )

        firma_mensajes_actuales = {
            (
                item.get("id"),
                item.get("visibleText"),
                item.get("textContent"),
            )
            for item in mensajes_actuales
        }

        if (
            firma_mensajes_actuales
            != firma_mensajes_antes
            and
            "MENSAJE_FECHA_CAMBIO"
            not in evidencias
        ):

            evidencias.append(
                "MENSAJE_FECHA_CAMBIO"
            )

        # ----------------------------------------------------
        # Cambió subtítulo "al DD/MM/YYYY"
        # ----------------------------------------------------

        subtitulos_actuales = (
            buscar_subtitulos_fecha(
                navegador
            )
        )

        firma_subtitulos_actuales = {
            (
                item.get("tag"),
                item.get("id"),
                item.get("text"),
            )
            for item
            in subtitulos_actuales
        }

        if (
            firma_subtitulos_actuales
            != firma_subtitulos_antes
            and
            "SUBTITULO_FECHA_CAMBIO"
            not in evidencias
        ):

            evidencias.append(
                "SUBTITULO_FECHA_CAMBIO"
            )

        if evidencias:

            # Dejar estabilizar la respuesta.
            time.sleep(
                3
            )

            try:

                esperar_documento(
                    navegador,
                    timeout=10
                )

            except Exception:

                pass

            return evidencias

        time.sleep(
            0.25
        )

    return evidencias


# ============================================================
# 36. COMPARAR ENCABEZADOS PRE / POST
# ============================================================

def comparar_encabezados(
    antes,
    despues
):

    # Priorizamos DataZone.
    textos_antes = (
        antes[
            "grid"
        ][
            "fila_candidata_interna"
        ][
            "textos"
        ]
    )

    textos_despues = (
        despues[
            "grid"
        ][
            "fila_candidata_interna"
        ][
            "textos"
        ]
    )

    claves_antes = {
        normalizar_texto(
            texto
        )
        for texto in textos_antes
        if limpiar_texto(
            texto
        )
    }

    claves_despues = {
        normalizar_texto(
            texto
        )
        for texto in textos_despues
        if limpiar_texto(
            texto
        )
    }

    return {
        "iguales":
            claves_antes
            == claves_despues,

        "nuevos":
            sorted(
                claves_despues
                - claves_antes
            ),

        "desaparecidos":
            sorted(
                claves_antes
                - claves_despues
            ),
    }


# ============================================================
# 37. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    snapshot_antes = None
    snapshot_despues = None

    try:

        titulo(
            "DIAGNÓSTICO DE CONFIRMACIÓN DE PERÍODO "
            "- SBS TASA ACTIVA - 30/06/2020"
        )

        escribir(
            "Objetivo:"
        )

        escribir(
            "Determinar inequívocamente si "
            "el POST cambia el resultado "
            "al período 30/06/2020."
        )

        escribir()
        escribir(
            "NO se extraerán tasas."
        )

        escribir(
            "NO se consultarán otros meses."
        )

        escribir(
            "NO se descargarán 211 meses."
        )

        escribir(
            "NO se seleccionarán bancos."
        )

        escribir(
            "NO se interpolarán datos."
        )

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

        if not asegurar_pagina_real(
            navegador
        ):

            raise RuntimeError(
                "No se pudo cargar "
                "la aplicación SBS real."
            )

        # ====================================================
        # CONFIGURACIÓN PRE
        # ====================================================

        titulo(
            "CONFIGURACIÓN PRE-CONSULTA"
        )

        validar_mn_b(
            navegador
        )

        establecer_fecha(
            navegador,
            FECHA_OBJETIVO
        )

        estado_pre = obtener_estado_fecha(
            navegador,
            FECHA_OBJETIVO
        )

        if not estado_pre[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "El DatePicker no quedó "
                "exactamente en 30/06/2020."
            )

        # Confirmar MN/B justo antes del POST.
        validar_mn_b(
            navegador
        )

        escribir()
        escribir(
            "[OK] Pre-consulta validada."
        )

        # ====================================================
        # SNAPSHOT ANTES
        # ====================================================

        snapshot_antes = tomar_snapshot(
            navegador,
            "ANTES DEL POST",
            SCREENSHOT_ANTES
        )

        mostrar_snapshot(
            snapshot_antes
        )

        # ====================================================
        # POST
        # ====================================================

        titulo(
            "PULSAR CONSULTAR"
        )

        evidencias = (
            pulsar_y_esperar_respuesta(
                navegador,
                snapshot_antes[
                    "sha256"
                ]
            )
        )

        escribir(
            f"Evidencias técnicas de respuesta: "
            f"{evidencias}"
        )

        if not evidencias:

            escribir(
                "[ADVERTENCIA] No se detectó "
                "una señal técnica clara "
                "antes del timeout."
            )

            escribir(
                "El diagnóstico continuará "
                "con el estado actual."
            )

        # ====================================================
        # SNAPSHOT DESPUÉS
        # ====================================================

        snapshot_despues = tomar_snapshot(
            navegador,
            "DESPUÉS DEL POST",
            SCREENSHOT_DESPUES
        )

        mostrar_snapshot(
            snapshot_despues
        )

        # ====================================================
        # COMPARACIÓN SHA / HEADERS
        # ====================================================

        titulo(
            "COMPARACIÓN ANTES VS DESPUÉS"
        )

        escribir(
            "SHA-256 ANTES:"
        )

        escribir(
            snapshot_antes[
                "sha256"
            ]
        )

        escribir()
        escribir(
            "SHA-256 DESPUÉS:"
        )

        escribir(
            snapshot_despues[
                "sha256"
            ]
        )

        html_cambio = (
            snapshot_antes[
                "sha256"
            ]
            !=
            snapshot_despues[
                "sha256"
            ]
        )

        escribir()
        escribir(
            f"¿Cambió el HTML?: "
            f"{html_cambio}"
        )

        comparacion_headers = (
            comparar_encabezados(
                snapshot_antes,
                snapshot_despues
            )
        )

        escribir()
        escribir(
            f"¿Encabezados candidatos "
            f"DataZone iguales?: "
            f"{comparacion_headers['iguales']}"
        )

        escribir()
        escribir(
            "Encabezados nuevos después:"
        )

        if comparacion_headers[
            "nuevos"
        ]:

            for texto in comparacion_headers[
                "nuevos"
            ]:

                escribir(
                    f"  {texto!r}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        escribir()
        escribir(
            "Encabezados que desaparecieron:"
        )

        if comparacion_headers[
            "desaparecidos"
        ]:

            for texto in comparacion_headers[
                "desaparecidos"
            ]:

                escribir(
                    f"  {texto!r}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        # ====================================================
        # VALIDACIÓN REAL DEL PERÍODO
        # ====================================================

        titulo(
            "VALIDACIÓN DE LA FECHA REAL DEL RESULTADO"
        )

        confirmacion = (
            confirmar_fecha_resultado(
                navegador
            )
        )

        escribir(
            "Elementos lblMensajeFecha* "
            "después del POST:"
        )

        if confirmacion[
            "mensajes"
        ]:

            for item in confirmacion[
                "mensajes"
            ]:

                escribir(
                    f"  id={item.get('id')!r} | "
                    f"visibleText="
                    f"{item.get('visibleText')!r} | "
                    f"textContent="
                    f"{item.get('textContent')!r}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        escribir()
        escribir(
            'Textos visibles "al DD/MM/YYYY":'
        )

        if confirmacion[
            "subtitulos"
        ]:

            for item in confirmacion[
                "subtitulos"
            ]:

                escribir(
                    f"  tag={item.get('tag')!r} | "
                    f"id={item.get('id')!r} | "
                    f"text={item.get('text')!r}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        escribir()
        escribir(
            "Fuentes que confirman "
            "exactamente 'al 30/06/2020':"
        )

        if confirmacion[
            "fuentes_confirmatorias"
        ]:

            for item in confirmacion[
                "fuentes_confirmatorias"
            ]:

                escribir(
                    f"  {item['fuente']} | "
                    f"{item['texto']!r}"
                )

        else:

            escribir(
                "  <NINGUNA>"
            )

        # ====================================================
        # CLASIFICACIÓN FINAL
        # ====================================================

        titulo(
            "CLASIFICACIÓN FINAL"
        )

        if confirmacion[
            "confirmado"
        ]:

            estado_final = (
                "FECHA_RESULTADO_CONFIRMADA"
            )

            escribir(
                "ESTADO = "
                "FECHA_RESULTADO_CONFIRMADA"
            )

            escribir()
            escribir(
                "SBS muestra explícitamente "
                "'al 30/06/2020' en el "
                "texto del resultado."
            )

        else:

            estado_final = (
                "FECHA_RESULTADO_NO_CONFIRMADA"
            )

            escribir(
                "ESTADO = "
                "FECHA_RESULTADO_NO_CONFIRMADA"
            )

            escribir()
            escribir(
                "Aunque el DatePicker haya quedado "
                "en 30/06/2020 y aunque exista "
                "una tabla o Consumo, eso NO "
                "demuestra que el resultado "
                "corresponda al período solicitado."
            )

        # ====================================================
        # ESTADO ESTRUCTURAL POST
        # ====================================================

        subtitulo(
            "ESTADO ESTRUCTURAL POST"
        )

        escribir(
            f"Tabla MN externa post: "
            f"{snapshot_despues['grid']['existe_externa']}"
        )

        escribir(
            f"DataZone MN post: "
            f"{snapshot_despues['grid']['existe_interna']}"
        )

        escribir(
            f"Consumo MN post: "
            f"{snapshot_despues['consumo']['cantidad_consumo']}"
        )

        escribir(
            f"hdTipoMoneda post: "
            f"{snapshot_despues['moneda']!r}"
        )

        escribir(
            f"hdTipoEntidad post: "
            f"{snapshot_despues['entidad']!r}"
        )

        # ====================================================
        # TEXTO VISIBLE POST
        # ====================================================

        subtitulo(
            "TEXTO VISIBLE POST - PRIMEROS 5000 CARACTERES"
        )

        escribir(
            snapshot_despues[
                "texto_visible"
            ][:5000]
        )

        # ====================================================
        # RESUMEN
        # ====================================================

        titulo(
            "RESUMEN DEL DIAGNÓSTICO"
        )

        escribir(
            f"Fecha objetivo: "
            f"{FECHA_OBJETIVO}"
        )

        escribir(
            f"Estado final: "
            f"{estado_final}"
        )

        escribir()
        escribir(
            "DATEPICKER:"
        )

        escribir(
            f"  Visible antes: "
            f"{snapshot_antes['estado_fecha']['visible_texto']!r}"
        )

        escribir(
            f"  Interno antes: "
            f"{snapshot_antes['estado_fecha']['interna_texto']!r}"
        )

        escribir(
            f"  Visible después: "
            f"{snapshot_despues['estado_fecha']['visible_texto']!r}"
        )

        escribir(
            f"  Interno después: "
            f"{snapshot_despues['estado_fecha']['interna_texto']!r}"
        )

        escribir()
        escribir(
            "CONFIGURACIÓN:"
        )

        escribir(
            f"  MN antes: "
            f"{snapshot_antes['moneda']!r}"
        )

        escribir(
            f"  B antes: "
            f"{snapshot_antes['entidad']!r}"
        )

        escribir(
            f"  MN después: "
            f"{snapshot_despues['moneda']!r}"
        )

        escribir(
            f"  B después: "
            f"{snapshot_despues['entidad']!r}"
        )

        escribir()
        escribir(
            "GRID MN:"
        )

        escribir(
            f"  Externa antes: "
            f"{snapshot_antes['grid']['existe_externa']}"
        )

        escribir(
            f"  Externa después: "
            f"{snapshot_despues['grid']['existe_externa']}"
        )

        escribir(
            f"  DataZone antes: "
            f"{snapshot_antes['grid']['existe_interna']}"
        )

        escribir(
            f"  DataZone después: "
            f"{snapshot_despues['grid']['existe_interna']}"
        )

        escribir()
        escribir(
            "CONSUMO:"
        )

        escribir(
            f"  Antes: "
            f"{snapshot_antes['consumo']['cantidad_consumo']}"
        )

        escribir(
            f"  Después: "
            f"{snapshot_despues['consumo']['cantidad_consumo']}"
        )

        escribir()
        escribir(
            "HTML:"
        )

        escribir(
            f"  SHA antes: "
            f"{snapshot_antes['sha256']}"
        )

        escribir(
            f"  SHA después: "
            f"{snapshot_despues['sha256']}"
        )

        escribir(
            f"  Cambió: "
            f"{html_cambio}"
        )

        escribir()
        escribir(
            "HEADERS:"
        )

        escribir(
            f"  DataZone iguales antes/después: "
            f"{comparacion_headers['iguales']}"
        )

        escribir()
        escribir(
            "CONFIRMACIÓN DEL PERÍODO:"
        )

        escribir(
            f"  Fuentes confirmatorias: "
            f"{len(confirmacion['fuentes_confirmatorias'])}"
        )

        for item in confirmacion[
            "fuentes_confirmatorias"
        ]:

            escribir(
                f"  {item['fuente']} | "
                f"{item['texto']!r}"
            )

        escribir()
        escribir(
            "IMPORTANTE:"
        )

        escribir(
            "La existencia de una tabla MN, "
            "DataZone o Consumo NO fue usada "
            "como prueba de que el resultado "
            "corresponda a junio de 2020."
        )

    except Exception as error:

        titulo(
            "ERROR DEL DIAGNÓSTICO"
        )

        escribir(
            f"Tipo: "
            f"{type(error).__name__}"
        )

        escribir(
            f"Detalle: "
            f"{repr(error)}"
        )

        if navegador is not None:

            try:

                guardar_screenshot_completo(
                    navegador,
                    SCREENSHOT_DESPUES
                )

            except Exception:

                pass

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

            except Exception:

                pass

        print()
        print("=" * 118)
        print("DIAGNÓSTICO FINALIZADO")
        print("=" * 118)

        print()
        print("TXT:")
        print(ARCHIVO_TXT)

        print()
        print("SCREENSHOT ANTES:")
        print(SCREENSHOT_ANTES)

        print()
        print("SCREENSHOT DESPUÉS:")
        print(SCREENSHOT_DESPUES)


# ============================================================
# 38. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()