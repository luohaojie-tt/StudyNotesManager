---
name: git-workflow
description: Automated Git workflow for StudyNotesManager project. Use when teammates need to perform Git operations including: (1) Creating feature branches with proper naming conventions, (2) Committing code with Conventional Commits format, (3) Creating Pull Requests with templates, (4) Managing daily Git workflows. Ensures all operations comply with team Git standards defined in docs/09-workflow/GIT_WORKFLOW.md.
---

# Git Workflow

Automated Git operations that ensure 100% compliance with team standards.

## Quick Start

### Create Feature Branch
```bash
git checkout develop
git pull origin develop
git checkout -b <branch-type>/<feature-name>
```

Branch types:
- `backend-dev/*` - Backend development
- `frontend-dev/*` - Frontend development
- `test/*` - Testing

### Commit Code
```bash
git add .
git commit -m "<type>: <description>"
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

### Push and Create PR
```bash
git push -u origin <branch-name>
gh pr create --base develop
```

## Commit Message Format

Must follow Conventional Commits:
```
<type>: <description>

[optional body]

[optional footer]
```

The Git hook at `.git/hooks/commit-msg` automatically validates this format.

## Pull Request Template

When creating PR, include:
- Change description
- Type of change (feature/fix/refactor/docs)
- Test checklist (unit/integration/manual, coverage >80%)
- Related task numbers

## Daily Workflow

**Morning**:
```bash
git checkout develop
git pull origin develop
```

**End of Day**:
```bash
git add .
git commit -m "wip: daily progress"
git push
```

## Validation

Automatic checks ensure:
- Branch naming follows convention
- Commit messages match Conventional Commits
- Code coverage >80% (via tests)
- No merge conflicts

## Common Errors

**Invalid branch name**:
```
❌ auth-api
✅ backend-dev/auth-api
```

**Invalid commit message**:
```
❌ "add feature"
✅ "feat: add user registration API"
```

## Reference Documentation

For detailed Git workflow specifications, see [references/standards.md](references/standards.md)

For teammate guidelines, see [references/guidelines.md](references/guidelines.md)
