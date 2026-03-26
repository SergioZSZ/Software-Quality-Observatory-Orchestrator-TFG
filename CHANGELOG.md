############################################

## **SOCA_CONTAINER**

- Eliminada cola `events`, conexión y declaración asociada, así como todo el sistema de publicación de eventos de SOCA  
- Eliminado file locker y archivos de status  
- Añadida generación de `failed_repo.json` en caso de error durante el procesamiento  
- Añadido script `genportal.py` para la generación del portal mediante `execute command` en n8n  
- Sustitución de llamadas a APIs por ejecución directa mediante `docker execute command` (se ejecuta el main del contenedor en lugar de endpoints)  

---

## **RSFC_CONTAINER**

- Eliminada cola `events`, conexión y declaración asociada, así como todo el sistema de publicación de eventos de RSFC  
- Eliminada BBDD `rsfc_runner` (obsoleta, sustituida por logs en JSON generados por assessments o fallos por target)  
- Añadida generación de `failed_assessments.json` cuando un repositorio falla  
- Añadido truncamiento de directorios del target para evitar indicadores obsoletos  
- Aumentado número máximo de reintentos del worker RSFC a **5** debido a problemas de red  
- Incrementado a **7 retries** en escenarios de red inestable y cambio de estrategia de backoff de lineal a exponencial  
- Añadida nueva cola de eventos `rsfc_events` para integración con workflows externos  
- Añadida nueva función `publish_event(target: str)` para el envío de eventos a `rsfc_events` incluyendo el target y sus repositorios  
- Sustitución de llamadas a APIs por ejecución directa mediante `docker execute command`  

---

## **N8N**

- Fusionados los workflows previos en un único workflow `SQOO_workflow` estructurado en 3 fases:
    1. Fetch de SOCA + publicación de jobs y espera activa hasta la generación de metadatos por repositorio  
    2. Publicación de jobs RSFC y espera activa hasta la generación de assessments  
    3. Envío de assessments a DashVERSE  

---

## **ACTUALIZACIONES Y MEJORAS GENERALES**

- Actualizado **somef** a versión `0.10.0`:
    - `soca/setup.cfg`
    - `rsfc-main/pyproject.toml`

- Cambios en `rsfc-main/pyproject.toml`:
    - Python actualizado a `>= 3.11`  
    - `scikit-learn` actualizado a `>= 1.5.0`  
    - `pytest` actualizado a `>= 7.4.4`  
    - `imbalanced-learn` actualizado a `>= 0.11.0`  

- Generado nuevo `requirements.txt`  

- Modificado `github harvester` (línea 211):
    - Incrementado timeout a **60 segundos**  

- Creación de imágenes Docker optimizadas:
    - `soca-heavy`
    - `rsfc-heavy`  
    → Mejora significativa en tiempos de ejecución en `docker-compose`  

- Modificado `.gitattributes`:
    - Forzado uso de `LF` en archivos `.sh`  

- Generado workflow específico de DashVERSE en n8n  

---

############################################