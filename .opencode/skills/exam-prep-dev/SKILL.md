---
name: exam-prep-dev
description: Conventions and end-to-end checklists for developing the ExamPrep Django + PostgreSQL study platform (quizzes/exam scoring, flashcard decks and study sessions, adding question types, views, seed data, Docker workflows). Use when working on this repository's exams, flashcards, migrations, templates or tests.
---

# ExamPrep development skill

All instructions assume commands run inside the Docker Compose stack from the
project root (`manage.py` directory).

## Everyday commands

```sh
docker compose up --build
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test
docker compose exec web python manage.py seed_exams
docker compose exec web python manage.py seed_flashcards
docker compose exec web python manage.py shell
```

Entrypoint already waits for Postgres and migrates on `up`, so plain
`docker compose up --build` is enough after adding a migration file. Commit the
generated `exams/migrations/*.py` files — tests and containers need them.

## Adding a new question kind (checklist)

1. Extend `Question.Kind` in `exams/models.py` (choices are stored in a
   `CharField`, so no DB migration is needed for a new label — but any new
   *field* on models requires `makemigrations`).
2. Implement grading in `Question.is_correctly_answered()` — it is the single
   source of truth for scoring; views call it and MCP does not re-implement it.
3. Add input rendering in `templates/exams/take_exam.html` (branch on
   `question.kind`) using `name="q{{ question.pk }}"`; POST parsing reads
   `request.POST.getlist(...)` — keep names in sync.
4. Add result rendering in `templates/exams/exam_result.html`.
5. Teach the seed data about it: `exams/management/commands/seed_exams.py`
   `SEED` list entries carry `"kind"` plus `"choices"` or `"expected_text"`.
6. Add grading tests in `exams/tests.py` (model-level for grading, view-level
   for the POST flow).

## Views/flow rules

- Start page (`exam_start`) never mutates state; the `Attempt` row is created
  lazily in `take_exam` (GET) — so refreshing must not create a second attempt
  (already handled by the "reuse open attempt" filter).
- Grading happens exactly once per attempt, in `_grade()`, called from
  `submit_exam` (POST) or from `take_exam` when the timer already expired.
- Anything that submits data is POST + CSRF + `@login_required`.
- Result and attempts pages must scope queries to `request.user` (see the
  `test_cannot_view_others_result` test for the expected 404).

## Registration (accounts app)

- `/accounts/register/` → `accounts.forms.RegisterForm` (subclass of
  `UserCreationForm` adding a required, format-checked `email` normalized to
  lowercase with a form-level uniqueness check). Stock `contrib.auth` User —
  **never introduce a custom user model for this** (would require migrating
  existing data).
- No e-mail is sent anywhere (SMTP is not set up): do not add
  `send_mail`/verification flows unless explicitly asked.
- On success the view logs the user in and redirects to `exam-list`;
  authenticated visitors hitting `register` are redirected away.
- Tests live in `accounts/tests.py`.

## Flashcards (flashcards app)

- Two models plus a result: `Deck` (unique title, auto-slug — same rules as
  `Exam`), `Card` (`term`, `definition`, `position`), `DeckResult`
  (`known_count`/`missed_count`, self-rated, has `percentage`/`passed`).
- URLs: `/flashcards/` list → `deck/<slug>/` detail (browse + flip grid and the
  user's recent sessions) → `deck/<slug>/study/` one-card-at-a-time →
  `deck/<slug>/mark/` (POST `mark=known|missed`, redirect-after-post).
- The study queue lives in the session under `flashcard_study:<slug>` with keys
  `queue` (shuffled card ids), `idx`, `known`, `missed`. It is created only by
  a GET to `study/`; a `mark` POST without a live queue redirects to `study/`
  (covered by `test_mark_without_session_redirects`).
- The `DeckResult` row is written on the final mark, the session key is
  deleted, and the user is redirected to the deck detail page — never render
  results from the POST response itself.
- Layout/JS: flip behavior is pure CSS + inline `onclick` class toggle
  (`.flip-card` / `.flip-inner` / `.flip-face` in `static/css/style.css`); no
  new JS libraries. Study buttons are one form with two submit buttons
  (`name="mark"`).
- New card surfaces (e.g. a typing mode) need coverage in
  `flashcards/tests.py` mirroring `ViewTests.test_study_flow_completes_and_records_result`.

## Templates & CSS

- Every page extends `templates/base.html` and blocks `title`/`content`.
- Styling lives solely in `static/css/style.css` (class names: `card`,
  `question`, `badge`, `chip`, `button`, `table`, `msg`). No CDN, no build step.
- Server messages use `django.contrib.messages` (rendered by base template).

## Checking data without writing SQL

The project's MCP server exposes `list_exams`, `get_exam`, `list_questions`
(full answer key), `exam_stats`, `get_attempt`, `get_db_schema`, `list_users`.
Prefer these tools over raw SQL. The stack must be running
(`docker compose up -d`) because the server uses the ORM against the
published Postgres port (127.0.0.1:5432).

## Pitfalls

- `Question.expected_text` is only used when `kind == "text"`; choice questions
  ignore it. Empty `expected_text` makes every text answer wrong by design.
- `Exam.duration_minutes = 0` means untimed (never render the countdown).
- Scoring is all-or-nothing per question — `multiple` requires the exact set
  of correct choices, no partial credit.
- `STATICFILES_DIRS` points at `static/`; don't create a second `static/`
  directory inside the app.
- Deck/Exam `title` columns are `unique=True`, so idempotent seed commands key
  on title; slugs must never be compared across apps (both auto-generate with
  a `-2`, `-3` suffix loop).
