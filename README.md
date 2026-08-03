# SecureNotes Lab

> ** Work in progress & intentionally-vulnerable-by-design.** This is a hands-on security-education project. The current `baseline` branch is a *secure* implementation. Later branches will deliberately introduce and then remediate OWASP API Top 10 vulnerabilities for study. Nothing here is production software, and the planned vulnerable branches are intentional and educational.

A small Flask + SQLite REST API for personal notes, built from scratch as a vehicle for learning application, web, and API security end to end — building it securely first, then studying how each class of vulnerability works by introducing it deliberately, detecting it, and remediating it.

This repository is shared as a **work sample**. It reflects genuine in-progress work, including the reasoning behind each security decision.

---

## Why this project exists

I wanted to understand API security at the level of *why*, not just *how* — so instead of reading about SQL injection or broken authentication, I'm building an API that will eventually contain each vulnerability on purpose, then hardening it and proving the fix. The `baseline` you see here is the secure foundation that everything else is measured against.

Building it manually (raw SQL and hand-rolled auth rather than an ORM or an auth library) is a deliberate choice: abstractions like automatic query parameterization or turnkey session management hide the exact mechanisms I'm trying to learn. Doing it by hand means I can later see precisely what protection I'm removing when I introduce a vulnerability.

---

## What's implemented (baseline)

A complete, authenticated REST API with a full session lifecycle and layered authorization.

**Authentication**
- User registration with **bcrypt** password hashing (per-password salting; passwords never stored in plaintext).
- Login that issues a cryptographically-random session token (`secrets.token_hex`) with a UTC expiry.
- Token verification on every protected request, with passive expiry enforcement (expired tokens are rejected at lookup time).
- Logout that actively revokes a token by deleting it — a genuine invalidation, so a logged-out token stops working immediately.

**Authorization**
- *Horizontal* — note ownership: users can only read, update, or delete their own notes. Enforced in the query (`WHERE id = ? AND owner_id = ?`) and verified with cross-user tests.
- *Vertical* — role-based access: admin-only endpoints reject regular users with `403`, distinct from the `401` returned to unauthenticated requests.

**Data handling**
- Parameterized queries throughout (no string-built SQL).
- Foreign-key enforcement enabled at the connection layer.
- Data minimization on every response — internal fields such as password hashes are never returned to clients.

**Auditing**
- Security-event logging for authentication and authorization events (login success/failure, access-denied), recording event type, attempted username, user id where applicable, endpoint, and source IP — the groundwork for later anomaly detection.

### Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | none | Liveness check |
| POST | `/api/register` | none | Create a user |
| POST | `/api/login` | none | Authenticate, receive a token |
| POST | `/api/logout` | token | Revoke the current token |
| GET | `/api/profile` | token | Current user's own profile |
| GET | `/api/notes` | token | List the user's own notes |
| POST | `/api/notes` | token | Create a note |
| GET | `/api/notes/<id>` | token | Retrieve one owned note |
| PUT | `/api/notes/<id>` | token | Partial update of an owned note |
| DELETE | `/api/notes/<id>` | token | Delete an owned note |
| GET | `/api/admin/users` | admin | List all users (admin only) |
| GET | `/api/users/<id>` | admin | Retrieve a user (admin only) |

---

## Security design decisions

The reasoning behind the implementation matters more than the code itself. A few choices worth calling out:

- **No username enumeration on login.** A failed login returns an identical response whether the username doesn't exist or the password is wrong, so an attacker can't discover valid usernames from the response.
- **Timing-attack mitigation.** Because bcrypt is deliberately slow, skipping the hash check when a user doesn't exist would make that path measurably faster and leak which usernames are real. The login path runs a hash check against a dummy hash even for nonexistent users, equalizing response time. (This is a mitigation, not a perfect constant-time guarantee — noted as residual risk.)
- **Authorization order.** Role checks run *before* resource lookups, so an unauthorized user can't distinguish "exists but forbidden" from "doesn't exist" and can't enumerate resource IDs.
- **Ownership enforced in the query.** Ownership checks are baked into the `WHERE` clause and confirmed via affected-row counts, so an operation on someone else's resource simply affects nothing.
- **Audit logs are self-describing and tolerant of missing data.** The security-events table deliberately allows a null user id (and captures the *attempted* username) so that events about nonexistent or deleted users — exactly the interesting security cases — can still be recorded faithfully.

---

## Architecture

The request lifecycle: a client sends a request with a bearer token; Flask routes it through authentication (valid, unexpired token?) and authorization (does this user own / have the role for this resource?) before any database access; security-relevant events are recorded to an audit log along the way.

See `lab-diagram.drawio.svg` for the diagram.

---

## Tech stack

- **Python 3 / Flask** — API framework
- **SQLite** (`sqlite3`, standard library) — storage
- **bcrypt** — password hashing
- **pytest, Bandit, pip-audit** — testing and security tooling (used in later phases)

Runtime and development dependencies are separated (`requirements.txt` vs `requirements-dev.txt`) so a future container image can ship without test/scan tooling.

---

## Running it locally

> Bound to `127.0.0.1` only — never exposed to the network. This is a deliberate safety control, since the project will later host intentional vulnerabilities.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# build the database schema and seed synthetic test data
sqlite3 securenotes.db < schema.sql
python seed.py

python app.py        # serves on http://127.0.0.1:5000
```

Example:

```bash
curl http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "password"}'
# -> {"token": "..."}

curl http://127.0.0.1:5000/api/notes \
  -H "Authorization: Bearer <token>"
```

All seeded data is synthetic. No real credentials are used anywhere.

---

## Roadmap

The baseline above is phase one. The project continues in deliberately-separated branches so that a `git diff` cleanly shows each vulnerability and each fix:

- **`baseline`** *(current)* — secure, functional API.
- **`vulnerable`** *(planned)* — introduce OWASP API Top 10 issues one at a time: SQL injection, broken object-level authorization (IDOR), broken authentication, mass assignment, verbose errors / information disclosure, security misconfiguration, and more.
- **`hardened`** *(planned)* — remediate each finding, with before/after evidence.
- **`testing`** *(planned)* — exploit and regression scripts that run against both the vulnerable and hardened versions to demonstrate that attacks succeed before hardening and are blocked after.

Also planned: request/error logging expansion, a lightweight threat model, automated functional and security-regression tests, baseline security scans (Bandit, pip-audit, OWASP ZAP), and containerization for isolation.

---

## What I've learned so far

This project has been as much about the reasoning as the code. A few things that clicked while building it:

- Why parameterized queries stop injection at the structural level — and that the same technique can't protect table/column names, which need allow-listing instead.
- That "identical error messages" isn't the same as "no information leak" — timing, status codes, and response differences are all side channels.
- The difference between authentication and authorization, and between horizontal (ownership) and vertical (role) access control.
- Why foreign keys aren't enforced by default in SQLite, and how to verify a security control actually works rather than assuming it does.
- Why audit logging is a design problem in its own right (what to capture, what *not* to log, and how to keep it high-signal).

---

## Status

Actively in development. The baseline application is complete and functional; the vulnerability-research and hardening phases are next. Feedback welcome.
