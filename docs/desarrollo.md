
## 3. Desarrollo
### 3.1 Dockerización de SOCA

Se ha:

- Preparado entorno aislado con poetry
- Clonado y preparado SOCA
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en un contenedor Docker
- Configurado volúmenes para persistencia de resultados
- Orquestado mediante lanzamiento de jobs para la extracción de metadatos por workers en paralelo
- Configurado `genportal.py` para crear el portal final tras RSFC y sw-metadata-bot
Salida generada:

- Fetch de los repositorios y envío a n8n
- Repositorios descargados
- Metadatos estructurados
- Portal web del catálogo


### 3.2 worker_soca container
El contenedor worker se encarga de la extracción de metadatos de los repositorios obtenidos en el fetch; el portal se genera al final con los reportes.

Mientras que soca_container publica en una cola de trabajo en RabbitMQ con el usuario/organización del cual se van a extraer metadatos.

Cada worker ejecuta el módulo `python -u -m soca_runner.worker` que se dedica a:

1. Recibe un job de RabbitMQ (con el target)
2. Se extraen metadatos de los repos obtenidos en el fetch por workers paralelos o genera un fichero explicando el error en caso de que no se pudiese extraer

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_soca=N`` siendo N el número de workers que se levantarán.

### 3.3 Dockerización de RSFC

Se ha:

- Preparado entorno aislado con poetry
- Instalado RSFC en el entorno
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en contenedor independiente
- Orquestado mediante lanzamiento de jobs a RabbitMQ la extraccion de indicadores
- Implementado lanzamiento de workers para procesar los jobs usando la cola de trabajo de RabbitMQ

Salida generada:
- Generación de indicadores de calidad de cada repositorio en formato `json`

### 3.4 worker_rsfc container
El contenedor worker se encarga del procesamiento asíncrono de los jobs generados por rsfc_container.

Mientras que rsfc_container actúa como encargado de registrar los jobs en la cola de trabajo de RabbitMQ correspondiente, los workers se encargan de consumir dichos jobs y ejecutar el análisis con RSFC.

Cada worker ejecuta el módulo `python -u -m rsfc_runner.worker` que se encarga de recibir los jobs publicados en RabbitMQ que:

1. Recibe un job de RabbitMQ
2. Ejecuta la evaluación del repositorio mediante rsfc
3. Genera un `rsfc_assessment.json` con los indicadores de calidad  o `failed_assessment.json` explicando el error de procesamiento
4. Espera a tener token para procesar siguiente trabajo (github rate limit)
5. Responde a RabbitMQ habiendo procesado el job para recibir otro

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_rsfc=N`` siendo N el número de workers que se levantarán.


### 3.5 rate_limiter_rsfc container
El contenedor rate_limiter se encarga del envío de tokens a una cola de RabbitMQ de tamaño 1. Los workers RSFC se esperarán a obtener un token de la cola para procesar los jobs para no saturar de peticiones GitHubAPI y no sobrepasar el RateLimit.

### 3.6 Integracion de RESQUI

Se ha integrado RESQUI mediante el contenedor `resqui_container`, usando `QualityPipelines-2.0` como submodulo del repositorio. La imagen `resqui-heavy` instala RESQUI y el runner propio `resqui_runner`, que publica jobs en RabbitMQ y permite que varios workers procesen repositorios en paralelo.

Componentes principales:

- `worker_resqui`: consume mensajes de la cola `resqui_jobs` y ejecuta RESQUI para cada repositorio.
- `rate_limiter_resqui`: publica tokens en `github_rate_limit_resqui` para controlar las peticiones a GitHubAPI.
- `resqui_work`: volumen Docker nombrado como `sqoo_resqui_work`, compartido entre el worker y los contenedores Docker que RESQUI lanza para plugins como Gitleaks, Super-Linter o RSFC.

Salida generada:

- Reportes RESQUI por repositorio en `outputs/resqui/<target>/<repo>/`.
- Ficheros `failed_assessment.json` cuando un repositorio no puede procesarse correctamente.

Modificaciones realizadas sobre RESQUI/QualityPipelines:

- Soporte opcional de workspace compartido mediante `RESQUI_SHARED_WORKDIR` y `RESQUI_DOCKER_WORK_VOLUME`.
- Uso de `--rm` en contenedores de plugins para evitar acumulacion de contenedores Docker parados.
- Inicializacion de `success = False` en funciones de OpenSSF Scorecard para evitar variables sin definir.

### 3.7 DashVerse Service
El servicio DashVerse sirve para la creación y visualización de los dashboards creados a partir de los indicadores de calidad obtenidos de las organizaciones. Dentro del directorio `/integrations/dashboards` existen 2 plantillas con diversos dashboards, los cuales son:

#### SQOO-org:
1. KPIs generales:
   - Total de assessments procesados
   - Total de repositorios
   - Total de organizaciones visualizadas

2. Análisis de resultados:
    **NOTA** la importancia del indicador viene declarada en: https://everse.software/indicators/website/rs_tiers.htm (Relevant for Prototype Tool)

    - Comparación de assessments que pasan los indicadores `Crucial` comparados con los assessments totales
    - Comparación de assessments que pasan los indicadores `Recommended` comparados con los assessments totales
    - Comparación de assessments que pasan los indicadores `Good to have` comparados con los assessments totales



#### SQOO-repo:
1. Relacionado a procesos:
    - Comparativa pocesos pasados de los assessments / procesos totales de los assessments para indicadores Crucial, Recommended y Good to have a nivel total de procesos por tier
    - Comparativa pocesos pasados de los assessments / procesos totales de los assessments para indicadores Crucial, Recommended y Good to have a nivel de indicador 
    - Tabla con metadatos de los assessments procesados
    - Tabla con los procesos fallidos del assessment + sugerencias

Con las plantillas dadas en `/integrations/dashboards` hay opciones cross-filtering, útiles por ejemplo para a seleccionar el nombre/id de un repositorio en el dashboard de metadatos, y que aparezcan en el dashboar de procesos de RSFC fallidos únicamente los procesos fallidos por ese repositorio.



### 3.8 Integración de sw-metadata-bot

Se ha:

- Integrado `sw-metadata-bot` como herramienta encargada de analizar la calidad de los metadatos de los repositorios procesados
- Preparado el uso del bot mediante una imagen Docker `sw-metadata-bot:latest`
- Adaptado su ejecución vía `execute-command` de n8n
- Configurado el montaje del volumen compartido de `outputs` para persistir los resultados del análisis
- Generado dinámicamente un archivo `config.json` con la lista de repositorios obtenidos durante el workflow
- Configurado el uso de `GITHUB_API_TOKEN` para permitir la consulta de repositorios y la publicación de issues
- Incorporado el análisis incremental mediante `previous_report`, permitiendo reutilizar ejecuciones anteriores cuando se indique
- Añadida la fase opcional de publicación de issues tras la generación de los informes de metadatos, controlada desde `launch_issue` en los workflows de n8n

El servicio `sw-metadata-bot` se ejecuta dentro del flujo de n8n después de obtener la lista de repositorios que forman parte del análisis. Para cada ejecución se crea un directorio específico dentro de:

- `/outputs/sw-metadata-bot/<target>/`

