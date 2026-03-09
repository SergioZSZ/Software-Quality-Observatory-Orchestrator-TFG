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
| Componente       | Rol                    |
| ---------------- | ---------------------- |
| n8n              | Orquestación           |
| soca_container   | extracción de repos    |
| rsfc_container   | creación/status de jobs|
| postgres         | base de datos          |
| rabbitmq         | message broker         |
| worker_container | procesamiento paralelo |

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
- Adaptado su ejecución vía API
- Encapsulado en un contenedor Docker
- Configurado volúmenes para persistencia de resultados
- Orquestado mediante lanzamiento de jobs a RabbitMQ la generación del portal software
- Implementado lanzamiento de un worker para procesar el job usando la cola de trabajo de RabbitMQ

Salida generada:

- Fetch de los repositorios y envío a n8n
- Repositorios descargados
- Metadatos estructurados
- Portal web del catálogo

### 3.1.2. Endpoints de soca_container

- `funcions/run`
    - Argumentos necesarios: 
        1. `target`: Nombre del usuario/organización de GitHub
        2. `type`: Declaración del tipo de `target`, usuario-> `user`, organización->`org`
    
    - Utilidades:
        - Fetch de repositorio del `target` dado
        - Publicación de jobs a cola de trabajo de RabbitMQ para extraer metadatos de repos fetcheados y de la generación del portal
        - Generación de ficheros status.json guardando el estado de la extracción de metadatos y generación del portal

    - Response:
        - `json` con los repositorios de la organización


- `funcions/status-metadata/{target}`
    - Argumentos necesarios: 
        1. `target`: Nombre del usuario/organización de GitHub
    
    - Utilidades:
        - Comprobación del fichero status.json de extracción de metadatos del target dado
    
    - Response:
        - Contenido del fichero status.json

- `funcions/status-portal/{target}`
    - Argumentos necesarios: 
        1. `target`: Nombre del usuario/organización de GitHub
    
    - Utilidades:
        - Comprobación del fichero status.json de generación del portal software del target dado
    
    - Response:
        - Contenido del fichero status.json

### 3.3 worker_soca container
El contenedor worker se encarga de la extracción de metadatos de los repositorios obtenidos en el fetch y generación del portal de manera asíncrona con el resto del workflow.

Mientras que soca_container actúa como API encargada publicar en una cola de trabajo en RabbitMQ con el usuario/organización del cual se va a general el portal software.

Cada worker ejecuta el módulo `python -u -m soca_runner.worker` que se dedica a:

1. Recibe un job de RabbitMQ (con el target)
2. Cambia ficheros status.json a "running"
3. Se extraen metadatos de los repos obtenidos en el fetch por workers asíncronos
4. Genera el portal software del target tras la extracción de metadatos de todos los repositorios
5. Cambia ficheros status.json a "completed" o "error"

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_soca=N`` siendo N el número de workers que se levantarán.

### 3.3.1 Dockerización de RSFC

Se ha:

- Preparado entorno aislado con poetry
- Instalado RSFC en el entorno
- Adaptado su ejecución vía API
- Encapsulado en contenedor independiente
- Orquestado mediante lanzamiento de jobs a RabbitMQ la extraccion de indicadores
- Creado una BBDD de jobs con su id, status, url_repo, detalles y result_path
- Implementado lanzamiento de workers para procesar los jobs usando la cola de trabajo de RabbitMQ

Salida generada:
- Generación de indicadores de calidad en formato `json`


### 3.3.2. Endpoints rsfc_container

- `funcions/run`
    - Argumentos necesarios:
        1. `repo_url`: url del repositorio a obtener indicadores
    
    - Utilidades:
        - Publicación de un job en RabbitMQ para procesamiento de la url por los workers
    
    - Response:
        - `json` con status del proceso y su id
    
- `/status/{job_id}`
    - Argumentos necesarios:
        1. `job_id`: id del job a verificar
    
    - Utilidades:
        - comprobación del estado del job y obtención de indicadores en caso de terminar
    
    - Response:
        - `json` con el estado del job, los detalles en caso de running y los indicadores en caso de success



### 3.4 worker_rsfc container
El contenedor worker se encarga del procesamiento asíncrono de los jobs generados por rsfc_container.

Mientras que rsfc_container actúa como API encargada de registrar los jobs, los workers se encargan de consumir dichos jobs desde la base de datos y ejecutar el análisis con RSFC.

Cada worker ejecuta el módulo `python -u -m rsfc_runner.worker` que se encarga de recibir los jobs publicados en RabbitMQ que:

1. Recibe un job de RabbitMQ
2. Cambia los jobs con estado queued a estado a running
4. Ejecuta la evaluación del repositorio mediante rsfc
5. Guarda los resultados generados en la bbdd
6. Actualiza el estado del job a success, error u evaluating
7. Espera a tener token para procesar siguiente trabajo (github rate limit)
8. Responde a RabbitMQ habiendo procesado el job para recibir otro

El sistema permite escalar horizontalmente el número de workers mediante docker compose lanzándolo con``docker compose up --scale worker_rsfc=N`` siendo N el número de workers que se levantarán.


### 3.5 worker_rsfc container
El contenedor rate_limiter se encarga del envío de tokens a una cola de RabbitMQ de tamaño 1. Los workers RSFC se esperarán a obtener un token de la cola para procesar los jobs para no saturar de peticiones GitHubAPI y no sobrepasar el RateLimit.

**NOTA: ATENCION A LA SECCION MEJORAS POR PROBLEMA CON ESTA IMPLEMENTACION**

### 3.6 Flujo actual(container n8n)

Mediante `n8n` se ha orquestado un workflow que realiza una petición http a las APIs dockerizadas para generar los diversos datos correspondientes a cada entrada del flujo:

1. Verificación de que los contenedores SOCA y RSFC estén activos
2. Petición http a soca_container para realizar el fetch 
3. Generación en paralelo del flujo del portal software de los repositorios obtenidos en el fetch
4. Split de n8n de los repositorios obtenidos 
5. Realización de httpRequests síncronos a `rsfc_container` de los repositorios obtenidos, obteniendo el id del job que se lanzó para procesar ese repositorio
6. Revisión de estado de jobs para gestión de error/success y obtención posterior de indicadores de calidad


## 4. Activación del entorno y ejemplo de uso
**PREVIA:** Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_TOKEN` siguiendo el formato `GITHUB_TOKEN=xxxxxx` siendo `xxxxxx` el token personal de github obtenido desde github
   - `DATABASE_URL` siguiendo el formato `DATABASE_URL=postgresql://usuario:password@host:puerto/database` siendo el usuario, password y database configurados en el environment del docker-compose.yml, host=postgres y puerto expuesto (default 5432)
   - `RABBITMQ_USER` usuario de RabbitMQ del docker compose
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ del docker compose

    ejemplo en `/containers/.env.example`. Se pueden usar tal cual las variables del archivo menos `GITHUB_TOKEN`. Este se debe obtener desde GitHub y generarlo con la opción 'All repositories', si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI 

### 4.1 Requisitos
    
   - Docker/Docker Desktop
   - Estar loggeado en Docker/Docker Desktop

Herramientas usadadas en el proyecto:
   - SOCA: https://github.com/oeg-upm/soca/
   - RSFC: https://github.com/oeg-upm/rsfc/
   - SOMEF: https://github.com/KnowledgeCaptureAndDiscovery/somef
   - DASHVERSE: https://github.com/EVERSE-ResearchSoftware/DashVERSE

### 4.2 Despliegue y ejecución

1. Desde el directorio `/containers` ejecutar el mandato en la terminal `docker compose up -d --scale worker_rsfc=N --scale worker_soca=N`, siendo N el nº de workers a lanzar(recomendable máximo 5 de cada)
2. Acceder a n8n mediante el navegador en http://localhost:5678
3. En el primer acceso:
    1. Crear cuenta de usuario en n8n
    2. Importar el workflow `/containers/n8n_container/workflow/cola_dinámica_con_workers.json` en un nuevo workflow
4. Ejecutar el workflow aún en test desde el nodo `Webhook`
5. Ejecutar el programa `/client/client.py` y rellenar los campos pedidos 

Tras ello se ejecutará el workflow obteniendo en el último nodo obteniendo como respuesta en
el programa ejecutado los repositorios procesados o los errores.


### Ejemplo de uso
1. Desde el directorio `/containers` en la terminal: `docker compose up -d --scale worker=4`
2. Activar el workflow como comentado antes de n8n en el nodo `WebHook` al princpio del workflow
3. Desde el directorio `/client` en la terminal: `poetry run python .\client.py`
4. Rellenar campos:
    - Introduce el usuario u organización: SergioZSZ
    - Introduce el tipo (user/org): user
5. Cuando se procesen los metadatos se guardará un `.json` en el directorio de `/client` con los indicadores/error generado y los ficheros generados durante el proceso en `/containers/outputs`.

## 5. Issues


- Actualizar diagrama de flujo con las nuevas funcionalidades añadidas (workers, rabbitmq, bbdd)
- Actualizar proyecto para que somef se ejecute solo 1 vez 
- Codificación y Dockerización de `dashverse_container` e implementar sus funcionalidades
- Integración en el workflow de `dashverse_container` y obtención de urls a dashboards
- Generación del portal software mediante `soca_container` con urls a dashboards
- Actualizar somef en soca y mejorar los metadatos mostrados
- FAIRificar los repositorios mejorando los checks de metadatos
- (Si da tiempo) automatizar sugerencias para mejorar los repositorios


- Actualmente el rendimiento del sistema está condicionado por las limitaciones externas de la API de GitHub:
    - 5000 requests/hora por token 
    - Si hay muchas peticiones en poco tiempo a un repositorio/user/org, como puede pasar con el contenedor RSFC, GitHubAPI devuelve `error 403 rate limit`, habiendo superado el rate limit que ofrece por un tiempo
por lo que organizaciones o usuarios con muchos repositorios pueden dar errores. Debido a ello se recomienda el uso de 4 workers al ejecutar el proyecto y se ha establecido un sleep de 8 a 10 segundos antes de ejecutar RSFC para no recibir ese error. Hay una versión del proyecto que falta por probar consistente en procesar secuencialmente los repositorios en vez de con un sistema de cola dinámico, pero tarda bastante más en procesarlos

- Se podría realizar una implementación para encontrar repositorios ya fetcheados/extraídos para no tener que volver a llamar a GitHubAPI y usar los metadatos/indicadores ya extraídos











   

