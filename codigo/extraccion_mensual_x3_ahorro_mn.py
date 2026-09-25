# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict
import csv
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
    NoSuchWindowException,
)


# ============================================================
# 1. IDENTIFICACIÓN
# ============================================================

CODIGO_ESTUDIANTE = "2024200485D"

VARIABLE = (
    "X3 - Tasa pasiva de Depósitos de Ahorro "
    "en Moneda Nacional (%)"
)


# ============================================================
# 2. FUENTE SBS
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIPasivaDepositoEmpresa.aspx?tip=B"
)


# ============================================================
# 3. ESTRUCTURA X3 VALIDADA
#
# Validada en:
#   - prueba 30/11/2015
#   - prueba histórica de 6 puntos
# ============================================================

ID_TABLA_MN = (
    "ctl00_cphContent_rpgActualPrimTablaMn_OT"
)

ID_DATAZONE_MN = (
    "ctl00_cphContent_"
    "rpgActualPrimTablaMn_ctl00_DataZone_DT"
)


# ============================================================
# 4. PERÍODO
# ============================================================

FECHA_INICIO = date(
    2015,
    11,
    1
)

FECHA_CORTE = date(
    2025,
    12,
    31
)


# ============================================================
# 5. CONFIGURACIÓN
# ============================================================

TIMEOUT = 60

TIMEOUT_MANUAL = 180

PAUSA_ENTRE_CONSULTAS = 1.2

# Intento original + máximo un reintento.
MAX_REINTENTOS_TECNICOS = 1

# Permite continuar una extracción interrumpida.
REANUDAR = True

# Conservar HTML de cada mes aceptado.
GUARDAR_HTML_CRUDO = True


# ============================================================
# 6. RUTAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_DATOS_CRUDOS = (
    RAIZ
    / "datos_crudos"
    / f"X3_ahorro_mn_{CODIGO_ESTUDIANTE}"
)

CARPETA_DATOS_PROCESADOS = (
    RAIZ
    / "datos_procesados"
)

CARPETA_DIAGNOSTICOS = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

CSV_DATOS = (
    CARPETA_DATOS_PROCESADOS
    / f"X3_tasa_pasiva_ahorro_mn_{CODIGO_ESTUDIANTE}.csv"
)

CSV_PROMEDIO = (
    CARPETA_DATOS_PROCESADOS
    / f"X3_promedio_ahorro_mn_{CODIGO_ESTUDIANTE}.csv"
)

CSV_AUDITORIA = (
    CARPETA_DIAGNOSTICOS
    / f"auditoria_X3_ahorro_mn_{CODIGO_ESTUDIANTE}.csv"
)

TXT_RESUMEN = (
    CARPETA_DIAGNOSTICOS
    / f"resumen_X3_ahorro_mn_{CODIGO_ESTUDIANTE}.txt"
)


# ============================================================
# 7. COLUMNAS
# ============================================================

COLUMNAS_DATOS = [
    "mes",
    "fecha_sbs",
    "banco_original",
    "tasa_pasiva_ahorro_mn",
]

COLUMNAS_PROMEDIO = [
    "mes",
    "fecha_sbs",
    "promedio_ahorro_mn",
]

COLUMNAS_AUDITORIA = [
    "mes",
    "fecha_calendario_final",
    "fecha_sbs",
    "dias_retrocedidos",
    "cantidad_bancos",
    "cantidad_faltantes_bancos",
    "promedio",
    "estado",
    "html_sha256",
    "fecha_hora_extraccion",
    "detalle",
]


# ============================================================
# 8. EXCEPCIONES
# ============================================================

class ErrorTecnicoX3(Exception):
    """
    Fallo Selenium, parser, controles, etc.

    Nunca debe convertirse en ausencia
    de información SBS.
    """
    pass


class EstructuraX3NoCompatible(Exception):
    """
    SBS confirmó la fecha exacta, pero la
    estructura histórica validada de X3 no
    está presente o visible.

    Tampoco debe producir retroceso de fecha.
    """
    pass


# ============================================================
# 9. TEXTO
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
    Solo para comparaciones internas.

    No se utiliza para modificar
    banco_original.
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


def clave_semantica(valor):

    return re.sub(
        r"[^a-z0-9]",
        "",
        normalizar_texto(
            valor
        )
    )


# ============================================================
# 10. FECHAS
# ============================================================

def fecha_a_texto(fecha):

    return fecha.strftime(
        "%d/%m/%Y"
    )


def fecha_a_iso(fecha):

    return fecha.strftime(
        "%Y-%m-%d"
    )


def mes_a_texto(
    anio,
    mes
):

    return (
        f"{anio:04d}-{mes:02d}"
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
        -
        timedelta(days=1)
    )


def generar_meses(
    inicio,
    corte
):

    meses = []

    anio = inicio.year
    mes = inicio.month

    while (
        anio < corte.year
        or
        (
            anio == corte.year
            and
            mes <= corte.month
        )
    ):

        meses.append(
            (
                anio,
                mes
            )
        )

        if mes == 12:

            anio += 1
            mes = 1

        else:

            mes += 1

    return meses


MESES_A_EXTRAER = generar_meses(
    FECHA_INICIO,
    FECHA_CORTE
)

if len(
    MESES_A_EXTRAER
) != 122:

    raise RuntimeError(
        "El período 2015-11 a 2025-12 "
        "debe contener exactamente 122 meses. "
        f"Se obtuvieron {len(MESES_A_EXTRAER)}."
    )


def convertir_fecha(valor):

    if valor is None:
        return None

    texto = limpiar_texto(
        valor
    )

    if not texto:
        return None

    # DD/MM/YYYY
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})"
        r"(?!\d)",
        texto
    )

    if coincidencia:

        try:

            return date(
                int(
                    coincidencia.group(3)
                ),
                int(
                    coincidencia.group(2)
                ),
                int(
                    coincidencia.group(1)
                ),
            )

        except ValueError:

            return None

    # YYYY-MM-DD
    coincidencia = re.search(
        r"(?<!\d)"
        r"(\d{4})-"
        r"(\d{1,2})-"
        r"(\d{1,2})"
        r"(?!\d)",
        texto
    )

    if coincidencia:

        try:

            return date(
                int(
                    coincidencia.group(1)
                ),
                int(
                    coincidencia.group(2)
                ),
                int(
                    coincidencia.group(3)
                ),
            )

        except ValueError:

            return None

    return None


# ============================================================
# 11. CSV ATÓMICO
# ============================================================

def leer_csv(ruta):

    if not ruta.exists():
        return []

    with ruta.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        return list(
            csv.DictReader(
                archivo
            )
        )


def escribir_csv_atomico(
    ruta,
    columnas,
    filas
):

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporal = ruta.with_suffix(
        ruta.suffix
        + ".tmp"
    )

    with temporal.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
            extrasaction="ignore"
        )

        escritor.writeheader()

        for fila in filas:

            escritor.writerow(
                fila
            )

    temporal.replace(
        ruta
    )


# ============================================================
# 12. CARGAR CHECKPOINT
# ============================================================

def cargar_checkpoint():

    datos_por_mes = defaultdict(
        list
    )

    for fila in leer_csv(
        CSV_DATOS
    ):

        mes = limpiar_texto(
            fila.get(
                "mes",
                ""
            )
        )

        if mes:

            datos_por_mes[
                mes
            ].append(
                fila
            )

    promedio_por_mes = {}

    for fila in leer_csv(
        CSV_PROMEDIO
    ):

        mes = limpiar_texto(
            fila.get(
                "mes",
                ""
            )
        )

        if mes:

            promedio_por_mes[
                mes
            ] = fila

    auditoria_por_mes = {}

    for fila in leer_csv(
        CSV_AUDITORIA
    ):

        mes = limpiar_texto(
            fila.get(
                "mes",
                ""
            )
        )

        if mes:

            auditoria_por_mes[
                mes
            ] = fila

    return (
        datos_por_mes,
        promedio_por_mes,
        auditoria_por_mes,
    )


# ============================================================
# 13. CHECKPOINT ROBUSTO
# ============================================================

def checkpoint_mes_completo(
    mes,
    datos_por_mes,
    promedio_por_mes,
    auditoria_por_mes
):
    """
    Solo dos estados pueden considerarse
    checkpoints completos:

        DISPONIBLE
        MES_SIN_DATO

    ERROR_TECNICO,
    ESTRUCTURA_X3_NO_COMPATIBLE
    o cualquier otro estado => False.
    """

    auditoria = auditoria_por_mes.get(
        mes
    )

    if auditoria is None:

        return False

    if (
        limpiar_texto(
            auditoria.get(
                "mes",
                ""
            )
        )
        != mes
    ):

        return False

    estado = limpiar_texto(
        auditoria.get(
            "estado",
            ""
        )
    )

    filas_mes = datos_por_mes.get(
        mes,
        []
    )

    # ========================================================
    # ERROR TÉCNICO
    # ========================================================

    if estado == "ERROR_TECNICO":

        return False

    # ========================================================
    # ESTRUCTURA INCOMPATIBLE
    # ========================================================

    if (
        estado
        ==
        "ESTRUCTURA_X3_NO_COMPATIBLE"
    ):

        return False

    # ========================================================
    # MES SIN DATO
    # ========================================================

    if estado == "MES_SIN_DATO":

        return (
            len(
                filas_mes
            )
            == 0
            and
            mes not in promedio_por_mes
        )

    # ========================================================
    # DISPONIBLE
    # ========================================================

    if estado == "DISPONIBLE":

        cantidad_texto = limpiar_texto(
            auditoria.get(
                "cantidad_bancos",
                ""
            )
        )

        try:

            cantidad_bancos = int(
                cantidad_texto
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        # cantidad_bancos > 0
        if cantidad_bancos <= 0:

            return False

        # filas == cantidad_bancos
        if (
            len(
                filas_mes
            )
            !=
            cantidad_bancos
        ):

            return False

        # Promedio presente
        if mes not in promedio_por_mes:

            return False

        fecha_sbs_auditoria = limpiar_texto(
            auditoria.get(
                "fecha_sbs",
                ""
            )
        )

        if not fecha_sbs_auditoria:

            return False

        # Todas las filas deben tener
        # exactamente mismo mes + fecha_sbs.
        for fila in filas_mes:

            if (
                limpiar_texto(
                    fila.get(
                        "mes",
                        ""
                    )
                )
                !=
                mes
            ):

                return False

            if (
                limpiar_texto(
                    fila.get(
                        "fecha_sbs",
                        ""
                    )
                )
                !=
                fecha_sbs_auditoria
            ):

                return False

        # Promedio debe coincidir también.
        promedio = promedio_por_mes[
            mes
        ]

        if (
            limpiar_texto(
                promedio.get(
                    "mes",
                    ""
                )
            )
            !=
            mes
        ):

            return False

        if (
            limpiar_texto(
                promedio.get(
                    "fecha_sbs",
                    ""
                )
            )
            !=
            fecha_sbs_auditoria
        ):

            return False

        return True

    return False


# ============================================================
# 14. GUARDAR CHECKPOINT
# ============================================================

def guardar_checkpoint(
    datos_por_mes,
    promedio_por_mes,
    auditoria_por_mes
):

    filas_datos = []

    for mes in sorted(
        datos_por_mes
    ):

        filas_datos.extend(
            datos_por_mes[
                mes
            ]
        )

    filas_promedio = [
        promedio_por_mes[
            mes
        ]
        for mes in sorted(
            promedio_por_mes
        )
    ]

    filas_auditoria = [
        auditoria_por_mes[
            mes
        ]
        for mes in sorted(
            auditoria_por_mes
        )
    ]

    escribir_csv_atomico(
        CSV_DATOS,
        COLUMNAS_DATOS,
        filas_datos
    )

    escribir_csv_atomico(
        CSV_PROMEDIO,
        COLUMNAS_PROMEDIO,
        filas_promedio
    )

    escribir_csv_atomico(
        CSV_AUDITORIA,
        COLUMNAS_AUDITORIA,
        filas_auditoria
    )


# ============================================================
# 15. NAVEGADOR
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
            [
                "enable-logging"
            ]
        )

        navegador = webdriver.Chrome(
            options=opciones
        )

        navegador.set_page_load_timeout(
            TIMEOUT
        )

        return navegador

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo iniciar Chrome/Selenium: "
            f"{type(error).__name__}: {error}"
        ) from error


def esperar_documento(navegador):

    try:

        WebDriverWait(
            navegador,
            TIMEOUT
        ).until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            )
            == "complete"
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se completó la carga "
            "del documento."
        ) from error


# ============================================================
# 16. CONTROLES
# ============================================================

def obtener_controles(navegador):

    try:

        return navegador.execute_script(
            r"""
            const elementos =
                Array.from(
                    document.querySelectorAll(
                        'input,select,button'
                    )
                );

            return elementos.map(el => {

                const style =
                    window.getComputedStyle(el);

                const r =
                    el.getBoundingClientRect();

                return {
                    tag:
                        el.tagName || '',

                    id:
                        el.id || '',

                    name:
                        el.name || '',

                    type:
                        el.type || '',

                    value:
                        (
                            el.value !== undefined
                            ? String(el.value)
                            : ''
                        ),

                    visible:
                        (
                            style.display !== 'none'
                            &&
                            style.visibility !== 'hidden'
                            &&
                            r.width > 0
                            &&
                            r.height > 0
                        )
                };
            });
            """
        ) or []

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudieron leer "
            "los controles SBS."
        ) from error


def info_elemento(elemento):

    return {
        "id":
            limpiar_texto(
                elemento.get_attribute(
                    "id"
                )
            ),

        "name":
            limpiar_texto(
                elemento.get_attribute(
                    "name"
                )
            ),

        "type":
            limpiar_texto(
                elemento.get_attribute(
                    "type"
                )
            ),

        "value":
            limpiar_texto(
                elemento.get_attribute(
                    "value"
                )
            ),
    }


# ============================================================
# 17. DATEPICKER VISIBLE
# ============================================================

def localizar_fecha_visible(navegador):

    selectores = [
        "input[id*='rdpDate'][id$='_dateInput']",
        "input[name*='rdpDate'][name$='$dateInput']",
        "input[id*='Date'][id$='_dateInput']",
    ]

    for selector in selectores:

        elementos = navegador.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for elemento in elementos:

            try:

                if elemento.is_displayed():
                    return elemento

            except Exception:
                continue

    return None


# ============================================================
# 18. DATEPICKER INTERNO
# ============================================================

def localizar_fecha_interna(
    navegador,
    fecha_visible,
    fecha_objetivo
):

    info_visible = info_elemento(
        fecha_visible
    )

    candidatos = []

    id_visible = info_visible[
        "id"
    ]

    name_visible = info_visible[
        "name"
    ]

    if id_visible.endswith(
        "_dateInput"
    ):

        id_base = id_visible[
            :-len(
                "_dateInput"
            )
        ]

        candidatos.extend(
            navegador.find_elements(
                By.ID,
                id_base
            )
        )

    if name_visible.endswith(
        "$dateInput"
    ):

        name_base = name_visible[
            :-len(
                "$dateInput"
            )
        ]

        candidatos.extend(
            navegador.find_elements(
                By.NAME,
                name_base
            )
        )

    vistos = set()

    for elemento in candidatos:

        try:

            info = info_elemento(
                elemento
            )

            clave = (
                info[
                    "id"
                ],
                info[
                    "name"
                ],
            )

            if clave in vistos:
                continue

            vistos.add(
                clave
            )

            if convertir_fecha(
                info[
                    "value"
                ]
            ) is not None:

                return elemento

        except Exception:
            continue

    posibles = []

    for elemento in navegador.find_elements(
        By.CSS_SELECTOR,
        "input"
    ):

        try:

            if elemento == fecha_visible:
                continue

            info = info_elemento(
                elemento
            )

            combinado = clave_semantica(
                info[
                    "id"
                ]
                + " "
                + info[
                    "name"
                ]
            )

            if (
                "date" not in combinado
                and
                "fecha" not in combinado
            ):
                continue

            fecha = convertir_fecha(
                info[
                    "value"
                ]
            )

            if fecha is None:
                continue

            posibles.append(
                elemento
            )

        except Exception:
            continue

    objetivos = []

    for elemento in posibles:

        try:

            fecha = convertir_fecha(
                elemento.get_attribute(
                    "value"
                )
            )

            if fecha == fecha_objetivo:

                objetivos.append(
                    elemento
                )

        except Exception:
            continue

    if len(
        objetivos
    ) == 1:

        return objetivos[
            0
        ]

    if len(
        posibles
    ) == 1:

        return posibles[
            0
        ]

    return None


# ============================================================
# 19. MONEDA / ENTIDAD
# ============================================================

def seleccionar_control_contexto(
    controles,
    tipo
):

    if tipo == "moneda":

        esperado = "MN"

        palabras = [
            "moneda",
            "tipomoneda",
            "currency",
        ]

    elif tipo == "entidad":

        esperado = "B"

        palabras = [
            "entidad",
            "tipoentidad",
            "entity",
        ]

    else:

        raise ValueError(
            "Tipo de control desconocido."
        )

    candidatos = []

    for control in controles:

        valor = limpiar_texto(
            control.get(
                "value",
                ""
            )
        ).upper()

        if valor != esperado:
            continue

        combinado = clave_semantica(
            control.get(
                "id",
                ""
            )
            + " "
            + control.get(
                "name",
                ""
            )
        )

        puntaje = 0

        for palabra in palabras:

            if clave_semantica(
                palabra
            ) in combinado:

                puntaje += 100

        if (
            limpiar_texto(
                control.get(
                    "type",
                    ""
                )
            ).lower()
            == "hidden"
        ):

            puntaje += 3

        candidatos.append({
            "control":
                control,

            "puntaje":
                puntaje,
        })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x:
        x[
            "puntaje"
        ],
        reverse=True
    )

    mejor = candidatos[
        0
    ]

    mejores = [
        item
        for item in candidatos
        if item[
            "puntaje"
        ]
        == mejor[
            "puntaje"
        ]
    ]

    if (
        mejor[
            "puntaje"
        ]
        > 0
        and
        len(
            mejores
        )
        == 1
    ):

        return mejor[
            "control"
        ]

    if len(
        candidatos
    ) == 1:

        return candidatos[
            0
        ][
            "control"
        ]

    return None


# ============================================================
# 20. BOTÓN CONSULTAR
# ============================================================

def localizar_boton_consultar(navegador):

    candidatos = []

    for elemento in navegador.find_elements(
        By.CSS_SELECTOR,
        "input,button"
    ):

        try:

            if not elemento.is_displayed():
                continue

            info = info_elemento(
                elemento
            )

            combinado = normalizar_texto(
                info[
                    "id"
                ]
                + " "
                + info[
                    "name"
                ]
                + " "
                + info[
                    "value"
                ]
                + " "
                + elemento.text
            )

            if (
                "consultar" in combinado
                or
                "btnconsultar" in combinado
            ):

                candidatos.append(
                    elemento
                )

        except Exception:
            continue

    if len(
        candidatos
    ) == 1:

        return candidatos[
            0
        ]

    return None


# ============================================================
# 21. PÁGINA REAL
# ============================================================

def pagina_real(navegador):

    try:

        return (
            localizar_fecha_visible(
                navegador
            )
            is not None
            and
            localizar_boton_consultar(
                navegador
            )
            is not None
        )

    except Exception:
        return False


def asegurar_pagina_real(navegador):

    try:

        WebDriverWait(
            navegador,
            15
        ).until(
            lambda d:
            pagina_real(
                d
            )
        )

        return

    except TimeoutException:

        print()
        print(
            "La página SBS real todavía "
            "no fue detectada."
        )

        print(
            "Si aparece una verificación "
            "de seguridad, complétala manualmente."
        )

        print()

        input(
            "Cuando aparezca la página real, "
            "presiona ENTER..."
        )

    try:

        WebDriverWait(
            navegador,
            TIMEOUT_MANUAL
        ).until(
            lambda d:
            pagina_real(
                d
            )
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se recuperó la página SBS real."
        ) from error


def cargar_base(navegador):

    try:

        navegador.get(
            URL
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo cargar SBS."
        ) from error

    esperar_documento(
        navegador
    )

    time.sleep(
        1.5
    )

    asegurar_pagina_real(
        navegador
    )


# ============================================================
# 22. ESTABLECER FECHA
# ============================================================

def establecer_fecha(
    navegador,
    fecha_objetivo
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_NO_LOCALIZADO"
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

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo escribir la fecha."
        ) from error

    time.sleep(
        1
    )

    campo = localizar_fecha_visible(
        navegador
    )

    interno = localizar_fecha_interna(
        navegador,
        campo,
        fecha_objetivo
    )

    fecha_visible = convertir_fecha(
        campo.get_attribute(
            "value"
        )
    )

    fecha_interna = None

    if interno is not None:

        fecha_interna = convertir_fecha(
            interno.get_attribute(
                "value"
            )
        )

    if (
        fecha_visible == fecha_objetivo
        and
        fecha_interna == fecha_objetivo
    ):

        return

    # ========================================================
    # FALLBACK TELERIK
    # ========================================================

    info = info_elemento(
        campo
    )

    id_visible = info[
        "id"
    ]

    if not id_visible.endswith(
        "_dateInput"
    ):

        raise ErrorTecnicoX3(
            "NO_PUEDE_DERIVARSE_PICKER_TELERIK"
        )

    id_picker = id_visible[
        :-len(
            "_dateInput"
        )
    ]

    try:

        resultado = navegador.execute_script(
            """
            try {

                if (
                    typeof $find === 'undefined'
                ) {
                    return 'NO_$find';
                }

                const picker =
                    $find(
                        arguments[0]
                    );

                if (!picker) {
                    return 'NO_PICKER';
                }

                const fecha =
                    new Date(
                        arguments[1],
                        arguments[2] - 1,
                        arguments[3]
                    );

                picker.set_selectedDate(
                    fecha
                );

                if (
                    picker.get_dateInput
                ) {

                    const entrada =
                        picker.get_dateInput();

                    if (
                        entrada
                        &&
                        entrada.set_value
                    ) {

                        entrada.set_value(
                            arguments[4]
                        );
                    }
                }

                return 'OK';

            } catch (e) {

                return (
                    'ERROR|' +
                    e.toString()
                );
            }
            """,
            id_picker,
            fecha_objetivo.year,
            fecha_objetivo.month,
            fecha_objetivo.day,
            texto_fecha,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "Falló fallback Telerik."
        ) from error

    if resultado != "OK":

        raise ErrorTecnicoX3(
            f"Telerik devolvió {resultado!r}"
        )

    time.sleep(
        1
    )


# ============================================================
# 23. VALIDAR CONTEXTO
# ============================================================

def validar_contexto(
    navegador,
    fecha_objetivo
):

    visible = localizar_fecha_visible(
        navegador
    )

    if visible is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_VISIBLE_NO_LOCALIZADO"
        )

    fecha_visible = convertir_fecha(
        visible.get_attribute(
            "value"
        )
    )

    interno = localizar_fecha_interna(
        navegador,
        visible,
        fecha_objetivo
    )

    if interno is None:

        raise ErrorTecnicoX3(
            "DATEPICKER_INTERNO_NO_LOCALIZADO"
        )

    fecha_interna = convertir_fecha(
        interno.get_attribute(
            "value"
        )
    )

    if (
        fecha_visible != fecha_objetivo
        or
        fecha_interna != fecha_objetivo
    ):

        raise ErrorTecnicoX3(
            "FECHA_VISIBLE_O_INTERNA_INVALIDA"
        )

    controles = obtener_controles(
        navegador
    )

    moneda = seleccionar_control_contexto(
        controles,
        "moneda"
    )

    entidad = seleccionar_control_contexto(
        controles,
        "entidad"
    )

    if moneda is None:

        raise ErrorTecnicoX3(
            "CONTROL_MONEDA_NO_UNIVOCO"
        )

    if entidad is None:

        raise ErrorTecnicoX3(
            "CONTROL_ENTIDAD_NO_UNIVOCO"
        )

    if (
        limpiar_texto(
            moneda.get(
                "value",
                ""
            )
        ).upper()
        != "MN"
    ):

        raise ErrorTecnicoX3(
            "MONEDA_NO_ES_MN"
        )

    if (
        limpiar_texto(
            entidad.get(
                "value",
                ""
            )
        ).upper()
        != "B"
    ):

        raise ErrorTecnicoX3(
            "ENTIDAD_NO_ES_B"
        )


# ============================================================
# 24. CONFIRMACIÓN EXACTA DE PERÍODO
# ============================================================

def buscar_confirmacion_periodo(
    navegador,
    fecha_objetivo
):

    texto_fecha = fecha_a_texto(
        fecha_objetivo
    )

    patron = re.compile(
        rf"\bal\s+"
        rf"{re.escape(texto_fecha)}\b",
        flags=re.IGNORECASE
    )

    try:

        elementos = navegador.execute_script(
            """
            const elementos = Array.from(
                document.querySelectorAll(
                    'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th,strong,b'
                )
            );

            const salida = [];

            for (const el of elementos) {

                const style =
                    window.getComputedStyle(el);

                const r =
                    el.getBoundingClientRect();

                if (
                    style.display === 'none'
                    ||
                    style.visibility === 'hidden'
                    ||
                    r.width <= 0
                    ||
                    r.height <= 0
                ) {
                    continue;
                }

                const texto =
                    (el.innerText || '')
                    .replace(/\\s+/g, ' ')
                    .trim();

                if (
                    texto
                    &&
                    texto.length <= 800
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
            """
        ) or []

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo inspeccionar "
            "el período SBS."
        ) from error

    confirmaciones = []

    vistos = set()

    for item in elementos:

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

        confirmaciones.append(
            item
        )

    return confirmaciones


def buscar_sin_informacion(navegador):

    try:

        texto = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo leer el cuerpo SBS."
        ) from error

    return (
        "no existe informacion "
        "para la fecha elegida"
        in
        normalizar_texto(
            texto
        )
    )


# ============================================================
# 25. CONSULTAR
# ============================================================

def consultar_fecha(
    navegador,
    fecha_objetivo
):

    boton = localizar_boton_consultar(
        navegador
    )

    if boton is None:

        raise ErrorTecnicoX3(
            "BOTON_CONSULTAR_NO_UNIVOCO"
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
            0.4
        )

        boton.click()

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo pulsar Consultar."
        ) from error

    inicio = time.time()

    while (
        time.time()
        -
        inicio
        <
        TIMEOUT
    ):

        sin_info = buscar_sin_informacion(
            navegador
        )

        confirmaciones = buscar_confirmacion_periodo(
            navegador,
            fecha_objetivo
        )

        # SIN_INFORMACION tiene prioridad.
        if sin_info:

            time.sleep(
                0.5
            )

            confirmaciones_finales = (
                buscar_confirmacion_periodo(
                    navegador,
                    fecha_objetivo
                )
            )

            return {
                "respuesta":
                    "SIN_INFORMACION",

                "periodo_confirmado":
                    len(
                        confirmaciones_finales
                    )
                    > 0,
            }

        if confirmaciones:

            time.sleep(
                1.5
            )

            if buscar_sin_informacion(
                navegador
            ):

                return {
                    "respuesta":
                        "SIN_INFORMACION",

                    "periodo_confirmado":
                        True,
                }

            confirmaciones = buscar_confirmacion_periodo(
                navegador,
                fecha_objetivo
            )

            if confirmaciones:

                return {
                    "respuesta":
                        "PERIODO_CONFIRMADO",

                    "periodo_confirmado":
                        True,
                }

        time.sleep(
            0.25
        )

    raise ErrorTecnicoX3(
        "RESPUESTA_SBS_NO_CONFIRMADA"
    )


# ============================================================
# 26. INSPECCIONAR ESTRUCTURA VALIDADA
# ============================================================

def inspeccionar_estructura_validada(
    navegador
):

    try:

        return navegador.execute_script(
            """
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

            const outer =
                document.getElementById(
                    arguments[0]
                );

            const data =
                document.getElementById(
                    arguments[1]
                );

            return {
                outerExists:
                    outer !== null,

                outerVisible:
                    outer
                    ? visible(outer)
                    : false,

                dataExists:
                    data !== null,

                dataVisible:
                    data
                    ? visible(data)
                    : false
            };
            """,
            ID_TABLA_MN,
            ID_DATAZONE_MN,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo inspeccionar "
            "tabla/DataZone X3."
        ) from error


# ============================================================
# 27. EXTRACTOR GEOMÉTRICO X3
#
# MISMA METODOLOGÍA YA VALIDADA.
# ============================================================

def extraer_ahorro_mn(
    navegador
):

    script = r"""
    const OUTER_ID = arguments[0];
    const DATA_ID = arguments[1];

    // ========================================================
    // A. UTILIDADES
    // ========================================================

    function original(el) {

        if (!el) {
            return '';
        }

        return (
            el.innerText
            ||
            el.textContent
            ||
            ''
        )
        .replace(/\u00a0/g, ' ')
        .trim();
    }

    function compacto(txt) {

        return (txt || '')
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normal(txt) {

        return compacto(txt)
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

    function esNumero(txt) {

        const t =
            compacto(txt);

        if (!t) {
            return false;
        }

        const numero =
            t
            .replace(/%/g, '')
            .replace(/,/g, '.')
            .trim();

        return (
            /^[-+]?\d+(?:\.\d+)?$/
            .test(numero)
        );
    }

    function esFaltante(txt) {

        const n =
            normal(txt);

        const faltantes =
            new Set([
                '',
                '-',
                '–',
                '—',
                's.i.',
                's.i',
                'n.d.',
                'n.d',
                'nd',
                'n/a',
                'na',
                'n.i.',
                'n.i',
                's/d',
                'sd'
            ]);

        return faltantes.has(
            n
        );
    }

    function esFaltanteExplicito(txt) {

        const n =
            normal(txt);

        const faltantes =
            new Set([
                '-',
                '–',
                '—',
                's.i.',
                's.i',
                'n.d.',
                'n.d',
                'nd',
                'n/a',
                'na',
                'n.i.',
                'n.i',
                's/d',
                'sd'
            ]);

        return faltantes.has(
            n
        );
    }

    function esValorTasa(txt) {

        return (
            esNumero(txt)
            ||
            esFaltante(txt)
        );
    }

    function terminalConTexto(
        elemento,
        textoNormal
    ) {

        const descendientes =
            Array.from(
                elemento.querySelectorAll(
                    'td,th,span,label,div'
                )
            );

        for (
            const hijo
            of descendientes
        ) {

            if (
                hijo === elemento
                ||
                !visible(hijo)
            ) {
                continue;
            }

            if (
                normal(
                    hijo.innerText
                    ||
                    hijo.textContent
                )
                ===
                textoNormal
            ) {

                return false;
            }
        }

        return true;
    }

    // ========================================================
    // B. TABLAS REALES VALIDADAS
    // ========================================================

    const outer =
        document.getElementById(
            OUTER_ID
        );

    const data =
        document.getElementById(
            DATA_ID
        );

    if (!outer) {

        return {
            ok:
                false,

            error:
                'TABLA_CONTENEDORA_MN_NO_EXISTE'
        };
    }

    if (!data) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_EXISTE'
        };
    }

    if (!visible(outer)) {

        return {
            ok:
                false,

            error:
                'TABLA_CONTENEDORA_MN_NO_VISIBLE'
        };
    }

    if (!visible(data)) {

        return {
            ok:
                false,

            error:
                'DATAZONE_MN_NO_VISIBLE'
        };
    }

    const rectData =
        rectInfo(
            data
        );

    // ========================================================
    // C. EXACTAMENTE UNA ETIQUETA DEPÓSITOS DE AHORRO
    // ========================================================

    const etiquetasAhorro = [];

    const elementosOuter =
        Array.from(
            outer.querySelectorAll(
                'td,th,span,label,div'
            )
        );

    for (
        const el
        of elementosOuter
    ) {

        if (!visible(el)) {
            continue;
        }

        const texto =
            original(el);

        if (
            normal(texto)
            !==
            'depositos de ahorro'
        ) {
            continue;
        }

        if (
            !terminalConTexto(
                el,
                'depositos de ahorro'
            )
        ) {
            continue;
        }

        etiquetasAhorro.push({
            element:
                el,

            text:
                texto,

            tag:
                el.tagName,

            id:
                el.id || '',

            rect:
                rectInfo(el),

            tableId:
                (
                    el.closest('table')
                    &&
                    el.closest('table').id
                )
                ||
                ''
        });
    }

    if (
        etiquetasAhorro.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'DEPOSITOS_AHORRO_NO_UNIVOCO',

            ahorroCount:
                etiquetasAhorro.length
        };
    }

    const etiquetaAhorro =
        etiquetasAhorro[0];

    // ========================================================
    // D. FILAS NUMÉRICAS
    // ========================================================

    const filasDOM =
        Array.from(
            data.querySelectorAll(
                'tr'
            )
        )
        .filter(
            fila =>
                fila.closest('table')
                === data
        );

    const filasNumericas = [];

    for (
        let i = 0;
        i < filasDOM.length;
        i++
    ) {

        const fila =
            filasDOM[i];

        if (!visible(fila)) {
            continue;
        }

        const celdas =
            Array.from(
                fila.children
            )
            .filter(
                celda =>
                    (
                        celda.tagName === 'TD'
                        ||
                        celda.tagName === 'TH'
                    )
                    &&
                    visible(celda)
            );

        if (
            celdas.length < 2
        ) {
            continue;
        }

        const valores =
            celdas.map(
                celda =>
                    original(
                        celda
                    )
            );

        const todosValores =
            valores.every(
                valor =>
                    esValorTasa(
                        valor
                    )
            );

        const tieneContenidoInformativo =
            valores.some(
                valor =>
                    esNumero(
                        valor
                    )
                    ||
                    esFaltanteExplicito(
                        valor
                    )
            );

        if (
            todosValores
            &&
            tieneContenidoInformativo
        ) {

            filasNumericas.push({
                index:
                    i,

                element:
                    fila,

                cells:
                    celdas,

                values:
                    valores,

                rect:
                    rectInfo(
                        fila
                    )
            });
        }
    }

    if (
        filasNumericas.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_SE_DETECTARON_FILAS_NUMERICAS'
        };
    }

    // ========================================================
    // E. COLUMNA DEPÓSITOS DE AHORRO POR GEOMETRÍA
    // ========================================================

    const mapeosColumna = [];

    for (
        const fila
        of filasNumericas
    ) {

        const candidatos = [];

        for (
            let j = 0;
            j < fila.cells.length;
            j++
        ) {

            const celda =
                fila.cells[j];

            const rect =
                rectInfo(
                    celda
                );

            const overlap =
                overlapHorizontal(
                    etiquetaAhorro.rect,
                    rect
                );

            const distancia =
                Math.abs(
                    etiquetaAhorro
                    .rect
                    .centerX
                    -
                    rect.centerX
                );

            const contieneCentro =
                (
                    etiquetaAhorro
                    .rect
                    .centerX
                    >=
                    rect.left
                    &&
                    etiquetaAhorro
                    .rect
                    .centerX
                    <=
                    rect.right
                );

            candidatos.push({
                index:
                    j,

                overlap:
                    overlap,

                distancia:
                    distancia,

                contieneCentro:
                    contieneCentro,

                rect:
                    rect
            });
        }

        candidatos.sort(
            (a, b) => {

                if (
                    Number(
                        b.contieneCentro
                    )
                    !==
                    Number(
                        a.contieneCentro
                    )
                ) {

                    return (
                        Number(
                            b.contieneCentro
                        )
                        -
                        Number(
                            a.contieneCentro
                        )
                    );
                }

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

        const mejor =
            candidatos[0];

        if (!mejor) {

            return {
                ok:
                    false,

                error:
                    'COLUMNA_AHORRO_NO_MAPEADA'
            };
        }

        if (
            !mejor.contieneCentro
            &&
            mejor.overlap < 0.25
        ) {

            return {
                ok:
                    false,

                error:
                    'ALINEACION_HORIZONTAL_AHORRO_INSUFICIENTE',

                fila:
                    fila.index,

                overlap:
                    mejor.overlap,

                distancia:
                    mejor.distancia
            };
        }

        // ====================================================
        // PROTECCIÓN DE AMBIGÜEDAD VALIDADA
        // ====================================================

        if (
            candidatos.length > 1
        ) {

            const segundo =
                candidatos[1];

            const empateCentro =
                (
                    mejor.contieneCentro
                    ===
                    segundo.contieneCentro
                );

            const empateOverlap =
                Math.abs(
                    mejor.overlap
                    -
                    segundo.overlap
                )
                <
                0.000001;

            const empateDistancia =
                Math.abs(
                    mejor.distancia
                    -
                    segundo.distancia
                )
                <
                0.5;

            if (
                empateCentro
                &&
                empateOverlap
                &&
                empateDistancia
            ) {

                return {
                    ok:
                        false,

                    error:
                        'COLUMNA_AHORRO_AMBIGUA',

                    fila:
                        fila.index,

                    mejor:
                        {
                            index:
                                mejor.index,

                            contieneCentro:
                                mejor.contieneCentro,

                            overlap:
                                mejor.overlap,

                            distancia:
                                mejor.distancia
                        },

                    segundo:
                        {
                            index:
                                segundo.index,

                            contieneCentro:
                                segundo.contieneCentro,

                            overlap:
                                segundo.overlap,

                            distancia:
                                segundo.distancia
                        }
                };
            }
        }

        mapeosColumna.push({
            rowIndex:
                fila.index,

            columnIndex:
                mejor.index,

            value:
                fila.values[
                    mejor.index
                ],

            overlap:
                mejor.overlap,

            distance:
                mejor.distancia,

            containsCenter:
                mejor.contieneCentro
        });
    }

    // ========================================================
    // F. MISMA COLUMNA EN TODAS LAS FILAS
    // ========================================================

    const indicesColumna =
        Array.from(
            new Set(
                mapeosColumna.map(
                    x =>
                        x.columnIndex
                )
            )
        );

    if (
        indicesColumna.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'INDICE_COLUMNA_AHORRO_INCONSISTENTE',

            columnIndices:
                indicesColumna,

            mappings:
                mapeosColumna
        };
    }

    const indiceColumnaAhorro =
        indicesColumna[0];

    // ========================================================
    // G. CANDIDATOS DE NOMBRES EXTERNOS
    // ========================================================

    const excluidos =
        new Set([
            'depositos de ahorro',
            'depositos a plazo',
            'depositos cts',
            'hasta 30 dias',
            '31-90 dias',
            '91-180 dias',
            '181-360 dias',
            'mas de 360 dias',
            'moneda nacional',
            'moneda extranjera',
            'empresa',
            'empresas',
            'tasa',
            'tasas',
            '%'
        ]);

    const candidatosNombre = [];

    for (
        const el
        of elementosOuter
    ) {

        if (!visible(el)) {
            continue;
        }

        if (
            data.contains(
                el
            )
        ) {
            continue;
        }

        const texto =
            original(
                el
            );

        const n =
            normal(
                texto
            );

        if (!n) {
            continue;
        }

        if (
            excluidos.has(
                n
            )
        ) {
            continue;
        }

        if (
            n.includes(
                'tasas pasivas'
            )
            ||
            n.includes(
                'ultimos 30 dias'
            )
            ||
            n.includes(
                'tipo de deposito'
            )
        ) {
            continue;
        }

        if (
            !terminalConTexto(
                el,
                n
            )
        ) {
            continue;
        }

        if (
            esNumero(
                texto
            )
            ||
            esFaltante(
                texto
            )
        ) {
            continue;
        }

        const rect =
            rectInfo(
                el
            );

        const estaALaIzquierda =
            (
                rect.centerX
                <
                rectData.left
                +
                40
            );

        candidatosNombre.push({
            element:
                el,

            text:
                texto,

            normal:
                n,

            tag:
                el.tagName,

            id:
                el.id || '',

            rect:
                rect,

            estaALaIzquierda:
                estaALaIzquierda,

            tableId:
                (
                    el.closest('table')
                    &&
                    el.closest('table').id
                )
                ||
                ''
        });
    }

    if (
        candidatosNombre.length === 0
    ) {

        return {
            ok:
                false,

            error:
                'NO_HAY_CANDIDATOS_DE_NOMBRES'
        };
    }

    // ========================================================
    // H. MAPEO VERTICAL NOMBRE -> FILA
    // ========================================================

    const filasMapeadas = [];

    for (
        const fila
        of filasNumericas
    ) {

        const candidatos = [];

        for (
            const nombre
            of candidatosNombre
        ) {

            const overlap =
                overlapVertical(
                    fila.rect,
                    nombre.rect
                );

            if (
                overlap < 0.50
            ) {
                continue;
            }

            const distanciaVertical =
                Math.abs(
                    fila.rect.centerY
                    -
                    nombre.rect.centerY
                );

            const distanciaHorizontal =
                Math.max(
                    0,
                    rectData.left
                    -
                    nombre.rect.right
                );

            let score =
                overlap
                *
                1000;

            if (
                nombre.estaALaIzquierda
            ) {

                score += 100;
            }

            score -= (
                distanciaVertical
                *
                10
            );

            score -= (
                distanciaHorizontal
                /
                100
            );

            candidatos.push({
                nombre:
                    nombre,

                overlap:
                    overlap,

                distanciaVertical:
                    distanciaVertical,

                distanciaHorizontal:
                    distanciaHorizontal,

                score:
                    score
            });
        }

        candidatos.sort(
            (a, b) =>
                b.score
                -
                a.score
        );

        if (
            candidatos.length === 0
        ) {

            return {
                ok:
                    false,

                error:
                    'FILA_NUMERICA_SIN_NOMBRE',

                rowIndex:
                    fila.index
            };
        }

        const mejor =
            candidatos[0];

        if (
            candidatos.length > 1
        ) {

            const segundo =
                candidatos[1];

            if (
                Math.abs(
                    mejor.score
                    -
                    segundo.score
                )
                <
                0.001
            ) {

                return {
                    ok:
                        false,

                    error:
                        'NOMBRE_DE_FILA_AMBIGUO',

                    rowIndex:
                        fila.index,

                    candidato1:
                        mejor.nombre.text,

                    candidato2:
                        segundo.nombre.text
                };
            }
        }

        const valorAhorro =
            fila.values[
                indiceColumnaAhorro
            ];

        filasMapeadas.push({
            dataRowIndex:
                fila.index,

            banco_original:
                mejor.nombre.text,

            bancoTag:
                mejor.nombre.tag,

            bancoId:
                mejor.nombre.id,

            bancoTableId:
                mejor.nombre.tableId,

            verticalOverlap:
                mejor.overlap,

            tasa:
                valorAhorro,

            faltante:
                esFaltante(
                    valorAhorro
                ),

            esPromedio:
                normal(
                    mejor.nombre.text
                )
                ===
                'promedio'
        });
    }

    // ========================================================
    // I. NOMBRES ÚNICOS
    // ========================================================

    const clavesNombre =
        filasMapeadas.map(
            x =>
                normal(
                    x.banco_original
                )
        );

    const nombresUnicos =
        new Set(
            clavesNombre
        );

    if (
        nombresUnicos.size
        !==
        filasMapeadas.length
    ) {

        return {
            ok:
                false,

            error:
                'NOMBRES_MAPEADOS_NO_UNICOS',

            names:
                clavesNombre
        };
    }

    // ========================================================
    // J. PROMEDIO
    // ========================================================

    const promedios =
        filasMapeadas.filter(
            x =>
                x.esPromedio
        );

    if (
        promedios.length
        !== 1
    ) {

        return {
            ok:
                false,

            error:
                'PROMEDIO_NO_UNIVOCO',

            promedioCount:
                promedios.length
        };
    }

    const promedio =
        promedios[0];

    const bancos =
        filasMapeadas.filter(
            x =>
                !x.esPromedio
        );

    // ========================================================
    // K. VALIDACIONES DE CANTIDAD
    // ========================================================

    const totalValoresObjetivo =
        mapeosColumna.length;

    const totalFilasMapeadas =
        filasMapeadas.length;

    if (
        totalFilasMapeadas
        !==
        totalValoresObjetivo
    ) {

        return {
            ok:
                false,

            error:
                'NUMERO_NOMBRES_DISTINTO_DE_VALORES',

            totalNames:
                totalFilasMapeadas,

            totalValues:
                totalValoresObjetivo
        };
    }

    if (
        bancos.length
        +
        1
        !==
        totalValoresObjetivo
    ) {

        return {
            ok:
                false,

            error:
                'BANCOS_MAS_PROMEDIO_NO_COINCIDEN',

            bankCount:
                bancos.length,

            totalValues:
                totalValoresObjetivo
        };
    }

    // ========================================================
    // L. RESULTADO
    // ========================================================

    return {
        ok:
            true,

        outerId:
            outer.id,

        dataZoneId:
            data.id,

        ahorroLabelCount:
            etiquetasAhorro.length,

        ahorroLabelText:
            etiquetaAhorro.text,

        ahorroLabelId:
            etiquetaAhorro.id,

        ahorroLabelTableId:
            etiquetaAhorro.tableId,

        ahorroColumnIndex:
            indiceColumnaAhorro,

        numericRowCount:
            filasNumericas.length,

        targetValueCount:
            totalValoresObjetivo,

        mappedRowCount:
            totalFilasMapeadas,

        bankCount:
            bancos.length,

        missingBankCount:
            bancos.filter(
                x =>
                    x.faltante
            ).length,

        bancos:
            bancos,

        promedio:
            promedio,

        mappings:
            filasMapeadas,

        columnMappings:
            mapeosColumna
    };
    """

    try:

        resultado = navegador.execute_script(
            script,
            ID_TABLA_MN,
            ID_DATAZONE_MN,
        )

    except Exception as error:

        raise ErrorTecnicoX3(
            "Falló el extractor geométrico X3: "
            f"{error}"
        ) from error

    if not resultado.get(
        "ok",
        False
    ):

        raise ErrorTecnicoX3(
            "El extractor geométrico X3 falló "
            "sobre una estructura presente. "
            f"Detalle={resultado}"
        )

    return resultado


# ============================================================
# 28. EVALUAR UNA FECHA
# ============================================================

def evaluar_dia(
    navegador,
    fecha_objetivo
):
    """
    Únicos resultados normales:

        SIN_INFORMACION
        ESTRUCTURA_X3_NO_COMPATIBLE
        DISPONIBLE

    SOLO SIN_INFORMACION permite retroceder.
    """

    cargar_base(
        navegador
    )

    establecer_fecha(
        navegador,
        fecha_objetivo
    )

    validar_contexto(
        navegador,
        fecha_objetivo
    )

    respuesta = consultar_fecha(
        navegador,
        fecha_objetivo
    )

    # ========================================================
    # SIN INFORMACIÓN
    # ========================================================

    if (
        respuesta[
            "respuesta"
        ]
        ==
        "SIN_INFORMACION"
    ):

        return {
            "estado":
                "SIN_INFORMACION",

            "estructura":
                None,

            "extraccion":
                None,
        }

    # ========================================================
    # PERÍODO CONFIRMADO
    # ========================================================

    if (
        respuesta[
            "respuesta"
        ]
        !=
        "PERIODO_CONFIRMADO"
        or
        not respuesta[
            "periodo_confirmado"
        ]
    ):

        raise ErrorTecnicoX3(
            "PERIODO_EXACTO_NO_CONFIRMADO"
        )

    validar_contexto(
        navegador,
        fecha_objetivo
    )

    # ========================================================
    # ESTRUCTURA
    # ========================================================

    estructura = inspeccionar_estructura_validada(
        navegador
    )

    estructura_compatible = (
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
    )

    if not estructura_compatible:

        return {
            "estado":
                "ESTRUCTURA_X3_NO_COMPATIBLE",

            "estructura":
                estructura,

            "extraccion":
                None,
        }

    # ========================================================
    # PARSER GEOMÉTRICO
    #
    # Cualquier fallo aquí es técnico/parser.
    # ========================================================

    extraccion = extraer_ahorro_mn(
        navegador
    )

    try:

        html = navegador.page_source

    except Exception as error:

        raise ErrorTecnicoX3(
            "No se pudo obtener el HTML "
            "de la fecha válida."
        ) from error

    sha256 = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    return {
        "estado":
            "DISPONIBLE",

        "estructura":
            estructura,

        "extraccion":
            extraccion,

        "html":
            html,

        "sha256":
            sha256,
    }


# ============================================================
# 29. REINTENTO TÉCNICO
# ============================================================

def evaluar_dia_con_reintento(
    navegador,
    fecha_objetivo
):

    errores = []

    total_intentos = (
        1
        +
        MAX_REINTENTOS_TECNICOS
    )

    for numero in range(
        total_intentos
    ):

        try:

            if numero > 0:

                print(
                    "      ↳ reintento técnico "
                    f"{numero}/"
                    f"{MAX_REINTENTOS_TECNICOS}"
                )

                time.sleep(
                    2
                )

            resultado = evaluar_dia(
                navegador,
                fecha_objetivo
            )

            return {
                "ok":
                    True,

                "resultado":
                    resultado,

                "errores":
                    errores,
            }

        except (
            ErrorTecnicoX3,
            TimeoutException,
            WebDriverException,
            StaleElementReferenceException,
            NoSuchWindowException,
        ) as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            errores.append(
                detalle
            )

            print(
                "      [ERROR TÉCNICO] "
                f"{detalle}"
            )

            if (
                numero
                <
                total_intentos - 1
            ):

                continue

            return {
                "ok":
                    False,

                "resultado":
                    None,

                "errores":
                    errores,
            }

        except Exception as error:

            detalle = (
                f"{type(error).__name__}: "
                f"{repr(error)}"
            )

            errores.append(
                detalle
            )

            print(
                "      [ERROR TÉCNICO "
                "NO CLASIFICADO] "
                f"{detalle}"
            )

            if (
                numero
                <
                total_intentos - 1
            ):

                continue

            return {
                "ok":
                    False,

                "resultado":
                    None,

                "errores":
                    errores,
            }

    return {
        "ok":
            False,

        "resultado":
            None,

        "errores":
            errores,
    }


# ============================================================
# 30. PROCESAR MES
# ============================================================

def procesar_mes(
    navegador,
    anio,
    mes
):

    clave_mes = mes_a_texto(
        anio,
        mes
    )

    fecha_final = ultimo_dia_mes(
        anio,
        mes
    )

    fecha_intento = fecha_final

    dias_retrocedidos = 0

    print()
    print(
        "=" * 90
    )

    print(
        f"MES {clave_mes}"
    )

    print(
        "=" * 90
    )

    print(
        "Último día calendario: "
        f"{fecha_a_texto(fecha_final)}"
    )

    while (
        fecha_intento.year == anio
        and
        fecha_intento.month == mes
    ):

        print()
        print(
            "  Probando "
            f"{fecha_a_texto(fecha_intento)} "
            f"(retroceso={dias_retrocedidos})"
        )

        evaluacion = evaluar_dia_con_reintento(
            navegador,
            fecha_intento
        )

        # ====================================================
        # ERROR TÉCNICO
        # ====================================================

        if not evaluacion[
            "ok"
        ]:

            return {
                "estado":
                    "ERROR_TECNICO",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    fecha_intento,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "cantidad_bancos":
                    None,

                "cantidad_faltantes":
                    None,

                "bancos":
                    [],

                "promedio":
                    None,

                "html":
                    None,

                "sha256":
                    None,

                "detalle":
                    " || ".join(
                        evaluacion[
                            "errores"
                        ]
                    ),
            }

        resultado = evaluacion[
            "resultado"
        ]

        estado = resultado[
            "estado"
        ]

        # ====================================================
        # DISPONIBLE
        # ====================================================

        if estado == "DISPONIBLE":

            extraccion = resultado[
                "extraccion"
            ]

            print(
                "      [DISPONIBLE]"
            )

            print(
                "      Fecha SBS: "
                f"{fecha_a_texto(fecha_intento)}"
            )

            print(
                "      Bancos: "
                f"{extraccion['bankCount']}"
            )

            print(
                "      Faltantes: "
                f"{extraccion['missingBankCount']}"
            )

            print(
                "      Promedio: "
                f"{extraccion['promedio']['tasa']!r}"
            )

            return {
                "estado":
                    "DISPONIBLE",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    fecha_intento,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "cantidad_bancos":
                    extraccion[
                        "bankCount"
                    ],

                "cantidad_faltantes":
                    extraccion[
                        "missingBankCount"
                    ],

                "bancos":
                    extraccion[
                        "bancos"
                    ],

                "promedio":
                    extraccion[
                        "promedio"
                    ],

                "html":
                    resultado[
                        "html"
                    ],

                "sha256":
                    resultado[
                        "sha256"
                    ],

                "detalle":
                    (
                        f"tabla={extraccion['outerId']}; "
                        f"datazone={extraccion['dataZoneId']}; "
                        f"nombres_valores="
                        f"{extraccion['mappedRowCount']}; "
                        f"columna_ahorro="
                        f"{extraccion['ahorroColumnIndex']}"
                    ),
            }

        # ====================================================
        # ESTRUCTURA INCOMPATIBLE
        #
        # NO RETROCEDER.
        # ====================================================

        if (
            estado
            ==
            "ESTRUCTURA_X3_NO_COMPATIBLE"
        ):

            estructura = resultado[
                "estructura"
            ]

            print(
                "      [ESTRUCTURA_X3_NO_COMPATIBLE]"
            )

            print(
                "      SBS confirmó la fecha, "
                "pero la estructura validada "
                "no coincide."
            )

            print(
                "      NO se retrocederá."
            )

            return {
                "estado":
                    "ESTRUCTURA_X3_NO_COMPATIBLE",

                "mes":
                    clave_mes,

                "fecha_calendario_final":
                    fecha_final,

                "fecha_sbs":
                    fecha_intento,

                "dias_retrocedidos":
                    dias_retrocedidos,

                "cantidad_bancos":
                    None,

                "cantidad_faltantes":
                    None,

                "bancos":
                    [],

                "promedio":
                    None,

                "html":
                    None,

                "sha256":
                    None,

                "detalle":
                    (
                        f"periodo_confirmado=True; "
                        f"outerExists="
                        f"{estructura['outerExists']}; "
                        f"outerVisible="
                        f"{estructura['outerVisible']}; "
                        f"dataExists="
                        f"{estructura['dataExists']}; "
                        f"dataVisible="
                        f"{estructura['dataVisible']}"
                    ),
            }

        # ====================================================
        # SIN INFORMACIÓN
        #
        # ÚNICO ESTADO QUE AUTORIZA RETROCESO.
        # ====================================================

        if estado == "SIN_INFORMACION":

            print(
                "      SIN_INFORMACION"
            )

            if fecha_intento.day == 1:

                break

            fecha_intento = (
                fecha_intento
                -
                timedelta(days=1)
            )

            dias_retrocedidos += 1

            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

            continue

        raise ErrorTecnicoX3(
            f"Estado diario desconocido: "
            f"{estado}"
        )

    # ========================================================
    # MES SIN DATO
    #
    # Solo si todos los días hasta el día 1
    # fueron SIN_INFORMACION.
    # ========================================================

    print(
        "      [MES_SIN_DATO]"
    )

    return {
        "estado":
            "MES_SIN_DATO",

        "mes":
            clave_mes,

        "fecha_calendario_final":
            fecha_final,

        "fecha_sbs":
            None,

        "dias_retrocedidos":
            fecha_final.day - 1,

        "cantidad_bancos":
            0,

        "cantidad_faltantes":
            0,

        "bancos":
            [],

        "promedio":
            None,

        "html":
            None,

        "sha256":
            None,

        "detalle":
            (
                "Todos los días del mes evaluados "
                "hasta el día 1 devolvieron "
                "SIN_INFORMACION."
            ),
    }


# ============================================================
# 31. CONSTRUIR FILAS PRINCIPALES
# ============================================================

def construir_filas_datos(
    resultado_mes
):

    if (
        resultado_mes[
            "estado"
        ]
        !=
        "DISPONIBLE"
    ):

        return []

    mes = resultado_mes[
        "mes"
    ]

    fecha_sbs = fecha_a_texto(
        resultado_mes[
            "fecha_sbs"
        ]
    )

    filas = []

    for registro in resultado_mes[
        "bancos"
    ]:

        filas.append({
            "mes":
                mes,

            "fecha_sbs":
                fecha_sbs,

            "banco_original":
                registro[
                    "banco_original"
                ],

            # Valor SBS bruto.
            #
            # "-" se conserva.
            # "s.i." se conserva.
            # vacío se conserva.
            "tasa_pasiva_ahorro_mn":
                registro[
                    "tasa"
                ],
        })

    return filas


# ============================================================
# 32. CONSTRUIR PROMEDIO
# ============================================================

def construir_fila_promedio(
    resultado_mes
):

    if (
        resultado_mes[
            "estado"
        ]
        !=
        "DISPONIBLE"
    ):

        return None

    return {
        "mes":
            resultado_mes[
                "mes"
            ],

        "fecha_sbs":
            fecha_a_texto(
                resultado_mes[
                    "fecha_sbs"
                ]
            ),

        "promedio_ahorro_mn":
            resultado_mes[
                "promedio"
            ][
                "tasa"
            ],
    }


# ============================================================
# 33. CONSTRUIR AUDITORÍA
# ============================================================

def construir_fila_auditoria(
    resultado_mes
):

    fecha_sbs = ""

    if resultado_mes[
        "fecha_sbs"
    ] is not None:

        fecha_sbs = fecha_a_texto(
            resultado_mes[
                "fecha_sbs"
            ]
        )

    cantidad_bancos = ""

    if resultado_mes[
        "cantidad_bancos"
    ] is not None:

        cantidad_bancos = str(
            resultado_mes[
                "cantidad_bancos"
            ]
        )

    cantidad_faltantes = ""

    if resultado_mes[
        "cantidad_faltantes"
    ] is not None:

        cantidad_faltantes = str(
            resultado_mes[
                "cantidad_faltantes"
            ]
        )

    promedio = ""

    if resultado_mes[
        "promedio"
    ] is not None:

        promedio = resultado_mes[
            "promedio"
        ][
            "tasa"
        ]

    return {
        "mes":
            resultado_mes[
                "mes"
            ],

        "fecha_calendario_final":
            fecha_a_texto(
                resultado_mes[
                    "fecha_calendario_final"
                ]
            ),

        "fecha_sbs":
            fecha_sbs,

        "dias_retrocedidos":
            str(
                resultado_mes[
                    "dias_retrocedidos"
                ]
            ),

        "cantidad_bancos":
            cantidad_bancos,

        "cantidad_faltantes_bancos":
            cantidad_faltantes,

        "promedio":
            promedio,

        "estado":
            resultado_mes[
                "estado"
            ],

        "html_sha256":
            (
                resultado_mes[
                    "sha256"
                ]
                or
                ""
            ),

        "fecha_hora_extraccion":
            datetime.now(
            ).astimezone(
            ).isoformat(
                timespec="seconds"
            ),

        "detalle":
            resultado_mes[
                "detalle"
            ],
    }


# ============================================================
# 34. GUARDAR HTML CRUDO
# ============================================================

def guardar_html_crudo(
    mes,
    fecha_sbs,
    html
):

    if not GUARDAR_HTML_CRUDO:

        return None

    CARPETA_DATOS_CRUDOS.mkdir(
        parents=True,
        exist_ok=True
    )

    # Si el mes se reprocesa,
    # retirar una captura aceptada anterior.
    patron = (
        f"X3_ahorro_mn_"
        f"{CODIGO_ESTUDIANTE}_"
        f"{mes}_*.html"
    )

    for viejo in CARPETA_DATOS_CRUDOS.glob(
        patron
    ):

        try:

            viejo.unlink()

        except OSError:

            pass

    nombre = (
        f"X3_ahorro_mn_"
        f"{CODIGO_ESTUDIANTE}_"
        f"{mes}_"
        f"{fecha_a_iso(fecha_sbs)}.html"
    )

    ruta = (
        CARPETA_DATOS_CRUDOS
        /
        nombre
    )

    ruta.write_text(
        html,
        encoding="utf-8"
    )

    return ruta


# ============================================================
# 35. RESUMEN TXT
# ============================================================

def escribir_resumen_txt(
    auditoria_por_mes,
    datos_por_mes
):

    CARPETA_DIAGNOSTICOS.mkdir(
        parents=True,
        exist_ok=True
    )

    lineas = []

    lineas.append(
        "EXTRACCIÓN X3 - TASA PASIVA DEPÓSITOS DE AHORRO MN"
    )

    lineas.append(
        "Estudiante: BRICEÑO LEON CRYSTELL HIDEKI"
    )

    lineas.append(
        f"Código: {CODIGO_ESTUDIANTE}"
    )

    lineas.append(
        "Período objetivo: 2015-11 a 2025-12"
    )

    lineas.append(
        f"Meses objetivo: {len(MESES_A_EXTRAER)}"
    )

    lineas.append(
        ""
    )

    disponibles = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "DISPONIBLE"
    ]

    sin_dato = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "MES_SIN_DATO"
    ]

    incompatibles = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "ESTRUCTURA_X3_NO_COMPATIBLE"
    ]

    errores = [
        fila
        for fila in auditoria_por_mes.values()
        if fila.get(
            "estado"
        )
        == "ERROR_TECNICO"
    ]

    lineas.append(
        f"Meses DISPONIBLE: {len(disponibles)}"
    )

    lineas.append(
        f"Meses MES_SIN_DATO: {len(sin_dato)}"
    )

    lineas.append(
        "Meses ESTRUCTURA_X3_NO_COMPATIBLE: "
        f"{len(incompatibles)}"
    )

    lineas.append(
        f"Meses ERROR_TECNICO: {len(errores)}"
    )

    total_filas = sum(
        len(
            filas
        )
        for filas in datos_por_mes.values()
    )

    lineas.append(
        f"Filas banco-mes extraídas: {total_filas}"
    )

    lineas.append(
        ""
    )

    lineas.append(
        "mes | fecha_sbs | retroceso | "
        "bancos | faltantes | Promedio | estado"
    )

    for mes in sorted(
        auditoria_por_mes
    ):

        fila = auditoria_por_mes[
            mes
        ]

        lineas.append(
            f"{mes} | "
            f"{fila.get('fecha_sbs', '')} | "
            f"{fila.get('dias_retrocedidos', '')} | "
            f"{fila.get('cantidad_bancos', '')} | "
            f"{fila.get('cantidad_faltantes_bancos', '')} | "
            f"{fila.get('promedio', '')} | "
            f"{fila.get('estado', '')}"
        )

    TXT_RESUMEN.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8"
    )


# ============================================================
# 36. MAIN
# ============================================================

def main():

    navegador = None

    (
        datos_por_mes,
        promedio_por_mes,
        auditoria_por_mes,
    ) = cargar_checkpoint()

    try:

        print(
            "=" * 90
        )

        print(
            "EXTRACCIÓN MENSUAL COMPLETA X3"
        )

        print(
            "=" * 90
        )

        print(
            VARIABLE
        )

        print()

        print(
            "Período: 2015-11 a 2025-12"
        )

        print(
            f"Meses esperados: "
            f"{len(MESES_A_EXTRAER)}"
        )

        print()

        print(
            "Regla de retroceso:"
        )

        print(
            "  SOLO SIN_INFORMACION permite "
            "retroceder un día."
        )

        print(
            "  ESTRUCTURA_X3_NO_COMPATIBLE "
            "detiene la extracción."
        )

        print(
            "  ERROR_TECNICO/parser "
            "detiene la extracción."
        )

        print()

        print(
            "No se interpolarán faltantes."
        )

        print(
            "No se homologarán nombres."
        )

        print(
            "No se seleccionarán bancos."
        )

        print(
            "Promedio permanecerá separado."
        )

        navegador = crear_navegador()

        for indice, (
            anio,
            mes
        ) in enumerate(
            MESES_A_EXTRAER,
            start=1
        ):

            clave_mes = mes_a_texto(
                anio,
                mes
            )

            print()
            print(
                f"[{indice:03d}/"
                f"{len(MESES_A_EXTRAER):03d}] "
                f"{clave_mes}"
            )

            # =================================================
            # REANUDAR SOLO CHECKPOINTS COMPLETOS
            # =================================================

            if (
                REANUDAR
                and
                checkpoint_mes_completo(
                    clave_mes,
                    datos_por_mes,
                    promedio_por_mes,
                    auditoria_por_mes
                )
            ):

                print(
                    "  [CHECKPOINT VÁLIDO] "
                    "Mes completo y coherente. "
                    "Se omite."
                )

                continue

            # =================================================
            # PROCESAR MES
            # =================================================

            resultado_mes = procesar_mes(
                navegador,
                anio,
                mes
            )

            # =================================================
            # ELIMINAR POSIBLES RESIDUOS DE
            # UN CHECKPOINT PREVIO INCOMPLETO
            # =================================================

            datos_por_mes[
                clave_mes
            ] = []

            promedio_por_mes.pop(
                clave_mes,
                None
            )

            # =================================================
            # DISPONIBLE
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                ==
                "DISPONIBLE"
            ):

                # Guardar primero la evidencia HTML.
                #
                # Si esto falla, el mes no se marca
                # silenciosamente como completo.
                try:

                    guardar_html_crudo(
                        clave_mes,
                        resultado_mes[
                            "fecha_sbs"
                        ],
                        resultado_mes[
                            "html"
                        ]
                    )

                except Exception as error:

                    resultado_mes = {
                        "estado":
                            "ERROR_TECNICO",

                        "mes":
                            clave_mes,

                        "fecha_calendario_final":
                            ultimo_dia_mes(
                                anio,
                                mes
                            ),

                        "fecha_sbs":
                            resultado_mes[
                                "fecha_sbs"
                            ],

                        "dias_retrocedidos":
                            resultado_mes[
                                "dias_retrocedidos"
                            ],

                        "cantidad_bancos":
                            None,

                        "cantidad_faltantes":
                            None,

                        "bancos":
                            [],

                        "promedio":
                            None,

                        "html":
                            None,

                        "sha256":
                            None,

                        "detalle":
                            (
                                "Error guardando HTML crudo: "
                                f"{type(error).__name__}: "
                                f"{error}"
                            ),
                    }

                # Solo construir datos si el guardado
                # de evidencia siguió siendo válido.
                if (
                    resultado_mes[
                        "estado"
                    ]
                    ==
                    "DISPONIBLE"
                ):

                    filas_datos = construir_filas_datos(
                        resultado_mes
                    )

                    fila_promedio = construir_fila_promedio(
                        resultado_mes
                    )

                    if (
                        len(
                            filas_datos
                        )
                        !=
                        resultado_mes[
                            "cantidad_bancos"
                        ]
                    ):

                        raise ErrorTecnicoX3(
                            f"{clave_mes}: número "
                            "de filas bancarias distinto "
                            "de cantidad_bancos."
                        )

                    if fila_promedio is None:

                        raise ErrorTecnicoX3(
                            f"{clave_mes}: Promedio "
                            "no pudo construirse."
                        )

                    datos_por_mes[
                        clave_mes
                    ] = filas_datos

                    promedio_por_mes[
                        clave_mes
                    ] = fila_promedio

            # =================================================
            # AUDITORÍA DEL MES
            # =================================================

            auditoria_por_mes[
                clave_mes
            ] = construir_fila_auditoria(
                resultado_mes
            )

            # =================================================
            # CHECKPOINT DESPUÉS DE CADA MES
            # =================================================

            guardar_checkpoint(
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            )

            escribir_resumen_txt(
                auditoria_por_mes,
                datos_por_mes
            )

            # =================================================
            # VALIDACIÓN INMEDIATA DEL CHECKPOINT
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                in {
                    "DISPONIBLE",
                    "MES_SIN_DATO",
                }
                and
                not checkpoint_mes_completo(
                    clave_mes,
                    datos_por_mes,
                    promedio_por_mes,
                    auditoria_por_mes
                )
            ):

                raise ErrorTecnicoX3(
                    f"{clave_mes}: el checkpoint "
                    "recién guardado no supera "
                    "la validación de coherencia."
                )

            # =================================================
            # ESTRUCTURA INCOMPATIBLE
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                ==
                "ESTRUCTURA_X3_NO_COMPATIBLE"
            ):

                raise EstructuraX3NoCompatible(
                    "La extracción se detuvo en "
                    f"{clave_mes}. SBS confirmó "
                    "la fecha, pero la estructura "
                    "X3 validada no estuvo disponible. "
                    "El estado quedó guardado "
                    "en la auditoría."
                )

            # =================================================
            # ERROR TÉCNICO
            # =================================================

            if (
                resultado_mes[
                    "estado"
                ]
                ==
                "ERROR_TECNICO"
            ):

                raise ErrorTecnicoX3(
                    "La extracción se detuvo en "
                    f"{clave_mes} por ERROR_TECNICO. "
                    "El avance quedó guardado. "
                    "Al volver a ejecutar, "
                    "REANUDAR=True retomará "
                    "desde este mes."
                )

            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

        # ====================================================
        # VALIDACIÓN FINAL DE LOS 122 MESES
        # ====================================================

        meses_completos = []

        for anio, mes in MESES_A_EXTRAER:

            clave_mes = mes_a_texto(
                anio,
                mes
            )

            if checkpoint_mes_completo(
                clave_mes,
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            ):

                meses_completos.append(
                    clave_mes
                )

        print()
        print(
            "=" * 90
        )

        print(
            "VALIDACIÓN FINAL"
        )

        print(
            "=" * 90
        )

        print(
            f"Meses objetivo: "
            f"{len(MESES_A_EXTRAER)}"
        )

        print(
            f"Meses completos y coherentes: "
            f"{len(meses_completos)}"
        )

        if (
            len(
                meses_completos
            )
            !=
            len(
                MESES_A_EXTRAER
            )
        ):

            raise ErrorTecnicoX3(
                "La ejecución llegó al final "
                "pero no existen 122 checkpoints "
                "completos y coherentes."
            )

        total_filas = sum(
            len(
                filas
            )
            for filas in datos_por_mes.values()
        )

        print(
            f"Filas banco-mes: "
            f"{total_filas}"
        )

        print()
        print(
            "CSV PRINCIPAL:"
        )

        print(
            CSV_DATOS
        )

        print()
        print(
            "PROMEDIOS:"
        )

        print(
            CSV_PROMEDIO
        )

        print()
        print(
            "AUDITORÍA:"
        )

        print(
            CSV_AUDITORIA
        )

        print()
        print(
            "RESUMEN:"
        )

        print(
            TXT_RESUMEN
        )

        print()
        print(
            "ESTADO = "
            "EXTRACCION_X3_COMPLETA"
        )

    except Exception as error:

        print()
        print(
            "=" * 90
        )

        print(
            "EXTRACCIÓN X3 DETENIDA"
        )

        print(
            "=" * 90
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        print()
        print(
            "Se intentará conservar "
            "todo el avance antes de salir."
        )

        # ====================================================
        # GUARDADO PREVENTIVO
        # ====================================================

        try:

            guardar_checkpoint(
                datos_por_mes,
                promedio_por_mes,
                auditoria_por_mes
            )

            escribir_resumen_txt(
                auditoria_por_mes,
                datos_por_mes
            )

            print(
                "[OK] CSV/checkpoints y resumen "
                "conservados."
            )

        except Exception as error_guardado:

            print()
            print(
                "[ADVERTENCIA] Falló también "
                "el guardado preventivo:"
            )

            print(
                f"{type(error_guardado).__name__}: "
                f"{error_guardado}"
            )

        # IMPORTANTE:
        #
        # Repropagar la excepción.
        # Python terminará con código != 0.
        # El finally se ejecutará antes y
        # cerrará Chrome.
        raise

    finally:

        # ====================================================
        # CIERRE GARANTIZADO DE CHROME
        # ====================================================

        if navegador is not None:

            try:

                navegador.quit()

                print()
                print(
                    "[OK] Chrome cerrado correctamente."
                )

            except Exception as error_cierre:

                print()
                print(
                    "[ADVERTENCIA] Chrome no pudo "
                    "cerrarse limpiamente:"
                )

                print(
                    f"{type(error_cierre).__name__}: "
                    f"{error_cierre}"
                )


# ============================================================
# 37. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()