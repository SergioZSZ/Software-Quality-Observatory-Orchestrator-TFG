[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18879858.svg)](https://doi.org/10.5281/zenodo.18879858)[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)[![GitHub release](https://img.shields.io/github/v/release/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG?include_prereleases)](https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/releases)

**🚧🚧 STILL IN PROGRESS 🚧🚧**

Documentación detallada en : https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/

# TFG – Orquestación automatizada de evaluación de software y generación de catálogo



## 1. Objetivo del proyecto

El objetivo del TFG es diseñar e implementar un sistema reproducible que:

1. Extraiga automáticamente repositorios de GitHub
2. Genere metadatos estructurados del software
3. Evalúe la calidad del software mediante indicadores automáticos
4. Prepare la información para su integración en dashboards (DashVERSE) y catálogos (SOCA)
5. Permita orquestar todo el proceso mediante workflows automatizados

El sistema se basa en la integración y orquestación de herramientas existentes dentro de una arquitectura desacoplada y reproducible.




## 2. Arquitectura del sistema
---
| Componente       | Rol                                    |
| ---------------- | -------------------------------------- |
| n8n              | Orquestación                           |
| soca_container   | extracción metadatos y repos           |
| rsfc_container   | creación de jobs                       |
| rabbitmq         | message broker                         |
| worker_rsfc      | procesamiento jobs indicadores         |
| worker_soca      | procesamiento jobs metadatos           |
| rate_limiter_rsfc| limitador tokens githubAPI worker_rsfc |
| rate_limiter_soca| limitador tokens githubAPI worker_soca |
| DashVerse        | observatorio de evaluación             |


---


![Diagrama de flujo del sistema](docs/images/flujo_SQOO.png)

---

Cada herramienta se ejecuta en su propio entorno aislado, garantizando:

- Reproducibilidad
- Portabilidad
- Independencia del sistema operativo
- Aislamiento de dependencias
- Escalabilidad



## 3. Desarrollo
### 3.1 Dockerización de SOCA

Se ha:

- Preparado entorno aislado con poetry
- Clonado y preparado SOCA
- Adaptado su ejecución vía execute-command de n8n
- Encapsulado en un contenedor Docker
- Configurado volúmenes para persistencia de resultados
- Orquestado mediante lanzamiento de jobs para la extracción de metadatos por workers en paralelo
- Configurado un script para la generación del portal ejecutado por n8n
Salida generada:

- Fetch de los repositorios y envío a n8n
- Repositorios descargados
- Metadatos estructurados
- Portal web del catálogo


### 3.2 worker_soca container
El contenedor worker se encarga de la extracción de metadatos de los repositorios obtenidos en el fetch y generación del portal de manera asíncrona con el resto del workflow.

Mientras que soca_container publica en una cola de trabajo en RabbitMQ con el usuario/organización del cual se va a general el portal software.

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




### 3.6 Flujo actual(container n8n)
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

Para filtrar por organizaciones es necesario crear un filtro de la siguiente manera:
 *in progress_ filtros de orgs para dashboard, cross-filtering... EN MANUAL DE USUARIO*

---



## 4. Requisitos(Requirements)
#### Requisitos generales
   - Docker/Docker Desktop
   - Estar loggeado en Docker/Docker Desktop

#### Instalaciones necesarias para desplegar DashVERSE:
   - make 
      - Linux:   ``sudo apt install make --classic``
      - Windows: ``winget install -e --id GnuWin32.Make``

   - Terraform/OpenTofu 
      - Linux:    ``sudo snap install opentofu --classic`` 
      - Windows:  ``winget install --exact --id=OpenTofu.Tofu``

   - Minikube
      - Windows:  ``winget install -e --id Kubernetes.minikube``
      - Linux:    ``sudo snap install minikube --classic``

   - Helm      
      - Windows:  ``winget install -e --id Helm.Helm``
      - Linux:    ``sudo snap install kubectl --classic``

   - Kubectl
      - Windows:  ``winget install -e --id Kubernetes.kubectl``
      - Linux:    ``sudo snap install helm --classic``



#### Herramientas usadadas en el proyecto:
- SOCA 0.0.3: 
https://github.com/oeg-upm/soca/releases/tag/0.0.3

- RSFC 0.1.3: 
https://github.com/oeg-upm/rsfc/releases/tag/v0.1.3

- SOMEF 0.10.0:
https://github.com/KnowledgeCaptureAndDiscovery/somef/releases/tag/0.10.0

- DASHVERSE 0.2.0: 
https://github.com/EVERSE-ResearchSoftware/DashVERSE/releases/tag/v0.2.0

- RsMetaCheck 0.2.1:
https://github.com/SoftwareUnderstanding/RsMetaCheck/releases/tag/0.2.1
      

## 5. Instalación/Despliegue

#### 5.1 Previa
 Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_TOKEN` siguiendo el formato `GITHUB_TOKEN=xxxxxx` siendo `xxxxxx` el token personal de github obtenido desde github

   - `RABBITMQ_USER` usuario de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`

   - `RATE_LIMIT_RSFC_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI

   - `OUTPUTS` la ruta de acceso al directorio a usar como volumen compartido (se debe llamar ``outputs`` y estar dentro del directorio `/containers`)

   - `DASHBOARD_ORG_URL` la URL al dashboard org desplegado, `http://localhost:8088/superset/dashboard/nº_de_dashboard/` en caso de seguir las indicaciones del README y lanzarlo en local

   - `DASHBOARD_REPO_URL` la URL al dashboard repo desplegado, `http://localhost:8088/superset/dashboard/nº_de_dashboard/` en caso de seguir las indicaciones del README y lanzarlo en local

    ejemplo en `/containers/.env.example`. Se pueden usar tal cual las variables del archivo menos `GITHUB_TOKEN` y `OUTPUTS` y `DASHBOARD_URL`. 
    
    El token se debe obtener desde GitHub y generarlo con la opción 'All repositories', si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error).

    El nº de dashboard es el que aparezca tras importar en DashVERSE la plantilla contenida en `/integrations/dashboard`


#### 5.2 Instalación/Despliegue del orquestador
Siguiendo los pasos en orden secuencial:

1. Generar imágenes  docker:
   - `soca-heavy`:
      - Directorio desde el que crearla: `/containers/soca_container` 
      - Mandato: `docker build -t soca-heavy .`
   - `rsfc-heavy`:
      - Directorio desde el que crearla: `/containers/rsfc_container` 
      - Mandato: `docker build -t rsfc-heavy .`

2. Desde el directorio `/containers` ejecutar el mandato en la terminal `docker compose up -d --scale worker_rsfc=N --scale worker_soca=N`, siendo N el nº de workers a lanzar (si es la primera vez desplegándolo usar la etiqueta `--build` )

3. Acceder a n8n mediante el navegador en http://localhost:5678
4. En el primer acceso:
    1. Crear cuenta de usuario en n8n
    2. Importar el workflow de `/containers/n8n_container/workflow/` en un nuevo
5. Editar el nodo `Input` al principio del workflow con la organización/usuario deseado
6. Ejecutar manualmente

Tras ello se ejecutará el workflow obteniendo en el directorio outputs declarado las extracciones, portal, metadatos e indicadores correspondientes y enviándoselos a DashVERSE.



#### 5.3 Instalación/Despliegue de DashVERSE
Todo este proceso se deberá hacer desde una terminal Unix, no powershell de windows (por ejemplo Git Bash https://git-scm.com/install/windows), este proceso inicial hacerlo dentro del directorio `/integrations/DashVERSE-2.0`

1. instalar minikube,  kubectl, y helm (docker instalado de antes)
      mandato: `pip install minikube kubectl helm`

2. cambiar driver de minikube a docker
      mandato:``minikube config set driver docker``

3. arrancar cluster de minikube
      mandato: ``minikube start --cpus=4 --memory=4g --driver=docker``

   para comprobar que  kubernetes responde usar este mandato:
   ``kubectl get nodes`` y si funciona y se crea el nodo todo ok

4. desplegar y montar el servicio con el archivo make del directorio `/integrations/DashVERSE`
      mandato: `make deploy`

5. Comprobar que se haya desplegado bien todo
      mandato: `kubectl get all -n dashverse`

6. Port-forward de los puertos del servicio (en un terminal mantenerlo abierto):
      mandato: `make port-forward`

7. Obtener credenciales de acceso a Superset
      - secrets que existen: ``kubectl get secrets -n dashverse``
      - observación de los secrets dashverse: ``kubectl get secret dashverse-secrets -n dashverse -o yaml`` 
      - obtención de la contraseña admin sin codificar: ``kubectl get secret dashverse-secrets -n dashverse -o jsonpath="{.data.superset-admin-password}" | base64 --decode`` 
      - obtención contraseña bbdd sin codificar: ``kubectl get secret dashverse-secrets -n dashverse -o jsonpath="{.data.postgres-password}" | base64 --decode``

      la contraseña obtenida es la contraseña del usuario admin.

8. Conectarse a superset en http://localhost:8088
      login con user: admin   pwd: la obtenida desde los secretos

9. Añadir Database a dashverse

| Campo        | Valor                              |
| ------------ | ---------------------------------- |
| HOST         | `postgresql`                       |
| PORT         | `5432`                             |
| DATABASE     | `dashverse`                        |
| USERNAME     | `dashverse`                        |
| PASSWORD     | `contraseña bbdd obtenida antes`   |
| DISPLAY NAME | `DashVERSE DB`                     |


10. Se necesita un token jwt para las peticiones desde n8n. Para ello con el servicio desplegado ir a http://localhost:8000 y hacerse una cuenta EVERSE. Después hacer login y generar un token auth. Expiran tras un mes. Este token debe ponerse en los nodos que hacen peticiones http a dashVERSE del flujo n8n en el campo Authorization dentro de Headers como `Bearer TU_TOKEN`.

11. Importar los dashboards encontrados en `/integrations/dashboards`

   
#### 5.4 Encendido y apagado del servicio DashVERSE:

##### apagar todo:
1. ``Cntrl+C`` para cerrar el port-forwarding desde el terminal abierto
2. ``minikube stop `` apaga el cluster

##### encenderlo:
1. encendemos cluster: ``minikube start`` 
2. lo reiniciamos ``kubectl delete pods --all -n dashverse``
3. forwarding de puertos desde ``/integrations/DashVERSE-2.0`` en un terminal linux(GitBash por ejemplo): `make port-forward`



---


## 6. Estudios sobre el proyecto



**Evaluación de paralelismo de workers:** 
https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/estudios/#estudio-sobre-el-paralelismo-de-workers

**Estudio sobre RAM y espacio del dispositivo:**
*In progress*


# 7. Issues

## NEXT STEPS:

### DASHVERSE:
#### General
- documentar manual de uso de usuario de dashverse

#### Dashboards:
- cambiar top quality assessments por un ranking (1 tabla, pero preguntar por nuevo scores debido a scores propios de dashverse aunque no funcionan)
- pensar más dashboards para SQO-ORG


### Orquestador
- ver como subir a dashverse los indicadores de RsMetaCheck


 ### General:

- Añadir al diagrama de flujo sw-bot
- Añadir a la documentación lo relacionado con sw-bot
- Realizar un nuevo estudio de consumo de memoria + espacio en disco
- Ver si merece la pena hacer un RO
- FAIRificar los repositorios mejorando los checks de metadatos
- (Si da tiempo) automatizar sugerencias para mejorar los repositorios


