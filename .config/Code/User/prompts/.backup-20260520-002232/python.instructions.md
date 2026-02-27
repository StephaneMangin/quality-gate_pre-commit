---
description: "Python development standards: PEP 8, type hints, f-strings, pathlib, logging. For Python files."
applyTo: "**/*.py"
---

# Python Development

- Target Python 3.10+ unless project constraints dictate otherwise
- Follow PEP 8 style guidelines
- Use type hints for function signatures and complex data structures
- f-strings > `.format()` or `%` formatting
- Use `pathlib` over `os.path` for file operations
- Prefer context managers (`with`) for resource management
- Use `dataclasses` or `attrs` for value objects
- Use virtual environments (`venv`, `virtualenv`) for dependency isolation
- Pin dependencies with exact versions in lock files
- Use `logging` module, not `print()`, for diagnostics
