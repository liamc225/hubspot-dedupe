# CLAUDE.md — Project Guardrails

## Project Overview

This project is a deterministic deduplication system for HubSpot exports. It helps RevOps and GTM engineering teams identify duplicate contacts and companies, explain why records were matched, and recommend the best surviving record before merges are executed.

## Tech Stack

| Area | Choice |
| --- | --- |
| Language & Runtime | Python 3.9 |
| Package Manager | pip-compatible `pyproject.toml` project, no external runtime dependencies |
| Framework | None |
| Testing Framework | Pytest |
| Linting & Formatting | Keep code `ruff`-compatible; no formatter dependency wired yet |
| Type Checking | Standard-library typing with compile checks |
| Persistence | None for MVP; CSV in, JSON/Markdown out |
| Monorepo | Single package |
| Pre-commit Hooks | Not yet configured |

## Golden Reference

Before writing new feature code, study the reference implementation in `src/_golden/`.
This is the canonical example of how code in this project should be structured.
It demonstrates file naming, module structure, explicit typing, deterministic behavior,
and test naming conventions.

## TDD Protocol (MANDATORY)

You MUST follow Red-Green-Refactor for all code changes:
1. RED: Write a failing test that describes the behavior.
2. RUN: Execute the test and confirm it fails.
3. GREEN: Write the minimum code required to pass.
4. RUN: Execute the test and confirm it passes.
5. REFACTOR: Improve the code while keeping tests green.

## Commands

- Run all tests: `PYTHONPATH=src pytest`
- Run single test: `PYTHONPATH=src pytest tests/test_engine.py -k "contacts"`
- Type check: `python3 -m py_compile src/hubspot_dedupe/*.py src/_golden/*.py`
- Lint: `python3 -m compileall src tests`
- Format: no formatter is wired yet
- Full check (CI-like): `python3 -m py_compile src/hubspot_dedupe/*.py src/_golden/*.py && PYTHONPATH=src pytest`

## Code Style

- Use explicit types on public functions and dataclasses.
- Keep scoring rules deterministic and explainable.
- Prefer pure functions for normalization and scoring.
- Do not swallow parsing errors silently; surface the bad input clearly.

### Code Style Examples

```python
def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip().lower()
    if not candidate:
        return None
    return candidate
```

```python
def test_select_master_prefers_more_complete_record() -> None:
    primary = make_contact(record_id="1", email="a@example.com", phone="3125550101")
    secondary = make_contact(record_id="2", email="a@example.com")

    cluster = build_cluster([primary, secondary], pair_matches=[])

    assert cluster.master_record.record_id == "1"
```

```python
def require_header(row: dict[str, str], header: str) -> str:
    value = row.get(header, "").strip()
    if not value:
        raise ValueError(f"Missing required header: {header}")
    return value
```

## Git Conventions

- Never commit directly to `main`.
- Branch names must start with `feat/`, `fix/`, `chore/`, `refactor/`, `test/`, or `docs/`.
- Use conventional commits.
- Run the full check command before committing.

## Parallel Agent Protocol

### Scope Discipline

- Check `SCOPE.md` in your worktree root.
- Never modify files outside your declared scope.

### Shared Interfaces

- Shared interfaces live in `src/hubspot_dedupe/models.py`.
- Do not make broad schema changes without user approval.

### Conflict Prevention

- Prefer new modules over large edits to shared logic.
- Keep CLI changes in `src/hubspot_dedupe/cli.py`.
- Keep scoring changes in `src/hubspot_dedupe/scoring.py`.

## Project Structure

```text
src/
  _golden/
  hubspot_dedupe/
tests/
scripts/
data/
worktrees/
```

