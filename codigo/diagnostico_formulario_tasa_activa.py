# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico técnico del formulario SBS - Tasa activa por tipo de crédito y empresa bancaria

from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib
import re

import requests
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

ARCHIVO_SALIDA = (
    CARPETA_SALIDA
    / "diagnostico_formulario_tasa_activa.txt"
)

# Queremos conocer los valores reales.
# Por eso los campos ocultos también se imprimen completos.
MOSTRAR_HIDDEN_COMPLETOS = False

TIMEOUT = 30

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/153.0 Safari/537.36 "
    "Trabajo académico UNCP - "
    "contacto estudiante - diagnóstico SBS"
)


# ============================================================
# 2. UTILIDAD PARA GUARDAR Y MOSTRAR
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
# 3. REPRESENTAR VALORES
# ============================================================

def representar_valor(
    valor,
    completo=True
):

    if valor is None:
        return "<SIN VALOR>"

    valor = str(valor)

    if completo:
        return repr(valor)

    # Resumen técnico para valores muy grandes
    sha256 = hashlib.sha256(
        valor.encode(
            "utf-8",
            errors="replace"
        )
    ).hexdigest()

    prefijo = valor[:100]
    sufijo = valor[-100:]

    return (
        f"<LONGITUD={len(valor)} "
        f"SHA256={sha256} "
        f"INICIO={prefijo!r} "
        f"FINAL={sufijo!r}>"
    )


# ============================================================
# 4. CONSULTA ÚNICA
# ============================================================

def obtener_pagina():

    sesion = requests.Session()

    sesion.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8"
        ),
        "Accept-Language": (
            "es-PE,es;q=0.9,en;q=0.8"
        ),
    })

    respuesta = sesion.get(
        URL,
        timeout=TIMEOUT,
        allow_redirects=True
    )

    respuesta.raise_for_status()

    return sesion, respuesta


# ============================================================
# 5. INFORMACIÓN GENERAL HTTP
# ============================================================

def diagnosticar_http(
    sesion,
    respuesta
):

    titulo(
        "1. CONSULTA HTTP"
    )

    escribir(
        f"URL solicitada: {URL}"
    )

    escribir(
        f"URL final: {respuesta.url}"
    )

    escribir(
        f"Status HTTP: {respuesta.status_code}"
    )

    escribir(
        f"Método utilizado por este diagnóstico: GET"
    )

    escribir(
        f"Content-Type: "
        f"{respuesta.headers.get('Content-Type')}"
    )

    escribir(
        f"Content-Length recibido: "
        f"{len(respuesta.content)} bytes"
    )

    escribir(
        f"Encoding detectado: "
        f"{respuesta.encoding}"
    )

    escribir()
    escribir(
        "Parámetros de la URL inicial:"
    )

    consulta = parse_qs(
        urlparse(URL).query,
        keep_blank_values=True
    )

    for nombre, valores in consulta.items():

        escribir(
            f"  {nombre} = {valores}"
        )

    escribir()
    escribir(
        "Cookies establecidas en la sesión:"
    )

    if not sesion.cookies:

        escribir(
            "  <NINGUNA>"
        )

    else:

        for cookie in sesion.cookies:

            escribir(
                f"  {cookie.name} = "
                f"{cookie.value!r}"
            )


# ============================================================
# 6. FORMULARIOS
# ============================================================

def diagnosticar_formularios(
    soup,
    base_url
):

    titulo(
        "2. FORMULARIOS HTML"
    )

    formularios = soup.find_all(
        "form"
    )

    escribir(
        f"Número de formularios encontrados: "
        f"{len(formularios)}"
    )

    for indice, form in enumerate(
        formularios,
        start=1
    ):

        escribir()
        escribir(
            f"FORMULARIO #{indice}"
        )

        escribir(
            f"  id     = {form.get('id')!r}"
        )

        escribir(
            f"  name   = {form.get('name')!r}"
        )

        metodo = (
            form.get(
                "method",
                "GET"
            )
            .upper()
        )

        escribir(
            f"  method = {metodo!r}"
        )

        action = form.get(
            "action"
        )

        escribir(
            f"  action original = "
            f"{action!r}"
        )

        action_absoluta = urljoin(
            base_url,
            action or ""
        )

        escribir(
            f"  action absoluta = "
            f"{action_absoluta!r}"
        )

        escribir(
            f"  enctype = "
            f"{form.get('enctype')!r}"
        )


# ============================================================
# 7. INPUTS
# ============================================================

def diagnosticar_inputs(
    soup
):

    titulo(
        "3. INPUTS Y PARÁMETROS REALES"
    )

    inputs = soup.find_all(
        "input"
    )

    escribir(
        f"Número total de <input>: "
        f"{len(inputs)}"
    )

    for indice, campo in enumerate(
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

        nombre = campo.get(
            "name"
        )

        identificador = campo.get(
            "id"
        )

        valor = campo.get(
            "value"
        )

        escribir()
        escribir(
            f"INPUT #{indice}"
        )

        escribir(
            f"  type    = {tipo!r}"
        )

        escribir(
            f"  id      = {identificador!r}"
        )

        escribir(
            f"  name    = {nombre!r}"
        )

        # Mostrar valores reales.
        if (
            tipo == "hidden"
            and not MOSTRAR_HIDDEN_COMPLETOS
            and valor is not None
            and len(str(valor)) > 500
        ):

            valor_mostrado = representar_valor(
                valor,
                completo=False
            )

        else:

            valor_mostrado = representar_valor(
                valor,
                completo=True
            )

        escribir(
            f"  value   = {valor_mostrado}"
        )

        escribir(
            f"  checked = "
            f"{campo.has_attr('checked')}"
        )

        escribir(
            f"  disabled = "
            f"{campo.has_attr('disabled')}"
        )

        escribir(
            f"  readonly = "
            f"{campo.has_attr('readonly')}"
        )

        if campo.get(
            "onclick"
        ):

            escribir(
                f"  onclick = "
                f"{campo.get('onclick')!r}"
            )

        if campo.get(
            "onchange"
        ):

            escribir(
                f"  onchange = "
                f"{campo.get('onchange')!r}"
            )


# ============================================================
# 8. CAMPOS ASP.NET
# ============================================================

def diagnosticar_aspnet(
    soup
):

    titulo(
        "4. CAMPOS OCULTOS ASP.NET"
    )

    prefijos_interes = (
        "__VIEWSTATE",
        "__EVENTVALIDATION",
        "__EVENTTARGET",
        "__EVENTARGUMENT",
        "__VIEWSTATEGENERATOR",
        "__SCROLLPOSITION",
        "__LASTFOCUS",
        "__ASYNCPOST",
    )

    encontrados = []

    for campo in soup.find_all(
        "input"
    ):

        nombre = campo.get(
            "name",
            ""
        )

        if any(
            nombre.startswith(prefijo)
            for prefijo
            in prefijos_interes
        ):

            encontrados.append(
                campo
            )

    escribir(
        f"Campos ASP.NET detectados: "
        f"{len(encontrados)}"
    )

    for campo in encontrados:

        nombre = campo.get(
            "name"
        )

        valor = campo.get(
            "value",
            ""
        )

        escribir()
        escribir(
            f"Nombre: {nombre!r}"
        )

        escribir(
            f"ID: {campo.get('id')!r}"
        )

        escribir(
            f"Longitud del valor: "
            f"{len(valor)}"
        )

        if MOSTRAR_HIDDEN_COMPLETOS:

            escribir(
                f"Valor real: {valor!r}"
            )

        else:

            escribir(
                "Valor técnico: "
                + representar_valor(
                    valor,
                    completo=False
                )
            )


# ============================================================
# 9. SELECTS / AÑO / MES
# ============================================================

def diagnosticar_selects(
    soup
):

    titulo(
        "5. CONTROLES <SELECT>"
    )

    selects = soup.find_all(
        "select"
    )

    escribir(
        f"Número de selects: "
        f"{len(selects)}"
    )

    for indice, select in enumerate(
        selects,
        start=1
    ):

        escribir()
        escribir(
            f"SELECT #{indice}"
        )

        escribir(
            f"  id   = "
            f"{select.get('id')!r}"
        )

        escribir(
            f"  name = "
            f"{select.get('name')!r}"
        )

        if select.get(
            "onchange"
        ):

            escribir(
                f"  onchange = "
                f"{select.get('onchange')!r}"
            )

        opciones = select.find_all(
            "option"
        )

        escribir(
            f"  Número de opciones: "
            f"{len(opciones)}"
        )

        for opcion in opciones:

            texto = opcion.get_text(
                " ",
                strip=True
            )

            valor = opcion.get(
                "value"
            )

            seleccionada = (
                opcion.has_attr(
                    "selected"
                )
            )

            escribir(
                "    "
                f"value={valor!r} "
                f"selected={seleccionada} "
                f"text={texto!r}"
            )


# ============================================================
# 10. TEXTAREAS Y BOTONES
# ============================================================

def diagnosticar_otros_controles(
    soup
):

    titulo(
        "6. BOTONES, TEXTAREAS Y CONTROLES CON EVENTOS"
    )

    for etiqueta in (
        "button",
        "textarea"
    ):

        elementos = soup.find_all(
            etiqueta
        )

        escribir()
        escribir(
            f"<{etiqueta}> encontrados: "
            f"{len(elementos)}"
        )

        for elemento in elementos:

            escribir(
                f"  id={elemento.get('id')!r} "
                f"name={elemento.get('name')!r} "
                f"value={elemento.get('value')!r} "
                f"text={elemento.get_text(' ', strip=True)!r}"
            )

    escribir()
    escribir(
        "Elementos con onclick/onchange/oncommand:"
    )

    contador = 0

    for elemento in soup.find_all(
        True
    ):

        eventos = {}

        for evento in (
            "onclick",
            "onchange",
            "oncommand",
            "onselectedindexchanged"
        ):

            valor = elemento.get(
                evento
            )

            if valor:

                eventos[
                    evento
                ] = valor

        if eventos:

            contador += 1

            escribir()
            escribir(
                f"  Etiqueta: "
                f"<{elemento.name}>"
            )

            escribir(
                f"  id={elemento.get('id')!r}"
            )

            escribir(
                f"  name={elemento.get('name')!r}"
            )

            for evento, valor in eventos.items():

                escribir(
                    f"  {evento}="
                    f"{valor!r}"
                )

    escribir()
    escribir(
        f"Total controles con eventos: "
        f"{contador}"
    )


# ============================================================
# 11. BUSCAR CONTROLES DE FECHA
# ============================================================

def diagnosticar_fecha(
    soup
):

    titulo(
        "7. CANDIDATOS A CONTROL DE FECHA / AÑO / MES"
    )

    palabras = (
        "fecha",
        "date",
        "calendar",
        "radDatePicker".lower(),
        "year",
        "anio",
        "año",
        "month",
        "mes",
    )

    encontrados = []

    for elemento in soup.find_all(
        True
    ):

        atributos = " ".join(
            [
                str(elemento.get("id", "")),
                str(elemento.get("name", "")),
                str(elemento.get("class", "")),
                str(elemento.get("title", "")),
                str(elemento.get("placeholder", "")),
            ]
        ).lower()

        if any(
            palabra.lower() in atributos
            for palabra in palabras
        ):

            encontrados.append(
                elemento
            )

    escribir(
        f"Candidatos encontrados: "
        f"{len(encontrados)}"
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
            f"  onchange="
            f"{elemento.get('onchange')!r}"
        )

        escribir(
            f"  onclick="
            f"{elemento.get('onclick')!r}"
        )


# ============================================================
# 12. BUSCAR CONTROLES DE MONEDA
# ============================================================

def diagnosticar_moneda(
    soup
):

    titulo(
        "8. CONTROL DE MONEDA"
    )

    textos_objetivo = (
        "moneda nacional",
        "moneda extranjera",
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    escribir(
        "Labels/textos relacionados:"
    )

    coincidencias = 0

    for elemento in soup.find_all(
        True
    ):

        texto = elemento.get_text(
            " ",
            strip=True
        )

        texto_normalizado = (
            texto.lower()
        )

        if any(
            objetivo in texto_normalizado
            for objetivo
            in textos_objetivo
        ):

            # Evitar imprimir contenedores gigantes
            if len(texto) > 300:
                continue

            coincidencias += 1

            escribir()
            escribir(
                f"<{elemento.name}> "
                f"id={elemento.get('id')!r} "
                f"name={elemento.get('name')!r}"
            )

            escribir(
                f"  texto={texto!r}"
            )

            escribir(
                f"  href={elemento.get('href')!r}"
            )

            escribir(
                f"  value={elemento.get('value')!r}"
            )

            escribir(
                f"  onclick={elemento.get('onclick')!r}"
            )

    escribir()
    escribir(
        f"Coincidencias textuales: "
        f"{coincidencias}"
    )

    # --------------------------------------------------------
    # Radios
    # --------------------------------------------------------

    escribir()
    escribir(
        "Inputs radio:"
    )

    radios = soup.find_all(
        "input",
        attrs={"type": "radio"}
    )

    if not radios:

        escribir(
            "  <NINGUNO>"
        )

    for radio in radios:

        escribir(
            f"  id={radio.get('id')!r} "
            f"name={radio.get('name')!r} "
            f"value={radio.get('value')!r} "
            f"checked={radio.has_attr('checked')}"
        )


# ============================================================
# 13. SCRIPTS EXTERNOS
# ============================================================

def diagnosticar_scripts_externos(
    soup,
    base_url
):

    titulo(
        "9. SCRIPTS EXTERNOS CARGADOS POR LA PÁGINA"
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

        absoluta = urljoin(
            base_url,
            src
        )

        escribir(
            f"  {absoluta}"
        )


# ============================================================
# 14. BUSCAR LLAMADAS SECUNDARIAS EN JAVASCRIPT
# ============================================================

def diagnosticar_javascript(
    soup,
    base_url
):

    titulo(
        "10. POSIBLES LLAMADAS SECUNDARIAS / POSTBACK / AJAX"
    )

    patrones_interes = [
        r"__doPostBack\s*\([^)]*\)",
        r"\$\.ajax\s*\([^;]*",
        r"\$\.get\s*\([^;]*",
        r"\$\.post\s*\([^;]*",
        r"fetch\s*\([^;]*",
        r"XMLHttpRequest",
        r"PageMethods\.[A-Za-z0-9_]+",
        r"WebService",
        r"Callback",
        r"RadAjax",
        r"ajaxRequest",
        r"[\"'][^\"']+\.aspx[^\"']*[\"']",
        r"[\"'][^\"']+\.asmx[^\"']*[\"']",
        r"[\"'][^\"']+\.svc[^\"']*[\"']",
        r"[\"'][^\"']+WebResource\.axd[^\"']*[\"']",
        r"[\"'][^\"']+ScriptResource\.axd[^\"']*[\"']",
    ]

    scripts_inline = [
        script.get_text(
            "\n",
            strip=False
        )
        for script in soup.find_all(
            "script"
        )
        if not script.get(
            "src"
        )
    ]

    javascript = "\n".join(
        scripts_inline
    )

    escribir(
        f"Bloques JS inline: "
        f"{len(scripts_inline)}"
    )

    escribir(
        f"Longitud JS inline combinada: "
        f"{len(javascript)} caracteres"
    )

    coincidencias_totales = []

    for patron in patrones_interes:

        coincidencias = re.findall(
            patron,
            javascript,
            flags=re.IGNORECASE
        )

        for coincidencia in coincidencias:

            coincidencias_totales.append(
                coincidencia
            )

    # Eliminar duplicados conservando orden
    unicos = []

    vistos = set()

    for item in coincidencias_totales:

        item_limpio = (
            str(item).strip()
        )

        if item_limpio not in vistos:

            vistos.add(
                item_limpio
            )

            unicos.append(
                item_limpio
            )

    escribir()
    escribir(
        "Coincidencias encontradas:"
    )

    if not unicos:

        escribir(
            "  <NINGUNA COINCIDENCIA DIRECTA>"
        )

    else:

        for item in unicos:

            escribir(
                f"  {item}"
            )

    # --------------------------------------------------------
    # URLs candidatas en todo el HTML
    # --------------------------------------------------------

    escribir()
    escribir(
        "URLs/endpoints candidatos encontrados "
        "en atributos href/src/action:"
    )

    urls = []

    for etiqueta in soup.find_all(
        True
    ):

        for atributo in (
            "href",
            "src",
            "action"
        ):

            valor = etiqueta.get(
                atributo
            )

            if not valor:
                continue

            absoluta = urljoin(
                base_url,
                valor
            )

            if absoluta not in urls:

                urls.append(
                    absoluta
                )

    for url in urls:

        if any(
            palabra in url.lower()
            for palabra in (
                ".aspx",
                ".asmx",
                ".svc",
                ".axd",
                "ajax",
                "callback",
                "telerik",
            )
        ):

            escribir(
                f"  {url}"
            )


# ============================================================
# 15. POSTBACK TARGETS
# ============================================================

def diagnosticar_postbacks(
    soup
):

    titulo(
        "11. EVENTTARGETS / __doPostBack"
    )

    html = str(
        soup
    )

    patron = re.compile(
        r"__doPostBack\("
        r"[\"']([^\"']+)[\"']"
        r"\s*,\s*"
        r"[\"']([^\"']*)[\"']"
        r"\)",
        flags=re.IGNORECASE
    )

    coincidencias = patron.findall(
        html
    )

    unicos = []

    vistos = set()

    for target, argumento in coincidencias:

        clave = (
            target,
            argumento
        )

        if clave not in vistos:

            vistos.add(
                clave
            )

            unicos.append(
                clave
            )

    escribir(
        f"Postbacks explícitos encontrados: "
        f"{len(unicos)}"
    )

    for target, argumento in unicos:

        escribir()
        escribir(
            f"  __EVENTTARGET = "
            f"{target!r}"
        )

        escribir(
            f"  __EVENTARGUMENT = "
            f"{argumento!r}"
        )


# ============================================================
# 16. DETECTAR SI LA TABLA YA VIENE EN EL HTML
# ============================================================

def diagnosticar_tabla_actual(
    soup
):

    titulo(
        "12. ¿LA TABLA YA VIENE EN EL HTML DEL GET?"
    )

    texto_pagina = soup.get_text(
        " ",
        strip=True
    )

    pruebas = [
        "Moneda Nacional",
        "Moneda Extranjera",
        "Consumo",
        "Hipotecarios",
        "BBVA",
        "Promedio",
    ]

    for prueba in pruebas:

        encontrado = (
            prueba.lower()
            in texto_pagina.lower()
        )

        escribir(
            f"{prueba!r}: "
            f"{encontrado}"
        )

    tablas = soup.find_all(
        "table"
    )

    escribir()
    escribir(
        f"Número de <table> en el HTML: "
        f"{len(tablas)}"
    )

    # Mostrar solo candidatos que contengan
    # palabras relevantes.
    for indice, tabla in enumerate(
        tablas,
        start=1
    ):

        texto = tabla.get_text(
            " ",
            strip=True
        )

        texto_lower = texto.lower()

        if any(
            palabra in texto_lower
            for palabra in (
                "consumo",
                "corporativos",
                "hipotecarios",
                "moneda nacional",
                "bbva",
            )
        ):

            escribir()
            escribir(
                f"TABLA CANDIDATA #{indice}"
            )

            escribir(
                f"  id={tabla.get('id')!r}"
            )

            escribir(
                f"  class={tabla.get('class')!r}"
            )

            escribir(
                "  texto inicial="
                f"{texto[:1000]!r}"
            )


# ============================================================
# 17. CONTROLES ESPECIALES TELERIK / RADDATEPICKER
# ============================================================

def diagnosticar_telerik(
    soup
):

    titulo(
        "13. TELERIK / RADDATEPICKER"
    )

    html = str(
        soup
    )

    palabras = [
        "RadDatePicker",
        "Telerik",
        "RadCalendar",
        "RadAjax",
        "WebResource.axd",
        "ScriptResource.axd",
    ]

    for palabra in palabras:

        cantidad = len(
            re.findall(
                re.escape(
                    palabra
                ),
                html,
                flags=re.IGNORECASE
            )
        )

        escribir(
            f"{palabra}: "
            f"{cantidad} ocurrencias"
        )

    escribir()
    escribir(
        "Elementos cuyo id/name/class contiene "
        "'rad', 'fecha', 'date' o 'calendar':"
    )

    for elemento in soup.find_all(
        True
    ):

        cadena = " ".join([
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
        ])

        if re.search(
            r"(rad|fecha|date|calendar)",
            cadena,
            flags=re.IGNORECASE
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
                f"  type={elemento.get('type')!r}"
            )

            escribir(
                f"  value={elemento.get('value')!r}"
            )

            escribir(
                f"  class={elemento.get('class')!r}"
            )


# ============================================================
# 18. RESUMEN AUTOMÁTICO
# ============================================================

def resumen_final(
    soup
):

    titulo(
        "14. RESUMEN AUTOMÁTICO"
    )

    forms = soup.find_all(
        "form"
    )

    escribir(
        f"Formularios: {len(forms)}"
    )

    if forms:

        form = forms[0]

        escribir(
            "Primer formulario:"
        )

        escribir(
            f"  method="
            f"{form.get('method', 'GET').upper()}"
        )

        escribir(
            f"  action="
            f"{form.get('action')!r}"
        )

    hidden = soup.find_all(
        "input",
        attrs={
            "type": "hidden"
        }
    )

    escribir(
        f"Campos hidden: "
        f"{len(hidden)}"
    )

    escribir(
        "Nombres de campos hidden:"
    )

    for campo in hidden:

        escribir(
            f"  {campo.get('name')!r}"
        )

    radios = soup.find_all(
        "input",
        attrs={
            "type": "radio"
        }
    )

    escribir(
        f"Radios: {len(radios)}"
    )

    selects = soup.find_all(
        "select"
    )

    escribir(
        f"Selects: {len(selects)}"
    )

    escribir()
    escribir(
        "Este diagnóstico NO realizó "
        "ninguna consulta histórica."
    )

    escribir(
        "Este diagnóstico NO seleccionó bancos."
    )

    escribir(
        "Este diagnóstico NO construyó "
        "una base de datos."
    )

    escribir(
        "Solo se realizó un GET a la "
        "página oficial SBS indicada."
    )


# ============================================================
# 19. GUARDAR TXT
# ============================================================

def guardar_reporte():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    contenido = "\n".join(
        lineas_reporte
    )

    ARCHIVO_SALIDA.write_text(
        contenido,
        encoding="utf-8"
    )

    print()
    print("=" * 110)

    print(
        "REPORTE GUARDADO EN:"
    )

    print(
        ARCHIVO_SALIDA
    )

    print("=" * 110)


# ============================================================
# 20. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    try:

        sesion, respuesta = (
            obtener_pagina()
        )

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        diagnosticar_http(
            sesion,
            respuesta
        )

        diagnosticar_formularios(
            soup,
            respuesta.url
        )

        diagnosticar_inputs(
            soup
        )

        diagnosticar_aspnet(
            soup
        )

        diagnosticar_selects(
            soup
        )

        diagnosticar_otros_controles(
            soup
        )

        diagnosticar_fecha(
            soup
        )

        diagnosticar_moneda(
            soup
        )

        diagnosticar_scripts_externos(
            soup,
            respuesta.url
        )

        diagnosticar_javascript(
            soup,
            respuesta.url
        )

        diagnosticar_postbacks(
            soup
        )

        diagnosticar_tabla_actual(
            soup
        )

        diagnosticar_telerik(
            soup
        )

        resumen_final(
            soup
        )

    except Exception as error:

        titulo(
            "ERROR DURANTE EL DIAGNÓSTICO"
        )

        escribir(
            repr(error)
        )

        raise

    finally:

        guardar_reporte()


# ============================================================
# 21. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()