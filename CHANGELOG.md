# General
- Documentados los nuevos workflows de n8n: versión no modular con publicación de issues elegible y versión modular de SQOO con subworkflows.
- Añadidos scripts de generación de imágenes docker necesarias para el software: `/scripts/build-docker-images.ps1` (powershell) y `/scripts/build-docker-images.sh` WSL/Linux

# sw-metadata-bot
- arreglado problema de configuración de github token en sw-metadata-bot

# nginx
- añadido contenedor nginx de despliegue de los portales soca generados

# Soca
- Mejorada visualización de metadatos de portal software generado por soca
- Actualizado somef dentro de soca a 0.10.3
- Añadido filtrado por software por defecto (que no se vean ni ontologías ni webs)
- Añadido botón `quality` en los cards, incluyendo el report de rsfc y pitfalls/warnings de sw-metadata-bot + link a la Issue generada por él.
- realizada pr a soca con nuevas incorporaciones

# RSFC
- Actualizado RSFC a su última versión 0.1.5
- En containers/rsfc_container/rsfc-0.1.5/pyproject.toml: relajado jsonschema de 4.24.0 a >=3,<5.

# DashVERSE
- Actualizado dashboard SQOO-ORG con chart TOP 5 softwares
- Configurado Superset/DashVERSE para permitir dashboards embebidos mediante `iframe` de superset y uso del rol `Public` para usuarios invitados
- Publicados los dashboards y añadidos los roles  `Public` en la configuración de acceso para permitir visualización
- Habilitada la visualización embebida del dashboard SQOO-ORG restringida al dominio autorizado (http://localhost:8030 en caso local, caso desplegable poner dominio desde donde se visualizará)


