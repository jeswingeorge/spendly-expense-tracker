# Spec: Login and Logout

## Overview

Complete the authentication loop started in Step 2. Registration already creates
users and hashes passwords, but there is no way to sign in: `GET /login` renders
`login.html`, the form POSTs to `/login`, and nothing handles that POST. `/logout`
is still a stub returning a plain string. This step adds a `POST /login` handler
that verifies the submitted email + password against the `users` table (werkzeug
`check_password_hash`), starts a server-side session on success, and redirects the
user to the landing page with a welcome flash; bad credentials re-render the form
with a single generic error. `/logout` clears the session and redirects back to
`/login` with a confirmation flash. A `before_request` hook loads the current user
into `g.user` so `base.html` can swap the nav between the signed-out links and a
signed-in state (user's name + Sign out). This is the last piece of core auth;
`/profile` and the expense CRUD steps build on the session established here.

## Depends on

- **Step 1 — Database setup** (complete). `users` table, `get_db()`.
- **Step 2 — Registration** (complete). `create_user()`, `get_user_by_email()`,
  `app.secret_key` is already set, and `base.html` already renders flashed
  messages via `get_flashed_messages(with_categories=true)`.

## Routes

- `GET /login` — render the sign-in form — public *(already exists; route changes
  to `methods=["GET", "POST"]`)*
- `POST /login` — validate credentials, start a session, redirect to `/` on
  success or re-render the form with an error — public
- `GET /logout` — clear the session and redirect to `/login` with a flash —
  logged-in *(currently a stub string; becomes a real redirect response)*

No other new routes.

## Database changes

No schema changes. The `users` row already carries `id`, `name`, `email`,
`password_hash`.

One new **helper function** is added to `database/db.py` in the existing
`# ---- Users ----` section (no DB logic in routes):

- `get_user_by_id(user_id)` — `SELECT` one user row by primary key, or `None`.
  Used by the `before_request` loader to hydrate `g.user` from `session["user_id"]`.

Credential checking itself (`check_password_hash`) is auth logic and stays in the
route, not in `db.py`.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/login.html` — change the hardcoded `action="/login"` to
    `action="{{ url_for('login') }}"`; keep the existing `{% if error %}` block;
    repopulate the email field with the submitted value
    (`value="{{ email or '' }}"`) so a rejected submission is not fully cleared.
  - `templates/base.html` — make the `.nav-links` block conditional on `g.user`:
    when signed in, show the user's name (e.g. `g.user["name"]`) and a **Sign out**
    link to `url_for('logout')`; when signed out, keep the current **Sign in** /
    **Get started** links. Reuse existing nav classes (`.nav-links`, `.nav-cta`)
    and CSS tokens — no new hex values. `g` is available in Jinja without being
    passed explicitly.

## Files to change

- `app.py`
  - add `session`, `g` to the `flask` import; add
    `from werkzeug.security import check_password_hash`; import `get_user_by_id`
    from `database.db`.
  - `login` route: `methods=["GET", "POST"]` + POST handler (normalise email with
    `strip().lower()`, look up via `get_user_by_email`, verify with
    `check_password_hash`, on success `session.clear()` then
    `session["user_id"] = user["id"]` and `redirect(url_for("landing"))` with a
    `flash(...)`, on failure re-render `login.html` with a generic error and the
    sticky email).
  - `logout` route: `session.clear()`, `flash("You have been signed out.", "success")`,
    `redirect(url_for("login"))` — no more raw string return.
  - add a `@app.before_request` loader that sets
    `g.user = get_user_by_id(session["user_id"])` when `session` has a `user_id`,
    else `g.user = None`.
- `database/db.py` — add `get_user_by_id()` under `# ---- Users ----`.
- `templates/login.html` — `url_for` action, sticky email value.
- `templates/base.html` — signed-in vs signed-out nav.
- `CLAUDE.md` — mark Step 3 / `POST /login` + `/logout` implemented in the route
  table and the "Completed steps" notes.

## Files to create

- `.claude/specs/03-login-and-logout.md` — this spec.

## New dependencies

No new dependencies. `werkzeug.security.check_password_hash` and Flask `session` /
`g` are already available.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` through `get_db()`.
- Parameterised queries only — never f-string / `%` / `.format` into SQL.
- Passwords are verified with `werkzeug.security.check_password_hash` against the
  stored `password_hash`; never compare plaintext, never log the password.
- All DB access lives in `database/db.py`, not in the route function — the route
  may call `check_password_hash` but must not open a connection or run SQL.
- Use CSS variables / existing classes — never hardcode hex values.
- All templates extend `base.html`.
- Keep the `# ---- Section ----` banner-comment style in `db.py` and the
  `# ------ Routes ------` banner style in `app.py`.
- Session auth: store only `session["user_id"]` (an int). Call `session.clear()`
  before setting it on login and again on logout. Do not build a "remember me" or
  token system.
- Login failure must be a **single generic message** ("Invalid email or password.")
  for both "no such email" and "wrong password" — do not reveal which was wrong,
  do not 500 on a missing user.
- Server-side validation, not just the HTML `required` attribute: email + password
  non-empty after `strip()`; email normalised to `strip().lower()` before lookup.
- On success: `flash(...)` then `redirect(url_for('landing'))`. Do not redirect to
  a stub route.
- Do not touch any stub route other than `login` and `logout`.
- App stays on port 5001.

## Definition of done

- [ ] `python app.py` starts with no errors on `http://localhost:5001`.
- [ ] `/login` shows the form; page source shows the form action resolving to
      `/login` via `url_for`.
- [ ] Signing in as the seeded demo user (`demo@spendly.com` / `demo123`)
      redirects to `/` and shows a welcome flash; the nav now shows the user's
      name and a **Sign out** link instead of Sign in / Get started.
- [ ] The session cookie is set after login; reloading `/` keeps the signed-in
      nav (session persists across requests).
- [ ] A newly registered user (from the Step 2 flow) can sign in with the
      password they chose.
- [ ] Wrong password for a real email re-renders `/login` with the generic
      "Invalid email or password." error and does **not** sign in.
- [ ] An email that is not registered shows the same generic error, no 500.
- [ ] A blank email or password re-renders the form with an error.
- [ ] A rejected login keeps the typed email in the input.
- [ ] Visiting `/logout` clears the session, redirects to `/login`, shows a
      "signed out" flash, and the nav returns to Sign in / Get started.
- [ ] `grep` shows no `sqlite3.connect` / `SELECT` inside `app.py` — user lookup
      goes through `database/db.py`; login still works.
