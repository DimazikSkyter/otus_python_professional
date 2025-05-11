FROM python:3.12-slim

ENV POETRY_VERSION=2.1.2


RUN pip install poetry==$POETRY_VERSION


WORKDIR /app

COPY pyproject.toml poetry.lock /app/
COPY src/ /app/src/
COPY reports/report.html /app/
COPY README.md /app/

RUN poetry install --only main

ENTRYPOINT ["poetry", "run", "python", "log_analyser.py", "--config", "config.json"]
