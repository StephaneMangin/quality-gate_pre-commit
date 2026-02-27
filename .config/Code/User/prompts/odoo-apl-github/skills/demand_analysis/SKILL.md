---
name: demand_analysis
description: "Use when: estimating effort for an APL change, demand sizing, chiffrage, ideal developer days, phase decomposition, risk assessment, profile adjustment. Keywords: estimate, estimation, effort, chiffrage, demand, sizing, days, phases, risks, junior, senior, USER ESTIMATE."
argument-hint: "Feature or change to estimate (e.g. add stock route validation)"
---

# Demand Analysis — APL Delta

> The generic estimation methodology lives in
> `~/.config/Code/User/prompts/odoo-estimate.instructions.md` (always loaded).
> This skill ONLY carries the APL-specific calibration and trigger.

## Trigger

Activate on `<USER ESTIMATE>` or any of: "estimate", "chiffrage",
"combien de jours", "sizing", "effort".

## APL calibration

The generic profile coefficient ranges narrow as follows for `odoo-apl`:

| Profile                                            | Coefficient  | Rationale                                                                                  |
| -------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| Junior (< 2 years Odoo)                            | × 2.0        | ~125 `apl_*` addons, route-rule / consigne / Topmotive quirks, Playwright UAT harness      |
| Confirmed (reference)                              | × 1.0        | Knows OCA + `odootest -o/-p`, comfortable with `stock` / `sale` overrides                  |
| Senior / expert (Odoo + APL repo familiarity)      | × 0.75       | Already knows the route-rule hierarchy, consigne mixin, pricing chain, Topmotive mocking   |

## APL-specific phase reminders

When decomposing, watch out for these APL-typical costs that easily slip a
phase estimate by +0.5 j each:

- **Route rule extension** — extending `AplAbstractStockRouteRule` requires
  a new subclass + matching test fixture (`apl_stock_route_rule_*` modules).
- **Consigne flow** — touching consigne almost always implies updating
  `apl_sale_consigne` AND `apl_rma_sale_consigne` in lockstep.
- **Pricing chain** — any `_get_display_price` / pricelist tweak must go
  through `apl_sale_line_price`. Account for a regression test on the chain.
- **API exposure** — exposing a model via `apl_api_*` adds: `uuid` field
  (via `apl_base_uuid`), `auth_api_key`, FastAPI route, Pydantic schema,
  HttpCase with API key.
- **Topmotive integration** — tests MUST mock the connector. Add a fixture
  cost (~0.25 j) if the test setup doesn't exist yet.
- **UAT video** — Playwright scenario + MP4 evidence in `uat_records/` is
  ~0.5–1 j depending on complexity.

## Output language

APL deliverables are written in **French**. Section headers and column names
follow:

- Section 1 — `Hypothèses & questions ouvertes`
- Section 2 — `Décomposition par phase` (columns: Phase / Tâche / Effort (j))
- Section 3 — `Risques (hors total)` (columns: Risque / Déclencheur / Impact)
- Section 4 — `Ajustement par profil` (columns: Profil / Coefficient / Total ajusté)

All other rules (phase list, output structure, forbidden patterns) come from
the generic methodology — do not duplicate them here.
