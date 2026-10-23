# Job Tracker

Personal job-application tracker. Portfolio project on GitHub, and my way of learning
production Python backend work for interviews.

## Stack
FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL 16, pytest, Ruff,
Docker Compose, GitHub Actions. Later: APScheduler/cron + AWS SES, deploy to EC2 + RDS.

## How I want to work
- I write the models, routes, and tests myself. You help with config, boilerplate,
  and debugging, and you review my code.
- Explain anything you generate. Map concepts to Rails when it helps
  (SQLAlchemy ≈ ActiveRecord, Alembic ≈ rails db:migrate, pytest ≈ RSpec, Ruff ≈ RuboCop).
- Use plan mode for anything touching more than one file. Show the plan before editing.
- Small commits. No redesigning mid-build. New ideas go in V2_IDEAS.md.

## Commands
- Run locally: `docker compose up --build`, then http://localhost:8000/health
- Tests: `pytest -v`
- Lint: `ruff check .`

## Data model (MVP)
Tables: users, applications, contacts, events, job_runs.

## Status
- [x] Repo, venv, FastAPI /health endpoint
- [x] First pytest test passing
- [x] Docker Compose (app + Postgres)
- [ ] SQLAlchemy models + first Alembic migration
- [ ] GitHub Actions CI (ruff + pytest)
