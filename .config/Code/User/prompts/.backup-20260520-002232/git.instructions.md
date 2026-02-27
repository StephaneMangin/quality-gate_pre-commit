---
description: "Git workflow standards: branch naming, commit conventions, rebasing, semantic versioning. For git operations or discussing version control strategy."
---

# Git Workflow

- Branch naming: `feature/`, `fix/`, `chore/`, `refactor/` prefixes
- Rebase feature branches on main before merging (keep linear history)
- Squash trivial commits before merge when appropriate
- Tag releases following semantic versioning (MAJOR.MINOR.PATCH)
- Use `.gitignore` to exclude build artifacts, IDE files, secrets
