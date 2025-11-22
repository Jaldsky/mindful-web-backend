# 🌐 Mindful-Web
*Aware presence in the digital world*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-black)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)

> **Mindful-Web** is an open-source tool for mindful internet use.

---

## 🌍 About / О проекте
### 🇬🇧 English
Mindful-Web is an open-source tool for anyone who wants to understand where their time online goes and reclaim
control over their attention.

### 🇷🇺 Русский
Mindful-Web — это open-source инструмент для тех, кто хочет понимать, куда уходит их время в интернете, и возвращать
контроль над своим вниманием.

## ✨ Features

- 🕒 **Full domain-level time tracking**
- 📊 **Daily & weekly usage reports**
- 💡 **Personalized suggestions** based on your habits
- 🔒 **Privacy-first**: only domains, never full URLs
- 🐳 **Docker-ready**: easy deployment with Docker Compose
- 🔄 **Auto-migrations**: database migrations applied automatically

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL with Alembic migrations
- **Task Queue**: Celery + Redis
- **Infrastructure**: Docker, Docker Compose
- **Development**: Poetry, Invoke, Ruff
- **CI/CD**: GitHub Actions (tests, linting, build)

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Jaldsky/mindful-web.git
cd mindful-web
```

### 2. Set up environment variables
Create `.env` file in the project root:
```bash
# Database
POSTGRES_USER=root
POSTGRES_PASSWORD=root
POSTGRES_DB=wmb
```

### 3. Build and start all services
```bash
# Build base image
poetry run invoke build-base

# Start all services (migrations will be applied automatically)
poetry run invoke compose --build
```

### 4. Check that it works
Open in your browser:<br>
🔗 **API Documentation**: http://localhost:8000/docs<br>
🔗 **Health Check**: http://localhost:8000/health

---

## 🛠️ Development

### Local Development Setup

#### 1. Install dependencies
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

#### 2. Start local services
```bash
# Start database and Redis
poetry run invoke compose "up db redis" -d

# Run migrations
poetry run invoke migrate-apply --local

# Start development server
poetry run invoke dev
```

### Available Commands

```bash
# Development
poetry run invoke dev                    # Start development server
poetry run invoke worker                 # Start Celery worker
poetry run invoke beat                   # Start Celery beat scheduler
poetry run invoke tests                  # Run tests
poetry run invoke lint                   # Run linter
poetry run invoke format                 # Format code

# Database
poetry run invoke migrate-create "msg" --local    # Create migration
poetry run invoke migrate-apply --local           # Apply migrations
poetry run invoke migrate-current --local         # Current revision
poetry run invoke migrate-history --local         # Migration history
poetry run invoke migrate-down --local            # Rollback migration

# Docker
poetry run invoke build-base                     # Build base Docker image
poetry run invoke compose                        # Docker Compose commands
```

---

## 🐳 Docker Services

| Service   | Description             | Port    |
|-----------|-------------------------|---------|
| `app`     | FastAPI application     | 8000    |
| `db`      | PostgreSQL database     | 5432    |
| `redis`   | Redis cache/queue       | 6379    |
| `worker`  | Celery worker           | -       |
| `beat`    | Celery scheduler        | -       |
| `migrate` | Database migrations     | -       |

---

## 🔧 Configuration

### Environment Variables

| Variable            | Default              | Description          |
|---------------------|----------------------|----------------------|
| `POSTGRES_USER`     | root                 | Database user        |
| `POSTGRES_PASSWORD` | root                 | Database password    |
| `POSTGRES_DB`       | wmb                  | Database name        |
| `POSTGRES_HOST`     | db                   | Database host        |
| `POSTGRES_PORT`     | 5432                 | Database port        |
| `REDIS_URL`         | redis://redis:6379/0 | Redis connection URL |

---

## 🧪 Testing

```bash
# Run all tests
poetry run invoke tests

# Run specific test file
poetry run python -m unittest app.tests.db.manager_test
```

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `poetry run invoke tests`
5. Run linter: `poetry run invoke lint`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.
