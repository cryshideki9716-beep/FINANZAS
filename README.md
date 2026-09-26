# FINANZAS I – Unidad I

## Dolarización del crédito y de los depósitos en el sistema financiero peruano

**Universidad Nacional del Centro del Perú**  
**Facultad de Economía – Escuela Profesional de Economía**  
**Curso:** Finanzas I (055D)  
**Unidad:** I  
**Tema N.º 4**

### Estudiante

**BRICEÑO LEON CRYSTELL HIDEKI**  
**Código de matrícula:** 2024200485D

---

## 1. Descripción del proyecto

Este repositorio contiene la base de datos, los scripts de extracción, limpieza y análisis, así como las tablas y figuras correspondientes a la evaluación procedimental de la Unidad I de Finanzas I.

El objetivo empírico es analizar la relación entre la dolarización del crédito y:

- la dolarización de los depósitos;
- la tasa activa de consumo en moneda nacional;
- la tasa pasiva de ahorro en moneda nacional;
- la inflación mensual.

El análisis se realiza mediante datos mensuales por banco.

Los resultados se interpretan como **asociaciones estadísticas** y no como relaciones causales.

---

## 2. Periodo, fecha de corte y muestra econométrica

### Ventanas de extracción

- **Ventana de extracción de X4 – BCRP:** 2008-06 a 2025-12.
- **Ventana SBS utilizada para Y, X1, X2 y X3:** 2015-11 a 2025-12.
- **Fecha de corte:** 2025-12.
- **Fecha de extracción final registrada:** 24 de septiembre de 2026.

### Muestra econométrica

La muestra econométrica final presenta las siguientes características:

- **Periodo:** noviembre de 2015 a diciembre de 2025.
- **Frecuencia:** mensual.
- **Meses calendario:** 122.
- **Bancos:** 12.
- **Observaciones efectivas:** 1,458.
- **Duplicados en `mes + banco_id`:** 0.
- **Valores faltantes en la muestra econométrica:** 0.
- **Interpolación:** no utilizada.
- **Imputación:** no utilizada.
- **Extrapolación:** no utilizada.

El archivo oficial utilizado por el análisis es:

```text
datos_procesados/datos_procesados_2024200485D.csv
```

---

## 3. Variables

| Variable | Descripción | Unidad | Nivel |
|---|---|---|---|
| `Y` | Dolarización del crédito | Porcentaje (%) | Banco-mes |
| `X1` | Dolarización de depósitos | Porcentaje (%) | Banco-mes |
| `X2` | Tasa activa de consumo en moneda nacional | Porcentaje (%) | Banco-mes |
| `X3` | Tasa pasiva de ahorro en moneda nacional | Porcentaje (%) | Banco-mes |
| `X4` | Inflación mensual | Variación porcentual mensual (%) | Mes |
| `mes` | Periodo de observación | AAAA-MM | Tiempo |
| `banco_id` | Identificador bancario homologado | Texto | Banco |

Las definiciones completas, unidades, frecuencia, nivel, fuente exacta y URL o endpoint de cada variable se encuentran en:

```text
diccionario_variables.md
```

---

## 4. Fuentes oficiales

Se utilizan dos instituciones oficiales: el Banco Central de Reserva del Perú y la Superintendencia de Banca, Seguros y AFP.

### 4.1 Banco Central de Reserva del Perú – BCRP

Variable obtenida:

- `X4`: inflación mensual.

Serie BCRPData:

```text
PN01271PM
```

Descripción de la serie:

```text
Índice de precios Lima Metropolitana
(variación porcentual mensual) - IPC
```

Endpoint utilizado por `01_extraccion_api.py`:

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/csv/{FECHA_INICIO}/{FECHA_CORTE}/esp
```

Para la extracción de X4:

```text
FECHA_INICIO = 2008-06
FECHA_CORTE = 2025-12
```

La ejecución oficial registró:

```text
Código HTTP: 200
Observaciones descargadas: 211
```

---

### 4.2 Superintendencia de Banca, Seguros y AFP – SBS

#### Y – Dolarización del crédito

Reporte:

```text
B-2359
Créditos Directos por Tipo, Modalidad y Moneda
```

Fuente:

```text
https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=B-2359
```

---

#### X1 – Dolarización de depósitos

Reporte:

```text
B-2318
Movimiento de los Depósitos
```

Fuente:

```text
https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=B-2318
```

---

#### X2 – Tasa activa de consumo en moneda nacional

Reporte:

```text
Tasas de Interés por Tipo de Crédito y Empresa Bancaria
Concepto: Consumo
Moneda: Moneda Nacional
```

Fuente:

```text
https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIActivaTipoCreditoEmpresa.aspx?tip=B
```

---

#### X3 – Tasa pasiva de ahorro en moneda nacional

Reporte:

```text
Tasas de Interés Pasivas por Empresa Bancaria
Concepto: Depósitos de Ahorro
Moneda: Moneda Nacional
```

Fuente:

```text
https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIPasivaDepositoEmpresa.aspx?tip=B
```

---

## 5. Métodos de extracción

### BCRP

La inflación se obtiene mediante consumo programático de la API oficial de BCRPData desde:

```text
codigo/01_extraccion_api.py
```

El script declara la serie, el endpoint y el periodo de consulta, controla la respuesta HTTP y conserva el archivo crudo obtenido.

### SBS

La extracción SBS se controla mediante:

```text
codigo/02_scraping_web.py
```

Este archivo constituye el **orquestador oficial de la extracción SBS de la Unidad I**.

Ejecuta los motores de extracción ya validados:

```text
extraccion_produccion_Y_X1_2024200485D.py
extraccion_mensual_x2_consumo_mn.py
extraccion_mensual_x3_ahorro_mn.py
```

La extracción de Y y X1 utiliza descarga programática de los archivos oficiales publicados por la SBS.

La extracción de X2 y X3 utiliza Selenium con Chrome para consultar las tablas históricas de tasas por empresa bancaria.

Los archivos obtenidos directamente de las fuentes se conservan en:

```text
datos_crudos/
```

El periodo SBS utilizado para la producción final es:

```text
2015-11 a 2025-12
122 meses
```

El `02_scraping_web.py` oficial valida cobertura, número de filas, duplicados, auditorías, archivos crudos y hashes de las salidas.

Su estado final validado es:

```text
ESTADO = EXTRACCION_SBS_COMPLETA_VALIDADA
```

---

## 6. Limpieza e integración

El procesamiento se realiza mediante:

```text
codigo/03_limpieza_datos.py
```

Las principales tareas son:

- lectura de las variables extraídas;
- tipificación de columnas;
- homologación de nombres bancarios;
- control de duplicados;
- conservación y control de faltantes;
- integración de las fuentes mediante llaves comunes;
- construcción del panel;
- selección de la muestra econométrica final;
- generación del archivo procesado oficial.

Las variables bancarias se integran mediante:

```text
mes + banco_id
```

La inflación se incorpora mediante:

```text
mes
```

No se realizan interpolaciones, imputaciones ni extrapolaciones.

El script genera como archivo oficial:

```text
datos_procesados/datos_procesados_2024200485D.csv
```

Su estado final validado es:

```text
ESTADO = LIMPIEZA_DATOS_COMPLETA_VALIDADA
```

---

## 7. Análisis estadístico y econométrico

El análisis se realiza mediante:

```text
codigo/04_analisis.py
```

El script utiliza como entrada oficial:

```text
datos_procesados/datos_procesados_2024200485D.csv
```

### Análisis descriptivo

Se generan:

- estructura de la muestra;
- estadísticos descriptivos;
- descriptivos por banco;
- matriz de correlaciones de Pearson;
- cuatro figuras.

La matriz de Pearson se utiliza únicamente de forma descriptiva.

### Modelo OLS de referencia

Se estima el siguiente modelo agrupado:

\[
Y_{it}
=
\beta_0
+
\beta_1 X1_{it}
+
\beta_2 X2_{it}
+
\beta_3 X3_{it}
+
\beta_4 X4_t
+
\varepsilon_{it}
\]

Se utilizan errores estándar:

```text
HC3
```

con:

```text
use_t=True
```

El OLS agrupado se presenta únicamente como modelo de referencia.

### Modelo principal

La especificación principal utiliza efectos fijos por banco:

\[
Y_{it}
=
\alpha_i
+
\beta_1 X1_{it}
+
\beta_2 X2_{it}
+
\beta_3 X3_{it}
+
\beta_4 X4_t
+
\varepsilon_{it}
\]

Configuración:

```text
Efectos fijos por banco: Sí
Efectos fijos completos por mes: No
Covarianza: Driscoll-Kraay
Kernel: Bartlett
Bandwidth: 4
```

No se incorporan efectos fijos completos por mes porque X4 es una variable común a todos los bancos dentro de cada periodo y quedaría absorbida por los efectos temporales completos.

La especificación Driscoll–Kraay fue definida previamente como la inferencia principal.

### Diagnósticos

El script reporta:

- VIF;
- Breusch–Pagan / Koenker;
- Wooldridge–Drukker para autocorrelación en panel;
- Pesaran CD para dependencia transversal;
- prueba F de poolability de los efectos bancarios.

Los diagnósticos documentan las características estadísticas del panel.

Los coeficientes se interpretan como **asociaciones** y no como efectos causales.

El estado final del script es:

```text
ESTADO = ANALISIS_COMPLETO_VALIDADO
```

---

## 8. Principales resultados del modelo de efectos fijos

El modelo principal de efectos fijos por banco con errores estándar Driscoll–Kraay produjo:

| Variable | Coeficiente | p-valor |
|---|---:|---:|
| `X1` | 0.31706120 | < 0.001 |
| `X2` | -0.02267341 | 0.00350735 |
| `X3` | -0.14685151 | 0.55196999 |
| `X4` | -0.88850944 | 0.00082374 |

Estadísticas generales:

```text
R² within = 0.31634906
N = 1458
Bancos = 12
```

Los resultados representan asociaciones condicionales dentro del panel y no efectos causales.

---

## 9. Orden de ejecución

Los scripts oficiales se ejecutan desde la carpeta raíz del proyecto en el siguiente orden:

```powershell
python codigo\01_extraccion_api.py
python codigo\02_scraping_web.py
python codigo\03_limpieza_datos.py
python codigo\04_analisis.py
```

El flujo general es:

```text
01_extraccion_api.py
        ↓
Extracción BCRP
        ↓
02_scraping_web.py
        ↓
Extracción SBS
        ↓
03_limpieza_datos.py
        ↓
datos_procesados_2024200485D.csv
        ↓
04_analisis.py
        ↓
tablas + figuras + resultados
```

---

## 10. Estado de validación

Las principales etapas finalizaron correctamente:

```text
02 SBS:
ESTADO = EXTRACCION_SBS_COMPLETA_VALIDADA

03 limpieza:
ESTADO = LIMPIEZA_DATOS_COMPLETA_VALIDADA

04 análisis:
ESTADO = ANALISIS_COMPLETO_VALIDADO
```

La ejecución cronológica completa queda registrada en:

```text
log_ejecucion.txt
```

El log contiene el flujo:

```text
01 API
→ 02 SBS
→ 03 limpieza
→ 04 análisis
```

---

## 11. Estructura principal del proyecto

```text
FINANZAS/
│
├── codigo/
│   ├── 01_extraccion_api.py
│   ├── 02_scraping_web.py
│   ├── 03_limpieza_datos.py
│   ├── 04_analisis.py
│   └── scripts auxiliares de extracción y diagnóstico
│
├── datos_crudos/
│   └── archivos originales obtenidos de BCRP y SBS
│
├── datos_procesados/
│   ├── datos_procesados_2024200485D.csv
│   ├── muestra_econometrica_12_bancos_2024200485D.csv
│   ├── panel_integrado_trazabilidad_2024200485D.csv
│   └── archivos intermedios de Y, X1, X2 y X3
│
├── salidas/
│   ├── tablas en CSV
│   ├── tablas en LaTeX
│   ├── figuras
│   ├── diagnosticos/
│   └── resumen_04_analisis.txt
│
├── diccionario_variables.md
├── requirements.txt
├── .env.example
├── log_ejecucion.txt
└── README.md
```

Los scripts auxiliares y de diagnóstico se conservan como evidencia del proceso de construcción, validación y depuración.

---

## 12. Salidas generadas

`04_analisis.py` genera automáticamente siete tablas en formato CSV y LaTeX:

```text
tabla_01_estructura_muestra
tabla_02_estadisticos_descriptivos
tabla_03_descriptivos_por_banco
tabla_04_correlaciones_pearson
tabla_05_ols_agrupado
tabla_06_efectos_fijos_banco
tabla_07_diagnosticos
```

También genera cuatro figuras:

```text
figura_01_dolarizacion_credito_depositos.png
figura_02_tasas_activa_pasiva.png
figura_03_inflacion_mensual.png
figura_04_dispersion_Y_X1.png
```

y el archivo:

```text
resumen_04_analisis.txt
```

Todos estos archivos se encuentran dentro de:

```text
salidas/
```

---

## 13. Entorno de ejecución

Versión de Python utilizada:

```text
Python 3.14.0
```

Principales librerías verificadas:

```text
requests==2.34.2
beautifulsoup4==4.15.0
xlrd==2.0.2
openpyxl==3.1.5
selenium==4.49.0
numpy==2.5.3
pandas==3.0.6
matplotlib==3.11.2
scipy==1.18.1
statsmodels==0.15.0
linearmodels==7.0
```

El entorno completo, incluidas sus dependencias, está congelado en:

```text
requirements.txt
```

El archivo se generó mediante:

```powershell
python -m pip freeze > requirements.txt
```

Para instalar el entorno registrado:

```powershell
python -m pip install -r requirements.txt
```

---

## 14. Variables de entorno

El archivo:

```text
.env.example
```

documenta las variables de entorno del proyecto.

Las fuentes públicas utilizadas en la Unidad I —SBS y BCRP— no requieren claves API privadas ni tokens personales para las extracciones implementadas.

---

## 15. Verificación SHA-256

Archivo procesado oficial:

```text
datos_procesados/datos_procesados_2024200485D.csv
```

SHA-256:

```text
342DE406A771419D1353FDBDEC456070611CDB22E38B041BD44EFCA2319E4BC4
```

Este hash corresponde al archivo procesado entregado.

Puede verificarse en PowerShell mediante:

```powershell
Get-FileHash .\datos_procesados\datos_procesados_2024200485D.csv -Algorithm SHA256
```

El hash obtenido debe coincidir exactamente con el valor anterior.

---

## 16. Reproducibilidad

La reproducibilidad del proyecto se sustenta en:

1. extracción programática desde fuentes oficiales;
2. conservación de los datos crudos;
3. parámetros de periodo declarados en los scripts;
4. controles de estructura y duplicados;
5. homologación bancaria documentada;
6. ausencia de interpolación, imputación y extrapolación;
7. archivo procesado con hash SHA-256;
8. versiones exactas del entorno registradas en `requirements.txt`;
9. registro cronológico de ejecución en `log_ejecucion.txt`;
10. generación automática de tablas y figuras desde la base procesada.

---

## 17. Repositorio GitHub

Repositorio del proyecto:

```text
https://github.com/cryshideki9716-beep/FINANZAS.git
```

El repositorio debe conservar el historial de versiones requerido para documentar el proceso de trabajo.

---

## 18. Archivos complementarios

Diccionario oficial de variables:

```text
diccionario_variables.md
```

Registro de ejecución:

```text
log_ejecucion.txt
```

Versiones exactas del entorno:

```text
requirements.txt
```

Plantilla de variables de entorno:

```text
.env.example
```

---

## 19. Nota metodológica

El objetivo de este trabajo es estudiar relaciones estadísticas entre la dolarización del crédito y las variables explicativas seleccionadas.

La estimación mediante efectos fijos controla la heterogeneidad no observada de cada banco que permanece constante en el tiempo.

Los errores estándar Driscoll–Kraay se utilizan en el modelo principal para realizar inferencia robusta frente a heterocedasticidad, autocorrelación temporal y dependencia transversal.

Los coeficientes obtenidos se describen como **asociaciones** y no deben interpretarse como efectos causales.

---

**Revisi�n final de reproducibilidad realizada el 26/09/2026.**
