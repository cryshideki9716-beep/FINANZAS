# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Prueba histórica controlada SBS - Tasa activa de Consumo MN por empresa bancaria

from pathlib import Path
from datetime import datetime
import hashlib
import re
import time
import unicodedata

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# ÚNICAMENTE estas dos fechas.
FECHAS_CONTROL = [
    "30/06/2008",
    "31/12/2025",
]

TIMEOUT = 60
TIMEOUT_MANUAL = 180

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "diagnostico_consulta_tasa_activa_2008_2025.txt"
)


# ============================================================
# 2. CONTROLES SBS IDENTIFICADOS
# ============================================================

# Fecha visible
NAME_FECHA_VISIBLE = (
    "ctl00$cphContent$rdpDate$dateInput"
)

ID_FECHA_VISIBLE = (
    "ctl00_cphContent_rdpDate_dateInput"
)

# Fecha interna del RadDatePicker
NAME_FECHA_INTERNA = (
    "ctl00$cphContent$rdpDate"
)

ID_FECHA_INTERNA = (
    "ctl00_cphContent_rdpDate"
)

# Botón consultar
NAME_BOTON = (
    "ctl00$cphContent$btnConsultar"
)

ID_BOTON = (
    "ctl00_cphContent_btnConsultar"
)

# Tabla Moneda Nacional
ID_TABLA_MN = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# RadDatePicker
ID_PICKER_TELERIK = (
    "ctl00_cphContent_rdpDate"
)

# Hidden de moneda
NAME_MONEDA = (
    "ctl00$cphContent$hdTipoMoneda"
)

ID_MONEDA = (
    "ctl00_cphContent_hdTipoMoneda"
)

# Hidden de entidad
NAME_ENTIDAD = (
    "ctl00$cphContent$hdTipoEntidad"
)

ID_ENTIDAD = (
    "ctl00_cphContent_hdTipoEntidad"
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
        "\n",
        " "
    )

    texto = texto.replace(
        "\r",
        " "
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def normalizar_comparacion(valor):

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
# 5. CONFIGURAR CHROME
# ============================================================

def crear_navegador():

    opciones = webdriver.ChromeOptions()

    # Navegador visible.
    # NO usamos headless.
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

def pagina_real_cargada(
    navegador
):

    try:

        cuerpo = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text.lower()

        existe_tabla = bool(
            navegador.find_elements(
                By.ID,
                ID_TABLA_MN
            )
        )

        return (
            existe_tabla
            and
            "consumo" in cuerpo
        )

    except Exception:

        return False


# ============================================================
# 8. VERIFICACIÓN MANUAL INICIAL
# ============================================================

def asegurar_pagina_real(
    navegador
):

    escribir()
    escribir(
        "Esperando que cargue "
        "la aplicación SBS..."
    )

    try:

        WebDriverWait(
            navegador,
            15
        ).until(
            lambda d:
            pagina_real_cargada(d)
        )

        escribir(
            "[OK] La aplicación SBS cargó "
            "sin intervención manual."
        )

        return True

    except TimeoutException:

        escribir()
        escribir(
            "La aplicación real todavía "
            "no fue detectada."
        )

        escribir(
            "Si Chrome muestra una "
            "verificación de seguridad, "
            "complétala MANUALMENTE."
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
            pagina_real_cargada(d)
        )

        escribir(
            "[OK] Página SBS real detectada "
            "después de la intervención manual."
        )

        return True

    except TimeoutException:

        escribir(
            "[ERROR] No se pudo confirmar "
            "la página SBS real."
        )

        return False


# ============================================================
# 9. CONVERTIR TEXTO A FECHA
# ============================================================

def convertir_fecha(
    valor
):
    """
    Intenta reconocer, entre otros:

        30/06/2008
        30/06/2008 00:00:00
        2008-06-30
        2008-06-30-00-00-00
        2008/06/30

    Retorna datetime.date o None.
    """

    if valor is None:

        return None

    valor = limpiar_texto(
        valor
    )

    if not valor:

        return None

    # --------------------------------------------------------
    # DD/MM/YYYY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # YYYY/MM/DD
    # --------------------------------------------------------

    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})/"
        r"(\d{1,2})/"
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

    raise NoSuchElementException(
        "No se encontró el "
        "input visible de fecha."
    )


# ============================================================
# 11. LEER FECHA VISIBLE
# ============================================================

def leer_fecha_visible(
    navegador
):

    elemento = localizar_fecha_visible(
        navegador
    )

    return limpiar_texto(
        elemento.get_attribute(
            "value"
        )
    )


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

            return limpiar_texto(
                elementos[
                    0
                ].get_attribute(
                    "value"
                )
            )

    return ""


# ============================================================
# 13. LEER CONTROL SIMPLE
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

            return limpiar_texto(
                elementos[
                    0
                ].get_attribute(
                    "value"
                )
            )

    return None


# ============================================================
# 14. VALIDAR MN Y BANCA
# ============================================================

def validar_configuracion(
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
            "La consulta no está configurada "
            "en Moneda Nacional."
        )

    if entidad != "B":

        raise RuntimeError(
            "La consulta no está configurada "
            "para entidades bancarias (B)."
        )


# ============================================================
# 15. ESCRIBIR FECHA MEDIANTE TECLADO
# ============================================================

def cambiar_fecha_teclado(
    navegador,
    fecha
):

    campo = localizar_fecha_visible(
        navegador
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

    # Salir del control para permitir
    # que Telerik procese el valor.
    campo.send_keys(
        Keys.TAB
    )

    time.sleep(
        1
    )


# ============================================================
# 16. FALLBACK MEDIANTE API TELERIK
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

            var nuevaFecha = new Date(
                arguments[1],
                arguments[2] - 1,
                arguments[3]
            );

            if (
                typeof picker.set_selectedDate
                !== 'function'
            ) {
                return 'NO_set_selectedDate';
            }

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
# 17. VALIDAR FECHA CONTRA OBJETIVO
# ============================================================

def estado_fecha(
    navegador,
    fecha_objetivo
):

    objetivo = convertir_fecha(
        fecha_objetivo
    )

    visible_texto = (
        leer_fecha_visible(
            navegador
        )
    )

    interna_texto = (
        leer_fecha_interna(
            navegador
        )
    )

    visible_fecha = convertir_fecha(
        visible_texto
    )

    interna_fecha = convertir_fecha(
        interna_texto
    )

    coincide_visible = (
        visible_fecha
        == objetivo
    )

    coincide_interna = (
        interna_fecha
        == objetivo
    )

    return {
        "objetivo": objetivo,

        "visible_texto":
            visible_texto,

        "interna_texto":
            interna_texto,

        "visible_fecha":
            visible_fecha,

        "interna_fecha":
            interna_fecha,

        "coincide_visible":
            coincide_visible,

        "coincide_interna":
            coincide_interna,

        "ambas_exactas":
            (
                coincide_visible
                and
                coincide_interna
            ),
    }


# ============================================================
# 18. MOSTRAR ESTADO FECHA
# ============================================================

def mostrar_estado_fecha(
    estado,
    prefijo=""
):

    escribir(
        f"{prefijo}Fecha visible texto: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"{prefijo}Fecha visible interpretada: "
        f"{estado['visible_fecha']}"
    )

    escribir(
        f"{prefijo}Fecha interna texto: "
        f"{estado['interna_texto']!r}"
    )

    escribir(
        f"{prefijo}Fecha interna interpretada: "
        f"{estado['interna_fecha']}"
    )

    escribir(
        f"{prefijo}Visible = objetivo: "
        f"{estado['coincide_visible']}"
    )

    escribir(
        f"{prefijo}Interna = objetivo: "
        f"{estado['coincide_interna']}"
    )


# ============================================================
# 19. ESTABLECER Y VALIDAR FECHA
# ============================================================

def establecer_fecha(
    navegador,
    fecha
):
    """
    REGLA ESTRICTA:

    Antes de pulsar Consultar deben cumplirse
    simultáneamente:

        fecha visible == objetivo
        fecha interna == objetivo

    Si teclado no lo logra, usa Telerik.
    Si Telerik tampoco lo logra, se aborta
    esa fecha SIN pulsar Consultar.
    """

    escribir(
        f"Fecha objetivo: {fecha}"
    )

    # --------------------------------------------------------
    # Intento 1: teclado
    # --------------------------------------------------------

    cambiar_fecha_teclado(
        navegador,
        fecha
    )

    estado = estado_fecha(
        navegador,
        fecha
    )

    escribir()
    escribir(
        "Validación después del teclado:"
    )

    mostrar_estado_fecha(
        estado,
        prefijo="  "
    )

    if estado[
        "ambas_exactas"
    ]:

        escribir(
            "[OK] Fecha visible e interna "
            "coinciden exactamente con "
            "la fecha objetivo."
        )

        return estado

    # --------------------------------------------------------
    # Intento 2: API Telerik
    # --------------------------------------------------------

    escribir()
    escribir(
        "La fecha visible y/o interna "
        "no coincide exactamente."
    )

    escribir(
        "Se utilizará la API del "
        "RadDatePicker."
    )

    resultado_telerik = (
        cambiar_fecha_telerik(
            navegador,
            fecha
        )
    )

    escribir(
        f"Resultado Telerik: "
        f"{resultado_telerik!r}"
    )

    estado = estado_fecha(
        navegador,
        fecha
    )

    escribir()
    escribir(
        "Validación después de Telerik:"
    )

    mostrar_estado_fecha(
        estado,
        prefijo="  "
    )

    if not estado[
        "ambas_exactas"
    ]:

        raise RuntimeError(
            "FECHA_PRECONSULTA_INVALIDA: "
            "la fecha visible y la fecha "
            "interna no corresponden ambas "
            "exactamente a la fecha objetivo. "
            "NO se pulsará Consultar."
        )

    escribir(
        "[OK] Después del fallback Telerik, "
        "fecha visible e interna coinciden "
        "exactamente con el objetivo."
    )

    return estado


# ============================================================
# 20. LOCALIZAR BOTÓN CONSULTAR
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

    raise NoSuchElementException(
        "No se encontró "
        "el botón Consultar."
    )


# ============================================================
# 21. LOCALIZAR TABLA MN
# ============================================================

def localizar_tabla_mn(
    navegador
):

    return navegador.find_element(
        By.ID,
        ID_TABLA_MN
    )


# ============================================================
# 22. EXTRAER FECHAS VISIBLES DE RESULTADO
# ============================================================

def fechas_resultado_visibles(
    html
):
    """
    Busca fechas mostradas como TEXTO en labels,
    spans, td, th, etc.

    No inspecciona inputs, por lo que la fecha
    escrita en el RadDatePicker no cuenta como
    "fecha de resultado".
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    etiquetas = [
        "span",
        "label",
        "div",
        "td",
        "th",
        "p",
        "strong",
        "b",
    ]

    resultados = []

    vistos = set()

    for elemento in soup.find_all(
        etiquetas
    ):

        texto = limpiar_texto(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not texto:
            continue

        # Evitar contenedores enormes.
        if len(texto) > 180:
            continue

        fecha = convertir_fecha(
            texto
        )

        if fecha is None:
            continue

        identificador = (
            elemento.get("id")
            or
            elemento.get("name")
            or
            ""
        )

        clases = " ".join(
            elemento.get(
                "class",
                []
            )
        )

        fuente = (
            f"{elemento.name}|"
            f"id={identificador}|"
            f"class={clases}|"
            f"text={texto}"
        )

        clave = (
            fecha.isoformat(),
            fuente
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        resultados.append({
            "fecha": fecha,
            "fecha_iso":
                fecha.isoformat(),
            "fuente": fuente,
            "texto": texto,
        })

    return resultados


# ============================================================
# 23. TIMEORIGIN DEL DOCUMENTO
# ============================================================

def obtener_time_origin(
    navegador
):

    try:

        return navegador.execute_script(
            """
            return (
                window.performance
                &&
                window.performance.timeOrigin
            )
            ? window.performance.timeOrigin
            : null;
            """
        )

    except Exception:

        return None


# ============================================================
# 24. TOMAR SNAPSHOT ANTES DEL POSTBACK
# ============================================================

def snapshot_preconsulta(
    navegador
):

    tabla = localizar_tabla_mn(
        navegador
    )

    html_tabla = (
        tabla.get_attribute(
            "outerHTML"
        )
        or ""
    )

    html_pagina = (
        navegador.page_source
    )

    return {
        "tabla_elemento":
            tabla,

        "tabla_html":
            html_tabla,

        "tabla_hash":
            hashlib.sha256(
                html_tabla.encode(
                    "utf-8",
                    errors="replace"
                )
            ).hexdigest(),

        "pagina_hash":
            hashlib.sha256(
                html_pagina.encode(
                    "utf-8",
                    errors="replace"
                )
            ).hexdigest(),

        "time_origin":
            obtener_time_origin(
                navegador
            ),

        "fechas_resultado":
            fechas_resultado_visibles(
                html_pagina
            ),
    }


# ============================================================
# 25. ESPERAR TABLA ESTABLE
# ============================================================

def esperar_tabla_estable(
    navegador,
    segundos_estable=1.0,
    timeout=15
):

    inicio = time.time()

    ultimo_html = None
    desde = None

    while (
        time.time()
        - inicio
        < timeout
    ):

        try:

            tabla = localizar_tabla_mn(
                navegador
            )

            html = (
                tabla.get_attribute(
                    "outerHTML"
                )
                or ""
            )

        except (
            NoSuchElementException,
            StaleElementReferenceException
        ):

            ultimo_html = None
            desde = None

            time.sleep(
                0.2
            )

            continue

        if html == ultimo_html:

            if desde is None:

                desde = time.time()

            if (
                time.time()
                - desde
                >= segundos_estable
            ):

                return True

        else:

            ultimo_html = html
            desde = time.time()

        time.sleep(
            0.2
        )

    return False


# ============================================================
# 26. PULSAR CONSULTAR CON EVIDENCIA REAL
# ============================================================

def pulsar_consultar(
    navegador,
    fecha_objetivo
):
    """
    NO considera terminada la consulta
    simplemente porque la tabla siga
    conteniendo 'Consumo'.

    Requiere evidencia real de actualización:

      A) la tabla MN cambió realmente; o
      B) el navegador realizó una navegación/postback
         de documento; o
      C) apareció una fecha de resultado nueva
         correspondiente al objetivo.

    La presencia previa de Consumo NO cuenta.
    """

    objetivo = convertir_fecha(
        fecha_objetivo
    )

    snapshot = snapshot_preconsulta(
        navegador
    )

    fechas_antes = {
        item["fecha"]
        for item
        in snapshot[
            "fechas_resultado"
        ]
    }

    escribir()
    escribir(
        "Snapshot antes de Consultar:"
    )

    escribir(
        f"  Hash tabla: "
        f"{snapshot['tabla_hash']}"
    )

    escribir(
        f"  timeOrigin: "
        f"{snapshot['time_origin']}"
    )

    escribir(
        "  Fechas visibles de resultado "
        "antes:"
    )

    if snapshot[
        "fechas_resultado"
    ]:

        for item in snapshot[
            "fechas_resultado"
        ]:

            escribir(
                f"    {item['fecha']} | "
                f"{item['texto']!r}"
            )

    else:

        escribir(
            "    <NINGUNA>"
        )

    boton = localizar_boton(
        navegador
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
        0.5
    )

    boton.click()

    inicio = time.time()

    evidencia = None
    detalle = None

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        tabla_cambio = False
        navegacion_cambio = False
        fecha_resultado_nueva = False

        # ----------------------------------------------------
        # A. ¿Cambió realmente la tabla?
        # ----------------------------------------------------

        try:

            tabla_actual = localizar_tabla_mn(
                navegador
            )

            html_actual = (
                tabla_actual.get_attribute(
                    "outerHTML"
                )
                or ""
            )

            tabla_cambio = (
                html_actual
                != snapshot[
                    "tabla_html"
                ]
            )

        except (
            NoSuchElementException,
            StaleElementReferenceException
        ):

            # Durante un postback la tabla puede
            # desaparecer temporalmente.
            pass

        # ----------------------------------------------------
        # B. ¿Hubo navegación/postback de documento?
        # ----------------------------------------------------

        time_origin_actual = (
            obtener_time_origin(
                navegador
            )
        )

        if (
            snapshot[
                "time_origin"
            ] is not None
            and
            time_origin_actual is not None
        ):

            navegacion_cambio = (
                time_origin_actual
                != snapshot[
                    "time_origin"
                ]
            )

        # ----------------------------------------------------
        # C. ¿Apareció una fecha de resultado nueva?
        # ----------------------------------------------------

        try:

            fechas_despues_tmp = (
                fechas_resultado_visibles(
                    navegador.page_source
                )
            )

        except Exception:

            fechas_despues_tmp = []

        fechas_despues_set = {
            item["fecha"]
            for item
            in fechas_despues_tmp
        }

        if (
            objetivo is not None
            and
            objetivo in fechas_despues_set
            and
            objetivo not in fechas_antes
        ):

            fecha_resultado_nueva = True

        # ----------------------------------------------------
        # Evidencia válida
        # ----------------------------------------------------

        if tabla_cambio:

            evidencia = (
                "TABLA_MN_CAMBIO"
            )

            detalle = (
                "El outerHTML de la tabla MN "
                "es diferente al anterior."
            )

            break

        if navegacion_cambio:

            evidencia = (
                "NAVEGACION_POSTBACK"
            )

            detalle = (
                "Cambió performance.timeOrigin; "
                "se cargó un nuevo documento."
            )

            break

        if fecha_resultado_nueva:

            evidencia = (
                "FECHA_RESULTADO_NUEVA"
            )

            detalle = (
                "Apareció como texto de resultado "
                "la fecha objetivo."
            )

            break

        time.sleep(
            0.25
        )

    if evidencia is None:

        raise TimeoutException(
            "No se detectó evidencia real "
            "de respuesta a la nueva fecha. "
            "La mera presencia de 'Consumo' "
            "NO fue aceptada como evidencia."
        )

    escribir()
    escribir(
        "[OK] Evidencia de actualización:"
    )

    escribir(
        f"  Tipo: {evidencia}"
    )

    escribir(
        f"  Detalle: {detalle}"
    )

    # --------------------------------------------------------
    # Esperar documento / nueva tabla.
    # --------------------------------------------------------

    try:

        esperar_documento(
            navegador,
            timeout=TIMEOUT
        )

    except TimeoutException:

        # En AJAX puede no ser relevante,
        # por eso no abortamos aquí.
        pass

    WebDriverWait(
        navegador,
        TIMEOUT
    ).until(
        lambda d:
        len(
            d.find_elements(
                By.ID,
                ID_TABLA_MN
            )
        )
        == 1
    )

    estable = esperar_tabla_estable(
        navegador
    )

    escribir(
        f"Tabla estable después de respuesta: "
        f"{estable}"
    )

    if not estable:

        raise TimeoutException(
            "La tabla MN no alcanzó "
            "un estado estable después "
            "de la actualización."
        )

    # --------------------------------------------------------
    # Información final de evidencia
    # --------------------------------------------------------

    html_final = navegador.page_source

    fechas_finales = (
        fechas_resultado_visibles(
            html_final
        )
    )

    escribir(
        "Fechas visibles de resultado después:"
    )

    if fechas_finales:

        for item in fechas_finales:

            escribir(
                f"  {item['fecha']} | "
                f"{item['texto']!r}"
            )

    else:

        escribir(
            "  <NINGUNA>"
        )

    return {
        "evidencia":
            evidencia,

        "detalle":
            detalle,

        "fechas_resultado":
            fechas_finales,
    }


# ============================================================
# 27. VALIDAR FECHA DESPUÉS DE CONSULTAR
# ============================================================

def validar_fecha_postconsulta(
    navegador,
    fecha_solicitada
):
    """
    Después del POST:

    - visible e interna deben poder interpretarse;
    - ambas deben coincidir entre sí;
    - pueden coincidir o no con la solicitada.

    Si ambas coinciden entre sí pero no con la
    solicitada, interpretamos que SBS ajustó
    automáticamente la fecha disponible.
    """

    solicitada = convertir_fecha(
        fecha_solicitada
    )

    visible_texto = (
        leer_fecha_visible(
            navegador
        )
    )

    interna_texto = (
        leer_fecha_interna(
            navegador
        )
    )

    visible = convertir_fecha(
        visible_texto
    )

    interna = convertir_fecha(
        interna_texto
    )

    escribir()
    escribir(
        "Validación de fecha "
        "después de Consultar:"
    )

    escribir(
        f"  Solicitada: "
        f"{solicitada}"
    )

    escribir(
        f"  Visible texto: "
        f"{visible_texto!r}"
    )

    escribir(
        f"  Visible interpretada: "
        f"{visible}"
    )

    escribir(
        f"  Interna texto: "
        f"{interna_texto!r}"
    )

    escribir(
        f"  Interna interpretada: "
        f"{interna}"
    )

    if visible is None:

        raise RuntimeError(
            "FECHA_POSTCONSULTA_INVALIDA: "
            "no se pudo interpretar "
            "la fecha visible."
        )

    if interna is None:

        raise RuntimeError(
            "FECHA_POSTCONSULTA_INVALIDA: "
            "no se pudo interpretar "
            "la fecha interna."
        )

    if visible != interna:

        raise RuntimeError(
            "FECHA_POSTCONSULTA_INCONSISTENTE: "
            "fecha visible y fecha interna "
            "no coinciden entre sí. "
            "No se extraerán tasas de esta fecha."
        )

    sbs_cambio_fecha = (
        visible != solicitada
    )

    escribir(
        f"  ¿SBS cambió automáticamente "
        f"la fecha?: {sbs_cambio_fecha}"
    )

    if sbs_cambio_fecha:

        escribir(
            "  Fecha solicitada: "
            f"{solicitada}"
        )

        escribir(
            "  Fecha utilizada por SBS: "
            f"{visible}"
        )

    else:

        escribir(
            "[OK] SBS mantuvo exactamente "
            "la fecha solicitada."
        )

    return {
        "fecha_solicitada":
            solicitada,

        "fecha_resultado":
            visible,

        "visible_texto":
            visible_texto,

        "interna_texto":
            interna_texto,

        "sbs_cambio_fecha":
            sbs_cambio_fecha,
    }


# ============================================================
# 28. EXPANDIR TABLA RESPETANDO COLSPAN / ROWSPAN
# ============================================================

def expandir_tabla(
    tabla
):

    filas_html = tabla.find_all(
        "tr"
    )

    matriz = []

    rowspans = {}

    for fila_html in filas_html:

        fila = []

        columna = 0

        celdas = fila_html.find_all(
            ["th", "td"],
            recursive=False
        )

        if not celdas:

            celdas = fila_html.find_all(
                ["th", "td"]
            )

        # ----------------------------------------------------
        # Aplicar rowspans pendientes
        # ----------------------------------------------------

        def consumir_rowspans():

            nonlocal columna

            while columna in rowspans:

                datos = rowspans[
                    columna
                ]

                while (
                    len(fila)
                    <= columna
                ):

                    fila.append("")

                fila[
                    columna
                ] = datos[
                    "texto"
                ]

                datos[
                    "restantes"
                ] -= 1

                if (
                    datos[
                        "restantes"
                    ]
                    <= 0
                ):

                    del rowspans[
                        columna
                    ]

                columna += 1

        # ----------------------------------------------------

        for celda in celdas:

            consumir_rowspans()

            texto = limpiar_texto(
                celda.get_text(
                    " ",
                    strip=True
                )
            )

            try:

                colspan = int(
                    celda.get(
                        "colspan",
                        1
                    )
                )

            except Exception:

                colspan = 1

            try:

                rowspan = int(
                    celda.get(
                        "rowspan",
                        1
                    )
                )

            except Exception:

                rowspan = 1

            for desplazamiento in range(
                colspan
            ):

                col = (
                    columna
                    + desplazamiento
                )

                while len(
                    fila
                ) <= col:

                    fila.append("")

                fila[
                    col
                ] = texto

                if rowspan > 1:

                    rowspans[
                        col
                    ] = {
                        "restantes":
                            rowspan - 1,
                        "texto":
                            texto,
                    }

            columna += colspan

        # ----------------------------------------------------
        # Consumir rowspans restantes hasta
        # la última columna activa.
        # ----------------------------------------------------

        limite = (
            max(
                rowspans.keys(),
                default=-1
            )
            + 1
        )

        while columna < limite:

            if columna in rowspans:

                datos = rowspans[
                    columna
                ]

                while len(
                    fila
                ) <= columna:

                    fila.append("")

                fila[
                    columna
                ] = datos[
                    "texto"
                ]

                datos[
                    "restantes"
                ] -= 1

                if (
                    datos[
                        "restantes"
                    ]
                    <= 0
                ):

                    del rowspans[
                        columna
                    ]

            columna += 1

        matriz.append(
            fila
        )

    ancho = max(
        (
            len(fila)
            for fila in matriz
        ),
        default=0
    )

    for fila in matriz:

        while len(
            fila
        ) < ancho:

            fila.append("")

    return matriz


# ============================================================
# 29. VALIDAR EXACTAMENTE UNA CELDA ORIGINAL CONSUMO
# ============================================================

def encontrar_consumo_unico(
    tabla
):
    """
    IMPORTANTE:

    Se cuentan las celdas HTML ORIGINALES,
    no las celdas expandidas por colspan.

    Debe existir exactamente una celda cuyo
    texto completo normalizado sea 'consumo'.
    """

    coincidencias = []

    filas_html = tabla.find_all(
        "tr"
    )

    for numero_fila, fila in enumerate(
        filas_html
    ):

        celdas = fila.find_all(
            ["th", "td"],
            recursive=False
        )

        if not celdas:

            celdas = fila.find_all(
                ["th", "td"]
            )

        for numero_celda, celda in enumerate(
            celdas
        ):

            texto = normalizar_comparacion(
                celda.get_text(
                    " ",
                    strip=True
                )
            )

            if texto == "consumo":

                coincidencias.append({
                    "fila_html":
                        numero_fila,

                    "celda_html":
                        numero_celda,

                    "texto_original":
                        limpiar_texto(
                            celda.get_text(
                                " ",
                                strip=True
                            )
                        ),
                })

    if len(
        coincidencias
    ) != 1:

        raise RuntimeError(
            "CONSUMO_NO_UNICO: "
            "se esperaba exactamente "
            "una celda cuyo concepto fuera "
            "'Consumo', pero se encontraron "
            f"{len(coincidencias)}. "
            f"Coincidencias={coincidencias}. "
            "No se extraerán datos de esta fecha."
        )

    return coincidencias[0]


# ============================================================
# 30. ¿PARECE VALOR DE TASA?
# ============================================================

def parece_valor_tasa(
    valor
):

    texto = limpiar_texto(
        valor
    )

    if not texto:

        return False

    if normalizar_comparacion(
        texto
    ) in {
        "-",
        "s.i.",
        "s.i",
        "n.d.",
        "n.d",
        "nd",
        "n/a",
    }:

        # Conservamos marcas SBS como valor reportado.
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
# 31. CLASIFICAR ENCABEZADO DE COLUMNA
# ============================================================

def clasificar_encabezado(
    nombre
):
    """
    NO excluye 'Efectiva'.

    Solo elimina explícitamente:
    - nombres vacíos;
    - Promedio;
    - encabezados conceptuales/agregados;
    - valores puramente numéricos.
    """

    original = limpiar_texto(
        nombre
    )

    texto = normalizar_comparacion(
        original
    )

    if not texto:

        return (
            False,
            "NOMBRE_VACIO"
        )

    # --------------------------------------------------------
    # Promedio nunca es banco.
    # --------------------------------------------------------

    if (
        texto == "promedio"
        or
        texto.startswith(
            "promedio "
        )
        or
        texto.endswith(
            " promedio"
        )
        or
        "promedio del sistema"
        in texto
    ):

        return (
            False,
            "PROMEDIO"
        )

    # --------------------------------------------------------
    # Encabezados generales.
    # OJO: NO incluimos "efectiva" sola.
    # --------------------------------------------------------

    frases_agregadas = [
        "moneda nacional",
        "moneda extranjera",
        "tipo de credito",
        "tipos de credito",
        "tasa de interes",
        "tasas de interes",
        "tasa efectiva anual",
        "tasas efectivas anuales",
        "empresa bancaria",
        "empresas bancarias",
        "sistema bancario",
        "banca multiple",
        "total banca multiple",
    ]

    if any(
        frase in texto
        for frase
        in frases_agregadas
    ):

        return (
            False,
            "ENCABEZADO_AGREGADO"
        )

    if texto in {
        "empresa",
        "empresas",
        "%",
        "tasa",
        "tasas",
        "mn",
        "me",
    }:

        return (
            False,
            "ENCABEZADO_GENERICO"
        )

    # --------------------------------------------------------
    # Un número no puede ser nombre de banco.
    # --------------------------------------------------------

    numero = (
        texto
        .replace(
            ",",
            "."
        )
        .replace(
            "%",
            ""
        )
        .strip()
    )

    try:

        float(
            numero
        )

        return (
            False,
            "ENCABEZADO_NUMERICO"
        )

    except ValueError:

        pass

    # --------------------------------------------------------
    # 'Efectiva' queda aceptada aquí.
    # --------------------------------------------------------

    return (
        True,
        "BANCO_CANDIDATO"
    )


# ============================================================
# 32. ENCONTRAR COLUMNA CONCEPTO EN MATRIZ
# ============================================================

def localizar_consumo_en_fila_expandida(
    matriz,
    fila_html_consumo
):

    if (
        fila_html_consumo
        >= len(matriz)
    ):

        raise RuntimeError(
            "La fila HTML de Consumo "
            "no existe en la matriz expandida."
        )

    fila = matriz[
        fila_html_consumo
    ]

    columnas = [
        indice
        for indice, valor
        in enumerate(fila)
        if normalizar_comparacion(
            valor
        )
        == "consumo"
    ]

    if not columnas:

        raise RuntimeError(
            "No se pudo localizar 'Consumo' "
            "en la fila expandida."
        )

    # Si la celda original tuviera colspan,
    # podrían aparecer varias copias en la matriz.
    # La unicidad YA fue validada sobre el HTML original.
    # Usamos el inicio del bloque.
    return min(
        columnas
    )


# ============================================================
# 33. IDENTIFICAR FILA DE BANCOS
# ============================================================

def identificar_fila_bancos(
    matriz,
    fila_consumo,
    columna_concepto
):
    """
    Primero identifica las columnas donde la fila
    Consumo contiene una tasa o marca SBS.

    Después examina las filas superiores y escoge
    aquella con mayor cantidad de nombres que
    realmente parecen entidades.

    Promedio y encabezados agregados NO suman.
    """

    fila_datos = matriz[
        fila_consumo
    ]

    columnas_valor = [
        columna
        for columna in range(
            columna_concepto + 1,
            len(fila_datos)
        )
        if parece_valor_tasa(
            fila_datos[
                columna
            ]
        )
    ]

    if not columnas_valor:

        raise RuntimeError(
            "La fila Consumo no contiene "
            "columnas de tasas reconocibles."
        )

    candidatos = []

    for numero_fila in range(
        fila_consumo - 1,
        -1,
        -1
    ):

        fila = matriz[
            numero_fila
        ]

        banco_candidatos = 0
        excluidos = 0
        nombres_validos = []

        for columna in columnas_valor:

            valor = (
                fila[
                    columna
                ]
                if columna
                < len(fila)
                else ""
            )

            valido, razon = (
                clasificar_encabezado(
                    valor
                )
            )

            if valido:

                banco_candidatos += 1

                nombres_validos.append(
                    normalizar_comparacion(
                        valor
                    )
                )

            else:

                excluidos += 1

        distintos = len(
            set(
                nombres_validos
            )
        )

        distancia = (
            fila_consumo
            - numero_fila
        )

        # Priorizamos:
        # 1) muchos nombres válidos,
        # 2) muchos nombres distintos,
        # 3) cercanía con Consumo.
        score = (
            banco_candidatos
            * 100
            +
            distintos
            * 20
            -
            excluidos
            * 2
            -
            distancia
            * 0.1
        )

        candidatos.append({
            "fila":
                numero_fila,

            "score":
                score,

            "bancos_candidatos":
                banco_candidatos,

            "distintos":
                distintos,

            "columnas_valor":
                columnas_valor,
        })

    if not candidatos:

        raise RuntimeError(
            "No existen filas superiores "
            "para identificar bancos."
        )

    mejor = max(
        candidatos,
        key=lambda item:
        item["score"]
    )

    if mejor[
        "bancos_candidatos"
    ] == 0:

        raise RuntimeError(
            "No fue posible identificar "
            "una fila con nombres bancarios."
        )

    return mejor


# ============================================================
# 34. EXTRAER CONSUMO MN
# ============================================================

def extraer_consumo(
    html,
    fecha_solicitada,
    fecha_resultado
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tablas = soup.find_all(
        id=ID_TABLA_MN
    )

    if len(tablas) != 1:

        raise RuntimeError(
            "TABLA_MN_INVALIDA: "
            "se esperaba exactamente una tabla "
            f"con id={ID_TABLA_MN!r}, "
            f"pero se encontraron {len(tablas)}."
        )

    tabla = tablas[0]

    # --------------------------------------------------------
    # REGLA 4:
    # exactamente una celda original Consumo.
    # --------------------------------------------------------

    consumo_html = (
        encontrar_consumo_unico(
            tabla
        )
    )

    matriz = expandir_tabla(
        tabla
    )

    fila_consumo = (
        consumo_html[
            "fila_html"
        ]
    )

    columna_concepto = (
        localizar_consumo_en_fila_expandida(
            matriz,
            fila_consumo
        )
    )

    cabecera = (
        identificar_fila_bancos(
            matriz,
            fila_consumo,
            columna_concepto
        )
    )

    fila_bancos = matriz[
        cabecera[
            "fila"
        ]
    ]

    fila_datos = matriz[
        fila_consumo
    ]

    registros = []
    excluidos = []

    for columna in cabecera[
        "columnas_valor"
    ]:

        tasa = (
            limpiar_texto(
                fila_datos[
                    columna
                ]
            )
            if columna
            < len(
                fila_datos
            )
            else ""
        )

        nombre = (
            limpiar_texto(
                fila_bancos[
                    columna
                ]
            )
            if columna
            < len(
                fila_bancos
            )
            else ""
        )

        valido, razon = (
            clasificar_encabezado(
                nombre
            )
        )

        if not valido:

            excluidos.append({
                "columna":
                    columna,

                "nombre":
                    nombre,

                "tasa":
                    tasa,

                "razon":
                    razon,
            })

            continue

        registros.append({
            "fecha_solicitada":
                fecha_solicitada,

            "fecha_resultado":
                fecha_resultado,

            "banco_original":
                nombre,

            "tasa_consumo_mn":
                tasa,

            "columna":
                columna,
        })

    # --------------------------------------------------------
    # Duplicados de nombres bancarios:
    # mejor detenerse que interpretar mal.
    # --------------------------------------------------------

    claves = [
        normalizar_comparacion(
            registro[
                "banco_original"
            ]
        )
        for registro in registros
    ]

    duplicados = sorted(
        {
            clave
            for clave
            in claves
            if claves.count(
                clave
            )
            > 1
        }
    )

    if duplicados:

        raise RuntimeError(
            "BANCOS_DUPLICADOS: "
            "la fila identificada como "
            "encabezado produce nombres "
            f"duplicados: {duplicados}. "
            "No se extraerá esta fecha."
        )

    if not registros:

        raise RuntimeError(
            "No se obtuvo ninguna empresa "
            "bancaria válida en la fila Consumo."
        )

    return {
        "matriz":
            matriz,

        "fila_consumo":
            fila_consumo,

        "columna_concepto":
            columna_concepto,

        "consumo_html":
            consumo_html,

        "cabecera":
            cabecera,

        "registros":
            registros,

        "excluidos":
            excluidos,
    }


# ============================================================
# 35. MOSTRAR CONTEXTO DE TABLA
# ============================================================

def mostrar_contexto_tabla(
    resultado
):

    matriz = resultado[
        "matriz"
    ]

    fila_consumo = resultado[
        "fila_consumo"
    ]

    inicio = max(
        0,
        fila_consumo - 5
    )

    fin = min(
        len(matriz),
        fila_consumo + 3
    )

    escribir()
    escribir(
        "Filas alrededor de Consumo:"
    )

    for indice in range(
        inicio,
        fin
    ):

        escribir(
            f"  Fila {indice}: "
            f"{matriz[indice]}"
        )


# ============================================================
# 36. ANALIZAR UNA FECHA
# ============================================================

def analizar_fecha(
    navegador,
    fecha
):

    titulo(
        f"CONSULTA CONTROLADA: {fecha}"
    )

    validar_configuracion(
        navegador
    )

    escribir()
    escribir(
        "Estado antes de modificar la fecha:"
    )

    escribir(
        f"  Visible: "
        f"{leer_fecha_visible(navegador)!r}"
    )

    escribir(
        f"  Interna: "
        f"{leer_fecha_interna(navegador)!r}"
    )

    # --------------------------------------------------------
    # PUNTO 1:
    # antes de Consultar ambas deben ser
    # exactamente la fecha objetivo.
    # --------------------------------------------------------

    establecer_fecha(
        navegador,
        fecha
    )

    # Revalidar configuración inmediatamente
    # antes de pulsar Consultar.
    validar_configuracion(
        navegador
    )

    escribir()
    escribir(
        "Fecha PRE-CONSULTA validada."
    )

    escribir(
        "Ahora sí se pulsará Consultar."
    )

    # --------------------------------------------------------
    # PUNTO 2:
    # esperar respuesta real.
    # --------------------------------------------------------

    evidencia = pulsar_consultar(
        navegador,
        fecha
    )

    # --------------------------------------------------------
    # Comprobar fecha utilizada por SBS.
    # --------------------------------------------------------

    fecha_post = (
        validar_fecha_postconsulta(
            navegador,
            fecha
        )
    )

    validar_configuracion(
        navegador
    )

    html = navegador.page_source

    hash_html = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    escribir(
        f"SHA256 HTML resultado: "
        f"{hash_html}"
    )

    # --------------------------------------------------------
    # PUNTOS 3 y 4:
    # extracción estricta.
    # --------------------------------------------------------

    resultado = extraer_consumo(
        html,
        fecha,
        fecha_post[
            "fecha_resultado"
        ].strftime(
            "%d/%m/%Y"
        )
    )

    escribir()
    escribir(
        "Validación de Consumo:"
    )

    escribir(
        "  Celdas originales exactas "
        "'Consumo': 1"
    )

    escribir(
        f"  Fila Consumo: "
        f"{resultado['fila_consumo']}"
    )

    escribir(
        f"  Columna inicial del concepto: "
        f"{resultado['columna_concepto']}"
    )

    escribir(
        f"  Fila identificada con bancos: "
        f"{resultado['cabecera']['fila']}"
    )

    mostrar_contexto_tabla(
        resultado
    )

    # --------------------------------------------------------
    # Columnas excluidas
    # --------------------------------------------------------

    subtitulo(
        "COLUMNAS EXCLUIDAS COMO NO-BANCO"
    )

    if not resultado[
        "excluidos"
    ]:

        escribir(
            "<NINGUNA>"
        )

    else:

        for item in resultado[
            "excluidos"
        ]:

            escribir(
                f"Columna {item['columna']} | "
                f"nombre={item['nombre']!r} | "
                f"valor={item['tasa']!r} | "
                f"razón={item['razon']}"
            )

    # --------------------------------------------------------
    # Valores bancarios
    # --------------------------------------------------------

    subtitulo(
        "VALORES EXTRAÍDOS"
    )

    escribir(
        "Formato:"
    )

    escribir(
        "fecha | banco_original | tasa_consumo_mn"
    )

    escribir()

    for registro in resultado[
        "registros"
    ]:

        escribir(
            f"{registro['fecha_resultado']} | "
            f"{registro['banco_original']} | "
            f"{registro['tasa_consumo_mn']}"
        )

    escribir()
    escribir(
        f"Total de empresas extraídas: "
        f"{len(resultado['registros'])}"
    )

    return {
        "estado":
            "OK",

        "fecha_solicitada":
            fecha,

        "fecha_resultado":
            fecha_post[
                "fecha_resultado"
            ].strftime(
                "%d/%m/%Y"
            ),

        "sbs_cambio_fecha":
            fecha_post[
                "sbs_cambio_fecha"
            ],

        "evidencia":
            evidencia[
                "evidencia"
            ],

        "registros":
            resultado[
                "registros"
            ],

        "excluidos":
            resultado[
                "excluidos"
            ],
    }


# ============================================================
# 37. MOSTRAR RESUMEN FINAL
# ============================================================

def mostrar_resumen(
    resultados
):

    titulo(
        "RESUMEN FINAL DE LAS DOS FECHAS"
    )

    for resultado in resultados:

        escribir()

        escribir(
            f"Fecha solicitada: "
            f"{resultado['fecha_solicitada']}"
        )

        escribir(
            f"Estado: "
            f"{resultado['estado']}"
        )

        if resultado[
            "estado"
        ] == "OK":

            escribir(
                f"Fecha resultado SBS: "
                f"{resultado['fecha_resultado']}"
            )

            escribir(
                f"¿SBS cambió la fecha?: "
                f"{resultado['sbs_cambio_fecha']}"
            )

            escribir(
                f"Evidencia de actualización: "
                f"{resultado['evidencia']}"
            )

            escribir(
                f"Empresas extraídas: "
                f"{len(resultado['registros'])}"
            )

            escribir(
                f"Columnas excluidas: "
                f"{len(resultado['excluidos'])}"
            )

            escribir()

            for registro in resultado[
                "registros"
            ]:

                escribir(
                    f"  "
                    f"{registro['fecha_resultado']} | "
                    f"{registro['banco_original']} | "
                    f"{registro['tasa_consumo_mn']}"
                )

        else:

            escribir(
                f"Problema: "
                f"{resultado['problema']}"
            )


# ============================================================
# 38. GUARDAR REPORTE
# ============================================================

def guardar_reporte():

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

    print()
    print("=" * 118)
    print("DIAGNÓSTICO GUARDADO EN:")
    print(ARCHIVO_TXT)
    print("=" * 118)


# ============================================================
# 39. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    resultados = []

    try:

        titulo(
            "PRUEBA HISTÓRICA CONTROLADA SBS "
            "- TASA ACTIVA CONSUMO MN"
        )

        escribir(
            "Únicamente se consultarán:"
        )

        for fecha in FECHAS_CONTROL:

            escribir(
                f"  {fecha}"
            )

        escribir()
        escribir(
            "NO se descargarán 211 meses."
        )

        escribir(
            "NO se seleccionarán cinco bancos."
        )

        escribir(
            "NO se interpolarán valores."
        )

        escribir(
            "NO se cambiará a Moneda Extranjera."
        )

        navegador = crear_navegador()

        escribir()
        escribir(
            "Abriendo página oficial SBS..."
        )

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
                "No se pudo acceder "
                "a la aplicación SBS real."
            )

        titulo(
            "CONFIGURACIÓN INICIAL"
        )

        escribir(
            f"URL final: "
            f"{navegador.current_url}"
        )

        validar_configuracion(
            navegador
        )

        escribir(
            f"Fecha visible inicial: "
            f"{leer_fecha_visible(navegador)!r}"
        )

        escribir(
            f"Fecha interna inicial: "
            f"{leer_fecha_interna(navegador)!r}"
        )

        escribir(
            f"Tabla MN presente: "
            f"{len(navegador.find_elements(By.ID, ID_TABLA_MN)) == 1}"
        )

        # ----------------------------------------------------
        # Solo dos fechas.
        # Si una fecha falla, se registra y no se
        # extraen datos de ella; luego puede probarse
        # la otra fecha de control.
        # ----------------------------------------------------

        for fecha in FECHAS_CONTROL:

            try:

                resultado = analizar_fecha(
                    navegador,
                    fecha
                )

                resultados.append(
                    resultado
                )

            except Exception as error:

                titulo(
                    f"PROBLEMA EN FECHA {fecha}"
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
                    "La fecha fue detenida."
                )

                escribir(
                    "No se extrajeron tasas "
                    "para esa fecha."
                )

                resultados.append({
                    "estado":
                        "ERROR",

                    "fecha_solicitada":
                        fecha,

                    "problema":
                        repr(error),
                })

        mostrar_resumen(
            resultados
        )

    except Exception as error:

        titulo(
            "ERROR GENERAL"
        )

        escribir(
            f"{type(error).__name__}: "
            f"{repr(error)}"
        )

        raise

    finally:

        if navegador is not None:

            try:

                navegador.quit()

            except Exception:

                pass

        guardar_reporte()


# ============================================================
# 40. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()