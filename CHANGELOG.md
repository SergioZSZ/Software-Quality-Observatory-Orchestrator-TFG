- añadidas 2 variables entorno para controlar si se quiere rate limit de workers
    - ``RATE_LIMIT_SOCA_ENABLED`` y `RATE_LIMIT_SOCA_ENABLED` poner true/false dependiendo de si se quiere activar el limiter para los workers para peticiones a GitHubAPI(con 8 workers de soca no hace falta, de rsfc con 3 es necesario)

- Modifiado bug de concurrencia de soca en `extract_metadata.py` que podía generar error en la creación de carpetas outputs de metadatos (existok=True)