# Desarrollo e integraciones

## SOCA

La imagen `soca-heavy` incorpora SOCA 0.0.4 y SOMEF 0.11.0. `soca_runner.main` recibe un proyecto, organizaciones o usuarios de GitHub y repositorios adicionales.

El runner mantiene `repository-state.json` y separa el inventario en repositorios actualizados y eliminados. Solo publica trabajos para los actualizados; los workers extraen los metadatos en staging y promueven el resultado de forma atómica. Un fallo conserva el resultado anterior y queda reflejado en `status.json`.

Los workers se escalan con:

```bash
docker compose up -d --scale worker_soca=N
```

Al final, `soca_runner.genportal` combina los metadatos con los resultados de calidad. Nginx publica los portales en `http://localhost:8030/portals/<project>/`.

## RSFC

La imagen `rsfc-heavy` utiliza RSFC 0.1.7 y reutiliza los metadatos SOCA cuando están disponibles. El launcher publica los repositorios actualizados en `rsfc_jobs` y elimina las salidas de los repositorios retirados.

Cada worker:

1. Espera un token del rate limiter cuando está activado.
2. Ejecuta RSFC en staging.
3. Valida `rsfc_output/rsfc_assessment.json`.
4. Promueve el resultado o genera `failed_assessment.json` sin borrar el anterior.
5. Actualiza `status.json` bajo bloqueo.

Los resultados se guardan en `outputs/rsfc/<project>/<owner>_<repo>/`.

## RESQUI

`resqui-heavy` incorpora QualityPipelines como submódulo y forma parte del workflow modular. Sus workers consumen `resqui_jobs`, ejecutan la configuración seleccionada y guardan `resqui_summary.json` en `outputs/resqui/<project>/<owner>_<repo>/`.

El volumen `sqoo_resqui_work` permite que el worker y los contenedores de plugins compartan el workspace. `RESQUI_SHARED_WORKDIR` y `RESQUI_DOCKER_WORK_VOLUME` configuran este comportamiento.

RESQUI utiliza el mismo patrón de staging, estado y eliminación de resultados retirados que RSFC. La configuración se encuentra en `containers/resqui_container/resqui_runner/configurations/`.

## sw-metadata-bot

Las imágenes `sw-metadata-bot:latest` y `sw-metadata-bot-conf:latest` contienen sw-metadata-bot 0.5.3 y los recursos NLTK/SOMEF necesarios.

n8n genera un `config.json` con el inventario completo. El bot localiza la snapshot anterior, compara commits y copia los artefactos de repositorios sin cambios. Los informes se guardan en `outputs/sw-metadata-bot/<project>/runs/<snapshot>/`.

`launch_issue` separa el análisis de la publicación: si es `false`, no se llama a `sw-metadata-bot publish`.

## DashVERSE y portal

`dashverse_workflow.json` lee los assessments de RSFC y RESQUI, completa `@id` y `author`, y publica en la API de DashVERSE usando `DASHVERSE_JWT`.

El portal incorpora:

- metadatos SOCA;
- indicadores RSFC;
- informes e issues de sw-metadata-bot;
- accesos a los dashboards SQOO-org y SQOO-repo.

Los identificadores de dashboards y el dominio de Superset se configuran con `DASHBOARD_ORG_EMBED_ID`, `DASHBOARD_REPO_EMBED_ID` y `SUPERSET_PUBLIC_DOMAIN`.
