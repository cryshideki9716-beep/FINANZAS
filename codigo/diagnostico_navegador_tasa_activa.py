# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico con navegador real - Tasa activa SBS por tipo de crédito y empresa bancaria

from pathlib import Path
from urllib.parse import urljoin
import hashlib
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
)

from bs4 import BeautifulSoup


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

URL = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIActivaTipoCreditoEmpresa.aspx?tip=B"
)

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_SALIDA = (
    RAIZ
    / "salidas"
    / "diagnosticos"
)

ARCHIVO_TXT = (
    CARPETA_SALIDA
    / "diagnostico_navegador_tasa_activa.txt"
)

ARCHIVO_HTML = (
    CARPETA_SALIDA
    / "tasa_activa_renderizada.html"
)

TIMEOUT = 60


# ============================================================
# 2. SALIDA
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
    escribir("=" * 110)
    escribir(texto)
    escribir("=" * 110)


def subtitulo(texto):

    escribir()
    escribir("-" * 110)
    escribir(texto)
    escribir("-" * 110)


# ============================================================
# 3. NORMALIZACIÓN
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

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


# ============================================================
# 4. CONFIGURAR CHROME
# ============================================================

def crear_navegador():

    opciones = webdriver.ChromeOptions()

    # IMPORTANTE:
    # No usamos --headless.
    # Queremos un Chrome real y visible.
    opciones.add_argument(
        "--start-maximized"
    )

    opciones.add_argument(
        "--lang=es-PE"
    )

    # Reducir mensajes innecesarios del navegador.
    opciones.add_experimental_option(
        "excludeSwitches",
        ["enable-logging"]
    )

    # Selenium 4 utiliza Selenium Manager y normalmente
    # encuentra Chrome/ChromeDriver automáticamente.
    navegador = webdriver.Chrome(
        options=opciones
    )

    navegador.set_page_load_timeout(
        TIMEOUT
    )

    return navegador


# ============================================================
# 5. ESPERAR DOCUMENTO
# ============================================================

def esperar_documento(
    navegador
):

    WebDriverWait(
        navegador,
        TIMEOUT
    ).until(
        lambda driver:
        driver.execute_script(
            "return document.readyState"
        )
        == "complete"
    )


# ============================================================
# 6. ESPERAR CONTENIDO SBS
# ============================================================

def esperar_pagina_real(
    navegador
):
    """
    Esperamos alguna señal del contenido real.

    No hacemos clic ni modificamos controles.
    """

    palabras_objetivo = (
        "consumo",
        "moneda nacional",
    )

    def pagina_tiene_contenido(
        driver
    ):

        try:

            cuerpo = driver.find_element(
                By.TAG_NAME,
                "body"
            )

            texto = cuerpo.text.lower()

            return any(
                palabra in texto
                for palabra
                in palabras_objetivo
            )

        except Exception:

            return False

    try:

        WebDriverWait(
            navegador,
            TIMEOUT
        ).until(
            pagina_tiene_contenido
        )

        return True

    except TimeoutException:

        return False


# ============================================================
# 7. DETECTAR POSIBLE BLOQUEO
# ============================================================

def detectar_bloqueo(
    texto_pagina
):

    texto = texto_pagina.lower()

    indicadores = [
        "incapsula",
        "imperva",
        "access denied",
        "request unsuccessful",
        "security check",
        "captcha",
        "verify you are human",
        "verifique que es humano",
    ]

    encontrados = [
        indicador
        for indicador
        in indicadores
        if indicador in texto
    ]

    return encontrados


# ============================================================
# 8. INFORMACIÓN DEL NAVEGADOR
# ============================================================

def diagnosticar_general(
    navegador,
    pagina_real,
    html
):

    titulo(
        "1. INFORMACIÓN GENERAL DEL NAVEGADOR"
    )

    escribir(
        f"URL solicitada: {URL}"
    )

    escribir(
        f"URL final: {navegador.current_url}"
    )

    escribir(
        f"Título: {navegador.title!r}"
    )

    escribir(
        f"¿Se detectó contenido SBS real?: "
        f"{pagina_real}"
    )

    escribir(
        f"Longitud HTML renderizado: "
        f"{len(html)} caracteres"
    )

    sha256 = hashlib.sha256(
        html.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    escribir(
        f"SHA256 HTML: {sha256}"
    )

    try:

        user_agent = navegador.execute_script(
            "return navigator.userAgent"
        )

    except Exception:

        user_agent = None

    escribir(
        f"User-Agent navegador: "
        f"{user_agent!r}"
    )

    try:

        cuerpo = navegador.find_element(
            By.TAG_NAME,
            "body"
        ).text

    except Exception:

        cuerpo = ""

    bloqueos = detectar_bloqueo(
        cuerpo
    )

    escribir(
        f"Indicadores de bloqueo detectados: "
        f"{bloqueos}"
    )

    escribir()
    escribir(
        "Primeros 1500 caracteres visibles:"
    )

    escribir(
        normalizar_texto(
            cuerpo
        )[:1500]
    )


# ============================================================
# 9. FORMULARIOS
# ============================================================

def diagnosticar_formularios(
    soup,
    base_url
):

    titulo(
        "2. FORMULARIOS"
    )

    formularios = soup.find_all(
        "form"
    )

    escribir(
        f"Formularios encontrados: "
        f"{len(formularios)}"
    )

    for numero, form in enumerate(
        formularios,
        start=1
    ):

        escribir()
        escribir(
            f"FORMULARIO #{numero}"
        )

        escribir(
            f"  id={form.get('id')!r}"
        )

        escribir(
            f"  name={form.get('name')!r}"
        )

        escribir(
            f"  method="
            f"{form.get('method', 'GET').upper()!r}"
        )

        action = form.get(
            "action"
        )

        escribir(
            f"  action original={action!r}"
        )

        escribir(
            "  action absoluta="
            f"{urljoin(base_url, action or '')!r}"
        )

        escribir(
            f"  enctype="
            f"{form.get('enctype')!r}"
        )


# ============================================================
# 10. TODOS LOS INPUTS
# ============================================================

def diagnosticar_inputs(
    soup
):

    titulo(
        "3. INPUTS"
    )

    inputs = soup.find_all(
        "input"
    )

    escribir(
        f"Inputs encontrados: "
        f"{len(inputs)}"
    )

    for numero, campo in enumerate(
        inputs,
        start=1
    ):

        tipo = (
            campo.get(
                "type",
                "text"
            )
            .lower()
        )

        valor = campo.get(
            "value"
        )

        escribir()
        escribir(
            f"INPUT #{numero}"
        )

        escribir(
            f"  type={tipo!r}"
        )

        escribir(
            f"  id={campo.get('id')!r}"
        )

        escribir(
            f"  name={campo.get('name')!r}"
        )

        # Los VIEWSTATE pueden ser enormes.
        if (
            valor is not None
            and len(str(valor)) > 300
        ):

            hash_valor = hashlib.sha256(
                str(valor).encode(
                    "utf-8",
                    errors="replace"
                )
            ).hexdigest()

            escribir(
                f"  value=<LONGITUD "
                f"{len(str(valor))}, "
                f"SHA256 {hash_valor}>"
            )

        else:

            escribir(
                f"  value={valor!r}"
            )

        escribir(
            f"  checked="
            f"{campo.has_attr('checked')}"
        )

        escribir(
            f"  disabled="
            f"{campo.has_attr('disabled')}"
        )

        escribir(
            f"  readonly="
            f"{campo.has_attr('readonly')}"
        )

        if campo.get(
            "onclick"
        ):

            escribir(
                f"  onclick="
                f"{campo.get('onclick')!r}"
            )

        if campo.get(
            "onchange"
        ):

            escribir(
                f"  onchange="
                f"{campo.get('onchange')!r}"
            )


# ============================================================
# 11. HIDDEN / ASP.NET
# ============================================================

def diagnosticar_hidden(
    soup
):

    titulo(
        "4. CAMPOS HIDDEN Y ASP.NET"
    )

    hidden = soup.find_all(
        "input",
        attrs={
            "type": "hidden"
        }
    )

    escribir(
        f"Hidden encontrados: "
        f"{len(hidden)}"
    )

    for campo in hidden:

        nombre = campo.get(
            "name"
        )

        valor = str(
            campo.get(
                "value",
                ""
            )
        )

        escribir()
        escribir(
            f"Nombre={nombre!r}"
        )

        escribir(
            f"ID={campo.get('id')!r}"
        )

        escribir(
            f"Longitud valor={len(valor)}"
        )

        if len(valor) <= 200:

            escribir(
                f"Valor={valor!r}"
            )

        else:

            sha256 = hashlib.sha256(
                valor.encode(
                    "utf-8",
                    errors="replace"
                )
            ).hexdigest()

            escribir(
                f"SHA256 valor={sha256}"
            )

            escribir(
                f"Inicio={valor[:80]!r}"
            )

            escribir(
                f"Final={valor[-80:]!r}"
            )


# ============================================================
# 12. SELECTS
# ============================================================

def diagnosticar_selects(
    soup
):

    titulo(
        "5. SELECTS"
    )

    selects = soup.find_all(
        "select"
    )

    escribir(
        f"Selects encontrados: "
        f"{len(selects)}"
    )

    for numero, select in enumerate(
        selects,
        start=1
    ):

        escribir()
        escribir(
            f"SELECT #{numero}"
        )

        escribir(
            f"  id={select.get('id')!r}"
        )

        escribir(
            f"  name={select.get('name')!r}"
        )

        escribir(
            f"  onchange="
            f"{select.get('onchange')!r}"
        )

        opciones = select.find_all(
            "option"
        )

        escribir(
            f"  opciones={len(opciones)}"
        )

        for opcion in opciones:

            escribir(
                "    "
                f"value={opcion.get('value')!r} "
                f"selected="
                f"{opcion.has_attr('selected')} "
                f"text="
                f"{opcion.get_text(' ', strip=True)!r}"
            )


# ============================================================
# 13. BOTONES
# ============================================================

def diagnosticar_botones(
    soup
):

    titulo(
        "6. BOTONES"
    )

    botones = []

    botones.extend(
        soup.find_all(
            "button"
        )
    )

    botones.extend(
        soup.find_all(
            "input",
            attrs={
                "type": re.compile(
                    r"^(submit|button|image)$",
                    re.I
                )
            }
        )
    )

    escribir(
        f"Botones encontrados: "
        f"{len(botones)}"
    )

    for numero, boton in enumerate(
        botones,
        start=1
    ):

        escribir()
        escribir(
            f"BOTÓN #{numero}"
        )

        escribir(
            f"  etiqueta=<{boton.name}>"
        )

        escribir(
            f"  type={boton.get('type')!r}"
        )

        escribir(
            f"  id={boton.get('id')!r}"
        )

        escribir(
            f"  name={boton.get('name')!r}"
        )

        escribir(
            f"  value={boton.get('value')!r}"
        )

        escribir(
            f"  text="
            f"{boton.get_text(' ', strip=True)!r}"
        )

        escribir(
            f"  onclick="
            f"{boton.get('onclick')!r}"
        )


# ============================================================
# 14. CONTROLES DE FECHA
# ============================================================

def diagnosticar_fecha(
    soup
):

    titulo(
        "7. CANDIDATOS A CONTROLES DE FECHA"
    )

    patron = re.compile(
        r"(fecha|date|calendar|mes|month|anio|año|year)",
        re.I
    )

    encontrados = []

    for elemento in soup.find_all(
        True
    ):

        atributos = " ".join([
            str(
                elemento.get(
                    "id",
                    ""
                )
            ),
            str(
                elemento.get(
                    "name",
                    ""
                )
            ),
            str(
                elemento.get(
                    "class",
                    ""
                )
            ),
            str(
                elemento.get(
                    "title",
                    ""
                )
            ),
            str(
                elemento.get(
                    "placeholder",
                    ""
                )
            ),
        ])

        if patron.search(
            atributos
        ):

            encontrados.append(
                elemento
            )

    escribir(
        f"Candidatos: {len(encontrados)}"
    )

    for elemento in encontrados:

        escribir()
        escribir(
            f"<{elemento.name}>"
        )

        escribir(
            f"  id={elemento.get('id')!r}"
        )

        escribir(
            f"  name={elemento.get('name')!r}"
        )

        escribir(
            f"  type={elemento.get('type')!r}"
        )

        escribir(
            f"  value={elemento.get('value')!r}"
        )

        escribir(
            f"  class={elemento.get('class')!r}"
        )

        escribir(
            f"  title={elemento.get('title')!r}"
        )

        escribir(
            f"  placeholder="
            f"{elemento.get('placeholder')!r}"
        )

        escribir(
            f"  onchange="
            f"{elemento.get('onchange')!r}"
        )

        escribir(
            f"  onclick="
            f"{elemento.get('onclick')!r}"
        )


# ============================================================
# 15. CONTROLES DE MONEDA
# ============================================================

def diagnosticar_moneda(
    soup
):

    titulo(
        "8. CONTROLES DE MONEDA"
    )

    escribir(
        "Inputs radio:"
    )

    radios = soup.find_all(
        "input",
        attrs={
            "type": "radio"
        }
    )

    for radio in radios:

        escribir()
        escribir(
            f"  id={radio.get('id')!r}"
        )

        escribir(
            f"  name={radio.get('name')!r}"
        )

        escribir(
            f"  value={radio.get('value')!r}"
        )

        escribir(
            f"  checked="
            f"{radio.has_attr('checked')}"
        )

        escribir(
            f"  onclick="
            f"{radio.get('onclick')!r}"
        )

    escribir()
    escribir(
        "Elementos cuyo texto contiene "
        "'Moneda Nacional' o "
        "'Moneda Extranjera':"
    )

    encontrados = []

    for elemento in soup.find_all(
        True
    ):

        texto = normalizar_texto(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        texto_lower = texto.lower()

        if (
            "moneda nacional"
            in texto_lower
            or
            "moneda extranjera"
            in texto_lower
        ):

            # Evitar contenedores de toda la página.
            if len(texto) > 250:
                continue

            encontrados.append(
                elemento
            )

    for elemento in encontrados:

        escribir()
        escribir(
            f"<{elemento.name}>"
        )

        escribir(
            f"  id={elemento.get('id')!r}"
        )

        escribir(
            f"  name={elemento.get('name')!r}"
        )

        escribir(
            f"  href={elemento.get('href')!r}"
        )

        escribir(
            f"  value={elemento.get('value')!r}"
        )

        escribir(
            f"  onclick="
            f"{elemento.get('onclick')!r}"
        )

        escribir(
            f"  texto="
            f"{normalizar_texto(elemento.get_text(' ', strip=True))!r}"
        )


# ============================================================
# 16. POSTBACKS / EVENTOS
# ============================================================

def diagnosticar_eventos(
    soup
):

    titulo(
        "9. POSTBACKS Y EVENTOS"
    )

    html = str(
        soup
    )

    patron_postback = re.compile(
        r"__doPostBack\("
        r"[\"']([^\"']+)[\"']"
        r"\s*,\s*"
        r"[\"']([^\"']*)[\"']"
        r"\)",
        re.I
    )

    postbacks = patron_postback.findall(
        html
    )

    vistos = set()

    escribir(
        "Postbacks explícitos:"
    )

    for target, argumento in postbacks:

        clave = (
            target,
            argumento
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        escribir()
        escribir(
            f"  __EVENTTARGET={target!r}"
        )

        escribir(
            f"  __EVENTARGUMENT={argumento!r}"
        )

    escribir()
    escribir(
        "Elementos con onclick/onchange:"
    )

    for elemento in soup.find_all(
        True
    ):

        onclick = elemento.get(
            "onclick"
        )

        onchange = elemento.get(
            "onchange"
        )

        if (
            onclick
            or onchange
        ):

            escribir()
            escribir(
                f"<{elemento.name}>"
            )

            escribir(
                f"  id={elemento.get('id')!r}"
            )

            escribir(
                f"  name={elemento.get('name')!r}"
            )

            escribir(
                f"  onclick={onclick!r}"
            )

            escribir(
                f"  onchange={onchange!r}"
            )


# ============================================================
# 17. BUSCAR CONSUMO
# ============================================================

def diagnosticar_consumo(
    soup
):

    titulo(
        "10. PRESENCIA DE 'CONSUMO'"
    )

    texto_pagina = normalizar_texto(
        soup.get_text(
            " ",
            strip=True
        )
    )

    aparece = (
        "consumo"
        in texto_pagina.lower()
    )

    escribir(
        f"¿Aparece 'Consumo'?: "
        f"{aparece}"
    )

    if aparece:

        escribir()
        escribir(
            "Filas <tr> que contienen "
            "'Consumo':"
        )

        for fila in soup.find_all(
            "tr"
        ):

            texto = normalizar_texto(
                fila.get_text(
                    " ",
                    strip=True
                )
            )

            if (
                "consumo"
                in texto.lower()
            ):

                escribir()
                escribir(
                    texto[:2000]
                )


# ============================================================
# 18. TABLAS Y POSIBLES BANCOS
# ============================================================

def diagnosticar_tablas(
    soup
):

    titulo(
        "11. TABLAS Y ENCABEZADOS"
    )

    tablas = soup.find_all(
        "table"
    )

    escribir(
        f"Tablas encontradas: "
        f"{len(tablas)}"
    )

    for numero, tabla in enumerate(
        tablas,
        start=1
    ):

        texto = normalizar_texto(
            tabla.get_text(
                " ",
                strip=True
            )
        )

        # Solo mostramos con detalle las tablas
        # relacionadas con la información financiera.
        relevante = any(
            palabra in texto.lower()
            for palabra in [
                "consumo",
                "moneda nacional",
                "corporativo",
                "hipotec",
                "empresa bancaria",
            ]
        )

        if not relevante:
            continue

        escribir()
        escribir(
            f"TABLA CANDIDATA #{numero}"
        )

        escribir(
            f"  id={tabla.get('id')!r}"
        )

        escribir(
            f"  class={tabla.get('class')!r}"
        )

        encabezados = []

        for celda in tabla.find_all(
            ["th", "td"]
        )[:80]:

            texto_celda = normalizar_texto(
                celda.get_text(
                    " ",
                    strip=True
                )
            )

            if texto_celda:

                encabezados.append(
                    texto_celda
                )

        escribir(
            "  Primeras celdas:"
        )

        for texto_celda in encabezados:

            escribir(
                f"    {texto_celda!r}"
            )

        escribir()
        escribir(
            "  Primeros 2000 caracteres "
            "de la tabla:"
        )

        escribir(
            texto[:2000]
        )


# ============================================================
# 19. BUSCAR TEXTOS TIPO BANCO
# ============================================================

def diagnosticar_posibles_bancos(
    soup
):

    titulo(
        "12. POSIBLES NOMBRES DE BANCOS VISIBLES"
    )

    candidatos = []

    for elemento in soup.find_all(
        ["th", "td", "span", "div"]
    ):

        texto = normalizar_texto(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not texto:
            continue

        if len(texto) > 100:
            continue

        texto_lower = texto.lower()

        if (
            "banco"
            in texto_lower
            or
            "bbva"
            in texto_lower
            or
            "interbank"
            in texto_lower
            or
            "scotiabank"
            in texto_lower
        ):

            candidatos.append(
                texto
            )

    unicos = []

    vistos = set()

    for texto in candidatos:

        if texto not in vistos:

            vistos.add(
                texto
            )

            unicos.append(
                texto
            )

    escribir(
        f"Candidatos únicos: "
        f"{len(unicos)}"
    )

    for texto in unicos:

        escribir(
            f"  {texto!r}"
        )


# ============================================================
# 20. SCRIPTS EXTERNOS
# ============================================================

def diagnosticar_scripts(
    soup,
    base_url
):

    titulo(
        "13. SCRIPTS EXTERNOS"
    )

    scripts = soup.find_all(
        "script",
        src=True
    )

    escribir(
        f"Scripts externos: "
        f"{len(scripts)}"
    )

    for script in scripts:

        src = script.get(
            "src"
        )

        escribir(
            "  "
            + urljoin(
                base_url,
                src
            )
        )


# ============================================================
# 21. COOKIES DEL NAVEGADOR
# ============================================================

def diagnosticar_cookies(
    navegador
):

    titulo(
        "14. COOKIES DEL NAVEGADOR"
    )

    try:

        cookies = navegador.get_cookies()

    except Exception:

        cookies = []

    escribir(
        f"Cookies encontradas: "
        f"{len(cookies)}"
    )

    for cookie in cookies:

        escribir()
        escribir(
            f"  name={cookie.get('name')!r}"
        )

        escribir(
            f"  domain={cookie.get('domain')!r}"
        )

        escribir(
            f"  path={cookie.get('path')!r}"
        )

        # No necesitamos imprimir el valor completo.
        valor = str(
            cookie.get(
                "value",
                ""
            )
        )

        escribir(
            f"  value_length={len(valor)}"
        )


# ============================================================
# 22. RESUMEN
# ============================================================

def resumen_final(
    soup,
    pagina_real
):

    titulo(
        "15. RESUMEN AUTOMÁTICO"
    )

    texto = normalizar_texto(
        soup.get_text(
            " ",
            strip=True
        )
    ).lower()

    escribir(
        f"Página real detectada: "
        f"{pagina_real}"
    )

    escribir(
        f"'Consumo' presente: "
        f"{'consumo' in texto}"
    )

    escribir(
        f"'Moneda Nacional' presente: "
        f"{'moneda nacional' in texto}"
    )

    escribir(
        f"'Moneda Extranjera' presente: "
        f"{'moneda extranjera' in texto}"
    )

    escribir(
        f"Formularios: "
        f"{len(soup.find_all('form'))}"
    )

    escribir(
        f"Inputs: "
        f"{len(soup.find_all('input'))}"
    )

    escribir(
        f"Hidden: "
        f"{len(soup.find_all('input', attrs={'type': 'hidden'}))}"
    )

    escribir(
        f"Selects: "
        f"{len(soup.find_all('select'))}"
    )

    escribir(
        f"Tablas: "
        f"{len(soup.find_all('table'))}"
    )

    escribir()
    escribir(
        "El navegador NO cambió la fecha."
    )

    escribir(
        "El navegador NO seleccionó moneda."
    )

    escribir(
        "El navegador NO seleccionó bancos."
    )

    escribir(
        "El navegador NO consultó meses históricos."
    )

    escribir(
        "El navegador NO realizó la descarga "
        "de los 211 meses."
    )


# ============================================================
# 23. GUARDAR RESULTADOS
# ============================================================

def guardar_resultados(
    html
):

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

    ARCHIVO_HTML.write_text(
        html,
        encoding="utf-8"
    )

    print()
    print("=" * 110)
    print("ARCHIVOS GUARDADOS")
    print("=" * 110)

    print(
        ARCHIVO_TXT
    )

    print(
        ARCHIVO_HTML
    )


# ============================================================
# 24. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    navegador = None
    html = ""

    try:

        titulo(
            "DIAGNÓSTICO SELENIUM - SBS TASA ACTIVA"
        )

        escribir(
            "Se abrirá únicamente la URL oficial con tip=B."
        )

        escribir(
            "No se realizará ninguna consulta histórica."
        )

        navegador = crear_navegador()

        escribir()
        escribir(
            "Abriendo Chrome..."
        )

        navegador.get(
            URL
        )

        # --------------------------------------------------------
        # PAUSA MANUAL PARA VERIFICACIÓN DE SEGURIDAD
        # --------------------------------------------------------
        # Si SBS muestra una comprobación tipo “no soy un robot”,
        # complétala manualmente en la ventana de Chrome.
        # El programa NO intenta automatizar ni evadir esa protección.
        print()
        print(
            "Si SBS pide verificar que no eres un robot, "
            "complétalo manualmente en Chrome."
        )
        input(
            "Cuando veas la página real de SBS, vuelve aquí "
            "y presiona ENTER... "
        )

        esperar_documento(
            navegador
        )

        # Damos unos segundos adicionales para
        # contenido cargado por JavaScript.
        time.sleep(
            3
        )

        pagina_real = esperar_pagina_real(
            navegador
        )

        # Un breve margen después de detectar contenido.
        if pagina_real:

            time.sleep(
                2
            )

        html = navegador.page_source

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        diagnosticar_general(
            navegador,
            pagina_real,
            html
        )

        diagnosticar_formularios(
            soup,
            navegador.current_url
        )

        diagnosticar_inputs(
            soup
        )

        diagnosticar_hidden(
            soup
        )

        diagnosticar_selects(
            soup
        )

        diagnosticar_botones(
            soup
        )

        diagnosticar_fecha(
            soup
        )

        diagnosticar_moneda(
            soup
        )

        diagnosticar_eventos(
            soup
        )

        diagnosticar_consumo(
            soup
        )

        diagnosticar_tablas(
            soup
        )

        diagnosticar_posibles_bancos(
            soup
        )

        diagnosticar_scripts(
            soup,
            navegador.current_url
        )

        diagnosticar_cookies(
            navegador
        )

        resumen_final(
            soup,
            pagina_real
        )

    except TimeoutException as error:

        titulo(
            "TIMEOUT"
        )

        escribir(
            repr(error)
        )

        if navegador is not None:

            try:

                html = navegador.page_source

            except Exception:

                pass

    except WebDriverException as error:

        titulo(
            "ERROR DE SELENIUM / CHROME"
        )

        escribir(
            repr(error)
        )

    except Exception as error:

        titulo(
            "ERROR GENERAL"
        )

        escribir(
            repr(error)
        )

        raise

    finally:

        if navegador is not None:

            try:

                navegador.quit()

            except Exception:

                pass

        guardar_resultados(
            html
        )


# ============================================================
# 25. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()