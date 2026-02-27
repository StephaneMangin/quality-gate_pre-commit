---
description: "Generic Odoo effort-estimation methodology — ideal developer-days, phase decomposition, risk separation, profile coefficients. Loaded when estimating an Odoo demand."
applyTo: "**"
---

# Odoo Effort Estimation — Generic Methodology

This file defines the **generic estimation contract** for any Odoo project. A
workspace skill (typically `demand_analysis`) declares the trigger keyword
(commonly `<USER ESTIMATE>`) and layers project-specific calibration on top.

---

## Pre-requisite: read the code first

**Never estimate without reading the impacted files.**

1. Identify the impacted modules/files from the demand.
2. Read the relevant files to validate scope hypotheses.
3. Only then produce the estimate.

Skipping this step produces unreliable totals. If the codebase is unknown, flag
it in assumptions.

---

## Unit & atomic phases

Estimates are expressed in **ideal developer-days** (focused work, no meetings,
no interruptions). One day = 8 hours of effective coding.

Split the demand into the atomic phases below. Skip a phase only if provably
out of scope, and state so explicitly.

| Phase                | What it covers                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Analysis             | Locate impacted modules, read existing code, validate hypotheses, extend vs. new addon         |
| Model                | Fields, computed/stored, constraints, ORM overrides (`create`, `write`, `unlink`)              |
| Business logic       | Methods, workflows, hooks (`@api.constrains`, `@api.onchange`, `@api.depends`)                 |
| Data                 | XML/CSV records, demo data, sequences, crons, server actions                                   |
| Security             | `ir.model.access.csv`, `ir.rule`, groups                                                       |
| Views & UI           | Form/tree/kanban/search views, widgets, JS/OWL components                                      |
| Tests (unit)         | `TransactionCase` / `HttpCase` — happy path, edge cases, error paths                           |
| Tests (UAT)          | Playwright scripts + MP4 artefacts (if the project has a UAT harness)                          |
| Quality gates        | `pre-commit run -a`, project test runner green, code review round-trip                         |
| Migration / data fix | Pre/post-init hooks, `migrations/<version>/` scripts if schema/data changes                    |

**Rules:**
1. Each phase line MUST include a short justification (what is done, why).
2. A 20% implicit buffer per phase covers minor unknowns. Do **not** double it.
3. Risks are listed **separately** — never folded into the main total.
4. Total = sum of phases only, rounded to 0.25 j.
5. Excluded by default (call out explicitly if requested): meetings, functional
   specification with client, deployment, end-user documentation, training,
   post-go-live support.

---

## Developer profile coefficients (default)

The reference estimate targets a **confirmed Odoo developer** (3–5 years of
Odoo experience, familiar with OCA conventions, `stock` / `sale` / `account`
core, ORM internals, and the project's tooling).

| Profile                                   | Coefficient  |
| ----------------------------------------- | ------------ |
| Junior (< 2 years Odoo)                   | × 1.8 – 2.2  |
| Confirmed (reference)                     | × 1.0        |
| Senior / expert                           | × 0.7 – 0.8  |

A workspace skill MAY narrow these ranges with project-specific calibration.

---

## Mandatory output format

The answer MUST contain exactly these four sections, in this order. No prose
before section 1.

### Section 1 — Hypotheses & open questions

Bullet list of every assumption made. Any blocking question shifting the total
by more than 0.5 j MUST be flagged as **"Question bloquante"** before the
breakdown table.

### Section 2 — Phase breakdown

```
| Phase | Task | Effort (j) |
|-------|------|------------|
| Analysis | ... | 0.5 |
| Model    | ... | 0.5 |
| ...      | ... | ... |
| **Total (confirmed)** | | **X.X j** |
```

Use only phases from the methodology table. Always include the total row in
bold.

### Section 3 — Risks (out of total)

```
| Risk | Trigger | Impact |
|------|---------|--------|
| Hypothesis X invalid | ... | +0.5 j |
```

Each risk MUST be actionable: name the trigger condition and the extra effort.

### Section 4 — Profile adjustment

```
| Profile | Coefficient | Adjusted total |
|---------|-------------|----------------|
| Junior | × 2.0 | X.X j |
| Confirmed (reference) | × 1.0 | **X.X j** |
| Senior / expert | × 0.75 | X.X j |
```

---

## Forbidden patterns

- Giving a single number without the phase breakdown.
- Folding risks into the main total.
- Omitting the profile adjustment table.
- Using hours instead of days (unless explicitly requested).
- Estimating before reading the impacted code.

---

## What this file does NOT contain

- The trigger keyword (defined per-project in a workspace skill).
- Project-specific phase examples (route rules, consigne, etc.).
- Calibrated profile coefficients per codebase.
- Test runner command (defined in `odoo-core.instructions.md` + workspace).

The workspace skill MAY override section 1's output language (e.g. French for
APL) — the rest of the methodology is invariant.
