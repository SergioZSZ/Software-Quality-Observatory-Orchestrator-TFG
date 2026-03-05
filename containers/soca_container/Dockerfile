FROM python:3.11

WORKDIR /app

# dependencias
RUN apt-get update
RUN pip install poetry
RUN poetry config virtualenvs.create false


# instalamos UNICAMENTE entorno (--no-root), si no fallo de que no este el paquete soca_runner
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root


# instalacion de soca
COPY soca ./soca
RUN pip install -e ./soca


# descarga de paquetes nltk (stopwords lemmatizer...)
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader wordnet omw-1.4

# resto cod
COPY . .


EXPOSE 8000

CMD ["uvicorn", "soca_runner.main:app", "--host", "0.0.0.0", "--port", "8000"]



