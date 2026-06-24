FROM python:3.11

ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/usr/local/share/nltk_data

WORKDIR /app

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# Dependencias del proyecto
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi

# Instalación de SOCA
COPY soca ./soca
RUN pip install --no-cache-dir -e ./soca

# Recursos NLTK descargados durante la construcción de la imagen
RUN pip install nltk
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader punkt_tab
RUN python -m nltk.downloader stopwords


        

# Configuración de SOMEF y SOCA
COPY initial_configs.sh /initial_configs.sh
RUN chmod +x /initial_configs.sh

# Código de los workers
COPY soca_runner ./soca_runner

ENTRYPOINT ["/initial_configs.sh"]
CMD ["python", "-u", "-m", "soca_runner.main"]