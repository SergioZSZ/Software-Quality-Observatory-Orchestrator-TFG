### 5. Instalación/Despliegue

#### 5.1 Previa
 Se debe crear un archivo `.env` en el directorio `/containers` que tenga las variables entorno: 
   - `GITHUB_TOKEN` siguiendo el formato `GITHUB_TOKEN=xxxxxx` siendo `xxxxxx` el token personal de github obtenido desde github

   - `RABBITMQ_USER` usuario de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`
   - `RABBITMQ_PASSWORD` contraseña de RabbitMQ puesto en el servicio `rabbitmq` del `/containers/docker-compose.yml`

   - ``RATE_LIMIT_SOCA_ENABLED`` y `RATE_LIMIT_RSFC_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI(con workers de soca no hace falta debido a que realiza 1 petición/repo, de rsfc si ya que realiza 7 aprox)

   - `OUTPUTS` la ruta de acceso al directorio a usar como volumen compartido (se debe llamar ``outputs`` y estar dentro del directorio `/containers`)

   - `DASHBOARD_ORG_URL` la URL al dashboard org desplegado, `http://localhost:8088/superset/dashboard/nº_de_dashboard/` en caso de seguir las indicaciones del README y lanzarlo en local

   - `DASHBOARD_REPO_URL` la URL al dashboard repo desplegado, `http://localhost:8088/superset/dashboard/nº_de_dashboard/` en caso de seguir las indicaciones del README y lanzarlo en local

    ejemplo en `/containers/.env.example`. Se pueden usar tal cual las variables del archivo menos `GITHUB_TOKEN` y `OUTPUTS` y `DASHBOARD_URL`. 
    
    El token se debe obtener desde GitHub y generarlo con la opción 'All repositories', si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error).

    El nº de dashboard es el que aparezca tras importar en DashVERSE la plantilla contenida en `/dashboard`


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



### 5.3 Instalación/Despliegue de DashVERSE

🚧🚧 *In_Progress (falta despliegue dashverse)* 🚧🚧


---
