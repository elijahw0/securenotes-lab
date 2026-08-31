# Baseline Security Scan

Security assessment of the `baseline` branch of SecureNotes. This branch is the secure control that the `vulnerable` and `hardened` branches get compared against, so it gets scanned and fixed before any flaws are added on purpose.

**Scan date:** 2026-08-30

---

## Scope and environment

**Code:** `app.py`, `db.py`, `seed.py`, `get_tokens.py`. 284 lines at the initial scan. `venv/` was excluded from SAST since it is third-party code that dependency scanning already covers.

| Component | Version |
| --- | --- |
| Python | 3.14.0 |
| Bandit | 1.9.4 |
| pip-audit | 2.9.0 |
| Gitleaks | 8.30.1 |
| OWASP ZAP | `zaproxy/zap-stable` (Docker) |

Gitleaks and ZAP are not Python packages, so they are not in `requirements-dev.txt`. They have to be installed separately to reproduce this assessment.

| Run | Commit |
| --- | --- |
| Run 01 (before fixes) | `e5693d2` |
| Run 02 (after fixes) | `2a7bae3` |
| Dependency upgrades | `3f57a0c` |

**Method:** scan, give every finding a verdict, fix at the root cause, then rescan to confirm. Raw output for both runs is committed under `docs/scans/`.

Dependency scanning used the same two-pass structure. Gitleaks and ZAP were only run once because none of the fixes touched credentials, git history, or response handling, so a second run would return the same thing.

---

## Static analysis: Bandit

### Toolchain failure

The pinned version (1.8.6) crashed on all four files with `AttributeError: module 'ast' has no attribute 'Num'`. `ast.Num` was removed in Python 3.14 and Bandit 1.8.6 came out before that removal.

It still wrote a valid JSON report, containing zero findings and four errors. A CI job that only checks the finding count would read that as a clean scan. The pin kept the scanner frozen while the interpreter moved underneath it.

Upgraded to 1.9.4 and updated the pin. Every run after that was checked for zero parse errors before the results were used.

### Run 01: `e5693d2`

| Rule | Severity | Location | Verdict |
| --- | --- | --- | --- |
| B201 `flask_debug_true` | High | `app.py:290` | Fixed |
| B113 `request_without_timeout` | Medium | `get_tokens.py:7` | Fixed |
| B113 `request_without_timeout` | Medium | `get_tokens.py:13` | Fixed |
| B105 `hardcoded_password_string` | Low | `get_tokens.py:7` | Accepted |

**B201.** `debug=True` exposes the Werkzeug interactive debugger, which gives you a Python console when an exception goes unhandled. The PIN protection is built from predictable host attributes and has been bypassed in published research, so this counts as remote code execution. Moved it behind an environment variable so running it insecurely takes a deliberate opt-in:

```python
debug = os.environ.get("FLASK_DEBUG", "0") == "1"
```

Confirmed by checking out `e5693d2` and verifying the finding was there before the fix and gone after.

**B113 (x2).** Neither `requests` call had a timeout, so a request would block forever if the server accepted the connection and never answered. Added `timeout=10` to both. Fixing it took one argument, which was less work than writing up why I was accepting it.

**B105.** The literal `"password"` is the seeded credential that `seed.py` creates. It is lab data, not a production secret, and parameterizing it would make a local helper harder to use without making anything safer. Accepted and suppressed with the rule ID written out:

```python
# nosec B105 # seeded lab credential, matches seed.py; not a production secret
```

Bandit prints `nosec encountered (B105), but no failed test`, which reads like the suppression is pointless. I tested it by deleting the comment and rescanning, and B105 fired right away. The suppression is doing real work and the warning is misleading here. The footer count is what to trust.

### Run 02: `2a7bae3`

```
No issues identified.
Total lines of code: 286
Total potential issues skipped due to specifically being disabled: 1
```

Three fixed at the root cause and one accepted with a written reason, verified as still active.

---

## Dependencies: pip-audit

| Package | Version | Advisory | CVSS | Verdict |
| --- | --- | --- | --- | --- |
| requests | 2.32.5 | PYSEC-2026-2275 | 5.5 Medium | Upgraded to 2.34.2 |
| pytest | 8.4.2 | PYSEC-2026-1845 | 6.8 Medium | Upgraded to 9.1.1 |

**requests.** `extract_zipped_paths()` used a predictable temp filename and reused files that were already there without validating them. The advisory says only applications that call that function directly are affected. I checked with `grep` and there are no matches in this codebase, so the vulnerable path is never reached. Upgraded anyway since the fix landed in a minor release.

**pytest.** Predictable `/tmp/pytest-of-{user}` handling with a local-only attack vector. It is a dev dependency that does not run in the deployed container, and there was no test suite at the time of the assessment, so the vulnerable code never ran at all. The fix needed a major version bump from 8.4.2 to 9.1.1, which would be a real migration on a project that already had tests. It cost nothing here.

**Scope correction.** The `-r` audits only check the packages the requirements files declare. I ran a third audit against the active environment to cover the resolved tree (urllib3, certifi, Werkzeug, Jinja2) and it came back clean.

The run-01 pip-audit artifacts were rebuilt on 2026-08-30 from the requirements files as they were at `e5693d2`. They were not captured live. The findings match what I originally saw, but advisory databases change over time.

---

## Secrets: Gitleaks

```
35 commits scanned. no leaks found.
```

This walks the full commit history, not just the working tree. Two things I checked by hand since they would not show up in scanner output:

- `securenotes.db` is untracked, so the seeded database and its bcrypt hashes were never committed. Gitleaks would not flag a binary database file anyway.
- `.gitignore` covers `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, and `.DS_Store`.

---

## Dynamic analysis: OWASP ZAP

Ran `zap-baseline.py` from Docker against the app running on the host, reached through `host.docker.internal`. The app was temporarily bound to `0.0.0.0:5001` for the scan since port 5000 is taken by macOS AirPlay Receiver.

```
FAIL-NEW: 0   WARN-NEW: 4   PASS: 63
```

| Rule | Finding |
| --- | --- |
| 10036 | Server leaks version through the `Server` header |
| 10038 | CSP header not set |
| 10049 | Storable and cacheable content |
| 10063 | Permissions Policy header not set |

### Coverage limitation

```
Total of 3 URLs, all 404
Job spider error accessing URL ... status code returned : 404 expected 200
```

None of the application's 12 endpoints were tested. `zap-baseline.py` is a passive spider that follows links in HTML responses. This is a JSON API with no route at `/`, and the endpoints need POST requests with JSON bodies and Bearer tokens, which a spider cannot discover or build on its own.

The four findings above came from headers on 404 responses. They are still real, since those headers are missing from every response, but they describe the server's default behavior rather than the security posture of the API.

Authenticated API scanning is deferred to the `vulnerable` branch, where an OpenAPI definition will let `zap-api-scan.py` import the endpoint list, authenticate, and run active attacks.

---

## Limitations

**SAST cannot find authorization flaws.** Bandit matches syntax patterns and has no way to tell whether an endpoint checks that the caller owns the resource it is returning. Broken object-level authorization, which is the main flaw class this lab teaches, is invisible to it. The manual threat model covers what static analysis structurally cannot.

**DAST reached no application endpoints.** The dynamic testing in this baseline only amounts to response header analysis.

**A rule matching is not the same as a risk assessment.** B201 matched on the literal `debug=True`. Once the value came from an environment variable the rule stopped matching, even though the capability still exists behind an opt-in. The change is a real improvement, but the finding went away because the pattern changed.

**Tool output needed verifying.** Two cases here: a crashed scanner that reported zero findings, and a warning that said a suppression was unnecessary when it was not. Reading either at face value would have led to the wrong conclusion.

---

## Summary

| Tool | Findings | Fixed | Accepted | Outstanding |
| --- | --- | --- | --- | --- |
| Bandit | 4 | 3 | 1 | 0 |
| pip-audit | 2 | 2 | 0 | 0 |
| Gitleaks | 0 | n/a | n/a | 0 |
| ZAP | 4 | 0 | 0 | 4 |

The four ZAP header findings are still open. CSP and Permissions-Policy control browser behavior and this API is not browser-facing, so the practical risk is limited, but I am recording them as outstanding instead of dismissing them. They are candidates for the `hardened` branch.

The baseline works as a secure control. The bigger issue is coverage rather than findings, since no authenticated dynamic testing happened and static analysis cannot evaluate the authorization logic this lab is built to demonstrate.

**Next:** write an OpenAPI 3.0 spec for all 12 endpoints so `zap-api-scan.py` can authenticate and scan the actual API surface.
