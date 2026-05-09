# Code Review: Issue #2 Backend Runtime, Settings, and Validation Tools

**Scope**: Uncommitted implementation for GitHub Issue #2
**Recommendation**: APPROVE

## Summary

Reviewed the backend scaffold for STORY-002: project metadata, FastAPI app and `/health`, Pydantic settings, Alembic/SQLAlchemy skeleton, scheduler placeholder, tests, docs, plan archive, and implementation report. The prior Python runtime mismatch has been fixed: the project now pins Python 3.12 and validation runs under Python 3.12.13.

## Issues Found

### Critical

None.

### High Priority

None.

### Medium Priority

None.

### Suggestions

None.

## Validation Results

| Check | Status |
|-------|--------|
| Python Runtime | PASS: `uv run python --version` reports `Python 3.12.13` |
| Dependency sync | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv sync` |
| Lint | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff check .` |
| Format | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff format --check .` |
| Type Check | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run mypy .` |
| Tests | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run pytest` (`6 passed`) |
| Diff Check | PASS: `git diff --check` |
| Frontend Build | SKIPPED: no frontend scaffold or `package.json` exists yet |

## What's Good

- The FastAPI app imports cleanly without provider or database calls.
- The health endpoint returns only non-secret operational metadata and is covered by tests.
- Settings are typed, environment-driven, and include timezone validation plus secret masking coverage.
- The scheduler placeholder makes the documented command runnable before jobs exist.
- README and `.env.example` now describe the backend scaffold clearly and preserve the educational-use framing.

## Recommendation

Approve. The runtime pinning issue is resolved and the backend validation remains green.

---

## Follow-up Review: Current Unstaged Changes

**Scope**: Full current unstaged worktree after Python 3.12 pin fix
**Recommendation**: APPROVE

### New Issues Found

#### Medium Priority

1. **`app/main.py:9` and `app/api/dependencies.py:6`**
   - Error: `create_app(settings=...)` does not actually use the provided settings for request handling. It only uses `resolved_settings` for FastAPI metadata, while `/health` still depends on `get_app_settings()`, which returns the global cached environment settings. A direct smoke check with `create_app(Settings(environment="test", timezone="UTC", ...))` returned `environment: "local"` and `timezone: "America/New_York"`.
   - Likely cause: The app factory accepts a `Settings` object, but the dependency layer is not wired to read app-scoped settings.
   - Fix: Store `resolved_settings` on `application.state.settings` and update `get_app_settings` to read from `Request.app.state.settings`, or set a dependency override inside `create_app()` so routes consistently use the factory-provided settings. Add a test that `TestClient(create_app(test_settings)).get("/health")` returns the injected environment/timezone without needing a manual dependency override.
   - Resolution: Fixed by storing settings on `application.state.settings`, reading those settings from the FastAPI `Request`, removing the test-only dependency override, and adding a regression test for factory-injected settings. The direct smoke check now returns `app_name: "InjectedApp"`, `environment: "test"`, `timezone: "UTC"`, and `market_data_provider: "test-provider"`.

### Validation Results

| Check | Status |
|-------|--------|
| Python Runtime | PASS: `uv run python --version` reports `Python 3.12.13` |
| Lint | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff check .` |
| Format | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff format --check .` |
| Type Check | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run mypy .` |
| Tests | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run pytest` (`6 passed`) |
| Diff Check | PASS: `git diff --check` |

### Fix Validation Results

| Check | Status |
|-------|--------|
| Python Runtime | PASS: `uv run python --version` reports `Python 3.12.13` |
| Lint | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff check .` |
| Format | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff format --check .` |
| Type Check | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run mypy .` |
| Tests | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run pytest` (`7 passed`) |
| Scheduler | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run python -m app.jobs.scheduler` |
| Direct Smoke | PASS: `create_app(custom_settings)` returns custom settings from `/health` |
| Diff Check | PASS: `git diff --check` |

---

## Final Review: Current Unstaged Changes

**Scope**: Full current unstaged worktree for GitHub Issue #2
**Recommendation**: APPROVE

### Issues Found

#### Critical

None.

#### High Priority

None.

#### Medium Priority

None.

#### Suggestions

None.

### Validation Results

| Check | Status |
|-------|--------|
| Dependency sync | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv sync` |
| Python Runtime | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run python --version` reports `Python 3.12.13` |
| Lint | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff check .` |
| Format | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run ruff format --check .` |
| Type Check | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run mypy .` |
| Tests | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run pytest` (`7 passed`) |
| Scheduler | PASS: `UV_CACHE_DIR=/private/tmp/nookscout-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/nookscout-uv-python uv run python -m app.jobs.scheduler` |
| Direct Smoke | PASS: `create_app(custom_settings)` returns custom settings from `/health` |
| Diff Check | PASS: `git diff --check` |
| Frontend Build | SKIPPED: no frontend scaffold or `package.json` exists yet |

### Summary

The current unstaged issue #2 scaffold satisfies the story acceptance criteria: Python 3.12 is pinned, the FastAPI app exposes a typed health endpoint without provider/database calls on import, settings are typed and environment-driven, documentation is updated, and backend validation passes. No remaining review blockers were found.
