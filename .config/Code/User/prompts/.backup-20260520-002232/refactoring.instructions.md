---
description: "Refactoring standards: chained branches, incremental commits, reviewable PRs, PR description formalism with metrics. For refactoring, restructuring, splitting modules, or reorganizing code across multiple files."
---

# Refactoring Guidelines

Refactoring: **reviewable by humans**. A large refactoring touching many files is very hard to review in single PR. Always split work into small, incremental, independently reviewable steps.

## Core Principles

- **Never mix refactoring with functional changes** → refactoring PRs: behavior-preserving
- **chained branches > single large branch** → each branch builds on previous one
- **Each PR should tell story** → reviewer should understand intent and verify correctness without needing full picture
- **Every intermediate state: green** → tests pass at each commit and each branch

## Prerequisite: Test Coverage Gate

**before refactoring begins, verify that existing test coverage is ≥ 90% on code being refactored.** If it's not:

1. **Stop** — do not start moving code
2. **Create dedicated first commit** in refactoring branch that adds missing tests to reach ≥ 90% coverage
3. This commit is **first commit of the PR** → it becomes safety net that guarantees refactoring is behavior-preserving
4. **Run `pre-commit run -a`** after this first commit → added tests must meet project's coding standards before refactoring begins
5. Only after coverage gate is met in that commit, proceed with refactoring commits

Without sufficient coverage, there is no way to prove that refactoring introduces no regression. Tests are proof → not "it looks right".

## Chained Branch Strategy

When refactoring spans many files or modules, split into chain of branches:

```
main
 └── refactor/step-1-extract-base
      └── refactor/step-2-move-logic
           └── refactor/step-3-cleanup-deps
                └── refactor/step-4-factorize-tests
```

### Rules for chaining
- Each branch has its own PR targeting previous branch (or main for first)
- Branch names follow pattern: `refactor/step-N-short-description`
- Each PR is small enough to review in one sitting (~300–500 lines changed max)
- Mention chain in each PR description with links to previous/next PRs
- Rebase chain when earlier PRs are merged

## Commit Discipline

- One logical move per commit (e.g., "move model X from module A to module B")
- Commit message format: `[REF] module_name: short description of the move`
- Never squash refactoring commits → step-by-step history IS review aid
- Each commit must leave codebase in working state (tests pass)

## PR Description Formalism

Every refactoring PR follow this structure. After each refactoring step, generate `PR<N>-comment.md` file at project root (e.g., `PR1-comment.md`, `PR2-comment.md`) containing full PR description below. This file serves as local record of the PR content before it's posted to remote.

Every refactoring PR follow this structure:

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

- **Starting commit SHA** in "Before" → allows reviewer to `git diff <start>..<end>` for full picture
- **Ending commit SHA** in "After" → marks exact state after the PR
- **Metrics table** → quantifies refactoring impact (complexity, LOC, dependencies)
- **Mermaid graphs** — visual before/after of module dependencies
- **Commit table** → each commit is reviewable unit with its purpose stated

## What Goes in Each PR Step

### Step 1 — Structural extraction
- Create new module/package skeleton (`__init__`, `__manifest__`, directory structure)
- Move models, fields, their associated views/security
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
- **No metrics** → "trust me, it's better" → always quantify improvement
- **Skipping dependency graph** → impossible to reason about module boundaries without it
