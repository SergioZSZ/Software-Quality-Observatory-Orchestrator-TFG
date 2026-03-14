#!/bin/sh

# inicializar base de datos
python -m rsfc_runner.database.init_db

# ejecutar el comando que se pase al contenedor
exec "$@"