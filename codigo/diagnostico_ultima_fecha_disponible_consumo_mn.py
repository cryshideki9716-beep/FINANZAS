# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico mensual de última fecha disponible - Tasa activa Consumo MN - SBS

from pathlib import Path
from datetime import date, timedelta
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
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# ÚNICAMENTE ESTOS CINCO MESES
MESES_CONTROL = [
    (2015, 6),
    (2016, 6),
    (2017, 6),
    (2018, 6),
    (2019, 6),
]

TIMEOUT = 45
TIMEOUT_MANUAL = 180

# Pausa entre días distintos.
PAUSA_ENTRE_INTENTOS = 1.0

# Si hay un fallo técnico:
# 1 intento original + 1 reintento controlado.
MAX_REINTENTOS_TECNICOS = 1

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "diagnostico_ultima_fecha_disponible_consumo_mn.txt"
)


# ============================================================
# 2. CONTROLES SBS
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

ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

ID_DATAZONE_MN = (
    "ctl00_cphContent_rpgActualMn_ctl00_DataZone_DT"
)


# ============================================================
# 3. ERROR TÉCNICO EXPLÍCITO
# ============================================================

class ErrorTecnicoDiagnostico(Exception):
    """
    Error que impide saber si la ausencia de datos
    es real o si la prueba simplemente falló
    técnicamente.

    Un ErrorTecnicoDiagnostico NUNCA debe ser
    interpretado como MES_SIN_DATO.
    """
    pass


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
# 5. NORMALIZACIÓN
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
# 6. FECHAS
# ============================================================

def fecha_a_texto(fecha):

    return fecha.strftime(
        "%d/%m/%Y"
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
        - timedelta(days=1)
    )


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

        anio = int(
            coincidencia.group(3)
        )

        try:

            return date(
                anio,
                mes,
                dia
            )

        except ValueError:

            return None

    # YYYY-MM-DD / formato interno Telerik
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        valor
    )

    if coincidencia:

        anio = int(
            coincidencia.group(1)
        )

        mes = int(
            coincidencia.group(2)
        )

        dia = int(
            coincidencia.group(3)
        )

        try:

            return date(
                anio,
                mes,
                dia
            )

        except ValueError:

            return None

    return None


# ============================================================
# 7. CREAR NAVEGADOR
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

        raise ErrorTecnicoDiagnostico(
            "No se pudo iniciar Chrome/Selenium: "
            f"{type(error).__name__}: {error}"
        ) from error


# ============================================================
# 8. ESPERAR DOCUMENTO
# ============================================================

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

        raise ErrorTecnicoDiagnostico(
            "Timeout esperando document.readyState=complete."
        ) from error

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Error de Selenium esperando "
            "la carga del documento: "
            f"{error}"
        ) from error


# ============================================================
# 9. COMPROBAR PÁGINA BASE SBS
# ============================================================

def pagina_base_real(
    navegador
):

    try:

        hay_fecha = navegador.find_elements(
            By.ID,
            ID_FECHA_VISIBLE
        )

        hay_boton = navegador.find_elements(
            By.ID,
            ID_BOTON
        )

        return (
            len(hay_fecha) > 0
            and
            len(hay_boton) > 0
        )

    except WebDriverException:

        return False


# ============================================================
# 10. VERIFICACIÓN MANUAL
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
            pagina_base_real(d)
        )

        return True

    except TimeoutException:

        escribir()
        escribir(
            "La aplicación SBS real todavía "
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
            pagina_base_real(d)
        )

        return True

    except TimeoutException as error:

        raise ErrorTecnicoDiagnostico(
            "No se recuperó la página SBS real "
            "después de la verificación manual."
        ) from error

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Selenium perdió acceso a la página SBS: "
            f"{error}"
        ) from error


# ============================================================
# 11. RECARGAR URL BASE
# ============================================================

def cargar_base(
    navegador
):

    try:

        navegador.get(
            URL
        )

    except TimeoutException as error:

        raise ErrorTecnicoDiagnostico(
            "Timeout al abrir la URL base SBS."
        ) from error

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Error de Selenium al abrir "
            "la URL base SBS: "
            f"{error}"
        ) from error

    esperar_documento(
        navegador
    )

    time.sleep(
        1.5
    )

    if not asegurar_pagina_real(
        navegador
    ):

        raise ErrorTecnicoDiagnostico(
            "La URL base no contiene los controles "
            "esperados de la aplicación SBS."
        )


# ============================================================
# 12. DATEPICKER
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

            elementos = navegador.find_elements(
                metodo,
                valor
            )

            if elementos:

                return elementos[0]

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Error de Selenium buscando "
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

        raise ErrorTecnicoDiagnostico(
            "No se pudo leer la fecha visible: "
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

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoDiagnostico(
            "No se pudo leer la fecha interna: "
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

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoDiagnostico(
            "No se pudo leer un control SBS: "
            f"{error}"
        ) from error

    return None


# ============================================================
# 13. VALIDAR MN Y B
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

    if moneda != "MN":

        raise ErrorTecnicoDiagnostico(
            "CONFIGURACION_MONEDA_INVALIDA: "
            f"se esperaba MN y se obtuvo "
            f"{moneda!r}."
        )

    if entidad != "B":

        raise ErrorTecnicoDiagnostico(
            "CONFIGURACION_ENTIDAD_INVALIDA: "
            f"se esperaba B y se obtuvo "
            f"{entidad!r}."
        )

    return moneda, entidad


# ============================================================
# 14. ESTADO DATEPICKER
# ============================================================

def obtener_estado_fecha(
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
        "objetivo":
            fecha_objetivo,

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
                visible == fecha_objetivo
                and
                interna == fecha_objetivo
            ),
    }


# ============================================================
# 15. CAMBIAR FECHA CON TECLADO
# ============================================================

def cambiar_fecha_teclado(
    navegador,
    fecha_objetivo
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise ErrorTecnicoDiagnostico(
            "No se encontró el DatePicker visible."
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

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoDiagnostico(
            "Fallo técnico escribiendo "
            "en el DatePicker: "
            f"{error}"
        ) from error

    time.sleep(
        0.8
    )


# ============================================================
# 16. FALLBACK TELERIK
# ============================================================

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

        raise ErrorTecnicoDiagnostico(
            "Error Selenium ejecutando "
            "la API Telerik: "
            f"{error}"
        ) from error

    time.sleep(
        0.8
    )

    return resultado


# ============================================================
# 17. ESTABLECER FECHA ESTRICTAMENTE
# ============================================================

def establecer_fecha(
    navegador,
    fecha_objetivo
):

    cambiar_fecha_teclado(
        navegador,
        fecha_objetivo
    )

    estado = obtener_estado_fecha(
        navegador,
        fecha_objetivo
    )

    if estado[
        "ambas_ok"
    ]:

        return estado

    resultado_telerik = cambiar_fecha_telerik(
        navegador,
        fecha_objetivo
    )

    estado = obtener_estado_fecha(
        navegador,
        fecha_objetivo
    )

    if not estado[
        "ambas_ok"
    ]:

        raise ErrorTecnicoDiagnostico(
            "FECHA_PRECONSULTA_INVALIDA: "
            f"{fecha_a_texto(fecha_objetivo)} | "
            f"Telerik={resultado_telerik!r} | "
            f"visible={estado['visible_texto']!r} | "
            f"interna={estado['interna_texto']!r}"
        )

    return estado


# ============================================================
# 18. BOTÓN CONSULTAR
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

            elementos = navegador.find_elements(
                metodo,
                valor
            )

            if elementos:

                return elementos[0]

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Error Selenium buscando "
            "el botón Consultar: "
            f"{error}"
        ) from error

    return None


# ============================================================
# 19. DETECTAR "NO EXISTE INFORMACIÓN"
# ============================================================

def buscar_sin_informacion(
    navegador
):

    try:

        texto_visible = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except (
        WebDriverException,
        NoSuchElementException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoDiagnostico(
            "No se pudo leer el texto visible "
            "de la respuesta SBS: "
            f"{error}"
        ) from error

    texto_limpio = limpiar_texto(
        texto_visible
    )

    normal = normalizar_texto(
        texto_limpio
    )

    frase_normal = (
        "no existe informacion "
        "para la fecha elegida"
    )

    encontrado = (
        frase_normal
        in normal
    )

    fragmento = ""

    if encontrado:

        posicion = normal.find(
            frase_normal
        )

        if posicion >= 0:

            inicio = max(
                0,
                posicion - 150
            )

            fin = min(
                len(texto_limpio),
                posicion + 350
            )

            fragmento = (
                texto_limpio[
                    inicio:fin
                ]
            )

        else:

            fragmento = (
                "No existe información "
                "para la fecha elegida"
            )

    return encontrado, fragmento


# ============================================================
# 20. CONFIRMAR EXACTAMENTE "al DD/MM/YYYY"
# ============================================================

def buscar_confirmacion_periodo(
    navegador,
    fecha_objetivo
):

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    patron = re.compile(
        rf"\bal\s+{re.escape(texto_fecha)}\b",
        flags=re.IGNORECASE
    )

    try:

        candidatos = navegador.execute_script(
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

                if (!texto) {
                    continue;
                }

                if (
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

        raise ErrorTecnicoDiagnostico(
            "No se pudieron inspeccionar "
            "los textos de fecha del resultado: "
            f"{error}"
        ) from error

    confirmaciones = []

    vistos = set()

    for item in candidatos or []:

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

        confirmaciones.append({
            "tag":
                item.get(
                    "tag",
                    ""
                ),

            "id":
                item.get(
                    "id",
                    ""
                ),

            "text":
                texto,
        })

    return confirmaciones


# ============================================================
# 21. SHA DEL HTML
# ============================================================

def sha_html(
    navegador
):

    try:

        html = navegador.page_source

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "No se pudo recuperar page_source: "
            f"{error}"
        ) from error

    return hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()


# ============================================================
# 22. INSPECCIONAR ESTADO DEL RESULTADO
# ============================================================

def inspeccionar_estado_resultado(
    navegador,
    fecha_objetivo
):
    """
    Registra por separado:

      - si la fecha aparece como
        'al DD/MM/YYYY';
      - si SBS dice
        'No existe información...'.

    REGLA:
    si ambas aparecen simultáneamente,
    la respuesta principal es SIN_INFORMACION,
    pero periodo_confirmado sigue siendo True.
    """

    confirmaciones = (
        buscar_confirmacion_periodo(
            navegador,
            fecha_objetivo
        )
    )

    sin_info, mensaje_sin_info = (
        buscar_sin_informacion(
            navegador
        )
    )

    periodo_confirmado = (
        len(
            confirmaciones
        )
        > 0
    )

    # --------------------------------------------------------
    # PRIORIDAD METODOLÓGICA SOLICITADA
    # --------------------------------------------------------

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

        "confirmaciones":
            confirmaciones,

        "sin_info":
            sin_info,

        "mensaje_sin_info":
            mensaje_sin_info,
    }


# ============================================================
# 23. CONSULTAR FECHA
# ============================================================

def consultar_fecha(
    navegador,
    fecha_objetivo
):
    """
    Después del click comprueba SIEMPRE
    las dos señales conjuntamente:

      A. al DD/MM/YYYY
      B. No existe información...

    Si A y B aparecen simultáneamente:
        respuesta = SIN_INFORMACION
        periodo_confirmado = True

    El mensaje SIN_INFORMACION tiene prioridad.
    """

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise ErrorTecnicoDiagnostico(
            "No se encontró el botón Consultar."
        )

    sha_antes = sha_html(
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

    except (
        WebDriverException,
        StaleElementReferenceException
    ) as error:

        raise ErrorTecnicoDiagnostico(
            "Fallo técnico pulsando Consultar: "
            f"{error}"
        ) from error

    inicio = time.time()
    cambio_detectado_en = None

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        estado = (
            inspeccionar_estado_resultado(
                navegador,
                fecha_objetivo
            )
        )

        # ----------------------------------------------------
        # SIN_INFORMACION TIENE PRIORIDAD,
        # incluso si fecha está confirmada.
        # ----------------------------------------------------

        if estado[
            "sin_info"
        ]:

            time.sleep(
                0.5
            )

            # Releer después del margen.
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

            # Releer para detectar la posibilidad
            # de que aparezca simultáneamente
            # el mensaje SIN_INFORMACION.
            return inspeccionar_estado_resultado(
                navegador,
                fecha_objetivo
            )

        sha_actual = sha_html(
            navegador
        )

        if (
            sha_actual != sha_antes
        ):

            if cambio_detectado_en is None:

                cambio_detectado_en = (
                    time.time()
                )

            # Dar margen al resultado postback.
            if (
                time.time()
                - cambio_detectado_en
                >= 3.0
            ):

                break

        time.sleep(
            0.25
        )

    # --------------------------------------------------------
    # INSPECCIÓN FINAL
    # --------------------------------------------------------

    return inspeccionar_estado_resultado(
        navegador,
        fecha_objetivo
    )


# ============================================================
# 24. ANALIZAR ESTRUCTURA MN
# ============================================================

def analizar_estructura_mn(
    navegador
):
    """
    NO extrae tasas.

    Solo diagnostica:

      - tabla MN;
      - DataZone;
      - Consumo exacto;
      - encabezados bancarios;
      - cantidad de bancos.

    No exige un número fijo de columnas.
    """

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    function limpiar(txt) {

        return (txt || '')
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normalizar(txt) {

        return limpiar(txt)
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

        const rect =
            el.getBoundingClientRect();

        return (
            rect.width > 0
            &&
            rect.height > 0
        );
    }

    function esNumerico(txt) {

        txt = limpiar(txt);

        if (!txt) {
            return false;
        }

        const n =
            normalizar(txt);

        const faltantes =
            new Set([
                '-',
                's.i.',
                's.i',
                'n.d.',
                'n.d',
                'nd',
                'n/a',
                'na'
            ]);

        if (
            faltantes.has(n)
        ) {
            return true;
        }

        const numero =
            txt
            .replace(/%/g, '')
            .replace(/,/g, '.')
            .trim();

        return (
            /^[-+]?\d+(\.\d+)?$/
            .test(numero)
        );
    }

    const outer =
        document.getElementById(
            OUTER_ID
        );

    const dataZone =
        document.getElementById(
            DATA_ID
        );

    const resultado = {

        outerExists:
            outer !== null,

        outerVisible:
            outer
            ? visible(outer)
            : false,

        dataExists:
            dataZone !== null,

        dataVisible:
            dataZone
            ? visible(dataZone)
            : false,

        consumoCount:
            0,

        consumoLocations:
            [],

        rawHeaders:
            [],

        bankHeaders:
            [],

        bankCount:
            0,

        promedioDetected:
            false,

        selectedHeaderRowIndex:
            null,

        selectedHeaderRowCells:
            null
    };

    // --------------------------------------------------------
    // A. CONSUMO EN TABLA EXTERNA
    // --------------------------------------------------------

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

            if (
                dataZone
                &&
                dataZone.contains(celda)
            ) {
                continue;
            }

            if (
                celda.querySelector('table')
            ) {
                continue;
            }

            const texto =
                limpiar(
                    celda.innerText
                    ||
                    celda.textContent
                );

            if (
                normalizar(texto)
                === 'consumo'
            ) {

                const fila =
                    celda.closest('tr');

                resultado.consumoCount++;

                resultado.consumoLocations.push({
                    rowIndex:
                        fila
                        ? fila.rowIndex
                        : null,

                    text:
                        texto
                });
            }
        }
    }

    // --------------------------------------------------------
    // B. ENCABEZADOS EN DATAZONE
    // --------------------------------------------------------

    if (dataZone) {

        const filas =
            Array.from(
                dataZone.rows
            );

        const candidatos = [];

        for (
            let i = 0;
            i < filas.length;
            i++
        ) {

            const fila =
                filas[i];

            if (!visible(fila)) {
                continue;
            }

            const celdas =
                Array.from(
                    fila.cells
                );

            if (
                celdas.length === 0
            ) {
                continue;
            }

            const textos = [];

            for (
                const celda
                of celdas
            ) {

                if (!visible(celda)) {
                    continue;
                }

                if (
                    celda.querySelector('table')
                ) {
                    continue;
                }

                const texto =
                    limpiar(
                        celda.innerText
                        ||
                        celda.textContent
                    );

                if (!texto) {
                    continue;
                }

                if (
                    esNumerico(texto)
                ) {
                    continue;
                }

                textos.push(
                    texto
                );
            }

            const unicos = [];

            const vistos =
                new Set();

            for (
                const texto
                of textos
            ) {

                const clave =
                    normalizar(texto);

                if (
                    vistos.has(clave)
                ) {
                    continue;
                }

                vistos.add(clave);

                unicos.push(
                    texto
                );
            }

            if (
                unicos.length > 0
            ) {

                candidatos.push({
                    rowIndex:
                        i,

                    cellCount:
                        celdas.length,

                    textCount:
                        unicos.length,

                    texts:
                        unicos
                });
            }
        }

        candidatos.sort(
            (a, b) => {

                if (
                    b.textCount
                    !==
                    a.textCount
                ) {

                    return (
                        b.textCount
                        -
                        a.textCount
                    );
                }

                if (
                    b.cellCount
                    !==
                    a.cellCount
                ) {

                    return (
                        b.cellCount
                        -
                        a.cellCount
                    );
                }

                return (
                    a.rowIndex
                    -
                    b.rowIndex
                );
            }
        );

        if (
            candidatos.length > 0
        ) {

            const mejor =
                candidatos[0];

            resultado.selectedHeaderRowIndex =
                mejor.rowIndex;

            resultado.selectedHeaderRowCells =
                mejor.cellCount;

            resultado.rawHeaders =
                mejor.texts;

            const genericos =
                new Set([
                    'moneda nacional',
                    'moneda extranjera',
                    'empresa',
                    'empresas',
                    'tasa',
                    'tasas',
                    '%'
                ]);

            const bancos = [];

            let promedio =
                false;

            for (
                const texto
                of mejor.texts
            ) {

                const clave =
                    normalizar(texto);

                if (
                    clave === 'promedio'
                ) {

                    promedio =
                        true;

                    continue;
                }

                if (
                    genericos.has(clave)
                ) {
                    continue;
                }

                bancos.push(
                    texto
                );
            }

            resultado.bankHeaders =
                bancos;

            resultado.bankCount =
                bancos.length;

            resultado.promedioDetected =
                promedio;
        }
    }

    return resultado;
    """

    try:

        return navegador.execute_script(
            script,
            ID_TABLA_MN_EXTERNA,
            ID_DATAZONE_MN,
        )

    except WebDriverException as error:

        raise ErrorTecnicoDiagnostico(
            "Error técnico inspeccionando "
            "la estructura MN: "
            f"{error}"
        ) from error


# ============================================================
# 25. EVALUAR UN DÍA
# ============================================================

def evaluar_dia(
    navegador,
    fecha_objetivo
):

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    # Cada prueba diaria parte de cero.
    cargar_base(
        navegador
    )

    moneda, entidad = validar_mn_b(
        navegador
    )

    estado_fecha = establecer_fecha(
        navegador,
        fecha_objetivo
    )

    # Confirmación final antes del POST.
    moneda, entidad = validar_mn_b(
        navegador
    )

    respuesta = consultar_fecha(
        navegador,
        fecha_objetivo
    )

    periodo_confirmado = respuesta[
        "periodo_confirmado"
    ]

    # --------------------------------------------------------
    # La estructura se inspecciona aunque SBS diga SIN_INFO,
    # únicamente con fines diagnósticos.
    #
    # PERO SIN_INFORMACION nunca puede ser fecha válida.
    # --------------------------------------------------------

    estructura = analizar_estructura_mn(
        navegador
    )

    valida = (
        respuesta[
            "respuesta"
        ]
        == "PERIODO_CONFIRMADO"
        and
        periodo_confirmado
        and
        not respuesta[
            "sin_info"
        ]
        and
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

    return {
        "fecha":
            fecha_objetivo,

        "fecha_texto":
            texto_fecha,

        "moneda":
            moneda,

        "entidad":
            entidad,

        "datepicker_ok":
            estado_fecha[
                "ambas_ok"
            ],

        "respuesta":
            respuesta[
                "respuesta"
            ],

        "periodo_confirmado":
            periodo_confirmado,

        "confirmaciones":
            respuesta[
                "confirmaciones"
            ],

        "sin_info":
            respuesta[
                "sin_info"
            ],

        "mensaje_sin_info":
            respuesta[
                "mensaje_sin_info"
            ],

        "tabla_mn_existe":
            estructura[
                "outerExists"
            ],

        "tabla_mn_visible":
            estructura[
                "outerVisible"
            ],

        "datazone_existe":
            estructura[
                "dataExists"
            ],

        "datazone_visible":
            estructura[
                "dataVisible"
            ],

        "consumo_count":
            estructura[
                "consumoCount"
            ],

        "consumo_locations":
            estructura[
                "consumoLocations"
            ],

        "encabezados":
            estructura[
                "bankHeaders"
            ],

        "cantidad_bancos":
            estructura[
                "bankCount"
            ],

        "promedio":
            estructura[
                "promedioDetected"
            ],

        "valida":
            valida,
    }


# ============================================================
# 26. MOSTRAR INTENTO
# ============================================================

def mostrar_intento(
    intento,
    dias_retrocedidos,
    numero_reintento=0
):

    escribir()
    escribir(
        f"Fecha probada: "
        f"{intento['fecha_texto']}"
    )

    escribir(
        f"Días retrocedidos: "
        f"{dias_retrocedidos}"
    )

    escribir(
        f"Reintento técnico: "
        f"{numero_reintento}"
    )

    escribir(
        f"DatePicker correcto: "
        f"{intento['datepicker_ok']}"
    )

    escribir(
        f"Respuesta SBS: "
        f"{intento['respuesta']}"
    )

    escribir(
        f"Período 'al "
        f"{intento['fecha_texto']}' confirmado: "
        f"{intento['periodo_confirmado']}"
    )

    escribir(
        f"'No existe información...': "
        f"{intento['sin_info']}"
    )

    # Caso metodológicamente importante:
    if (
        intento[
            "periodo_confirmado"
        ]
        and
        intento[
            "sin_info"
        ]
    ):

        escribir(
            "  [IMPORTANTE] SBS confirmó "
            "la fecha del resultado, pero "
            "simultáneamente indicó que "
            "no existe información."
        )

        escribir(
            "  Se conserva "
            "periodo_confirmado=True, "
            "pero la respuesta principal es "
            "SIN_INFORMACION."
        )

    if intento[
        "mensaje_sin_info"
    ]:

        escribir(
            f"Mensaje SBS: "
            f"{intento['mensaje_sin_info']!r}"
        )

    escribir(
        f"Tabla MN existe: "
        f"{intento['tabla_mn_existe']}"
    )

    escribir(
        f"Tabla MN visible: "
        f"{intento['tabla_mn_visible']}"
    )

    escribir(
        f"DataZone existe: "
        f"{intento['datazone_existe']}"
    )

    escribir(
        f"DataZone visible: "
        f"{intento['datazone_visible']}"
    )

    escribir(
        f"Consumo exacto: "
        f"{intento['consumo_count']}"
    )

    escribir(
        f"Bancos detectados: "
        f"{intento['cantidad_bancos']}"
    )

    escribir(
        f"Promedio detectado: "
        f"{intento['promedio']}"
    )

    escribir(
        f"FECHA VÁLIDA: "
        f"{intento['valida']}"
    )


# ============================================================
# 27. REINTENTO CONTROLADO DE UNA FECHA
# ============================================================

def evaluar_dia_con_reintento(
    navegador,
    fecha_objetivo,
    dias_retrocedidos
):
    """
    Máximo:
      intento original + 1 reintento técnico.

    Si ambos fallan técnicamente:
      devuelve ERROR_TECNICO

    NO permite seguir retrocediendo como si
    esa fecha simplemente no tuviera datos.
    """

    errores_tecnicos = []

    total_intentos = (
        1
        + MAX_REINTENTOS_TECNICOS
    )

    for numero_intento in range(
        total_intentos
    ):

        try:

            if numero_intento > 0:

                escribir()
                escribir(
                    "[REINTENTO TÉCNICO CONTROLADO]"
                )

                escribir(
                    f"Se repetirá una sola vez "
                    f"la fecha "
                    f"{fecha_a_texto(fecha_objetivo)}."
                )

                time.sleep(
                    2
                )

            intento = evaluar_dia(
                navegador,
                fecha_objetivo
            )

            mostrar_intento(
                intento,
                dias_retrocedidos,
                numero_reintento=numero_intento
            )

            return {
                "estado":
                    "OK",

                "intento":
                    intento,

                "errores_tecnicos":
                    errores_tecnicos,
            }

        except (
            ErrorTecnicoDiagnostico,
            TimeoutException,
            WebDriverException,
            StaleElementReferenceException,
            NoSuchWindowException,
        ) as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )

            errores_tecnicos.append(
                detalle
            )

            escribir()
            escribir(
                "[ERROR TÉCNICO]"
            )

            escribir(
                f"Fecha: "
                f"{fecha_a_texto(fecha_objetivo)}"
            )

            escribir(
                f"Intento técnico: "
                f"{numero_intento + 1}/"
                f"{total_intentos}"
            )

            escribir(
                f"Detalle: "
                f"{detalle}"
            )

            # Si queda un reintento, continuar.
            if (
                numero_intento
                <
                total_intentos - 1
            ):

                continue

            # ------------------------------------------------
            # Segundo fallo:
            # NO se interpreta como ausencia.
            # ------------------------------------------------

            return {
                "estado":
                    "ERROR_TECNICO",

                "intento":
                    None,

                "errores_tecnicos":
                    errores_tecnicos,
            }

        except Exception as error:
            """
            Cualquier excepción no prevista también
            es conservadoramente tratada como
            fallo técnico.

            Nunca como "fecha sin dato".
            """

            detalle = (
                f"{type(error).__name__}: "
                f"{repr(error)}"
            )

            errores_tecnicos.append(
                detalle
            )

            escribir()
            escribir(
                "[ERROR TÉCNICO NO CLASIFICADO]"
            )

            escribir(
                f"Fecha: "
                f"{fecha_a_texto(fecha_objetivo)}"
            )

            escribir(
                f"Detalle: "
                f"{detalle}"
            )

            if (
                numero_intento
                <
                total_intentos - 1
            ):

                continue

            return {
                "estado":
                    "ERROR_TECNICO",

                "intento":
                    None,

                "errores_tecnicos":
                    errores_tecnicos,
            }

    # No debería alcanzarse.
    return {
        "estado":
            "ERROR_TECNICO",

        "intento":
            None,

        "errores_tecnicos":
            errores_tecnicos,
    }


# ============================================================
# 28. DIAGNOSTICAR UN MES
# ============================================================

def diagnosticar_mes(
    navegador,
    anio,
    mes
):

    fecha_final = ultimo_dia_mes(
        anio,
        mes
    )

    clave_mes = (
        f"{anio:04d}-{mes:02d}"
    )

    titulo(
        f"MES: {clave_mes}"
    )

    escribir(
        f"Último día calendario: "
        f"{fecha_a_texto(fecha_final)}"
    )

    escribir()
    escribir(
        "Regla:"
    )

    escribir(
        "1. empezar en el último día calendario;"
    )

    escribir(
        "2. si no hay fecha válida, "
        "retroceder un día;"
    )

    escribir(
        "3. no salir del mismo mes;"
    )

    escribir(
        "4. si hay fallo técnico, "
        "permitir como máximo un reintento;"
    )

    escribir(
        "5. si el reintento técnico falla, "
        "detener el mes como ERROR_TECNICO."
    )

    fecha_intento = fecha_final

    dias_retrocedidos = 0

    dias_evaluados = 0

    while (
        fecha_intento.year == anio
        and
        fecha_intento.month == mes
    ):

        dias_evaluados += 1

        subtitulo(
            f"DÍA EVALUADO {dias_evaluados}: "
            f"{fecha_a_texto(fecha_intento)}"
        )

        evaluacion = (
            evaluar_dia_con_reintento(
                navegador,
                fecha_intento,
                dias_retrocedidos
            )
        )

        # ====================================================
        # ERROR TÉCNICO:
        # DETENER EL MES.
        # ====================================================

        if (
            evaluacion[
                "estado"
            ]
            == "ERROR_TECNICO"
        ):

            escribir()
            escribir(
                "CLASIFICACIÓN DEL MES = "
                "ERROR_TECNICO"
            )

            escribir(
                "El diagnóstico de este mes "
                "se detiene."
            )

            escribir(
                "NO se seguirá retrocediendo "
                "a días anteriores."
            )

            escribir(
                "Por tanto este mes NO puede "
                "clasificarse como MES_SIN_DATO."
            )

            escribir()
            escribir(
                "Errores técnicos registrados:"
            )

            for error in evaluacion[
                "errores_tecnicos"
            ]:

                escribir(
                    f"  - {error}"
                )

            return {
                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs_utilizada":
                    None,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "disponible":
                    "ERROR_TECNICO",

                "cantidad_bancos":
                    None,

                "encabezados":
                    [],

                "dias_evaluados":
                    dias_evaluados,

                "fecha_error_tecnico":
                    fecha_intento,

                "errores_tecnicos":
                    evaluacion[
                        "errores_tecnicos"
                    ],
            }

        intento = evaluacion[
            "intento"
        ]

        # ====================================================
        # FECHA VÁLIDA
        # ====================================================

        if intento[
            "valida"
        ]:

            escribir()
            escribir(
                "[OK] ÚLTIMA FECHA "
                "DISPONIBLE ENCONTRADA."
            )

            escribir(
                f"Fecha SBS utilizada: "
                f"{fecha_a_texto(fecha_intento)}"
            )

            escribir(
                f"Días retrocedidos: "
                f"{dias_retrocedidos}"
            )

            escribir(
                f"Cantidad de bancos: "
                f"{intento['cantidad_bancos']}"
            )

            escribir()
            escribir(
                "Encabezados bancarios:"
            )

            if intento[
                "encabezados"
            ]:

                escribir(
                    "  "
                    +
                    " | ".join(
                        intento[
                            "encabezados"
                        ]
                    )
                )

            else:

                escribir(
                    "  <NO DETECTADOS>"
                )

            return {
                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs_utilizada":
                    fecha_intento,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "disponible":
                    "DISPONIBLE",

                "cantidad_bancos":
                    intento[
                        "cantidad_bancos"
                    ],

                "encabezados":
                    intento[
                        "encabezados"
                    ],

                "dias_evaluados":
                    dias_evaluados,

                "fecha_error_tecnico":
                    None,

                "errores_tecnicos":
                    [],
            }

        # ====================================================
        # FECHA NO VÁLIDA, PERO SIN ERROR TÉCNICO.
        #
        # Aquí sí se permite retroceder:
        #
        # - SIN_INFORMACION;
        # - fecha no confirmada;
        # - tabla MN ausente;
        # - DataZone ausente;
        # - Consumo ausente/múltiple;
        # - estructura no válida.
        # ====================================================

        escribir()
        escribir(
            "[FECHA NO VÁLIDA]"
        )

        escribir(
            "La prueba técnica terminó "
            "correctamente, pero esta fecha "
            "no cumple todos los criterios."
        )

        escribir(
            "Se puede retroceder un día."
        )

        # ----------------------------------------------------
        # Si ya es día 1, terminar mes.
        # ----------------------------------------------------

        if fecha_intento.day == 1:

            break

        fecha_intento = (
            fecha_intento
            - timedelta(days=1)
        )

        dias_retrocedidos += 1

        time.sleep(
            PAUSA_ENTRE_INTENTOS
        )

    # ========================================================
    # SOLO SE LLEGA AQUÍ SI TODAS LAS FECHAS
    # DEL MES FUERON EVALUADAS TÉCNICAMENTE
    # SIN FALLAR Y NINGUNA FUE VÁLIDA.
    # ========================================================

    escribir()
    escribir(
        "CLASIFICACIÓN DEL MES = MES_SIN_DATO"
    )

    escribir()
    escribir(
        "Se llegó al día 1."
    )

    escribir(
        "Todas las fechas probadas pudieron "
        "ser evaluadas técnicamente."
    )

    escribir(
        "Ninguna cumplió simultáneamente:"
    )

    escribir(
        "  1. fecha del resultado confirmada;"
    )

    escribir(
        "  2. ausencia de mensaje "
        "'No existe información';"
    )

    escribir(
        "  3. tabla MN visible;"
    )

    escribir(
        "  4. DataZone visible;"
    )

    escribir(
        "  5. exactamente un Consumo."
    )

    return {
        "mes":
            clave_mes,

        "fecha_calendario_final":
            fecha_final,

        "fecha_sbs_utilizada":
            None,

        "dias_retrocedidos":
            (
                fecha_final.day - 1
            ),

        "disponible":
            "MES_SIN_DATO",

        "cantidad_bancos":
            0,

        "encabezados":
            [],

        "dias_evaluados":
            dias_evaluados,

        "fecha_error_tecnico":
            None,

        "errores_tecnicos":
            [],
    }


# ============================================================
# 29. RESUMEN FINAL
# ============================================================

def mostrar_resumen(
    resultados
):

    titulo(
        "RESUMEN - ÚLTIMA FECHA DISPONIBLE "
        "DE CONSUMO MN POR MES"
    )

    escribir(
        "mes | fecha_calendario_final | "
        "fecha_sbs_utilizada | dias_retrocedidos | "
        "disponible | cantidad_bancos"
    )

    for resultado in resultados:

        fecha_final = fecha_a_texto(
            resultado[
                "fecha_calendario_final"
            ]
        )

        if resultado[
            "fecha_sbs_utilizada"
        ] is None:

            fecha_sbs = (
                "<NINGUNA>"
            )

        else:

            fecha_sbs = fecha_a_texto(
                resultado[
                    "fecha_sbs_utilizada"
                ]
            )

        if resultado[
            "cantidad_bancos"
        ] is None:

            cantidad_bancos = (
                "NA"
            )

        else:

            cantidad_bancos = str(
                resultado[
                    "cantidad_bancos"
                ]
            )

        escribir(
            f"{resultado['mes']} | "
            f"{fecha_final} | "
            f"{fecha_sbs} | "
            f"{resultado['dias_retrocedidos']} | "
            f"{resultado['disponible']} | "
            f"{cantidad_bancos}"
        )

    # ========================================================
    # DETALLE POR MES
    # ========================================================

    subtitulo(
        "DETALLE FINAL POR MES"
    )

    for resultado in resultados:

        escribir()
        escribir(
            f"MES: {resultado['mes']}"
        )

        escribir(
            f"  Estado: "
            f"{resultado['disponible']}"
        )

        escribir(
            f"  Días evaluados: "
            f"{resultado['dias_evaluados']}"
        )

        if resultado[
            "fecha_sbs_utilizada"
        ] is not None:

            escribir(
                f"  Fecha SBS utilizada: "
                f"{fecha_a_texto(resultado['fecha_sbs_utilizada'])}"
            )

            escribir(
                f"  Bancos: "
                f"{resultado['cantidad_bancos']}"
            )

        if resultado[
            "disponible"
        ] == "ERROR_TECNICO":

            escribir(
                f"  Fecha donde ocurrió "
                f"el error técnico: "
                f"{fecha_a_texto(resultado['fecha_error_tecnico'])}"
            )

            escribir(
                "  Errores:"
            )

            for error in resultado[
                "errores_tecnicos"
            ]:

                escribir(
                    f"    - {error}"
                )

    # ========================================================
    # ENCABEZADOS
    # ========================================================

    subtitulo(
        "ENCABEZADOS DE LA FECHA VÁLIDA "
        "DE CADA MES"
    )

    for resultado in resultados:

        escribir()
        escribir(
            f"{resultado['mes']}:"
        )

        if resultado[
            "encabezados"
        ]:

            escribir(
                "  "
                +
                " | ".join(
                    resultado[
                        "encabezados"
                    ]
                )
            )

        elif resultado[
            "disponible"
        ] == "ERROR_TECNICO":

            escribir(
                "  <NO EVALUABLE POR ERROR TÉCNICO>"
            )

        else:

            escribir(
                "  <SIN ENCABEZADOS VÁLIDOS>"
            )

    # ========================================================
    # REGLA METODOLÓGICA
    # ========================================================

    subtitulo(
        "REGLA MENSUAL APLICADA"
    )

    escribir(
        "Para cada mes:"
    )

    escribir(
        "1. iniciar en el último día calendario;"
    )

    escribir(
        "2. recargar la URL base antes "
        "de cada intento;"
    )

    escribir(
        "3. establecer y validar la fecha "
        "visible e interna;"
    )

    escribir(
        "4. consultar SBS;"
    )

    escribir(
        "5. registrar por separado si SBS "
        "confirma 'al DD/MM/YYYY';"
    )

    escribir(
        "6. registrar por separado si SBS "
        "dice 'No existe información "
        "para la fecha elegida';"
    )

    escribir(
        "7. si ambas señales aparecen, "
        "la respuesta es SIN_INFORMACION, "
        "aunque periodo_confirmado=True;"
    )

    escribir(
        "8. aceptar una fecha solo si no existe "
        "el mensaje SIN_INFORMACION y además "
        "hay tabla MN visible, DataZone visible "
        "y exactamente un Consumo;"
    )

    escribir(
        "9. ante fecha no válida sin fallo "
        "técnico, retroceder un día;"
    )

    escribir(
        "10. ante fallo técnico, realizar "
        "como máximo un reintento;"
    )

    escribir(
        "11. si también falla el reintento, "
        "detener ese mes como ERROR_TECNICO;"
    )

    escribir(
        "12. MES_SIN_DATO solo puede declararse "
        "si se llegó al día 1 sin ningún "
        "fallo técnico no resuelto."
    )

    escribir()
    escribir(
        "No se extrajeron tasas."
    )

    escribir(
        "No se seleccionaron bancos finales."
    )

    escribir(
        "No se interpolaron datos."
    )

    escribir(
        "No se consultaron meses distintos "
        "de junio de 2015, 2016, 2017, "
        "2018 y 2019."
    )


# ============================================================
# 30. GUARDAR REPORTE
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


# ============================================================
# 31. MAIN
# ============================================================

def main():

    navegador = None

    resultados = []

    try:

        titulo(
            "DIAGNÓSTICO DE ÚLTIMA FECHA "
            "DISPONIBLE MENSUAL - CONSUMO MN"
        )

        escribir(
            "Meses incluidos:"
        )

        for anio, mes in MESES_CONTROL:

            escribir(
                f"  {anio:04d}-{mes:02d}"
            )

        escribir()
        escribir(
            "Cada intento diario volverá "
            "a cargar la URL base SBS."
        )

        escribir(
            "Los errores técnicos NO serán "
            "tratados como ausencia de datos."
        )

        escribir(
            "Cada fecha admite como máximo "
            "un reintento técnico controlado."
        )

        escribir()
        escribir(
            "NO se extraerán tasas."
        )

        escribir(
            "NO se seleccionarán bancos."
        )

        escribir(
            "NO se interpolarán datos."
        )

        escribir(
            "NO se consultarán otros meses."
        )

        navegador = crear_navegador()

        for anio, mes in MESES_CONTROL:

            resultado = diagnosticar_mes(
                navegador,
                anio,
                mes
            )

            resultados.append(
                resultado
            )

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

        escribir()
        escribir(
            "Este error general NO equivale "
            "a ausencia de datos SBS."
        )

    finally:

        guardar_reporte()

        if navegador is not None:

            try:

                navegador.quit()

            except Exception:

                pass

        print()
        print("=" * 122)
        print("DIAGNÓSTICO FINALIZADO")
        print("=" * 122)

        print()
        print(
            "Resultado guardado en:"
        )

        print(
            ARCHIVO_TXT
        )


# ============================================================
# 32. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()