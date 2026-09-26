# Diccionario de variables

## Identificación del proyecto

- **Estudiante:** BRICEÑO LEON CRYSTELL HIDEKI
- **Código de matrícula:** 2024200485D
- **Tema 4:** Dolarización del crédito y de los depósitos en el sistema financiero peruano
- **Periodo de la muestra econométrica:** 2015-11 a 2025-12
- **Frecuencia:** mensual
- **Unidad de observación principal:** banco-mes
- **Archivo procesado oficial:** `datos_procesados/datos_procesados_2024200485D.csv`

## Variables del archivo procesado

| Variable | Nombre | Definición | Unidad de medida | Frecuencia | Nivel | Fuente exacta | URL / endpoint de origen |
|---|---|---|---|---|---|---|---|
| `id_obs` | Identificador correlativo de observación | Número secuencial asignado a cada observación efectiva de la muestra econométrica final, desde 1 hasta 1458. Es auxiliar y no sustituye la llave `mes + banco_id`. | Entero | Mensual | Observación | Construida en `03_limpieza_datos.py` | No aplica |
| `mes` | Periodo mensual | Identifica el mes correspondiente a cada observación del panel, expresado en formato AAAA-MM. | AAAA-MM | Mensual | Tiempo | Construida a partir del periodo reportado por las fuentes SBS y BCRP | No aplica como serie independiente; corresponde al periodo reportado por las fuentes |
| `banco_id` | Identificador homologado del banco | Identificador normalizado utilizado para vincular una misma empresa bancaria cuando su denominación cambia entre fuentes o a través del tiempo. La homologación se realiza en `03_limpieza_datos.py`. | Texto | Mensual | Banco | Derivado de los nombres originales publicados por la SBS | Fuentes SBS señaladas para `Y`, `X1`, `X2` y `X3` |
| `Y` | Dolarización del crédito | Porcentaje de los créditos directos de una empresa bancaria denominados en moneda extranjera respecto del total de créditos directos. Se obtiene a partir de los montos en moneda nacional, moneda extranjera y total reportados por la SBS. | Porcentaje (%) | Mensual | Banco | SBS, reporte B-2359: **Créditos Directos por Tipo, Modalidad y Moneda** | https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=B-2359 |
| `X1` | Dolarización de depósitos | Porcentaje del saldo de depósitos en moneda extranjera respecto de la suma de los depósitos en moneda nacional y moneda extranjera de cada empresa bancaria. | Porcentaje (%) | Mensual | Banco | SBS, reporte B-2318: **Movimiento de los Depósitos** | https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=B-2318 |
| `X2` | Tasa activa de consumo en moneda nacional | Tasa de interés activa correspondiente al concepto **Consumo**, en moneda nacional, reportada por empresa bancaria. | Porcentaje (%) | Mensual | Banco | SBS, **Tasas de Interés por Tipo de Crédito y Empresa Bancaria**, concepto Consumo, Moneda Nacional | https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIActivaTipoCreditoEmpresa.aspx?tip=B |
| `X3` | Tasa pasiva de ahorro en moneda nacional | Tasa de interés pasiva correspondiente a **Depósitos de Ahorro**, en moneda nacional, reportada por empresa bancaria. | Porcentaje (%) | Mensual | Banco | SBS, **Tasas de Interés Pasivas por Empresa Bancaria**, Depósitos de Ahorro, Moneda Nacional | https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIPasivaDepositoEmpresa.aspx?tip=B |
| `X4` | Inflación mensual | Variación porcentual mensual del Índice de Precios al Consumidor de Lima Metropolitana. Es una variable común a todos los bancos dentro de un mismo mes. | Variación porcentual mensual (%) | Mensual | Sistema | Banco Central de Reserva del Perú, BCRPData, serie `PN01271PM`: **Índice de precios Lima Metropolitana (variación porcentual mensual) - IPC** | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/csv/{FECHA_INICIO}/{FECHA_CORTE}/esp` |

## Llaves de integración

Las variables bancarias `Y`, `X1`, `X2` y `X3` se integran mediante:

`mes + banco_id`

La variable macroeconómica `X4` se incorpora mediante:

`mes`

## Tratamiento de los datos

La base final no utiliza interpolación, imputación ni extrapolación.

Los valores ausentes provenientes de la fuente se conservan como faltantes durante la integración. Para construir la muestra econométrica final se excluyen las observaciones incompletas.

La muestra econométrica contiene:

- **12 bancos**
- **122 meses calendario**
- **1,458 observaciones efectivas**
- **Periodo:** 2015-11 a 2025-12
- **0 duplicados** en la llave `mes + banco_id`
- **0 valores faltantes** en `Y`, `X1`, `X2`, `X3` y `X4` dentro de la muestra econométrica final

## Fuente de cada variable sustantiva

- `Y`: Superintendencia de Banca, Seguros y AFP — SBS, reporte B-2359.
- `X1`: Superintendencia de Banca, Seguros y AFP — SBS, reporte B-2318.
- `X2`: Superintendencia de Banca, Seguros y AFP — SBS, Tasas de Interés por Tipo de Crédito y Empresa Bancaria, concepto Consumo, Moneda Nacional.
- `X3`: Superintendencia de Banca, Seguros y AFP — SBS, Tasas de Interés Pasivas por Empresa Bancaria, Depósitos de Ahorro, Moneda Nacional.
- `X4`: Banco Central de Reserva del Perú — BCRP, serie `PN01271PM`.

## Nota de interpretación

Las variables se utilizan para analizar asociaciones estadísticas entre la dolarización del crédito y las variables explicativas. El análisis no establece relaciones causales.