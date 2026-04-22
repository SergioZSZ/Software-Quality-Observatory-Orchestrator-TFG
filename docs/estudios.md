# Estudio sobre el paralelismo de workers

## Objetivo

Este documento resume los resultados obtenidos en los tres casos de estudio analizados para evaluar el impacto del paralelismo en los workers de SOCA y RSFC:

- `SergioZSZ` (3 repositorios)
- `FAIR2ADAPT` (31 repositorios)
- `oeg-upm` (381 repositorios)

En todos los casos, los tiempos reflejan solo el tiempo de ejecución de los workers de `SOCA` y `RSFC`, sin contar tiempos intermedios del workflow. `RsMetaCheck` se ha ejecutado de forma secuencial y su coste temporal es reducido frente al resto del pipeline

## Resultados finales

### SergioZSZ

| Nº de workers | Tiempo SOCA | Tiempo RSFC | Tiempo total |
| ------------- | ----------- | ----------- | ------------ |
| 1             | 01m 29s     | 00m 49s     | 02m 18s      |
| 2             | 01m 20s     | 00m 23s     | 01m 43s      |
| 4             | 01m 02s     | 00m 21s     | 01m 23s      |
| 6 y 4         | 01m 53s     | 00m 21s     | 02m 14s      |

### FAIR2ADAPT

| Nº de workers | Tiempo SOCA | Tiempo RSFC | Tiempo total |
| ------------- | ----------- | ----------- | ------------ |
| 1             | 05m 32s     | 04m 45s     | 10m 17s      |
| 2             | 03m 02s     | 03m 04s     | 06m 06s      |
| 4             | 01m 49s     | 03m 05s     | 04m 54s      |
| 6 y 4         | 01m 46s     | 03m 09s     | 04m 55s      |

### oeg-upm

| Nº de workers | Tiempo SOCA | Tiempo RSFC | Tiempo total |
| ------------- | ----------- | ----------- | ------------ |
| 1             |             |             |              |
| 2             | 1h 20m 27s  | 44m 57s     | 2h 05m 24s   |
| 4             | 50m 48s     | 38m 16s     | 1h 29m 04s   |
| 6 y 4         | 42m 50s     | 38m 14s     | 1h 21m 04s   |

## Conclusiones por herramienta

### SOCA

- El paralelismo en `SOCA` aporta una mejora clara al pasar de `1` a `2` workers y de `2` a `4` workers
- En casos pequeños, como `SergioZSZ`, aumentar hasta `6` workers no solo deja de mejorar, sino que empeora el tiempo total
- En `FAIR2ADAPT`, pasar de `4` a `6` workers apenas reduce el tiempo de `SOCA` (`01m 49s` frente a `01m 46s`), por lo que la mejora marginal es casi nula
- En `oeg-upm`, que es un caso mucho mas grande, `SOCA` sigue mejorando al subir de `4` a `6` workers, aunque la mejora ya es menor que en saltos anteriores

### RSFC

- `RSFC` mejora de forma clara entre `1` y `2` workers en los casos pequeños y medianos
- Sin embargo, a partir de `4` workers el comportamiento se estabiliza mucho mas que `SOCA`
- En `FAIR2ADAPT`, `RSFC` permanece prácticamente igual entre los escenarios `4` y `6 y 4`
- En `oeg-upm`, `RSFC` mejora ligeramente entre `2` y `4` workers, pero apenas cambia entre `4` y `6 y 4`, lo que sugiere que en este entorno el cuello de botella ya no depende tanto del numero de workers

### RsMetaCheck

- `RsMetaCheck` tiene un coste temporal muy bajo en los tres casos de estudio
- Su contribución al tiempo total del pipeline es pequena frente a `SOCA` y `RSFC`
- Esto refuerza la idea de que no resulta prioritario paralelizar `RsMetaCheck` en el estado actual del orquestador

## Conclusiones globales

- El paralelismo es util en el orquestador, pero no escala de forma lineal.
- El mayor beneficio se obtiene al pasar de `1` a `2` workers y, en muchos casos, hasta `4` workers
- A partir de cierto punto, el aumento de workers provoca rendimientos decrecientes debido al consumo de recursos
- En los casos pequenos y medianos (`SergioZSZ` y `FAIR2ADAPT`), el punto más equilibrado se encuentra alrededor de `4 workers` para `SOCA` y `4 workers` para `RSFC`
- En el caso grande (`oeg-upm`), el escenario `6 workers SOCA + 4 workers RSFC` es el mejor de los medidos, pero la mejora respecto a `4 workers` ya es bastante menor que en los saltos anteriores

## Interpretacion final

Tomando en conjunto los tres casos de estudio, puede concluirse que:

- `4 workers` constituye un punto de equilibrio muy razonable para el sistema en este equipo
- `6 workers` en `SOCA` solo parece compensar en organizaciones o usuarios con muchos repositorios
- `RSFC` alcanza antes su zona de saturación, por lo que aumentar workers por encima de `4` no parece una prioridad clara con los datos actuales
- La configuración `4 workers SOCA + 4 workers RSFC` puede considerarse una configuracion base equilibrada
- La configuración `6 workers SOCA + 4 workers RSFC` puede reservarse para organizaciones grandes, donde el tamano del lote se aprovecha mejor con dicha configuración
