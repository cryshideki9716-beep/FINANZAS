# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico de rango histórico SBS - Tasa activa Consumo MN por empresa bancaria

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
from selenium.common.exceptions import TimeoutException


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# ÚNICAMENTE ESTAS CUATRO FECHAS
FECHAS_CONTROL = [
    "31/12/2010",
    "31/12/2011",
    "30/06/2015",
    "30/06/2020",
]

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
    / "diagnostico_rango_historico_tasa_activa.txt"
)


# ============================================================
# 2. CONTROLES IDENTIFICADOS
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

# Tabla MN completa
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# DataZone MN
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
# 7. COMPROBAR PÁGINA SBS REAL
# ============================================================

def pagina_real_cargada(
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
            pagina_real_cargada(d)
        )

        escribir(
            "[OK] Página SBS real cargada."
        )

        return True

    except TimeoutException:

        escribir()
        escribir(
            "No se detectó todavía "
            "la aplicación SBS real."
        )

        escribir(
            "Si Chrome muestra una verificación, "
            "complétala manualmente."
        )

        escribir()

        input(
            "Cuando veas la página SBS real, "
            "presiona ENTER..."
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
# 13. LEER CONTROL
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
# 14. VALIDAR MN Y B
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
            f"se esperaba MN y se obtuvo "
            f"{moneda!r}."
        )

    if entidad != "B":

        raise RuntimeError(
            "CONFIGURACION_ENTIDAD_INVALIDA: "
            f"se esperaba B y se obtuvo "
            f"{entidad!r}."
        )


# ============================================================
# 15. ESTADO DE FECHA
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
# 16. MOSTRAR ESTADO DE FECHA
# ============================================================

def mostrar_estado_fecha(
    estado
):

    escribir(
        f"Fecha objetivo: "
        f"{estado['objetivo']}"
    )

    escribir(
        f"Fecha visible: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"Visible interpretada: "
        f"{estado['visible_fecha']}"
    )

    escribir(
        f"Fecha interna: "
        f"{estado['interna_texto']!r}"
    )

    escribir(
        f"Interna interpretada: "
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
            "No existe el control "
            "visible de fecha."
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

        escribir(
            "[OK] Fecha visible e interna "
            "correctas."
        )

        return estado

    escribir()
    escribir(
        "Aplicando API RadDatePicker..."
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

    mostrar_estado_fecha(
        estado
    )

    if not estado[
        "ambas_ok"
    ]:

        raise RuntimeError(
            "FECHA_PRECONSULTA_INVALIDA: "
            "visible e interna no coinciden "
            "exactamente con el objetivo."
        )

    escribir(
        "[OK] Fecha validada "
        "después de Telerik."
    )

    return estado


# ============================================================
# 20. BOTÓN CONSULTAR
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
# 21. BUSCAR FECHA COMO TEXTO DE RESULTADO
# ============================================================

def buscar_fecha_visible_resultado(
    navegador,
    fecha
):

    try:

        resultados = navegador.execute_script(
            """
            const fecha = arguments[0];

            const elementos = Array.from(
                document.querySelectorAll(
                    'span,label,td,th,p,strong,b,div'
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

                const texto =
                    (el.innerText || '')
                    .replace(/\\s+/g, ' ')
                    .trim();

                if (!texto) {
                    continue;
                }

                if (texto.length > 350) {
                    continue;
                }

                if (
                    texto.includes(fecha)
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
            """,
            fecha,
        )

        return resultados or []

    except Exception:

        return []


# ============================================================
# 22. TIME ORIGIN
# ============================================================

def obtener_time_origin(
    navegador
):

    try:

        return navegador.execute_script(
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

    except Exception:

        return None


# ============================================================
# 23. HASH DEL HTML
# ============================================================

def hash_html_navegador(
    navegador
):

    try:

        html = navegador.page_source

        return hashlib.sha256(
            html.encode(
                "utf-8",
                errors="replace"
            )
        ).hexdigest()

    except Exception:

        return None


# ============================================================
# 24. PULSAR CONSULTAR
# ============================================================

def pulsar_consultar(
    navegador,
    fecha
):

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se encontró "
            "el botón Consultar."
        )

    hash_antes = hash_html_navegador(
        navegador
    )

    time_origin_antes = (
        obtener_time_origin(
            navegador
        )
    )

    fechas_antes = (
        buscar_fecha_visible_resultado(
            navegador,
            fecha
        )
    )

    firmas_antes = {
        (
            item.get("tag"),
            item.get("id"),
            item.get("text"),
        )
        for item in fechas_antes
    }

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

    evidencia = None

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        # ----------------------------------------------------
        # Navegación / postback
        # ----------------------------------------------------

        time_origin_actual = (
            obtener_time_origin(
                navegador
            )
        )

        if (
            time_origin_antes is not None
            and
            time_origin_actual is not None
            and
            time_origin_actual
            != time_origin_antes
        ):

            evidencia = (
                "NAVEGACION_POSTBACK"
            )

            break

        # ----------------------------------------------------
        # Cambio de HTML
        # ----------------------------------------------------

        hash_actual = (
            hash_html_navegador(
                navegador
            )
        )

        if (
            hash_actual is not None
            and
            hash_actual != hash_antes
        ):

            evidencia = (
                "HTML_CAMBIO"
            )

            break

        # ----------------------------------------------------
        # Nueva fecha visible de resultado
        # ----------------------------------------------------

        fechas_actuales = (
            buscar_fecha_visible_resultado(
                navegador,
                fecha
            )
        )

        nuevas = [
            item
            for item in fechas_actuales
            if (
                item.get("tag"),
                item.get("id"),
                item.get("text"),
            )
            not in firmas_antes
        ]

        if nuevas:

            evidencia = (
                "FECHA_RESULTADO_VISIBLE"
            )

            break

        time.sleep(
            0.25
        )

    # Dar margen al DOM.
    time.sleep(
        2
    )

    try:

        esperar_documento(
            navegador,
            timeout=10
        )

    except Exception:

        pass

    return evidencia


# ============================================================
# 25. CONTAR CELDAS LÓGICAS DE UNA FILA
# ============================================================

def contar_columnas_logicas(
    fila
):
    """
    Cuenta columnas respetando colspan.
    No extrae tasas.
    """

    total = 0

    celdas = fila.find_all(
        ["th", "td"],
        recursive=False
    )

    if not celdas:

        celdas = fila.find_all(
            ["th", "td"]
        )

    for celda in celdas:

        try:

            colspan = int(
                celda.get(
                    "colspan",
                    1
                )
            )

        except Exception:

            colspan = 1

        total += colspan

    return total


# ============================================================
# 26. CELDAS ORIGINALES / LEAF
# ============================================================

def obtener_celdas_originales(
    tabla
):
    """
    Devuelve únicamente celdas reales sin
    tablas anidadas internas.

    Esto evita que una celda contenedora de
    DataZone sea confundida con la celda
    real donde aparece 'Consumo'.
    """

    resultado = []

    for numero_fila, fila in enumerate(
        tabla.find_all(
            "tr"
        )
    ):

        celdas = fila.find_all(
            ["th", "td"],
            recursive=False
        )

        for numero_celda, celda in enumerate(
            celdas
        ):

            # Si esta celda contiene otra tabla,
            # es contenedora y no se usa para
            # determinar el concepto original.
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

            resultado.append({
                "fila":
                    numero_fila,

                "celda":
                    numero_celda,

                "texto":
                    texto,

                "elemento":
                    celda,
            })

    return resultado


# ============================================================
# 27. BUSCAR CONSUMO EN TABLA EXTERNA
# ============================================================

def buscar_consumo_en_tabla_externa(
    tabla_externa
):
    """
    REGLA PRINCIPAL:

    Consumo se busca en la TABLA EXTERNA MN,
    no en la DataZone.

    Debe existir exactamente una celda
    original cuyo texto sea exactamente
    'Consumo'.
    """

    celdas = obtener_celdas_originales(
        tabla_externa
    )

    coincidencias = [
        {
            "fila":
                item["fila"],

            "celda":
                item["celda"],

            "texto":
                item["texto"],
        }
        for item in celdas
        if normalizar_texto(
            item["texto"]
        )
        == "consumo"
    ]

    return coincidencias


# ============================================================
# 28. BUSCAR CONSUMO EN DATAZONE SOLO COMO DIAGNÓSTICO
# ============================================================

def buscar_consumo_en_datazone(
    tabla_interna
):
    """
    Solo diagnóstico.

    La ausencia aquí NO significa
    que Consumo no exista en la tabla MN.
    """

    if tabla_interna is None:

        return []

    celdas = obtener_celdas_originales(
        tabla_interna
    )

    return [
        {
            "fila":
                item["fila"],

            "celda":
                item["celda"],

            "texto":
                item["texto"],
        }
        for item in celdas
        if normalizar_texto(
            item["texto"]
        )
        == "consumo"
    ]


# ============================================================
# 29. ANALIZAR DATAZONE
# ============================================================

def analizar_datazone(
    tabla_interna
):
    """
    La DataZone se usa únicamente para
    diagnosticar columnas/encabezados.

    NO se extraen tasas.
    NO se seleccionan bancos.
    """

    if tabla_interna is None:

        return {
            "filas":
                None,

            "max_columnas_logicas":
                None,

            "promedio_detectado":
                False,

            "promedio_cantidad":
                0,

            "bancos_estimados":
                None,

            "fila_mas_ancha":
                None,

            "textos_fila_mas_ancha":
                [],
        }

    filas = tabla_interna.find_all(
        "tr"
    )

    max_columnas = 0
    fila_mas_ancha = None
    textos_fila_mas_ancha = []

    for indice, fila in enumerate(
        filas
    ):

        columnas = (
            contar_columnas_logicas(
                fila
            )
        )

        if columnas > max_columnas:

            max_columnas = columnas

            fila_mas_ancha = (
                indice
            )

            celdas = fila.find_all(
                ["th", "td"],
                recursive=False
            )

            textos_fila_mas_ancha = [
                limpiar_texto(
                    celda.get_text(
                        " ",
                        strip=True
                    )
                )
                for celda in celdas
            ]

    # --------------------------------------------------------
    # Promedio exacto dentro de DataZone
    # --------------------------------------------------------

    celdas = obtener_celdas_originales(
        tabla_interna
    )

    promedio_cantidad = sum(
        1
        for item in celdas
        if normalizar_texto(
            item["texto"]
        )
        == "promedio"
    )

    promedio_detectado = (
        promedio_cantidad > 0
    )

    # --------------------------------------------------------
    # Estimación conservadora:
    #
    # si la DataZone contiene N columnas y
    # una corresponde a Promedio, estimamos
    # N - 1 columnas bancarias.
    #
    # No se leen tasas.
    # --------------------------------------------------------

    if max_columnas > 0:

        bancos_estimados = (
            max_columnas
            - 1
            if promedio_detectado
            else max_columnas
        )

        bancos_estimados = max(
            bancos_estimados,
            0
        )

    else:

        bancos_estimados = None

    return {
        "filas":
            len(filas),

        "max_columnas_logicas":
            max_columnas,

        "promedio_detectado":
            promedio_detectado,

        "promedio_cantidad":
            promedio_cantidad,

        "bancos_estimados":
            bancos_estimados,

        "fila_mas_ancha":
            fila_mas_ancha,

        "textos_fila_mas_ancha":
            textos_fila_mas_ancha,
    }


# ============================================================
# 30. ANALIZAR TABLAS POST
# ============================================================

def analizar_tablas_post(
    html
):
    """
    CORRECCIÓN METODOLÓGICA:

    1. Comprueba ambos IDs.
    2. Consumo se busca en la tabla EXTERNA MN.
    3. Si existe la externa, debe tener
       exactamente un Consumo original.
    4. DataZone solo se usa para columnas.
    5. Se registra explícitamente si concepto
       y datos están en zonas diferentes.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    todas_tablas = soup.find_all(
        "table"
    )

    ids_tablas = [
        tabla.get(
            "id"
        )
        for tabla in todas_tablas
    ]

    tabla_externa = soup.find(
        id=ID_TABLA_MN_EXTERNA
    )

    tabla_interna = soup.find(
        id=ID_TABLA_MN_INTERNA
    )

    existe_externa = (
        tabla_externa
        is not None
    )

    existe_interna = (
        tabla_interna
        is not None
    )

    # --------------------------------------------------------
    # CONSUMO: SIEMPRE desde tabla externa
    # --------------------------------------------------------

    if existe_externa:

        consumo_externo = (
            buscar_consumo_en_tabla_externa(
                tabla_externa
            )
        )

    else:

        consumo_externo = []

    consumo_externo_cantidad = len(
        consumo_externo
    )

    # --------------------------------------------------------
    # DataZone: Consumo solo como diagnóstico,
    # nunca como condición principal.
    # --------------------------------------------------------

    consumo_datazone = (
        buscar_consumo_en_datazone(
            tabla_interna
        )
    )

    consumo_datazone_cantidad = len(
        consumo_datazone
    )

    # --------------------------------------------------------
    # La existencia válida de Consumo MN
    # depende EXCLUSIVAMENTE de la tabla externa.
    # --------------------------------------------------------

    if existe_externa:

        consumo_externo_valido = (
            consumo_externo_cantidad
            == 1
        )

    else:

        consumo_externo_valido = False

    # --------------------------------------------------------
    # Zonas separadas
    # --------------------------------------------------------

    zonas_separadas = (
        existe_externa
        and
        existe_interna
        and
        consumo_externo_cantidad == 1
        and
        consumo_datazone_cantidad == 0
    )

    # --------------------------------------------------------
    # Diagnóstico de columnas en DataZone
    # --------------------------------------------------------

    datazone = analizar_datazone(
        tabla_interna
    )

    # --------------------------------------------------------
    # Estado estructural MN
    # --------------------------------------------------------

    problemas_estructura = []

    if not existe_externa:

        problemas_estructura.append(
            "TABLA_MN_EXTERNA_AUSENTE"
        )

    else:

        if consumo_externo_cantidad == 0:

            problemas_estructura.append(
                "CONSUMO_AUSENTE_EN_TABLA_MN_EXTERNA"
            )

        elif consumo_externo_cantidad > 1:

            problemas_estructura.append(
                "CONSUMO_MULTIPLE_EN_TABLA_MN_EXTERNA"
            )

    if existe_interna:

        if datazone[
            "max_columnas_logicas"
        ] == 0:

            problemas_estructura.append(
                "DATAZONE_SIN_COLUMNAS"
            )

    tabla_mn_utilizable = (
        existe_externa
        and
        consumo_externo_valido
    )

    return {
        "cantidad_tablas":
            len(
                todas_tablas
            ),

        "ids_tablas":
            ids_tablas,

        "existe_mn_externa":
            existe_externa,

        "existe_mn_interna":
            existe_interna,

        "consumo_externo_cantidad":
            consumo_externo_cantidad,

        "consumo_externo":
            consumo_externo,

        "consumo_externo_valido":
            consumo_externo_valido,

        "consumo_datazone_cantidad":
            consumo_datazone_cantidad,

        "consumo_datazone":
            consumo_datazone,

        "zonas_separadas":
            zonas_separadas,

        "tabla_mn_utilizable":
            tabla_mn_utilizable,

        "problemas_estructura":
            problemas_estructura,

        "datazone_filas":
            datazone[
                "filas"
            ],

        "datazone_columnas":
            datazone[
                "max_columnas_logicas"
            ],

        "promedio_detectado":
            datazone[
                "promedio_detectado"
            ],

        "promedio_cantidad":
            datazone[
                "promedio_cantidad"
            ],

        "bancos_estimados":
            datazone[
                "bancos_estimados"
            ],

        "datazone_fila_mas_ancha":
            datazone[
                "fila_mas_ancha"
            ],

        "datazone_textos_fila_mas_ancha":
            datazone[
                "textos_fila_mas_ancha"
            ],
    }


# ============================================================
# 31. FECHA DE RESULTADO PRESENTE
# ============================================================

def fecha_resultado_presente(
    navegador,
    fecha
):

    coincidencias = (
        buscar_fecha_visible_resultado(
            navegador,
            fecha
        )
    )

    return (
        len(
            coincidencias
        )
        > 0,
        coincidencias
    )


# ============================================================
# 32. RECARGAR URL BASE
# ============================================================

def recargar_base(
    navegador
):

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
            "la página SBS base."
        )


# ============================================================
# 33. DIAGNOSTICAR UNA FECHA
# ============================================================

def diagnosticar_fecha(
    navegador,
    fecha
):

    titulo(
        f"FECHA DE CONTROL: {fecha}"
    )

    resultado = {
        "fecha":
            fecha,

        "estado":
            "ERROR",

        "problema":
            None,
    }

    try:

        # ----------------------------------------------------
        # Siempre iniciar desde URL base.
        # --------------------------------------------------------

        escribir(
            "Recargando URL base..."
        )

        recargar_base(
            navegador
        )

        escribir(
            f"URL base cargada: "
            f"{navegador.current_url}"
        )

        # ----------------------------------------------------
        # MN y B PRE-POST
        # --------------------------------------------------------

        subtitulo(
            "CONFIGURACIÓN PRE-CONSULTA"
        )

        validar_mn_b(
            navegador
        )

        # ----------------------------------------------------
        # Fecha exacta
        # --------------------------------------------------------

        subtitulo(
            "VALIDACIÓN DE FECHA"
        )

        establecer_fecha(
            navegador,
            fecha
        )

        estado_pre = obtener_estado_fecha(
            navegador,
            fecha
        )

        if not estado_pre[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "Fecha visible e interna "
                "no validadas."
            )

        # Confirmación final de MN y B.
        validar_mn_b(
            navegador
        )

        escribir(
            "[OK] Configuración "
            "pre-consulta correcta."
        )

        # ----------------------------------------------------
        # POST
        # --------------------------------------------------------

        subtitulo(
            "CONSULTAR"
        )

        evidencia = pulsar_consultar(
            navegador,
            fecha
        )

        escribir(
            f"Evidencia de respuesta: "
            f"{evidencia!r}"
        )

        # ----------------------------------------------------
        # Analizar respuesta
        # --------------------------------------------------------

        html = navegador.page_source

        hash_resultado = hashlib.sha256(
            html.encode(
                "utf-8",
                errors="replace"
            )
        ).hexdigest()

        (
            fecha_visible_resultado,
            coincidencias_fecha
        ) = fecha_resultado_presente(
            navegador,
            fecha
        )

        escribir(
            f"¿SBS muestra la fecha solicitada "
            f"como texto visible?: "
            f"{fecha_visible_resultado}"
        )

        escribir(
            f"Coincidencias visibles de fecha: "
            f"{len(coincidencias_fecha)}"
        )

        analisis = analizar_tablas_post(
            html
        )

        # ----------------------------------------------------
        # ESTRUCTURA
        # --------------------------------------------------------

        subtitulo(
            "ESTRUCTURA POST-CONSULTA"
        )

        escribir(
            f"URL final: "
            f"{navegador.current_url}"
        )

        escribir(
            f"Título final: "
            f"{navegador.title!r}"
        )

        escribir(
            f"SHA256 HTML: "
            f"{hash_resultado}"
        )

        escribir(
            f"Cantidad total de tablas: "
            f"{analisis['cantidad_tablas']}"
        )

        escribir()
        escribir(
            "TABLA MN EXTERNA:"
        )

        escribir(
            f"  ID: "
            f"{ID_TABLA_MN_EXTERNA}"
        )

        escribir(
            f"  Existe: "
            f"{analisis['existe_mn_externa']}"
        )

        escribir(
            f"  Celdas originales exactas "
            f"'Consumo': "
            f"{analisis['consumo_externo_cantidad']}"
        )

        escribir(
            f"  Consumo válido "
            f"(exactamente uno): "
            f"{analisis['consumo_externo_valido']}"
        )

        escribir(
            f"  Coincidencias: "
            f"{analisis['consumo_externo']}"
        )

        escribir()
        escribir(
            "DATAZONE MN:"
        )

        escribir(
            f"  ID: "
            f"{ID_TABLA_MN_INTERNA}"
        )

        escribir(
            f"  Existe: "
            f"{analisis['existe_mn_interna']}"
        )

        escribir(
            f"  'Consumo' dentro de DataZone "
            f"(solo diagnóstico): "
            f"{analisis['consumo_datazone_cantidad']}"
        )

        escribir(
            f"  Filas DataZone: "
            f"{analisis['datazone_filas']}"
        )

        escribir(
            f"  Máximo de columnas lógicas "
            f"DataZone: "
            f"{analisis['datazone_columnas']}"
        )

        escribir(
            f"  Promedio detectado: "
            f"{analisis['promedio_detectado']}"
        )

        escribir(
            f"  Cantidad de celdas "
            f"Promedio: "
            f"{analisis['promedio_cantidad']}"
        )

        escribir(
            f"  Bancos/columnas bancarias "
            f"estimadas: "
            f"{analisis['bancos_estimados']}"
        )

        escribir(
            f"  Fila más ancha DataZone: "
            f"{analisis['datazone_fila_mas_ancha']}"
        )

        escribir(
            "  Encabezados/textos de la "
            "fila más ancha:"
        )

        for texto in analisis[
            "datazone_textos_fila_mas_ancha"
        ]:

            escribir(
                f"    {texto!r}"
            )

        escribir()
        escribir(
            "RELACIÓN ENTRE ZONAS:"
        )

        escribir(
            f"  ¿Concepto y datos parecen "
            f"estar en zonas separadas?: "
            f"{analisis['zonas_separadas']}"
        )

        if analisis[
            "zonas_separadas"
        ]:

            escribir(
                "  [OK] Consumo está en la "
                "tabla MN completa aunque no "
                "aparezca en la DataZone."
            )

            escribir(
                "  La ausencia de Consumo en "
                "DataZone NO se considera "
                "falta de la categoría."
            )

        escribir()
        escribir(
            f"Tabla MN utilizable "
            f"estructuralmente: "
            f"{analisis['tabla_mn_utilizable']}"
        )

        escribir(
            f"Problemas estructurales: "
            f"{analisis['problemas_estructura']}"
        )

        # ----------------------------------------------------
        # IDs
        # --------------------------------------------------------

        escribir()
        escribir(
            "IDs DE TODAS LAS TABLAS:"
        )

        for identificador in analisis[
            "ids_tablas"
        ]:

            escribir(
                f"  {identificador!r}"
            )

        # ----------------------------------------------------
        # CONTROLES POST
        # --------------------------------------------------------

        subtitulo(
            "CONTROLES POST-CONSULTA"
        )

        visible_post = (
            leer_fecha_visible(
                navegador
            )
        )

        interna_post = (
            leer_fecha_interna(
                navegador
            )
        )

        moneda_post = leer_control(
            navegador,
            NAME_MONEDA,
            ID_MONEDA
        )

        entidad_post = leer_control(
            navegador,
            NAME_ENTIDAD,
            ID_ENTIDAD
        )

        escribir(
            f"Fecha visible post: "
            f"{visible_post!r}"
        )

        escribir(
            f"Fecha interna post: "
            f"{interna_post!r}"
        )

        escribir(
            f"hdTipoMoneda post: "
            f"{moneda_post!r}"
        )

        escribir(
            f"hdTipoEntidad post: "
            f"{entidad_post!r}"
        )

        # ----------------------------------------------------
        # RESULTADO
        # --------------------------------------------------------

        resultado.update({
            "estado":
                "OK",

            "problema":
                None,

            "evidencia":
                evidencia,

            "fecha_resultado_visible":
                fecha_visible_resultado,

            "cantidad_tablas":
                analisis[
                    "cantidad_tablas"
                ],

            "existe_mn_externa":
                analisis[
                    "existe_mn_externa"
                ],

            "existe_mn_interna":
                analisis[
                    "existe_mn_interna"
                ],

            "consumo_mn_externa":
                analisis[
                    "consumo_externo_cantidad"
                ],

            "consumo_mn_valido":
                analisis[
                    "consumo_externo_valido"
                ],

            "consumo_datazone":
                analisis[
                    "consumo_datazone_cantidad"
                ],

            "zonas_separadas":
                analisis[
                    "zonas_separadas"
                ],

            "tabla_mn_utilizable":
                analisis[
                    "tabla_mn_utilizable"
                ],

            "columnas_datazone":
                analisis[
                    "datazone_columnas"
                ],

            "promedio":
                analisis[
                    "promedio_detectado"
                ],

            "bancos_estimados":
                analisis[
                    "bancos_estimados"
                ],

            "problemas_estructura":
                analisis[
                    "problemas_estructura"
                ],

            "moneda_post":
                moneda_post,

            "entidad_post":
                entidad_post,
        })

    except Exception as error:

        escribir()
        escribir(
            "[ERROR EN ESTA FECHA]"
        )

        escribir(
            f"{type(error).__name__}: "
            f"{repr(error)}"
        )

        escribir(
            "Se continuará con "
            "la siguiente fecha."
        )

        resultado.update({
            "estado":
                "ERROR",

            "problema":
                (
                    f"{type(error).__name__}: "
                    f"{repr(error)}"
                ),
        })

    return resultado


# ============================================================
# 34. RESUMEN FINAL
# ============================================================

def mostrar_resumen(
    resultados
):

    titulo(
        "RESUMEN COMPARATIVO DEL RANGO HISTÓRICO"
    )

    for resultado in resultados:

        escribir()
        escribir(
            f"FECHA: "
            f"{resultado['fecha']}"
        )

        escribir(
            f"  Estado: "
            f"{resultado['estado']}"
        )

        if resultado[
            "estado"
        ] != "OK":

            escribir(
                f"  Problema: "
                f"{resultado['problema']}"
            )

            continue

        escribir(
            f"  SBS mostró fecha solicitada: "
            f"{resultado['fecha_resultado_visible']}"
        )

        escribir(
            f"  Tabla MN externa: "
            f"{resultado['existe_mn_externa']}"
        )

        escribir(
            f"  Tabla MN interna/DataZone: "
            f"{resultado['existe_mn_interna']}"
        )

        escribir(
            f"  Consumo exacto en tabla MN externa: "
            f"{resultado['consumo_mn_externa']}"
        )

        escribir(
            f"  Consumo externo válido: "
            f"{resultado['consumo_mn_valido']}"
        )

        escribir(
            f"  Consumo dentro de DataZone "
            f"(solo diagnóstico): "
            f"{resultado['consumo_datazone']}"
        )

        escribir(
            f"  Zonas separadas: "
            f"{resultado['zonas_separadas']}"
        )

        escribir(
            f"  Tabla MN utilizable: "
            f"{resultado['tabla_mn_utilizable']}"
        )

        escribir(
            f"  Columnas DataZone: "
            f"{resultado['columnas_datazone']}"
        )

        escribir(
            f"  Promedio detectado: "
            f"{resultado['promedio']}"
        )

        escribir(
            f"  Bancos estimados: "
            f"{resultado['bancos_estimados']}"
        )

        escribir(
            f"  Problemas estructurales: "
            f"{resultado['problemas_estructura']}"
        )

    # ========================================================
    # TABLA COMPACTA
    # ========================================================

    subtitulo(
        "TABLA COMPACTA"
    )

    escribir(
        "fecha | estado | fecha_sbs | "
        "mn_externa | mn_datazone | "
        "consumo_externa | consumo_datazone | "
        "zonas_separadas | utilizable | "
        "columnas_datazone | bancos_estimados"
    )

    for resultado in resultados:

        if resultado[
            "estado"
        ] == "OK":

            escribir(
                f"{resultado['fecha']} | "
                f"OK | "
                f"{resultado['fecha_resultado_visible']} | "
                f"{resultado['existe_mn_externa']} | "
                f"{resultado['existe_mn_interna']} | "
                f"{resultado['consumo_mn_externa']} | "
                f"{resultado['consumo_datazone']} | "
                f"{resultado['zonas_separadas']} | "
                f"{resultado['tabla_mn_utilizable']} | "
                f"{resultado['columnas_datazone']} | "
                f"{resultado['bancos_estimados']}"
            )

        else:

            escribir(
                f"{resultado['fecha']} | "
                f"ERROR | "
                f"NA | NA | NA | NA | NA | "
                f"NA | NA | NA | NA"
            )


# ============================================================
# 35. GUARDAR TXT
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
# 36. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    resultados = []

    try:

        titulo(
            "DIAGNÓSTICO DE RANGO HISTÓRICO "
            "SBS - TASA ACTIVA CONSUMO MN"
        )

        escribir(
            "Se consultarán únicamente "
            "estas cuatro fechas:"
        )

        for fecha in FECHAS_CONTROL:

            escribir(
                f"  {fecha}"
            )

        escribir()
        escribir(
            "Antes de CADA fecha se volverá "
            "a cargar la URL base."
        )

        escribir(
            "Consumo se buscará únicamente "
            "en la TABLA EXTERNA MN completa."
        )

        escribir(
            "La DataZone se utilizará únicamente "
            "para diagnosticar columnas."
        )

        escribir()
        escribir(
            "NO se extraerán tasas."
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

        for fecha in FECHAS_CONTROL:

            resultado = diagnosticar_fecha(
                navegador,
                fecha
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

    finally:

        guardar_reporte()

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
        print(
            "Resultado guardado en:"
        )

        print(
            ARCHIVO_TXT
        )


# ============================================================
# 37. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()