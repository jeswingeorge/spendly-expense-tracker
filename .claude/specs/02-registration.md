# Spec: Registration

## Overview

Turn the existing `GET /register` page into a working sign-up flow. Right now
`register.html` renders a form that POSTs to `/register`, but no POST handler
exists, so submitting does nothing. This step adds server-side handling: validate
the submitted name / email / password, hash the password with werkzeug, insert a
new row into the `users` table via a helper in `database/db.py`, and redirect the
new user to the login page with a success flash message. Duplicate emails and
invalid input are rejected and re-rendered on the form with a clear error. This is
the first half of authentication in the Spendly roadmap; logging the user in and
out comes in later steps.

## Depends on

- **Step 1 — Database setup** (complete). `database/db.py` already provides
  `get_db()`, `init_db()`, `seed_db()` and the `users` table
  (`id, name, email UNIQUE, password_hash, created_at`).

## Routes

- `GET /register` — render the empty registration form — public *(already exists;
  route changes to `methods=["GET", "POST"]`)*
- `POST /register` — validate input, create the user, redirect to `/login` on
  success or re-render the form with an error — public

No other new routes.

## Database changes

No schema changes. The `users` table from Step 1 already has every column needed
(`name`, `email` with a `UNIQUE` constraint, `password_hash`, `created_at`
default).

Two new **helper functions** are added to `database/db.py` (no DB logic in
routes):

- `get_user_by_email(email)` — `SELECT` one user row by email, or `None`.
- `create_user(name, email, password)` — hash `password` with
  `generate_password_hash`, `INSERT` the row, `commit`, return the new user id.
  Raises `sqlite3.IntegrityError` if the email is already taken.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/register.html` — change the hardcoded
    `action="/register"` to `action="{{ url_for('register') }}"`; keep the
    existing `{% if error %}` block; repopulate `name` and `email` with submitted
    values (`value="{{ name or '' }}"`) so a rejected submission is not fully
    cleared.
  - `templates/base.html` — add a `get_flashed_messages()` loop just inside
    `<main class="main-content">` so the login page (and future pages) can show
    the "Account created — please sign in" success message. Use existing style
    tokens / classes; no new hex values.

## Files to change

- `app.py` — allow `POST` on the `register` route, add the handler, set
  `app.secret_key` (needed for `flash` / sessions).
- `database/db.py` — add `get_user_by_email()` and `create_user()` in a new
  `# ---- Users ----` section.
- `templates/register.html` — `url_for` action, sticky field values.
- `templates/base.html` — render flashed messages.
- `CLAUDE.md` — mark Step 2 / `POST /register` as implemented in the route table.

## Files to create

- `.claude/specs/02-registration.md` — this spec.

## New dependencies

No new dependencies. `werkzeug.security.generate_password_hash` and `flask.flash`
are already available.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` through `get_db()`.
- Parameterised queries only — never f-string / `%` / `.format` into SQL.
- Passwords hashed with `werkzeug.security.generate_password_hash`; never store
  the raw password.
- All DB access lives in `database/db.py`, not in the route function.
- Use CSS variables / existing classes — never hardcode hex values.
- All templates extend `base.html`.
- Keep the `# ---- Section ----` banner-comment style in `db.py` and the
  `# ------ Routes ------` style in `app.py`.
- Server-side validation, not just the HTML `required` attribute:
  - name, email, password all non-empty after `strip()`
  - email normalised to `strip().lower()` before lookup / insert
  - password at least 8 characters (matches the form's "Min. 8 characters" hint)
  - duplicate email → re-render form with error, do not 500 on
    `IntegrityError`
- On success: `flash(...)` then `redirect(url_for('login'))` — do **not**
  auto-login (session handling belongs to the login/logout steps).
- Do not touch any stub route other than `register`.
- App stays on port 5001.

## Definition of done

- [ ] `python app.py` starts with no errors on `http://localhost:5001`.
- [ ] Visiting `/register` shows the form; page source shows the form action
      resolving to `/register` via `url_for`.
- [ ] Submitting valid new details redirects to `/login` and the login page
      shows a "please sign in" success message.
- [ ] The new user exists in `users` with a `password_hash` that is **not** the
      plaintext password (verify with a quick `sqlite3` query or
      `get_user_by_email`).
- [ ] Submitting an email that already exists (e.g. `demo@spendly.com`) re-renders
      the form with a visible "email already registered" error and creates no new
      row.
- [ ] Submitting a blank field or a < 8-character password re-renders the form
      with an error and creates no row.
- [ ] A rejected submission keeps the typed name and email in the inputs.
- [ ] `grep` shows no SQL string-formatting and no `sqlite3.connect` /
      `INSERT` inside `app.py` — user creation goes through `database/db.py`.
