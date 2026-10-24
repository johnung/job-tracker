# Job Tracker App — MVP Scope

Oct 18, 2026 · @John

## Goal and ground rules

A deployed Python job-application tracker, built in two weekends: the tool I use for my own job search.

- **Timebox:** two weekends for v1. Anything not done by then moves to the v2 list, not into weekend three.
- **No redesigns mid-build:** decisions in this doc are locked for v1. New ideas go on the v2 list.

## MVP features

v1 covers the basics of tracking applications, plus one thing a spreadsheet can't do: email you when an application goes quiet.

**In v1**

- Log in (single user is fine, but real auth: hashed passwords + JWT)
- Applications: create, edit, delete; company, role, stage, applied date, link, pay range, location, source
- Stage changes are recorded automatically as timeline events (an audit trail, not just a status field)
- Contacts per application: name, title, how you met, notes
- Timeline events: date + what happened (calls, emails, interview rounds)
- Retro fields: what went well, what to improve
- Search across companies, roles, contacts and notes
- Daily follow-up email for applications with no activity in 10+ days
- Minimal web UI: server-rendered pages (Jinja2 + HTMX) or a plain HTML page calling the API

**Out of v1 (the v2 list)**

- React/Vue frontend
- Multi-user sign-up, password reset, OAuth
- Pipeline charts and stats
- Resume version tracking per application
- Importing jobs from Dice/Indeed
- AI features beyond v1.5 (RAG, vector DB, fine-tuning, auto-apply)

## v1.5: AI features (after v1 + CI)

This phase builds hands-on experience with AI-assisted engineering workflows and LLM features in production, applied to a real problem: vetting job postings. It comes before v2 (multi-user sign-up).

**1. Posting analyzer (LLM feature)**

- Paste a job posting → LLM returns structured JSON: title, company, location/remote, salary range, required stack, years required, red flags (e.g. "on-site 5 days", "7+ years", "clearance required")
- Validate the LLM output with a Pydantic schema; reject or retry on invalid JSON
- Save the result as a draft application to review and edit
- Log tokens and cost per call
- Tests: mock the LLM in unit tests; a small eval set of \~10 real postings with expected fields, run as a separate test target

**2. MCP server for the tracker**

- Read-only tools first: `list_applications`, `get_application`, `search_applications` (by company or status)
- Goal: query the tracker from Claude ("which applications are older than 2 weeks with no response?")
- Write-access tools only after read-only works and is tested

**3. Workflow practice (how to build 1 and 2)**

- Build with 2–3 Claude Code sessions in parallel git worktrees (e.g. one on the analyzer, one on the MCP server, one on tests)
- Review every diff before merging; record what the agents got wrong in `docs/AI_LOG.md` (hallucinated APIs, wrong patterns, corrections)

**Out of scope for v1.5:** auto-applying to jobs, scraping LinkedIn, fine-tuning, RAG or a vector DB.

## Tech stack

Each choice has a Rails equivalent, since I came from Rails.

| Layer | Choice | Rails equivalent | Why |
| --- | --- | --- | --- |
| Web framework | FastAPI | Rails controllers + routes | Most-asked-about Python API framework; auto-generated API docs at /docs |
| Validation | Pydantic | Strong params + model validations | Built into FastAPI |
| ORM | SQLAlchemy 2.0 | ActiveRecord | Industry standard; forces you to see the SQL |
| Migrations | Alembic | `rails db:migrate` | Same idea, explicit migration files |
| Database | PostgreSQL | PostgreSQL | Production-proven, same as the Rails side |
| Background jobs | APScheduler (in-process) or cron + a CLI command | ActiveJob / Delayed Job / cron + rake | One daily job doesn't justify a queue (see below) |
| Email | AWS SES | ActionMailer | Stays inside AWS |
| Tests | pytest + httpx test client | RSpec | Same TDD habits |
| Lint/format | Ruff | RuboCop | Direct parallel to RuboCop |
| Packaging | Docker + docker-compose | Docker | App + Postgres in one command |
| CI | GitHub Actions | GitLab CI/CD | Run tests and Ruff on every push |
| Hosting | AWS EC2 + RDS | — | Familiar AWS setup; cheap on a t-series instance |

## Data model

Four tables, plus a small job\_runs log for the background job. Contacts and events are separate tables, not JSON columns, so search and "last activity" are plain SQL.

| Table | Columns | Notes |
| --- | --- | --- |
| users | id, email (unique), password\_hash, created\_at, updated\_at, name | One user for now; keeps auth honest |
| applications | id, user\_id → users, company, role, stage, applied\_on, posting\_url, pay\_range, location, source, went\_well, to\_improve, notes, created\_at, updated\_at | `stage` is a Postgres enum: wishlist, applied, screen, technical, onsite, offer, rejected, ghosted, withdrawn |
| contacts | id, application\_id → applications (cascade delete), name, title, how\_met, notes | One application has many contacts |
| events | id, application\_id → applications (cascade delete), occurred\_on, kind, body | `kind`: note, stage\_change, interview, email. Stage changes write a row here automatically |

**Indexes:** `applications(user_id, stage)`, `events(application_id, occurred_on)`.

**"Needs follow-up"** = stage in (applied, screen, technical, onsite) and the latest `events.occurred_on` (or `applied_on`) is 10+ days ago. One query with a `MAX()` and `GROUP BY`.

## API endpoints

REST, JSON, every route except login behind a bearer token. Twelve routes cover v1.

| Method | Path | Does |
| --- | --- | --- |
| POST | /auth/login | Email + password → JWT |
| GET | /applications | List; filters `?stage=`, `?q=` (search), `?needs_follow_up=true` |
| POST | /applications | Create; writes a first "applied" event |
| GET | /applications/{id} | One application with its contacts and events |
| PATCH | /applications/{id} | Partial update; a stage change also writes a stage\_change event |
| DELETE | /applications/{id} | Delete (cascades to contacts and events) |
| POST | /applications/{id}/contacts | Add a contact |
| PATCH | /contacts/{id} | Edit a contact |
| DELETE | /contacts/{id} | Remove a contact |
| POST | /applications/{id}/events | Log an event |
| DELETE | /events/{id} | Remove an event |
| GET | /health | For the load balancer and uptime checks |

Every route checks that the record belongs to the logged-in user; a test proves another user gets a 404.

## Background job: daily follow-up email

One scheduled job at 8:00 AM Pacific emails a list of applications that have gone quiet for 10+ days. If the list is empty, it sends nothing.

1. Scheduler fires (cron on the EC2 box calling `python -m tracker.jobs.follow_up`, or APScheduler inside the app).
2. Run the "needs follow-up" query from the data model.
3. Build a plain-text email: company, role, stage, days since last activity, last contact's name.
4. Send through AWS SES.
5. Record the run in a `job_runs` row (started, finished, count, error) so a failure is visible, not silent.

**Design decisions:**

- **Why no queue (Celery, RQ)?** One job, once a day, a few rows. A queue adds Redis and a worker process for no benefit. You'd add one when jobs are triggered by users, run long, or need retries at volume.
- **Idempotency:** if the job runs twice in a day, it shouldn't email twice. Check `job_runs` for today's success before sending.
- **Failure handling:** an SES error is caught and written to `job_runs`; the next day's run still happens.

## Two-weekend build plan

Four sessions of about 3 hours each. Each one ends with something that runs and a commit on GitHub.

**Weekend 1, Saturday: skeleton**

- [ ] Repo, README stub, Ruff, pytest, GitHub Actions running both
- [ ] docker-compose with FastAPI + Postgres; `/health` returns 200
- [ ] SQLAlchemy models + first Alembic migration for all tables

**Weekend 1, Sunday: the core API**

- [ ] Login + JWT; password hashing
- [ ] Applications CRUD with stage-change events
- [ ] Contacts and events routes
- [ ] Tests for each route, including the other-user 404

**Weekend 2, Saturday: search, follow-up, UI**

- [ ] `?q=` search and `?needs_follow_up=true` filter
- [ ] Follow-up job + SES email + job\_runs + idempotency test
- [ ] Minimal UI: list, detail, add forms

**Weekend 2, Sunday: ship it**

- [ ] Deploy to EC2 + RDS; secrets in environment variables, not the repo
- [ ] Schedule the daily job; confirm one real email arrives
- [ ] README: what it is, architecture sketch, how to run, design decisions
