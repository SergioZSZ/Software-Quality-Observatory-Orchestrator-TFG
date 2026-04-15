### 3.7 Flujo actual(container n8n)
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

##### 5. Envío de assessments a DashVERSE

- Lectura de los archivos generados: `rsfc_assessment.json` por cada repositorio
- Extracción y transformación de los datos del assessment
- Separación en tres entidades:
   - `assessments`: información general del assessment (contexto, tipo, nombre, descripción, fecha de creación del assessment, licencia)
   - `assessment_software`: información del software evaluado (nombre, versión, URL)
   - `assessment_checks`: checks individuales del assessment (indicadores, evidencias, resultados)
- Iteración sobre cada repositorio y sus checks mediante nodos `Split Out`
- Envío de datos mediante peticiones HTTP POST a la API de DashVERSE:
   - `/assessments`
   - `/assessment_software`
   - `/assessment_checks`
- Uso de la cabecera `Prefer: resolution=merge-duplicates` para evitar duplicados en la base de datos
- Persistencia final de los resultados en DashVERSE para su posterior visualización en dashboards





---