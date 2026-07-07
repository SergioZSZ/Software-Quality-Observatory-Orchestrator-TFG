# Requisitos

## Orquestador

- Docker Engine o Docker Desktop con Compose v2.
- Python 3.11 o 3.12 para desarrollo local.
- Git con soporte de submódulos.
- Token de GitHub recomendado para evitar el rate limit y publicar issues.

En Windows, Docker Desktop debe tener activada la integración con WSL si se despliega DashVERSE.

## DashVERSE

DashVERSE se despliega desde Linux o Ubuntu en WSL. Requiere:

- Make
- OpenTofu
- Minikube
- Helm
- kubectl
- Ansible

`kubectl`, `make deploy`, `make sync-apply`, `make setup-dashboards` y `make port-forward` deben ejecutarse desde el mismo entorno para compartir el contexto de Kubernetes.

## Versiones integradas

| Herramienta | Versión |
| --- | --- |
| SOCA | 0.0.4 |
| RSFC | 0.1.7 |
| SOMEF | 0.11.0 |
| DashVERSE | 0.2.0 |
| sw-metadata-bot | 0.5.3 |
| RsMetaCheck | >=0.3.3 |

RESQUI utiliza el submódulo `QualityPipelines-2.0` fijado por el repositorio.
