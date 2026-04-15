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
Todo este proceso se deberá hacer desde una terminal Unix, no powershell de windows (por ejemplo Git Bash https://git-scm.com/install/windows), este proceso inicial hacerlo dentro del directorio `/DashVERSE`

1. instalar minikube,  kubectl, y helm (docker instalado de antes)
      mandato: `pip install minikube kubectl helm`

2. cambiar driver de minikube a docker
      mandato:``minikube config set driver docker``

3. arrancar cluster de minikube
    mandato: ``minikube start --cpus=4 --memory=4g --driver=docker``

   para comprobar que  kubernetes responde usar este mandato:
   ``kubectl get nodes`` y si funciona y se crea el nodo todo ok

4. a partir de ahora se necesitará estar desde el terminal en el directorio `/DashVERSE/kubernetes` para el resto de pasos. 

5. generar los secretos 
   mandato: ``bash generate-variables.sh``
   se generará el directorio `/DashVERSE/kubernetes/deployments` y dentro de este una carpeta con un nombre aleatorio (por ejemplo `eX5SDk6watlUx__17_03_2026__18_24`), entre sus archivos estará  ``secrets.env`` con las variables entorno autogeneradas

6. cargamos variables entorno desde el directorio generado (directorio ejemplo:`/DashVERSE/kubernetes/deployments/eX5SDk6watlUx__17_03_2026__18_24`)
   mandato ejemplo desde directorio `/DashVERSE/kubernetes`: ``source deployments/eX5SDk6watlUx__17_03_2026__18_24/secrets.env``

7. construimos la imagen init de BD Desde desde kubernetes
   mandato: ``docker build --no-cache -t ghcr.io/everse-researchsoftware/postgresql-setup-script:latest -t everse-db-scripts:latest ./DBModel``

   obteniendo así la imagen docker de init_db  **everse-db-scripts:latest**

8. la cargamos en minikube
   mandato:`` minikube image load everse-db-scripts:latest``
    (comprobar que se carga con ``minikube image ls``, si se encuentra se cargó bien)

9. creamos un namespace
   mandato: ``kubectl create namespace superset``

10. aplicamos los secretos (variables entornos configuradas antes) desde directorio kubernetes
   mandato: ``kubectl apply -f $DASHVERSE_SECRETS_FILE_NAME --namespace superset``

11. desplegamos bbdd
   mandato: ``envsubst < deploy-db.yaml | kubectl apply --namespace superset -f -``
   
   y revisamos que la BD de init job arranca bien
   mandato para listar pods: ``kubectl get pods --namespace superset``, si aparece la bbdd postgres está correcto

   logs de init se pueden ver ejecutando esta secuencia de mandatos:
   ``DB_JOB_POD_NAME=$(kubectl get pods --namespace superset | grep "postgresql-init-job" | cut -d" " -f1)``
   ``kubectl logs --namespace superset $DB_JOB_POD_NAME -c init-python-container``

12. ya con la bbdd inicializada, desplegamos postgrest (servicio para integrar datos en la base de datos de DashVERSE mediante peticiones http)
   mandato: ``envsubst < deploy-postgrest.yaml | kubectl apply --namespace superset -f -``

   recordatorio, se puede visualizar si se inician los pods con `kubectl get pods --namespace superset` y los logs de cada pod con:
   logs: ``kubectl logs --namespace superset <nombre-del-pod-postgrest> --all-containers``
   ejemplo: ``kubectl logs --namespace superset postgrest-665f67f757-v86l9 --all-containers``

13. instalamos superset con helm 
    1. añadimos repo superset: ``helm repo add superset https://apache.github.io/superset``
    2. actualizamos: ``helm repo update``

14. desplegamos superset (con el código de DashVERSE de este repositorio, debido a modificaicones propias para su funcionamiento)
   1. cargamos el yaml: ``envsubst < dashverse-values.yaml > dashverse-values-with-secrets.yaml``

   2. lo usamos y upgrade del superset: ``helm upgrade --install superset superset/superset --values dashverse-values-with-secrets.yaml --namespace superset --create-namespace --debug --cleanup-on-fail``

   3. eliminamos el yaml generado con secretos ``rm -f dashverse-values-with-secrets.yaml ``
   4. esperamos a que estén levantados todos los servicios mirando en `kubectl get pods -n superset`


15. Una vez funcional, conectamos un tunel del cluster con nuestra máquina local para que se conecte a los puertos, para ello se deben ejecutar una única vez estos mandatos (ESTO PARA EXPONER EN LOCAL):

cambio a loadbalancer de postgrest para acceso desde local:
``kubectl patch svc postgrest -n superset -p '{"spec": {"type": "LoadBalancer"}}'``   

cambio a loadbalancer de postgrest para acceso desde local:
``kubectl patch svc superset -n superset -p '{"spec": {"type": "LoadBalancer"}}'  `` 
    
para conectar el tunel y que ya funcionen los puertos en local, se debe tener un terminal abierto con este mandato: `minikube tunnel`, para cerrar el tunel ``Cntrl + C``


16. Una vez todo funcional, debemos modificar la BBDD de esta manera:
   1. acceder al pod de postgres (siendo postgres-pod el nombre del pod postgres, ejemplo: superset-postgresql-5ddb4d7bff-wq9c5): 
   `kubectl exec -it superset-postgresql-5ddb4d7bff-wq9c5 -n superset -- bash psql -U postgres -d superset`

   2. ejecutar estos mandatos: 
ALTER TABLE everse.assessments
ADD CONSTRAINT unique_assessments_id UNIQUE (id);

ALTER TABLE everse.assessments
ADD CONSTRAINT unique_assessments_name UNIQUE (name);

ALTER TABLE everse.assessment_software
ADD CONSTRAINT unique_assessment_software_assessment_id UNIQUE (assessment_id);

ALTER TABLE everse.assessment_checks
ADD CONSTRAINT unique_assessment_checks_assessment_test UNIQUE (assessment_id, test_id);

17. Reiniciamos el namespace con `kubectl delete pods --all -n superset` y esperamos a que estén levantado de nuevo los servicios.

18. Una vez levantados, realizar el mandato `minikube tunnel` en una terminal para acceder a los puertos locales y entrar en `http://localhost:8088`

19. ahí nos pedirá el nombre de usuario y contraseña, el nombre y contraseña generados en estas variables entorno del archivo `/DashVERSE/kubernetes/deployments/eX5SDk6watlUx__17_03_2026__18_24/secrets.env` (la carpeta intermedia entre deployments y el archivo tendrá un nombre distinto):
   - SUPERSET_ADMIN_USER='nombre'
   - SUPERSET_ADMIN_PASSWORD='contraseña'

20. configurar en database conections la url a la bbdd
    postgresql://superset:<secrets.env SUPERSET_DB_PASSWORD>@superset-postgresql:5432/superset

21. dar permisos para acceder a postgrest del cluster desde n8n:
    1. vemos el nombre de nuestro pod postgres con kubectl get pods -n superset (superset-postgresql-5ddb4d7bff-5j4bf por ejemplo)
    2. entramos en bash
        kubectl exec -it superset-postgresql-5ddb4d7bff-k6544  -n superset -- bash
    3. entramos a la bbdd: psql -U postgres -d superset
    
    4. dar permisos a schema everse a web_anon y permisos de tablas
    -- acceso al schema
    GRANT USAGE ON SCHEMA everse TO web_anon;

    -- acceso a tablas
    GRANT SELECT, INSERT, UPDATE, DELETE 
    ON ALL TABLES IN SCHEMA everse 
    TO web_anon;

    -- acceso a secuencias (IMPORTANTE para INSERT)
    GRANT USAGE, SELECT 
    ON ALL SEQUENCES IN SCHEMA everse 
    TO web_anon;
   
### 5.4 Encendido y apagado del servicio DashVERSE:

apagar todo:
   minikube stop               # apaga el cluster

encenderlo:
   minikube start  #encendemos cluster
   kubectl delete pods --all -n superset
   kubectl get pods -n superset # comprobar los pods activados



---
