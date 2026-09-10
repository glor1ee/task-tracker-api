# Task Tracker API

![CI](https://github.com/glor1ee/task-tracker-api/actions/workflows/ci.yml/badge.svg)

REST API for tasks and projects with per-user ownership, built with FastAPI,
SQLAlchemy 2.0, Alembic and PostgreSQL.

## Features

- JWT authentication (OAuth2 password flow), passwords hashed with Argon2
- Tasks and projects are private to their owner; foreign resources return `404`
- CRUD with filtering and pagination; projects contain tasks with cascade delete
- Database schema managed by Alembic migrations
- Test suite on pytest, run against PostgreSQL in CI

## Stack

FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 17 · Pydantic v2 · PyJWT ·
pytest · Docker Compose · GitHub Actions · Ruff

## Run with Docker

```bash
docker compose up --build
```

API docs: <http://localhost:8002/docs>

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # then set DATABASE_URL and SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests and linting

```bash
pytest                             # SQLite by default
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/tasktracker_test pytest
ruff check .
```

`TEST_DATABASE_URL` must point to a dedicated test database: the suite drops all
tables after every test.

## Project layout

```
app/
  main.py          FastAPI application and router wiring
  config.py        settings from environment / .env
  database.py      engine, session, declarative base
  models.py        SQLAlchemy models: User, Project, Task
  schemas.py       Pydantic request/response schemas
  crud.py          database access
  security.py      password hashing and JWT
  dependencies.py  current-user dependency
  routers/         auth, tasks, projects endpoints
migrations/        Alembic revisions
tests/             pytest suite
```
