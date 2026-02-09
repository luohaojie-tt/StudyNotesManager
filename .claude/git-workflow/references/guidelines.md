# Teammate Guidelines

Daily work guidelines and best practices for teammates.

## ⏱️ Time Control Rules (CRITICAL - All Teammates Must Follow)

### Basic Rules

**Applies to**: All teammates (including team-lead)

**Core Rule**:
```
Maximum task duration: 30 minutes
```

### Required Workflow After 30 Minutes

**Step 1: Stop Immediately**
- Stop all coding work
- Regardless of task completion status
- Do not continue "just a bit more"

**Step 2: Report Progress to team-lead**

Example format:
```
📊 Task Progress Report
✅ Completed: User registration API endpoint definition
🔄 In Progress: Password validation logic (50% done)
📋 Pending: Email verification feature
⏱️ Time Used: 30 minutes
🚧 Blockers: None
```

**Step 3: Git Management for Unfinished Work**

```bash
# 1. Save all changes
git add .

# 2. Commit progress with detailed notes
git commit -m "wip: User authentication module progress

Completed:
- POST /api/auth/register endpoint
- Basic form validation

In Progress:
- Password hashing (50% done)
- bcrypt integration added
- Pending: salt rounds configuration

To Complete:
- Email verification
- JWT token generation
- Unit tests

Next Steps:
1. Complete password hashing logic
2. Implement email verification endpoint
3. Write unit tests (target >80% coverage)
"

# 3. Push to remote to save work
git push -u origin backend-dev/user-auth
```

**Step 4: Update TaskList Status**
- Mark unfinished task as `in_progress`
- Add detailed progress notes to description
- Record next steps

### 🛑 team-lead Stop Command

**Stop Command Meaning**:
```
team-lead: "Stop for today" or "Stop work"
↓
This means: Work day ends
```

**Required Actions After Stop Command**:

1. **Immediately Stop** all development work
   - No "just finishing this function"
   - No "just one more commit"

2. **Report Task Completion to team-lead**
   ```
   Today's Completed Tasks:
   ✅ User registration API (completed)
   ✅ Login verification logic (completed)

   Unfinished Tasks & Progress:
   🔄 Notes list API - 60% complete
      - Done: Basic query, database connection
      - Todo: Pagination, filtering

   🔄 OCR integration - 30% complete
      - Done: Baidu OCR SDK setup
      - Todo: Image upload handling, result parsing

   Issues Encountered:
   ⚠️ Baidu OCR API slow response, needs optimization
   ```

3. **Git Management**
   ```bash
   git add .
   git commit -m "wip: 2026-02-09 work progress

   Today's Completed:
   ✅ User registration API (completed)
      - endpoint: POST /api/auth/register
      - Validation logic complete
      - Unit tests passing

   ✅ Login verification (completed)
      - JWT generation working
      - Password hash verification passing

   Unfinished Progress:
   🔄 Notes list API - 60% complete
      - Done: Basic query, database connection
      - Todo: Pagination logic, filters, sorting

   🔄 OCR integration - 30% complete
      - Done: Baidu OCR SDK config, API key setup
      - Todo: Image upload endpoint, result parsing

   Next Development Plan:
   1. Complete notes list pagination
   2. Implement image upload endpoint
   3. OCR result parsing and storage
   4. Write unit tests (current coverage: 65%)
   "

   git push
   ```

4. **Update TaskList**
   - Mark completed tasks as `completed`
   - Record detailed progress for unfinished tasks
   - Define clear starting point for next session

### ▶️ Resume Development Workflow

**Only continue after receiving team-lead's continue instruction**:

```bash
# team-lead evaluates progress and issues continue instruction
# teammate resumes from git records:

git pull origin develop
git checkout backend-dev/user-auth
git pull

# Check last commit message for progress
git log -1 --pretty=format:"%B"

# Continue unfinished work
```

### ⚠️ Violation Consequences

**Not Following 30-Minute Rule**:
```
1st time: ⚠️ Warning
2nd time: 🔄 Task reassigned
3rd time: ❌ Removed from team
```

**Not Following Stop Command**:
```
Immediate:
- ❌ All development permissions revoked
- ❌ Code will not be merged
- ❌ Removed from team
```

### 📋 Example Complete Workflow

**Scenario: backend-dev developing user authentication API**

```
00:00 - Start task: Implement user registration API
00:25 - In progress: Password hashing
00:30 - ⏰ 30 minutes reached!

✅ Execute 30-minute workflow:
1. Stop coding
2. Report progress to team-lead
3. git add . && git commit -m "wip: detailed progress..."
4. git push
5. Update TaskList

team-lead evaluates: "OK to continue"
backend-dev continues development...

00:55 - Another 30 minutes
Report progress again...

01:20 - team-lead: "Stop for today"
✅ Immediately execute stop workflow
✅ Report today's completion
✅ Git manage all work
✅ End of day
```

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
