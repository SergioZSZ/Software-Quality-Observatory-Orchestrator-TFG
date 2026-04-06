 **Modificaciones soca:**
   - en template.html de generacion de portal cambiado linea 19
    		<div data-toggle="tooltip" data-placement="right" title="SOCA Dashboard Analytics"><a href="https://dashboards-software.oeg.fi.upm.es/d/FX3TNka4k/prototype?orgId=1&from=now-6M&to=now&var-organisation=oeg-upm&var-SOCA_Version=0.0.3&var-SOMEF_Version=0.9.3&kiosk" target="_blank"><img src="img/statIcon.svg" class="grey-color-svg" style="height: 2rem; margin-left: 1rem;"></a></div>

      el cambio se efectúa en el nodo <a> cambiado a:
           <a id="dashverse-link" href="#" target="_blank">

    para encontrar el id desde python y pondiendo href como valor provisional # para modificarlo en python

   - añadido en generacion de portal soca funcion add dashverse link, y añadida en la generacion

   - Mejorada la visualización de metadatos del portal, pasando de mostrar datos en bruto a una representación más estructurada y navegable.

**NOTA:** Todos los links del portal referentes al repo apuntana a ramas main o master

   - README: 
      - antes: Se visualizaba el rawgithub readme

      - ahora: el enlace ahora apunta a la vista de GitHub (blob) en lugar del raw, permitiendo una mejor navegación del repositorio.

   - Docker: 
      - antes: link al rawgithub del archivo docker

      - ahora: mejorada la detección de archivos Dockerfile y docker-compose, incluyendo aquellos en subdirectorios. Se generan enlaces correctos a GitHub y se filtran archivos no relacionados, representando mejor proyectos con múltiples configuraciones (ya no aparecen archivos de requisitos, solo relacionados con docker)

   - Requirements:
      - antes: cogía los archivos requirements y poetry y Requirements del README.md  los escribía directamente en el portal

      - ahora: en lugar de mostrar el contenido completo, ahora se listan únicamente los archivos relevantes (requirements.txt, pyproject.toml, etc.) con enlaces directos al repositorio, agrupados por tipo de entorno, reduciendo ruido visual, y sacando información de los README.md de requisitos si tienen (alomejor a medio implementar, toca probar)

   - Citation: 
      - antes: se enseñaba directamente el CITATION.cff

      - ahora: reemplazada la visualización del contenido RAW del CITATION.cff por una interpretación estructurada del mismo


**Modificaciones DashVERSE:**
   - Ahora la BBDD de DashVERSE actualiza los repositorios en vez de añadirlos otra vez en caso de repetición (añadidas constraints UNIQUE en tablas y ?on_conflict en n8n para postgrest)

**Modificaciones n8n:**
   - Modificadas peticiones http a postgrest para que envíe en batches los assessments y checks a postgrest evitando saturación de peticiones 