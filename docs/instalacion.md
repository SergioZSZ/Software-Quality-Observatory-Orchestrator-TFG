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
-  El token (classic) se debe obtener desde GitHub y seleccionando el sope 'public_repo'. si no saltará error el uso de ese token. Se puede dejar vacía pero sólo se podrán realizar 50 peticiones por hora a GitHubAPI (no recomendable, muchos repos = error) y no se podrán subir las Issues automáticamente.

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

   Desde Windows se puede acceder en el navegador a `http://localhost:8088`, `http://localhost:8080`, `http://localhost:3000` y `http://localhost:8000` mientras ese terminal siga abierto.

8. Obtener credenciales de acceso a Superset
      desde terminal linux, ejecutar desde este mismo directorio
      `bash ./scripts/show-access.sh` pudiendo obtener así todas las credenciales necesarias


9. Conectarse a superset en http://localhost:8088
      login con user: admin   pwd: la obtenida desde el script anterior

10. generar conexión a la BBDD y dashboards base de DashVERSE:
      mandato: ``make setup-dashboards``

11. Se necesita un token jwt para las peticiones desde n8n. Para ello con el servicio desplegado ir a http://localhost:8000 y hacerse una cuenta EVERSE. Después hacer login y generar un token auth. Expiran tras un mes. Este token debe ponerse en los nodos que hacen peticiones http a dashVERSE del flujo n8n en el campo Authorization dentro de Headers como `Bearer TU_TOKEN`.

12. Importar los dashboards encontrados en `/integrations/dashboards` si se quieren mantener tambien los dashboards SQOO antiguos.

   
#### 5.4 Encendido y apagado del servicio DashVERSE:

##### apagar todo:
1. ``Cntrl+C`` para cerrar el port-forwarding desde el terminal abierto
2. ``minikube stop `` apaga el cluster

##### encenderlo:
1. encendemos cluster: ``minikube start`` 
2. lo reiniciamos ``kubectl delete pods --all -n dashverse``
3. forwarding de puertos desde ``~/projects/SQOO_TFG/integrations/DashVERSE-0.2.0`` en un terminal WSL: `make port-forward`
