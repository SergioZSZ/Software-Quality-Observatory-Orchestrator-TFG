# Instalación y despliegue

## Orquestador

### 1. Clonar el repositorio

```bash
git clone --recurse-submodules https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG.git
cd Software-Quality-Observatory-Orchestrator-TFG
```

En una copia existente:

```bash
git submodule update --init --recursive
```

### 2. Configurar el entorno

Copiar `containers/.env.example` como `containers/.env` y completar:

- `GITHUB_API_TOKEN`: token de GitHub para consultas y publicación de issues.
- `RABBITMQ_USER` y `RABBITMQ_PASSWORD`.
- `RATE_LIMIT_RSFC_ENABLED` y `RATE_LIMIT_RESQUI_ENABLED`.
- `OUTPUTS`: ruta absoluta de `containers/outputs`.
- `PORTAL_PORT`: puerto de Nginx, `8030` por defecto.
- `DASHBOARD_ORG_EMBED_ID` y `DASHBOARD_REPO_EMBED_ID`.
- `SUPERSET_PUBLIC_DOMAIN`: `http://localhost:8088` en local.
- `DASHVERSE_JWT`: token generado por la API de DashVERSE.

No se deben guardar tokens reales en Git.

### 3. Construir las imágenes

Se pueden usar `scripts/build-docker-images.sh` en WSL/Linux o `scripts/build-docker-images.ps1` en PowerShell. Los mandatos equivalentes desde la raíz son:

```bash
docker build -t soca-heavy:latest containers/soca_container
docker build -t rsfc-heavy:latest containers/rsfc_container
docker build -t resqui-heavy:latest containers/resqui_container
docker build -t sw-metadata-bot:latest integrations/sw-metadata-bot-0.5.3
docker build -t sw-metadata-bot-conf:latest containers/sw-metadata-bot_container
```

La imagen `sw-metadata-bot-conf` debe construirse después de `sw-metadata-bot`, ya que hereda de ella.

### 4. Levantar los servicios

```bash
cd containers
docker compose up -d --build \
  --scale worker_soca=4 \
  --scale worker_rsfc=4 \
  --scale worker_resqui=4
```

Los workers pueden escalarse según los recursos disponibles. Los logs se consultan con:

```bash
docker compose logs -f worker_soca worker_rsfc worker_resqui
```

### 5. Importar el workflow

Acceder a `http://localhost:5678` e importar:

- `SQOO_modular_workflow.json`
- `soca_workflow.json`
- `rsfc_workflow.json`
- `resqui_workflow.json`
- `sw-metadata-bot_workfow.json`
- `dashverse_workflow.json`

Revisar los nodos `Call '<subworkflow>'` para que apunten a los workflows importados.

En el nodo `Conf` configurar:

```json
{
  "project": "mi-proyecto",
  "organizations": [
    {"org": "mi-organizacion", "type": "org"}
  ],
  "extra_repositories": [],
  "launch_issue": false
}
```

El portal quedará disponible en `http://localhost:8030/portals/<project>/`.

## DashVERSE 0.2.0

En Windows, el despliegue se realiza desde Ubuntu en WSL con Docker Desktop y su integración WSL activada. Se recomienda trabajar en el sistema de archivos Linux, no bajo `/mnt/c`.

### Requisitos

- Docker
- Make
- OpenTofu
- Minikube
- Helm
- kubectl
- Ansible

### Despliegue

```bash
cd integrations/DashVERSE-0.2.0
minikube config set driver docker
minikube start --cpus=4 --memory=4096 --driver=docker
helm repo add Superset https://apache.github.io/superset --force-update
helm repo update
make deploy
make sync-apply
make status
make port-forward
```

Mientras `make port-forward` esté activo se exponen:

- Superset: `http://localhost:8088`
- Demo portal: `http://localhost:8080`
- API de assessments: `http://localhost:3000`
- API de autenticación: `http://localhost:8000`

Las credenciales se consultan con:

```bash
bash ./scripts/show-access.sh
```

Los dashboards base se configuran con `make setup-dashboards`. Las plantillas SQOO se importan desde `integrations/dashboards/` y deben publicarse con permisos para el rol utilizado, por ejemplo `Public`.

Para obtener `DASHVERSE_JWT`, crear una cuenta e iniciar sesión en `http://localhost:8000`. El token se guarda en `containers/.env`; no se copia manualmente en los nodos de n8n.

### Parada y arranque posterior

```bash
# Parar
minikube stop

# Volver a iniciar
minikube start
make port-forward
```
