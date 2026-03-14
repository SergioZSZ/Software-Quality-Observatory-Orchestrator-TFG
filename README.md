**STILL IN PROCESS**


# TFG – Orquestación automatizada de evaluación de software y generación de catálogo
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18879858.svg)](https://doi.org/10.5281/zenodo.18879858)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![GitHub release](https://img.shields.io/github/v/release/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG?include_prereleases)](https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/releases)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
## 1. Objetivo del proyecto

El objetivo del TFG es diseñar e implementar un sistema reproducible que:

1. Extraiga automáticamente repositorios de GitHub
2. Genere metadatos estructurados del software
3. Evalúe la calidad del software mediante indicadores automáticos
4. Prepare la información para su integración en dashboards (DashVERSE) y catálogos (SOCA)
5. Permita orquestar todo el proceso mediante workflows automatizados

El sistema se basa en la integración y orquestación de herramientas existentes dentro de una arquitectura desacoplada y reproducible.




## 2. Arquitectura actual
---
| Componente       | Rol                                    |
| ---------------- | -------------------------------------- |
| n8n              | Orquestación                           |
| soca_container   | extracción/status metadatos y repos    |
| rsfc_container   | creación/status de jobs                |
| postgres         | base de datos                          |
| rabbitmq         | message broker                         |
| worker_rsfc      | procesamiento jobs indicadores         |
| worker_soca      | procesamiento jobs metadatos/portal    |
| rate_limiter_rsfc| limitador tokens githubAPI worker_rsfc |
| rate_limiter_soca| limitador tokens githubAPI worker_soca |


---

### Arquitectura basada en contenedores Docker

El sistema está desacoplado en contenedores independientes:

- `soca`
- `rsfc`
- `n8n` (actualmente incorporado hasta obtención de clasificadores mediante `rsfc`)
- `postgres`
- `worker` 
- `rabbitmq`
- Red Docker compartida


Cada herramienta se ejecuta en su propio entorno aislado, garantizando:

- Reproducibilidad
- Portabilidad
- Independencia del sistema operativo
- Aislamiento de dependencias
- Escalabilidad



## 3. Estado actual del desarrollo
### 3.1.1 Dockerización de SOCA

Se ha:

- Preparado entorno aislado con poetry
- Clonado y preparado SOCA
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en un contenedor Docker
- Configurado volúmenes para persistencia de resultados
- Orquestado mediante lanzamiento de jobs para la extracción de metadatos y generación del portal por workers en paralelo

Salida generada:

- Fetch de los repositorios y envío a n8n
- Repositorios descargados
- Metadatos estructurados
- Portal web del catálogo


### 3.3 worker_soca container
El contenedor worker se encarga de la extracción de metadatos de los repositorios obtenidos en el fetch y generación del portal de manera asíncrona con el resto del workflow.

Mientras que soca_container publica en una cola de trabajo en RabbitMQ con el usuario/organización del cual se va a general el portal software.

Cada worker ejecuta el módulo `python -u -m soca_runner.worker` que se dedica a:

1. Recibe un job de RabbitMQ (con el target)
2. Cambia ficheros status.json a "running"
3. Se extraen metadatos de los repos obtenidos en el fetch por workers paralelos
4. Genera el portal software del target tras la extracción de metadatos de todos los repositorios
5. Cambia ficheros status.json a "completed" o "error"
6. Envío de mensaje a RabbitMQ de finalizada extracción de metadatos

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_soca=N`` siendo N el número de workers que se levantarán.

### 3.3.1 Dockerización de RSFC

Se ha:

- Preparado entorno aislado con poetry
- Instalado RSFC en el entorno
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en contenedor independiente
- Orquestado mediante lanzamiento de jobs a RabbitMQ la extraccion de indicadores
- Creado una BBDD de jobs con su id, status, url_repo, detalles y result_path
- Implementado lanzamiento de workers para procesar los jobs usando la cola de trabajo de RabbitMQ

Salida generada:
- Generación de indicadores de calidad de cada repositorio en formato `json`


### 3.4 worker_rsfc container
El contenedor worker se encarga del procesamiento asíncrono de los jobs generados por rsfc_container.

Mientras que rsfc_container actúa como encargado de registrar los jobs en la cola de trabajo de RabbitMQ correspondiente, los workers se encargan de consumir dichos jobs y ejecutar el análisis con RSFC.

Cada worker ejecuta el módulo `python -u -m rsfc_runner.worker` que se encarga de recibir los jobs publicados en RabbitMQ que:

1. Recibe un job de RabbitMQ
2. Cambia los jobs con estado queued a estado a running
4. Ejecuta la evaluación del repositorio mediante rsfc
5. Guarda los resultados generados en la bbdd
6. Actualiza el estado del job a success, error
7. Espera a tener token para procesar siguiente trabajo (github rate limit)
8. Responde a RabbitMQ habiendo procesado el job para recibir otro

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_rsfc=N`` siendo N el número de workers que se levantarán.


### 3.5 rate_limiter_rsfc container
El contenedor rate_limiter se encarga del envío de tokens a una cola de RabbitMQ de tamaño 1. Los workers RSFC se esperarán a obtener un token de la cola para procesar los jobs para no saturar de peticiones GitHubAPI y no sobrepasar el RateLimit.


### 3.6 Flujo actual(container n8n)

Mediante `n8n` se han orquestado 2 workflows para la ejecución del flujo:

1. soca_workflow: ejecuta `soca_container` via docker de la organización escrita y su tipo escritas en formato `.json` del nodo Edit Fields. El workflow se activa manualmente pulsando en 'Execute Workflow'

2. rsfc_worfklow: Se activa mediante un nodo `RabbitMQ Trigger` configurado para actuar cuando la cola `soca_events` recibe el evento `soca_extracted`. Entonces se leen y transforman los enlaces del archivo `repos.txt` generados en el fetch para enviárselos a `rsfc_container` para que publique los jobs de dichos repositorios. **DEBE ESTAR EN ESTADO PUBLISH**

Ambos workflow se encuentran en `/containers/n8n_container/workflow`



## 4. Activación del entorno y ejemplo de uso
**PREVIA:** Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_TOKEN` siguiendo el formato `GITHUB_TOKEN=xxxxxx` siendo `xxxxxx` el token personal de github obtenido desde github
   - `DATABASE_URL` siguiendo el formato `DATABASE_URL=postgresql://usuario:password@host:puerto/database` siendo el usuario, password y database configurados en el environment del docker-compose.yml, host=postgres y puerto expuesto (default 5432)
   - `RABBITMQ_USER` usuario de RabbitMQ del docker compose
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ del docker compose
   - ``RATE_LIMIT_SOCA_ENABLED`` y `RATE_LIMIT_SOCA_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI(con workers de soca no hace falta debido a que realiza 1 petición/repo, de rsfc si ya que realiza 7 aprox)
   - `OUTPUTS` la ruta de acceso al directorio a usar como volumen compartido (se debe llamar ``outputs`` y estar dentro del directorio `/containers`)

    ejemplo en `/containers/.env.example`. Se pueden usar tal cual las variables del archivo menos `GITHUB_TOKEN` y `OUTPUTS`. El token se debe obtener desde GitHub y generarlo con la opción 'All repositories', si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error)

### 4.1 Requisitos
    
   - Docker/Docker Desktop
   - Estar loggeado en Docker/Docker Desktop

Herramientas usadadas en el proyecto:
   - SOCA: https://github.com/oeg-upm/soca/
   - RSFC: https://github.com/oeg-upm/rsfc/
   - SOMEF: https://github.com/KnowledgeCaptureAndDiscovery/somef
   - DASHVERSE: https://github.com/EVERSE-ResearchSoftware/DashVERSE

### 4.2 Despliegue y ejecución

1. Desde el directorio `/containers` ejecutar el mandato en la terminal `docker compose up -d --scale worker_rsfc=N --scale worker_soca=N`, siendo N el nº de workers a lanzar

        - Configuración usada en desarrollo RSFC worker = 5 | SOCA worker = 10
2. Acceder a n8n mediante el navegador en http://localhost:5678
3. En el primer acceso:
    1. Crear cuenta de usuario en n8n
    2. Importar los workflows de `/containers/n8n_container/workflow/` en  nuevos workflows
    3. Publicar `rsfc_workflow`
4. Editar el nodo `Edit Field` de `soca_workflow` con la organización/usuario deseado
5. Ejecutar `soca_workflow` manualmente 

Tras ello se ejecutará el workflow obteniendo en el directorio outputs declarado las extracciones, portal, metadatos e indicadores correspondientes.


## 5. Evaluación del paralelismo en los workers
## 5.1 Hardware usado en las pruebas

| Componente        | Especificación                  |
| ----------------- | ------------------------------- |
| Equipo            | Lenovo 20WNS30L13               |
| CPU               | Intel Core i7-1185G7 (11th Gen) |
| Núcleos           | 4 cores / 8 threads             |
| Frecuencia        | ~3.0 GHz                        |
| RAM               | 16 GB                           |
| Sistema Operativo | Windows 11 Pro 64 bits          |
| DirectX           | DirectX 12                      |

## 5.2 Rendimientos con distintos workers


**IN PROGRESS**



## 6. Issues



- Paralelización procesamientos SOCA y RSFC: Codificar que la publicación de jobs rsfcs se realice nada más extraer los datos del repo(reduciendo así enormemente el tiempo del workflow) 
- Actualizar diagrama de flujo con las nuevas funcionalidades añadidas (workers, rabbitmq, bbdd, limmiters)
- Actualizar proyecto para que somef se ejecute solo 1 vez 
- Codificación y Dockerización de `dashverse_container` e implementar sus funcionalidades
- Integración en el workflow de `dashverse_container` y obtención de urls a dashboards
- Añadir URL dashverse a repositorios del portal software
- Actualizar somef en soca y mejorar los metadatos mostrados(somef actualizado ya hecho en el setup.cfg de soca)
- FAIRificar los repositorios mejorando los checks de metadatos
- (Si da tiempo) automatizar sugerencias para mejorar los repositoros
