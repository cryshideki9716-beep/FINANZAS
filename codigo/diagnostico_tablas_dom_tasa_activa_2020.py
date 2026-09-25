# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico DOM histórico SBS - ubicación real de tabla Consumo MN - 30/06/2020

from pathlib import Path
from datetime import datetime
import base64
import hashlib
import json
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
    / "diagnostico_tablas_dom_tasa_activa_2020.txt"
)

ARCHIVO_HTML = (
    CARPETA_SALIDA
    / "tasa_activa_2020_dom_post.html"
)

ARCHIVO_PNG = (
    CARPETA_SALIDA
    / "tasa_activa_2020_dom_post.png"
)


# ============================================================
# 2. CONTROLES CONOCIDOS DE LA PÁGINA INICIAL
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

# IDs modernos conocidos.
# SOLO se registran.
# NO se usan para decidir qué tabla es histórica.
ID_MN_EXTERNA_MODERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

ID_MN_DATAZONE_MODERNA = (
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
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# 5. CHROME
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
    m = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})"
        r"(?!\d)",
        valor
    )

    if m:

        dia = int(m.group(1))
        mes = int(m.group(2))
        anio = int(m.group(3))

        try:

            return datetime(
                anio,
                mes,
                dia
            ).date()

        except ValueError:

            return None

    # YYYY-MM-DD
    m = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        valor
    )

    if m:

        anio = int(m.group(1))
        mes = int(m.group(2))
        dia = int(m.group(3))

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

    try:

        return limpiar_texto(
            elemento.get_attribute(
                "value"
            )
        )

    except Exception:

        return None


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
# 11. ESTADO DE FECHA
# ============================================================

def estado_fecha(
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
# 12. CAMBIAR FECHA POR TECLADO
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
# 13. FALLBACK TELERIK
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
# 14. ESTABLECER FECHA ESTRICTAMENTE
# ============================================================

def establecer_fecha(
    navegador
):

    cambiar_fecha_teclado(
        navegador
    )

    estado = estado_fecha(
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

    escribir(
        f"Visible interpretada: "
        f"{estado['visible']}"
    )

    escribir(
        f"Interna interpretada: "
        f"{estado['interna']}"
    )

    if estado[
        "ambas_ok"
    ]:

        escribir(
            "[OK] DatePicker validado."
        )

        return

    escribir()
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

    estado = estado_fecha(
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
# 15. VALIDAR MN Y B
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
# 17. DETECTAR RESULTADO "al 30/06/2020"
# ============================================================

def buscar_confirmacion_periodo(
    navegador
):
    """
    El DatePicker NO cuenta.

    Busca texto visible que contenga:

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

                const style =
                    window.getComputedStyle(el);

                if (
                    style.display === 'none'
                    ||
                    style.visibility === 'hidden'
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

                if (texto.length > 500) {
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
# 18. PULSAR CONSULTAR Y ESPERAR PERÍODO CONFIRMADO
# ============================================================

def consultar_2020(
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

        raise TimeoutException(
            "No apareció texto visible "
            "'al 30/06/2020'."
        )

    escribir()
    escribir(
        "[OK] Período histórico confirmado:"
    )

    for item in confirmaciones:

        escribir(
            f"  {item}"
        )

    # Dar tiempo a que termine de renderizar.
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

    return confirmaciones


# ============================================================
# 19. HTML + SHA
# ============================================================

def obtener_html_y_hash(
    navegador
):

    html = navegador.page_source

    sha = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    return html, sha


# ============================================================
# 20. SCREENSHOT
# ============================================================

def guardar_screenshot(
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

        ARCHIVO_PNG.write_bytes(
            base64.b64decode(
                resultado[
                    "data"
                ]
            )
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
                "SELENIUM_VIEWPORT"
            )

        except Exception as error2:

            return (
                False,
                f"{error!r} / {error2!r}"
            )


# ============================================================
# 21. ENUMERAR TODAS LAS TABLAS DEL DOM
# ============================================================

def enumerar_tablas_dom(
    navegador
):
    """
    Este es el núcleo del diagnóstico.

    Analiza TODAS las tablas después del POST.

    No extrae tasas:
    las celdas numéricas se sustituyen por
    <NUMERICO> en las muestras de texto.
    """

    script = r"""
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

    function esNumerico(txt) {

        txt = limpiar(txt);

        if (!txt) {
            return false;
        }

        const especiales = [
            '-',
            's.i.',
            's.i',
            'n.d.',
            'nd',
            'n/a'
        ];

        if (
            especiales.includes(
                normalizar(txt)
            )
        ) {
            return true;
        }

        const limpio = txt
            .replace(/%/g, '')
            .replace(/,/g, '.')
            .trim();

        return (
            /^[-+]?\d+(\.\d+)?$/
            .test(limpio)
        );
    }

    function estaVisible(el) {

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

        if (
            rect.width <= 0
            ||
            rect.height <= 0
        ) {
            return false;
        }

        return true;
    }

    function columnasLogicas(fila) {

        if (!fila) {
            return 0;
        }

        let total = 0;

        for (
            const celda
            of Array.from(fila.cells)
        ) {

            total += (
                celda.colSpan || 1
            );
        }

        return total;
    }

    function celdasPropias(tabla) {

        const salida = [];

        for (
            let i = 0;
            i < tabla.rows.length;
            i++
        ) {

            const fila =
                tabla.rows[i];

            for (
                let j = 0;
                j < fila.cells.length;
                j++
            ) {

                const celda =
                    fila.cells[j];

                /*
                Evitar que una celda contenedora
                de otra tabla se interprete como
                la fila real Consumo.
                */
                const tablasHijas =
                    celda.querySelectorAll(
                        ':scope > table'
                    );

                if (
                    tablasHijas.length > 0
                ) {
                    continue;
                }

                salida.push({
                    row:
                        i,

                    col:
                        j,

                    text:
                        limpiar(
                            celda.innerText
                            ||
                            celda.textContent
                        )
                });
            }
        }

        return salida;
    }

    function contieneTexto(
        texto,
        buscado
    ) {

        return normalizar(texto)
            .includes(
                normalizar(buscado)
            );
    }

    const tablas =
        Array.from(
            document.querySelectorAll(
                'table'
            )
        );

    const resultado = [];

    for (
        let indice = 0;
        indice < tablas.length;
        indice++
    ) {

        const tabla =
            tablas[indice];

        const visible =
            estaVisible(
                tabla
            );

        const textoCompleto =
            limpiar(
                tabla.innerText
                ||
                tabla.textContent
            );

        const celdas =
            celdasPropias(
                tabla
            );

        const consumoExacto =
            celdas.filter(
                x =>
                normalizar(
                    x.text
                ) === 'consumo'
            );

        const comercioExacto =
            celdas.filter(
                x =>
                normalizar(
                    x.text
                ) === 'comercio'
            );

        const aztecaExacto =
            celdas.filter(
                x =>
                normalizar(
                    x.text
                ) === 'azteca'
            );

        const alfinExacto =
            celdas.filter(
                x =>
                normalizar(
                    x.text
                ) === 'alfin'
            );

        const bankChinaExacto =
            celdas.filter(
                x =>
                normalizar(
                    x.text
                ) === 'bank of china'
            );

        /*
        También registramos presencia por
        substring por si el encabezado tiene
        texto adicional.
        */

        const contieneComercio =
            contieneTexto(
                textoCompleto,
                'Comercio'
            );

        const contieneAzteca =
            contieneTexto(
                textoCompleto,
                'Azteca'
            );

        const contieneAlfin =
            contieneTexto(
                textoCompleto,
                'Alfin'
            );

        const contieneBankChina =
            contieneTexto(
                textoCompleto,
                'Bank of China'
            );

        let maxColumnas = 0;

        for (
            const fila
            of Array.from(
                tabla.rows
            )
        ) {

            maxColumnas = Math.max(
                maxColumnas,
                columnasLogicas(
                    fila
                )
            );
        }

        /*
        Primeros encabezados/textos.
        Los valores numéricos se enmascaran.
        */

        const primerasFilas = [];

        const limiteFilas =
            Math.min(
                tabla.rows.length,
                8
            );

        for (
            let i = 0;
            i < limiteFilas;
            i++
        ) {

            const fila =
                tabla.rows[i];

            const textos = [];

            const limiteCeldas =
                Math.min(
                    fila.cells.length,
                    30
                );

            for (
                let j = 0;
                j < limiteCeldas;
                j++
            ) {

                const txt =
                    limpiar(
                        fila.cells[j].innerText
                        ||
                        fila.cells[j].textContent
                    );

                if (
                    esNumerico(txt)
                ) {

                    textos.push(
                        '<NUMERICO>'
                    );

                } else {

                    /*
                    Limitar textos gigantes de
                    celdas contenedoras.
                    */

                    if (
                        txt.length > 180
                    ) {

                        textos.push(
                            txt.slice(
                                0,
                                180
                            )
                            + '...'
                        );

                    } else {

                        textos.push(
                            txt
                        );
                    }
                }
            }

            primerasFilas.push({
                row:
                    i,

                cells:
                    textos
            });
        }

        /*
        Encabezados puramente textuales.
        */

        const encabezados = [];

        for (
            const celda
            of celdas
        ) {

            if (!celda.text) {
                continue;
            }

            if (
                esNumerico(
                    celda.text
                )
            ) {
                continue;
            }

            const clave =
                normalizar(
                    celda.text
                );

            if (
                !encabezados.some(
                    x =>
                    normalizar(x)
                    === clave
                )
            ) {

                encabezados.push(
                    celda.text
                );
            }

            if (
                encabezados.length >= 40
            ) {
                break;
            }
        }

        /*
        Tabla padre, si existe.
        */

        const padreTabla =
            tabla.parentElement
            ? tabla.parentElement
                .closest('table')
            : null;

        /*
        Puntaje diagnóstico.
        NO es selección de bancos.
        */

        let score = 0;

        if (visible) {
            score += 20;
        }

        if (
            consumoExacto.length === 1
        ) {
            score += 40;
        }

        if (contieneComercio) {
            score += 20;
        }

        if (contieneAzteca) {
            score += 20;
        }

        if (contieneAlfin) {
            score -= 10;
        }

        if (contieneBankChina) {
            score -= 10;
        }

        resultado.push({
            domIndex:
                indice,

            id:
                tabla.id || '',

            className:
                typeof tabla.className
                === 'string'
                ? tabla.className
                : '',

            visible:
                visible,

            rows:
                tabla.rows.length,

            maxLogicalColumns:
                maxColumnas,

            parentTableId:
                padreTabla
                ? (
                    padreTabla.id
                    || '<SIN_ID>'
                )
                : null,

            outerHtmlLength:
                tabla.outerHTML.length,

            exactConsumoCount:
                consumoExacto.length,

            consumoLocations:
                consumoExacto,

            exactComercioCount:
                comercioExacto.length,

            exactAztecaCount:
                aztecaExacto.length,

            exactAlfinCount:
                alfinExacto.length,

            exactBankOfChinaCount:
                bankChinaExacto.length,

            containsComercio:
                contieneComercio,

            containsAzteca:
                contieneAzteca,

            containsAlfin:
                contieneAlfin,

            containsBankOfChina:
                contieneBankChina,

            headersAndTexts:
                encabezados,

            firstRowsMasked:
                primerasFilas,

            diagnosticScore:
                score
        });
    }

    return resultado;
    """

    return navegador.execute_script(
        script
    )


# ============================================================
# 22. CLASIFICAR TABLAS CANDIDATAS
# ============================================================

def clasificar_tablas(
    tablas,
    periodo_confirmado
):
    """
    Una tabla NO puede clasificarse como histórica
    si el período 30/06/2020 no fue confirmado.

    Candidata histórica fuerte:
      - visible
      - exactamente 1 Consumo
      - Comercio y/o Azteca
      - resultado al 30/06/2020 confirmado

    Alfin / Bank of China se registran como
    señales de estructura moderna, no como
    prohibición automática absoluta.
    """

    candidatas = []

    for tabla in tablas:

        if not periodo_confirmado:

            estado = (
                "PERIODO_NO_CONFIRMADO"
            )

        elif (
            tabla[
                "visible"
            ]
            and
            tabla[
                "exactConsumoCount"
            ] == 1
            and
            (
                tabla[
                    "containsComercio"
                ]
                or
                tabla[
                    "containsAzteca"
                ]
            )
        ):

            estado = (
                "CANDIDATA_HISTORICA_FUERTE"
            )

        elif (
            tabla[
                "visible"
            ]
            and
            tabla[
                "exactConsumoCount"
            ] == 1
        ):

            estado = (
                "CONSUMO_VISIBLE_SIN_MARCADOR_HISTORICO"
            )

        elif (
            not tabla[
                "visible"
            ]
            and
            tabla[
                "exactConsumoCount"
            ] == 1
        ):

            estado = (
                "CONSUMO_EN_TABLA_OCULTA"
            )

        elif (
            tabla[
                "containsAlfin"
            ]
            or
            tabla[
                "containsBankOfChina"
            ]
        ):

            estado = (
                "ESTRUCTURA_CON_MARCADORES_MODERNOS"
            )

        else:

            estado = (
                "NO_CANDIDATA"
            )

        tabla[
            "clasificacion"
        ] = estado

        if estado == (
            "CANDIDATA_HISTORICA_FUERTE"
        ):

            candidatas.append(
                tabla
            )

    # --------------------------------------------------------
    # Identificar candidata principal SOLO si es posible.
    # --------------------------------------------------------

    candidata_principal = None
    resolucion = None

    if not periodo_confirmado:

        resolucion = (
            "PERIODO_NO_CONFIRMADO"
        )

    elif len(
        candidatas
    ) == 0:

        resolucion = (
            "NO_SE_IDENTIFICO_TABLA_HISTORICA"
        )

    else:

        # Orden:
        # 1. mayor score
        # 2. visible
        # 3. tabla más específica/pequeña
        ordenadas = sorted(
            candidatas,
            key=lambda x: (
                -x[
                    "diagnosticScore"
                ],
                x[
                    "outerHtmlLength"
                ],
            )
        )

        mejor = ordenadas[
            0
        ]

        if (
            len(
                ordenadas
            ) == 1
        ):

            candidata_principal = mejor

            resolucion = (
                "TABLA_HISTORICA_IDENTIFICADA"
            )

        else:

            # Si la mejor supera en score
            # claramente a la segunda.
            segunda = ordenadas[
                1
            ]

            if (
                mejor[
                    "diagnosticScore"
                ]
                >
                segunda[
                    "diagnosticScore"
                ]
            ):

                candidata_principal = mejor

                resolucion = (
                    "TABLA_HISTORICA_IDENTIFICADA"
                )

            else:

                # No forzar conclusión.
                resolucion = (
                    "MULTIPLES_CANDIDATAS_HISTORICAS"
                )

    return (
        tablas,
        candidatas,
        candidata_principal,
        resolucion,
    )


# ============================================================
# 23. MOSTRAR UNA TABLA
# ============================================================

def mostrar_tabla(
    tabla
):

    escribir(
        f"DOM index: "
        f"{tabla['domIndex']}"
    )

    escribir(
        f"ID: "
        f"{tabla['id']!r}"
    )

    escribir(
        f"Clases: "
        f"{tabla['className']!r}"
    )

    escribir(
        f"Visible: "
        f"{tabla['visible']}"
    )

    escribir(
        f"Tabla padre: "
        f"{tabla['parentTableId']!r}"
    )

    escribir(
        f"Filas: "
        f"{tabla['rows']}"
    )

    escribir(
        f"Máximo columnas lógicas: "
        f"{tabla['maxLogicalColumns']}"
    )

    escribir(
        f"Longitud outerHTML: "
        f"{tabla['outerHtmlLength']}"
    )

    escribir(
        f"Consumo exacto: "
        f"{tabla['exactConsumoCount']}"
    )

    escribir(
        f"Ubicación(es) Consumo: "
        f"{tabla['consumoLocations']}"
    )

    escribir(
        f"Contiene Comercio: "
        f"{tabla['containsComercio']} "
        f"(exactos={tabla['exactComercioCount']})"
    )

    escribir(
        f"Contiene Azteca: "
        f"{tabla['containsAzteca']} "
        f"(exactos={tabla['exactAztecaCount']})"
    )

    escribir(
        f"Contiene Alfin: "
        f"{tabla['containsAlfin']} "
        f"(exactos={tabla['exactAlfinCount']})"
    )

    escribir(
        f"Contiene Bank of China: "
        f"{tabla['containsBankOfChina']} "
        f"(exactos={tabla['exactBankOfChinaCount']})"
    )

    escribir(
        f"Puntaje diagnóstico: "
        f"{tabla['diagnosticScore']}"
    )

    escribir(
        f"Clasificación: "
        f"{tabla['clasificacion']}"
    )

    escribir()
    escribir(
        "Primeros encabezados/textos "
        "no numéricos:"
    )

    if tabla[
        "headersAndTexts"
    ]:

        for texto in tabla[
            "headersAndTexts"
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
        "Primeras filas "
        "(valores numéricos enmascarados):"
    )

    for fila in tabla[
        "firstRowsMasked"
    ]:

        escribir(
            f"  Fila {fila['row']}: "
            f"{fila['cells']}"
        )


# ============================================================
# 24. GUARDAR HTML
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
# 25. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None

    try:

        titulo(
            "DIAGNÓSTICO DOM DE TODAS LAS TABLAS "
            "- SBS - 30/06/2020"
        )

        escribir(
            "Objetivo:"
        )

        escribir(
            "Identificar qué tabla del DOM "
            "contiene realmente la fila histórica "
            "visible de Consumo correspondiente "
            "al 30/06/2020."
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

        estado_pre = estado_fecha(
            navegador
        )

        if not estado_pre[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "DatePicker no validado."
            )

        escribir()
        escribir(
            "[OK] Fecha visible e interna "
            "son exactamente 30/06/2020."
        )

        # ====================================================
        # POST
        # ====================================================

        titulo(
            "CONSULTAR 30/06/2020"
        )

        confirmaciones = consultar_2020(
            navegador
        )

        periodo_confirmado = (
            len(
                confirmaciones
            )
            > 0
        )

        if not periodo_confirmado:

            raise RuntimeError(
                "FECHA_RESULTADO_NO_CONFIRMADA"
            )

        # ====================================================
        # CAPTURA POST
        # ====================================================

        html_post, sha_post = (
            obtener_html_y_hash(
                navegador
            )
        )

        guardar_html(
            html_post
        )

        screenshot_ok, screenshot_metodo = (
            guardar_screenshot(
                navegador
            )
        )

        titulo(
            "ESTADO POST-CONSULTA"
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
            f"SHA-256 HTML post: "
            f"{sha_post}"
        )

        escribir(
            f"Período al 30/06/2020 "
            f"confirmado: "
            f"{periodo_confirmado}"
        )

        escribir(
            f"Screenshot guardado: "
            f"{screenshot_ok}"
        )

        escribir(
            f"Método screenshot: "
            f"{screenshot_metodo}"
        )

        escribir(
            f"HTML guardado en: "
            f"{ARCHIVO_HTML}"
        )

        escribir(
            f"PNG guardado en: "
            f"{ARCHIVO_PNG}"
        )

        # ====================================================
        # ENUMERAR TODAS LAS TABLAS
        # ====================================================

        titulo(
            "ENUMERACIÓN COMPLETA DE TABLAS DEL DOM"
        )

        tablas = enumerar_tablas_dom(
            navegador
        )

        (
            tablas,
            candidatas,
            candidata_principal,
            resolucion,
        ) = clasificar_tablas(
            tablas,
            periodo_confirmado
        )

        escribir(
            f"Cantidad total de tablas: "
            f"{len(tablas)}"
        )

        escribir()

        for numero, tabla in enumerate(
            tablas,
            start=1
        ):

            escribir()
            escribir(
                "=" * 110
            )

            escribir(
                f"TABLA DOM #{numero}"
            )

            escribir(
                "=" * 110
            )

            mostrar_tabla(
                tabla
            )

        # ====================================================
        # TABLAS QUE CONTIENEN CONSUMO
        # ====================================================

        titulo(
            "TABLAS CON CELDA EXACTA 'CONSUMO'"
        )

        tablas_consumo = [
            tabla
            for tabla in tablas
            if tabla[
                "exactConsumoCount"
            ] > 0
        ]

        escribir(
            f"Cantidad: "
            f"{len(tablas_consumo)}"
        )

        for tabla in tablas_consumo:

            escribir()
            escribir(
                f"DOM index="
                f"{tabla['domIndex']} | "
                f"id={tabla['id']!r} | "
                f"visible={tabla['visible']} | "
                f"Consumo={tabla['exactConsumoCount']} | "
                f"Comercio={tabla['containsComercio']} | "
                f"Azteca={tabla['containsAzteca']} | "
                f"Alfin={tabla['containsAlfin']} | "
                f"Bank of China="
                f"{tabla['containsBankOfChina']} | "
                f"clasificación="
                f"{tabla['clasificacion']}"
            )

        # ====================================================
        # COMPARAR IDs MODERNOS
        # ====================================================

        titulo(
            "DIAGNÓSTICO ESPECÍFICO DE LOS IDs MODERNOS"
        )

        for id_moderno in [
            ID_MN_EXTERNA_MODERNA,
            ID_MN_DATAZONE_MODERNA,
        ]:

            encontradas = [
                tabla
                for tabla in tablas
                if tabla[
                    "id"
                ] == id_moderno
            ]

            escribir()
            escribir(
                f"ID: {id_moderno}"
            )

            if not encontradas:

                escribir(
                    "  <NO EXISTE>"
                )

                continue

            for tabla in encontradas:

                escribir(
                    f"  Visible: "
                    f"{tabla['visible']}"
                )

                escribir(
                    f"  Consumo exacto: "
                    f"{tabla['exactConsumoCount']}"
                )

                escribir(
                    f"  Comercio: "
                    f"{tabla['containsComercio']}"
                )

                escribir(
                    f"  Azteca: "
                    f"{tabla['containsAzteca']}"
                )

                escribir(
                    f"  Alfin: "
                    f"{tabla['containsAlfin']}"
                )

                escribir(
                    f"  Bank of China: "
                    f"{tabla['containsBankOfChina']}"
                )

                escribir(
                    f"  Clasificación: "
                    f"{tabla['clasificacion']}"
                )

        # ====================================================
        # CANDIDATAS HISTÓRICAS
        # ====================================================

        titulo(
            "CANDIDATAS A TABLA HISTÓRICA REAL"
        )

        escribir(
            f"Candidatas fuertes: "
            f"{len(candidatas)}"
        )

        for tabla in candidatas:

            escribir()
            escribir(
                f"DOM index="
                f"{tabla['domIndex']} | "
                f"id={tabla['id']!r} | "
                f"visible={tabla['visible']} | "
                f"filas={tabla['rows']} | "
                f"columnas={tabla['maxLogicalColumns']} | "
                f"Comercio={tabla['containsComercio']} | "
                f"Azteca={tabla['containsAzteca']} | "
                f"Alfin={tabla['containsAlfin']} | "
                f"Bank of China="
                f"{tabla['containsBankOfChina']} | "
                f"score={tabla['diagnosticScore']}"
            )

        # ====================================================
        # RESOLUCIÓN
        # ====================================================

        titulo(
            "RESOLUCIÓN DEL DIAGNÓSTICO"
        )

        escribir(
            f"Estado: "
            f"{resolucion}"
        )

        if candidata_principal is not None:

            escribir()
            escribir(
                "TABLA HISTÓRICA PRINCIPAL "
                "IDENTIFICADA:"
            )

            escribir(
                f"DOM index: "
                f"{candidata_principal['domIndex']}"
            )

            escribir(
                f"ID: "
                f"{candidata_principal['id']!r}"
            )

            escribir(
                f"Clases: "
                f"{candidata_principal['className']!r}"
            )

            escribir(
                f"Visible: "
                f"{candidata_principal['visible']}"
            )

            escribir(
                f"Filas: "
                f"{candidata_principal['rows']}"
            )

            escribir(
                f"Columnas lógicas: "
                f"{candidata_principal['maxLogicalColumns']}"
            )

            escribir(
                f"Consumo exacto: "
                f"{candidata_principal['exactConsumoCount']}"
            )

            escribir(
                f"Comercio: "
                f"{candidata_principal['containsComercio']}"
            )

            escribir(
                f"Azteca: "
                f"{candidata_principal['containsAzteca']}"
            )

            escribir(
                f"Alfin: "
                f"{candidata_principal['containsAlfin']}"
            )

            escribir(
                f"Bank of China: "
                f"{candidata_principal['containsBankOfChina']}"
            )

            escribir()
            escribir(
                "Primeros encabezados/textos:"
            )

            for texto in candidata_principal[
                "headersAndTexts"
            ]:

                escribir(
                    f"  {texto!r}"
                )

        elif resolucion == (
            "MULTIPLES_CANDIDATAS_HISTORICAS"
        ):

            escribir()
            escribir(
                "Hay más de una tabla compatible "
                "con la estructura histórica."
            )

            escribir(
                "NO se seleccionó automáticamente "
                "ninguna."
            )

        else:

            escribir()
            escribir(
                "No se identificó inequívocamente "
                "una tabla histórica con los "
                "criterios actuales."
            )

        # ====================================================
        # RESUMEN COMPACTO
        # ====================================================

        titulo(
            "RESUMEN COMPACTO"
        )

        escribir(
            f"Fecha resultado confirmada: "
            f"{periodo_confirmado}"
        )

        escribir(
            f"Total tablas DOM: "
            f"{len(tablas)}"
        )

        escribir(
            f"Tablas con Consumo exacto: "
            f"{len(tablas_consumo)}"
        )

        escribir(
            f"Candidatas históricas fuertes: "
            f"{len(candidatas)}"
        )

        escribir(
            f"Resolución: "
            f"{resolucion}"
        )

        if candidata_principal:

            escribir(
                f"ID histórica principal: "
                f"{candidata_principal['id']!r}"
            )

            escribir(
                f"DOM index histórica principal: "
                f"{candidata_principal['domIndex']}"
            )

        escribir()
        escribir(
            "IMPORTANTE:"
        )

        escribir(
            "No se extrajo ninguna tasa."
        )

        escribir(
            "Los valores numéricos de las "
            "primeras filas fueron enmascarados "
            "como <NUMERICO>."
        )

        escribir(
            "Los IDs modernos no fueron usados "
            "para decidir qué tabla corresponde "
            "al resultado histórico."
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

                html, _ = obtener_html_y_hash(
                    navegador
                )

                guardar_html(
                    html
                )

                guardar_screenshot(
                    navegador
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
        print("=" * 120)
        print("DIAGNÓSTICO FINALIZADO")
        print("=" * 120)

        print()
        print("TXT:")
        print(ARCHIVO_TXT)

        print()
        print("HTML POST:")
        print(ARCHIVO_HTML)

        print()
        print("PNG POST:")
        print(ARCHIVO_PNG)


# ============================================================
# 26. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()