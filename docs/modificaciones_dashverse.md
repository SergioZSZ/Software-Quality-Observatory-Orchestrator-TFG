## Cambio en el código
Trying to deploy DashVERSE 2.0 service in my own local machine I had this error:
bash
```
╷
│ Error: Unsupported attribute
│
│ on main.tf line 109, in module "demo_portal":
│ 109: superset_url = "http://${module.superset.service_name}:${module.superset.port}"
│ ├────────────────
│ │ module.superset is a object
│
│ This object does not have an attribute named "service_name".
╵
make: *** [deploy] Error 1
```


This was fixed by replacing: line 109 in main.tf 

 superset_url   = "http://$/{module.superset.service_name}:${module.superset.port}"
 
with

superset_url = module.superset.url

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