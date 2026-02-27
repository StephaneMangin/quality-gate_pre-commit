# GitHub Copilot — Workspace Instructions for `odoo-apl`

> **Prerequisite:** the generic Odoo development contract is defined in
> `~/.config/Code/User/prompts/odoo-core.instructions.md` and is auto-loaded.
> This file carries ONLY the **APL delta** — project identity, exact commands,
> agent/skill mapping, and APL-specific conventions.

---

## APL project identity

- **Module prefix:** all custom addons MUST start with `apl_`.
- **Addons root:** `odoo/addons/` contains ~125 `apl_*` modules.
- **Integrations:** `apl_api_*` modules host FastAPI / GraphQL / Topmotive
  connectors.
- **UAT harness:** `uat_records/` (Playwright + page objects).

---

## APL test runner (concrete command)

The generic contract requires using a project test runner instead of bare
`pytest`. On APL the runner is **`odootest`**:

```bash
odootest -o <module_name>   # install/update module + run Odoo tests
odootest -p <module_name>   # re-run via pytest (faster, no reinstall)
```

This rule is absolute. No exception unless the user explicitly requests one.

---

## `<USER DEMAND>` mapping → APL agents

The 8-step workflow defined in `odoo-core.instructions.md` is orchestrated end
to end by the **`odoo-demand`** agent ([agents/odoo-demand.agent.md](./agents/odoo-demand.agent.md)).

Delegate via `runSubagent("odoo-demand", …)`. Step 3 of the workflow follows the
**two-layer delegation** pattern (generic OCA agent first, then APL delta):

| Step | Generic agent (`~/prompts`) | APL delta (`.github/agents`) |
|------|----------------------------|------------------------------|
| 3 — model | `odoo-model` | `apl-patterns` |
| 3 — view | `odoo-view` | — |
| 3 — wizard | `odoo-wizard` | — |
| 3 — security | `odoo-security` | — |
| 3 — data | `odoo-data` | — |
| 3 — report | `odoo-report` | — |
| 3 — API | _(direct APL)_ | `odoo-api` |
| 3 — migration | `odoo-migration` | — |
| 4 — tests | `odoo-test` | `apl-test` |
| 6 — pre-commit | `odoo-precommit` | — |
| 7 — review | `odoo-review` | `apl-review` |
| 8 — UAT video | _(direct APL)_ | `odoo-uat-records` |

---

## `<USER ESTIMATE>` mapping → APL skill

Generic estimation methodology lives in `~/.config/Code/User/prompts/odoo-estimate.instructions.md`
(always loaded). The APL delta lives in skill
[`demand_analysis`](./skills/demand_analysis/SKILL.md), which only carries:

- Calibrated profile coefficients for this codebase (junior × 2.0, senior × 0.75)
- APL-typical phase reminders (route rule, consigne, pricing chain, API exposure, Topmotive, UAT video)
- French output language for section headers

---

## `<USER REVIEW>` mapping → APL agents

Generic read-only audit contract lives in `odoo-core.instructions.md`.
On APL, the audit is run as a two-layer chain:

1. **`odoo-review`** (generic OCA / Python / security / tests)
2. **`apl-review`** (APL convention checklist — module prefix, route rule
   inheritance, consigne pattern, pricing chain, customer groups, UUID for
   API, `apl_api_*` auth)

Both are read-only. The orchestrator MUST NOT delegate to any agent that
edits files.

Verdict format: `COMPLIANT` only if both layers return clean. Any CRITICAL
finding from either blocks merge.

---

## `<USER REFACTOR>` mapping → APL agents

Generic refactor contract lives in `refactoring.instructions.md` + the
`<USER REFACTOR>` section of `odoo-core.instructions.md`. On APL:

- Orchestration is delegated to the **`odoo-demand`** agent in refactor mode
  (chained branches, no new feature, behaviour preserved).
- After each branch, run **`apl-review`** in addition to `odoo-review` to
  enforce APL conventions on the refactored code.
- Tests MUST go green via `odootest -p <module>` after each branch \(not only
  at the end\).

---

## `<USER FIX>` mapping → APL agents

Generic bug-fix contract lives in the `<USER FIX>` section of
`odoo-core.instructions.md`. On APL:

- Orchestration is delegated to the generic **`odoo-fix`** agent
  (`~/.config/Code/User/prompts/odoo-fix.agent.md`).
- Step 4 (tests) MUST use an **existing** test file of the impacted
  `apl_*` module. If none exists, the agent escalates to `<USER DEMAND>`.
- Step 5 (run tests) MUST use `odootest -p <module>`.
- Step 7 (review) follows the same 2-layer chain as `<USER REVIEW>`:
  `odoo-review` → `apl-review`.
- No UAT video unless the fix is visually demonstrable on an existing scenario.

---

## APL-specific MANDATORY rules

### API exposure
- Any model exposed via an `apl_api_*` route MUST carry a `uuid` field from
  `apl_base_uuid`.
- `apl_api_*` routes MUST authenticate via `auth_api_key`. No unauthenticated
  mutation routes.

### Stock routing
- New routing logic MUST extend `AplAbstractStockRouteRule` (from
  `apl_stock_route_rule`). Never duplicate route logic in a standalone class.

### Consigne flows
- Consigne return logic MUST extend `apl_sale_consigne` /
  `apl_rma_sale_consigne` patterns. Never add parallel fields on `sale.order`
  or `stock.picking`.

### Pricing chain
- Price computation MUST go through `apl_sale_line_price`. Never override
  `product.pricelist._compute_price_rule` or `_get_display_price` directly.

### Partner segmentation
- Customer groups use `apl_partner_customer_group` fields. Never add raw
  `Selection` fields on `res.partner` for segmentation.

### Topmotive integration
- Tests MUST mock the Topmotive connector. Never hit the real API in tests.

---

## Pointers

- Team overview & architecture: [README.md](./README.md)
- Interaction graphs: [workflow.mmd](./workflow.mmd) (compact),
  [workflow.interactions.mmd](./workflow.interactions.mmd) (storage view),
  [workflow.legacy.mmd](./workflow.legacy.mmd) (exhaustive)
- APL convention audit checklist: [agents/apl-review.agent.md](./agents/apl-review.agent.md)
