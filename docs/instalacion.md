## 5. Instalación/Despliegue

#### 5.1 Previa (env)
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



#### 5.3 Instalación/Despliegue de DashVERSE
Todo lo relacionado con DashVESE se deberá hacer desde una terminal Unix, no powershell de windows (por ejemplo Git Bash https://git-scm.com/install/windows). este proceso inicial hacerlo dentro del directorio `/DashVERSE`

1. instalar minikube,  kubectl, y helm (docker instalado de antes)
      mandato: `pip install minikube kubectl helm`

2. cambiar driver de minikube a docker
      mandato:``minikube config set driver docker``

3. arrancar cluster de minikube
      mandato: ``minikube start --cpus=4 --memory=4g --driver=docker``

      para comprobar que  kubernetes responde usar este mandato:
      ``kubectl get nodes`` y si funciona y se crea el nodo todo ok

4. desplegar y montar el servicio con el archivo make del directorio `/DashVERSE`
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

11. Importar los dashboards encontrados en `/dashboards`



#### 5.4 Encendido y apagado del servicio DashVERSE:

##### apagar todo:
1. ``Cntrl+C`` para cerrar el port-forwarding desde el terminal abierto
2. ``minikube stop `` apaga el cluster

##### encenderlo:
1. encendemos cluster: ``minikube start`` 
2. lo reiniciamos ``kubectl delete pods --all -n dashverse``
3. desde ``/DashVERSE-2.0`` en un terminal linux(GitBash por ejemplo): `make port-forward`


