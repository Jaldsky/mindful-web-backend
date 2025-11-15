#!/usr/bin/env python3
"""
Invoke tasks for the mindful-web application.
"""

import os
import sys
import uvicorn
from invoke import task
from pathlib import Path

from app.common.logging import setup_logging

logger = setup_logging()


def _get_project_root():
    """Получение корневой директории проекта безопасным способом."""
    return Path(__file__).parent.absolute()


def _get_python_executable():
    """Получение правильного исполняемого файла Python для текущей платформы."""
    if sys.platform == "win32":
        return "python.exe"
    return "python"


def _run_safe_command(ctx, cmd, **kwargs):
    """Безопасное выполнение команды с обработкой ошибок.

    Args:
        ctx: Контекст invoke
        cmd: Команда для выполнения (строка или список)
        **kwargs: Дополнительные параметры для ctx.run

    Returns:
        Результат выполнения команды

    Raises:
        Exception: При ошибке выполнения команды
    """
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))

    kwargs.setdefault("shell", "/bin/bash")

    try:
        result = ctx.run(cmd, **kwargs)
        return result
    except Exception as e:
        logger.error(f"❌ Команда завершилась с ошибкой: {e}")
        raise


@task(name="dev")
def dev_server(ctx, host="127.0.0.1", port=8000, reload=True):
    """Запуск сервера разработки с горячей перезагрузкой.

    Args:
        host: Хост сервера (по умолчанию: 127.0.0.1)
        port: Порт сервера (по умолчанию: 8000)
        reload: Включить горячую перезагрузку (по умолчанию: True)
    """
    logger.info(f"🌐 Запуск сервера разработки на {host}:{port}...")
    logger.info("🔄 Горячая перезагрузка включена" if reload else "🔄 Горячая перезагрузка отключена")
    logger.info("⏹️ Нажмите Ctrl+C для остановки")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, log_level="info")


@task(name="worker")
def start_worker(ctx, concurrency=4, loglevel="info"):
    """Запуск Celery worker.

    Args:
        concurrency: Количество процессов worker (по умолчанию: 4)
        loglevel: Уровень логирования (по умолчанию: info)
    """
    logger.info(f"🔄 Запуск Celery worker с {concurrency} процессами...")
    cmd = ["celery", "-A", "app.celery", "worker", f"--loglevel={loglevel}", f"--concurrency={concurrency}"]
    _run_safe_command(ctx, cmd)


@task(name="beat")
def start_beat(ctx, loglevel="info"):
    """Запуск Celery beat планировщика.

    Args:
        loglevel: Уровень логирования (по умолчанию: info)
    """
    logger.info("⏰ Запуск Celery beat планировщика...")
    cmd = ["celery", "-A", "app.celery", "beat", f"--loglevel={loglevel}"]
    _run_safe_command(ctx, cmd)


@task(name="tests")
def tests(ctx):
    """Запуск тестов."""
    logger.info("🧪 Запуск тестов...")
    cmd = ["python", "-m", "unittest", "discover", '--pattern="*test*.py"']
    _run_safe_command(ctx, cmd)


@task(name="lint")
def run_lint(ctx):
    """Проверка кода линтером."""
    logger.info("🔍 Проверка кода линтером...")
    cmd = ["ruff", "check", "app/", "deploy/"]
    _run_safe_command(ctx, cmd)


@task(name="format")
def format_code(ctx):
    """Форматирование кода."""
    logger.info("✨ Форматирование кода...")
    cmd = ["ruff", "format", "app/", "deploy/"]
    _run_safe_command(ctx, cmd)


@task(name="build-base")
def build_base_image(ctx, no_cache=False, image_name="mindfulweb-base", tag="latest"):
    """Сборка базового Docker образа.

    Args:
        no_cache: Сборка без кеша (по умолчанию: False)
        image_name: Название образа (по умолчанию: mindfulweb-base)
        tag: Тег образа (по умолчанию: latest)
    """
    logger.info(f"🐳 Сборка базового Docker образа {image_name}:{tag}...")

    dockerfile_path = os.path.join(_get_project_root(), "deploy", "docker", "base.Dockerfile")

    cmd = ["docker", "build", "-f", dockerfile_path, "-t", f"{image_name}:{tag}", _get_project_root()]

    if no_cache:
        cmd.append("--no-cache")
        logger.info("🚫 Сборка без кеша...")

    _run_safe_command(ctx, cmd)


@task(name="compose")
def docker_compose(ctx, command="up", detach=True, build=False, env_file=".env"):
    """Запуск Docker Compose с подтягиванием .env файла.

    Args:
        command: Команда docker-compose (по умолчанию: up)
        detach: Запуск в фоне (по умолчанию: True)
        build: Сборка образов перед запуском (по умолчанию: False)
        env_file: Путь к .env файлу (по умолчанию: .env)
    """
    logger.info(f"🐳 Запуск Docker Compose: {command}...")

    compose_file = os.path.join(_get_project_root(), "deploy", "docker-compose.yml")
    env_file_path = os.path.join(_get_project_root(), env_file)

    cmd = ["docker-compose", "-f", compose_file, "--env-file", env_file_path, command]

    if command == "up" and detach:
        cmd.append("-d")
        logger.info("🚀 Запуск в фоновом режиме...")

    if build:
        cmd.append("--build")
        logger.info("🔨 Сборка образов перед запуском...")

    _run_safe_command(ctx, cmd)


@task(name="migrate-apply")
def apply_migrations(ctx, local=False):
    """Применение существующих миграций к базе данных.

    Args:
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


@task(name="migrate-create")
def create_migration(ctx, message, local=False):
    """Создание новой миграции.

    Args:
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


@task(name="migrate-down")
def downgrade_migrations(ctx, revision="-1", local=False):
    """Откат миграций.

    Args:
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


@task(name="migrate-history")
def migration_history(ctx, local=False):
    """Показать историю миграций."""
    project_root = _get_project_root()
    alembic_config_path = os.path.join(project_root, "deploy", "config", "alembic.ini")

    env = os.environ.copy()
    if local:
        env["POSTGRES_HOST"] = "localhost"
        logger.info("🏠 Используется localhost для подключения к БД")

    logger.info("📜 История миграций:")
    cmd = ["alembic", "-c", alembic_config_path, "history", "--verbose"]
    _run_safe_command(ctx, cmd, env=env)


@task(name="migrate-current")
def current_migration(ctx, local=False):
    """Показать текущую ревизию."""
    project_root = _get_project_root()
    alembic_config_path = os.path.join(project_root, "deploy", "config", "alembic.ini")

    env = os.environ.copy()
    if local:
        env["POSTGRES_HOST"] = "localhost"
        logger.info("🏠 Используется localhost для подключения к БД")

    logger.info("📍 Текущая ревизия:")
    cmd = ["alembic", "-c", alembic_config_path, "current"]
    _run_safe_command(ctx, cmd, env=env)


@task(name="migrate-create-docker")
def create_migration_docker(ctx, message):
    """Создание новой миграции в Docker контейнере.

    Args:
        message: Сообщение для миграции
    """
    logger.info(f"🐳 Создание миграции в Docker: {message}")
    cmd = [
        "docker-compose",
        "-f",
        "deploy/docker-compose.yml",
        "run",
        "--rm",
        "migrate",
        ".venv/bin/python",
        "-m",
        "invoke",
        "migrate-create",
        message,
    ]
    _run_safe_command(ctx, cmd)


@task(name="migrate-apply-docker")
def apply_migrations_docker(ctx):
    """Применение миграций в Docker контейнере."""
    logger.info("🐳 Применение миграций в Docker...")
    cmd = [
        "docker-compose",
        "-f",
        "deploy/docker-compose.yml",
        "run",
        "--rm",
        "migrate",
        ".venv/bin/python",
        "-m",
        "invoke",
        "migrate-apply",
    ]
    _run_safe_command(ctx, cmd)
