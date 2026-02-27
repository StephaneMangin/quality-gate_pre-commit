---
description: "Python development standards: PEP 8, type hints, f-strings, pathlib, logging, pytest, ruff, mypy, async patterns. For Python files."
applyTo: "**/*.py"
---

# Python Development Standards

## Language & Style

- Target Python 3.10+ unless project constraints dictate otherwise.
- Follow PEP 8.
- Use type hints on every function signature, return type, and complex data structure.
- f-strings > `.format()` or `%` formatting.
- Use `pathlib` over `os.path` for filesystem operations.
- Prefer context managers (`with`) for resource management.
- Use `dataclasses` (or `attrs` / Pydantic when validation is needed) for value objects.
- Use the `logging` module — never `print()` for diagnostics.

## Dependencies

- Always work inside a virtual environment (`venv`, `virtualenv`, `uv`, …).
- Pin dependencies with exact versions in lock files.
- Audit transitive dependencies before adding a new one.

## Linting & formatting

- `ruff` is the canonical linter and formatter. No `flake8` / `pylint` / `black` / `isort` parallel configs.
- `ruff check` and `ruff format` MUST pass before any commit.
- Configure per-file ignores explicitly in `pyproject.toml`; no inline `# noqa` without a reason after it.

## Type checking

- `mypy` (or `pyright`) MUST run on the project. New code SHOULD be fully typed.
- Use `from __future__ import annotations` to keep runtime cost low.
- `Any` is a code smell — use it only at clearly documented boundaries.
- Use `Protocol` for structural typing instead of inheritance hierarchies when only a method signature is needed.

## Testing (pytest)

- `pytest` is the runner. Tests live under `tests/` or alongside modules in a `_test.py` file (project convention).
- One test = one observable behaviour. Test method names describe the behaviour, not the implementation.
- Use fixtures for shared setup; avoid `setUp/tearDown` style unless inheriting from a framework class (e.g. Odoo `TransactionCase`).
- Mark slow / network / integration tests with `@pytest.mark.slow` and exclude them from the default run.
- Mock external dependencies via `unittest.mock` or `pytest-mock`. Never hit the network in unit tests.
- Parametrize repetitive tests with `@pytest.mark.parametrize`.
- Assertions: prefer plain `assert` over `unittest`-style methods. Use `pytest.raises` for expected exceptions.

## Async

- Async code uses `async def` + `await`. Never call `asyncio.run` inside a coroutine.
- Use `anyio` when you need to support both `asyncio` and `trio`.
- Don't mix sync I/O inside async functions — offload via `asyncio.to_thread` or a thread pool.
- Cancel tasks explicitly; use `asyncio.TaskGroup` (3.11+) when you need structured concurrency.

## Error handling

- Catch specific exceptions only. `except Exception:` is acceptable at process boundaries (CLI entrypoints, request handlers) only with a re-raise or a log + re-raise.
- Never bare `except:`.
- Raise custom exceptions for domain errors; avoid using built-in `ValueError`/`RuntimeError` as a catch-all.
- Use `raise ... from ...` to preserve cause when re-raising.

## Imports

- Order: standard library → third-party → first-party (project) → relative.
- One import per line.
- Avoid wildcard imports (`from x import *`).
- Use `TYPE_CHECKING` guards for imports needed only for typing.

## Performance

- Mind algorithmic complexity before micro-optimising.
- Profile before optimising (`cProfile`, `py-spy`, `scalene`).
- Generators / iterators for large data — don't materialise lists unless needed.
- `functools.lru_cache` for pure functions with hashable args.

## Security

- Never `eval` / `exec` user input.
- Parameterised queries only — never f-string SQL.
- Validate inputs at the boundary (Pydantic, marshmallow, custom validators).
- Use `secrets` module for tokens / passwords, never `random`.
- Don't log secrets, API keys, PII.
