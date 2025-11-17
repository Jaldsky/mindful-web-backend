FROM mwb-base:latest
LABEL maintainer="ryzhenkovartg@gmail.com"

COPY --chown=appuser:appgroup pyproject.toml /service/

RUN poetry install \
    && poetry cache clear --all . \
    && rm poetry.lock

COPY --chown=appuser:appgroup deploy/config/ /service/deploy/config/
COPY --chown=appuser:appgroup tasks.py /service/
COPY --chown=appuser:appgroup /app/ /service/app

USER appuser
