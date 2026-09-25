# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Prueba controlada de extracción Consumo MN - SBS - 30/06/2020

from pathlib import Path
from datetime import datetime
import re
import time
import unicodedata

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

FECHA_OBJETIVO = "30/06/2020"

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
    / "prueba_extraccion_consumo_mn_2020.txt"
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

# Tabla completa MN confirmada en el diagnóstico 2020
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# DataZone histórica confirmada
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
    escribir("=" * 120)
    escribir(texto)
    escribir("=" * 120)


def subtitulo(texto):

    escribir()
    escribir("-" * 120)
    escribir(texto)
    escribir("-" * 120)


# ============================================================
# 4. TEXTO
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

    return re.sub(
        r"\s+",
        " ",
        texto
    ).strip()


# ============================================================
# 5. NAVEGADOR
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
# 7. COMPROBAR SBS REAL
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
            "Si aparece una verificación "
            "de seguridad, complétala manualmente."
        )

        escribir(
            "No cierres Chrome."
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
            "[OK] Página SBS real detectada."
        )

        return True

    except TimeoutException:

        return False


# ============================================================
# 9. FECHAS
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

        anio = int(
            coincidencia.group(3)
        )

        try:

            return datetime(
                anio,
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

            return datetime(
                anio,
                mes,
                dia
            ).date()

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
# 12. ESTADO DATEPICKER
# ============================================================

def obtener_estado_fecha(
    navegador
):

    objetivo = convertir_fecha(
        FECHA_OBJETIVO
    )

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
            objetivo,

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
                visible == objetivo
                and
                interna == objetivo
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
        FECHA_OBJETIVO
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

    objetivo = datetime.strptime(
        FECHA_OBJETIVO,
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
        objetivo.year,
        objetivo.month,
        objetivo.day,
        FECHA_OBJETIVO,
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
            "[OK] Visible e interna "
            "son exactamente 30/06/2020."
        )

        return

    escribir()
    escribir(
        "Aplicando API Telerik..."
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
        "[OK] Visible e interna "
        "validadas después de Telerik."
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
# 17. CONFIRMACIÓN REAL DEL PERÍODO
# ============================================================

def buscar_confirmacion_periodo(
    navegador
):
    """
    El DatePicker NO sirve como evidencia.

    Exige texto visible del resultado:

        al 30/06/2020
    """

    try:

        resultados = navegador.execute_script(
            r"""
            const patron =
                /\bal\s+30\/06\/2020\b/i;

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
                    texto.length > 500
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
# 18. CONSULTAR SOLO 30/06/2020
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
        0.5
    )

    boton.click()

    inicio = time.time()

    confirmaciones = []

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        confirmaciones = (
            buscar_confirmacion_periodo(
                navegador
            )
        )

        if confirmaciones:

            break

        time.sleep(
            0.25
        )

    if not confirmaciones:

        raise RuntimeError(
            "FECHA_RESULTADO_NO_CONFIRMADA: "
            "no apareció texto visible "
            "'al 30/06/2020'."
        )

    escribir()
    escribir(
        "[OK] SBS confirmó explícitamente:"
    )

    for item in confirmaciones:

        escribir(
            f"  id={item.get('id')!r} | "
            f"text={item.get('text')!r}"
        )

    # Margen para renderización final del grid.
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


# ============================================================
# 19. RECONSTRUIR GRID MEDIANTE GEOMETRÍA
# ============================================================

def reconstruir_consumo(
    navegador
):
    """
    REGLA CENTRAL

    NO utiliza offset de filas.

    La correspondencia se reconstruye usando
    la posición visual real del navegador:

      etiqueta externa
            ↕ alineación vertical
      fila numérica DataZone

    Los encabezados se alinean horizontalmente
    con las 16 celdas de la fila Consumo.

    Devuelve únicamente los valores de Consumo.
    """

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    // --------------------------------------------------------
    // FUNCIONES AUXILIARES
    // --------------------------------------------------------

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

    function esDato(txt) {

        txt = limpiar(txt);

        /*
        Vacío se considera faltante posible,
        pero no basta por sí solo para declarar
        una fila numérica.
        */

        if (!txt) {
            return true;
        }

        const n =
            normalizar(txt);

        const faltantes = new Set([
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

    function tieneDatoReal(txt) {

        txt = limpiar(txt);

        if (!txt) {
            return false;
        }

        return esDato(txt);
    }

    // --------------------------------------------------------
    // LOCALIZAR LAS DOS TABLAS CONFIRMADAS
    // --------------------------------------------------------

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

    // --------------------------------------------------------
    // 1. FILAS NUMÉRICAS REALES DE DATAZONE
    // --------------------------------------------------------

    const dataRows = [];

    const filasDataZone =
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
        i < filasDataZone.length;
        i++
    ) {

        const row =
            filasDataZone[i];

        if (!visible(row)) {
            continue;
        }

        const cells =
            Array.from(
                row.children
            )
            .filter(
                el =>
                    el.tagName === 'TD'
                    ||
                    el.tagName === 'TH'
            );

        if (
            cells.length === 0
        ) {
            continue;
        }

        const textos =
            cells.map(
                cell =>
                    limpiar(
                        cell.innerText
                        ||
                        cell.textContent
                    )
            );

        const todosDatos =
            textos.every(
                texto =>
                    esDato(texto)
            );

        const algunDato =
            textos.some(
                texto =>
                    tieneDatoReal(texto)
            );

        /*
        Para esta prueba esperamos 16 columnas.
        No asumimos qué fila es Consumo.
        */

        if (
            cells.length === 16
            &&
            todosDatos
            &&
            algunDato
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
                    textos
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
                'NO_SE_DETECTARON_FILAS_NUMERICAS_DE_16_COLUMNAS'
        };
    }

    // --------------------------------------------------------
    // 2. ETIQUETAS EXTERNAS DEL GRID MN
    //
    // Excluimos cualquier celda que esté dentro
    // de DataZone.
    //
    // No usamos número de fila ni offset.
    // --------------------------------------------------------

    const etiquetas = [];

    const celdasOuter =
        Array.from(
            outer.querySelectorAll(
                'td,th'
            )
        );

    const filasYaVistas =
        new Set();

    for (
        const cell
        of celdasOuter
    ) {

        if (!visible(cell)) {
            continue;
        }

        /*
        No considerar nada de DataZone.
        */

        if (
            cell === dataZone
            ||
            dataZone.contains(cell)
        ) {
            continue;
        }

        /*
        Evitar celdas contenedoras de
        subtablas completas.
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
        Una etiqueta conceptual no debe ser
        numérica.
        */

        if (esDato(texto)) {
            continue;
        }

        const row =
            cell.closest('tr');

        if (!row) {
            continue;
        }

        if (!visible(row)) {
            continue;
        }

        /*
        Una misma fila podría contener varias
        celdas textuales. Elegimos después la
        celda más útil, pero conservamos cada
        etiqueta candidata.
        */

        etiquetas.push({
            text:
                texto,

            row:
                row,

            rowRect:
                rectInfo(row),

            cellRect:
                rectInfo(cell)
        });
    }

    // --------------------------------------------------------
    // 3. CONSTRUIR MAPEO GEOMÉTRICO
    //
    // Cada etiqueta se asigna a la fila numérica
    // con mayor solapamiento VERTICAL.
    //
    // No hay offsets fijos.
    // --------------------------------------------------------

    const mapeos = [];

    for (
        const etiqueta
        of etiquetas
    ) {

        let mejor = null;

        for (
            const filaDato
            of dataRows
        ) {

            const overlap =
                overlapVertical(
                    etiqueta.rowRect,
                    filaDato.rect
                );

            const distancia =
                Math.abs(
                    etiqueta.rowRect.centerY
                    -
                    filaDato.rect.centerY
                );

            const candidato = {
                dataRowIndex:
                    filaDato.originalIndex,

                overlap:
                    overlap,

                centerDistance:
                    distancia,

                valueCount:
                    filaDato.texts.length
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
                    candidato.centerDistance
                    <
                    mejor.centerDistance
                )
            ) {

                mejor =
                    candidato;
            }
        }

        /*
        Exigimos solapamiento fuerte.
        */

        if (
            mejor
            &&
            mejor.overlap >= 0.50
        ) {

            mapeos.push({
                label:
                    etiqueta.text,

                normalizedLabel:
                    normalizar(
                        etiqueta.text
                    ),

                dataRowIndex:
                    mejor.dataRowIndex,

                verticalOverlap:
                    mejor.overlap,

                centerDistance:
                    mejor.centerDistance,

                valueCount:
                    mejor.valueCount
            });
        }
    }

    // --------------------------------------------------------
    // 4. LOCALIZAR EXACTAMENTE CONSUMO
    // --------------------------------------------------------

    const consumoMapeos =
        mapeos.filter(
            x =>
                x.normalizedLabel
                === 'consumo'
        );

    /*
    El mismo row podría generar más de una
    etiqueta duplicada. Dedupe por data row.
    */

    const consumoUnicos = [];

    const consumoVistos =
        new Set();

    for (
        const item
        of consumoMapeos
    ) {

        const clave =
            item.dataRowIndex;

        if (
            consumoVistos.has(
                clave
            )
        ) {
            continue;
        }

        consumoVistos.add(
            clave
        );

        consumoUnicos.push(
            item
        );
    }

    if (
        consumoUnicos.length !== 1
    ) {

        return {
            ok:
                false,

            error:
                'CONSUMO_NO_MAPEADO_UNIVOCAMENTE',

            cantidadConsumoMapeos:
                consumoUnicos.length,

            mappings:
                mapeos
        };
    }

    const consumoMap =
        consumoUnicos[0];

    const consumoRow =
        dataRows.find(
            x =>
                x.originalIndex
                ===
                consumoMap.dataRowIndex
        );

    if (!consumoRow) {

        return {
            ok:
                false,

            error:
                'FILA_NUMERICA_CONSUMO_NO_ENCONTRADA'
        };
    }

    if (
        consumoRow.cells.length
        !== 16
    ) {

        return {
            ok:
                false,

            error:
                'CONSUMO_NO_TIENE_16_VALORES',

            valorCount:
                consumoRow.cells.length
        };
    }

    // --------------------------------------------------------
    // 5. DETECTAR LOS 16 ENCABEZADOS
    //
    // Tampoco asumimos offset fijo.
    //
    // Para cada fila textual situada por encima
    // de Consumo se intenta alinear horizontalmente
    // cada celda de encabezado con cada celda de
    // la fila numérica Consumo.
    // --------------------------------------------------------

    const dataCellRects =
        consumoRow.cells.map(
            cell =>
                rectInfo(cell)
        );

    const todasFilasOuter =
        Array.from(
            outer.querySelectorAll(
                'tr'
            )
        );

    const headerCandidates = [];

    for (
        let rowIndex = 0;
        rowIndex < todasFilasOuter.length;
        rowIndex++
    ) {

        const row =
            todasFilasOuter[rowIndex];

        if (!visible(row)) {
            continue;
        }

        const rowRect =
            rectInfo(row);

        /*
        Debe estar por encima de la fila Consumo.
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
                    el.tagName === 'TD'
                    ||
                    el.tagName === 'TH'
            )
            .filter(
                cell =>
                    visible(cell)
            );

        if (
            cells.length === 0
        ) {
            continue;
        }

        const candidateCells =
            cells
            .map(
                cell => ({
                    element:
                        cell,

                    text:
                        limpiar(
                            cell.innerText
                            ||
                            cell.textContent
                        ),

                    rect:
                        rectInfo(cell)
                })
            )
            .filter(
                item =>
                    item.text
                    &&
                    !esDato(
                        item.text
                    )
                    &&
                    !item.element
                        .querySelector('table')
            );

        if (
            candidateCells.length === 0
        ) {
            continue;
        }

        const headers = [];
        let matchedCount = 0;

        for (
            let j = 0;
            j < dataCellRects.length;
            j++
        ) {

            const dataRect =
                dataCellRects[j];

            let mejorHeader = null;

            for (
                const item
                of candidateCells
            ) {

                const overlap =
                    overlapHorizontal(
                        dataRect,
                        item.rect
                    );

                const distancia =
                    Math.abs(
                        dataRect.centerX
                        -
                        item.rect.centerX
                    );

                const candidato = {
                    text:
                        item.text,

                    overlap:
                        overlap,

                    distance:
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
                        candidato.distance
                        <
                        mejorHeader.distance
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
                    mejorHeader.text
                );

                matchedCount += 1;

            } else {

                headers.push(
                    null
                );
            }
        }

        const completos =
            headers.every(
                h =>
                    h !== null
                    &&
                    limpiar(h) !== ''
            );

        const unicos =
            new Set(
                headers
                .filter(
                    h => h !== null
                )
                .map(
                    h =>
                        normalizar(h)
                )
            ).size;

        if (
            matchedCount >= 1
        ) {

            headerCandidates.push({
                domRowIndex:
                    rowIndex,

                matchedCount:
                    matchedCount,

                uniqueCount:
                    unicos,

                headers:
                    headers,

                distanceAbove:
                    (
                        consumoRow.rect.top
                        -
                        rowRect.bottom
                    )
            });
        }
    }

    if (
        headerCandidates.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_DETECTARON_ENCABEZADOS_ALINEADOS',

            consumoMapping:
                consumoMap,

            values:
                consumoRow.texts,

            mappings:
                mapeos
        };
    }

    /*
    Priorizamos:
      1. 16 columnas emparejadas
      2. 16 nombres distintos o casi todos distintos
      3. fila más cercana verticalmente
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

    const headerBest =
        headerCandidates[0];

    if (
        headerBest.matchedCount
        !== 16
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_OBTUVIERON_16_ENCABEZADOS_ALINEADOS',

            bestHeaderCandidate:
                headerBest,

            consumoMapping:
                consumoMap,

            values:
                consumoRow.texts,

            mappings:
                mapeos
        };
    }

    if (
        headerBest.headers.length
        !== 16
    ) {

        return {
            ok:
                false,

            error:
                'CANTIDAD_ENCABEZADOS_DISTINTA_DE_16'
        };
    }

    // --------------------------------------------------------
    // 6. ARMAR ÚNICAMENTE CONSUMO
    // --------------------------------------------------------

    const registros = [];

    for (
        let i = 0;
        i < 16;
        i++
    ) {

        registros.push({
            columnIndex:
                i,

            header:
                limpiar(
                    headerBest.headers[i]
                ),

            rawValue:
                limpiar(
                    consumoRow.texts[i]
                )
        });
    }

    return {
        ok:
            true,

        outerId:
            outer.id,

        dataZoneId:
            dataZone.id,

        numericRowCount:
            dataRows.length,

        mappings:
            mapeos,

        consumoMapping:
            consumoMap,

        consumoDataRowIndex:
            consumoRow.originalIndex,

        consumoVerticalOverlap:
            consumoMap.verticalOverlap,

        consumoCenterDistance:
            consumoMap.centerDistance,

        headerSourceRowIndex:
            headerBest.domRowIndex,

        headerMatchCount:
            headerBest.matchedCount,

        headerUniqueCount:
            headerBest.uniqueCount,

        headerDistanceAbove:
            headerBest.distanceAbove,

        headers:
            headerBest.headers,

        values:
            consumoRow.texts,

        registros:
            registros
    };
    """

    return navegador.execute_script(
        script,
        ID_TABLA_MN_EXTERNA,
        ID_DATAZONE_MN,
    )


# ============================================================
# 20. MOSTRAR MAPEO DE ETIQUETAS
# ============================================================

def mostrar_mapeos(
    resultado
):

    subtitulo(
        "RECONSTRUCCIÓN ETIQUETA EXTERNA → FILA DATAZONE"
    )

    escribir(
        "La correspondencia siguiente se obtuvo "
        "mediante alineación vertical en pantalla."
    )

    escribir(
        "No se utilizó ningún offset fijo."
    )

    escribir()

    escribir(
        "etiqueta | data_row_index | "
        "overlap_vertical | distancia_centros | columnas"
    )

    for item in resultado.get(
        "mappings",
        []
    ):

        escribir(
            f"{item.get('label', '')} | "
            f"{item.get('dataRowIndex')} | "
            f"{item.get('verticalOverlap', 0):.6f} | "
            f"{item.get('centerDistance', 0):.6f} | "
            f"{item.get('valueCount')}"
        )


# ============================================================
# 21. MOSTRAR EXTRACCIÓN CONSUMO
# ============================================================

def mostrar_consumo(
    resultado
):

    titulo(
        "VALIDACIÓN DE LA FILA CONSUMO"
    )

    escribir(
        f"Tabla MN externa: "
        f"{resultado['outerId']}"
    )

    escribir(
        f"DataZone MN: "
        f"{resultado['dataZoneId']}"
    )

    escribir(
        f"Filas numéricas de 16 columnas "
        f"detectadas: "
        f"{resultado['numericRowCount']}"
    )

    escribir()
    escribir(
        "Mapeo específico de Consumo:"
    )

    escribir(
        f"  DataZone row index: "
        f"{resultado['consumoDataRowIndex']}"
    )

    escribir(
        f"  Solapamiento vertical: "
        f"{resultado['consumoVerticalOverlap']:.6f}"
    )

    escribir(
        f"  Distancia entre centros Y: "
        f"{resultado['consumoCenterDistance']:.6f}"
    )

    escribir()
    escribir(
        "Detección de encabezados:"
    )

    escribir(
        f"  Fila DOM usada como encabezado: "
        f"{resultado['headerSourceRowIndex']}"
    )

    escribir(
        f"  Encabezados alineados: "
        f"{resultado['headerMatchCount']}"
    )

    escribir(
        f"  Encabezados únicos: "
        f"{resultado['headerUniqueCount']}"
    )

    escribir(
        f"  Distancia vertical al Consumo: "
        f"{resultado['headerDistanceAbove']:.6f}"
    )

    encabezados = resultado[
        "headers"
    ]

    valores = resultado[
        "values"
    ]

    subtitulo(
        "VALIDACIÓN 16 × 16"
    )

    escribir(
        f"Cantidad de encabezados: "
        f"{len(encabezados)}"
    )

    escribir(
        f"Cantidad de valores Consumo: "
        f"{len(valores)}"
    )

    if len(
        encabezados
    ) != 16:

        raise RuntimeError(
            "No se obtuvieron exactamente "
            "16 encabezados."
        )

    if len(
        valores
    ) != 16:

        raise RuntimeError(
            "No se obtuvieron exactamente "
            "16 valores."
        )

    escribir(
        "[OK] 16 encabezados y 16 valores."
    )

    # --------------------------------------------------------
    # Mostrar encabezados antes de las tasas
    # --------------------------------------------------------

    escribir()
    escribir(
        "Encabezados detectados:"
    )

    for indice, encabezado in enumerate(
        encabezados,
        start=1
    ):

        escribir(
            f"  {indice:02d}. "
            f"{encabezado}"
        )

    # --------------------------------------------------------
    # Tabla solicitada
    # --------------------------------------------------------

    titulo(
        "RESULTADO: CONSUMO MN - 30/06/2020"
    )

    escribir(
        "banco | tasa_consumo_mn"
    )

    escribir(
        "-" * 80
    )

    for registro in resultado[
        "registros"
    ]:

        banco = limpiar_texto(
            registro[
                "header"
            ]
        )

        valor = limpiar_texto(
            registro[
                "rawValue"
            ]
        )

        # Vacío sigue siendo faltante.
        # No se reemplaza por cero.
        if valor == "":

            valor_mostrar = (
                "<VACIO>"
            )

        else:

            # "-", "s.i.", etc. permanecen
            # exactamente como aparecen.
            valor_mostrar = valor

        escribir(
            f"{banco} | "
            f"{valor_mostrar}"
        )

    escribir()
    escribir(
        "NOTA:"
    )

    escribir(
        "Promedio se conserva como el "
        "encabezado número 16 porque esta "
        "es una prueba estructural completa."
    )

    escribir(
        "No se está considerando Promedio "
        "como uno de los cinco bancos finales."
    )

    escribir(
        "Los faltantes no se convirtieron "
        "a cero y no se interpolaron."
    )


# ============================================================
# 22. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    try:

        titulo(
            "PRUEBA DE EXTRACCIÓN CONTROLADA "
            "CONSUMO MN - 30/06/2020"
        )

        escribir(
            "Se consultará únicamente "
            "30/06/2020."
        )

        escribir()
        escribir(
            "Objetivo:"
        )

        escribir(
            "Demostrar qué fila numérica "
            "de DataZone corresponde "
            "exactamente a la etiqueta "
            "externa Consumo."
        )

        escribir()
        escribir(
            "NO se consultarán otros meses."
        )

        escribir(
            "NO se descargarán 211 meses."
        )

        escribir(
            "NO se seleccionarán los "
            "cinco bancos finales."
        )

        escribir(
            "NO se interpolarán valores."
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

        # ====================================================
        # POST
        # ====================================================

        titulo(
            "CONSULTAR"
        )

        consultar(
            navegador
        )

        # ----------------------------------------------------
        # Volver a comprobar explícitamente
        # que el resultado es 2020.
        # ----------------------------------------------------

        confirmaciones = (
            buscar_confirmacion_periodo(
                navegador
            )
        )

        if not confirmaciones:

            raise RuntimeError(
                "FECHA_RESULTADO_NO_CONFIRMADA"
            )

        escribir()
        escribir(
            "[OK] El resultado histórico "
            "sigue confirmado como "
            "'al 30/06/2020'."
        )

        # ====================================================
        # COMPROBAR SOLO LAS TABLAS MN
        # ====================================================

        titulo(
            "COMPROBACIÓN DE ESTRUCTURA MN"
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
            f"Tabla MN externa encontrada: "
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
        # RECONSTRUCCIÓN
        # ====================================================

        titulo(
            "RECONSTRUCCIÓN DE FILAS"
        )

        resultado = reconstruir_consumo(
            navegador
        )

        if not resultado.get(
            "ok",
            False
        ):

            escribir(
                f"ERROR DEL MAPE0: "
                f"{resultado.get('error')}"
            )

            if resultado.get(
                "mappings"
            ):

                mostrar_mapeos(
                    resultado
                )

            raise RuntimeError(
                resultado.get(
                    "error",
                    "ERROR_MAPEO_DESCONOCIDO"
                )
            )

        mostrar_mapeos(
            resultado
        )

        mostrar_consumo(
            resultado
        )

        # ====================================================
        # CLASIFICACIÓN FINAL
        # ====================================================

        titulo(
            "CLASIFICACIÓN FINAL DE LA PRUEBA"
        )

        escribir(
            "ESTADO = "
            "EXTRACCION_CONSUMO_MN_2020_VALIDADA"
        )

        escribir()
        escribir(
            "La etiqueta externa 'Consumo' "
            "fue relacionada con una única "
            "fila numérica de DataZone mediante "
            "alineación geométrica vertical."
        )

        escribir(
            "No se utilizó un offset fijo "
            "de filas."
        )

        escribir(
            "Los 16 encabezados fueron "
            "relacionados con las 16 celdas "
            "de la fila mediante alineación "
            "horizontal."
        )

        escribir(
            "El período fue confirmado "
            "independientemente mediante "
            "el texto visible "
            "'al 30/06/2020'."
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
            "No se considerará validada "
            "la extracción mientras exista "
            "este error."
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
        print("=" * 120)
        print("PRUEBA FINALIZADA")
        print("=" * 120)

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