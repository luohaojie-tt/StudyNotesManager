# Analytics Feature Technical Debt

## Status: Deferred (Phase 2)

### Overview
The analytics feature (`backend/app/services/analytics_service.py`) was implemented before models were finalized, creating significant technical debt.

### Issues Found

#### 1. Model Field Mismatches
- **Location**: Lines 156, 213-221
- **Issue**: References `Mistake.question_text` but model uses `Mistake.question`
- **Fix**: Change all references to `Mistake.question`

#### 2. Category Integration Issues
- **Location**: Lines 177-197
- **Issue**: Attempts to join on `Mistake.category_id` which doesn't exist
- **Root Cause**: Mistake model uses `subject` field, not Category foreign key
- **Fix**: Aggregate by `Mistake.subject` instead

#### 3. StudySession Field Mismatch
- **Location**: Line 457
- **Issue**: References `StudySession.quizzes_completed` field
- **Root Cause**: StudySession has `questions_answered`, not `quizzes_completed`
- **Fix**: Use `questions_answered` field

#### 4. Missing Imports
- **Location**: Line 11
- **Issue**: `QuizQuestion` used but not imported
- **Fix**: Add to imports: `from app.models.quiz import Quiz, QuizSession, QuizAnswer, QuizQuestion`

#### 5. SQLAlchemy Syntax Errors
- **Location**: Line 58
- **Issue**: Uses `func.nullif()` which doesn't exist
- **Fix**: Replace with `func.coalesce()`

### Estimated Fix Time: 4-6 hours

### Implementation Status

**Current State**:
- Service code exists (481 lines)
- API routes exist (`backend/app/api/analytics.py`)
- Schemas exist (`backend/app/schemas/analytics.py`)
- Tests written but failing due to mock complexity

**Resolution**:
Created clean `stats_service.py` (Task #24) with simpler implementations

### Next Steps When Resuming

1. Write integration tests with real database for analytics endpoints
2. Add missing analytics endpoints:
   - Knowledge point coverage analysis
   - Timeline data (daily/weekly trends)
   - Export functionality (CSV/PDF)

---

**Created**: 2026-02-12
**Status**: Deferred
**Priority**: Medium (enhancement, not critical for core functionality)

