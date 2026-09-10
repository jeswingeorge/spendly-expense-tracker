# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Spendly" — a personal expense-tracker web app (Flask, server-rendered Jinja2, SQLite),
denominated in Indian Rupees (₹). It is a **teaching scaffold**: a step-by-step course
exercise where large parts are intentionally left unimplemented for a student to build.
Upstream: https://github.com/campusx-official/spendly

Because of this, most of the code is still a skeleton. Do not treat the remaining
stubs as bugs — they are the assignment. When asked to "implement Step N", match
the spec in the relevant file's comments and keep the existing style.

**Completed steps:**

- **Step 1 (database setup)** — `database/db.py` is fully implemented
  (`get_db()`, `init_db()`, `seed_db()`). See `.claude/specs/01-database-setup.md`.
  Anything below that still calls `db.py` "empty" is out of date.
- **Step 2 (registration)** — `POST /register` is implemented: server-side
  validation, werkzeug password hashing, `create_user()` / `get_user_by_email()`
  helpers in `database/db.py`, success flash + redirect to `/login`. See
  `.claude/specs/02-registration.md`. Login/logout and sessions are still stubs.

The remaining steps still apply.

## Commands

Environment: Windows 11, PowerShell. A virtualenv already exists at `.venv`.

```powershell
.venv\Scripts\Activate.ps1            # activate venv
pip install -r requirements.txt       # install deps (flask, werkzeug, pytest, pytest-flask)

python app.py                         # run dev server -> http://localhost:5001 (debug reloader on)

pytest                                # run tests (pytest-flask configured; no tests written yet)
pytest path/to/test_file.py::test_name   # run a single test
```

Note the port is **5001**, not Flask's default 5000.

## Architecture

- **`app.py`** — the entire application: one Flask app, all routes defined flat in this
  file. Routes split into "real" (`/`, `/register`, `/login`, `/terms`, `/privacy` — these
  `render_template`) and placeholder stubs (`/logout`, `/profile`, `/expenses/add`,
  `/expenses/<id>/edit`, `/expenses/<id>/delete`) that currently return plain strings
  labeled "coming in Step N". There is no blueprint / app-factory structure.

- **`database/db.py`** — implemented in Step 1. Provides `get_db()` (SQLite
  connection with `row_factory` + `PRAGMA foreign_keys = ON`), `init_db()`
  (`CREATE TABLE IF NOT EXISTS` for `users` and `expenses`), and `seed_db()`
  (idempotent demo user + 8 sample expenses). The DB file is `expense_tracker.db`
  at repo root (gitignored). Feature-specific helpers (e.g. user lookups) are
  still added here per step, not in route functions.

- **`templates/`** — Jinja2. Every page `{% extends "base.html" %}` and fills
  `{% block content %}` (plus optional `head` / `scripts` blocks). `base.html` owns the
  nav, footer, font `<link>`s, and the global CSS/JS includes. Use `url_for()` for all
  internal links and static assets. `POST /register` is implemented (Step 2); the
  `POST /login` handler does not exist yet.

- **`static/css/style.css`** — a hand-written design system, no CSS framework. Colors,
  fonts, spacing, and radii are CSS custom properties on `:root` (`--ink*`, `--paper*`,
  `--accent*`, `--danger*`, `--border*`, `--font-display` = DM Serif Display,
  `--font-body` = DM Sans). Reuse these tokens rather than hardcoding values.

- **`static/js/main.js`** — essentially empty; page-specific JS currently lives inline in
  a template's `{% block scripts %}` (see `landing.html`).

## Conventions

- Python and CSS files use full-width `# ---- Section ----` / `/* ---- Section ---- */`
  banner comments to divide sections; follow that when adding code.
- `notes/` and `file.md` are the course author's personal learning notes (Claude Code
  tutorials), not project docs — don't modify them or rely on them for app behavior.

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET, POST /register` | Implemented — Step 2 (registration) |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is implemented (Step 1)** — `get_db()`, `init_db()`, `seed_db()` exist; do not assume *other* helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this