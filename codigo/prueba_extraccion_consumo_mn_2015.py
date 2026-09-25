# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Prueba controlada de extracción Consumo MN - SBS - 30/11/2015

from pathlib import Path
from datetime import date
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
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

# ÚNICA FECHA DE ESTA PRUEBA
FECHA_OBJETIVO = date(
    2015,
    11,
    30
)

FECHA_TEXTO = (
    "30/11/2015"
)

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
    / "prueba_extraccion_consumo_mn_2015.txt"
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

# Tabla histórica MN ya identificada.
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# DataZone histórica MN.
ID_DATAZONE_MN = (
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
    escribir("=" * 122)
    escribir(texto)
    escribir("=" * 122)


def subtitulo(texto):

    escribir()
    escribir("-" * 122)
    escribir(texto)
    escribir("-" * 122)


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

    """
    Se usa únicamente para comparar
    etiquetas como Consumo y Promedio.

    NO se normalizan los nombres bancarios
    que se guardan en la salida.
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


# ============================================================
# 5. NAVEGADOR
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

def pagina_sbs_real(
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
            len(fecha) > 0
            and
            len(boton) > 0
        )

    except Exception:

        return False


# ============================================================
# 8. VERIFICACIÓN MANUAL
# ============================================================

def asegurar_pagina_real(
    navegador
):

    try:

        WebDriverWait(
            navegador,
            15
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
            "La aplicación SBS real todavía "
            "no fue detectada."
        )

        escribir(
            "Si Chrome muestra una verificación "
            "de seguridad, complétala manualmente."
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
# 10. DATEPICKER
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


def leer_fecha_visible(
    navegador
):

    elemento = localizar_fecha_visible(
        navegador
    )

    if elemento is None:

        return None

    return limpiar_texto(
        elemento.get_attribute(
            "value"
        )
    )


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
# 11. VALIDAR MN Y B
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
            "Se esperaba hdTipoMoneda='MN'."
        )

    if entidad != "B":

        raise RuntimeError(
            "Se esperaba hdTipoEntidad='B'."
        )


# ============================================================
# 12. ESTADO DEL DATEPICKER
# ============================================================

def obtener_estado_fecha(
    navegador
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
                visible == FECHA_OBJETIVO
                and
                interna == FECHA_OBJETIVO
            ),
    }


# ============================================================
# 13. CAMBIAR FECHA POR TECLADO
# ============================================================

def cambiar_fecha_teclado(
    navegador
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise RuntimeError(
            "No se encontró el DatePicker visible."
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


# ============================================================
# 14. FALLBACK TELERIK
# ============================================================

def cambiar_fecha_telerik(
    navegador
):

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

            var fecha = new Date(
                arguments[1],
                arguments[2] - 1,
                arguments[3]
            );

            picker.set_selectedDate(
                fecha
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
        FECHA_OBJETIVO.year,
        FECHA_OBJETIVO.month,
        FECHA_OBJETIVO.day,
        FECHA_TEXTO,
    )

    time.sleep(
        1
    )

    return resultado


# ============================================================
# 15. ESTABLECER FECHA ESTRICTAMENTE
# ============================================================

def establecer_fecha(
    navegador
):

    cambiar_fecha_teclado(
        navegador
    )

    estado = obtener_estado_fecha(
        navegador
    )

    escribir(
        f"Fecha visible: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"Fecha interna: "
        f"{estado['interna_texto']!r}"
    )

    if estado[
        "ambas_ok"
    ]:

        escribir(
            "[OK] DatePicker validado."
        )

        return

    escribir(
        "Aplicando fallback Telerik..."
    )

    resultado = cambiar_fecha_telerik(
        navegador
    )

    escribir(
        f"Resultado Telerik: "
        f"{resultado!r}"
    )

    estado = obtener_estado_fecha(
        navegador
    )

    escribir(
        f"Fecha visible final: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"Fecha interna final: "
        f"{estado['interna_texto']!r}"
    )

    if not estado[
        "ambas_ok"
    ]:

        raise RuntimeError(
            "FECHA_PRECONSULTA_INVALIDA"
        )

    escribir(
        "[OK] DatePicker validado "
        "después de Telerik."
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

    for metodo, valor in candidatos:

        elementos = navegador.find_elements(
            metodo,
            valor
        )

        if elementos:

            return elementos[0]

    return None


# ============================================================
# 17. CONFIRMAR PERÍODO REAL DEL RESULTADO
# ============================================================

def buscar_confirmacion_periodo(
    navegador
):
    """
    Exige texto visible:

        al 30/11/2015

    El DatePicker NO cuenta como evidencia
    del período del resultado.
    """

    try:

        resultados = navegador.execute_script(
            r"""
            const patron =
                /\bal\s+30\/11\/2015\b/i;

            const elementos =
                Array.from(
                    document.querySelectorAll(
                        'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th,strong,b'
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
                    rect.width <= 0
                    ||
                    rect.height <= 0
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
                    texto.length > 600
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

                if (vistos.has(clave)) {
                    continue;
                }

                vistos.add(clave);

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

        return resultados or []

    except Exception:

        return []


# ============================================================
# 18. BUSCAR MENSAJE SIN INFORMACIÓN
# ============================================================

def buscar_sin_informacion(
    navegador
):

    try:

        texto = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except Exception:

        return False

    normal = normalizar_texto(
        texto
    )

    return (
        "no existe informacion "
        "para la fecha elegida"
        in normal
    )


# ============================================================
# 19. CONSULTAR SOLO 30/11/2015
# ============================================================

def consultar(
    navegador
):

    boton = localizar_boton(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se encontró el botón Consultar."
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

    confirmaciones = []

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        sin_info = buscar_sin_informacion(
            navegador
        )

        confirmaciones = (
            buscar_confirmacion_periodo(
                navegador
            )
        )

        # SIN_INFORMACION tiene prioridad.
        if sin_info:

            raise RuntimeError(
                "SIN_INFORMACION: SBS indicó "
                "'No existe información para "
                "la fecha elegida'."
            )

        if confirmaciones:

            break

        time.sleep(
            0.25
        )

    if not confirmaciones:

        raise RuntimeError(
            "FECHA_RESULTADO_NO_CONFIRMADA: "
            "no apareció 'al 30/11/2015'."
        )

    # Margen de estabilización.
    time.sleep(
        2
    )

    # Revisión final por si el mensaje aparece
    # después del encabezado de fecha.
    if buscar_sin_informacion(
        navegador
    ):

        raise RuntimeError(
            "SIN_INFORMACION: la fecha fue "
            "confirmada pero SBS indicó "
            "que no existe información."
        )

    confirmaciones = (
        buscar_confirmacion_periodo(
            navegador
        )
    )

    if not confirmaciones:

        raise RuntimeError(
            "FECHA_RESULTADO_NO_CONFIRMADA_POST"
        )

    escribir(
        "[OK] SBS confirmó explícitamente:"
    )

    for item in confirmaciones:

        escribir(
            f"  id={item.get('id')!r} | "
            f"text={item.get('text')!r}"
        )


# ============================================================
# 20. RECONSTRUIR CONSUMO SIN OFFSET FIJO
# ============================================================

def reconstruir_consumo(
    navegador
):
    """
    La correspondencia se reconstruye
    geométricamente.

    PASOS:

    1. localizar exactamente una etiqueta
       externa Consumo;

    2. identificar las filas de datos de
       DataZone dinámicamente, sin imponer
       cantidad fija de columnas;

    3. asociar Consumo con la fila numérica
       que se encuentra a la misma altura;

    4. determinar el número N de valores;

    5. buscar dinámicamente una fila de
       encabezados con N columnas;

    6. alinear encabezado y valor por
       posición horizontal.

    No se usa ningún offset de fila.
    """

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    // ========================================================
    // FUNCIONES AUXILIARES
    // ========================================================

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

    function esFaltante(txt) {

        const n =
            normalizar(txt);

        const faltantes =
            new Set([
                '',
                '-',
                's.i.',
                's.i',
                'n.d.',
                'n.d',
                'nd',
                'n/a',
                'na',
                'n.i.',
                'n.i'
            ]);

        return faltantes.has(n);
    }

    function esNumero(txt) {

        txt = limpiar(txt);

        if (!txt) {
            return false;
        }

        const numero =
            txt
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

    // ========================================================
    // 1. OBTENER EXCLUSIVAMENTE GRID MN + DATAZONE
    // ========================================================

    const outer =
        document.getElementById(
            OUTER_ID
        );

    const dataZone =
        document.getElementById(
            DATA_ID
        );

    if (!outer) {

        return {
            ok:
                false,

            error:
                'TABLA_MN_EXTERNA_NO_ENCONTRADA'
        };
    }

    if (!dataZone) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_ENCONTRADA'
        };
    }

    if (!visible(outer)) {

        return {
            ok:
                false,

            error:
                'TABLA_MN_EXTERNA_NO_VISIBLE'
        };
    }

    if (!visible(dataZone)) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_VISIBLE'
        };
    }

    // ========================================================
    // 2. LOCALIZAR EXACTAMENTE UNA ETIQUETA EXTERNA CONSUMO
    // ========================================================

    const consumoLabels = [];

    const outerCells =
        Array.from(
            outer.querySelectorAll(
                'td,th'
            )
        );

    for (
        const cell
        of outerCells
    ) {

        if (!visible(cell)) {
            continue;
        }

        /*
        La etiqueta debe ser EXTERNA.
        Excluir DataZone.
        */
        if (
            dataZone.contains(cell)
        ) {
            continue;
        }

        /*
        Evitar celdas contenedoras de
        tablas anidadas.
        */
        if (
            cell.querySelector('table')
        ) {
            continue;
        }

        const texto =
            limpiar(
                cell.innerText
                ||
                cell.textContent
            );

        if (
            normalizar(texto)
            !== 'consumo'
        ) {
            continue;
        }

        const row =
            cell.closest('tr');

        if (
            !row
            ||
            !visible(row)
        ) {
            continue;
        }

        consumoLabels.push({
            text:
                texto,

            element:
                cell,

            row:
                row,

            cellRect:
                rectInfo(cell),

            rowRect:
                rectInfo(row)
        });
    }

    if (
        consumoLabels.length !== 1
    ) {

        return {
            ok:
                false,

            error:
                'CONSUMO_EXTERNO_NO_UNIVOCO',

            consumoLabelCount:
                consumoLabels.length
        };
    }

    const consumoLabel =
        consumoLabels[0];

    // ========================================================
    // 3. DETECTAR FILAS DE DATOS DE DATAZONE
    //
    // NO SE IMPONE NÚMERO DE COLUMNAS.
    // ========================================================

    const dataRows = [];

    const rows =
        Array.from(
            dataZone.querySelectorAll(
                'tr'
            )
        )
        .filter(
            row =>
                row.closest('table')
                === dataZone
        );

    for (
        let i = 0;
        i < rows.length;
        i++
    ) {

        const row =
            rows[i];

        if (!visible(row)) {
            continue;
        }

        const cells =
            Array.from(
                row.children
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
            cells.length < 2
        ) {
            continue;
        }

        const texts =
            cells.map(
                cell =>
                    limpiar(
                        cell.innerText
                        ||
                        cell.textContent
                    )
            );

        /*
        Una fila de datos debe estar formada
        únicamente por números o faltantes.

        Se exige al menos un número real,
        para evitar confundir una fila vacía.
        */

        const todosSonValores =
            texts.every(
                texto =>
                    esValorTasa(texto)
            );

        const tieneNumero =
            texts.some(
                texto =>
                    esNumero(texto)
            );

        if (
            todosSonValores
            &&
            tieneNumero
        ) {

            dataRows.push({
                originalIndex:
                    i,

                element:
                    row,

                rect:
                    rectInfo(row),

                cells:
                    cells,

                texts:
                    texts,

                valueCount:
                    cells.length
            });
        }
    }

    if (
        dataRows.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_DETECTARON_FILAS_NUMERICAS'
        };
    }

    // ========================================================
    // 4. MAPEAR CONSUMO A FILA NUMÉRICA
    //
    // SIN OFFSET FIJO.
    // ========================================================

    const candidatosConsumo = [];

    for (
        const fila
        of dataRows
    ) {

        const overlap =
            overlapVertical(
                consumoLabel.rowRect,
                fila.rect
            );

        const distancia =
            Math.abs(
                consumoLabel.rowRect.centerY
                -
                fila.rect.centerY
            );

        candidatosConsumo.push({
            fila:
                fila,

            overlap:
                overlap,

            distancia:
                distancia
        });
    }

    candidatosConsumo.sort(
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

    const mejorConsumo =
        candidatosConsumo[0];

    if (
        !mejorConsumo
        ||
        mejorConsumo.overlap < 0.50
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_PUDO_MAPEAR_CONSUMO_POR_GEOMETRIA',

            bestOverlap:
                mejorConsumo
                ? mejorConsumo.overlap
                : null,

            bestDistance:
                mejorConsumo
                ? mejorConsumo.distancia
                : null
        };
    }

    /*
    Comprobar unicidad geométrica.

    Si dos filas tienen exactamente el mismo
    grado de solapamiento y prácticamente la
    misma distancia, no forzamos selección.
    */

    if (
        candidatosConsumo.length > 1
    ) {

        const segundo =
            candidatosConsumo[1];

        const overlapMuyParecido =
            Math.abs(
                mejorConsumo.overlap
                -
                segundo.overlap
            )
            < 0.000001;

        const distanciaMuyParecida =
            Math.abs(
                mejorConsumo.distancia
                -
                segundo.distancia
            )
            < 0.5;

        if (
            overlapMuyParecido
            &&
            distanciaMuyParecida
        ) {

            return {
                ok:
                    false,

                error:
                    'MAPEO_CONSUMO_AMBIGUO',

                firstRow:
                    mejorConsumo.fila.originalIndex,

                secondRow:
                    segundo.fila.originalIndex
            };
        }
    }

    const consumoRow =
        mejorConsumo.fila;

    const cantidadValores =
        consumoRow.cells.length;

    // ========================================================
    // 5. DETECTAR DINÁMICAMENTE LA FILA DE ENCABEZADOS
    //
    // Debe tener el mismo número de posiciones
    // que la fila Consumo.
    //
    // No se asume banco alguno.
    // ========================================================

    const consumoCellRects =
        consumoRow.cells.map(
            cell =>
                rectInfo(cell)
        );

    const headerCandidates = [];

    const allRows =
        Array.from(
            dataZone.querySelectorAll(
                'tr'
            )
        )
        .filter(
            row =>
                row.closest('table')
                === dataZone
        );

    for (
        let i = 0;
        i < allRows.length;
        i++
    ) {

        const row =
            allRows[i];

        if (!visible(row)) {
            continue;
        }

        const rowRect =
            rectInfo(row);

        /*
        Encabezado debe estar arriba
        de la fila Consumo.
        */
        if (
            rowRect.bottom
            >
            consumoRow.rect.top
            + 1
        ) {
            continue;
        }

        const cells =
            Array.from(
                row.children
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
            cells.length < 2
        ) {
            continue;
        }

        const items =
            [];

        for (
            const cell
            of cells
        ) {

            /*
            No usar contenedores de otras tablas.
            */
            if (
                cell.querySelector('table')
            ) {
                continue;
            }

            const texto =
                limpiar(
                    cell.innerText
                    ||
                    cell.textContent
                );

            if (!texto) {
                continue;
            }

            /*
            Los encabezados deben ser textuales.
            */
            if (
                esNumero(texto)
                ||
                esFaltante(texto)
            ) {
                continue;
            }

            items.push({
                text:
                    texto,

                rect:
                    rectInfo(cell)
            });
        }

        if (
            items.length === 0
        ) {
            continue;
        }

        /*
        Alinear horizontalmente cada celda
        Consumo con el mejor encabezado.
        */

        const headers =
            [];

        let matchedCount = 0;

        for (
            const valueRect
            of consumoCellRects
        ) {

            let mejor = null;

            for (
                const item
                of items
            ) {

                const overlap =
                    overlapHorizontal(
                        valueRect,
                        item.rect
                    );

                const distancia =
                    Math.abs(
                        valueRect.centerX
                        -
                        item.rect.centerX
                    );

                const candidato = {
                    text:
                        item.text,

                    overlap:
                        overlap,

                    distancia:
                        distancia
                };

                if (
                    mejor === null
                    ||
                    candidato.overlap
                    >
                    mejor.overlap
                    ||
                    (
                        candidato.overlap
                        === mejor.overlap
                        &&
                        candidato.distancia
                        <
                        mejor.distancia
                    )
                ) {

                    mejor =
                        candidato;
                }
            }

            if (
                mejor
                &&
                mejor.overlap >= 0.50
            ) {

                headers.push(
                    mejor.text
                );

                matchedCount++;

            } else {

                headers.push(
                    null
                );
            }
        }

        const uniqueHeaders =
            new Set(
                headers
                .filter(
                    x => x !== null
                )
                .map(
                    x =>
                        normalizar(x)
                )
            ).size;

        headerCandidates.push({
            rowIndex:
                i,

            matchedCount:
                matchedCount,

            uniqueCount:
                uniqueHeaders,

            headers:
                headers,

            distanceAbove:
                consumoRow.rect.top
                -
                rowRect.bottom
        });
    }

    if (
        headerCandidates.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_ENCONTRARON_ENCABEZADOS',

            valueCount:
                cantidadValores
        };
    }

    /*
    Elegir:
      1. mayor número de matches;
      2. mayor número de encabezados únicos;
      3. fila más cercana a los datos.
    */

    headerCandidates.sort(
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

    const bestHeader =
        headerCandidates[0];

    if (
        bestHeader.matchedCount
        !==
        cantidadValores
    ) {

        return {
            ok:
                false,

            error:
                'ENCABEZADOS_NO_COINCIDEN_CON_VALORES',

            headerMatchedCount:
                bestHeader.matchedCount,

            valueCount:
                cantidadValores,

            headers:
                bestHeader.headers,

            values:
                consumoRow.texts
        };
    }

    if (
        bestHeader.headers.length
        !==
        cantidadValores
    ) {

        return {
            ok:
                false,

            error:
                'NUMERO_ENCABEZADOS_DISTINTO_DE_NUMERO_VALORES',

            headerCount:
                bestHeader.headers.length,

            valueCount:
                cantidadValores
        };
    }

    // ========================================================
    // 6. ARMAR REGISTROS SIN NORMALIZAR NOMBRES
    // ========================================================

    const registros = [];

    let promedio = null;

    const bancos = [];

    for (
        let i = 0;
        i < cantidadValores;
        i++
    ) {

        const encabezado =
            limpiar(
                bestHeader.headers[i]
            );

        const valor =
            limpiar(
                consumoRow.texts[i]
            );

        const registro = {
            columnIndex:
                i,

            header:
                encabezado,

            rawValue:
                valor,

            isMissing:
                esFaltante(valor),

            isPromedio:
                normalizar(encabezado)
                === 'promedio'
        };

        registros.push(
            registro
        );

        if (
            registro.isPromedio
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

        } else {

            bancos.push(
                registro
            );
        }
    }

    if (
        promedio === null
    ) {

        return {
            ok:
                false,

            error:
                'PROMEDIO_NO_DETECTADO',

            headers:
                bestHeader.headers,

            values:
                consumoRow.texts
        };
    }

    return {
        ok:
            true,

        outerId:
            outer.id,

        dataZoneId:
            dataZone.id,

        consumoLabelCount:
            consumoLabels.length,

        numericRowCount:
            dataRows.length,

        consumoDataRowIndex:
            consumoRow.originalIndex,

        consumoVerticalOverlap:
            mejorConsumo.overlap,

        consumoCenterDistance:
            mejorConsumo.distancia,

        totalHeaderCount:
            bestHeader.headers.length,

        totalValueCount:
            consumoRow.texts.length,

        headerSourceRowIndex:
            bestHeader.rowIndex,

        headerMatchCount:
            bestHeader.matchedCount,

        headerUniqueCount:
            bestHeader.uniqueCount,

        headers:
            bestHeader.headers,

        values:
            consumoRow.texts,

        registros:
            registros,

        bancos:
            bancos,

        promedio:
            promedio,

        bankCount:
            bancos.length
    };
    """

    return navegador.execute_script(
        script,
        ID_TABLA_MN_EXTERNA,
        ID_DATAZONE_MN,
    )


# ============================================================
# 21. MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    resultado
):

    titulo(
        "VALIDACIÓN DEL MAPEO DE CONSUMO"
    )

    escribir(
        f"Tabla MN: "
        f"{resultado['outerId']}"
    )

    escribir(
        f"DataZone MN: "
        f"{resultado['dataZoneId']}"
    )

    escribir(
        f"Etiquetas externas exactas Consumo: "
        f"{resultado['consumoLabelCount']}"
    )

    escribir(
        f"Filas numéricas detectadas: "
        f"{resultado['numericRowCount']}"
    )

    escribir(
        f"Fila DataZone mapeada a Consumo: "
        f"{resultado['consumoDataRowIndex']}"
    )

    escribir(
        f"Solapamiento vertical: "
        f"{resultado['consumoVerticalOverlap']:.6f}"
    )

    escribir(
        f"Distancia de centros verticales: "
        f"{resultado['consumoCenterDistance']:.6f}"
    )

    subtitulo(
        "VALIDACIÓN ENCABEZADOS ↔ VALORES"
    )

    cantidad_encabezados = (
        resultado[
            "totalHeaderCount"
        ]
    )

    cantidad_valores = (
        resultado[
            "totalValueCount"
        ]
    )

    escribir(
        f"Cantidad total de encabezados: "
        f"{cantidad_encabezados}"
    )

    escribir(
        f"Cantidad total de valores: "
        f"{cantidad_valores}"
    )

    escribir(
        f"Fila de encabezados detectada: "
        f"{resultado['headerSourceRowIndex']}"
    )

    escribir(
        f"Encabezados alineados: "
        f"{resultado['headerMatchCount']}"
    )

    escribir(
        f"Encabezados únicos: "
        f"{resultado['headerUniqueCount']}"
    )

    if (
        cantidad_encabezados
        !=
        cantidad_valores
    ):

        raise RuntimeError(
            "El número de encabezados "
            "no coincide con el número "
            "de valores."
        )

    escribir(
        "[OK] El número de encabezados "
        "es exactamente igual al "
        "número de valores."
    )

    subtitulo(
        "ENCABEZADOS HISTÓRICOS DETECTADOS"
    )

    for indice, encabezado in enumerate(
        resultado[
            "headers"
        ],
        start=1
    ):

        escribir(
            f"{indice:02d}. "
            f"{encabezado}"
        )

    # ========================================================
    # TABLA DE BANCOS
    # ========================================================

    titulo(
        "TASA ACTIVA DE CONSUMO MN - 30/11/2015"
    )

    escribir(
        "banco | tasa_consumo_mn"
    )

    escribir(
        "-" * 82
    )

    for registro in resultado[
        "bancos"
    ]:

        banco = registro[
            "header"
        ]

        valor = registro[
            "rawValue"
        ]

        # No convertir:
        # - a cero;
        # - a promedio;
        # - ni interpolar.
        #
        # Para que un vacío sea visible en el TXT,
        # se muestra <VACIO>, aunque el valor bruto
        # conservado internamente sigue siendo "".

        if valor == "":

            valor_visible = (
                "<VACIO>"
            )

        else:

            valor_visible = valor

        escribir(
            f"{banco} | "
            f"{valor_visible}"
        )

    # ========================================================
    # PROMEDIO SEPARADO
    # ========================================================

    subtitulo(
        "PROMEDIO - SEPARADO DE LOS BANCOS"
    )

    promedio = resultado[
        "promedio"
    ]

    promedio_valor = promedio[
        "rawValue"
    ]

    if promedio_valor == "":

        promedio_visible = (
            "<VACIO>"
        )

    else:

        promedio_visible = (
            promedio_valor
        )

    escribir(
        f"Promedio | "
        f"{promedio_visible}"
    )

    # ========================================================
    # FALTANTES
    # ========================================================

    subtitulo(
        "CONTROL DE FALTANTES"
    )

    faltantes_bancos = [
        registro
        for registro in resultado[
            "bancos"
        ]
        if registro[
            "isMissing"
        ]
    ]

    escribir(
        f"Cantidad de bancos: "
        f"{resultado['bankCount']}"
    )

    escribir(
        f"Valores faltantes entre bancos: "
        f"{len(faltantes_bancos)}"
    )

    if faltantes_bancos:

        for registro in faltantes_bancos:

            valor = registro[
                "rawValue"
            ]

            if valor == "":

                valor = (
                    "<VACIO>"
                )

            escribir(
                f"  {registro['header']} "
                f"→ {valor}"
            )

    else:

        escribir(
            "  <NINGUNO>"
        )

    escribir()
    escribir(
        "Los faltantes se conservaron "
        "tal como los entrega SBS."
    )

    escribir(
        "No se reemplazaron por cero."
    )

    escribir(
        "No se interpolaron."
    )

    escribir(
        "No se normalizaron nombres bancarios."
    )


# ============================================================
# 22. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    try:

        titulo(
            "PRUEBA DE EXTRACCIÓN "
            "TASA ACTIVA CONSUMO MN "
            "- 30/11/2015"
        )

        escribir(
            "Fecha única consultada: "
            "30/11/2015"
        )

        escribir()
        escribir(
            "Objetivo:"
        )

        escribir(
            "extraer únicamente la fila "
            "Consumo en Moneda Nacional, "
            "manteniendo la estructura "
            "bancaria histórica de 2015."
        )

        escribir()
        escribir(
            "NO se consultarán otros meses."
        )

        escribir(
            "NO se interpolarán datos."
        )

        escribir(
            "NO se seleccionarán bancos finales."
        )

        escribir(
            "NO se normalizarán nombres bancarios."
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
        # PRE-CONSULTA
        # ====================================================

        titulo(
            "VALIDACIÓN PRE-CONSULTA"
        )

        validar_mn_b(
            navegador
        )

        establecer_fecha(
            navegador
        )

        validar_mn_b(
            navegador
        )

        estado = obtener_estado_fecha(
            navegador
        )

        if not estado[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "DatePicker no validado."
            )

        escribir(
            "[OK] Fecha visible e interna "
            "son exactamente 30/11/2015."
        )

        # ====================================================
        # POST
        # ====================================================

        titulo(
            "CONSULTAR"
        )

        consultar(
            navegador
        )

        # Confirmación independiente final.
        confirmaciones = (
            buscar_confirmacion_periodo(
                navegador
            )
        )

        if not confirmaciones:

            raise RuntimeError(
                "FECHA_RESULTADO_NO_CONFIRMADA"
            )

        if buscar_sin_informacion(
            navegador
        ):

            raise RuntimeError(
                "SIN_INFORMACION"
            )

        escribir()
        escribir(
            "[OK] Resultado histórico "
            "confirmado como "
            "'al 30/11/2015'."
        )

        # ====================================================
        # ESTRUCTURA EXCLUSIVAMENTE MN
        # ====================================================

        titulo(
            "VALIDACIÓN DEL GRID MN"
        )

        externas = navegador.find_elements(
            By.ID,
            ID_TABLA_MN_EXTERNA
        )

        internas = navegador.find_elements(
            By.ID,
            ID_DATAZONE_MN
        )

        escribir(
            f"Tabla MN encontrada: "
            f"{len(externas)}"
        )

        escribir(
            f"DataZone MN encontrada: "
            f"{len(internas)}"
        )

        if len(
            externas
        ) != 1:

            raise RuntimeError(
                "Se esperaba exactamente "
                "una tabla MN externa."
            )

        if len(
            internas
        ) != 1:

            raise RuntimeError(
                "Se esperaba exactamente "
                "una DataZone MN."
            )

        # ====================================================
        # RECONSTRUCCIÓN SIN OFFSET FIJO
        # ====================================================

        titulo(
            "RECONSTRUCCIÓN "
            "ETIQUETA CONSUMO → FILA NUMÉRICA"
        )

        resultado = reconstruir_consumo(
            navegador
        )

        if not resultado.get(
            "ok",
            False
        ):

            escribir(
                f"ERROR DE RECONSTRUCCIÓN: "
                f"{resultado.get('error')}"
            )

            escribir(
                f"Detalle recibido: "
                f"{resultado}"
            )

            raise RuntimeError(
                resultado.get(
                    "error",
                    "ERROR_RECONSTRUCCION"
                )
            )

        # ====================================================
        # MOSTRAR EXTRACCIÓN
        # ====================================================

        mostrar_resultado(
            resultado
        )

        # ====================================================
        # VALIDACIÓN FINAL
        # ====================================================

        titulo(
            "CLASIFICACIÓN FINAL"
        )

        escribir(
            "ESTADO = "
            "EXTRACCION_CONSUMO_MN_2015_VALIDADA"
        )

        escribir()
        escribir(
            "Validaciones cumplidas:"
        )

        escribir(
            "1. período confirmado "
            "'al 30/11/2015';"
        )

        escribir(
            "2. se utilizó exclusivamente "
            "la tabla MN indicada;"
        )

        escribir(
            "3. se utilizó exclusivamente "
            "su DataZone MN;"
        )

        escribir(
            "4. existe exactamente una "
            "etiqueta externa Consumo;"
        )

        escribir(
            "5. Consumo fue asociado "
            "geométricamente a su fila "
            "numérica sin offset fijo;"
        )

        escribir(
            "6. los encabezados fueron "
            "detectados dinámicamente;"
        )

        escribir(
            "7. número de encabezados = "
            "número de valores;"
        )

        escribir(
            "8. Promedio quedó separado;"
        )

        escribir(
            "9. los faltantes se conservaron;"
        )

        escribir(
            "10. no hubo interpolación;"
        )

        escribir(
            "11. no se normalizaron "
            "nombres bancarios;"
        )

        escribir(
            "12. no se consultaron "
            "otros meses."
        )

    except Exception as error:

        titulo(
            "ERROR DE LA PRUEBA"
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
            "La extracción NO debe "
            "considerarse validada mientras "
            "exista este error."
        )

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
        print("=" * 122)
        print("PRUEBA FINALIZADA")
        print("=" * 122)

        print()
        print(
            "Resultado guardado en:"
        )

        print(
            ARCHIVO_TXT
        )


# ============================================================
# 23. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()