
### 4. Flujo actual(container n8n)
El sistema utiliza **n8n** como motor de orquestación para coordinar la ejecución completa del pipeline de análisis. 

A diferencia de versiones anteriores, donde el flujo estaba dividido en múltiples workflows (`soca`, `rsfc`, `dashboard`), actualmente se ha **unificado en un único workflow end-to-end**, simplificando la gestión, monitorización y control del proceso.

---

#### Descripción general del flujo

El workflow implementa un pipeline completo que abarca:

1. **Extracción de repositorios**
2. **Procesamiento de metadatos (SOCA)**
3. **Generación de portal/**
4. **Evaluación de calidad (RSFC)**
4. **Envío de indicadores a DashVERSE**

---

####  Etapas del workflow

##### 1. Inicialización 

- Trigger manual (`Execute Workflow`)
- Definición del objetivo (`target`) y tipo (`user` / `org`)
- Ejecución del contenedor: ```soca-heavy:latest ```
- Ejecución del pipeline SOCA por los workers
- Generación de metadatos por repositorio

##### 2. Lectura y procesamiento de repositorios

- Lectura del archivo generado: `repos.txt`
- Transformación a lista de URLs
- Cálculo del número total de repositorios (repo_count)
- Control de finalización procesamiento de repositorios: se espera a que los jsons generados sean iguales a la cantidad de repositorios de `repos.txt`


##### 3. Generación del portal
- Generación del portal software mediante nodo Execute-command lanzando un contenedor docker ejecutando el script `genportal.py`, generándose el portal software.

##### 4. Evaluación RSFC
- Envío de repositorios a los workers RSFC, evaluando la calidad de software
- Control de finalización: se espera a que los jsons generados sean iguales a la cantidad de repositorios de `repos.txt`

##### 5. Análisis de metadatos con sw-metadata-bot

n8n ejecuta `sw-metadata-bot` para analizar la calidad de los metadatos de los repositorios y generar issues automáticos cuando se detectan carencias.

Se ha:

- Generado un `config.json` con los repositorios obtenidos en el workflow
- Configurado el directorio de salida en `/outputs/sw-metadata-bot/<target>/`
- Ejecutado el análisis mediante `sw-metadata-bot run-analysis`
- Reutilizado ejecuciones anteriores mediante `previous_report` cuando aplica
- Publicado los issues generados mediante `sw-metadata-bot publish`

Salida generada:

- Informes de análisis por repositorio
- `run_report.json` con el resumen de la ejecución
- `issue_report.md` con el contenido del issue propuesto
- Issues en GitHub con recomendaciones para mejorar los metadatos

##### 6. Envío de assessments a DashVERSE

- Lectura de los archivos generados: `rsfc_assessment.json` por cada repositorio
- Extracción y transformación de los datos del assessment añadiendo un @id y el `author` como keys del json-ld

- Iteración sobre cada repositorio y sus checks mediante nodos `Split Out`
- Envío de datos mediante peticiones HTTP POST a la API de DashVERSE `/assessments_raw`