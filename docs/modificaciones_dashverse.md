#### Cambios aplicados sobre DashVERSE 0.2.0

Durante la instalación de DashVERSE 0.2.0 en el entorno local se realizaron dos pequeñas modificaciones para que el despliegue y la sincronización funcionasen correctamente en Windows/Git Bash.

##### 1. Corrección en `terraform/main.tf`

En el fichero:

```text
terraform/main.tf
```

se modificó la línea del módulo `demo_portal`:

```hcl
superset_url = "http://${module.superset.service_name}:${module.superset.port}"
```

por:

```hcl
superset_url = module.superset.url
```

El motivo es que el módulo `superset` no expone el atributo `service_name`, por lo que OpenTofu fallaba durante el despliegue con un error de atributo no soportado. Al usar `module.superset.url`, se utiliza directamente la URL interna expuesta por el módulo de Superset, permitiendo completar correctamente el deployment.

##### 2. Corrección en `scripts/sync-everse.sh`

Durante la ejecución de:

```bash
make sync-apply
```

en Windows con Git Bash, el script fallaba al descargar dimensiones e indicadores de EVERSE con el siguiente error:

```text
curl: (3) URL rejected: Malformed input to a URL function
```

Las URLs funcionaban correctamente al probarlas manualmente con `curl`, por lo que el problema estaba causado por caracteres ocultos de retorno de carro (`\r`) en los nombres de fichero obtenidos desde `jq`.

Para solucionarlo, se modificaron las variables `DIMS` e `INDS` eliminando dichos caracteres:

```bash
DIMS=$(curl -sf "$GITHUB_API/dimensions" | jq -r '.[].name | select(endswith(".json"))' | tr -d '\r')
INDS=$(curl -sf "$GITHUB_API/indicators" | jq -r '.[].name | select(endswith(".json"))' | tr -d '\r')
```

Tras este cambio, `make sync-apply SYNC_DIR=./everse-sync` descarga correctamente las dimensiones e indicadores y los importa en DashVERSE.

## Publicación de assessments desde n8n

Los assessments originales pueden no incluir `@id` ni `author`. `dashverse_workflow.json` completa ambos campos antes de llamar a la API:

- `author` se obtiene del propietario presente en la URL de GitHub.
- `@id` se genera con la URL del repositorio, el origen (`rsfc` o `resqui`) y `dateCreated`.

El workflow publica:

- RSFC en `/assessment_raw`, envolviendo el JSON-LD en `payload`.
- RESQUI en `/assessment`, usando el esquema validado por DashVERSE.

La autenticación se configura una sola vez mediante `DASHVERSE_JWT` en `containers/.env`. Los nodos HTTP forman la cabecera `Authorization: Bearer ...` a partir de esa variable.
