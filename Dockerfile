FROM python:3.12-alpine

WORKDIR /app/

RUN pip install --upgrade pip
RUN apk add gcc musl-dev libffi-dev

RUN pip install --no-cache-dir poetry && \
poetry config virtualenvs.create false

COPY pyproject.toml .
COPY poetry.lock .
COPY app/ app/
COPY .env .

RUN poetry install

ENV PYTHONPATH=/app.

ENTRYPOINT ["python", "-m", "app.main"]
