FROM python:3.11

WORKDIR /app

# dependencias
RUN apt-get update
RUN pip install poetry
RUN poetry config virtualenvs.create false



# instalamos UNICAMENTE entorno (--no-root), si no fallo de que no este el paquete rsfc_runner
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root


# rsfc 
COPY rsfc-main ./rsfc-main
RUN pip install -e ./rsfc-main


# instalacion de nltk para somef de soca
RUN pip install nltk
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4

# resto del runner
COPY rsfc_runner ./rsfc_runner

RUN chmod +x /app/rsfc_runner/database/init_db.sh

ENTRYPOINT ["/app/rsfc_runner/database/init_db.sh"]

CMD ["python","-m","rsfc_runner.main"]

