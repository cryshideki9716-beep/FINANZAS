# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Diagnóstico estructural de archivos piloto SBS

from pathlib import Path
import re

import xlrd
from openpyxl import load_workbook


# ============================================================
# 1. CARPETAS
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_PILOTO = (
    RAIZ
    / "datos_crudos"
    / "sbs_piloto"
)


# ============================================================
# 2. PALABRAS QUE NOS INTERESA LOCALIZAR
# ============================================================

PALABRAS_CLAVE = [
    "empresa",
    "empresas",
    "moneda nacional",
    "moneda extranjera",
    "saldo final",
    "créditos directos",
    "creditos directos",
    "total créditos",
    "total creditos",
]


# ============================================================
# 3. LIMPIAR TEXTO SOLO PARA BUSCAR
# ============================================================

def normalizar_texto(valor):
    """
    Convierte una celda a texto comparable.

    NO modifica el archivo original.
    """

    if valor is None:
        return ""

    texto = str(valor)

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip().lower()


# ============================================================
# 4. DETECTAR FORMATO REAL
# ============================================================

def detectar_formato(ruta):

    with open(ruta, "rb") as archivo:
        cabecera = archivo.read(8)

    firma_ole = bytes.fromhex(
        "D0CF11E0A1B11AE1"
    )

    firmas_zip = (
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
    )

    if cabecera == firma_ole:
        return "XLS_OLE"

    if cabecera.startswith(firmas_zip):
        return "XLSX_ZIP"

    return "DESCONOCIDO"


# ============================================================
# 5. CONVERTIR XLS/OLE EN MATRICES DE SOLO LECTURA
# ============================================================

def leer_xls(ruta):

    libro = xlrd.open_workbook(
        filename=str(ruta),
        on_demand=True
    )

    hojas = []

    for nombre in libro.sheet_names():

        hoja = libro.sheet_by_name(nombre)

        filas = []

        for i in range(hoja.nrows):

            fila = [
                hoja.cell_value(i, j)
                for j in range(hoja.ncols)
            ]

            filas.append(fila)

        hojas.append({
            "nombre": nombre,
            "filas": filas,
            "nfilas": hoja.nrows,
            "ncolumnas": hoja.ncols,
        })

    libro.release_resources()

    return hojas


# ============================================================
# 6. CONVERTIR XLSX/ZIP EN MATRICES DE SOLO LECTURA
# ============================================================

def leer_xlsx(ruta):

    archivo_binario = open(
        ruta,
        "rb"
    )

    libro = load_workbook(
        archivo_binario,
        read_only=True,
        data_only=True
    )

    hojas = []

    for nombre in libro.sheetnames:

        hoja = libro[nombre]

        filas = []

        for fila in hoja.iter_rows(
            values_only=True
        ):

            filas.append(
                list(fila)
            )

        ncolumnas = max(
            (
                len(fila)
                for fila in filas
            ),
            default=0
        )

        hojas.append({
            "nombre": nombre,
            "filas": filas,
            "nfilas": len(filas),
            "ncolumnas": ncolumnas,
        })

    libro.close()
    archivo_binario.close()

    return hojas


# ============================================================
# 7. LEER SEGÚN FORMATO
# ============================================================

def leer_archivo(ruta):

    formato = detectar_formato(ruta)

    if formato == "XLS_OLE":

        hojas = leer_xls(ruta)

    elif formato == "XLSX_ZIP":

        hojas = leer_xlsx(ruta)

    else:

        hojas = []

    return formato, hojas


# ============================================================
# 8. BUSCAR PALABRAS CLAVE
# ============================================================

def buscar_palabras(filas):

    hallazgos = []

    for numero_fila, fila in enumerate(filas):

        texto_fila = " | ".join(
            normalizar_texto(valor)
            for valor in fila
        )

        encontradas = []

        for palabra in PALABRAS_CLAVE:

            if palabra in texto_fila:

                encontradas.append(
                    palabra
                )

        if encontradas:

            hallazgos.append({
                "fila": numero_fila,
                "palabras": encontradas,
                "contenido": fila,
            })

    return hallazgos


# ============================================================
# 9. IDENTIFICAR FILAS NO VACÍAS INICIALES
# ============================================================

def primeras_filas_no_vacias(
    filas,
    limite=15
):

    resultado = []

    for numero_fila, fila in enumerate(filas):

        tiene_datos = any(
            normalizar_texto(valor) != ""
            for valor in fila
        )

        if tiene_datos:

            resultado.append(
                (numero_fila, fila)
            )

        if len(resultado) >= limite:
            break

    return resultado


# ============================================================
# 10. ANALIZAR UN ARCHIVO
# ============================================================

def analizar_archivo(ruta):

    print()
    print("=" * 90)

    print(
        "ARCHIVO:",
        ruta.name
    )

    print("=" * 90)

    formato, hojas = leer_archivo(
        ruta
    )

    print(
        "Formato real:",
        formato
    )

    print(
        "Número de hojas:",
        len(hojas)
    )

    if not hojas:

        print(
            "[ERROR] No se pudieron "
            "obtener hojas."
        )

        return

    for hoja in hojas:

        print()
        print("-" * 90)

        print(
            "HOJA:",
            hoja["nombre"]
        )

        print(
            "Dimensión:",
            hoja["nfilas"],
            "filas x",
            hoja["ncolumnas"],
            "columnas"
        )

        # ----------------------------------------------------
        # Buscar palabras clave
        # ----------------------------------------------------

        hallazgos = buscar_palabras(
            hoja["filas"]
        )

        print()
        print(
            "FILAS CON PALABRAS CLAVE:"
        )

        if not hallazgos:

            print(
                "  Ninguna encontrada."
            )

        else:

            for item in hallazgos[:20]:

                print()
                print(
                    f"  Fila {item['fila']}:"
                )

                print(
                    "  Palabras:",
                    item["palabras"]
                )

                print(
                    "  Contenido:",
                    item["contenido"]
                )

        # ----------------------------------------------------
        # Primeras filas no vacías
        # ----------------------------------------------------

        print()
        print(
            "PRIMERAS 15 FILAS NO VACÍAS:"
        )

        muestra = primeras_filas_no_vacias(
            hoja["filas"],
            limite=15
        )

        for numero, fila in muestra:

            print(
                f"  Fila {numero}:",
                fila
            )


# ============================================================
# 11. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 90)

    print(
        "DIAGNÓSTICO DE ESTRUCTURA SBS"
    )

    print(
        "COMPARACIÓN DEL PILOTO 2008-2025"
    )

    print("=" * 90)

    if not CARPETA_PILOTO.exists():

        print()
        print(
            "[ERROR] No existe:"
        )

        print(
            CARPETA_PILOTO
        )

        return

    archivos = [
    CARPETA_PILOTO / "creditos_2010_12.xls",
    CARPETA_PILOTO / "creditos_2011_12.xls",
    CARPETA_PILOTO / "creditos_2015_06.xls",
    CARPETA_PILOTO / "creditos_2020_06.xls",
]

    print()
    print(
        "Archivos encontrados:",
        len(archivos)
    )

    if not archivos:

        print(
            "No existen archivos piloto."
        )

        return

    for ruta in archivos:

        analizar_archivo(
            ruta
        )

    print()
    print("=" * 90)

    print(
        "DIAGNÓSTICO TERMINADO"
    )

    print("=" * 90)

    print()
    print(
        "No se modificó ningún archivo crudo."
    )

    print(
        "No se descargó ningún archivo adicional."
    )


# ============================================================
# 12. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()