# General
- Actualizados scripts de creación de imágenes docker y de instalación de herramientas para DashVERSE
- Añadida nueva variable entorno `RESQUI_CONF` para seleccionar la configuración querida para los worker_resqui
- Cambio de configuración para añadir repos y orgs al portal linkeddata, ejemplo:
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

  
  "linkeddata_portal": {
    "organizations": ["SergioZSZ"],
    "extra_repositories": ["https://github.com/oeg-upm/soca"]
  }
}
```

# SW-METADATA-BOT


# SOCA
- Añadida generación del portal linkeddata a partir del yaml base + orgs/repos que se metan desde conf en el workflow
- Mejorada la heurística de detección de tipo de repositorio
# RSFC


# RESQUI
- Arreglados bugs de conexión timeout worker_resqui-rabbitmq

# DashVERSE



