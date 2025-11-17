FROM python:3.11-alpine3.21
LABEL maintainer="ryzhenkovartg@gmail.com"
ENV TZ="Europe/Moscow"

RUN apk add --no-cache gcc musl-dev postgresql-dev libpq bash

RUN addgroup -g 1001 -S appgroup \
    && adduser -u 1001 -S appuser -G appgroup

WORKDIR /service/

COPY pyproject.toml /service/

ENV POETRY_VERSION=1.8.3 \
    VIRTUAL_ENV=/service/.venv \
    PATH="/service/.venv/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV \
    && $VIRTUAL_ENV/bin/pip install -U pip \
    && $VIRTUAL_ENV/bin/pip install "poetry==$POETRY_VERSION" \
    && ln -s $VIRTUAL_ENV/bin/poetry /usr/local/bin/poetry

RUN poetry install --only=main --no-root --no-cache \
    && rm poetry.lock

RUN chown -R appuser:appgroup /service/
