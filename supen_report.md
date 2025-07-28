# Análisis de operadoras de pensiones de Costa Rica

## Objetivo

La Superintendencia de Pensiones (SUPEN) de Costa Rica publica un conjunto de estadísticas públicas a través de una API oficial.  El objetivo de este análisis es comparar el desempeño de las diferentes **operadoras de pensiones complementarias (OPC)** en tres horizontes de tiempo —**corto**, **mediano** y **largo plazo**— con base en sus rendimientos nominales.  A partir de estos datos se pretende elaborar un **ranking** que oriente la elección de una operadora.

## Fuente de datos y método

* SUPEN publica sus estadísticas en el dominio `webapps.supen.fi.cr/Estadisticas/API`.  La API agrupa la información en categorías como activos, rendimientos, inversiones y afiliados.  Para este análisis se requieren únicamente los **rendimientos nominales**.
* Dado que la documentación oficial no fue accesible desde este entorno (problemas de certificados), el código proporcionado se basa en la estructura descrita en la *Guía para el uso de la API de estadísticas SUPEN*.  Será necesario ajustar las **rutas de los endpoints** y los **códigos de operadora** de acuerdo con la documentación oficial cuando ejecute el script localmente.
* Para cada operadora, el script realiza tres llamadas a la API (corto, mediano y largo plazo).  Entre cada llamada se espera **10 segundos** siguiendo la recomendación de SUPEN para evitar sobrecargar sus servidores.
* Con los datos de rendimientos se construye un `DataFrame` de **pandas** y se ordena a las operadoras en función del **rendimiento de largo plazo** (60 meses).  El usuario puede modificar esta métrica de ordenamiento si desea priorizar otro horizonte.

### Script `supen_analysis.py`

El repositorio incluye el fichero `supen_analysis.py`, que implementa las siguientes funciones principales:

| Funcíón | Descripción | Parámetros clave |
|---|---|---|
| **`fetch_returns_for_horizon(horizon)`** | Llama al endpoint de la API correspondiente al horizonte (`"short"`, `"medium"` o `"long"`) y devuelve un diccionario con los rendimientos por operadora. | Utiliza el diccionario `ENDPOINTS` para construir la URL y el nombre del campo con el rendimiento. |
| **`collect_returns()`** | Invoca `fetch_returns_for_horizon` para cada horizonte, respeta una pausa de 10 segundos entre llamadas y unifica los datos en una lista de instancias `ReturnData`. | – |
| **`create_ranking(returns)`** | Construye un `DataFrame` ordenado descendentemente por el rendimiento de largo plazo. | – |

El script se ejecuta desde línea de comandos.  Ejemplo de uso:

```bash
python supen_analysis.py --out resultados.csv
```

Este comando imprimirá el ranking por consola y guardará los resultados en `resultados.csv`.

## Operadoras consideradas

La siguiente tabla resume las operadoras de pensiones complementarias que se incluyen de forma predeterminada en el script.  Es posible que SUPEN añada o elimine entidades; por eso los **códigos** deberán revisarse en la documentación oficial.

| Operadora | Código (placeholder) | Observaciones |
|---|---|---|
| **BN Vital** | `BNV` | Brazo del Banco Nacional; históricamente presenta rendimientos competitivos. |
| **BCR Pensiones** | `BCR` | Afiliada al Banco de Costa Rica; suele situarse en los primeros lugares de rendimiento. |
| **Popular Pensiones** | `POP` | Vinculada al Banco Popular; gestiona uno de los portafolios más diversificados. |
| **BAC San José Pensiones** | `BAC` | Parte del Grupo BAC; mantiene comisiones moderadas. |
| **Vida Plena Pensiones** | `VID` | Anteriormente conocida como INS Pensiones; conviene revisar su trayectoria reciente. |
| **ACOFINSA** | `ACO` | Operadora más pequeña orientada al sector cooperativo; los retornos pueden variar. |

## Limitaciones

Debido a restricciones técnicas del entorno de este agente, no se pudieron realizar llamadas reales a la API de SUPEN.  Por esta razón **no se incluyen valores numéricos ni un ranking definitivo** en este informe.  Para obtener el ranking real deberá ejecutar el script `supen_analysis.py` desde su propio entorno con acceso a la API.  El procedimiento general es el siguiente:

1. Ajuste los endpoints y códigos de operadora en el diccionario `ENDPOINTS` y la variable `OPERATORS` según la documentación oficial de SUPEN.
2. Ejecute el script y verifique que las llamadas devuelvan la estructura JSON esperada.  En caso de que la respuesta esté anidada, modifique la función `fetch_returns_for_horizon` para extraer la lista de registros correctamente.
3. El script imprimirá el ranking ordenado por rendimiento de largo plazo.  Puede exportar los resultados a un fichero CSV para un análisis más profundo en Excel o cualquier otra herramienta.

## Recomendaciones generales para elegir operadora

Aunque el rendimiento nominal es un criterio central, la elección de una operadora de pensiones también debería considerar otros factores:

* **Comisiones de administración:** operadoras con comisiones más bajas pueden incrementar el rendimiento neto de sus afiliados.
* **Solidez financiera y respaldo institucional:** instituciones más grandes o respaldadas por bancos estatales tienden a ofrecer mayor estabilidad.
* **Calidad de servicio y herramientas digitales:** la disponibilidad de plataformas en línea, aplicación móvil y servicio al cliente puede influir en la satisfacción del afiliado.
* **Riesgo del portafolio:** verifique la composición de inversiones y la política de riesgos, especialmente si su horizonte para la jubilación es largo.

En términos generales se busca una operadora que combine **buenos rendimientos a largo plazo**, **comisiones razonables** y **servicio de calidad**.  Una vez obtenga los datos reales de SUPEN, el ranking cuantitativo le permitirá contrastar objetivamente el desempeño de cada operadora.
