FROM python:3.11

WORKDIR /app

# dependencias
RUN apt-get update && apt-get install -y --no-install-recommends docker-cli && rm -rf /var/lib/apt/lists/*
RUN pip install poetry
RUN poetry config virtualenvs.create false



# instalamos UNICAMENTE entorno (--no-root), si no fallo de que no este el paquete rsfc_runner
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root


# resqui
COPY QualityPipelines-2.0 ./QualityPipelines-2.0
RUN pip install -e ./QualityPipelines-2.0


# instalacion de nltk para somef
RUN pip install nltk
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4

# resto del runner
COPY resqui_runner ./resqui_runner


CMD ["python","-m","resqui_runner.main"]

