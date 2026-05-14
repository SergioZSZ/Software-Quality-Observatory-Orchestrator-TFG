FROM python:3.11

WORKDIR /app

# dependencias
RUN apt-get update
RUN pip install poetry
RUN poetry config virtualenvs.create false


# instalamos UNICAMENTE entorno (--no-root), si no fallo de que no este el paquete soca_runner
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root



COPY . ./

EXPOSE 9001

CMD ["python","-m","uvicorn","emb_api:app", "--host", "0.0.0.0","--port","9001"]



