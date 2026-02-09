# Git Workflow Standards

Complete Git workflow specification for StudyNotesManager project.

## Branch Strategy

```
main (production)
  ↑
  └─ merge (stable releases only)

develop (development)
  ↑
  ├─ backend-dev/* (backend features)
  ├─ frontend-dev/* (frontend features)
  └─ test/* (testing)
```

## Branch Naming Rules

| Pattern | Purpose | Example |
|---------|---------|---------|
| `backend-dev/*` | Backend API/features | `backend-dev/auth-api` |
| `frontend-dev/*` | Frontend UI/components | `frontend-dev/note-list` |
| `test/*` | Test development | `test/integration-auth` |

## Commit Message Specification

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation update
- `test`: Test related
- `chore`: Build/tooling
- `perf`: Performance improvement
- `ci`: CI configuration

### Examples

```
feat: implement user registration API

- POST /api/auth/register endpoint
- Email validation
- Password bcrypt hashing
- JWT token generation

Closes #123
```

```
fix: resolve login validation error

Users with special characters in email
could not log in. Fixed regex pattern.

Fixes #456
```

## Pull Request Process

1. Create PR from feature branch to `develop`
2. Fill PR template completely
3. Code-reviewer performs review
4. Address CRITICAL and HIGH issues
5. Use "Squash and Merge" to combine commits
6. Delete feature branch after merge

## Merge Strategy

**Always use "Squash and Merge"** for feature branches.

This maintains clean history by combining all commits into one meaningful commit.

## Code Review Checklist

### Security (CRITICAL)
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities
- [ ] No hardcoded secrets
- [ ] Authentication/authorization verified

### Quality (HIGH)
- [ ] Single responsibility for functions
- [ ] No code duplication
- [ ] Clear naming
- [ ] Proper error handling

### Testing (MEDIUM)
- [ ] Unit tests included
- [ ] Test coverage >80%
- [ ] Test cases comprehensive

### Documentation (LOW)
- [ ] API docstrings present
- [ ] Complex logic commented
- [ ] README updated if needed
