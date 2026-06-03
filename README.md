[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18879858.svg)](https://doi.org/10.5281/zenodo.18879858)[![Project Status: Active ](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)[![GitHub release](https://img.shields.io/github/v/release/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG?include_prereleases)](https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/releases)![RSFC_Coverage](https://img.shields.io/badge/rsfc-coverage_83%25-green)


Documentación detallada en : https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/

# TFG – Orquestación automatizada de evaluación de software y generación de catálogo



## 1. Objetivo del proyecto

El objetivo del TFG es diseñar e implementar un sistema reproducible que:

1. Extraiga automáticamente repositorios de GitHub
2. Genere metadatos estructurados del software
3. Evalúe la calidad del software mediante indicadores automáticos
4. Evalúe la calidad de los metadatos del software y suba Issues automáticas a GitHub
5. Prepare la información para su integración en dashboards (DashVERSE) y catálogos (SOCA)
6. Permita orquestar todo el proceso mediante workflows automatizados

El sistema se basa en la integración y orquestación de herramientas existentes dentro de una arquitectura desacoplada y reproducible.

---



## 2. Arquitectura del sistema

| Componente       | Rol                                    |
| ---------------- | -------------------------------------- |
| n8n              | Orquestación                           |
| soca_container   | extracción metadatos-repos y jobs soca |
| rsfc_container   | creación de jobs rsfc                  |
| rabbitmq         | message broker                         |
| worker_rsfc      | procesamiento jobs indicadores         |
| worker_soca      | procesamiento jobs metadatos           |
| rate_limiter_rsfc| limitador tokens githubAPI worker_rsfc |
| nginx            | publicacion del portal SOCA |
| DashVerse        | observatorio de evaluación             |
| sw-metadata-bot  | Generación de issues sobre metadatos   |





![Diagrama de flujo del sistema](docs/images/flujo_SQOO.png)



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

### 3.6 DashVerse Service
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




### 3.7 Integración de sw-metadata-bot

Se ha:

- Integrado `sw-metadata-bot` como herramienta encargada de analizar la calidad de los metadatos de los repositorios procesados
- Preparado el uso del bot mediante una imagen Docker `sw-metadata-bot:latest`
- Adaptado su ejecución vía `execute-command` de n8n
- Configurado el montaje del volumen compartido de `outputs` para persistir los resultados del análisis
- Generado dinámicamente un archivo `config.json` con la lista de repositorios obtenidos durante el workflow
- Configurado el uso de `GITHUB_API_TOKEN` para permitir la consulta de repositorios y la publicación de issues
- Incorporado el análisis incremental mediante `previous_report`, permitiendo reutilizar ejecuciones anteriores cuando se indique
- Añadida la fase de publicación de issues tras la generación de los informes de metadatos

El servicio `sw-metadata-bot` se ejecuta dentro del flujo de n8n después de obtener la lista de repositorios que forman parte del análisis. Para cada ejecución se crea un directorio específico dentro de:

- `/outputs/sw-metadata-bot/<target>/`

---


### 4. Flujo actual(container n8n)
El sistema utiliza **n8n** como motor de orquestación para coordinar la ejecución completa del pipeline de análisis. 

A diferencia de versiones anteriores, donde el flujo estaba dividido en múltiples workflows (`soca`, `rsfc`, `dashboard`), actualmente se ha **unificado en un único workflow end-to-end**, simplificando la gestión, monitorización y control del proceso.



#### Descripción general del flujo

El workflow implementa un pipeline completo que abarca:

1. **Extracción de repositorios**
2. **Procesamiento de metadatos (SOCA)**
3. **Evaluación de calidad (RSFC)**
4. **Evaluación de metadatos(sw-metadata-bot)**
5. **Generación de portal software enriquecido**
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

##### 4. Análisis de metadatos con sw-metadata-bot

n8n ejecuta `sw-metadata-bot` para analizar la calidad de los metadatos de los repositorios y generar issues automáticos cuando se detectan carencias. Todo siguiento este proceso:

- Generado un `config.json` con los repositorios obtenidos en el workflow

- Ejecutado el análisis mediante `sw-metadata-bot run-analysis`
- Reutilizado ejecuciones anteriores mediante `previous_report` cuando aplica
- Publicado los issues generados mediante `sw-metadata-bot publish`

##### 5. Generación del portal

- Se ejecuta `genportal.py` cuando ya existen los reportes de RSFC y sw-metadata-bot.
- El portal incorpora metadatos SOCA, indicadores RSFC e informes/issues de sw-metadata-bot.
- Portal persistido en `outputs/soca/<target>/portal/` y publicado por Nginx.
- Incluye dashboards embebidos mediante iframe directo a Superset/DashVERSE.

Salida generada: portal software enriquecido con reportes y metadatos


##### 6. Envío de assessments a DashVERSE

- Lectura de los archivos generados: `rsfc_assessment.json` por cada repositorio
- Extracción y transformación de los datos del assessment añadiendo un @id y el `author` como keys del json-ld

- Iteración sobre cada repositorio y sus checks mediante nodos `Split Out`
- Envío de datos mediante peticiones HTTP POST a la API de DashVERSE `/assessment_raw`

---





## 4. Requisitos(Requirements)
#### Requisitos generales
   - Docker/Docker Desktop
   - Estar loggeado en Docker/Docker Desktop

#### Instalaciones necesarias para desplegar DashVERSE:
Si usas windows, todo debe ser realizado e instalado desde un entorno Ubuntu como WSL, la que usaremos siempre para el despliegue de dashverse. Ansible no funciona como control node nativo en Windows y conviene que `kubectl`, `make port-forward` y `make setup-dashboards` se ejecuten en el mismo entorno para que no haya problemas con `localhost`.

Antes de empezar en Windows hay que tener Docker Desktop instalado, abierto y con la integracion WSL activada para Ubuntu.

   - make 
      - Linux/WSL:   ``sudo apt install make``

   - Terraform/OpenTofu 
      - Linux/WSL:    ``sudo snap install opentofu --classic`` 

   - Minikube
      - Linux/WSL:
        ```bash
        curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
        sudo install minikube-linux-amd64 /usr/local/bin/minikube
        rm minikube-linux-amd64
        minikube version
        ```
      
   - Helm      
      - Linux/WSL:    ``sudo snap install helm --classic``

   - Kubectl
      - Linux/WSL:    instalarlo dentro de WSL y comprobar que `which kubectl` apunta al binario de linux
      
   - Ansible
      - Linux/WSL:
        ```bash
        sudo apt update
        sudo apt install -y python3 python3-pip
        python3 -m pip install --user ansible
        ansible --version
        ```


         

#### Herramientas usadadas en el proyecto:
- SOCA 0.0.3: 
https://github.com/oeg-upm/soca/releases/tag/0.0.3

- RSFC 0.1.5: 
https://github.com/oeg-upm/rsfc/releases/tag/v0.1.5

- SOMEF 0.10.3:
https://github.com/KnowledgeCaptureAndDiscovery/somef/releases/tag/0.10.3

- DASHVERSE 0.2.0: 
https://github.com/EVERSE-ResearchSoftware/DashVERSE/releases/tag/v0.2.0

- sw-metadata-bot 0.4.2:
https://github.com/SoftwareUnderstanding/sw-metadata-bot/releases/tag/v0.4.2

- RsMetaCheck 0.2.1:
https://github.com/SoftwareUnderstanding/RsMetaCheck/releases/tag/0.2.1
      
      
---


## 5. Instalación/Despliegue

#### 5.1 Previa
 Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_API_TOKEN`: siguiendo el formato `GITHUB_TOKEN=xxxxxx`, siendo el `xxxxxx` el token personal obtenido desde github ( token classic) marcándo el scope 'public_repo' 

   - `RABBITMQ_USER` usuario de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`

   - `RATE_LIMIT_RSFC_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI

   - `OUTPUTS` la ruta de acceso al directorio a usar como volumen compartido (se debe llamar ``outputs`` y estar dentro del directorio `/containers`)
   - `PORTAL_PORT` puerto del host desde el que Nginx publica los portales SOCA (por defecto `8030`)

   - `DASHBOARD_ORG_EMBED_ID` id o slug del dashboard SQO-org importado en DashVERSE/Superset
   - `DASHBOARD_REPO_EMBED_ID` id o slug del dashboard SQO-repo importado en DashVERSE/Superset

   - ``SUPERSET_PUBLIC_DOMAIN`` dominio publico usado por el portal para cargar los dashboards embebidos. En Docker Desktop/Windows se debe usar `http://host.docker.internal:8088` para que el portal generado desde los contenedores apunte correctamente a Superset.

      ejemplo en `/containers/.env.example`. Se pueden usar tal cual las variables del archivo menos `GITHUB_TOKEN`, `OUTPUTS`, `DASHBOARD_ORG_EMBED_ID` y `DASHBOARD_REPO_EMBED_ID`.


**A tener en cuenta**:  
-  El token (classic) se debe obtener desde GitHub y seleccionando el scope 'public_repo'. si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error) y no se podrán subir las Issues automáticamente.

-  El nº o slug de dashboard es el que aparezca tras importar en DashVERSE la plantilla contenida en `/integrations/dashboard`. Los dashboards deben estar publicados y permitir embebido desde el portal.


#### 5.2 Instalación/Despliegue del orquestador
Siguiendo los pasos en orden secuencial:

1. Generar imágenes  docker:
   - `soca-heavy`:
      - Directorio desde el que crearla: `/containers/soca_container` 
      - Mandato: `docker build -t soca-heavy .`
   - `rsfc-heavy`:
      - Directorio desde el que crearla: `/containers/rsfc_container` 
      - Mandato: `docker build -t rsfc-heavy .`
   - `sw-metadata-bot`:
      - Directorio desde el que crearla: `/integrations/sw-metadata-bot-0.4.2`
      
2. Desde el directorio `/containers` ejecutar el mandato en la terminal `docker compose up -d --scale worker_rsfc=N --scale worker_soca=N`, siendo N el nº de workers a lanzar (si es la primera vez desplegándolo usar la etiqueta `--build` )

3. Acceder a n8n mediante el navegador en http://localhost:5678
4. En el primer acceso:
    1. Crear cuenta de usuario en n8n
    2. Importar el workflow de `/containers/n8n_container/workflow/` en un nuevo
5. Editar el nodo `Input` al principio del workflow con la organización/usuario deseado
6. Ejecutar manualmente

Tras ello se ejecutará el workflow obteniendo en `outputs` las extracciones, reportes RSFC, informes de sw-metadata-bot y el portal final enriquecido antes del envío a DashVERSE. Los portales generados por SOCA se sirven con Nginx en `http://localhost:8030/portals/<target>/`, donde `<target>` coincide con la organizacion o usuario configurado en el workflow. Las paginas `dashboard-org.html` y `dashboard-repo.html` cargan los dashboards de DashVERSE mediante iframe directo usando `SUPERSET_PUBLIC_DOMAIN`.



#### 5.3 Instalación/Despliegue de DashVERSE
**PREVIA**
Todos los scripts de `/integrations/DashVERSE-0.2.0/scripts` deben tener permisos de ejecución para la instalación de DashVERSE en Linux `chmod +x *.sh`

Todo este proceso, si se usa Windows, se debe hacer desde Ubuntu en WSL, no desde PowerShell ni Git Bash. Ansible no corre de forma nativa en Windows y es importante que `kubectl`, `make port-forward` y `make setup-dashboards` se ejecuten en el mismo entorno.

Tambien es recomendable copiar DashVERSE al sistema de archivos de WSL para evitar problemas de permisos con Ansible al trabajar desde `/mnt/c`:

```bash
mkdir -p ~/projects/SQOO_TFG/integrations
rsync -a /mnt/c/Users/jzaba/Documents/GitHub/SQOO_TFG/integrations/DashVERSE-0.2.0/ ~/projects/SQOO_TFG/integrations/DashVERSE-0.2.0/
chmod -R go-w ~/projects/SQOO_TFG
cd ~/projects/SQOO_TFG/integrations/DashVERSE-0.2.0
```

1. comprobar que Docker Desktop esta accesible desde WSL:
      mandato: `docker ps`

2. si `kubectl` apunta a un binario antiguo, dejar primero `/usr/bin` en el PATH:
      mandato: `echo 'export PATH="/usr/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc`

3. cambiar driver de minikube a docker
      mandato:``minikube config set driver docker``

4. arrancar cluster de minikube
      mandato: ``minikube start --cpus=4 --memory=4096 --driver=docker``

   para comprobar que  kubernetes responde usar este mandato:
   ``kubectl get nodes`` y si funciona y se crea el nodo todo ok


5. desplegar y montar el servicio con el archivo make del directorio de DashVERSE. Primero hay que instalar superset con helm.
      mandatos: `helm repo add Superset https://apache.github.io/superset --force-update`
      `helm repo update`
y posteriormente hacer el deploy
      mandato: `make deploy`
tras ello, realizar `make sync-apply` para importar los indicadores y dimensiones EVERSE en la base de datos (tener en cuenta las modificaciones dashverse si no se usa el DASHVERSE del repositorio)

6. Comprobar que se haya desplegado bien todo
      mandato: `kubectl get all -n dashverse`

7. Port-forward de los puertos del servicio (en un terminal WSL mantenerlo abierto):
      mandato: `make port-forward` 
      **NOTA:** si se esta desplegando en servidores y no en local, si se quiere tener accesible el subdominio para acceder se debe sustituir la línea 21 por `--address 0.0.0.0 -n "$NS" "svc/$svc" "$local_port:$remote_port" 2>/dev/null || true` en el script `/integrations/DashVERSE-0.2.0/scripts/port-forward.sh.sh`

   Desde Windows se puede acceder en el navegador a `http://localhost:8088`, `http://localhost:8080`, `http://localhost:3000` y `http://localhost:8000` mientras ese terminal siga abierto.

8. Obtener credenciales de acceso a Superset
      desde terminal linux, ejecutar desde este mismo directorio
      `bash ./scripts/show-access.sh` pudiendo obtener así todas las credenciales necesarias


9. Conectarse a superset en http://localhost:8088
      login con user: admin   pwd: la obtenida desde el script anterior

10. generar conexión a la BBDD y dashboards base de DashVERSE:
      mandato: ``make setup-dashboards``

11. Se necesita un token jwt para las peticiones desde n8n. Para ello con el servicio desplegado ir a http://localhost:8000 y hacerse una cuenta EVERSE. Después hacer login y generar un token auth. Expiran tras un mes. Este token debe ponerse en los nodos que hacen peticiones http a dashVERSE del flujo n8n en el campo Authorization dentro de Headers como `Bearer TU_TOKEN`.

12. Importar los dashboards encontrados en `/integrations/dashboards` si se quieren mantener tambien los dashboards SQOO antiguos. También editarlos desde la pestaña de navegación `Dashboards` para darle acceso a los roles que se quieran configurar (Admin y Public por ejemplo). También habrá que configurar los permisos de los roles. Para ello acceder a `Settings/list roles` y editar los permisos de los roles, mínimo del Public.

   
#### 5.4 Encendido y apagado del servicio DashVERSE:

##### apagar todo:
1. ``Cntrl+C`` para cerrar el port-forwarding desde el terminal abierto
2. ``minikube stop `` apaga el cluster

##### encenderlo:
1. encendemos cluster: ``minikube start`` 
2. lo reiniciamos ``kubectl delete pods --all -n dashverse``
3. forwarding de puertos desde ``~/projects/SQOO_TFG/integrations/DashVERSE-0.2.0`` en un terminal WSL: `make port-forward`

---



## 6. Estudios sobre el proyecto



**Evaluación de paralelismo de workers:** 
https://software-quality-observatory-orchestrator-tfg.readthedocs.io/es/latest/estudios/#estudio-sobre-el-paralelismo-de-workers

**Estudio sobre RAM y espacio del dispositivo:**
*In progress*

---



# 7. Issues

## NEXT STEPS:




 ### General:
- (Si da tiempo) automatizar sugerencias para mejorar los repositorios

### Opcional:
- Ver si merece la pena hacer un RO
- Realizar un nuevo estudio de consumo de memoria + espacio en disco
- documentar manual de uso de usuario de dashverse
---



# 8. Support
Para cualquier problema escribir una issue en:
https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/issues


