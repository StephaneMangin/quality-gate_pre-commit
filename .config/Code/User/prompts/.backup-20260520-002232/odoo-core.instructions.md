---
description: "Generic Odoo development core rules — mandatory workflow, test command pattern, pre-commit, demand resolution patterns. Always active across all Odoo projects."
applyTo: "**"
---

# Odoo Core — Generic Rules (cross-project)

This file defines the **generic Odoo development contract** shared by every Odoo
project. Workspace-level `.github/copilot-instructions.md` extends it with
project-specific commands, agents, and conventions.

> If you maintain multiple Odoo projects, copy or symlink this file once and
> never duplicate its content per project. The per-project workspace file should
> only carry the **delta**.

---

## MANDATORY: Always load companion instructions

Before any task, load:

- `general.instructions.md` — Core engineering principles
- `python.instructions.md` — Python conventions (for `.py` files)
- `odoo.instructions.md` — OCA module structure (auto-loaded on `__manifest__.py`)

Conditional (load when matching files are touched):

| Instruction file | Triggers on |
| ---------------- | ----------- |
| `database.instructions.md` | `.sql`, `.migration` |
| `docker-devops.instructions.md` | `Dockerfile`, `docker-compose*.yml` |
| `javascript.instructions.md` | `.js`, `.ts`, `.jsx`, `.tsx` |
| `web-frontend.instructions.md` | `.html`, `.css`, `.scss`, `.vue` |
| `rest-api.instructions.md` | API endpoints, routes, controllers |
| `ui-uat-records.instructions.md` | `UAT/` test files |
| `refactoring.instructions.md` | refactoring tasks |
| `git.instructions.md` | git operations |
| `pattern.instructions.md` | architecture decisions |

---

## MANDATORY: Test execution pattern

**NEVER** use bare `pytest`, `python -m pytest`, or `odoo --test-enable`. Every
Odoo project provides a **dedicated test runner** that handles DB setup, module
install/update, and test isolation. Use that runner exclusively.

The exact command is defined per-project in `.github/copilot-instructions.md`
(common pattern: `<test-runner> -o <module>` for install+test, `<test-runner>
-p <module>` for pytest re-run).

---

## MANDATORY: Pre-commit before any commit

Run `pre-commit run -a` after any code change. Never bypass with `--no-verify`.

---

## MANDATORY: Code quality thresholds

Inherited from `general.instructions.md`:

- Max 30 lines per function (excluding short docstring)
- Max 3 nesting levels
- Max 5 logical blocks per function
- One function = one responsibility
- Orchestration functions delegate to named helpers
- Prefer readable, explicit code over compact/clever code

---

## Demand-resolution patterns

These are **generic workflows triggered by special keywords**. Each project maps
the keyword to a concrete agent or skill in its workspace
`.github/copilot-instructions.md`. The workflow described here is the
**contract** — projects may extend it with extra steps, never remove a step.

### `<USER DEMAND>` — full development workflow

When the user prefixes a request with `<USER DEMAND>`, execute the following
ordered workflow:

1. **Analyse** — locate impacted files, modules, dependencies.
2. **Apply instructions** — for each impacted file type, load the matching
   `*.instructions.md` (or default to `general.instructions.md`).
3. **Implement** — code the change, respecting all quality thresholds.
4. **Tests** — write/update tests (happy path, edge cases, errors, access rights).
5. **Run tests** — via the project test runner. Fix code, not tests.
6. **Pre-commit** — `pre-commit run -a` until clean.
7. **Review** — apply OCA + project-specific checklist. Block on CRITICAL.
8. **UAT video** — produce an MP4 evidence via the project UAT harness.
   **Mandatory when the workspace declares a UAT harness** (e.g. `uat_records/`
   present). Optional only when the project explicitly has no UAT harness.
   The workspace file is the single source of truth — never skip this step
   based on this generic label alone.

The workspace file specifies which agent orchestrates each step. The default
mapping (when no project agent is declared) is: do the steps inline.

### `<USER ESTIMATE>` — effort estimation

When the user prefixes a request with `<USER ESTIMATE>`, run an estimation
procedure that produces:

- **Hypotheses & open questions** (assumptions, blocking questions)
- **Phase breakdown** (in ideal developer-days) covering at least: Analysis,
  Model, Business logic, Data, Security, Views, Tests (unit), Tests (UAT),
  Quality gates, Migration. Each phase has a short justification.
- **Risks** (separate from total) — actionable trigger + extra effort.
- **Profile coefficients** — junior / confirmed / senior multipliers.

The workspace file specifies which skill or sub-agent handles the procedure.

### `<USER REVIEW>` — read-only audit

When the user prefixes a request with `<USER REVIEW>`, perform a **read-only**
audit of the targeted code (file, module, branch, or MR).

**Hard constraint:** do NOT modify any file. No edits, no auto-fix, no commit.
If a fix is needed, describe it; do not apply it. Switching to implementation
requires a separate `<USER DEMAND>`.

The audit MUST cover:

- OCA conventions (manifest, module structure, naming, `_()` wrapping)
- Python quality (function size, nesting, complexity, `general.instructions.md`)
- Security (access rights, record rules, `sudo()` justification, SQL injection)
- Tests (coverage of happy path, edges, errors, access rights)
- Project-specific conventions (defined in the workspace file)

Output format: findings grouped by severity (CRITICAL / WARNING / INFO) with
file + line references. End with a verdict: COMPLIANT / VIOLATIONS-FOUND.

The workspace file specifies which agent(s) perform the audit.

### `<USER REFACTOR>` — incremental refactoring

When the user prefixes a request with `<USER REFACTOR>`, follow
`refactoring.instructions.md` strictly:

- Chained branches (one logical step per branch)
- Atomic commits with conventional messages
- Each PR independently reviewable
- PR description carries metrics (LOC delta, complexity delta, affected files)
- Behaviour MUST be preserved — run tests after each step

**Hard constraint:** never collapse multiple refactor steps into a single
commit/PR. If the scope is too large, decompose further.

The workspace file specifies which agent orchestrates the chained workflow
(commonly the same Tech Lead agent as `<USER DEMAND>`, with refactor mode on).

### `<USER FIX>` — bug fix on existing code only

When the user prefixes a request with `<USER FIX>`, apply a **bounded bug fix
on already-existing code**. This is NOT a feature-development workflow.

**Hard constraints:**

- ONLY edit files that already exist. No new files (no new module, no new
  Python file, no new XML view, no new test file).
- ONLY add new declarations (fields, methods, views, records) if the existing
  file is their natural home AND the fix cannot be expressed otherwise.
  Prefer modifying the existing logic over introducing new constructs.
- Behaviour change is limited to **the bug described**. No drive-by refactor,
  no opportunistic cleanup, no scope creep.
- Add/update tests in **existing test files** to cover the regression.
  If the module has no test file at all, state it and stop — escalate to
  `<USER DEMAND>` instead of creating one.

The workflow is the short version of `<USER DEMAND>`:

1. Reproduce / locate the buggy path.
2. Apply the minimal patch in existing files.
3. Update the existing test(s) to cover the regression.
4. Run the project test runner — must be green.
5. Run `pre-commit run -a` — must be clean.
6. Apply review checklist (generic + project).

Skip steps that don't apply to existing-code edits (no UAT video unless the
fix is visually demonstrable on a known scenario).

The workspace file specifies which agent handles `<USER FIX>`.

---

## Agent delegation pattern

A project's AI team typically has **two layers**:

1. **Generic Odoo agents** (this `~/.config/Code/User/prompts/` directory) —
   OCA conventions, universal patterns.
2. **Project-specific agents** (project `.github/agents/`) — project conventions,
   custom prefixes, integration patterns.

**Rule:** never invoke a project-specific agent in isolation. The orchestrator
(typically a Tech Lead agent declared in the workspace file) invokes the generic
agent first, then the project delta on top.

---

## Convention checks (universal)

Regardless of project:

- Module prefix follows project naming convention (defined per-project).
- `__manifest__.py` carries all required OCA fields.
- `_()` wraps user-facing strings.
- No bare `except:`.
- `@api.depends` lists all dependencies explicitly.
- `sudo()` usage is justified by a short `# why` comment.
- No N+1 patterns (search/browse in loops).

### License compatibility — MANDATORY before creating any module

Before writing a single line of code, determine the license of every direct
dependency. Apply the following rules:

- `AGPL-3` module: all dependencies must be `AGPL-3` or `LGPL-3`. Any
  proprietary or OEEL dependency is a **blocker** — stop and escalate.
- `LGPL-3` module: dependencies must be `LGPL-3` or other LGPL-compatible
  open-source licenses. Never depend on AGPL or proprietary.
- `OEEL-1` module: may depend on Odoo Enterprise (OEEL) and LGPL modules.
  MUST NOT depend on any AGPL module — even transitively.

#### When a feature requires both an AGPL and an OEEL dependency

The ONLY valid architecture is three modules. Creating a single module that
lists both an AGPL and an OEEL dependency is a license violation — never do it.

**Module 1 — AGPL side** (`*_feature`, license: `AGPL-3`): depends on the
OCA/AGPL module only. No knowledge of the OEEL module.

**Module 2 — OEEL side** (`*_feature_ee`, license: `OEEL-1`): depends on the
Enterprise/OEEL module only. MUST NOT list the AGPL module in `depends`.

**Module 3 — Glue** (`*_feature_glue`, license: `AGPL-3`): lists both
`*_feature` and `*_feature_ee` in `depends`, sets `auto_install: True`.
Installs automatically when both are present. This is the sole coordination
point. It is contaminated AGPL — acceptable for internal use only.

```
OCA (AGPL) ──▶ apl_feature (AGPL) ──▶ apl_feature_glue (AGPL, auto_install)
                                                  ▲
ENT (OEEL) ──▶ apl_feature_ee (OEEL) ────────────┘
```

If the split cannot be achieved cleanly: either drop the OEEL dependency (go
full AGPL), or extract a fourth `LGPL-3` core module that both sides can safely
depend on.

---

## What this file does NOT contain

- Exact test runner command (`odootest -o`, `oca-port`, `runbot.sh`, …)
- Project module prefix (`apl_`, `acsone_`, `oca_`, …)
- Concrete agent/skill names (those map keywords to actual `.agent.md`)
- Project-specific business patterns (route rules, pricing chains, custom flows)

All of those live in the workspace `.github/copilot-instructions.md`.
