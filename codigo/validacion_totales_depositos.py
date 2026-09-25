# BRICEÑO LEON CRYSTELL HIDEKI
# Código: 2024200485D
# Tema 4: Dolarización del crédito y de los depósitos en el sistema financiero peruano
# Validación de totales - Movimiento de los Depósitos SBS B-2318

from pathlib import Path

from parser_piloto_depositos import (
    leer_archivo,
    detectar_tablas_monetarias,
    extraer_saldos,
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent

CARPETA_PILOTO = (
    RAIZ
    / "datos_crudos"
    / "sbs_piloto"
)

ARCHIVOS_CONTROL = [
    "depositos_2008_06.xls",
    "depositos_2010_12.xls",
    "depositos_2011_12.xls",
    "depositos_2015_06.xls",
    "depositos_2020_06.xls",
    "depositos_2025_12.xls",
]


# ============================================================
# 2. VALIDAR UNA MONEDA
# ============================================================

def validar_moneda(
    registros,
    moneda
):
    """
    Compara:

        suma de bancos individuales

    contra:

        TOTAL BANCA MÚLTIPLE

    para una moneda determinada.
    """

    individuales = [
        registro
        for registro in registros
        if not registro["es_agregado"]
    ]

    agregados = [
        registro
        for registro in registros
        if registro["es_agregado"]
    ]

    # --------------------------------------------------------
    # Debe existir exactamente un agregado.
    # --------------------------------------------------------

    if len(agregados) != 1:

        return {
            "moneda": moneda,
            "estado": "ERROR_AGREGADO",
            "cantidad_bancos": len(
                individuales
            ),
            "cantidad_agregados": len(
                agregados
            ),
            "suma_bancos": None,
            "total_sbs": None,
            "diferencia": None,
            "diferencia_absoluta": None,
            "diferencia_pct": None,
        }

    # --------------------------------------------------------
    # Suma de bancos individuales
    # --------------------------------------------------------

    suma_bancos = sum(
        registro["saldo_final"]
        for registro in individuales
    )

    # --------------------------------------------------------
    # Total oficial SBS
    # --------------------------------------------------------

    total_sbs = agregados[
        0
    ]["saldo_final"]

    # --------------------------------------------------------
    # Diferencias
    # --------------------------------------------------------

    diferencia = (
        suma_bancos
        - total_sbs
    )

    diferencia_absoluta = abs(
        diferencia
    )

    if total_sbs != 0:

        diferencia_pct = (
            diferencia
            / total_sbs
            * 100
        )

    else:

        diferencia_pct = None

    return {
        "moneda": moneda,
        "estado": "OK",
        "cantidad_bancos": len(
            individuales
        ),
        "cantidad_agregados": len(
            agregados
        ),
        "suma_bancos": suma_bancos,
        "total_sbs": total_sbs,
        "diferencia": diferencia,
        "diferencia_absoluta": diferencia_absoluta,
        "diferencia_pct": diferencia_pct,
    }


# ============================================================
# 3. ANALIZAR UN ARCHIVO
# ============================================================

def analizar_archivo(
    ruta
):

    formato, hojas = leer_archivo(
        ruta
    )

    tablas_mn, tablas_me = (
        detectar_tablas_monetarias(
            hojas
        )
    )

    if (
        len(tablas_mn) != 1
        or len(tablas_me) != 1
    ):

        print()
        print(
            "[ERROR]",
            ruta.name,
            "no contiene exactamente "
            "una tabla MN y una tabla ME."
        )

        return None

    registros_mn = extraer_saldos(
        tablas_mn[0]
    )

    registros_me = extraer_saldos(
        tablas_me[0]
    )

    validacion_mn = validar_moneda(
        registros_mn,
        "MN"
    )

    validacion_me = validar_moneda(
        registros_me,
        "ME"
    )

    return {
        "archivo": ruta.name,
        "formato": formato,
        "hoja_mn": tablas_mn[
            0
        ]["nombre_hoja"],
        "hoja_me": tablas_me[
            0
        ]["nombre_hoja"],
        "mn": validacion_mn,
        "me": validacion_me,
    }


# ============================================================
# 4. MOSTRAR VALIDACIÓN
# ============================================================

def mostrar_validacion(
    resultado
):

    print()
    print("=" * 100)

    print(
        "ARCHIVO:",
        resultado["archivo"]
    )

    print("=" * 100)

    print(
        "Hoja MN:",
        repr(
            resultado["hoja_mn"]
        )
    )

    print(
        "Hoja ME:",
        repr(
            resultado["hoja_me"]
        )
    )

    for clave in (
        "mn",
        "me"
    ):

        item = resultado[
            clave
        ]

        print()
        print(
            "MONEDA:",
            item["moneda"]
        )

        print("-" * 100)

        print(
            "Estado:",
            item["estado"]
        )

        print(
            "Bancos individuales:",
            item["cantidad_bancos"]
        )

        print(
            "Agregados encontrados:",
            item["cantidad_agregados"]
        )

        print(
            "Suma bancos:",
            item["suma_bancos"]
        )

        print(
            "TOTAL BANCA MÚLTIPLE SBS:",
            item["total_sbs"]
        )

        print(
            "Diferencia:",
            item["diferencia"]
        )

        print(
            "Diferencia absoluta:",
            item["diferencia_absoluta"]
        )

        print(
            "Diferencia porcentual:",
            item["diferencia_pct"]
        )


# ============================================================
# 5. FUNCIÓN PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 100)

    print(
        "VALIDACIÓN DE TOTALES DE DEPÓSITOS"
    )

    print(
        "SBS B-2318 | SEIS ARCHIVOS PILOTO"
    )

    print("=" * 100)

    print()
    print(
        "Esta prueba utiliza únicamente "
        "los archivos piloto locales."
    )

    print(
        "NO descarga información."
    )

    print(
        "NO modifica archivos crudos."
    )

    resultados = []

    for nombre in ARCHIVOS_CONTROL:

        ruta = (
            CARPETA_PILOTO
            / nombre
        )

        if not ruta.exists():

            print()
            print(
                "[ERROR] No existe:",
                ruta
            )

            continue

        resultado = analizar_archivo(
            ruta
        )

        if resultado is None:
            continue

        resultados.append(
            resultado
        )

        mostrar_validacion(
            resultado
        )

    # ========================================================
    # RESUMEN COMPARATIVO
    # ========================================================

    print()
    print("=" * 100)

    print(
        "RESUMEN COMPARATIVO"
    )

    print("=" * 100)

    for resultado in resultados:

        mn = resultado[
            "mn"
        ]

        me = resultado[
            "me"
        ]

        print()
        print(
            resultado["archivo"]
        )

        print(
            "  MN | bancos:",
            mn["cantidad_bancos"],
            "| suma:",
            mn["suma_bancos"],
            "| SBS:",
            mn["total_sbs"],
            "| diferencia:",
            mn["diferencia"],
            "| diferencia %:",
            mn["diferencia_pct"]
        )

        print(
            "  ME | bancos:",
            me["cantidad_bancos"],
            "| suma:",
            me["suma_bancos"],
            "| SBS:",
            me["total_sbs"],
            "| diferencia:",
            me["diferencia"],
            "| diferencia %:",
            me["diferencia_pct"]
        )

    # ========================================================
    # CONTROL FINAL
    # ========================================================

    print()
    print("=" * 100)

    print(
        "CONTROL FINAL"
    )

    print("=" * 100)

    errores_agregado = []

    for resultado in resultados:

        for moneda in (
            "mn",
            "me"
        ):

            item = resultado[
                moneda
            ]

            if item[
                "estado"
            ] != "OK":

                errores_agregado.append(
                    (
                        resultado["archivo"],
                        item["moneda"]
                    )
                )

    if not errores_agregado:

        print()
        print(
            "[OK] Todos los archivos contienen "
            "exactamente un TOTAL BANCA MÚLTIPLE "
            "en MN y ME."
        )

    else:

        print()
        print(
            "[ADVERTENCIA] Revisar agregados:"
        )

        for error in errores_agregado:

            print(
                " ",
                error
            )

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "La magnitud de las diferencias debe "
        "evaluarse antes de declarar validado DOLDEP."
    )

    print(
        "El script NO decide automáticamente "
        "que una diferencia es redondeo."
    )


# ============================================================
# 6. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    main()