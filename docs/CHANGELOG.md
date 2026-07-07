# General

- Actualizado el workflow modular para procesar solo repositorios nuevos o modificados, retirar los eliminados y conservar el inventario completo.
- Integrado RESQUI en el pipeline modular y reforzada la persistencia de resultados de SOCA, RSFC y RESQUI ante fallos.
- Añadidos scripts para construir las imágenes Docker desde Windows o WSL/Linux.
- Añadida la variable `DASHVERSE_JWT` para autenticar la publicación desde n8n.

# SOCA

- Actualizado SOMEF a la versión 0.11.0 y mejorado el portal software enriquecido.

# RSFC

- Actualizado RSFC a la versión 0.1.7.
- Reutilizados los metadatos de SOCA y corregidas las comprobaciones de versiones y del gestor de issues.

# RESQUI

- Actualizado QualityPipelines e integrado RESQUI en el workflow modular.

# sw-metadata-bot

- Actualizado a la versión 0.5.3, con análisis incremental y publicación de issues configurable.

# DashVERSE

- Añadida la publicación de assessments de RSFC y RESQUI y la visualización embebida de dashboards.
