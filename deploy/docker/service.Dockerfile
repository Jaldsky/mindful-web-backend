FROM mindfulweb-base:latest
LABEL maintainer="ryzhenkovartg@gmail.com"

COPY --chown=appuser:appgroup . /app/
COPY --chown=appuser:appgroup deploy/config/celery_conf.py /app/app/celery_conf.py

RUN poetry install --no-root --no-cache

USER appuser
WORKDIR /app

CMD [".venv/bin/python", "-m", "gunicorn", "-c", "deploy/config/gunicorn_conf.py", "app.main:app"]
