# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico estructural histórico SBS - Tasa activa - 31/12/2025

from pathlib import Path
from datetime import datetime
import base64
import hashlib
import re
import time

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# SOLO ESTA FECHA
FECHA_OBJETIVO = "31/12/2025"

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
    / "diagnostico_historico_tasa_activa_2025.txt"
)

ARCHIVO_HTML = (
    CARPETA_SALIDA
    / "tasa_activa_2025_renderizada.html"
)

ARCHIVO_PNG = (
    CARPETA_SALIDA
    / "tasa_activa_2025_pagina.png"
)


# ============================================================
# 2. CONTROLES IDENTIFICADOS EN LA PÁGINA INICIAL
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
# 4. LIMPIEZA DE TEXTO
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

    return limpiar_texto(
        valor
    ).lower()


# ============================================================
# 5. CREAR CHROME
# ============================================================

def crear_navegador():

    opciones = webdriver.ChromeOptions()

    # Chrome visible
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
# 7. COMPROBAR APLICACIÓN SBS REAL
# ============================================================

def pagina_sbs_real(
    navegador
):

    try:

        cuerpo = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text.lower()

    except Exception:

        return False

    return (
        "consumo" in cuerpo
        or
        "moneda nacional" in cuerpo
    )


# ============================================================
# 8. VERIFICACIÓN MANUAL INICIAL
# ============================================================

def asegurar_pagina_real(
    navegador
):

    escribir()
    escribir(
        "Esperando aplicación SBS..."
    )

    try:

        WebDriverWait(
            navegador,
            15
        ).until(
            lambda d:
            pagina_sbs_real(d)
        )

        escribir(
            "[OK] SBS cargó sin "
            "intervención manual."
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
            "NO cierres Chrome."
        )

        escribir()

        input(
            "Cuando aparezca la página SBS real, "
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
            "[OK] Aplicación SBS real detectada."
        )

        return True

    except TimeoutException:

        return False


# ============================================================
# 9. CONVERTIR TEXTO A FECHA
# ============================================================

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
# 11. LEER FECHA VISIBLE SIN FALLAR
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
# 12. LEER FECHA INTERNA SIN FALLAR
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
# 13. LEER CONTROL SIN FALLAR
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
# 14. ESTADO DE FECHA
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
            visible_fecha
            == objetivo,

        "interna_ok":
            interna_fecha
            == objetivo,

        "ambas_ok":
            (
                visible_fecha
                == objetivo
                and
                interna_fecha
                == objetivo
            ),
    }


# ============================================================
# 15. MOSTRAR ESTADO DE FECHA
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
# 16. CAMBIAR FECHA CON TECLADO
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
            "No existe el input visible "
            "de fecha antes de consultar."
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
# 17. CAMBIAR FECHA CON API TELERIK
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
# 18. ESTABLECER FECHA ESTRICTAMENTE
# ============================================================

def establecer_fecha(
    navegador,
    fecha
):

    subtitulo(
        "ESTABLECER FECHA PRE-CONSULTA"
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
            "[OK] Visible e interna "
            "coinciden exactamente."
        )

        return estado

    escribir()
    escribir(
        "No coinciden ambas."
    )

    escribir(
        "Usando API RadDatePicker..."
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
            "exactamente a 31/12/2025. "
            "No se pulsará Consultar."
        )

    escribir()
    escribir(
        "[OK] Fecha pre-consulta "
        "validada estrictamente."
    )

    return estado


# ============================================================
# 19. LOCALIZAR BOTÓN
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
# 20. BUSCAR FECHA EN TEXTO VISIBLE
# ============================================================

def obtener_textos_visibles_fecha(
    navegador,
    fecha
):
    """
    Busca la fecha como TEXTO VISIBLE real.

    No usa inputs, por lo que el DatePicker
    no cuenta como resultado.
    """

    try:

        resultados = navegador.execute_script(
            """
            const fecha = arguments[0];

            const selector = [
                'span',
                'label',
                'td',
                'th',
                'p',
                'strong',
                'b',
                'div'
            ].join(',');

            const elementos =
                Array.from(
                    document.querySelectorAll(
                        selector
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
                    rect.width === 0
                    &&
                    rect.height === 0
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
                    texto.length > 300
                ) {
                    continue;
                }

                if (
                    !texto.includes(fecha)
                ) {
                    continue;
                }

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
            """,
            fecha,
        )

        return resultados or []

    except Exception:

        return []


# ============================================================
# 21. FIRMA DE COINCIDENCIA
# ============================================================

def firma_coincidencia(
    item
):

    return (
        f"{item.get('tag', '')}|"
        f"{item.get('id', '')}|"
        f"{item.get('className', '')}|"
        f"{item.get('text', '')}"
    )


# ============================================================
# 22. PULSAR CONSULTAR
# ============================================================

def consultar_2025(
    navegador
):
    """
    No espera ningún ID específico de tabla.

    Detecta la nueva aparición visible de
    31/12/2025 después de pulsar Consultar.

    Si no aparece en el timeout, el diagnóstico
    continúa con el estado actual de Chrome.
    """

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se encontró "
            "el botón Consultar."
        )

    coincidencias_antes = (
        obtener_textos_visibles_fecha(
            navegador,
            FECHA_OBJETIVO
        )
    )

    firmas_antes = {
        firma_coincidencia(
            item
        )
        for item
        in coincidencias_antes
    }

    escribir()
    escribir(
        "Coincidencias visibles con "
        "31/12/2025 ANTES del click:"
    )

    if coincidencias_antes:

        for item in coincidencias_antes:

            escribir(
                f"  {item}"
            )

    else:

        escribir(
            "  <NINGUNA>"
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

    escribir()
    escribir(
        "Pulsando Consultar..."
    )

    boton.click()

    inicio = time.time()

    nueva_coincidencia = None
    todas_despues = []

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        todas_despues = (
            obtener_textos_visibles_fecha(
                navegador,
                FECHA_OBJETIVO
            )
        )

        nuevas = [
            item
            for item
            in todas_despues
            if firma_coincidencia(
                item
            )
            not in firmas_antes
        ]

        if nuevas:

            nueva_coincidencia = (
                nuevas[0]
            )

            break

        time.sleep(
            0.25
        )

    escribir()

    if nueva_coincidencia:

        escribir(
            "[OK] Se detectó una NUEVA "
            "fecha visible de resultado:"
        )

        escribir(
            f"  {nueva_coincidencia}"
        )

        escribir()
        escribir(
            "No se esperará ningún "
            "ID específico de tabla."
        )

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

        return {
            "fecha_resultado_detectada":
                True,

            "coincidencia":
                nueva_coincidencia,

            "coincidencias_despues":
                todas_despues,
        }

    escribir(
        "[ADVERTENCIA] No se detectó "
        "una nueva coincidencia visible "
        "antes del timeout."
    )

    escribir(
        "El diagnóstico continuará "
        "con la página actual."
    )

    return {
        "fecha_resultado_detectada":
            False,

        "coincidencia":
            None,

        "coincidencias_despues":
            todas_despues,
    }


# ============================================================
# 23. OBTENER TEXTO VISIBLE COMPLETO
# ============================================================

def obtener_texto_visible(
    navegador
):

    try:

        cuerpo = navegador.find_element(
            By.TAG_NAME,
            "body"
        )

        return cuerpo.text

    except Exception:

        return ""


# ============================================================
# 24. DIAGNOSTICAR CONTROLES POST
# ============================================================

def diagnosticar_controles_post(
    navegador
):

    subtitulo(
        "CONTROLES DESPUÉS DE LA CONSULTA"
    )

    fecha_visible = (
        leer_fecha_visible(
            navegador
        )
    )

    fecha_interna = (
        leer_fecha_interna(
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

    escribir(
        f"Fecha visible: "
        f"{fecha_visible!r}"
    )

    escribir(
        f"Fecha interna: "
        f"{fecha_interna!r}"
    )

    escribir(
        f"hdTipoMoneda: "
        f"{moneda!r}"
    )

    escribir(
        f"hdTipoEntidad: "
        f"{entidad!r}"
    )

    escribir(
        f"Fecha visible interpretada: "
        f"{convertir_fecha(fecha_visible)}"
    )

    escribir(
        f"Fecha interna interpretada: "
        f"{convertir_fecha(fecha_interna)}"
    )


# ============================================================
# 25. PRIMERAS FILAS DE UNA TABLA
# ============================================================

def obtener_filas_tabla(
    tabla,
    limite_filas=10,
    limite_celdas=35
):

    salida = []

    filas = tabla.find_all(
        "tr"
    )

    for indice_fila, fila in enumerate(
        filas[:limite_filas]
    ):

        celdas = fila.find_all(
            ["th", "td"]
        )

        textos = []

        for celda in celdas[
            :limite_celdas
        ]:

            textos.append(
                limpiar_texto(
                    celda.get_text(
                        " ",
                        strip=True
                    )
                )
            )

        salida.append({
            "fila":
                indice_fila,

            "celdas":
                textos,
        })

    return salida


# ============================================================
# 26. TABLA CANDIDATA
# ============================================================

def tabla_es_candidata(
    tabla
):

    identificador = normalizar_texto(
        tabla.get(
            "id",
            ""
        )
    )

    texto = normalizar_texto(
        tabla.get_text(
            " ",
            strip=True
        )
    )

    palabras = [
        "consumo",
        "moneda nacional",
        "moneda extranjera",
        "tasa",
        "credito",
        "crédito",
        "efectiva",
        "promedio",
        "banco",
        "empresa",
    ]

    if any(
        palabra in texto
        for palabra in palabras
    ):

        return True

    if any(
        fragmento in identificador
        for fragmento in [
            "rpg",
            "grid",
            "actual",
            "mn",
            "me",
        ]
    ):

        return True

    return False


# ============================================================
# 27. DIAGNOSTICAR TODAS LAS TABLAS
# ============================================================

def diagnosticar_tablas(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tablas = soup.find_all(
        "table"
    )

    subtitulo(
        "TODAS LAS TABLAS EXISTENTES"
    )

    escribir(
        f"Cantidad total de tablas: "
        f"{len(tablas)}"
    )

    ids = []

    for indice, tabla in enumerate(
        tablas,
        start=1
    ):

        identificador = tabla.get(
            "id"
        )

        clases = tabla.get(
            "class"
        )

        filas = tabla.find_all(
            "tr"
        )

        ids.append(
            identificador
        )

        escribir(
            f"Tabla #{indice}: "
            f"id={identificador!r} | "
            f"class={clases!r} | "
            f"filas={len(filas)}"
        )

    escribir()
    escribir(
        "LISTA DE IDs DE TABLAS:"
    )

    for indice, identificador in enumerate(
        ids,
        start=1
    ):

        escribir(
            f"  {indice}. "
            f"{identificador!r}"
        )

    subtitulo(
        "TABLAS CANDIDATAS"
    )

    candidatas = []

    for indice, tabla in enumerate(
        tablas,
        start=1
    ):

        if not tabla_es_candidata(
            tabla
        ):

            continue

        candidatas.append(
            (
                indice,
                tabla
            )
        )

    escribir(
        f"Cantidad de tablas candidatas: "
        f"{len(candidatas)}"
    )

    for indice_original, tabla in candidatas:

        identificador = tabla.get(
            "id"
        )

        clases = tabla.get(
            "class"
        )

        texto = limpiar_texto(
            tabla.get_text(
                " ",
                strip=True
            )
        )

        escribir()
        escribir(
            "=" * 100
        )

        escribir(
            f"TABLA CANDIDATA "
            f"#{indice_original}"
        )

        escribir(
            f"id={identificador!r}"
        )

        escribir(
            f"class={clases!r}"
        )

        escribir(
            f"Longitud texto="
            f"{len(texto)}"
        )

        encabezados = [
            limpiar_texto(
                th.get_text(
                    " ",
                    strip=True
                )
            )
            for th in tabla.find_all(
                "th"
            )
        ]

        escribir(
            f"Encabezados <th>: "
            f"{encabezados}"
        )

        filas = obtener_filas_tabla(
            tabla
        )

        escribir(
            "Primeras filas:"
        )

        for fila in filas:

            escribir(
                f"  Fila "
                f"{fila['fila']}: "
                f"{fila['celdas']}"
            )

        escribir(
            "Primeros 1500 caracteres "
            "del texto:"
        )

        escribir(
            texto[:1500]
        )


# ============================================================
# 28. DIAGNOSTICAR CONSUMO
# ============================================================

def diagnosticar_consumo(
    html,
    texto_visible
):

    subtitulo(
        "PRESENCIA DE CONSUMO"
    )

    aparece_visible = (
        "consumo"
        in texto_visible.lower()
    )

    aparece_html = (
        "consumo"
        in html.lower()
    )

    escribir(
        f"'Consumo' en texto visible: "
        f"{aparece_visible}"
    )

    escribir(
        f"'Consumo' en HTML: "
        f"{aparece_html}"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    coincidencias = []

    for fila in soup.find_all(
        "tr"
    ):

        texto = limpiar_texto(
            fila.get_text(
                " ",
                strip=True
            )
        )

        if (
            "consumo"
            in texto.lower()
        ):

            coincidencias.append(
                texto
            )

    escribir(
        f"Filas <tr> con 'Consumo': "
        f"{len(coincidencias)}"
    )

    for indice, texto in enumerate(
        coincidencias,
        start=1
    ):

        escribir()
        escribir(
            f"Coincidencia #{indice}:"
        )

        escribir(
            texto[:2500]
        )


# ============================================================
# 29. INFORMACIÓN GENERAL POST-CONSULTA
# ============================================================

def diagnosticar_pagina(
    navegador,
    html,
    texto_visible
):

    titulo(
        "ESTADO DE LA PÁGINA HISTÓRICA "
        "DESPUÉS DE CONSULTAR"
    )

    escribir(
        f"URL final: "
        f"{navegador.current_url}"
    )

    escribir(
        f"Título: "
        f"{navegador.title!r}"
    )

    escribir(
        f"Longitud HTML renderizado: "
        f"{len(html)}"
    )

    hash_html = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    escribir(
        f"SHA256 HTML: "
        f"{hash_html}"
    )

    escribir(
        f"Longitud texto visible: "
        f"{len(texto_visible)}"
    )

    subtitulo(
        "TEXTO VISIBLE DE LA PÁGINA"
    )

    if texto_visible:

        escribir(
            texto_visible
        )

    else:

        escribir(
            "<SIN TEXTO VISIBLE>"
        )


# ============================================================
# 30. SCREENSHOT PNG
# ============================================================

def guardar_screenshot_completo(
    navegador
):

    CARPETA_SALIDA.mkdir(
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

        ARCHIVO_PNG.write_bytes(
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
                    ARCHIVO_PNG
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
# 31. GUARDAR HTML
# ============================================================

def guardar_html(
    html
):

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    ARCHIVO_HTML.write_text(
        html,
        encoding="utf-8"
    )


# ============================================================
# 32. GUARDAR TXT
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
# 33. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None
    html_final = ""

    try:

        titulo(
            "DIAGNÓSTICO HISTÓRICO SBS "
            "- 31/12/2025"
        )

        escribir(
            "Se consultará únicamente:"
        )

        escribir(
            f"  {FECHA_OBJETIVO}"
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
            "NO se elegirán bancos."
        )

        escribir(
            "NO se realizará interpolación."
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
                "No se pudo confirmar "
                "la aplicación SBS real."
            )

        # ====================================================
        # ESTADO INICIAL
        # ====================================================

        titulo(
            "ESTADO INICIAL"
        )

        escribir(
            f"URL inicial: "
            f"{navegador.current_url}"
        )

        escribir(
            f"Título inicial: "
            f"{navegador.title!r}"
        )

        moneda_inicial = leer_control(
            navegador,
            NAME_MONEDA,
            ID_MONEDA
        )

        entidad_inicial = leer_control(
            navegador,
            NAME_ENTIDAD,
            ID_ENTIDAD
        )

        escribir(
            f"hdTipoMoneda inicial: "
            f"{moneda_inicial!r}"
        )

        escribir(
            f"hdTipoEntidad inicial: "
            f"{entidad_inicial!r}"
        )

        escribir(
            f"Fecha visible inicial: "
            f"{leer_fecha_visible(navegador)!r}"
        )

        escribir(
            f"Fecha interna inicial: "
            f"{leer_fecha_interna(navegador)!r}"
        )

        # ====================================================
        # ESTABLECER FECHA
        # ====================================================

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

        titulo(
            "VALIDACIÓN FINAL PRE-CONSULTA"
        )

        mostrar_estado_fecha(
            estado_final_pre
        )

        if not estado_final_pre[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "La fecha pre-consulta "
                "no es exactamente 31/12/2025."
            )

        escribir()
        escribir(
            "[OK] Se permite pulsar Consultar."
        )

        # ====================================================
        # CONSULTA
        # ====================================================

        titulo(
            "RESPUESTA A LA CONSULTA 31/12/2025"
        )

        resultado_espera = (
            consultar_2025(
                navegador
            )
        )

        escribir()
        escribir(
            "Fecha de resultado detectada: "
            f"{resultado_espera['fecha_resultado_detectada']}"
        )

        if resultado_espera[
            "coincidencia"
        ]:

            escribir(
                "Coincidencia utilizada:"
            )

            escribir(
                str(
                    resultado_espera[
                        "coincidencia"
                    ]
                )
            )

        # ====================================================
        # NO DEPENDEMOS DE ID ESPECÍFICO DE TABLA
        # ====================================================

        html_final = (
            navegador.page_source
        )

        texto_visible = (
            obtener_texto_visible(
                navegador
            )
        )

        diagnosticar_pagina(
            navegador,
            html_final,
            texto_visible
        )

        diagnosticar_controles_post(
            navegador
        )

        diagnosticar_consumo(
            html_final,
            texto_visible
        )

        diagnosticar_tablas(
            html_final
        )

        # ====================================================
        # GUARDAR HTML
        # ====================================================

        subtitulo(
            "ARCHIVO HTML"
        )

        guardar_html(
            html_final
        )

        escribir(
            "HTML guardado en:"
        )

        escribir(
            str(
                ARCHIVO_HTML
            )
        )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        subtitulo(
            "SCREENSHOT"
        )

        screenshot_ok, metodo = (
            guardar_screenshot_completo(
                navegador
            )
        )

        escribir(
            f"Screenshot guardado: "
            f"{screenshot_ok}"
        )

        escribir(
            f"Método: "
            f"{metodo}"
        )

        escribir(
            "Ruta PNG:"
        )

        escribir(
            str(
                ARCHIVO_PNG
            )
        )

        # ====================================================
        # RESUMEN
        # ====================================================

        titulo(
            "RESUMEN DEL DIAGNÓSTICO"
        )

        escribir(
            f"Fecha consultada: "
            f"{FECHA_OBJETIVO}"
        )

        escribir(
            f"Fecha visible de resultado "
            f"detectada: "
            f"{resultado_espera['fecha_resultado_detectada']}"
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
            f"Fecha visible post: "
            f"{leer_fecha_visible(navegador)!r}"
        )

        escribir(
            f"Fecha interna post: "
            f"{leer_fecha_interna(navegador)!r}"
        )

        escribir(
            f"hdTipoMoneda post: "
            f"{leer_control(navegador, NAME_MONEDA, ID_MONEDA)!r}"
        )

        escribir(
            f"hdTipoEntidad post: "
            f"{leer_control(navegador, NAME_ENTIDAD, ID_ENTIDAD)!r}"
        )

        escribir(
            f"'Consumo' visible: "
            f"{'consumo' in texto_visible.lower()}"
        )

        escribir(
            f"'Consumo' en HTML: "
            f"{'consumo' in html_final.lower()}"
        )

        escribir()
        escribir(
            "El diagnóstico NO intentó "
            "extraer tasas bancarias."
        )

        escribir(
            "El diagnóstico NO exigió "
            "ningún ID específico de tabla."
        )

    except Exception as error:

        titulo(
            "ERROR / ESTADO INESPERADO"
        )

        escribir(
            f"Tipo: "
            f"{type(error).__name__}"
        )

        escribir(
            f"Detalle: "
            f"{repr(error)}"
        )

        # Incluso si ocurre un error,
        # guardamos el estado actual.
        if navegador is not None:

            try:

                html_final = (
                    navegador.page_source
                )

                guardar_html(
                    html_final
                )

                escribir()
                escribir(
                    "HTML del estado de error "
                    "guardado."
                )

            except Exception as error_html:

                escribir(
                    f"No se pudo guardar HTML: "
                    f"{error_html!r}"
                )

            try:

                screenshot_ok, metodo = (
                    guardar_screenshot_completo(
                        navegador
                    )
                )

                escribir(
                    f"Screenshot del estado "
                    f"de error: "
                    f"{screenshot_ok} | "
                    f"{metodo}"
                )

            except Exception as error_png:

                escribir(
                    f"No se pudo guardar PNG: "
                    f"{error_png!r}"
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
        print("TXT:")
        print(ARCHIVO_TXT)

        print()
        print("HTML:")
        print(ARCHIVO_HTML)

        print()
        print("PNG:")
        print(ARCHIVO_PNG)


# ============================================================
# 34. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()