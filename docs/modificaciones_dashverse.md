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

## Datasets que se rellenan parcialmente


#### `api.assessment`

Se rellena parcialmente.

Comportamiento observado:
- `@context` y `@type` se muestran correctamente.
- `dateCreated` se muestra correctamente.
- `license` y `assessedSoftware` se muestran correctamente como objetos JSON.
- `@id` aparece como `N/A`.
- `author` aparece como `N/A`.

Motivo:
- la vista `api.assessment` extrae estos campos del `payload`:

```sql
payload->>'@id' AS "@id",
payload->'author' AS author,
```

- los assessments generados por RSFC no incluyen esos campos:
  - no incluyen `@id`,
  - no incluyen `author`.

Por tanto, no se trata de un fallo de la vista, sino de una diferencia entre el modelo esperado por DashVERSE y el JSON-LD generado por RSFC.

**YA SOLUCIONADO**
Solución:
- si se desea que esos campos aparezcan, habría que enriquecer el JSON-LD antes de insertarlo
  - se guardo en "author" el user/org de github encontrado en la url
  - en id se guardó el @id del "dataCreated" ya que es único por assessment