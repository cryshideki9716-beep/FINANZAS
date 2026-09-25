# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico de inicio de disponibilidad histórica - Consumo MN SBS

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

# SOLO ESTAS CUATRO FECHAS
FECHAS_CONTROL = [
    "30/06/2016",
    "30/06/2017",
    "30/06/2018",
    "30/06/2019",
]

TIMEOUT = 50
TIMEOUT_MANUAL = 180

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "diagnostico_inicio_disponibilidad_consumo_mn.txt"
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

# Tabla completa MN confirmada en 2020
ID_TABLA_MN_EXTERNA = (
    "ctl00_cphContent_rpgActualMn_OT"
)

# DataZone MN confirmada en 2020
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
# 5. CREAR NAVEGADOR
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
# 7. COMPROBAR PÁGINA BASE SBS
# ============================================================

def pagina_base_real(
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
            pagina_base_real(d)
        )

        escribir(
            "[OK] Página SBS base cargada."
        )

        return True

    except TimeoutException:

        escribir()
        escribir(
            "La página SBS real todavía "
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
# 11. VALIDAR MN Y B PRE-CONSULTA
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
# 12. ESTADO DEL DATEPICKER
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

        "visible_ok":
            visible == objetivo,

        "interna_ok":
            interna == objetivo,

        "ambas_ok":
            (
                visible == objetivo
                and
                interna == objetivo
            ),
    }


# ============================================================
# 13. CAMBIAR FECHA CON TECLADO
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
        fecha
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
# 15. ESTABLECER FECHA ESTRICTAMENTE
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
        f"Fecha visible: "
        f"{estado['visible_texto']!r}"
    )

    escribir(
        f"Fecha interna: "
        f"{estado['interna_texto']!r}"
    )

    escribir(
        f"Visible exacta: "
        f"{estado['visible_ok']}"
    )

    escribir(
        f"Interna exacta: "
        f"{estado['interna_ok']}"
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
# 17. BUSCAR TEXTO "al DD/MM/YYYY"
# ============================================================

def buscar_confirmacion_periodo(
    navegador,
    fecha
):
    """
    El DatePicker NO cuenta como confirmación.

    Busca texto visible del resultado
    que contenga exactamente:

        al DD/MM/YYYY
    """

    try:

        candidatos = navegador.execute_script(
            """
            const fecha = arguments[0];

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
                    texto.length > 500
                ) {
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

    except Exception:

        candidatos = []

    patron = re.compile(
        rf"\bal\s+{re.escape(fecha)}\b",
        flags=re.IGNORECASE
    )

    confirmados = []

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

        confirmados.append({
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

    return confirmados


# ============================================================
# 18. CONSULTAR Y ESPERAR CONFIRMACIÓN
# ============================================================

def consultar_fecha(
    navegador,
    fecha
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
                navegador,
                fecha
            )
        )

        if confirmaciones:

            break

        time.sleep(
            0.25
        )

    if confirmaciones:

        # Dar margen para que el grid termine
        # de actualizarse.
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

    return confirmaciones


# ============================================================
# 19. ANALIZAR ESTRUCTURA MN
# ============================================================

def analizar_estructura_mn(
    navegador
):
    """
    NO extrae tasas.

    Diagnostica únicamente:

      - existencia/visibilidad tabla MN;
      - existencia/visibilidad DataZone;
      - cantidad exacta de etiquetas Consumo;
      - encabezados históricos de DataZone;
      - cantidad de bancos;
      - existencia de Promedio.

    El número de columnas es dinámico.
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

            const estilo =
                window.getComputedStyle(
                    actual
                );

            if (
                estilo.display === 'none'
                ||
                estilo.visibility === 'hidden'
                ||
                Number(estilo.opacity) === 0
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

        const normal =
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
            faltantes.has(normal)
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

        selectedHeaderRowCellCount:
            null
    };

    // --------------------------------------------------------
    // 1. BUSCAR CONSUMO SOLO EN LA ESTRUCTURA EXTERNA
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

            /*
            No contar celdas de la DataZone.
            */

            if (
                dataZone
                &&
                dataZone.contains(celda)
            ) {
                continue;
            }

            /*
            Evitar celdas contenedoras de
            subtablas.
            */

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
    // 2. DETECTAR FILA DE ENCABEZADOS EN DATAZONE
    //
    // No exigimos un número fijo de columnas.
    // Escogemos la fila visible con mayor
    // cantidad de textos no numéricos.
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

                /*
                Evitar celdas contenedoras
                de tablas internas.
                */

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

            // Dedupe preservando orden.
            const unicos = [];

            const vistos =
                new Set();

            for (
                const texto
                of textos
            ) {

                const clave =
                    normalizar(
                        texto
                    );

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

                    totalCells:
                        celdas.length,

                    textCount:
                        unicos.length,

                    texts:
                        unicos
                });
            }
        }

        /*
        Priorizar:
        1. mayor cantidad de textos;
        2. mayor cantidad de celdas;
        3. fila más cercana al inicio.
        */

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
                    b.totalCells
                    !==
                    a.totalCells
                ) {

                    return (
                        b.totalCells
                        -
                        a.totalCells
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

            resultado.selectedHeaderRowCellCount =
                mejor.totalCells;

            resultado.rawHeaders =
                mejor.texts;

            /*
            Separar Promedio del conteo de
            bancos.

            NO usamos lista fija de bancos.
            */

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
                    normalizar(
                        texto
                    );

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

    return navegador.execute_script(
        script,
        ID_TABLA_MN_EXTERNA,
        ID_DATAZONE_MN,
    )


# ============================================================
# 20. RECARGAR URL BASE ANTES DE CADA FECHA
# ============================================================

def cargar_base(
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
            "No se pudo cargar la página SBS base."
        )


# ============================================================
# 21. DIAGNOSTICAR UNA FECHA
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
            "NO_DISPONIBLE",

        "error":
            None,

        "periodo_confirmado":
            False,

        "tabla_mn_existe":
            False,

        "tabla_mn_visible":
            False,

        "datazone_existe":
            False,

        "datazone_visible":
            False,

        "consumo_count":
            0,

        "encabezados_bancarios":
            [],

        "cantidad_bancos":
            0,

        "promedio":
            False,
    }

    try:

        # ----------------------------------------------------
        # 1. NUEVA CARGA BASE
        # ----------------------------------------------------

        escribir(
            "Recargando URL base..."
        )

        cargar_base(
            navegador
        )

        # ----------------------------------------------------
        # 2. VALIDAR MN Y B
        # ----------------------------------------------------

        subtitulo(
            "CONFIGURACIÓN PRE-CONSULTA"
        )

        validar_mn_b(
            navegador
        )

        # ----------------------------------------------------
        # 3. FECHA VISIBLE E INTERNA
        # ----------------------------------------------------

        subtitulo(
            "DATEPICKER"
        )

        establecer_fecha(
            navegador,
            fecha
        )

        estado_fecha = (
            obtener_estado_fecha(
                navegador,
                fecha
            )
        )

        if not estado_fecha[
            "ambas_ok"
        ]:

            raise RuntimeError(
                "FECHA_PRECONSULTA_INVALIDA"
            )

        # Validación final MN/B antes del POST.
        validar_mn_b(
            navegador
        )

        # ----------------------------------------------------
        # 4. CONSULTAR
        # ----------------------------------------------------

        subtitulo(
            "CONSULTAR"
        )

        confirmaciones = (
            consultar_fecha(
                navegador,
                fecha
            )
        )

        periodo_confirmado = (
            len(
                confirmaciones
            )
            > 0
        )

        resultado[
            "periodo_confirmado"
        ] = periodo_confirmado

        escribir(
            f"Período confirmado mediante "
            f"'al {fecha}': "
            f"{periodo_confirmado}"
        )

        if confirmaciones:

            escribir(
                "Fuentes de confirmación:"
            )

            for item in confirmaciones:

                escribir(
                    f"  tag={item['tag']!r} | "
                    f"id={item['id']!r} | "
                    f"text={item['text']!r}"
                )

        else:

            escribir(
                "No apareció confirmación "
                "explícita del período."
            )

        # ----------------------------------------------------
        # 5. ANALIZAR ESTRUCTURA
        # ----------------------------------------------------

        subtitulo(
            "ESTRUCTURA MN"
        )

        estructura = analizar_estructura_mn(
            navegador
        )

        resultado[
            "tabla_mn_existe"
        ] = estructura[
            "outerExists"
        ]

        resultado[
            "tabla_mn_visible"
        ] = estructura[
            "outerVisible"
        ]

        resultado[
            "datazone_existe"
        ] = estructura[
            "dataExists"
        ]

        resultado[
            "datazone_visible"
        ] = estructura[
            "dataVisible"
        ]

        resultado[
            "consumo_count"
        ] = estructura[
            "consumoCount"
        ]

        resultado[
            "encabezados_bancarios"
        ] = estructura[
            "bankHeaders"
        ]

        resultado[
            "cantidad_bancos"
        ] = estructura[
            "bankCount"
        ]

        resultado[
            "promedio"
        ] = estructura[
            "promedioDetected"
        ]

        escribir(
            f"Tabla MN existe: "
            f"{estructura['outerExists']}"
        )

        escribir(
            f"Tabla MN visible: "
            f"{estructura['outerVisible']}"
        )

        escribir(
            f"DataZone existe: "
            f"{estructura['dataExists']}"
        )

        escribir(
            f"DataZone visible: "
            f"{estructura['dataVisible']}"
        )

        escribir(
            f"Consumo exacto en tabla MN externa: "
            f"{estructura['consumoCount']}"
        )

        escribir(
            f"Ubicación de Consumo: "
            f"{estructura['consumoLocations']}"
        )

        # ----------------------------------------------------
        # 6. ENCABEZADOS
        # ----------------------------------------------------

        subtitulo(
            "ENCABEZADOS HISTÓRICOS DETECTADOS"
        )

        escribir(
            f"Fila DataZone identificada "
            f"como encabezado: "
            f"{estructura['selectedHeaderRowIndex']}"
        )

        escribir(
            f"Número físico de celdas "
            f"en esa fila: "
            f"{estructura['selectedHeaderRowCellCount']}"
        )

        escribir()
        escribir(
            "Encabezados crudos detectados:"
        )

        if estructura[
            "rawHeaders"
        ]:

            for indice, encabezado in enumerate(
                estructura[
                    "rawHeaders"
                ],
                start=1
            ):

                escribir(
                    f"  {indice:02d}. "
                    f"{encabezado}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        escribir()
        escribir(
            "Encabezados bancarios "
            "(sin Promedio):"
        )

        if estructura[
            "bankHeaders"
        ]:

            for indice, banco in enumerate(
                estructura[
                    "bankHeaders"
                ],
                start=1
            ):

                escribir(
                    f"  {indice:02d}. "
                    f"{banco}"
                )

        else:

            escribir(
                "  <NINGUNO>"
            )

        escribir()
        escribir(
            f"Cantidad de bancos detectados: "
            f"{estructura['bankCount']}"
        )

        escribir(
            f"Promedio detectado: "
            f"{estructura['promedioDetected']}"
        )

        # ----------------------------------------------------
        # 7. CLASIFICACIÓN ESTRICTA
        # ----------------------------------------------------

        disponible = (
            periodo_confirmado
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

        if disponible:

            resultado[
                "estado"
            ] = "DISPONIBLE"

            escribir()
            escribir(
                "CLASIFICACIÓN = DISPONIBLE"
            )

        else:

            resultado[
                "estado"
            ] = "NO_DISPONIBLE"

            escribir()
            escribir(
                "CLASIFICACIÓN = NO_DISPONIBLE"
            )

        escribir()
        escribir(
            "Criterios:"
        )

        escribir(
            f"  Fecha confirmada: "
            f"{periodo_confirmado}"
        )

        escribir(
            f"  Tabla MN existe: "
            f"{estructura['outerExists']}"
        )

        escribir(
            f"  Tabla MN visible: "
            f"{estructura['outerVisible']}"
        )

        escribir(
            f"  DataZone existe: "
            f"{estructura['dataExists']}"
        )

        escribir(
            f"  DataZone visible: "
            f"{estructura['dataVisible']}"
        )

        escribir(
            f"  Consumo exactamente una vez: "
            f"{estructura['consumoCount'] == 1}"
        )

        # Los encabezados se registran,
        # pero NO forman parte del criterio
        # mínimo de disponibilidad solicitado.

        if (
            periodo_confirmado
            and
            estructura[
                "dataExists"
            ]
            and
            estructura[
                "bankCount"
            ]
            == 0
        ):

            escribir()
            escribir(
                "[ADVERTENCIA] "
                "El período y DataZone existen, "
                "pero no se logró reconstruir "
                "la fila de encabezados bancarios."
            )

    except Exception as error:

        resultado[
            "estado"
        ] = "NO_DISPONIBLE"

        resultado[
            "error"
        ] = (
            f"{type(error).__name__}: "
            f"{repr(error)}"
        )

        escribir()
        escribir(
            "[ERROR EN ESTA FECHA]"
        )

        escribir(
            resultado[
                "error"
            ]
        )

        escribir(
            "Se continuará con "
            "la siguiente fecha."
        )

    return resultado


# ============================================================
# 22. RESUMEN FINAL
# ============================================================

def mostrar_resumen(
    resultados
):

    titulo(
        "RESUMEN - INICIO DE DISPONIBILIDAD "
        "HISTÓRICA CONSUMO MN"
    )

    for resultado in resultados:

        escribir()

        escribir(
            f"FECHA: "
            f"{resultado['fecha']}"
        )

        escribir(
            f"  Clasificación: "
            f"{resultado['estado']}"
        )

        escribir(
            f"  Período confirmado: "
            f"{resultado['periodo_confirmado']}"
        )

        escribir(
            f"  Tabla MN existe: "
            f"{resultado['tabla_mn_existe']}"
        )

        escribir(
            f"  Tabla MN visible: "
            f"{resultado['tabla_mn_visible']}"
        )

        escribir(
            f"  DataZone existe: "
            f"{resultado['datazone_existe']}"
        )

        escribir(
            f"  DataZone visible: "
            f"{resultado['datazone_visible']}"
        )

        escribir(
            f"  Consumo exacto: "
            f"{resultado['consumo_count']}"
        )

        escribir(
            f"  Cantidad de bancos: "
            f"{resultado['cantidad_bancos']}"
        )

        escribir(
            f"  Promedio: "
            f"{resultado['promedio']}"
        )

        escribir(
            "  Bancos:"
        )

        if resultado[
            "encabezados_bancarios"
        ]:

            escribir(
                "    "
                +
                " | ".join(
                    resultado[
                        "encabezados_bancarios"
                    ]
                )
            )

        else:

            escribir(
                "    <NO DETECTADOS>"
            )

        if resultado[
            "error"
        ]:

            escribir(
                f"  Error: "
                f"{resultado['error']}"
            )

    # ========================================================
    # TABLA COMPACTA
    # ========================================================

    subtitulo(
        "TABLA COMPACTA"
    )

    escribir(
        "fecha | clasificacion | "
        "fecha_confirmada | "
        "tabla_mn_visible | "
        "datazone_visible | "
        "consumo_exacto | "
        "bancos | promedio"
    )

    for resultado in resultados:

        escribir(
            f"{resultado['fecha']} | "
            f"{resultado['estado']} | "
            f"{resultado['periodo_confirmado']} | "
            f"{resultado['tabla_mn_visible']} | "
            f"{resultado['datazone_visible']} | "
            f"{resultado['consumo_count']} | "
            f"{resultado['cantidad_bancos']} | "
            f"{resultado['promedio']}"
        )

    # ========================================================
    # PRIMERA FECHA DISPONIBLE ENTRE LAS PROBADAS
    # ========================================================

    disponibles = [
        resultado
        for resultado in resultados
        if resultado[
            "estado"
        ]
        == "DISPONIBLE"
    ]

    subtitulo(
        "CONCLUSIÓN DEL DIAGNÓSTICO"
    )

    if disponibles:

        escribir(
            "Primera fecha DISPONIBLE "
            "entre las cuatro fechas "
            "probadas:"
        )

        escribir(
            disponibles[
                0
            ][
                "fecha"
            ]
        )

        escribir()
        escribir(
            "IMPORTANTE:"
        )

        escribir(
            "Esto identifica únicamente "
            "la primera fecha disponible "
            "ENTRE 2016, 2017, 2018 y 2019."
        )

        escribir(
            "Todavía NO demuestra que ese "
            "sea el primer mes histórico "
            "disponible de toda la serie."
        )

    else:

        escribir(
            "Ninguna de las cuatro fechas "
            "probadas cumplió todos los "
            "criterios de DISPONIBLE."
        )

    escribir()
    escribir(
        "No se extrajeron tasas."
    )

    escribir(
        "No se consultaron otros meses."
    )

    escribir(
        "No se descargaron 211 meses."
    )

    escribir(
        "No se seleccionaron bancos finales."
    )

    escribir(
        "No se realizó interpolación."
    )


# ============================================================
# 23. GUARDAR REPORTE
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
# 24. MAIN
# ============================================================

def main():

    navegador = None

    resultados = []

    try:

        titulo(
            "DIAGNÓSTICO DEL INICIO DE "
            "DISPONIBILIDAD HISTÓRICA "
            "- CONSUMO MN"
        )

        escribir(
            "Se consultarán únicamente:"
        )

        for fecha in FECHAS_CONTROL:

            escribir(
                f"  {fecha}"
            )

        escribir()
        escribir(
            "Antes de cada fecha se recargará "
            "la URL base SBS."
        )

        escribir(
            "No se exige un número fijo "
            "de bancos o columnas."
        )

        escribir(
            "Promedio se detectará y se "
            "separará del conteo bancario."
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
        print("=" * 120)
        print("DIAGNÓSTICO FINALIZADO")
        print("=" * 120)

        print()
        print(
            "Resultado guardado en:"
        )

        print(
            ARCHIVO_TXT
        )


# ============================================================
# 25. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()