# General
- Actualizado el workflow modular para procesar solo repositorios nuevos o modificados, retirar los eliminados y conservar el inventario completo
- Integrado RESQUI en el pipeline modular y reforzada la persistencia de resultados de SOCA, RSFC y RESQUI ante fallos
- Añadidos scripts de generación de imágenes docker necesarias para el software: `/scripts/build-docker-images.ps1` (powershell) y `/scripts/build-docker-images.sh` WSL/Linux
- Añadida nueva variable entorno ``DASHVERSE_JWT`` para meter el token para el acceso a dashverse de n8n

# SW-METADATA-BOT
- arreglado problema de configuración de github token en sw-metadata-bot
- añadida configuración para elegir si lanzar issues o no
- Actualizado bot a la versión 0.5.3

# NGINX
- añadido contenedor nginx de despliegue de los portales soca generados

# SOCA
- Mejorada visualización de metadatos de portal software generado por soca
- Actualizado somef dentro de soca a 0.11.0
- Añadido filtrado por software por defecto (que no se vean ni ontologías ni webs)
- Añadido botón `quality` en los cards, incluyendo el report de rsfc y pitfalls/warnings de sw-metadata-bot + link a la Issue generada por él

# RSFC
- Actualizado RSFC a la versión 0.1.7.
- Reutilizados los metadatos de SOCA y adaptada la integración a SOMEF 0.11.0.
- Corregidas las comprobaciones de versiones y del gestor de issues

# RESQUI
- Actualizado al commit https://github.com/EVERSE-ResearchSoftware/QualityPipelines/commit/141eaf25c366bf3a59115846c483bf63da6c7e31

# DashVERSE
- Añadida la publicación de assessments de RSFC y RESQUI desde el workflow modular
- Actualizado dashboard SQOO-ORG con chart TOP 5 softwares
- Configurado Superset/DashVERSE para permitir dashboards embebidos mediante `iframe` de superset y uso del rol `Public` para usuarios invitados
- Publicados los dashboards y añadidos los roles  `Public` en la configuración de acceso para permitir visualización
- Habilitada la visualización embebida del dashboard SQOO-ORG restringida al dominio autorizado (http://localhost:8030 en caso local, caso desplegable poner dominio desde donde se visualizará)


