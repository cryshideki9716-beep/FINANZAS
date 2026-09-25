# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico de confirmación de período SBS - Tasa activa - 30/06/2015

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
FECHA_OBJETIVO = "30/06/2015"

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
    / "diagnostico_confirmacion_periodo_tasa_activa_2015.txt"
)

SCREENSHOT_ANTES = (
    CARPETA_SALIDA
    / "tasa_activa_2015_antes.png"
)

SCREENSHOT_DESPUES = (
    CARPETA_SALIDA
    / "tasa_activa_2015_despues.png"
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

# Mensaje/fecha del resultado
ID_MENSAJE_FECHA = (
    "ctl00_cphContent_lblMensajeFecha"
)

# Grid MN
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

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
# 4. NORMALIZACIÓN DE TEXTO
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

    # Navegador visible.
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
# 7. CONFIRMAR PÁGINA SBS REAL
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
# 8. PERMITIR VERIFICACIÓN MANUAL
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
            "Si Chrome muestra una "
            "verificación de seguridad, "
            "complétala manualmente."
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

    # YYYY-MM-DD / Telerik
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
# 13. LEER CONTROL GENERICO
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
# 14. LEER lblMensajeFecha
# ============================================================

def leer_mensaje_fecha(
    navegador
):
    """
    Devuelve:
      existe
      texto visible
      textContent

    No falla si desaparece después del POST.
    """

    elementos = navegador.find_elements(
        By.ID,
        ID_MENSAJE_FECHA
    )

    if not elementos:

        return {
            "existe": False,
            "texto_visible": None,
            "text_content": None,
        }

    elemento = elementos[0]

    try:

        texto_visible = limpiar_texto(
            elemento.text
        )

    except Exception:

        texto_visible = None

    try:

        text_content = limpiar_texto(
            elemento.get_attribute(
                "textContent"
            )
        )

    except Exception:

        text_content = None

    return {
        "existe": True,
        "texto_visible": texto_visible,
        "text_content": text_content,
    }


# ============================================================
# 15. ESTADO DE FECHA DEL DATEPICKER
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
# 18. FALLBACK API TELERIK
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
            "exactamente a 30/06/2015."
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
# 21. BUSCAR TEXTOS "al DD/MM/YYYY"
# ============================================================

def buscar_subtitulos_fecha(
    navegador
):
    """
    Busca únicamente TEXTO visible del documento.

    Ejemplos:
      al 30/06/2015
      Tasas ... al 30/06/2015

    Los inputs del DatePicker NO forman parte
    de esta búsqueda.
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

            const elementos = Array.from(
                document.querySelectorAll(
                    selector
                )
            );

            const salida = [];
            const vistos = new Set();

            for (const el of elementos) {

                const style =
                    window.getComputedStyle(el);

                if (
                    style.display === 'none'
                    ||
                    style.visibility === 'hidden'
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

                if (texto.length > 350) {
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

                if (vistos.has(clave)) {
                    continue;
                }

                vistos.add(clave);

                salida.push({
                    tag: el.tagName,
                    id: el.id || '',
                    className:
                        typeof el.className === 'string'
                        ? el.className
                        : '',
                    text: texto
                });
            }

            return salida;
            """
        )

        return resultados or []

    except Exception:

        return []


# ============================================================
# 22. BUSCAR FECHA OBJETIVO EN TEXTO DE RESULTADO
# ============================================================

def confirmar_fecha_resultado(
    navegador
):
    """
    CRITERIO PRINCIPAL DEL DIAGNÓSTICO.

    30/06/2015 debe aparecer en una fuente
    de resultado:

      1. lblMensajeFecha
      o
      2. un encabezado/subtítulo visible
         del tipo "al DD/MM/YYYY".

    El DatePicker NO cuenta como prueba.
    """

    mensaje = leer_mensaje_fecha(
        navegador
    )

    subtitulos = buscar_subtitulos_fecha(
        navegador
    )

    fuentes_confirmatorias = []

    # --------------------------------------------------------
    # lblMensajeFecha
    # --------------------------------------------------------

    for clave in (
        "texto_visible",
        "text_content",
    ):

        valor = mensaje.get(
            clave
        )

        if (
            valor
            and
            FECHA_OBJETIVO in valor
        ):

            fuentes_confirmatorias.append({
                "fuente":
                    f"lblMensajeFecha.{clave}",

                "texto":
                    valor,
            })

    # --------------------------------------------------------
    # Subtítulos al DD/MM/YYYY
    # --------------------------------------------------------

    for item in subtitulos:

        texto = item.get(
            "text",
            ""
        )

        if FECHA_OBJETIVO in texto:

            fuentes_confirmatorias.append({
                "fuente":
                    (
                        f"{item.get('tag')} "
                        f"id={item.get('id')!r}"
                    ),

                "texto":
                    texto,
            })

    confirmado = (
        len(
            fuentes_confirmatorias
        )
        > 0
    )

    return {
        "confirmado":
            confirmado,

        "mensaje":
            mensaje,

        "subtitulos":
            subtitulos,

        "fuentes_confirmatorias":
            fuentes_confirmatorias,
    }


# ============================================================
# 23. HASH HTML
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
# 24. SCREENSHOT COMPLETO
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
# 25. ¿TEXTO PARECE NUMÉRICO?
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

    texto_numero = (
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
            texto_numero
        )

        return True

    except ValueError:

        return False


# ============================================================
# 26. FILA CANDIDATA DE ENCABEZADOS
# ============================================================

def obtener_candidatos_encabezados(
    tabla
):
    """
    NO extrae tasas.

    Busca la fila que tenga mayor cantidad
    de textos no numéricos.

    Se usa únicamente para saber qué
    encabezados/nombres bancarios aparentes
    están mostrando las tablas.
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

            # Evitar celdas contenedoras de
            # otras tablas anidadas.
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

        # Eliminar duplicados manteniendo orden.
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
# 27. ENCABEZADOS SEMÁNTICOS
# ============================================================

def obtener_encabezados_semanticos(
    tabla
):
    """
    Obtiene textos de <th> y elementos
    con apariencia explícita de header.

    No obtiene celdas numéricas de tasas.
    """

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

    # TD con clases/atributos de header
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
# 28. DIAGNÓSTICO DE GRID MN
# ============================================================

def diagnosticar_grid_mn(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    externa = soup.find(
        id=ID_TABLA_MN_EXTERNA
    )

    interna = soup.find(
        id=ID_TABLA_MN_INTERNA
    )

    existe_externa = (
        externa is not None
    )

    existe_interna = (
        interna is not None
    )

    encabezados_externa = (
        obtener_encabezados_semanticos(
            externa
        )
    )

    encabezados_interna = (
        obtener_encabezados_semanticos(
            interna
        )
    )

    fila_externa = (
        obtener_candidatos_encabezados(
            externa
        )
    )

    fila_interna = (
        obtener_candidatos_encabezados(
            interna
        )
    )

    return {
        "existe_externa":
            existe_externa,

        "existe_interna":
            existe_interna,

        "encabezados_semanticos_externa":
            encabezados_externa,

        "encabezados_semanticos_interna":
            encabezados_interna,

        "fila_candidata_externa":
            fila_externa,

        "fila_candidata_interna":
            fila_interna,
    }


# ============================================================
# 29. MOSTRAR GRID MN
# ============================================================

def mostrar_grid_mn(
    diagnostico,
    momento
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

    for texto in diagnostico[
        "fila_candidata_externa"
    ][
        "textos"
    ]:

        escribir(
            f"  {texto!r}"
        )

    escribir()
    escribir(
        "Encabezados semánticos "
        "DataZone:"
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

    for texto in diagnostico[
        "fila_candidata_interna"
    ][
        "textos"
    ]:

        escribir(
            f"  {texto!r}"
        )


# ============================================================
# 30. PRESENCIA DE CONSUMO EN MN
# ============================================================

def contar_consumo_en_mn(
    html
):
    """
    Solo diagnóstico.

    Consumo se busca en la tabla EXTERNA MN.
    No se extraen sus valores.
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

        # Evitar duplicación por celdas
        # contenedoras de tablas.
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
# 31. TEXTO VISIBLE RELEVANTE
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

    mensaje_fecha = leer_mensaje_fecha(
        navegador
    )

    subtitulos_fecha = (
        buscar_subtitulos_fecha(
            navegador
        )
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

        "mensaje_fecha":
            mensaje_fecha,

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
        "lblMensajeFecha"
    )

    mensaje = snapshot[
        "mensaje_fecha"
    ]

    escribir(
        f"Existe: "
        f"{mensaje['existe']}"
    )

    escribir(
        f"Texto visible: "
        f"{mensaje['texto_visible']!r}"
    )

    escribir(
        f"textContent: "
        f"{mensaje['text_content']!r}"
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
        "CONFIGURACIÓN MONEDA / ENTIDAD"
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
        "GRID MN / ENCABEZADOS BANCARIOS"
    )

    mostrar_grid_mn(
        snapshot[
            "grid"
        ],
        snapshot[
            "momento"
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
# 34. LOCALIZAR BOTÓN CONSULTAR
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
# 35. ESPERAR RESPUESTA SIN ASUMIR FECHA
# ============================================================

def pulsar_y_esperar_respuesta(
    navegador,
    sha_antes
):
    """
    Solo espera evidencia técnica de respuesta:

      - cambio de HTML,
      - navegación/postback,
      - cambio en lblMensajeFecha,
      - aparición/cambio de subtítulo de resultado.

    NINGUNA de estas evidencias, por sí sola,
    confirma que la fecha histórica sea 2015.
    """

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se encontró el botón Consultar."
        )

    mensaje_antes = leer_mensaje_fecha(
        navegador
    )

    subtitulos_antes = (
        buscar_subtitulos_fecha(
            navegador
        )
    )

    firmas_subtitulos_antes = {
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
        # HTML
        # ----------------------------------------------------

        try:

            _, sha_actual = (
                obtener_html_y_hash(
                    navegador
                )
            )

            if (
                sha_actual
                != sha_antes
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
        # Navegación
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
        # lblMensajeFecha
        # ----------------------------------------------------

        mensaje_actual = leer_mensaje_fecha(
            navegador
        )

        if (
            mensaje_actual
            != mensaje_antes
            and
            "MENSAJE_FECHA_CAMBIO"
            not in evidencias
        ):

            evidencias.append(
                "MENSAJE_FECHA_CAMBIO"
            )

        # ----------------------------------------------------
        # subtítulo de resultado
        # ----------------------------------------------------

        subtitulos_actuales = (
            buscar_subtitulos_fecha(
                navegador
            )
        )

        firmas_actuales = {
            (
                item.get("tag"),
                item.get("id"),
                item.get("text"),
            )
            for item
            in subtitulos_actuales
        }

        if (
            firmas_actuales
            != firmas_subtitulos_antes
            and
            "SUBTITULO_FECHA_CAMBIO"
            not in evidencias
        ):

            evidencias.append(
                "SUBTITULO_FECHA_CAMBIO"
            )

        # ----------------------------------------------------
        # Si hubo alguna evidencia técnica,
        # esperamos un pequeño margen y salimos.
        # ----------------------------------------------------

        if evidencias:

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

    candidatos_antes = set(
        normalizar_texto(
            texto
        )
        for texto
        in antes[
            "grid"
        ][
            "fila_candidata_interna"
        ][
            "textos"
        ]
        if limpiar_texto(
            texto
        )
    )

    candidatos_despues = set(
        normalizar_texto(
            texto
        )
        for texto
        in despues[
            "grid"
        ][
            "fila_candidata_interna"
        ][
            "textos"
        ]
        if limpiar_texto(
            texto
        )
    )

    iguales = (
        candidatos_antes
        == candidatos_despues
    )

    nuevos = sorted(
        candidatos_despues
        - candidatos_antes
    )

    desaparecidos = sorted(
        candidatos_antes
        - candidatos_despues
    )

    return {
        "iguales":
            iguales,

        "nuevos":
            nuevos,

        "desaparecidos":
            desaparecidos,
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
            "- SBS TASA ACTIVA - 30/06/2015"
        )

        escribir(
            "Objetivo:"
        )

        escribir(
            "Determinar si el POST realmente "
            "cambia el período del resultado."
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
        # CONFIGURAR 30/06/2015
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

        estado_final_pre = (
            obtener_estado_fecha(
                navegador,
                FECHA_OBJETIVO
            )
        )

        if not estado_final_pre[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "El DatePicker no quedó "
                "exactamente en 30/06/2015."
            )

        # Confirmar otra vez MN/B.
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
                "dentro del timeout."
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
        # COMPARACIÓN
        # ====================================================

        titulo(
            "COMPARACIÓN ANTES VS DESPUÉS"
        )

        escribir(
            f"SHA-256 ANTES:"
        )

        escribir(
            snapshot_antes[
                "sha256"
            ]
        )

        escribir()
        escribir(
            f"SHA-256 DESPUÉS:"
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

        escribir(
            f"Encabezados nuevos después:"
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

        escribir(
            f"Encabezados que desaparecieron:"
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
        # CRITERIO DECISIVO:
        # FECHA DEL RESULTADO
        # ====================================================

        titulo(
            "VALIDACIÓN DE LA FECHA REAL DEL RESULTADO"
        )

        confirmacion = (
            confirmar_fecha_resultado(
                navegador
            )
        )

        mensaje = confirmacion[
            "mensaje"
        ]

        escribir(
            f"lblMensajeFecha existe: "
            f"{mensaje['existe']}"
        )

        escribir(
            f"lblMensajeFecha texto visible: "
            f"{mensaje['texto_visible']!r}"
        )

        escribir(
            f"lblMensajeFecha textContent: "
            f"{mensaje['text_content']!r}"
        )

        escribir()
        escribir(
            'Textos de resultado "al DD/MM/YYYY":'
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
            "exactamente 30/06/2015:"
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
                "30/06/2015 en el texto "
                "del resultado."
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
                "El DatePicker puede haber quedado "
                "en 30/06/2015 y puede existir "
                "una tabla con Consumo, pero eso "
                "NO demuestra que la tabla "
                "corresponda al período solicitado."
            )

            escribir()
            escribir(
                "Por criterio metodológico, "
                "esta tabla NO debe considerarse "
                "histórica para junio de 2015."
            )

        # ====================================================
        # TEXTO VISIBLE RELEVANTE POST
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

        escribir(
            f"DatePicker visible antes: "
            f"{snapshot_antes['estado_fecha']['visible_texto']!r}"
        )

        escribir(
            f"DatePicker interno antes: "
            f"{snapshot_antes['estado_fecha']['interna_texto']!r}"
        )

        escribir(
            f"DatePicker visible después: "
            f"{snapshot_despues['estado_fecha']['visible_texto']!r}"
        )

        escribir(
            f"DatePicker interno después: "
            f"{snapshot_despues['estado_fecha']['interna_texto']!r}"
        )

        escribir(
            f"lblMensajeFecha después: "
            f"{snapshot_despues['mensaje_fecha']['text_content']!r}"
        )

        escribir(
            f"hdTipoMoneda antes: "
            f"{snapshot_antes['moneda']!r}"
        )

        escribir(
            f"hdTipoEntidad antes: "
            f"{snapshot_antes['entidad']!r}"
        )

        escribir(
            f"hdTipoMoneda después: "
            f"{snapshot_despues['moneda']!r}"
        )

        escribir(
            f"hdTipoEntidad después: "
            f"{snapshot_despues['entidad']!r}"
        )

        escribir(
            f"Consumo MN antes: "
            f"{snapshot_antes['consumo']['cantidad_consumo']}"
        )

        escribir(
            f"Consumo MN después: "
            f"{snapshot_despues['consumo']['cantidad_consumo']}"
        )

        escribir(
            f"HTML cambió: "
            f"{html_cambio}"
        )

        escribir(
            f"Headers DataZone iguales: "
            f"{comparacion_headers['iguales']}"
        )

        escribir()
        escribir(
            "IMPORTANTE:"
        )

        escribir(
            "La existencia de tabla MN o "
            "Consumo NO fue usada como prueba "
            "de que el período sea 2015."
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

        # Intentamos guardar el estado visible
        # aunque ocurra un error.
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