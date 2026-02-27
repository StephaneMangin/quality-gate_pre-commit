---
description: "Refactoring standards: chained branches, incremental commits, reviewable PRs, PR description formalism with metrics. Use when refactoring, restructuring, splitting modules, or reorganizing code across multiple files."
---

# Refactoring Guidelines

Refactoring must be **reviewable by humans**. A large refactoring touching many files is nearly impossible to review in a single PR. Always split the work into small, incremental, independently reviewable steps.

## Core Principles

- **Never mix refactoring with functional changes** — refactoring PRs must be behavior-preserving
- **Prefer chained branches over a single large branch** — each branch builds on the previous one
- **Each PR should tell a story** — a reviewer should understand the intent and verify correctness without needing the full picture
- **Every intermediate state must be green** — tests pass at each commit and each branch

## Prerequisite: Test Coverage Gate

**Before any refactoring begins, verify that existing test coverage is ≥ 90% on the code being refactored.** If it is not:

1. **Stop** — do not start moving code
2. **Create a dedicated first commit** in the refactoring branch that adds missing tests to reach ≥ 90% coverage
3. This commit is the **first commit of the PR** — it becomes the safety net that guarantees the refactoring is behavior-preserving
4. **Run `pre-commit run -a`** after this first commit — the added tests must meet the project's coding standards before any refactoring begins
5. Only after the coverage gate is met in that commit, proceed with the refactoring commits

Without sufficient coverage, there is no way to prove that a refactoring introduces no regression. Tests are the proof — not "it looks right".

## Chained Branch Strategy

When a refactoring spans many files or modules, split into a chain of branches:

```
main
 └── refactor/step-1-extract-base
      └── refactor/step-2-move-logic
           └── refactor/step-3-cleanup-deps
                └── refactor/step-4-factorize-tests
```

### Rules for chaining
- Each branch has its own PR targeting the previous branch (or main for the first)
- Branch names follow the pattern: `refactor/step-N-short-description`
- Each PR is small enough to review in one sitting (~300–500 lines changed max)
- Mention the chain in each PR description with links to previous/next PRs
- Rebase the chain when earlier PRs are merged

## Commit Discipline

- One logical move per commit (e.g., "move model X from module A to module B")
- Commit message format: `[REF] module_name: short description of the move`
- Never squash refactoring commits — the step-by-step history IS the review aid
- Each commit must leave the codebase in a working state (tests pass)

## PR Description Formalism

Every refactoring PR must follow this structure. After each refactoring step, generate a `PR<N>-comment.md` file at the project root (e.g., `PR1-comment.md`, `PR2-comment.md`) containing the full PR description below. This file serves as a local record of the PR content before it is posted to the remote.

Every refactoring PR must follow this structure:

```markdown
## :dart: Goal

> One-sentence summary of what this refactoring step achieves.

### Issues

refs #XXXX (or fixes #XXXX for the final step)

## Before / After Diagram

<details>
<summary>Module dependencies</summary>

**Before** (N modules — `<starting commit SHA>`) :

(Mermaid dependency graph showing the state BEFORE this PR)

**After** (M modules — `<ending commit SHA>`) :

(Mermaid dependency graph showing the state AFTER this PR)

> **Legend:** ━━ thick border = module added | ┄┄ dashed border = module removed

</details>

## Metrics

| State | Module | CC | CC max | LOC py | LOC xml | Deps |
|-------|--------|----|--------|--------|---------|------|
| **Before** | ... | ... | ... | ... | ... | ... |
| **After** | ... | ... | ... | ... | ... | ... |
| | **Δ** | ... | ... | ... | ... | — |

> Commentary on overhead, complexity reduction, and dependency changes.

<details>
<summary>Detailed contents per module</summary>

**module_name** — Role description

- List of moved/added/removed elements
- Depends: `dep1`, `dep2`, ...

</details>

## Commits

| \# | SHA | Summary | Impact |
|----|-----|---------|--------|
| 1 | `abc1234` | [REF] module: description | Structure |
| 2 | `def5678` | [REF] module: description | Logic + Tests |

## Checks

- [ ] XX tests passed (add a bit of context about what was tested very briefly)
- [ ] No functional change (code movement only if so otherwize, verified by tests)
- [ ] No new external dependency introduced
```

### Key elements

- **Starting commit SHA** in "Before" — allows the reviewer to `git diff <start>..<end>` for the full picture
- **Ending commit SHA** in "After" — marks the exact state after the PR
- **Metrics table** — quantifies the refactoring impact (complexity, LOC, dependencies)
- **Mermaid graphs** — visual before/after of module dependencies
- **Commit table** — each commit is a reviewable unit with its purpose stated

## What Goes in Each PR Step

### Step 1 — Structural extraction
- Create new module/package skeleton (`__init__`, `__manifest__`, directory structure)
- Move models, fields, and their associated views/security
- Migration hooks if needed
- **Impact:** Structure only

### Step 2 — Logic migration
- Move business logic methods, overrides, computed fields
- Move associated tests
- Update imports and dependencies
- **Impact:** Logic + Tests

### Step 3 — Dependency cleanup
- Remove unused dependencies from manifests
- Absorb deprecated/satellite modules
- Update downstream module references
- **Impact:** Dependencies

### Step 4 — Test factorization
- Create shared `common.py` test base classes
- Factorize duplicated test data setup across modules
- Extract reusable test helpers
- Remove redundant test files
- **Impact:** Tests

## Metrics to Track

Always measure and report before/after for each PR step:

| Metric | Description |
|--------|-------------|
| **CC** | Total cyclomatic complexity per module |
| **CC max** | Highest single-function complexity with grade (A ≤ 5, B ≤ 10, C ≤ 15, D > 15) |
| **LOC py** | Lines of Python code |
| **LOC js** | Lines of JavaScript code |
| **LOC xml** | Lines of XML (views, data, security) |
| **Deps** | Number of direct module dependencies |
| **Test count** | Number of test methods |
| **Coverage** | Test coverage percentage |

## Anti-Patterns

- **Big bang refactoring** — one PR with 50+ files changed → unreadable, unreviewable
- **Mixing refactoring and features** — "while I'm here, let me also add..." → split it
- **Breaking intermediate commits** — reviewer can't `git bisect` or verify step by step
- **No metrics** — "trust me, it's better" → always quantify the improvement
- **Skipping the dependency graph** — impossible to reason about module boundaries without it
