# General
- Ahora los failed_repos de anteriores iteraciones del workflow se intentan procesan en la siguiente para soca, rsfc y resqui
- Aumentados los MB de descarga de somef a 2000MB para soca y sw-metadata-bot
- Actualizados scripts de creación de imágenes docker y de instalación de herramientas para DashVERSE
- Añadida nueva variable entorno `RESQUI_CONF` para seleccionar la configuración querida para los worker_resqui
- Cambio de configuración para generar el portal linkeddata usando un YAML propio con URLs de repositorios, ejemplo:
```json
{
  "project": "sergio-soca-incremental",
  "organizations": [
    {
      "org": "SergioZSZ",
      "type": "user"
    }
  ],
  "extra_repositories": ["https://github.com/oeg-upm/soca"],
  "launch_issue": false,
  "linkeddata_tools": "/app/outputs/linkeddata_tools.yml"
}
```
- `linkeddata_tools` apunta al YAML propio que sustituye las herramientas del YAML base de LinkedData.
- Las tools nuevas se declaran solo como URLs de GitHub en ese YAML; los campos de la card se rellenan desde metadatos SOCA/SOMEF.
- Si no existen metadatos previos de SOCA para una URL, se intentan extraer como fallback.

# SW-METADATA-BOT


# SOCA
- Añadida generación del portal linkeddata a partir del YAML base + YAML propio de URLs de herramientas (`linkeddata_tools`)
- Mejorada la de detección de tipo de repositorio
- Mejorada la obtención der descripciones a partir de metadatos de los repositorios
# RSFC


# RESQUI
- Arreglados bugs de conexión timeout worker_resqui-rabbitmq
- Mejorada la tolerancia a git clone en los worker_resqui
# DashVERSE



