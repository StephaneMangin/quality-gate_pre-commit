---
description: "Odoo and OCA development standards: module structure, OCA guidelines, migration, pre-commit, odootest, security. For Odoo modules, __manifest__.py, OCA contributions, or Odoo XML/Python files."
applyTo: "**/{__manifest__.py,__openerp__.py}"
---

# Odoo Development Context

Always provide code that meets OCA standards, is community-ready, well-tested, production-grade.
you're developing Odoo modules following enterprise-grade standards and OCA contribution guidelines. Always adhere to these guidelines:

## OCA Contribution Guidelines
- Follow **OCA (Odoo Community Association) coding guidelines** from https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst
- Ensure modules are ready for community contribution and review
- Use proper licensing (LGPL-3 for most OCA modules)
- Include comprehensive README.rst with usage instructions
- Follow OCA module structure and naming conventions

## Code Quality Standards
- Use **pre-commit hooks** to ensure code quality before commits
- Write comprehensive tests using **odootest** framework
- Maintain backward compatibility and follow semantic versioning
- Code: production-ready and maintainable

## OCA Module Structure
- Proper `__manifest__.py` with all required fields (name, version, author, license, etc.)
- Organized directory structure: `models/`, `views/`, `data/`, `tests/`, `static/`, `security/`
- Follow naming conventions: snake_case for files/methods, PascalCase for classes
- Implement proper inheritance patterns using `_inherit` and `_name`
- Use translation-ready strings with `_()` function
- Add comprehensive docstrings following Python standards

## Python File Formalism
- **One model class per file** → file name must match model name (e.g., `sale_order.py` for `sale.order`)
- Keep `__init__.py` files as pure import lists — no logic, no configuration
- Import order: stdlib → third-party → odoo core → odoo addons → local (enforced by `isort`)
- Inherit from parent module test classes to reuse `setUpClass` data — avoid duplicating test data creation
- Minimize `setUpClass` / `setUp` data: create only what current test class needs; use parent common test classes (e.g., `TestSaleCommon`, `TestStockCommon`) for shared fixtures
- Group related test methods in single test class; split into separate files/classes when testing distinct features
- Use `cls.env["model.name"]` in `setUpClass` and `self.env["model.name"]` in test methods — never mix them
- Method ordering within model class: `_name`/`_inherit`/`_description` → fields → constrains/onchanges → CRUD overrides → business methods → private helpers
- Avoid defining standalone functions in model files — use `@api.model` class methods instead
- One wizard per file in `wizards/` directory; same naming convention as models

## OCA Module Migration Guidelines
- Ensure all changes are backward compatible
- Follow semantic versioning (major, minor, patch)
- Update `__manifest__.py` with new version number
- Create a README.rst if not exists, following this formalism:
- title is rounded by `=` signs
- A brief explanation of module's purposes
- Check for all content compatibility with the Odoo version to migrate
- This includes:
  - views (attrs, groups, xml references, etc.)
  - models (method overrides, fields, etc.)
  - data files (records, xml references, etc.)
  - security files
  - static files
- Provide migration guide in README.rst if needed
- Provide migration script if needed
- When changes are made, inform user that job has been done and needs review
- Once validated, add to staging area in git and proceed to commit which needs this formalism:
- `[MIG] {module name}: migration to XX.0` where XX is major Odoo version being migrated

## Pre-commit Standards (OCA Requirements)
Use command: `pre-commit run -a`
- Code must pass `black` formatting (line length 88)
- Use `flake8` for linting compliance
- Ensure `isort` import organization
- Pass `pylint-odoo` specific checks
- Validate XML/CSV syntax and structure
- Check manifest files completeness
- Ensure proper file headers and copyright notices

## Testing with odootest
- Write comprehensive tests in `tests/` directory
- Use `TransactionCase` for database-dependent tests or inherit parent modules to reuse their own
- Use `HttpCase` for web/integration tests
- Implement proper `setUpClass()`, `setUp()` and `tearDown()` methods
- Test all business logic paths and edge cases
- Use descriptive test method names starting with `test_` and easily readable for humans (short sentence explaing what test is for)
- Use exhaustive and descriptive docstring to give hints of what test method is used for
- Ensure tests are isolated and repeatable
- Use `odootest -o <module name>` to install/update module with its dependencies and run Odoo tests
- Use `odootest -p <module name>` to run tests using pytest

## Security & Performance (OCA Standards)
- Implement proper access rights (`ir.model.access.csv`) when needed
- Define record rules when needed (`security/` directory)
- Use `@api.depends` for computed fields optimization
- Optimize database queries and avoid N+1 problems
- Validate user inputs and implement proper error handling
- Follow Odoo security best practices

## Odoo Documentation Requirements
- Include detailed README.rst with installation and usage instructions following the OCA template or other module's README if exists
- Document all public methods and complex business logic
- Provide configuration examples and screenshots when relevant
- Include changelog for version updates
- DON'T write comments that state obvious → only useful comments explaining *why* piece of code exists, not *what* it does (reading code suffices)
- DON'T use `"""` docstrings when overriding method → use `#` comments instead
