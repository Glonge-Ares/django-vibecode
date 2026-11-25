# AGENTS.md — ExamPrep

## What this project is

ExamPrep is a study platform for exam preparation: students browse published
exams, take timed quizzes (single choice, multiple choice, short text), get
instant scores and can review their attempt history. It also ships Quizlet-like
flashcard decks for memorizing terms (flip cards, self-rated study sessions,
per-user results). Instructors manage all content through the Django admin.

- **Stack**: Django 5.2 (server-rendered templates, no JS framework) +
  PostgreSQL 16, running in Docker Compose.
- **Root**: this directory is the Django project root (`manage.py` lives here).

## Layout

| Path | Purpose |
| --- | --- |
| `config/` | Django project package (`settings.py`, `urls.py`) |
| `accounts/` | Registration app: form, view, tests (uses `contrib.auth` User) |
| `exams/` | Quizzes business app: models, views, templates, admin, seed, tests |
| `flashcards/` | Quizlet-like decks business app: decks, cards, study sessions, results |
| `templates/` | Project-level templates (`base.html`, `registration/login.html`); app templates in `exams/templates/exams/` |
| `static/css/style.css` | All styling — no build step, no npm |
| `mcp_server/server.py` | Custom MCP server exposing exam data to agents |
| `.venv-mcp/` | Host-side venv for the MCP server (never commit) |
| `Dockerfile`, `docker-compose.yml`, `entrypoint.sh` | Container setup |
| `.opencode/skills/exam-prep-dev/SKILL.md` | Project skill — read it before changing quiz/exam logic |

## Domain model (exams/models.py)

- `Exam` — slug auto-generated from title; `duration_minutes` (0 = untimed); `is_published`.
- `Question` — `kind` ∈ {`single`, `multiple`, `text`}; `points`; `order`;
  `expected_text` for short-text grading. Grading is exact-set equality for
  choice questions (no partial credit) and case-insensitive trim equality for
  text answers. The grading rule lives in `Question.is_correctly_answered()`.
- `Choice` — options for a question; `is_correct` flags the right ones.
- `Attempt` — one in-progress attempt per user+exam (reused on page refresh,
  which restarts neither the attempt nor the timer). Stores score/max_score.
- `Answer` — per-question outcome inside an attempt.

URLs: `/` list, `/exam/<slug>/` start page, `/exam/<slug>/take/` the form,
`/exam/<slug>/submit/` (POST only) grades, `/attempts/` history,
`/attempts/<id>/` result, `/admin/` admin.

### Registration (accounts app)

- `/accounts/register/` (name `register`) — `RegisterForm` subclasses
  `UserCreationForm` and adds a **required `email`** field. No e-mail is ever
  sent (SMTP is not configured) — the address is stored as-is, normalized to
  lowercase and validated for format + form-level uniqueness; on success the
  user is logged in immediately and redirected to `exam-list`.
- Uses the stock `contrib.auth` User (no custom user model, no migrations).
- Auth URLs: `/accounts/login/`, `/accounts/logout/`, `/accounts/register/`.

### Flashcards (flashcards/models.py)

- `Deck` — title (unique) with auto-slug, `is_published`; same slug rules as `Exam`.
- `Card` — `term` + `definition` + `position`; flip-card content.
- `DeckResult` — per-user study outcome (`known_count`/`missed_count`); stores
  the self-rated score, not correctness of content.
- Study flow: `/flashcards/` list, `/flashcards/deck/<slug>/` detail (browse +
  flip, recent results), `/flashcards/deck/<slug>/study/` (login required,
  server-side shuffled queue in the session, one card at a time),
  `/flashcards/deck/<slug>/mark/` (POST `mark=known|missed`, redirects
  PRG-style). The study queue is created only by a GET to `study/` — a POST
  without an in-progress session redirects back there.

## Running things (always via Docker Compose)

```sh
docker compose up --build            # build + start web (:8000) and db (:5432)
docker compose exec web python manage.py test          # run the test suite
docker compose exec web python manage.py shell         # Django shell
docker compose exec web python manage.py seed_exams    # idempotent sample data
docker compose exec web python manage.py seed_flashcards  # sample decks
docker compose logs -f web                             # app logs
```

The entrypoint waits for Postgres and runs `migrate` on every start, so
migrations should be committed and `makemigrations` output always checked in.

Postgres is published on host port 5432 (same credentials as `.env.example`),
so the MCP server and ad-hoc psql can reach it from the host.

Demo accounts (created manually, dev only): `admin`/`admin12345` (staff),
`student`/`student12345` (regular user).

## MCP server (host side)

`mcp_server/server.py` (MCP python SDK 2.x, `MCPServer`, stdio) is registered in
`opencode.json` as `exam-db`. Its venv is `.venv-mcp`:

```sh
python3 -m venv .venv-mcp
.venv-mcp/bin/pip install -r requirements.txt mcp
.venv-mcp/bin/python mcp_server/server.py   # starts the stdio server
```

It talks to the Django ORM with `DB_HOST=127.0.0.1`, so the compose stack must
be running first. Tools: `list_exams`, `get_exam`, `list_questions` (full
answer key), `exam_stats`, `get_attempt`, `get_db_schema`, `list_users`.
**Use these tools instead of hand-writing SQL** when asked about exam data,
statistics or schema.

## Conventions

- Follow the `exam-prep-dev` skill (`.opencode/skills/exam-prep-dev/SKILL.md`)
  for feature work — it documents the end-to-end checklists for adding question
  types, flashcard study flows, views and seed data.
- Keep it server-rendered: no new JS/CSS toolchains, only `static/css/style.css`.
- New behavior needs a test in the matching app's `tests.py`
  (`exams/`, `flashcards/`, `accounts/`); run the suite in the container
  before claiming done.
- All page views that mutate data are `@login_required` + `@require_POST`
  where appropriate; staff manage content exclusively through Django admin.
- Env-driven settings only (`DB_*`, `DJANGO_*` in `config/settings.py`) —
  no hardcoded hosts/keys.
