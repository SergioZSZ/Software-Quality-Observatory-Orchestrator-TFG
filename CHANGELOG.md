 **Modificaciones soca:**
   - en template.html de generacion de portal cambiado linea 19
    		<div data-toggle="tooltip" data-placement="right" title="SOCA Dashboard Analytics"><a href="https://dashboards-software.oeg.fi.upm.es/d/FX3TNka4k/prototype?orgId=1&from=now-6M&to=now&var-organisation=oeg-upm&var-SOCA_Version=0.0.3&var-SOMEF_Version=0.9.3&kiosk" target="_blank"><img src="img/statIcon.svg" class="grey-color-svg" style="height: 2rem; margin-left: 1rem;"></a></div>

      el cambio se efectúa en el nodo <a> cambiado a:
           <a id="dashverse-link" href="#" target="_blank">

    para encontrar el id desde python y pondiendo href como valor provisional # para modificarlo en python

   - añadido en generacion de portal soca funcion add dashverse link, y añadida en la generacion del script portal.py de soca

   - Mejorada la visualización de metadatos del portal, pasando de mostrar datos en bruto a una representación más estructurada y navegable:


         - README: 
            - antes: Se visualizaba el rawgithub readme

            - ahora: el enlace ahora apunta a la vista de GitHub (blob) en lugar del raw, permitiendo una mejor navegación del repositorio.

         - Docker: 
            - antes: link al rawgithub del archivo docker

            - ahora: mejorada la detección de archivos Dockerfile y docker-compose, y archivos de generación de entornos (agrupados y con semántica referente a donde se encuentran) y al clickar te lleva al archivo en github 


         - Citation: 
            - antes: se enseñaba directamente la citación encontrada (bibtex, citation.cff o texto)

            - ahora: reemplazada la visualización del contenido RAW del bibtex o citation.cff y lo visualiza estructuradamente (o texto) + generación de bibtex en caso de citation.cff (aparece el source de cada parte)

         - Requirements:
            - antes: se enseñaba una mezcla entre requirements.txt, .tomls y el readme sin markdown
            - ahora: archivos de requisitos tienen link para ir a verlos y el readme se ve con markdown (aparece el source de cada)

         - Instalation: ahora se ve en markdown y aparece el source

   - cambiado el nombre de soca/assets/img/statIcon.svg a statIcon-org.svg para diferenciarlo del siguiente emoticono

   - añadido a soca/assets/img una imagen statIcon-user.svg para tener un emoticono que lleve al dashboard de usuarios 

   - añadida nueva linea en el template.html para añadir emoticono statIcon-user.svg
linea 20:         
      <div data-toggle="tooltip" data-placement="right" title="SOCA Dashboard Analytics (user)"><a id="dashverse-user-link" href="#" target="_blank"><img src="img/statIcon-user.svg" class="grey-color-svg" style="height: 2rem; margin-left: 1rem;"></a></div>

   - modificada funcion propia add_dashverse_link en soca/commands/portal.py para añadir el link al dashboard de usuarios

   - añadido al servicio soca del docker compose estas variables entorno para coger las url del entorno:
            - DASHBOARD_ORG_URL=${DASHBOARD_ORG_URL}
            - DASHBOARD_REPO_URL=${DASHBOARD_REPO_URL}
   

**Modificaciones DashVERSE:**
   - Actualizado DashVERSE a su versión 2.0


**Modificaciones n8n:**
   - Actualizado workflow:
      1. Modificado workflow para compatibilidad con 2 modos de ejecución del orquestador:
         - `auto`:   Obtención de indicadores y metadatos de una organización o usuario de GitHub concreto
         - `manual`: Obtención de indicadores y metadatos de repositorios específicos de GitHub a partir de un documento `repos.txt` propio ubicado en `/containers/outputs`