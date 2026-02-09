# Teammate Guidelines

Daily work guidelines and best practices for teammates.

## Daily Workflow

### Morning Routine

1. Pull latest changes
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. Create/update feature branch
   ```bash
   git checkout -b <branch-type>/<feature-name>
   ```

3. Check TaskList for assigned tasks

4. Report today's plan to team-lead

### During Development

1. Follow TDD approach
   - Write tests first
   - Implement to pass
   - Refactor

2. Frequent commits
   - One logical change per commit
   - Use proper commit format
   - Don't accumulate changes

3. Run tests frequently
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

### Evening Routine

1. Commit all changes
   ```bash
   git add .
   git commit -m "wip: daily progress summary"
   ```

2. Push to remote
   ```bash
   git push
   ```

3. Create PR if feature complete
   ```bash
   gh pr create --base develop
   ```

4. Report to team-lead:
   - Completed tasks
   - Issues encountered
   - Tomorrow's plan

## Coding Standards

### Backend (Python)

- Use type annotations
- Write docstrings for functions
- Handle errors properly
- Follow PEP 8

Example:
```python
def create_note(user_id: UUID, title: str, content: str) -> Note:
    """
    Create a new note.

    Args:
        user_id: User ID
        title: Note title
        content: Note content

    Returns:
        Created note object

    Raises:
        ValueError: If validation fails
    """
    if not title or len(title) > 255:
        raise ValueError("Title must be 1-255 characters")

    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
```

### Frontend (TypeScript)

- Use TypeScript types
- Write JSDoc comments
- Handle errors
- Follow ESLint rules

Example:
```typescript
interface CreateNoteParams {
  userId: string;
  title: string;
  content: string;
}

/**
 * Create a new note
 * @param params - Note parameters
 * @returns Created note object
 */
async function createNote(params: CreateNoteParams): Promise<Note> {
  if (!params.title || params.title.length > 255) {
    throw new Error('Title must be 1-255 characters');
  }

  const response = await apiClient.post('/api/notes', params);
  return response.data;
}
```

## Testing Requirements

### Coverage
- Backend: >80% (pytest-cov)
- Frontend: >80% (Vitest)

### TDD Process
1. Write test (RED)
2. Implement (GREEN)
3. Refactor (IMPROVE)

## Communication

### Daily Standup
Report to team-lead:
- What you completed today
- Blockers or issues
- Plan for tomorrow

### Asking for Help
When stuck:
1. Check documentation first
2. Ask team-lead for guidance
3. Coordinate with other teammates

## Code Review

### Before Creating PR
- [ ] All tests pass
- [ ] Coverage >80%
- [ ] Code is clean
- [ ] Documentation updated

### During Review
- Address CRITICAL issues immediately
- Fix HIGH issues when possible
- Consider MEDIUM/LOW feedback

### After Review
- Make requested changes
- Request re-review
- Wait for approval before merging

## Common Mistakes to Avoid

### Don't
- ❌ Commit directly to develop
- ❌ Use vague commit messages
- ❌ Skip writing tests
- ❌ Ignore code review feedback
- ❌ Work without updating task status

### Do
- ✅ Always work on feature branches
- ✅ Use descriptive commit messages
- ✅ Follow TDD approach
- ✅ Address code review promptly
- ✅ Keep task list updated
