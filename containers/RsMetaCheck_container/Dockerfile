FROM python:3.11

WORKDIR /app

# dependencias base
RUN apt-get update
RUN pip install poetry
RUN poetry config virtualenvs.create false


# instalamos solo el entorno del contenedor
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root


# instalacion editable de RsMetaCheck
COPY RsMetaCheck-0.2.1 ./RsMetaCheck-0.2.1
RUN pip install -e ./RsMetaCheck-0.2.1


# recursos nltk usados indirectamente por somef
RUN pip install nltk
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4


# configuracion inicial de somef
COPY initial_configs.sh /initial_configs.sh
RUN chmod +x /initial_configs.sh


# runner del contenedor
COPY rsmetacheck_runner ./rsmetacheck_runner


ENTRYPOINT ["/initial_configs.sh"]

CMD ["python", "-m", "rsmetacheck_runner.main"]
