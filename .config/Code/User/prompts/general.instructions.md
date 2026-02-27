---
description: "Core software engineering principles: code quality, testing, security, performance, error handling, documentation. Always active."
applyTo: "**"
---

# Top priority: human readability and long-term maintainability.

Always produce code that is clean, well-tested, secure, production-grade.
Follow the principle of least surprise. Simplicity > cleverness.
When in doubt between compact and readable code: choose readable.

## Mandatory design rules

1. One function = one main responsibility.
2. Orchestration functions delegate to helpers named by intent (`collect_*`, `build_*`, `normalize_*`, `validate_*`).
3. Avoid compact comprehensions/expressions when they hide intent.
4. Prefer explicit intermediate variables over compaction.
5. For complex payloads: build by named sub-sections before final assembly.

## Complexity thresholds

- Max 30 lines per function (excluding short docstring).
- Max 3 levels of nesting — use early returns, guard clauses, or extract helpers.
- Max 5 logical blocks in a single function.
- Max 3–4 parameters per function; group related arguments in dataclasses.
- Cyclomatic complexity ≤ 10 per function; refactor if higher.
- File length ≤ 300–400 lines; split into focused modules when larger.
- If an `if/for/try` combines data transformation + I/O + mapping, split immediately.

## Readability conventions

- Self-documenting code with meaningful names for variables, functions, classes, modules.
- Use business vocabulary for helpers, not technical jargon.
- No abbreviations unless universally understood.
- One concept per line; avoid chaining too many operations in a single expression.
- Flat code > deeply nested conditionals (invert conditions, return early).
- Optimize for reading, not writing — code is read 10× more than it is written.

## Comments and docstrings

- Write comments explaining **why**, not **what**.
- Add a short "why" comment only for non-obvious decisions.
- Docstrings: one sentence of intent, then a note **only** for non-obvious invariants (edge case, counter-intuitive side effect, implicit business constraint).
- Forbidden in docstrings:
  - Paraphrasing the function body (a list of "Rules:" describing each branch).
  - Repeating types/names of parameters already visible in the signature.
  - Documenting what the function name and code already say.
- If a docstring only describes the flow: remove it.

## Imports

- Import order: stdlib → third-party → odoo core → odoo addons → local.
- No complex implicit imports without justification. If using a deferred import, comment the reason (cycle, optional deps, startup cost).

## Composition and coupling

- Composition > inheritance when appropriate.
- Reduce coupling between modules — depend on abstractions, not concrete implementations.
- Keep public API surface small — expose only what is needed.
- Remove dead code; don't comment it out.

## Version control

- Clear, descriptive commit messages following conventional commits when applicable.
- Atomic commits — one logical change per commit.
- Feature branches and pull requests for code review.
- Never commit secrets, credentials, or sensitive data.

## Testing

- Write tests before or alongside implementation (TDD/BDD when practical).
- Cover happy paths, edge cases, error conditions.
- Tests: isolated, repeatable, deterministic.
- Descriptive test names documenting expected behavior.
- Mock external dependencies; never rely on network or third-party services in unit tests.

## Security

- Validate and sanitize all external inputs (user input, API responses, file contents).
- Never trust client-side data.
- Parameterized queries — never concatenate user input into SQL.
- Principle of least privilege for access control.
- Keep dependencies up to date and audit for known vulnerabilities.
- Never log or expose sensitive data (passwords, tokens, PII).

## Performance

- Mind algorithmic complexity (O notation).
- Avoid N+1 query patterns in ORM/database interactions.
- Pagination for large datasets.
- Prefer lazy evaluation and streaming for large data processing.
- Cache expensive computations when data is stable.

## Error handling

- Fail fast and fail loud — don't silently swallow errors.
- Use specific exception types, never bare `except:`.
- Actionable error messages.
- Log errors with enough context to debug without reproducing.

## Documentation

- Document public APIs, complex business logic, non-obvious decisions.
- Keep documentation close to code (docstrings, README).
- Update documentation when changing behavior.

## Mandatory post-refactor validation

- Guarantee unchanged behavior.
- Run repo quality gates (`pytest`, `pre-commit run -a`) after modifications.
- In your reply, explain: what was extracted, why, and how behavior is preserved.

## Compact vs. readable

If you propose a compact version, also automatically provide a readable step-by-step version, then apply the readable one by default.

## Language

All code, comments, identifiers, docstrings, and log messages MUST be written in English. Never use French (or any other non-English language) in code artefacts.
