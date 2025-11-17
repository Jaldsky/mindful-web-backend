#!/usr/bin/env python3
"""
Invoke tasks for the mindful-web application.
"""

import os
import uvicorn
from invoke import task
from pathlib import Path

from app.common.logging import setup_logging

logger = setup_logging()


def _run_safe_command(ctx, cmd, **kwargs):
    """Безопасное выполнение команды с обработкой ошибок.

    Args:
        ctx: Контекст invoke.
        cmd: Команда для выполнения.
        **kwargs: Дополнительные параметры для ctx.run

    Returns:
        Результат выполнения команды

    Raises:
        Exception: При ошибке выполнения команды
    """
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))

    kwargs.setdefault("shell", "/bin/sh")

    try:
        result = ctx.run(cmd, **kwargs)
        return result
    except Exception as e:
        logger.error(f"❌ Команда завершилась с ошибкой: {e}")
        raise


def _get_project_root():
    """Получение корневой директории проекта безопасным способом."""
    return Path(__file__).parent.absolute()


@task(name="dev")
def dev_server(ctx, host="127.0.0.1", port=8000, reload=True):
    """Запуск сервера разработки с горячей перезагрузкой.

    Args:
        ctx: Контекст invoke.
        host: Хост сервера.
        port: Порт сервера.
        reload: Включить горячую перезагрузку.
    """
    logger.info(f"🌐 Запуск сервера разработки на {host}:{port}...")
    logger.info("🔄 Горячая перезагрузка включена" if reload else "🔄 Горячая перезагрузка отключена")
    logger.info("⏹️ Нажмите Ctrl+C для остановки")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, log_level="info")


@task(name="worker")
def start_worker(ctx, concurrency=4, loglevel="info"):
    """Запуск Celery worker.

    Args:
        ctx: Контекст invoke.
        concurrency: Количество процессов worker.
        loglevel: Уровень логирования.
    """
    logger.info(f"🔄 Запуск Celery worker с {concurrency} процессами...")
    cmd = ["celery", "-A", "app.celery", "worker", f"--loglevel={loglevel}", f"--concurrency={concurrency}"]
    _run_safe_command(ctx, cmd)


@task(name="beat")
def start_beat(ctx, loglevel="info"):
    """Запуск Celery beat планировщика.

    Args:
        ctx: Контекст invoke.
        loglevel: Уровень логирования.
    """
    logger.info("⏰ Запуск Celery beat планировщика...")
    cmd = ["celery", "-A", "app.celery", "beat", f"--loglevel={loglevel}"]
    _run_safe_command(ctx, cmd)


@task(name="tests")
def tests(ctx):
    """Запуск тестов.

    Args:
        ctx: Контекст invoke.
    """
    logger.info("🧪 Запуск тестов...")
    cmd = ["python", "-m", "unittest", "discover", '--pattern="*test*.py"']
    _run_safe_command(ctx, cmd)


@task(name="lint")
def run_lint(ctx):
    """Проверка кода линтером.

    Args:
        ctx: Контекст invoke.
    """
    logger.info("🔍 Проверка кода линтером...")
    cmd = ["ruff", "check", "app/", "deploy/"]
    _run_safe_command(ctx, cmd)


@task(name="format")
def format_code(ctx):
    """Форматирование кода.

    Args:
        ctx: Контекст invoke.
    """
    logger.info("✨ Форматирование кода...")
    cmd = ["ruff", "format", "app/", "deploy/"]
    _run_safe_command(ctx, cmd)


@task(name="build-base")
def build_base_image(ctx, no_cache=False, image_name="wmb-base", tag="latest"):
    """Сборка базового Docker образа.

    Args:
        ctx: контекст invoke.
        no_cache: Сборка без кеша.
        image_name: Название образа.
        tag: Тег образа.
    """
    logger.info(f"🐳 Сборка базового Docker образа {image_name}:{tag}...")

    dockerfile_path = os.path.join(_get_project_root(), "deploy", "docker", "base.Dockerfile")

    cmd = ["docker", "build", "-f", dockerfile_path, "-t", f"{image_name}:{tag}", _get_project_root()]

    if no_cache:
        cmd.append("--no-cache")
        logger.info("🚫 Сборка без кеша...")

    _run_safe_command(ctx, cmd)


@task(name="compose-up")
def docker_compose_up(ctx, rebuild=False, env_file=".env"):
    """Запуск Docker Compose с подтягиванием .env файла.

    Args:
        ctx: Контекст invoke.
        rebuild: Пересобирать ли образ базовый образ и образ сервиса.
        env_file: Путь к .env файлу (по умолчанию: .env)
    """
    base_image_name = "mwb-base"
    base_image_tag = "latest"

    project_root = _get_project_root()
    compose_file = os.path.join(project_root, "deploy", "docker-compose.yml")
    env_file_path = os.path.join(project_root, env_file)

    logger.info("🐳 Запуск Docker Compose...")

    env = os.environ.copy()
    if rebuild:
        logger.info("🐛 Сборка локального базового образа...")
        build_base_image(ctx, image_name=base_image_name, tag=base_image_tag)
        logger.info("✅ Локальный базовый образ собран")

        base_image = f"{base_image_name}:{base_image_tag}"
        env["BASE_IMAGE"] = base_image
        env["DOCKER_BUILDKIT"] = "0"
        logger.info(f"🐛 Используется локальный базовый образ: {base_image}")

    cmd = ["docker-compose", "-f", compose_file, "--env-file", env_file_path, "up", "-d"]
    logger.info("🚀 Запуск в фоновом режиме...")

    if rebuild:
        cmd.append("--build")
        cmd.append("--pull=never")

    _run_safe_command(ctx, cmd)


@task(name="migrate-create")
def create_migration(ctx, message, local=False):
    """Создание новой миграции.

    Args:
        ctx: Контекст invoke.
        message: Сообщение для миграции
        local: Использовать localhost вместо db для подключения к БД (по умолчанию: False)
    """
    project_root = _get_project_root()
    alembic_config_path = os.path.join(project_root, "deploy", "config", "alembic.ini")

    env = os.environ.copy()
    if local:
        env["POSTGRES_HOST"] = "localhost"
        logger.info("🏠 Используется localhost для подключения к БД")

    logger.info(f"🔄 Создание новой миграции: {message}")
    cmd = ["alembic", "-c", alembic_config_path, "revision", "--autogenerate", "-m", message]
    _run_safe_command(ctx, cmd, env=env)


@task(name="migrate-apply")
def apply_migrations(ctx, local=False):
    """Применение существующих миграций к базе данных.

    Args:
        ctx: Контекст invoke.
        local: Использовать localhost вместо db для подключения к БД (по умолчанию: False)
    """
    project_root = _get_project_root()
    alembic_config_path = os.path.join(project_root, "deploy", "config", "alembic.ini")

    env = os.environ.copy()
    if local:
        env["POSTGRES_HOST"] = "localhost"
        logger.info("🏠 Используется localhost для подключения к БД")

    logger.info("🔄 Применение миграций...")
    cmd = ["alembic", "-c", alembic_config_path, "upgrade", "head"]
    _run_safe_command(ctx, cmd, env=env)


@task(name="migrate-down")
def downgrade_migrations(ctx, revision="-1", local=False):
    """Откат миграций.

    Args:
        ctx: Контекст invoke.
        revision: Ревизия для отката (по умолчанию: -1)
        local: Использовать localhost вместо db для подключения к БД (по умолчанию: False)
    """
    project_root = _get_project_root()
    alembic_config_path = os.path.join(project_root, "deploy", "config", "alembic.ini")

    env = os.environ.copy()
    if local:
        env["POSTGRES_HOST"] = "localhost"
        logger.info("🏠 Используется localhost для подключения к БД")

    logger.info(f"⬇️ Откат миграций до ревизии: {revision}")
    cmd = ["alembic", "-c", alembic_config_path, "downgrade", revision]
    _run_safe_command(ctx, cmd, env=env)
