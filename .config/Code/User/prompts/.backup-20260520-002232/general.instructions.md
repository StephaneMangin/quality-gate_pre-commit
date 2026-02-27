---
description: "Core software engineering principles: code quality, testing, security, performance, error handling, documentation. Always active."
applyTo: "**"
---

# Priorité absolue: lisibilité humaine et maintenabilité long terme.

##Règles de conception (obligatoires):
1. Une fonction = une responsabilité principale.
2. Toute fonction d’orchestration doit déléguer à des helpers nommés par intention (`collect_*`, `build_*`, `normalize_*`, `validate_*`).
3. Éviter les compréhensions/expressions compactes si elles masquent l’intention.
4. Préférer variables intermédiaires explicites à la compaction.
5. Retour de payloads complexes: construire par sous-sections nommées avant l’assemblage final.

##Seuils de complexité à respecter:
6. Max 30 lignes par fonction (hors docstring courte).
7. Max 3 niveaux d’imbrication.
8. Max 5 blocs logiques dans une même fonction.
9. Si un `if/for/try` se combine avec transformation de données + I/O + mapping, découper immédiatement.

##Conventions de lisibilité:
10. Nommer les helpers avec vocabulaire métier, pas technique.
11. Ajouter un commentaire court “why” uniquement pour les décisions non évidentes.
11.bis Docstrings: une phrase d’intention, puis une note UNIQUEMENT pour les invariants/pièges non évidents (cas limite, effet de bord contre-intuitif, contrainte métier implicite). Interdits:
   - paraphraser le corps de la fonction (liste de "Rules:" qui décrit chaque branche `if/return/continue`);
   - répéter types/noms des paramètres déjà visibles dans la signature;
   - documenter ce que le nom de la fonction et le code disent déjà.
   Si la docstring se contente de décrire le flux: la supprimer.
12. Aucun import implicite complexe sans justification: si import différé, commenter le motif (cycle, optional deps, startup cost).

##Validation obligatoire après refactor:
13. Garantir comportement inchangé.
14. Exécuter tests et quality gates du repo (`pytest`, `pre-commit run -a`) après modifications.
15. En réponse, expliquer:
- ce qui été extrait,
- pourquoi,
   - et comment le comportement est conservé.

##Arbitrage:
16. En cas de doute entre code court et code clair: choisir code clair.

## A RESPECTER TOUT LE TEMPS

Si tu proposes une version compacte, fournis aussi automatiquement une version lisible en étapes explicites, puis applique la version lisible par défaut.

# General Software Engineering Principles

Always produce code that is clean, well-tested, secure, production-grade.
Follow principle of least surprise. simplicity > cleverness.

## Code Quality
- Write self-documenting code with meaningful names for variables, functions, classes, modules
- Keep functions small and focused on single responsibility (SRP)
- composition > inheritance when apt
- Avoid premature optimization — profile first, optimize second
- Remove dead code; don't comment it out
- DON'T write comments that state obvious → only write comments explaining *why*, not *what*

## Version Control
- Write clear, descriptive commit messages following conventional commits when applicable
- Keep commits atomic — one logical change per commit
- Use feature branches and pull requests for code review
- Never commit secrets/credentials/sensitive data

## Testing
- Write tests *before* or *alongside* implementation (TDD/BDD when practical)
- Cover happy paths, edge cases, error conditions
- Tests: isolated, repeatable, deterministic
- Use descriptive test names documenting expected behavior
- Mock external dependencies; don't rely on network or third-party services in unit tests

## Security
- Validate and sanitize all external inputs (user input, API responses, file contents)
- Never trust client-side data
- Use parameterized queries — never concatenate user input into SQL
- Follow principle of least privilege for access control
- Keep dependencies up to date and audit for known vulnerabilities
- Never log or expose sensitive data (passwords, tokens, PII)

## Performance
- mind algorithmic complexity (O notation)
- Avoid N+1 query patterns in ORM/database interactions
- Use pagination for large datasets
- Prefer lazy evaluation and streaming for large data processing
- Cache expensive computations when data is stable

## Error Handling
- Fail fast and fail loud — don't silently swallow errors
- Use specific exception types, not bare `except:`
- Provide actionable error messages
- Log errors with enough context to debug without reproducing

## Code Complexity & Readability
- Keep cyclomatic complexity low — aim for ≤ 10 per function; refactor if higher
- Limit function length to ~30 lines; if it needs scroll, it needs split
- Limit nesting depth to 3 levels — use early returns, guard clauses, or extract helpers
- Limit function parameters to 3–4; use objects/dataclasses to group related arguments
- flat code > deeply nested conditionals → invert conditions and return early
- Use consistent naming conventions throughout codebase → no abbreviations unless universally understood
- Optimize for reading, not writing → code is read 10x > it's written
- One concept per line → avoid chaining too many operations in single expression
- Keep cognitive complexity low → minimize mental effort required to understand block of code
- Limit file length to ~300–400 lines; split into focused modules when larger
- Reduce coupling between modules — depend on abstractions, not concrete implementations
- Keep public API surface small → expose only what is needed

## Documentation
- Document public APIs, complex business logic, non-obvious decisions
- Keep documentation close to code (docstrings, README)
- Update documentation when changing behavior
