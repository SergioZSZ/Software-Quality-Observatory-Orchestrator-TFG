FROM python:3.11

WORKDIR /app

# dependencias
RUN apt-get update
RUN pip install poetry
RUN poetry config virtualenvs.create false



# instalamos UNICAMENTE entorno (--no-root), si no fallo de que no este el paquete rsfc_runner
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# descarga de paquetes nltk (stopwords, lemmatizzer)
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader wordnet omw-1.4

# cod
COPY . .


EXPOSE 8000

CMD ["sh", "-c", "python -m rsfc_runner.init_db && uvicorn rsfc_runner.main:app --host 0.0.0.0 --port 8000"]


