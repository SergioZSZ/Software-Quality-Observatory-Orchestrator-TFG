[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18879858.svg)](https://doi.org/10.5281/zenodo.18879858)[![Project Status: Active ](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)[![GitHub release](https://img.shields.io/github/v/release/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG?include_prereleases)](https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/releases)![RSFC_Coverage](https://img.shields.io/badge/rsfc-coverage_83%25-green)


Documentación detallada en : https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/

# TFG – Orquestación automatizada de evaluación de software y generación de catálogo



## 1. Objetivo del proyecto

El objetivo del proyecto es diseñar e implementar un sistema reproducible que:

1. Extraiga automáticamente repositorios de GitHub
2. Genere metadatos estructurados del software
3. Evalúe la calidad del software mediante indicadores automáticos
4. Evalúe la calidad de los metadatos del software y, si se habilita, suba Issues automáticas a GitHub
5. Prepare la información para su integración en dashboards (DashVERSE) y catálogos (SOCA)
6. Permita orquestar todo el proceso mediante workflows automatizados

El sistema se basa en la integración y orquestación de herramientas existentes dentro de una arquitectura desacoplada y reproducible.

---



## 2. Arquitectura del sistema

| Componente       | Rol                                    |
| ---------------- | -------------------------------------- |
| n8n              | Orquestación del workflow modular y sus subworkflows |
| SOCA              | Descubrimiento incremental, metadatos y portal software |
| RSFC              | Evaluación de indicadores FAIR de software |
| RESQUI            | Evaluación configurable mediante QualityPipelines |
| RabbitMQ          | Distribución de trabajos entre workers |
| workers           | Procesamiento paralelo de SOCA, RSFC y RESQUI |
| rate limiters     | Control de peticiones a GitHub para RSFC y RESQUI |
| Nginx             | Publicación del portal SOCA |
| sw-metadata-bot   | Evaluación incremental de metadatos e issues opcionales |
| DashVERSE         | Persistencia y visualización de assessments |





Cada herramienta se ejecuta en su propio entorno aislado, garantizando:

- Reproducibilidad
- Portabilidad
- Independencia del sistema operativo
- Aislamiento de dependencias
- Escalabilidad

---


## 3. Desarrollo
### 3.1 Dockerización de SOCA

Se ha:

- Preparado entorno aislado con poetry
- Clonado y preparado SOCA
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en un contenedor Docker
- Configurado volúmenes para persistencia de resultados
- Orquestado mediante lanzamiento de jobs para la extracción de metadatos por workers en paralelo
- Añadido seguimiento de estado para procesar solo repositorios nuevos o modificados y retirar los eliminados
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

1. Recibe un repositorio actualizado desde RabbitMQ
2. Extrae los metadatos en un directorio temporal y promueve el resultado de forma atómica
3. Conserva el resultado anterior y registra el error si la nueva extracción falla

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_soca=N`` siendo N el número de workers que se levantarán.

### 3.3 Dockerización de RSFC

Se ha:

- Preparado entorno aislado con poetry
- Instalado RSFC en el entorno
- Actualizado a RSFC 0.1.7 y SOMEF 0.11.0
- Reutilizados los metadatos ya generados por SOCA cuando están disponibles
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
3. Genera un `rsfc_assessment.json` o un `failed_assessment.json` sin eliminar un resultado válido anterior
4. Espera a tener token para procesar siguiente trabajo (github rate limit)
5. Responde a RabbitMQ habiendo procesado el job para recibir otro

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_rsfc=N`` siendo N el número de workers que se levantarán.


### 3.5 rate_limiter_rsfc container
El contenedor rate_limiter se encarga del envío de tokens a una cola de RabbitMQ de tamaño 1. Los workers RSFC se esperarán a obtener un token de la cola para procesar los jobs para no saturar de peticiones GitHubAPI y no sobrepasar el RateLimit.

### 3.6 Integracion de RESQUI

Se ha integrado RESQUI en el workflow modular mediante el contenedor `resqui_container`. La imagen `resqui-heavy` instala el submódulo `QualityPipelines-2.0` y el runner que distribuye las evaluaciones entre workers.

Componentes principales:

- `worker_resqui`: consume mensajes de la cola `resqui_jobs` y ejecuta RESQUI para cada repositorio.
- `rate_limiter_resqui`: publica tokens en `github_rate_limit_resqui` para controlar las peticiones a GitHubAPI.
- `resqui_work`: volumen Docker nombrado como `sqoo_resqui_work`, compartido entre el worker y los contenedores Docker que RESQUI lanza para plugins como Gitleaks, Super-Linter o RSFC.

Salida generada:

- Reportes RESQUI por repositorio en `outputs/resqui/<project>/<owner>_<repo>/`.
- Ficheros `failed_assessment.json` cuando un repositorio no puede procesarse correctamente, conservando los resultados válidos anteriores.

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

Con las plantillas dada en `/integrations/dashboards` hay opciones cross-filtering, útiles por ejemplo para a seleccionar el nombre/id de un repositorio en el dashboard de metadatos, y que aparezcan en el dashboar de procesos de RSFC fallidos únicamente los procesos fallidos por ese repositorio.




### 3.8 Integración de sw-metadata-bot

Se ha:

- Integrado `sw-metadata-bot` como herramienta encargada de analizar la calidad de los metadatos de los repositorios procesados
- Preparado `sw-metadata-bot` 0.5.3 mediante las imágenes `sw-metadata-bot:latest` y `sw-metadata-bot-conf:latest`
- Adaptado su ejecución vía `execute-command` de n8n
- Configurado el montaje del volumen compartido de `outputs` para persistir los resultados del análisis
- Generado dinámicamente un archivo `config.json` con la lista de repositorios obtenidos durante el workflow
- Configurado el uso de `GITHUB_API_TOKEN` para permitir la consulta de repositorios y la publicación de issues
- Incorporado el análisis incremental: el bot localiza la snapshot anterior y reutiliza los artefactos de repositorios sin cambios
- Añadida la fase opcional de publicación de issues tras la generación de los informes de metadatos, controlada desde `launch_issue` en los workflows de n8n

El bot recibe el inventario completo para que cada snapshot conserve también los repositorios no modificados. Para cada ejecución se crea un directorio específico dentro de:

- `outputs/sw-metadata-bot/<project>/runs/<snapshot>/`

---


## 4. Workflow modular de n8n

`SQOO_modular_workflow.json` es el único workflow principal. Orquesta, en este orden, `soca_workflow.json`, `rsfc_workflow.json`, `resqui_workflow.json`, `sw-metadata-bot_workfow.json` y `dashverse_workflow.json`.

El nodo `Conf` define:

- `project`: nombre estable de la ejecución.
- `organizations`: organizaciones o usuarios de GitHub, indicando `org` y `type`.
- `extra_repositories`: repositorios adicionales.
- `launch_issue`: activa o desactiva la publicación de issues.

### Etapas

1. SOCA consulta GitHub y compara el inventario con `repository-state.json`. Genera `repos.txt`, `repos-updated.txt` y `repos-removed.txt`.
2. `If has changes` continúa el pipeline cuando hay repositorios actualizados o eliminados; si no hay cambios, consolida directamente el estado.
3. Solo los repositorios nuevos o modificados pasan por los workers de SOCA, RSFC y RESQUI. Los retirados se eliminan de sus salidas persistidas.
4. RSFC y RESQUI guardan resultados por `owner_repo` y notifican el estado del lote mediante `status.json`; los fallos por repositorio quedan registrados en `failed_repos` sin detener el pipeline.
5. sw-metadata-bot recibe el inventario completo, reutiliza la snapshot anterior para repositorios sin cambios y publica issues solo si `launch_issue` está activado.
6. SOCA genera el portal enriquecido, que Nginx publica en `http://localhost:8030/portals/<project>/`.
7. `If repo updated` llama a DashVERSE solo si existen assessments nuevos; una ejecución con solo eliminaciones pasa directamente a la consolidación.
8. El estado pendiente se consolida como `repository-state.json` únicamente cuando finaliza el pipeline.

---





## 5. Requisitos

### Orquestador

- Docker Engine o Docker Desktop con Compose v2.
- Python 3.11 o 3.12 para desarrollo local.
- Git con soporte de submódulos.
- Token de GitHub recomendado para evitar el rate limit y publicar issues.

En Windows, Docker Desktop debe tener activada la integración con WSL si se despliega DashVERSE.

### DashVERSE

DashVERSE 0.3.0 se despliega desde Linux sobre Kubernetes local con Minikube. Todos los comandos de `kubectl`, `minikube`, `tofu`, `ansible-playbook` y `just` deben ejecutarse desde el mismo entorno para compartir el contexto de Kubernetes.

Requisitos principales:

- Docker Engine con Compose v2.
- Git.
- Minikube.
- kubectl.
- Helm.
- OpenTofu (`tofu`).
- Ansible (`ansible-playbook`).
- Just.
- curl.
- jq.
- base64.
- zip y unzip.
- netcat (`nc`).

Instalación de utilidades habituales en Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  jq \
  unzip \
  zip \
  ansible \
  netcat-openbsd
```

Además, deben estar instalados Docker, Minikube, kubectl, Helm, OpenTofu y Just.

Comprobación desde la raíz de DashVERSE:

```bash
cd integrations/DashVERSE-0.3.0
just check-deps
```



         

#### Herramientas usadas en el proyecto:
- SOCA 0.0.4:
https://github.com/oeg-upm/soca/releases

- RSFC 0.1.7:
https://github.com/oeg-upm/rsfc/releases/tag/v0.1.7

- SOMEF 0.11.1:
https://github.com/KnowledgeCaptureAndDiscovery/somef/releases/tag/0.11.1

- DASHVERSE 0.3.0: 
https://github.com/EVERSE-ResearchSoftware/DashVERSE/releases/tag/v0.3.0

- sw-metadata-bot 0.5.3:
https://github.com/SoftwareUnderstanding/sw-metadata-bot/releases/tag/v0.5.3

- RsMetaCheck >=0.3.3:
https://github.com/SoftwareUnderstanding/RsMetaCheck/releases
      
      
---


## 6. Instalación/Despliegue

#### 6.1 Previa
 Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_API_TOKEN`: token personal de GitHub; para publicar issues debe permitir acceso a repositorios públicos

   - `RABBITMQ_USER` usuario de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`

   - `RATE_LIMIT_RSFC_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI
   - `RATE_LIMIT_RESQUI_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers RESQUI para peticiones a GitHubAPI

   - `OUTPUTS` la ruta de acceso al directorio a usar como volumen compartido (se debe llamar ``outputs`` y estar dentro del directorio `/containers`)
   - `PORTAL_PORT` puerto del host desde el que Nginx publica los portales SOCA (por defecto `8030`)

   - `DASHBOARD_ORG_EMBED_ID` id o slug del dashboard global importado en DashVERSE/Superset (por defecto `global`)
   - `DASHBOARD_REPO_EMBED_ID` id o slug del dashboard SQO-repo importado en DashVERSE/Superset (por defecto `assessments`)
      ambos valores corresponden a dashboards por defecto de dashverse

   - `DASHVERSE_JWT` token generado por la API de DashVERSE para publicar assessments desde n8n

   - `SUPERSET_PUBLIC_DOMAIN` dominio público usado por el navegador para cargar los dashboards. En local se utiliza `http://localhost:8088`.

      El archivo `/containers/.env.example` contiene todos los nombres necesarios; hay que sustituir los tokens, rutas e identificadores de dashboard.


**A tener en cuenta**:  
-  El token (classic) se debe obtener desde GitHub y seleccionando el scope 'public_repo'. si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error) y no se podrán subir las Issues automáticamente.

-  El nº o slug de dashboard es el que aparezca tras importar en DashVERSE la plantilla contenida en `/integrations/dashboard`. Los dashboards deben estar publicados y permitir embebido desde el portal.


#### 6.2 Instalación/Despliegue del orquestador
Siguiendo los pasos en orden secuencial:

Las imágenes pueden construirse con `scripts/build-docker-images.sh` en WSL/Linux o `scripts/build-docker-images.ps1` en PowerShell. Los mandatos equivalentes son:

0. Importar los submodulos del repositorio:
   - SQOO usa `containers/resqui_container/QualityPipelines-2.0` como submodulo para incluir el codigo fuente de RESQUI/QualityPipelines.
   - Si se clona el repositorio desde cero, usar:
      - Mandato: `git clone --recurse-submodules https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG.git`
   - Si el repositorio ya estaba clonado o se acaba de hacer `git pull`, ejecutar desde la raiz de SQOO:
      - Mandato: `git submodule update --init --recursive`
   - Para comprobar que el submodulo esta descargado:
      - Mandato: `git submodule status`

1. Generar imágenes  docker:
   - `soca-heavy`:
      - Directorio desde el que crearla: `/containers/soca_container` 
      - Mandato: `docker build -t soca-heavy .`
   - `rsfc-heavy`:
      - Directorio desde el que crearla: `/containers/rsfc_container` 
      - Mandato: `docker build -t rsfc-heavy .`
   - `sw-metadata-bot`:
      - Directorio desde el que crearla: `/integrations/sw-metadata-bot-0.5.3`
      - Mandato: `docker build -t sw-metadata-bot .`
   - `sw-metadata-bot-conf`:
      - Directorio desde el que crearla: `/containers/sw-metadata-bot_container` 
      - Mandato: `docker build -t sw-metadata-bot-conf .`
   - `resqui-heavy`:
      - Directorio desde el que crearla: `/containers/resqui_container`
      - Mandato: `docker build -t resqui-heavy .`

2. Desde el directorio `/containers` ejecutar el mandato en la terminal `docker compose up -d --scale worker_rsfc=N --scale worker_soca=N --scale worker_resqui=N`, siendo N el nº de workers a lanzar (si es la primera vez desplegándolo usar la etiqueta `--build` )

   El servicio RESQUI usa el volumen Docker nombrado `sqoo_resqui_work` montado como `/resqui-work`. Este volumen permite que el worker `resqui-heavy` y los contenedores Docker lanzados por los plugins de RESQUI compartan el mismo workspace de trabajo. No debe sustituirse por un bind mount local si se quiere ejecutar RESQUI dentro de Docker con plugins.

3. Acceder a n8n mediante el navegador en http://localhost:5678
4. En el primer acceso:
    1. Crear cuenta de usuario en n8n
    2. Importar los workflows desde `/containers/n8n_container/workflows/`
5. Importar y usar el workflow modular:
   - Importar `SQOO_modular_workflow.json` y los subworkflows `soca_workflow.json`, `rsfc_workflow.json`, `resqui_workflow.json`, `sw-metadata-bot_workfow.json` y `dashverse_workflow.json`.
   - Despues revisar los nodos `Call '<subworkflow>'` del workflow principal para que apunten a los subworkflows importados en la instancia de n8n.
6. Editar el nodo inicial de configuración con la organización/usuario deseado:
   - `project`: nombre estable para las salidas y el estado incremental.
   - `organizations`: lista de objetos con `org` y `type` (`org` o `user`).
   - `extra_repositories`: lista opcional de URLs adicionales.
   - `launch_issue`: `true` para publicar issues con `sw-metadata-bot publish`, `false` para ejecutar solo el análisis de metadatos.
7. Ejecutar manualmente

Tras ello se obtienen en `outputs` los metadatos SOCA, assessments RSFC y RESQUI, snapshots de sw-metadata-bot y el portal final. Nginx sirve el portal en `http://localhost:8030/portals/<project>/`.



## Instalación/Despliegue DashVERSE 0.3.0

### 1. Entrar en DashVERSE

Desde la raíz del repositorio SQOO:

```bash
cd integrations/DashVERSE-0.3.0
```

Comprobar los mandatos disponibles:

```bash
just --list
```

Comprobar dependencias:

```bash
just check-deps
```

### 2. Arrancar Minikube

```bash
minikube config set driver docker
minikube start --cpus=4 --memory=4096 --driver=docker
```

Comprobar el estado:

```bash
minikube status
kubectl get ns
```

### 3. Desplegar DashVERSE

```bash
just forward_address=0.0.0.0 deploy
```

Este mandato realiza el despliegue completo:

- comprueba las dependencias;
- comprueba o arranca Minikube;
- construye las imágenes de backend y frontend;
- aplica la infraestructura con OpenTofu;
- configura los port-forwards;
- sincroniza el catálogo de indicadores y dimensiones de EVERSE;
- importa dashboards, charts y datasets en Superset.

Si el despliegue falla en la importación de dashboards con `zip: not found`:

```bash
sudo apt update
sudo apt install -y zip unzip
just setup-dashboards
```

### 4. Comprobar servicios

```bash
just status
```

Consultar credenciales generadas:

```bash
just show-access
```

Consultar logs generales:

```bash
just logs
```

Logs concretos:

```bash
just logs-postgres
just logs-postgrest
just logs-superset
just logs-backend
just logs-frontend
```

### 5. URLs expuestas

Con los port-forwards activos se exponen los siguientes servicios:

- Frontend DashVERSE: `http://localhost:8080`
- Superset: `http://localhost:8088`
- API de assessments: `http://localhost:3000`
- API de autenticación/backend: `http://localhost:8000`
- Documentación de PostgREST: `http://localhost:3001`
- Documentación del backend: `http://localhost:8001`

Comprobaciones rápidas:

```bash
curl -I http://localhost:8088/health
curl http://localhost:3000/
```

### 6. Crear usuario

Acceder al backend:

```text
http://localhost:8000
```

Crear un usuario para SQOO, por ejemplo:

```text
username: sqoo
email: sqoo@example.org
password: <password>
```

### 7. Generar el token JWT

DashVERSE 0.3.0 incluye un mandato rápido para generar el JWT:

```bash
just jwt <usuario> '<password>'
```

Ejemplo:

```bash
just jwt sqoo '<password>'
```



### 8. Configurar SQOO

En `containers/.env` configurar:

```env
DASHVERSE_JWT=<token_generado_con_just_jwt>
SUPERSET_PUBLIC_DOMAIN=http://localhost:8088
```

### 9. Reimportar dashboards o resincronizar catálogo

Reimportar dashboards de Superset:

```bash
just setup-dashboards
```

Resincronizar indicadores y dimensiones EVERSE:

```bash
just trigger-sync
```

### 10. Parada y arranque posterior

Parar Minikube:

```bash
minikube stop
```

Volver a arrancar:

```bash
minikube start --driver=docker
```

Comprobar el servicio de port-forward:

```bash
just port-forward-status
```

Si los port-forwards no están activos:

```bash
just forward_address=0.0.0.0 port-forward
```




## 7. Estudios sobre el proyecto



**Evaluación de paralelismo de workers:** 
https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/estudios/#estudio-sobre-el-paralelismo-de-workers

**Estudio sobre RAM y espacio del dispositivo:**
*In progress*

---


## 8. Soporte
Para cualquier problema escribir una issue en:
https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/issues


