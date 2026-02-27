---
name: onboarding
description: "Use when: new developer joining the project, project overview, understanding module structure, getting started, first setup, where to start, discover codebase, odoo-apl introduction. Keywords: onboarding, new developer, getting started, project overview, discover, introduction, setup, first time, where to start."
argument-hint: "Optional focus area (e.g. stock routing, API integration, POS flows)"
---

# odoo-apl — Developer Onboarding

## Project Overview

**odoo-apl** is an Odoo 18 implementation for APL (automotive parts distribution).
It contains **125 custom `apl_*` addons** on top of Odoo Enterprise + OCA modules.

## Essential Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install + run Odoo tests for a module
odootest -o <module_name>

# Run tests via pytest (faster, no reinstall)
odootest -p <module_name>

# Run all code quality checks before committing
pre-commit run -a
```

**NEVER** use bare `pytest` or `odoo --test-enable`.

## Repository Structure

```
odoo/addons/apl_*/     ← 125 custom APL addons (the codebase)
src/addons/            ← Odoo Enterprise + OCA community addons (dependencies)
uat_records/           ← Playwright UAT video tests (23 scenarios)
.github/agents/        ← AI agent team (see below)
.github/skills/        ← AI skills (estimation, onboarding)
.github/hooks/         ← Pre-commit enforcement hook
```

## Module Map by Domain

### Sale & Pricing
| Module | What it does |
| ------ | ------------ |
| `apl_sale_line_price` | Pricelist recompute on sale lines — entry point for all pricing |
| `apl_sale_discount` | Discount rules and cascade |
| `apl_pricelist_brand` | Brand-based pricelist logic |
| `apl_partner_customer_group` | Customer group segmentation (drives pricing) |
| `apl_sale_stock_split_line` | Auto-split sale lines by stock availability |

### Stock & Logistics
| Module | What it does |
| ------ | ------------ |
| `apl_stock_route_rule` | Base abstract routing rule + 3 specializations |
| `apl_sale_stock_route_resolution` | Route resolution on sale order confirmation |
| `apl_sale_stock_route_bypass_packing` | Bypass packing zone for certain routes |
| `apl_stock_replenishment` | Replenishment with waiting SO filter |
| `apl_stock_dispatch_putaway` | Dispatch putaway strategies |
| `apl_stock_barcode_next_transfer` | Barcode — next transfer matrix |

### POS Session
| Module | What it does |
| ------ | ------------ |
| `apl_sale_pos_session` | POS session workflow (cash, invoices) |
| `apl_sale_pos_cash_entry` | Cash entry on POS |
| `apl_sale_pos_workflow` | POS → sale order workflow |
| `apl_sale_pos_invoice_payment` | Invoice payment via POS |

### Partner
| Module | What it does |
| ------ | ------------ |
| `apl_partner_customer_group` | Customer group (A/B/C segmentation) |
| `apl_partner_visit_calendar` | Sales visit scheduling |
| `apl_partner_salesperson` | Salesperson assignment rules |
| `apl_partner_topmotive` | Topmotive ID on partner |
| `apl_partner_region` | Geo region on partner |

### RMA / Consigne
| Module | What it does |
| ------ | ------------ |
| `apl_sale_consigne` | Consigne (deposit) on sale orders |
| `apl_rma_sale_consigne` | Consigne RMA return flow |
| `apl_rma_product_return` | Product return RMA |

### API / Integration
| Module | What it does |
| ------ | ------------ |
| `apl_api` | FastAPI base — shared router + auth |
| `apl_api_topmotive` | Topmotive connector |
| `apl_api_product_importer` | Bulk product import |
| `apl_graphql` | GraphQL schema |
| `apl_unity_bridge_connector` | Unity Bridge ERP connector |

### Product / Tecdoc
| Module | What it does |
| ------ | ------------ |
| `apl_product_tecdoc` | Tecdoc reference data on products |
| `apl_product_brand_tecdoc` | Brand → Tecdoc mapping |
| `apl_product_supplier` | Supplier info extensions |
| `apl_product_pricelist_supplier_default` | Default supplier pricelist |

## Key Architectural Patterns

### 1. Route rules
All stock routing logic inherits from `AplAbstractStockRouteRule` in `apl_stock_route_rule`.
Three specializations: `stock`, `purchase`, `replenishment`.
**Never** add routing logic outside this hierarchy.

### 2. Pricing chain
`apl_sale_line_price` → `apl_pricelist_brand` → `apl_partner_customer_group`
Pricelist computation goes through this chain. Override at the right level.

### 3. API authentication
All `apl_api_*` routes use `auth_api_key` (OCA). Keys managed via `auth_api_key_server_env`.

### 4. UUID
All API-exposed models carry a `uuid` field from `apl_base_uuid`. Always add it when
creating a new API-exposed model.

## UAT Video Tests

Located in `uat_records/tests/`. Each test produces an MP4 artefact.
Key scenarios to know:
- `test_pricelist_recompute.py` — pricing chain
- `test_sale_to_delivery_full_flow.py` — order → delivery
- `test_dropshipping_flow.py` — dropship route
- `test_barcode_next_transfer_nominal.py` — barcode workflow
- `test_consigne.py` — consigne round-trip

Run a single UAT test:
```bash
cd uat_records && pytest tests/test_<name>.py --headed
```

## AI Agent Team

| Agent | Trigger | Role |
| ----- | ------- | ---- |
| `odoo-demand` | `<USER DEMAND>` | Orchestrates full dev workflow |
| `odoo-api` | api / fastapi / graphql | API/integration specialist |
| `odoo-model` | model / field / _inherit | Model specialist (APL patterns) |
| `odoo-test` | test / odootest | Test writer |
| `odoo-precommit` | pre-commit / lint | Quality gates |
| `odoo-review` | review / audit | Code review |
| `odoo-uat-records` | video / MP4 / UAT | Video evidence |
| `demand_analysis` skill | `<USER ESTIMATE>` | Effort estimation |
