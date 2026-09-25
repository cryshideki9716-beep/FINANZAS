# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Fecha de extracción: 2026-09-24

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
    "TIPasivaDepositoEmpresa.aspx?tip=B"
)

# ÚNICA FECHA DE ESTA PRUEBA
FECHA_OBJETIVO = date(
    2015,
    11,
    30
)

FECHA_TEXTO = "30/11/2015"

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
    / "diagnostico_x3_pasiva_ahorro_mn_2015.txt"
)

ARCHIVO_HTML = (
    CARPETA_SALIDA
    / "diagnostico_x3_pasiva_ahorro_mn_2015.html"
)

ARCHIVO_PNG = (
    CARPETA_SALIDA
    / "diagnostico_x3_pasiva_ahorro_mn_2015.png"
)


# ============================================================
# 2. SALIDA
# ============================================================

lineas = []


def escribir(texto=""):

    texto = str(texto)

    print(texto)

    lineas.append(
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
# 3. UTILIDADES DE TEXTO
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


def clave_semantica(valor):

    """
    Versión muy compacta usada solo para
    analizar IDs/names de controles.

    NO modifica ningún dato SBS.
    """

    texto = normalizar_texto(
        valor
    )

    return re.sub(
        r"[^a-z0-9]",
        "",
        texto
    )


# ============================================================
# 4. FECHAS
# ============================================================

def convertir_fecha(valor):

    """
    Acepta, entre otros:

        30/11/2015
        2015-11-30
        2015-11-30-00-00-00

    Basta con que la representación contenga
    inequívocamente la fecha objetivo.
    """

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


def esperar_documento(
    navegador
):

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


# ============================================================
# 6. INVENTARIO DINÁMICO DE CONTROLES
# ============================================================

def obtener_controles(
    navegador
):
    """
    No presupone IDs.

    Devuelve controles reales encontrados
    en el DOM con:

      tag
      id
      name
      type
      value
      visible
    """

    try:

        return navegador.execute_script(
            r"""
            const elementos =
                Array.from(
                    document.querySelectorAll(
                        'input,select,button'
                    )
                );

            const salida = [];

            for (const el of elementos) {

                const style =
                    window.getComputedStyle(el);

                const rect =
                    el.getBoundingClientRect();

                let valor = '';

                try {

                    valor =
                        el.value !== undefined
                        ? String(el.value)
                        : '';

                } catch (e) {

                    valor = '';
                }

                salida.push({
                    tag:
                        el.tagName || '',

                    id:
                        el.id || '',

                    name:
                        el.name || '',

                    type:
                        el.type || '',

                    value:
                        valor,

                    visible:
                        (
                            style.display !== 'none'
                            &&
                            style.visibility !== 'hidden'
                            &&
                            rect.width > 0
                            &&
                            rect.height > 0
                        )
                });
            }

            return salida;
            """
        ) or []

    except WebDriverException as error:

        raise RuntimeError(
            "No se pudieron inventariar "
            f"los controles SBS: {error}"
        ) from error


# ============================================================
# 7. DATEPICKER VISIBLE DINÁMICO
# ============================================================

def localizar_fecha_visible(
    navegador
):

    selectores = [
        "input[id*='rdpDate'][id$='_dateInput']",
        "input[name*='rdpDate'][name$='$dateInput']",
        "input[id*='Date'][id$='_dateInput']",
    ]

    for selector in selectores:

        encontrados = navegador.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for elemento in encontrados:

            try:

                if elemento.is_displayed():

                    return elemento

            except (
                WebDriverException,
                StaleElementReferenceException
            ):

                continue

    return None


def info_elemento(
    elemento
):

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
# 8. DATEPICKER INTERNO DINÁMICO
# ============================================================

def localizar_fecha_interna(
    navegador,
    fecha_visible
):
    """
    Primero intenta hallar el control hermano
    exacto del DatePicker visible.

    Si no aparece, busca controles relacionados
    con 'date'/'fecha' cuya fecha pueda leerse.

    No inventa ningún ID.
    """

    info_visible = info_elemento(
        fecha_visible
    )

    id_visible = info_visible[
        "id"
    ]

    name_visible = info_visible[
        "name"
    ]

    candidatos_preferidos = []

    # --------------------------------------------------------
    # A. Derivar únicamente a partir del ID REAL observado.
    # --------------------------------------------------------

    if id_visible.endswith(
        "_dateInput"
    ):

        id_base = id_visible[
            :-len(
                "_dateInput"
            )
        ]

        encontrados = navegador.find_elements(
            By.ID,
            id_base
        )

        candidatos_preferidos.extend(
            encontrados
        )

    if name_visible.endswith(
        "$dateInput"
    ):

        name_base = name_visible[
            :-len(
                "$dateInput"
            )
        ]

        encontrados = navegador.find_elements(
            By.NAME,
            name_base
        )

        candidatos_preferidos.extend(
            encontrados
        )

    # Eliminar repetidos.
    vistos = set()

    preferidos_unicos = []

    for elemento in candidatos_preferidos:

        try:

            clave = (
                elemento.get_attribute(
                    "id"
                ),
                elemento.get_attribute(
                    "name"
                ),
            )

        except Exception:

            continue

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        preferidos_unicos.append(
            elemento
        )

    # --------------------------------------------------------
    # B. Si uno de los preferidos contiene una fecha,
    #    ese será el interno.
    # --------------------------------------------------------

    for elemento in preferidos_unicos:

        try:

            valor = limpiar_texto(
                elemento.get_attribute(
                    "value"
                )
            )

            if convertir_fecha(
                valor
            ) is not None:

                return (
                    elemento,
                    "HERMANO_DATEPICKER"
                )

        except Exception:

            continue

    # --------------------------------------------------------
    # C. Fallback dinámico: controles date/fecha/rdpDate
    #    distintos del visible.
    # --------------------------------------------------------

    controles = navegador.find_elements(
        By.CSS_SELECTOR,
        "input"
    )

    candidatos = []

    for elemento in controles:

        try:

            if elemento == fecha_visible:
                continue

            info = info_elemento(
                elemento
            )

            combinado = clave_semantica(
                " ".join(
                    [
                        info[
                            "id"
                        ],
                        info[
                            "name"
                        ],
                    ]
                )
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

            candidatos.append(
                elemento
            )

        except Exception:

            continue

    # Si hay uno solo, no hay ambigüedad.
    if len(
        candidatos
    ) == 1:

        return (
            candidatos[0],
            "UNICO_CONTROL_FECHA_INTERNA"
        )

    # Si hay varios, preferimos el que contenga
    # exactamente la fecha objetivo.
    candidatos_objetivo = []

    for elemento in candidatos:

        try:

            fecha = convertir_fecha(
                elemento.get_attribute(
                    "value"
                )
            )

            if fecha == FECHA_OBJETIVO:

                candidatos_objetivo.append(
                    elemento
                )

        except Exception:

            continue

    if len(
        candidatos_objetivo
    ) == 1:

        return (
            candidatos_objetivo[0],
            "UNICO_CONTROL_CON_FECHA_OBJETIVO"
        )

    return (
        None,
        "NO_LOCALIZADO_O_AMBIGUO"
    )


# ============================================================
# 9. CONTROL DINÁMICO MONEDA / ENTIDAD
# ============================================================

def seleccionar_control_contexto(
    controles,
    tipo
):
    """
    Localiza dinámicamente:

        moneda -> valor esperado MN
        entidad -> valor esperado B

    Usa primero el valor REAL del control y
    después evidencia semántica del ID/name.

    No crea ni presupone IDs.
    """

    if tipo == "moneda":

        esperado = "MN"

        palabras_fuertes = [
            "moneda",
            "tipomoneda",
            "currency",
        ]

    elif tipo == "entidad":

        esperado = "B"

        palabras_fuertes = [
            "entidad",
            "tipoentidad",
            "entity",
        ]

    else:

        raise ValueError(
            f"Tipo desconocido: {tipo}"
        )

    candidatos_valor = []

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
            " ".join(
                [
                    control.get(
                        "id",
                        ""
                    ),
                    control.get(
                        "name",
                        ""
                    ),
                ]
            )
        )

        puntaje = 0

        evidencias = []

        for palabra in palabras_fuertes:

            clave = clave_semantica(
                palabra
            )

            if clave in combinado:

                puntaje += 100

                evidencias.append(
                    palabra
                )

        if (
            "tipo" in combinado
        ):

            puntaje += 5

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

        candidatos_valor.append({
            "control":
                control,

            "puntaje":
                puntaje,

            "evidencias":
                evidencias,
        })

    if not candidatos_valor:

        return {
            "ok":
                False,

            "motivo":
                (
                    f"No existe control con "
                    f"value={esperado!r}"
                ),

            "seleccionado":
                None,

            "candidatos":
                [],
        }

    candidatos_valor.sort(
        key=lambda x:
        x[
            "puntaje"
        ],
        reverse=True
    )

    # --------------------------------------------------------
    # Primero buscamos evidencia semántica inequívoca.
    # --------------------------------------------------------

    mejor_puntaje = candidatos_valor[
        0
    ][
        "puntaje"
    ]

    mejores = [
        candidato
        for candidato
        in candidatos_valor
        if candidato[
            "puntaje"
        ]
        == mejor_puntaje
    ]

    if (
        mejor_puntaje > 0
        and
        len(
            mejores
        )
        == 1
    ):

        return {
            "ok":
                True,

            "motivo":
                "EVIDENCIA_SEMANTICA_UNIVOCA",

            "seleccionado":
                mejores[0],

            "candidatos":
                candidatos_valor,
        }

    # --------------------------------------------------------
    # Si no hay evidencia semántica pero solo existe
    # UN control con ese valor, puede identificarse
    # dinámicamente sin inventar.
    # --------------------------------------------------------

    if len(
        candidatos_valor
    ) == 1:

        return {
            "ok":
                True,

            "motivo":
                "UNICO_CONTROL_CON_VALOR_ESPERADO",

            "seleccionado":
                candidatos_valor[0],

            "candidatos":
                candidatos_valor,
        }

    return {
        "ok":
            False,

        "motivo":
            (
                "CONTROLES_AMBIGUOS_CON_EL_MISMO_VALOR"
            ),

        "seleccionado":
            None,

        "candidatos":
            candidatos_valor,
    }


# ============================================================
# 10. VALIDACIÓN COMPLETA DEL ESTADO DEL FORMULARIO
# ============================================================

def validar_estado_formulario(
    navegador,
    etapa
):
    """
    Se ejecutará:

      1. después de establecer 30/11/2015;
      2. después de pulsar Consultar.

    Exige:

      fecha visible = 30/11/2015
      fecha interna = 30/11/2015 equivalente
      moneda = MN
      entidad = B
    """

    titulo(
        f"VALIDACIÓN DEL FORMULARIO - {etapa}"
    )

    # ========================================================
    # A. FECHA VISIBLE
    # ========================================================

    fecha_visible = localizar_fecha_visible(
        navegador
    )

    if fecha_visible is None:

        raise RuntimeError(
            f"{etapa}: no se encontró "
            "el DatePicker visible."
        )

    info_visible = info_elemento(
        fecha_visible
    )

    fecha_visible_parseada = convertir_fecha(
        info_visible[
            "value"
        ]
    )

    escribir(
        "FECHA VISIBLE"
    )

    escribir(
        f"  id = "
        f"{info_visible['id']!r}"
    )

    escribir(
        f"  name = "
        f"{info_visible['name']!r}"
    )

    escribir(
        f"  value = "
        f"{info_visible['value']!r}"
    )

    escribir(
        f"  fecha parseada = "
        f"{fecha_visible_parseada}"
    )

    if (
        fecha_visible_parseada
        !=
        FECHA_OBJETIVO
    ):

        raise RuntimeError(
            f"{etapa}: fecha visible "
            "no es 30/11/2015."
        )

    escribir(
        "  [OK] fecha visible = 30/11/2015"
    )

    # ========================================================
    # B. FECHA INTERNA
    # ========================================================

    (
        fecha_interna,
        metodo_interno
    ) = localizar_fecha_interna(
        navegador,
        fecha_visible
    )

    if fecha_interna is None:

        raise RuntimeError(
            f"{etapa}: fecha interna "
            "no pudo localizarse "
            "de manera inequívoca."
        )

    info_interna = info_elemento(
        fecha_interna
    )

    fecha_interna_parseada = convertir_fecha(
        info_interna[
            "value"
        ]
    )

    escribir()
    escribir(
        "FECHA INTERNA"
    )

    escribir(
        f"  método de localización = "
        f"{metodo_interno}"
    )

    escribir(
        f"  id = "
        f"{info_interna['id']!r}"
    )

    escribir(
        f"  name = "
        f"{info_interna['name']!r}"
    )

    escribir(
        f"  type = "
        f"{info_interna['type']!r}"
    )

    escribir(
        f"  value = "
        f"{info_interna['value']!r}"
    )

    escribir(
        f"  fecha parseada = "
        f"{fecha_interna_parseada}"
    )

    if (
        fecha_interna_parseada
        !=
        FECHA_OBJETIVO
    ):

        raise RuntimeError(
            f"{etapa}: fecha interna "
            "no equivale a 30/11/2015."
        )

    escribir(
        "  [OK] fecha interna equivale "
        "a 30/11/2015"
    )

    # ========================================================
    # C. INVENTARIO REAL DE CONTROLES
    # ========================================================

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

    # ========================================================
    # D. MONEDA
    # ========================================================

    escribir()
    escribir(
        "CONTROL DE MONEDA"
    )

    escribir(
        f"  resultado de búsqueda = "
        f"{moneda['motivo']}"
    )

    escribir(
        "  candidatos con value='MN':"
    )

    if moneda[
        "candidatos"
    ]:

        for numero, candidato in enumerate(
            moneda[
                "candidatos"
            ],
            start=1
        ):

            control = candidato[
                "control"
            ]

            escribir(
                f"    {numero}. "
                f"id={control.get('id')!r} | "
                f"name={control.get('name')!r} | "
                f"type={control.get('type')!r} | "
                f"value={control.get('value')!r} | "
                f"visible={control.get('visible')} | "
                f"puntaje={candidato['puntaje']} | "
                f"evidencia={candidato['evidencias']}"
            )

    else:

        escribir(
            "    <NINGUNO>"
        )

    if not moneda[
        "ok"
    ]:

        raise RuntimeError(
            f"{etapa}: control de moneda "
            "no pudo identificarse "
            "de manera inequívoca."
        )

    control_moneda = moneda[
        "seleccionado"
    ][
        "control"
    ]

    escribir(
        "  CONTROL DE MONEDA SELECCIONADO:"
    )

    escribir(
        f"    id = "
        f"{control_moneda.get('id')!r}"
    )

    escribir(
        f"    name = "
        f"{control_moneda.get('name')!r}"
    )

    escribir(
        f"    type = "
        f"{control_moneda.get('type')!r}"
    )

    escribir(
        f"    value = "
        f"{control_moneda.get('value')!r}"
    )

    if (
        limpiar_texto(
            control_moneda.get(
                "value",
                ""
            )
        ).upper()
        != "MN"
    ):

        raise RuntimeError(
            f"{etapa}: moneda distinta de MN."
        )

    escribir(
        "  [OK] moneda = MN"
    )

    # ========================================================
    # E. ENTIDAD
    # ========================================================

    escribir()
    escribir(
        "CONTROL DE ENTIDAD"
    )

    escribir(
        f"  resultado de búsqueda = "
        f"{entidad['motivo']}"
    )

    escribir(
        "  candidatos con value='B':"
    )

    if entidad[
        "candidatos"
    ]:

        for numero, candidato in enumerate(
            entidad[
                "candidatos"
            ],
            start=1
        ):

            control = candidato[
                "control"
            ]

            escribir(
                f"    {numero}. "
                f"id={control.get('id')!r} | "
                f"name={control.get('name')!r} | "
                f"type={control.get('type')!r} | "
                f"value={control.get('value')!r} | "
                f"visible={control.get('visible')} | "
                f"puntaje={candidato['puntaje']} | "
                f"evidencia={candidato['evidencias']}"
            )

    else:

        escribir(
            "    <NINGUNO>"
        )

    if not entidad[
        "ok"
    ]:

        raise RuntimeError(
            f"{etapa}: control de entidad "
            "no pudo identificarse "
            "de manera inequívoca."
        )

    control_entidad = entidad[
        "seleccionado"
    ][
        "control"
    ]

    escribir(
        "  CONTROL DE ENTIDAD SELECCIONADO:"
    )

    escribir(
        f"    id = "
        f"{control_entidad.get('id')!r}"
    )

    escribir(
        f"    name = "
        f"{control_entidad.get('name')!r}"
    )

    escribir(
        f"    type = "
        f"{control_entidad.get('type')!r}"
    )

    escribir(
        f"    value = "
        f"{control_entidad.get('value')!r}"
    )

    if (
        limpiar_texto(
            control_entidad.get(
                "value",
                ""
            )
        ).upper()
        != "B"
    ):

        raise RuntimeError(
            f"{etapa}: entidad distinta de B."
        )

    escribir(
        "  [OK] entidad = B"
    )

    return {
        "fecha_visible":
            info_visible,

        "fecha_interna":
            info_interna,

        "moneda":
            control_moneda,

        "entidad":
            control_entidad,
    }


# ============================================================
# 11. BOTÓN CONSULTAR DINÁMICO
# ============================================================

def localizar_boton_consultar(
    navegador
):

    candidatos = navegador.find_elements(
        By.CSS_SELECTOR,
        "input,button"
    )

    encontrados = []

    for elemento in candidatos:

        try:

            if not elemento.is_displayed():
                continue

            info = info_elemento(
                elemento
            )

            texto_visible = limpiar_texto(
                elemento.text
            )

            combinado = normalizar_texto(
                " ".join(
                    [
                        info[
                            "id"
                        ],
                        info[
                            "name"
                        ],
                        info[
                            "value"
                        ],
                        texto_visible,
                    ]
                )
            )

            if (
                "consultar" in combinado
                or
                "btnconsultar" in combinado
            ):

                encontrados.append(
                    elemento
                )

        except Exception:

            continue

    if len(
        encontrados
    ) == 1:

        return encontrados[
            0
        ]

    return None


# ============================================================
# 12. DETECTAR PÁGINA REAL
# ============================================================

def pagina_real(
    navegador
):

    try:

        fecha = localizar_fecha_visible(
            navegador
        )

        boton = localizar_boton_consultar(
            navegador
        )

        return (
            fecha is not None
            and
            boton is not None
        )

    except Exception:

        return False


def asegurar_pagina_real(
    navegador
):

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

        escribir()
        escribir(
            "La aplicación SBS real "
            "todavía no fue detectada."
        )

        escribir(
            "Si aparece una verificación "
            "de seguridad, complétala "
            "manualmente."
        )

        escribir(
            "No cierres Chrome."
        )

        escribir()

        input(
            "Cuando veas la página SBS real, "
            "presiona ENTER aquí..."
        )

    WebDriverWait(
        navegador,
        TIMEOUT_MANUAL
    ).until(
        lambda d:
        pagina_real(
            d
        )
    )


# ============================================================
# 13. ESTABLECER 30/11/2015
# ============================================================

def establecer_fecha(
    navegador
):

    campo = localizar_fecha_visible(
        navegador
    )

    if campo is None:

        raise RuntimeError(
            "No se encontró "
            "el DatePicker visible."
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

    # --------------------------------------------------------
    # Primera validación de visible + interno.
    # --------------------------------------------------------

    campo = localizar_fecha_visible(
        navegador
    )

    valor_visible = limpiar_texto(
        campo.get_attribute(
            "value"
        )
    )

    (
        interno,
        metodo
    ) = localizar_fecha_interna(
        navegador,
        campo
    )

    fecha_visible = convertir_fecha(
        valor_visible
    )

    fecha_interna = None

    if interno is not None:

        fecha_interna = convertir_fecha(
            interno.get_attribute(
                "value"
            )
        )

    if (
        fecha_visible == FECHA_OBJETIVO
        and
        fecha_interna == FECHA_OBJETIVO
    ):

        return

    # ========================================================
    # FALLBACK TELERIK
    # ========================================================

    escribir(
        "El DatePicker no quedó validado "
        "en el primer intento."
    )

    escribir(
        "Aplicando fallback Telerik usando "
        "el ID REAL del DatePicker visible..."
    )

    info_visible = info_elemento(
        campo
    )

    id_visible = info_visible[
        "id"
    ]

    if not id_visible.endswith(
        "_dateInput"
    ):

        raise RuntimeError(
            "No puede derivarse de forma segura "
            "el objeto Telerik porque el ID real "
            "del input visible no termina "
            "en '_dateInput'."
        )

    id_picker_real = id_visible[
        :-len(
            "_dateInput"
        )
    ]

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

            if (
                typeof picker.set_selectedDate
                !== 'function'
            ) {
                return 'NO_set_selectedDate';
            }

            const fecha =
                new Date(
                    2015,
                    10,
                    30
                );

            picker.set_selectedDate(
                fecha
            );

            if (
                typeof picker.get_dateInput
                === 'function'
            ) {

                const input =
                    picker.get_dateInput();

                if (
                    input
                    &&
                    typeof input.set_value
                    === 'function'
                ) {

                    input.set_value(
                        '30/11/2015'
                    );
                }
            }

            return (
                'OK|' +
                arguments[0]
            );

        } catch (e) {

            return (
                'ERROR|' +
                e.toString()
            );
        }
        """,
        id_picker_real
    )

    escribir(
        f"Resultado fallback = "
        f"{resultado!r}"
    )

    time.sleep(
        1
    )

    # La validación completa se realiza
    # inmediatamente después en main().


# ============================================================
# 14. CONFIRMACIÓN DEL PERÍODO
# ============================================================

def buscar_confirmacion_periodo(
    navegador
):

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

        const vistos =
            new Set();

        for (const el of elementos) {

            const style =
                window.getComputedStyle(el);

            const rect =
                el.getBoundingClientRect();

            if (
                style.display === 'none'
                ||
                style.visibility === 'hidden'
                ||
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
                texto.length > 800
            ) {
                continue;
            }

            if (
                !patron.test(texto)
            ) {
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

            vistos.add(
                clave
            );

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


def buscar_sin_informacion(
    navegador
):

    texto = navegador.find_element(
        By.TAG_NAME,
        "body"
    ).text

    normal = normalizar_texto(
        texto
    )

    return (
        "no existe informacion "
        "para la fecha elegida"
        in normal
    )


# ============================================================
# 15. CONSULTAR
# ============================================================

def consultar(
    navegador
):

    boton = localizar_boton_consultar(
        navegador
    )

    if boton is None:

        raise RuntimeError(
            "No se localizó de manera inequívoca "
            "el botón Consultar."
        )

    info_boton = info_elemento(
        boton
    )

    escribir(
        "Botón Consultar detectado dinámicamente:"
    )

    escribir(
        f"  id = "
        f"{info_boton['id']!r}"
    )

    escribir(
        f"  name = "
        f"{info_boton['name']!r}"
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

    while (
        time.time()
        - inicio
        < TIMEOUT
    ):

        sin_info = buscar_sin_informacion(
            navegador
        )

        confirmaciones = buscar_confirmacion_periodo(
            navegador
        )

        # ====================================================
        # SIN_INFORMACION TIENE PRIORIDAD
        # ====================================================

        if sin_info:

            time.sleep(
                0.5
            )

            confirmaciones = buscar_confirmacion_periodo(
                navegador
            )

            return {
                "respuesta":
                    "SIN_INFORMACION",

                "periodo_confirmado":
                    len(
                        confirmaciones
                    )
                    > 0,

                "confirmaciones":
                    confirmaciones,
            }

        if confirmaciones:

            # Dar tiempo a que termine de
            # estabilizarse el postback.
            time.sleep(
                2
            )

            sin_info = buscar_sin_informacion(
                navegador
            )

            confirmaciones = buscar_confirmacion_periodo(
                navegador
            )

            if sin_info:

                return {
                    "respuesta":
                        "SIN_INFORMACION",

                    "periodo_confirmado":
                        len(
                            confirmaciones
                        )
                        > 0,

                    "confirmaciones":
                        confirmaciones,
                }

            return {
                "respuesta":
                    "PERIODO_CONFIRMADO",

                "periodo_confirmado":
                    True,

                "confirmaciones":
                    confirmaciones,
            }

        time.sleep(
            0.25
        )

    raise RuntimeError(
        "La respuesta SBS no confirmó "
        "'al 30/11/2015' ni mostró "
        "SIN_INFORMACION dentro del tiempo "
        "de espera. Se considera error técnico, "
        "no ausencia de datos."
    )


# ============================================================
# 16. DIAGNÓSTICO ESTRUCTURAL DE X3
# ============================================================

def diagnosticar_estructura_x3(
    navegador
):
    """
    NO extrae tasas.

    Determina:

      - etiquetas visibles exactas
        'Depósitos de Ahorro';

      - tabla y cadena de tablas de cada etiqueta;

      - cuál corresponde a MN;

      - ubicaciones de Promedio;

      - tablas candidatas donde aparecen bancos;

      - DataZones/tablas numéricas;

      - asociación estructural con la etiqueta MN.
    """

    script = r"""
    const MONEDA_ACTUAL =
        arguments[0];

    // ========================================================
    // UTILIDADES
    // ========================================================

    function limpiar(txt) {

        return (txt || '')
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normal(txt) {

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

    function horizontalOverlap(
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

    function verticalDistance(
        a,
        b
    ) {

        return Math.abs(
            a.centerY
            -
            b.centerY
        );
    }

    function esNumero(txt) {

        const t =
            limpiar(txt);

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

        return (
            n === ''
            ||
            n === '-'
            ||
            n === '–'
            ||
            n === '—'
            ||
            n === 's.i.'
            ||
            n === 's.i'
            ||
            n === 'n.d.'
            ||
            n === 'n.d'
            ||
            n === 'nd'
            ||
            n === 'n/a'
            ||
            n === 'na'
        );
    }

    function tablaKey(
        tabla,
        indice
    ) {

        if (
            tabla
            &&
            tabla.id
        ) {

            return tabla.id;
        }

        return (
            '__TABLE_' +
            String(indice)
        );
    }

    function tablasAncestro(
        elemento
    ) {

        const salida = [];

        let actual =
            elemento
            ? elemento.parentElement
            : null;

        while (actual) {

            if (
                actual.tagName
                === 'TABLE'
            ) {

                salida.push(
                    actual.id || '<TABLE_SIN_ID>'
                );
            }

            actual =
                actual.parentElement;
        }

        return salida;
    }

    function elementoTerminalConTexto(
        elemento,
        textoObjetivo
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

            const texto =
                normal(
                    hijo.innerText
                    ||
                    hijo.textContent
                );

            if (
                texto
                === textoObjetivo
            ) {

                return false;
            }
        }

        return true;
    }

    // ========================================================
    // INVENTARIO DE TABLAS
    // ========================================================

    const tablasDOM =
        Array.from(
            document.querySelectorAll(
                'table'
            )
        );

    const tablasVisibles = [];

    const tablaIndice =
        new Map();

    for (
        let i = 0;
        i < tablasDOM.length;
        i++
    ) {

        tablaIndice.set(
            tablasDOM[i],
            i
        );

        if (
            visible(
                tablasDOM[i]
            )
        ) {

            tablasVisibles.push(
                tablasDOM[i]
            );
        }
    }

    // ========================================================
    // ANCLAS MONEDA NACIONAL / EXTRANJERA
    // ========================================================

    const currencyAnchors = [];

    const candidatosAnchor =
        Array.from(
            document.querySelectorAll(
                'span,label,div,p,h1,h2,h3,h4,h5,h6,td,th'
            )
        );

    for (
        const el
        of candidatosAnchor
    ) {

        if (!visible(el)) {
            continue;
        }

        const texto =
            limpiar(
                el.innerText
                ||
                el.textContent
            );

        if (
            !texto
            ||
            texto.length > 600
        ) {
            continue;
        }

        const n =
            normal(texto);

        let moneda = null;

        if (
            n === 'moneda nacional'
            ||
            (
                n.includes(
                    'tasas pasivas anuales'
                )
                &&
                n.includes(
                    'moneda nacional'
                )
            )
        ) {

            moneda = 'MN';
        }

        if (
            n === 'moneda extranjera'
            ||
            (
                n.includes(
                    'tasas pasivas anuales'
                )
                &&
                n.includes(
                    'moneda extranjera'
                )
            )
        ) {

            moneda = 'ME';
        }

        if (!moneda) {
            continue;
        }

        currencyAnchors.push({
            moneda:
                moneda,

            tag:
                el.tagName,

            id:
                el.id || '',

            text:
                texto,

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

    // ========================================================
    // ETIQUETAS EXACTAS VISIBLES DEPÓSITOS DE AHORRO
    // ========================================================

    const ahorro = [];

    const posiblesEtiquetas =
        Array.from(
            document.querySelectorAll(
                'td,th,span,label,div'
            )
        );

    for (
        const el
        of posiblesEtiquetas
    ) {

        if (!visible(el)) {
            continue;
        }

        const texto =
            limpiar(
                el.innerText
                ||
                el.textContent
            );

        if (
            normal(texto)
            !==
            'depositos de ahorro'
        ) {
            continue;
        }

        /*
        Evita contar simultáneamente el TD
        y un DIV interno con el mismo texto.
        Nos quedamos con la etiqueta terminal.
        */

        if (
            !elementoTerminalConTexto(
                el,
                'depositos de ahorro'
            )
        ) {
            continue;
        }

        const tabla =
            el.closest(
                'table'
            );

        const fila =
            el.closest(
                'tr'
            );

        const rect =
            rectInfo(el);

        const ancestros =
            tablasAncestro(el);

        ahorro.push({
            element:
                el,

            text:
                texto,

            tag:
                el.tagName,

            id:
                el.id || '',

            tableElement:
                tabla,

            tableId:
                tabla
                ? tabla.id || ''
                : '',

            rowIndex:
                fila
                ? fila.rowIndex
                : null,

            cellIndex:
                (
                    el.tagName === 'TD'
                    ||
                    el.tagName === 'TH'
                )
                ? el.cellIndex
                : null,

            rect:
                rect,

            ancestorTableIds:
                ancestros,

            currency:
                'NO_CLASIFICADA',

            currencyEvidence:
                []
        });
    }

    // ========================================================
    // CLASIFICAR CADA AHORRO COMO MN / ME / AMBIGUA
    // ========================================================

    for (
        const etiqueta
        of ahorro
    ) {

        const evidenciaMN = [];

        const evidenciaME = [];

        // ----------------------------------------------------
        // A. Evidencia mediante IDs reales de ancestros.
        // ----------------------------------------------------

        for (
            const id
            of etiqueta.ancestorTableIds
        ) {

            const nid =
                normal(id)
                .replace(
                    /[^a-z0-9]/g,
                    ''
                );

            if (
                nid.includes(
                    'actualmn'
                )
                ||
                nid.includes(
                    'monedanacional'
                )
            ) {

                evidenciaMN.push(
                    'ID_ANCESTRO:' +
                    id
                );
            }

            if (
                nid.includes(
                    'actualme'
                )
                ||
                nid.includes(
                    'monedaextranjera'
                )
            ) {

                evidenciaME.push(
                    'ID_ANCESTRO:' +
                    id
                );
            }
        }

        if (
            evidenciaMN.length > 0
            &&
            evidenciaME.length === 0
        ) {

            etiqueta.currency =
                'MN';

            etiqueta.currencyEvidence =
                evidenciaMN;

            continue;
        }

        if (
            evidenciaME.length > 0
            &&
            evidenciaMN.length === 0
        ) {

            etiqueta.currency =
                'ME';

            etiqueta.currencyEvidence =
                evidenciaME;

            continue;
        }

        // ----------------------------------------------------
        // B. Ancla de moneda visible más cercana.
        // ----------------------------------------------------

        let mejorMN = null;
        let mejorME = null;

        for (
            const anchor
            of currencyAnchors
        ) {

            /*
            Preferimos títulos que estén
            encima o aproximadamente a la
            misma altura de la etiqueta.
            */

            const dy =
                etiqueta.rect.centerY
                -
                anchor.rect.centerY;

            if (
                dy < -50
            ) {
                continue;
            }

            const distancia =
                Math.abs(dy);

            if (
                anchor.moneda === 'MN'
            ) {

                if (
                    mejorMN === null
                    ||
                    distancia
                    <
                    mejorMN.distancia
                ) {

                    mejorMN = {
                        distancia:
                            distancia,

                        anchor:
                            anchor
                    };
                }
            }

            if (
                anchor.moneda === 'ME'
            ) {

                if (
                    mejorME === null
                    ||
                    distancia
                    <
                    mejorME.distancia
                ) {

                    mejorME = {
                        distancia:
                            distancia,

                        anchor:
                            anchor
                    };
                }
            }
        }

        if (
            mejorMN
            &&
            (
                !mejorME
                ||
                mejorMN.distancia
                <
                mejorME.distancia
            )
        ) {

            etiqueta.currency =
                'MN';

            etiqueta.currencyEvidence.push(
                'ANCLA_MN_MAS_CERCANA:' +
                mejorMN.anchor.text
            );

            continue;
        }

        if (
            mejorME
            &&
            (
                !mejorMN
                ||
                mejorME.distancia
                <
                mejorMN.distancia
            )
        ) {

            etiqueta.currency =
                'ME';

            etiqueta.currencyEvidence.push(
                'ANCLA_ME_MAS_CERCANA:' +
                mejorME.anchor.text
            );

            continue;
        }
    }

    /*
    Fallback metodológico seguro:

    Si existe UNA SOLA etiqueta visible exacta
    en toda la página y el control de moneda
    validado externamente es MN, esa etiqueta
    puede asociarse a la sección visible MN.
    */

    if (
        ahorro.length === 1
        &&
        MONEDA_ACTUAL === 'MN'
        &&
        ahorro[0].currency
        === 'NO_CLASIFICADA'
    ) {

        ahorro[0].currency =
            'MN';

        ahorro[0].currencyEvidence.push(
            'UNICA_ETIQUETA_VISIBLE_Y_CONTROL_MONEDA_MN'
        );
    }

    // ========================================================
    // UBICACIONES DE PROMEDIO
    // ========================================================

    const promedios = [];

    for (
        const el
        of posiblesEtiquetas
    ) {

        if (!visible(el)) {
            continue;
        }

        const texto =
            limpiar(
                el.innerText
                ||
                el.textContent
            );

        if (
            normal(texto)
            !== 'promedio'
        ) {
            continue;
        }

        if (
            !elementoTerminalConTexto(
                el,
                'promedio'
            )
        ) {
            continue;
        }

        const tabla =
            el.closest(
                'table'
            );

        const fila =
            el.closest(
                'tr'
            );

        const ancestros =
            tablasAncestro(el);

        let moneda =
            'NO_CLASIFICADA';

        const evidencias = [];

        for (
            const id
            of ancestros
        ) {

            const nid =
                normal(id)
                .replace(
                    /[^a-z0-9]/g,
                    ''
                );

            if (
                nid.includes(
                    'actualmn'
                )
                ||
                nid.includes(
                    'monedanacional'
                )
            ) {

                moneda = 'MN';

                evidencias.push(
                    'ID_ANCESTRO:' +
                    id
                );
            }

            if (
                nid.includes(
                    'actualme'
                )
                ||
                nid.includes(
                    'monedaextranjera'
                )
            ) {

                moneda = 'ME';

                evidencias.push(
                    'ID_ANCESTRO:' +
                    id
                );
            }
        }

        promedios.push({
            text:
                texto,

            tag:
                el.tagName,

            id:
                el.id || '',

            tableId:
                tabla
                ? tabla.id || ''
                : '',

            rowIndex:
                fila
                ? fila.rowIndex
                : null,

            rect:
                rectInfo(el),

            ancestorTableIds:
                ancestros,

            currency:
                moneda,

            currencyEvidence:
                evidencias
        });
    }

    // ========================================================
    // MÉTRICAS DE CADA TABLA VISIBLE
    // ========================================================

    const tables = [];

    for (
        const tabla
        of tablasVisibles
    ) {

        const indice =
            tablaIndice.get(
                tabla
            );

        const key =
            tablaKey(
                tabla,
                indice
            );

        const filas =
            Array.from(
                tabla.rows || []
            );

        let maxCols = 0;
        let numericCount = 0;
        let missingCount = 0;
        let ahorroCount = 0;
        let promedioCount = 0;

        const textosCortos = [];

        for (
            const fila
            of filas
        ) {

            maxCols =
                Math.max(
                    maxCols,
                    fila.cells.length
                );

            for (
                const celda
                of Array.from(
                    fila.cells
                )
            ) {

                if (!visible(celda)) {
                    continue;
                }

                /*
                Para no contar contenido repetido
                de tablas anidadas, las métricas
                textuales usan celdas terminales.
                */

                if (
                    celda.querySelector(
                        'table'
                    )
                ) {
                    continue;
                }

                const texto =
                    limpiar(
                        celda.innerText
                        ||
                        celda.textContent
                    );

                const n =
                    normal(texto);

                if (
                    n ===
                    'depositos de ahorro'
                ) {

                    ahorroCount++;
                }

                if (
                    n ===
                    'promedio'
                ) {

                    promedioCount++;
                }

                if (
                    esNumero(texto)
                ) {

                    numericCount++;
                }

                if (
                    esFaltante(texto)
                ) {

                    missingCount++;
                }

                if (
                    texto
                    &&
                    texto.length <= 80
                    &&
                    !esNumero(texto)
                    &&
                    !esFaltante(texto)
                ) {

                    textosCortos.push(
                        texto
                    );
                }
            }
        }

        const unicos = [];

        const vistosTexto =
            new Set();

        for (
            const texto
            of textosCortos
        ) {

            const clave =
                normal(texto);

            if (
                vistosTexto.has(
                    clave
                )
            ) {
                continue;
            }

            vistosTexto.add(
                clave
            );

            unicos.push(
                texto
            );
        }

        const idNormal =
            normal(
                tabla.id || ''
            );

        const parentTable =
            tabla.parentElement
            ? tabla.parentElement.closest(
                'table'
            )
            : null;

        const textoTotal =
            normal(
                tabla.innerText
                ||
                tabla.textContent
            );

        tables.push({
            key:
                key,

            id:
                tabla.id || '',

            parentTableId:
                parentTable
                ? parentTable.id || ''
                : '',

            rows:
                filas.length,

            maxCols:
                maxCols,

            numericCount:
                numericCount,

            missingCount:
                missingCount,

            ahorroExacto:
                ahorroCount,

            promedioExacto:
                promedioCount,

            idPareceDataZone:
                (
                    idNormal.includes(
                        'datazone'
                    )
                    ||
                    idNormal.includes(
                        'datagrid'
                    )
                ),

            contieneMNTexto:
                textoTotal.includes(
                    'moneda nacional'
                ),

            contieneMETexto:
                textoTotal.includes(
                    'moneda extranjera'
                ),

            shortTexts:
                unicos.slice(
                    0,
                    40
                ),

            rect:
                rectInfo(tabla),

            element:
                tabla
        });
    }

    // ========================================================
    // ETIQUETA MN
    // ========================================================

    const etiquetasMN =
        ahorro.filter(
            x =>
                x.currency === 'MN'
        );

    let etiquetaMN =
        null;

    if (
        etiquetasMN.length === 1
    ) {

        etiquetaMN =
            etiquetasMN[0];
    }

    // ========================================================
    // ASOCIACIÓN DE TABLAS NUMÉRICAS CON AHORRO MN
    // ========================================================

    const numericCandidates = [];

    if (
        etiquetaMN !== null
    ) {

        for (
            const tabla
            of tables
        ) {

            const cantidadDatos =
                tabla.numericCount
                +
                tabla.missingCount;

            if (
                cantidadDatos < 5
            ) {
                continue;
            }

            let score = 0;

            const evidencias = [];

            const tablaEl =
                tabla.element;

            const tablaEtiqueta =
                etiquetaMN.tableElement;

            // Misma tabla inmediata.
            if (
                tablaEtiqueta
                &&
                tablaEl === tablaEtiqueta
            ) {

                score += 100;

                evidencias.push(
                    'MISMA_TABLA_DE_ETIQUETA'
                );
            }

            // La tabla de la etiqueta contiene
            // esta tabla numérica anidada.
            if (
                tablaEtiqueta
                &&
                tablaEtiqueta.contains(
                    tablaEl
                )
                &&
                tablaEtiqueta !== tablaEl
            ) {

                score += 90;

                evidencias.push(
                    'DESCENDIENTE_DE_TABLA_ETIQUETA'
                );
            }

            // La tabla numérica contiene
            // la etiqueta.
            if (
                tablaEl.contains(
                    etiquetaMN.element
                )
            ) {

                score += 80;

                evidencias.push(
                    'TABLA_CONTIENE_ETIQUETA'
                );
            }

            if (
                tabla.idPareceDataZone
            ) {

                score += 35;

                evidencias.push(
                    'ID_PARECE_DATAZONE'
                );
            }

            const overlap =
                horizontalOverlap(
                    etiquetaMN.rect,
                    tabla.rect
                );

            score += (
                overlap
                * 10
            );

            if (
                overlap > 0
            ) {

                evidencias.push(
                    'SOLAPAMIENTO_HORIZONTAL='
                    +
                    overlap.toFixed(4)
                );
            }

            const distancia =
                verticalDistance(
                    etiquetaMN.rect,
                    tabla.rect
                );

            if (
                distancia <= 600
            ) {

                score += (
                    Math.max(
                        0,
                        10
                        -
                        distancia / 60
                    )
                );

                evidencias.push(
                    'PROXIMIDAD_VERTICAL='
                    +
                    distancia.toFixed(2)
                );
            }

            numericCandidates.push({
                key:
                    tabla.key,

                id:
                    tabla.id,

                parentTableId:
                    tabla.parentTableId,

                rows:
                    tabla.rows,

                maxCols:
                    tabla.maxCols,

                numericCount:
                    tabla.numericCount,

                missingCount:
                    tabla.missingCount,

                idPareceDataZone:
                    tabla.idPareceDataZone,

                score:
                    score,

                evidence:
                    evidencias
            });
        }

        numericCandidates.sort(
            (a, b) =>
                b.score - a.score
        );
    }

    // ========================================================
    // CANDIDATOS DE TABLA CON NOMBRES BANCARIOS
    // ========================================================

    const cabecerasNoBanco =
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
            'tasas'
        ]);

    const bankTableCandidates = [];

    for (
        const tabla
        of tables
    ) {

        const posiblesNombres = [];

        for (
            const texto
            of tabla.shortTexts
        ) {

            const n =
                normal(texto);

            if (
                cabecerasNoBanco.has(
                    n
                )
            ) {
                continue;
            }

            if (
                n === 'promedio'
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
                ||
                n.includes(
                    'personas naturales'
                )
                ||
                n.includes(
                    'personas juridicas'
                )
            ) {
                continue;
            }

            /*
            No afirmamos todavía que sean bancos.
            Son textos cortos candidatos.
            */

            posiblesNombres.push(
                texto
            );
        }

        let score = 0;

        const evidencias = [];

        if (
            tabla.promedioExacto > 0
        ) {

            score += 60;

            evidencias.push(
                'CONTIENE_PROMEDIO'
            );
        }

        if (
            posiblesNombres.length >= 5
        ) {

            score += 30;

            evidencias.push(
                'VARIOS_TEXTOS_CORTOS_CANDIDATOS'
            );
        }

        if (
            tabla.idPareceDataZone
        ) {

            score += 10;

            evidencias.push(
                'ID_PARECE_DATAZONE'
            );
        }

        if (
            etiquetaMN !== null
        ) {

            const tablaEl =
                tabla.element;

            const tablaEtiqueta =
                etiquetaMN.tableElement;

            if (
                tablaEtiqueta
                &&
                tablaEtiqueta.contains(
                    tablaEl
                )
            ) {

                score += 40;

                evidencias.push(
                    'DESCENDIENTE_DE_SECCION_AHORRO_MN'
                );
            }

            if (
                tablaEl.contains(
                    etiquetaMN.element
                )
            ) {

                score += 30;

                evidencias.push(
                    'MISMO_CONTENEDOR_DE_AHORRO_MN'
                );
            }

            const distancia =
                verticalDistance(
                    etiquetaMN.rect,
                    tabla.rect
                );

            if (
                distancia <= 700
            ) {

                score += 10;

                evidencias.push(
                    'PROXIMO_A_AHORRO_MN'
                );
            }
        }

        if (
            score > 0
        ) {

            bankTableCandidates.push({
                key:
                    tabla.key,

                id:
                    tabla.id,

                parentTableId:
                    tabla.parentTableId,

                rows:
                    tabla.rows,

                maxCols:
                    tabla.maxCols,

                promedioExacto:
                    tabla.promedioExacto,

                numericCount:
                    tabla.numericCount,

                score:
                    score,

                candidateTexts:
                    posiblesNombres.slice(
                        0,
                        30
                    ),

                evidence:
                    evidencias
            });
        }
    }

    bankTableCandidates.sort(
        (a, b) =>
            b.score - a.score
    );

    // ========================================================
    // LIMPIAR OBJETOS NO SERIALIZABLES
    // ========================================================

    const ahorroSalida =
        ahorro.map(
            (x, i) => ({
                index:
                    i + 1,

                text:
                    x.text,

                tag:
                    x.tag,

                id:
                    x.id,

                tableId:
                    x.tableId,

                rowIndex:
                    x.rowIndex,

                cellIndex:
                    x.cellIndex,

                rect:
                    x.rect,

                ancestorTableIds:
                    x.ancestorTableIds,

                currency:
                    x.currency,

                currencyEvidence:
                    x.currencyEvidence
            })
        );

    const tablesSalida =
        tables.map(
            x => ({
                key:
                    x.key,

                id:
                    x.id,

                parentTableId:
                    x.parentTableId,

                rows:
                    x.rows,

                maxCols:
                    x.maxCols,

                numericCount:
                    x.numericCount,

                missingCount:
                    x.missingCount,

                ahorroExacto:
                    x.ahorroExacto,

                promedioExacto:
                    x.promedioExacto,

                idPareceDataZone:
                    x.idPareceDataZone,

                contieneMNTexto:
                    x.contieneMNTexto,

                contieneMETexto:
                    x.contieneMETexto,

                shortTexts:
                    x.shortTexts,

                rect:
                    x.rect
            })
        );

    return {
        currentCurrency:
            MONEDA_ACTUAL,

        currencyAnchors:
            currencyAnchors,

        ahorro:
            ahorroSalida,

        ahorroVisibleCount:
            ahorroSalida.length,

        ahorroMNCount:
            ahorroSalida.filter(
                x =>
                    x.currency === 'MN'
            ).length,

        ahorroMECount:
            ahorroSalida.filter(
                x =>
                    x.currency === 'ME'
            ).length,

        ahorroAmbiguousCount:
            ahorroSalida.filter(
                x =>
                    x.currency ===
                    'NO_CLASIFICADA'
            ).length,

        promedios:
            promedios,

        tables:
            tablesSalida,

        numericCandidates:
            numericCandidates,

        bankTableCandidates:
            bankTableCandidates,

        bestNumericCandidate:
            (
                numericCandidates.length > 0
                ? numericCandidates[0]
                : null
            ),

        bestBankTableCandidate:
            (
                bankTableCandidates.length > 0
                ? bankTableCandidates[0]
                : null
            )
    };
    """

    try:

        return navegador.execute_script(
            script,
            "MN"
        )

    except WebDriverException as error:

        raise RuntimeError(
            "Falló el diagnóstico estructural "
            f"de X3: {error}"
        ) from error


# ============================================================
# 17. MOSTRAR DIAGNÓSTICO ESTRUCTURAL
# ============================================================

def mostrar_diagnostico(
    diagnostico
):

    # ========================================================
    # A. ETIQUETAS DEPÓSITOS DE AHORRO
    # ========================================================

    titulo(
        "ETIQUETAS VISIBLES EXACTAS "
        "'DEPÓSITOS DE AHORRO'"
    )

    escribir(
        f"Total visible exacto = "
        f"{diagnostico['ahorroVisibleCount']}"
    )

    escribir(
        f"Clasificadas MN = "
        f"{diagnostico['ahorroMNCount']}"
    )

    escribir(
        f"Clasificadas ME = "
        f"{diagnostico['ahorroMECount']}"
    )

    escribir(
        f"No clasificadas = "
        f"{diagnostico['ahorroAmbiguousCount']}"
    )

    for item in diagnostico[
        "ahorro"
    ]:

        escribir()
        escribir(
            f"ETIQUETA #{item['index']}"
        )

        escribir(
            f"  texto = "
            f"{item['text']!r}"
        )

        escribir(
            f"  tag = "
            f"{item['tag']!r}"
        )

        escribir(
            f"  id propio = "
            f"{item['id']!r}"
        )

        escribir(
            f"  tabla inmediata = "
            f"{item['tableId']!r}"
        )

        escribir(
            f"  fila = "
            f"{item['rowIndex']}"
        )

        escribir(
            f"  celda = "
            f"{item['cellIndex']}"
        )

        escribir(
            f"  tablas ancestro = "
            f"{item['ancestorTableIds']}"
        )

        escribir(
            f"  moneda clasificada = "
            f"{item['currency']}"
        )

        escribir(
            f"  evidencia moneda = "
            f"{item['currencyEvidence']}"
        )

        escribir(
            f"  geometría = "
            f"{item['rect']}"
        )

    # ========================================================
    # B. ANCLAS MONETARIAS
    # ========================================================

    titulo(
        "ANCLAS VISIBLES DE MONEDA"
    )

    for numero, item in enumerate(
        diagnostico[
            "currencyAnchors"
        ],
        start=1
    ):

        escribir(
            f"{numero}. "
            f"moneda={item['moneda']} | "
            f"tag={item['tag']} | "
            f"id={item['id']!r} | "
            f"tabla={item['tableId']!r} | "
            f"text={item['text']!r}"
        )

    # ========================================================
    # C. PROMEDIO
    # ========================================================

    titulo(
        "UBICACIONES VISIBLES EXACTAS DE PROMEDIO"
    )

    escribir(
        f"Total Promedio visible exacto = "
        f"{len(diagnostico['promedios'])}"
    )

    for numero, item in enumerate(
        diagnostico[
            "promedios"
        ],
        start=1
    ):

        escribir()
        escribir(
            f"PROMEDIO #{numero}"
        )

        escribir(
            f"  tag = "
            f"{item['tag']!r}"
        )

        escribir(
            f"  id = "
            f"{item['id']!r}"
        )

        escribir(
            f"  tabla inmediata = "
            f"{item['tableId']!r}"
        )

        escribir(
            f"  fila = "
            f"{item['rowIndex']}"
        )

        escribir(
            f"  tablas ancestro = "
            f"{item['ancestorTableIds']}"
        )

        escribir(
            f"  moneda por evidencia de IDs = "
            f"{item['currency']}"
        )

        escribir(
            f"  evidencia = "
            f"{item['currencyEvidence']}"
        )

    # ========================================================
    # D. TABLAS NUMÉRICAS ASOCIADAS
    # ========================================================

    titulo(
        "DATAZONES / TABLAS NUMÉRICAS "
        "CANDIDATAS ASOCIADAS A AHORRO MN"
    )

    candidatos_numericos = diagnostico[
        "numericCandidates"
    ]

    if not candidatos_numericos:

        escribir(
            "<NINGUNA TABLA NUMÉRICA "
            "PUDO ASOCIARSE>"
        )

    else:

        for numero, tabla in enumerate(
            candidatos_numericos[
                :10
            ],
            start=1
        ):

            escribir()
            escribir(
                f"CANDIDATO NUMÉRICO #{numero}"
            )

            escribir(
                f"  id = "
                f"{tabla['id']!r}"
            )

            escribir(
                f"  key = "
                f"{tabla['key']!r}"
            )

            escribir(
                f"  parentTableId = "
                f"{tabla['parentTableId']!r}"
            )

            escribir(
                f"  filas = "
                f"{tabla['rows']}"
            )

            escribir(
                f"  máximo columnas = "
                f"{tabla['maxCols']}"
            )

            escribir(
                f"  celdas numéricas = "
                f"{tabla['numericCount']}"
            )

            escribir(
                f"  faltantes = "
                f"{tabla['missingCount']}"
            )

            escribir(
                f"  ID parece DataZone = "
                f"{tabla['idPareceDataZone']}"
            )

            escribir(
                f"  score asociación = "
                f"{tabla['score']}"
            )

            escribir(
                f"  evidencia = "
                f"{tabla['evidence']}"
            )

    # ========================================================
    # E. DÓNDE APARECEN LOS BANCOS
    # ========================================================

    titulo(
        "TABLAS CANDIDATAS DONDE APARECEN "
        "LOS NOMBRES BANCARIOS"
    )

    candidatos_bancos = diagnostico[
        "bankTableCandidates"
    ]

    if not candidatos_bancos:

        escribir(
            "<NO SE PUDO IDENTIFICAR "
            "UNA TABLA DE NOMBRES>"
        )

    else:

        for numero, tabla in enumerate(
            candidatos_bancos[
                :10
            ],
            start=1
        ):

            escribir()
            escribir(
                f"CANDIDATO BANCOS #{numero}"
            )

            escribir(
                f"  id = "
                f"{tabla['id']!r}"
            )

            escribir(
                f"  key = "
                f"{tabla['key']!r}"
            )

            escribir(
                f"  parentTableId = "
                f"{tabla['parentTableId']!r}"
            )

            escribir(
                f"  filas = "
                f"{tabla['rows']}"
            )

            escribir(
                f"  máximo columnas = "
                f"{tabla['maxCols']}"
            )

            escribir(
                f"  Promedio exacto en tabla = "
                f"{tabla['promedioExacto']}"
            )

            escribir(
                f"  score = "
                f"{tabla['score']}"
            )

            escribir(
                f"  evidencia = "
                f"{tabla['evidence']}"
            )

            escribir(
                "  textos candidatos "
                "a nombres:"
            )

            for texto in tabla[
                "candidateTexts"
            ]:

                escribir(
                    f"    - {texto}"
                )

    # ========================================================
    # F. INVENTARIO REDUCIDO DE TABLAS
    # ========================================================

    titulo(
        "INVENTARIO DE TABLAS VISIBLES RELEVANTES"
    )

    relevantes = [
        tabla
        for tabla in diagnostico[
            "tables"
        ]
        if (
            tabla[
                "ahorroExacto"
            ]
            > 0
            or
            tabla[
                "promedioExacto"
            ]
            > 0
            or
            tabla[
                "numericCount"
            ]
            >= 5
            or
            tabla[
                "idPareceDataZone"
            ]
        )
    ]

    for numero, tabla in enumerate(
        relevantes,
        start=1
    ):

        escribir()
        escribir(
            f"TABLA #{numero}"
        )

        escribir(
            f"  id = "
            f"{tabla['id']!r}"
        )

        escribir(
            f"  key = "
            f"{tabla['key']!r}"
        )

        escribir(
            f"  parentTableId = "
            f"{tabla['parentTableId']!r}"
        )

        escribir(
            f"  filas = "
            f"{tabla['rows']}"
        )

        escribir(
            f"  maxCols = "
            f"{tabla['maxCols']}"
        )

        escribir(
            f"  ahorroExacto = "
            f"{tabla['ahorroExacto']}"
        )

        escribir(
            f"  promedioExacto = "
            f"{tabla['promedioExacto']}"
        )

        escribir(
            f"  numericCount = "
            f"{tabla['numericCount']}"
        )

        escribir(
            f"  missingCount = "
            f"{tabla['missingCount']}"
        )

        escribir(
            f"  idPareceDataZone = "
            f"{tabla['idPareceDataZone']}"
        )


# ============================================================
# 18. CLASIFICACIÓN FINAL
# ============================================================

def clasificar_diagnostico(
    diagnostico
):

    titulo(
        "CLASIFICACIÓN FINAL DEL DIAGNÓSTICO X3"
    )

    ahorro_total = diagnostico[
        "ahorroVisibleCount"
    ]

    ahorro_mn = diagnostico[
        "ahorroMNCount"
    ]

    mejor_numerica = diagnostico[
        "bestNumericCandidate"
    ]

    mejor_bancos = diagnostico[
        "bestBankTableCandidate"
    ]

    promedios = diagnostico[
        "promedios"
    ]

    escribir(
        f"Etiquetas visibles exactas "
        f"'Depósitos de Ahorro' = "
        f"{ahorro_total}"
    )

    escribir(
        f"Etiquetas identificadas como MN = "
        f"{ahorro_mn}"
    )

    # --------------------------------------------------------
    # Buscar Promedio vinculado razonablemente
    # a la estructura MN.
    # --------------------------------------------------------

    promedio_mn_evidente = [
        item
        for item in promedios
        if item[
            "currency"
        ]
        == "MN"
    ]

    promedio_en_tabla_bancos = []

    if mejor_bancos is not None:

        id_tabla_bancos = mejor_bancos[
            "id"
        ]

        for item in promedios:

            if (
                id_tabla_bancos
                and
                (
                    item[
                        "tableId"
                    ]
                    == id_tabla_bancos
                    or
                    id_tabla_bancos
                    in item[
                        "ancestorTableIds"
                    ]
                )
            ):

                promedio_en_tabla_bancos.append(
                    item
                )

    hay_promedio_asociado = (
        len(
            promedio_mn_evidente
        )
        > 0
        or
        len(
            promedio_en_tabla_bancos
        )
        > 0
    )

    escribir(
        f"Promedio asociado a MN/tabla "
        f"de bancos = "
        f"{hay_promedio_asociado}"
    )

    # --------------------------------------------------------
    # Mostrar selección diagnóstica.
    # --------------------------------------------------------

    if mejor_numerica is not None:

        escribir()
        escribir(
            "TABLA NUMÉRICA / DATAZONE "
            "MÁS ASOCIADA:"
        )

        escribir(
            f"  id = "
            f"{mejor_numerica['id']!r}"
        )

        escribir(
            f"  key = "
            f"{mejor_numerica['key']!r}"
        )

        escribir(
            f"  filas = "
            f"{mejor_numerica['rows']}"
        )

        escribir(
            f"  maxCols = "
            f"{mejor_numerica['maxCols']}"
        )

        escribir(
            f"  ID parece DataZone = "
            f"{mejor_numerica['idPareceDataZone']}"
        )

        escribir(
            f"  evidencia = "
            f"{mejor_numerica['evidence']}"
        )

    else:

        escribir()
        escribir(
            "TABLA NUMÉRICA / DATAZONE "
            "MÁS ASOCIADA = <NO IDENTIFICADA>"
        )

    if mejor_bancos is not None:

        escribir()
        escribir(
            "TABLA MÁS PROBABLE DE "
            "NOMBRES BANCARIOS:"
        )

        escribir(
            f"  id = "
            f"{mejor_bancos['id']!r}"
        )

        escribir(
            f"  key = "
            f"{mejor_bancos['key']!r}"
        )

        escribir(
            f"  Promedio exacto = "
            f"{mejor_bancos['promedioExacto']}"
        )

        escribir(
            f"  evidencia = "
            f"{mejor_bancos['evidence']}"
        )

        escribir(
            "  textos candidatos:"
        )

        for texto in mejor_bancos[
            "candidateTexts"
        ]:

            escribir(
                f"    - {texto}"
            )

    else:

        escribir()
        escribir(
            "TABLA DE NOMBRES BANCARIOS "
            "= <NO IDENTIFICADA>"
        )

    # ========================================================
    # CRITERIO DE ÉXITO DEL DIAGNÓSTICO
    # ========================================================

    exito = (
        ahorro_total >= 1
        and
        ahorro_mn == 1
        and
        mejor_numerica is not None
        and
        mejor_bancos is not None
        and
        hay_promedio_asociado
    )

    escribir()

    if exito:

        escribir(
            "ESTADO = "
            "ESTRUCTURA_X3_MN_DIAGNOSTICADA"
        )

        escribir()
        escribir(
            "La sección de Depósitos de Ahorro "
            "en Moneda Nacional quedó identificada "
            "estructuralmente."
        )

        escribir(
            "Esto TODAVÍA NO valida la extracción "
            "de valores."
        )

        escribir(
            "El siguiente paso será una prueba "
            "de extracción para 30/11/2015 "
            "utilizando exclusivamente los IDs "
            "y relaciones realmente observados."
        )

    else:

        escribir(
            "ESTADO = "
            "ESTRUCTURA_X3_MN_AMBIGUA"
        )

        escribir()
        escribir(
            "No se programará todavía la "
            "extracción de tasas."
        )

        escribir(
            "Primero deberá revisarse este TXT, "
            "el HTML y la captura para resolver "
            "la estructura sin inventar IDs "
            "ni offsets."
        )


# ============================================================
# 19. MAIN
# ============================================================

def main():

    navegador = None

    try:

        CARPETA_SALIDA.mkdir(
            parents=True,
            exist_ok=True
        )

        titulo(
            "DIAGNÓSTICO X3 "
            "- TASA PASIVA DEPÓSITOS DE AHORRO MN"
        )

        escribir(
            "Fecha única consultada: 30/11/2015"
        )

        escribir(
            "Fuente: SBS - Tasas Pasivas "
            "por Tipo de Depósito y "
            "Empresa Bancaria"
        )

        escribir()
        escribir(
            "Este script:"
        )

        escribir(
            "  - NO extrae tasas;"
        )

        escribir(
            "  - NO consulta otros meses;"
        )

        escribir(
            "  - NO interpola;"
        )

        escribir(
            "  - NO homologa nombres;"
        )

        escribir(
            "  - NO selecciona bancos;"
        )

        escribir(
            "  - NO presupone IDs de moneda, "
            "entidad, bancos o DataZone."
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

        asegurar_pagina_real(
            navegador
        )

        # ====================================================
        # A. ESTABLECER FECHA
        # ====================================================

        titulo(
            "ESTABLECER FECHA OBJETIVO"
        )

        establecer_fecha(
            navegador
        )

        # ====================================================
        # B. VALIDACIÓN PRE-CONSULTA
        # ====================================================

        estado_pre = validar_estado_formulario(
            navegador,
            "DESPUÉS DE ESTABLECER FECHA / ANTES DE CONSULTAR"
        )

        escribir()
        escribir(
            "[OK] Contexto pre-consulta validado:"
        )

        escribir(
            "  fecha visible = 30/11/2015"
        )

        escribir(
            "  fecha interna = equivalente a 30/11/2015"
        )

        escribir(
            "  moneda = MN"
        )

        escribir(
            "  entidad = B"
        )

        # ====================================================
        # C. CONSULTAR
        # ====================================================

        titulo(
            "CONSULTA SBS"
        )

        respuesta = consultar(
            navegador
        )

        escribir(
            f"respuesta = "
            f"{respuesta['respuesta']}"
        )

        escribir(
            f"periodo_confirmado = "
            f"{respuesta['periodo_confirmado']}"
        )

        escribir(
            f"cantidad_confirmaciones = "
            f"{len(respuesta['confirmaciones'])}"
        )

        for item in respuesta[
            "confirmaciones"
        ]:

            escribir(
                f"  id={item.get('id')!r} | "
                f"text={item.get('text')!r}"
            )

        # ====================================================
        # D. VALIDACIÓN POST-CONSULTA
        # ====================================================

        estado_post = validar_estado_formulario(
            navegador,
            "DESPUÉS DE CONSULTAR"
        )

        escribir()
        escribir(
            "[OK] Contexto post-consulta validado:"
        )

        escribir(
            "  fecha visible = 30/11/2015"
        )

        escribir(
            "  fecha interna = equivalente a 30/11/2015"
        )

        escribir(
            "  moneda = MN"
        )

        escribir(
            "  entidad = B"
        )

        # ====================================================
        # E. SIN INFORMACIÓN
        # ====================================================

        if (
            respuesta[
                "respuesta"
            ]
            == "SIN_INFORMACION"
        ):

            titulo(
                "RESULTADO"
            )

            escribir(
                "ESTADO = "
                "SIN_INFORMACION_30_11_2015"
            )

            escribir(
                f"periodo_confirmado = "
                f"{respuesta['periodo_confirmado']}"
            )

            return

        # ====================================================
        # F. EXIGIR PERÍODO EXACTO
        # ====================================================

        if (
            respuesta[
                "respuesta"
            ]
            != "PERIODO_CONFIRMADO"
            or
            not respuesta[
                "periodo_confirmado"
            ]
        ):

            raise RuntimeError(
                "El resultado no confirmó "
                "explícitamente 'al 30/11/2015'."
            )

        escribir()
        escribir(
            "[OK] SBS confirmó explícitamente "
            "'al 30/11/2015'."
        )

        # ====================================================
        # G. DIAGNÓSTICO ESTRUCTURAL
        # ====================================================

        diagnostico = diagnosticar_estructura_x3(
            navegador
        )

        mostrar_diagnostico(
            diagnostico
        )

        # ====================================================
        # H. GUARDAR EVIDENCIA ANTES DE CLASIFICAR
        # ====================================================

        ARCHIVO_HTML.write_text(
            navegador.page_source,
            encoding="utf-8"
        )

        navegador.save_screenshot(
            str(
                ARCHIVO_PNG
            )
        )

        escribir()
        escribir(
            "[OK] HTML histórico guardado."
        )

        escribir(
            "[OK] Captura del diagnóstico guardada."
        )

        # ====================================================
        # I. CLASIFICACIÓN
        # ====================================================

        clasificar_diagnostico(
            diagnostico
        )

    except Exception as error:

        titulo(
            "ERROR TÉCNICO DEL DIAGNÓSTICO"
        )

        escribir(
            f"Tipo = "
            f"{type(error).__name__}"
        )

        escribir(
            f"Detalle = "
            f"{repr(error)}"
        )

        escribir()
        escribir(
            "Este error NO equivale "
            "a ausencia de información SBS."
        )

        # Intentar conservar la evidencia
        # que exista hasta ese momento.
        if navegador is not None:

            try:

                ARCHIVO_HTML.write_text(
                    navegador.page_source,
                    encoding="utf-8"
                )

            except Exception:

                pass

            try:

                navegador.save_screenshot(
                    str(
                        ARCHIVO_PNG
                    )
                )

            except Exception:

                pass

        raise

    finally:

        CARPETA_SALIDA.mkdir(
            parents=True,
            exist_ok=True
        )

        ARCHIVO_TXT.write_text(
            "\n".join(
                lineas
            ),
            encoding="utf-8"
        )

        if navegador is not None:

            try:

                navegador.quit()

                print()
                print(
                    "[OK] Chrome cerrado."
                )

            except Exception:

                pass

        print()
        print("=" * 118)
        print("DIAGNÓSTICO FINALIZADO")
        print("=" * 118)

        print()
        print(
            "TXT:"
        )

        print(
            ARCHIVO_TXT
        )

        print()
        print(
            "HTML:"
        )

        print(
            ARCHIVO_HTML
        )

        print()
        print(
            "PNG:"
        )

        print(
            ARCHIVO_PNG
        )


# ============================================================
# 20. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":

    main()