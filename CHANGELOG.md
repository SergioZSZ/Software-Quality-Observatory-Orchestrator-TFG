- quitados apis por execute commands de docker (en vez de endpoints se ejecuta el main de cada container)
- modificado workflows a 2, uno para rsfc y otro para soca
- modificdo github harvester linea 211 subido timeout a 60
- aumentado max retries a 5 de worker rsfc por problemas de red

- creado imagenes de soca y rsfc heavy, para que docker compose vaya mas rapido (modificando docker y docker compose con ellas)
- modificado .githubatributes para que los .sh sean siempre `lf`
- añadida nueva cola de eventos rsfc_events para trigger de workflow dashverse
- añadido nueva función `publish_event(target: str)` en rsfc para el envío de event a rsfc_events
con el target y sus repositorios
- subido a 7 retries los problemas de red y cambiado backoff lineal a exponencial
- generado workflow dashverse en n8n



############################################

- Modificado soca_container:
    1. Eliminada cola events, conexión y declaración a ella y todo lo relacionado con publish event soca
    2. eliminado file locker y archivos de status
    3. añadida generacion de failed_repo.json si hay error al procesar 
    4. añadido script genportal.py para generación del portal mediante execute command en n8n

- Modificado rsfc_container:
    1. Eliminada cola events, conexión y declaración a ella y todo lo relacionado con publish event rsfc
    2. Eliminada BBDD rsfc_runner, obsoleta (logs orquestados por jsons de assessments o failed en el target)
    3. Añadida funcion de que si un repositorio falla, genere un failed_assessments.json en el directorio donde debería ir el rsfc_assessments.json
    4. Añadido truncamiento de directorios del target en rsfc_container para eliminar indicadores obsoletos

- Modificado n8n:
    - Fusionado todos los workflows anteriores en SQOO_workflow con 3 fases:
        1. Fetch de soca + publish jobs soca && wait hasta generación de metadatos de cada repo
        2. publish jobs rsfc && wait a que terminen de procesar los assessments
        3. envío de assessments a DashVERSE


- Actualizado somef, modificando los siguientes ficheros para ello:
    - soca:
        - setup.cfg -> somef=0.10.0

    - rsfc-main:
        - pyproject.toml:
            - somef = 0.10.0
            - python subido >=3.11
            - scikit-learn ahora >= 1.5.0
            - pytest ahora >= 7.4.4
            - imbalanced-learn >= 0.11.0
        
        - generado nuevo requirements.txt