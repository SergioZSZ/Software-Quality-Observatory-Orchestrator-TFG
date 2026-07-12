# Workflow modular

El sistema utiliza `SQOO_modular_workflow.json` como único workflow principal de n8n. Orquesta los siguientes subworkflows:

- `soca_workflow.json`
- `rsfc_workflow.json`
- `resqui_workflow.json`
- `sw-metadata-bot_workfow.json`
- `dashverse_workflow.json`

## Configuración de entrada

El nodo `Conf` define:

- `project`: nombre estable usado en directorios y estado incremental.
- `organizations`: lista de objetos `{"org": "nombre", "type": "org|user"}`.
- `extra_repositories`: URLs adicionales a las descubiertas en GitHub.
- `launch_issue`: activa la publicación de issues de sw-metadata-bot.

## 1. Descubrimiento incremental y SOCA

`soca_workflow.json` ejecuta `soca_runner.main`, consulta GitHub y compara cada `updated_at` con `outputs/soca/<project>/repository-state.json`.

Genera:

- `repos.txt`: inventario completo.
- `repos-updated.txt`: repositorios nuevos o modificados.
- `repos-removed.txt`: repositorios retirados.
- `repository-state.pending.json`: estado pendiente de consolidar.

Los workers procesan solo `repos-updated.txt`. Cada extracción se genera en staging y sustituye de forma atómica el resultado anterior; si falla, se conserva el último resultado válido y se registra el error. `status.json` diferencia repositorios correctos y fallidos.

El workflow principal evalúa `has_changes`. Si es `true`, continúa con RSFC; si es `false`, no repite las evaluaciones y consolida directamente el estado pendiente.

## 2. RSFC y RESQUI

Los subworkflows reciben `repos_url` y `repos_removed`:

- RSFC 0.1.7 evalúa los repositorios actualizados, reutiliza metadatos SOCA cuando existen y escribe en `outputs/rsfc/<project>/<owner>_<repo>/`.
- RESQUI evalúa el mismo lote con QualityPipelines y escribe en `outputs/resqui/<project>/<owner>_<repo>/`.
- Ambos eliminan las salidas persistidas de los repositorios retirados y conservan un resultado anterior si una nueva evaluación falla.
- Los subworkflows esperan a que todos los repositorios se procesen. Cuando termina el lote, `status.json` queda en `completed` aunque haya repositorios fallidos; esos fallos se conservan en `failed_repos` y no detienen el pipeline.

## 3. sw-metadata-bot

sw-metadata-bot 0.5.3 recibe el inventario completo, no solo el lote actualizado. Esto permite que cada snapshot mantenga todos los repositorios.

El bot:

1. Genera `config.json`.
2. Ejecuta `sw-metadata-bot run-analysis` con una snapshot fechada.
3. Localiza automáticamente el `run_report.json` anterior.
4. Reutiliza los artefactos cuyo commit no ha cambiado.
5. Ejecuta `sw-metadata-bot publish` solo cuando `launch_issue` es `true`.

Las snapshots se guardan en `outputs/sw-metadata-bot/<project>/runs/<snapshot>/`.

## 4. Portal

Cuando terminan las evaluaciones, `soca_runner.genportal` combina metadatos SOCA, assessments RSFC e informes de sw-metadata-bot. El portal se guarda en `outputs/soca/<project>/portal/` y Nginx lo sirve en:

```text
http://localhost:8030/portals/<project>/
```

## 5. DashVERSE

`dashverse_workflow.json` enriquece los assessments con `@id` y `author` antes de publicarlos:

- RSFC: `POST /assessment_raw` con `{ "payload": assessment }`.
- RESQUI: `POST /assessment` con el assessment validado.

Las peticiones utilizan `Authorization: Bearer <DASHVERSE_JWT>`.

Tras generar el portal, `If repo updated` comprueba `repo_count`. DashVERSE solo se ejecuta cuando existen repositorios actualizados; los lotes que contienen únicamente eliminaciones pasan directamente a la consolidación.

## 6. Consolidación del estado

Al terminar DashVERSE, o directamente cuando no hay assessments nuevos, n8n sustituye `repository-state.json` por `repository-state.pending.json`. Así, una ejecución fallida no marca como procesados cambios incompletos y una ejecución con solo eliminaciones actualiza correctamente el inventario.
