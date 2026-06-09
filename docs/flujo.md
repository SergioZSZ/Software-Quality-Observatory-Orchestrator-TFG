### 4. Flujo actual(container n8n)
El sistema utiliza **n8n** como motor de orquestación para coordinar la ejecución completa del pipeline de análisis. 

Actualmente el despliegue se apoya en el workflow modular:

- `SQOO_modular_workflow.json`: workflow principal modular de SQOO. Orquesta los subworkflows `soca_workflow.json`, `rsfc_workflow.json`, `sw-metadata-bot_workfow.json` y `dashverse_workflow.json`.
- `resqui_workflow.json`: subworkflow de RESQUI preparado para ejecutar la evaluacion con workers `worker_resqui`.

La versión modular facilita aislar y mantener cada fase sin cambiar el contrato global del pipeline. El workflow principal pasa entre fases los campos `target`, `type`, `mode`, `repos`, `repos_url`, `repo_count` y `launch_issue` según corresponda.

**Nota:** `resqui_workflow.json` aun no esta integrado en `SQOO_modular_workflow.json`; se mantiene como subworkflow independiente y su integracion en el flujo principal se realizara proximamente.



#### Descripción general del flujo

Los workflows implementan un pipeline completo que abarca:

1. **Extracción de repositorios**
2. **Procesamiento de metadatos (SOCA)**
3. **Evaluación de calidad (RSFC)**
4. **Evaluación de metadatos (sw-metadata-bot)**
5. **Generación y publicacion de portal software enriquecido**
6. **Envío de indicadores a DashVERSE**



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


##### 3. Evaluación RSFC
- Envío de repositorios a los workers RSFC, evaluando la calidad de software
- Control de finalización: se espera a que los jsons generados sean iguales a la cantidad de repositorios de `repos.txt`

##### Subworkflow RESQUI (pendiente de integracion)

- `resqui_workflow.json` publica los repositorios en la cola `resqui_jobs`.
- Los workers `worker_resqui` ejecutan RESQUI con la configuracion incluida en `containers/resqui_container/resqui_runner/configurations/`.
- Los resultados se escriben en `outputs/resqui/<target>/`.
- Este subworkflow aun no forma parte del workflow principal modular; se integrara proximamente.

##### 4. Análisis de metadatos con sw-metadata-bot

n8n ejecuta `sw-metadata-bot` para analizar la calidad de los metadatos de los repositorios y, si se habilita, generar issues automáticos cuando se detectan carencias. Todo siguiendo este proceso:

- Generado un `config.json` con los repositorios obtenidos en el workflow

- Ejecutado el análisis mediante `sw-metadata-bot run-analysis`
- Reutilizado ejecuciones anteriores mediante `previous_report` cuando aplica
- Comprobado que existe `run_report.json` para la ejecución generada
- Publicados los issues generados mediante `sw-metadata-bot publish` solo cuando `launch_issue` está activado

En `SQOO_modular_workflow.json` esta decisión se define en el nodo `Conf` y se propaga al subworkflow `sw-metadata-bot_workfow`.

##### 5. Generación y publicacion del portal

- Se ejecuta `genportal.py` cuando ya existen los reportes de RSFC y sw-metadata-bot.
- El portal incorpora metadatos SOCA, indicadores RSFC e informes/issues de sw-metadata-bot.
- El portal queda persistido en `outputs/soca/<target>/portal/`.
- El servicio `nginx` publica ese directorio en `http://localhost:8030/portals/<target>/`.
- Las paginas embebidas cargan los dashboards de DashVERSE/Superset mediante iframe directo usando `SUPERSET_PUBLIC_DOMAIN`.

Salida generada:

- Portal HTML/JSON enriquecido con reportes y metadatos
- Dashboards embebidos publicados junto al catálogo

##### 6. Envío de assessments a DashVERSE

- Lectura de los archivos generados: `rsfc_assessment.json` por cada repositorio
- Extracción y transformación de los datos del assessment añadiendo un @id y el `author` como keys del json-ld

- Iteración sobre cada repositorio y sus checks mediante nodos `Split Out`
- Envío de datos mediante peticiones HTTP POST a la API de DashVERSE `/assessment_raw`
