# Testing Guide for StudyNotesManager

This document provides comprehensive information about the testing strategy, setup, and execution for the StudyNotesManager project.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Coverage Reports](#coverage-reports)
6. [CI/CD Integration](#cicd-integration)

---

## Testing Overview

The project uses a three-tier testing approach:

### 1. Unit Tests
- **Purpose**: Test individual functions, classes, and components in isolation
- **Framework**: pytest
- **Location**: `backend/tests/unit/`
- **Execution Time**: Fast (seconds)
- **Coverage Target**: >80%

### 2. Integration Tests
- **Purpose**: Test API endpoints and database operations
- **Framework**: pytest + httpx
- **Location**: `backend/tests/integration/`
- **Execution Time**: Medium (seconds to minutes)
- **Database**: In-memory SQLite

### 3. E2E Tests
- **Purpose**: Test complete user workflows through the UI
- **Framework**: Playwright
- **Location**: `backend/tests/e2e/` and `frontend/tests/e2e/`
- **Execution Time**: Slow (minutes)
- **Browsers**: Chromium, Firefox, WebKit, Mobile

---

## Test Structure

### Backend Test Structure

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── utils.py                 # Test utility functions
│   ├── fixtures/                # Custom fixtures
│   │   ├── database.py          # Database fixtures
│   │   └── __init__.py
│   ├── unit/                    # Unit tests
│   │   ├── test_auth.py         # Authentication tests
│   │   ├── test_notes.py        # Notes API tests
│   │   ├── test_mindmap.py      # Mindmap generation tests
│   │   └── __init__.py
│   ├── integration/             # Integration tests
│   │   ├── test_api_integration.py
│   │   └── __init__.py
│   └── e2e/                     # E2E tests
│       ├── test_user_workflows.py
│       └── __init__.py
├── pyproject.toml               # Pytest configuration
└── requirements.txt             # Test dependencies
```

### Frontend Test Structure

```
frontend/
└── tests/
    └── e2e/
        ├── playwright.config.ts # Playwright configuration
        ├── auth.spec.ts         # Authentication E2E tests
        ├── notes.spec.ts        # Notes E2E tests
        └── ...                  # Additional E2E test files
```

---

## Running Tests

### Prerequisites

Install test dependencies:

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (E2E)
cd frontend
npm install -D @playwright/test
npx playwright install
```

### Backend Tests

#### Run All Tests
```bash
cd backend
pytest
```

#### Run Unit Tests Only
```bash
pytest -m unit
```

#### Run Integration Tests Only
```bash
pytest -m integration
```

#### Run Specific Test File
```bash
pytest tests/unit/test_auth.py
```

#### Run with Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

#### Run with Verbose Output
```bash
pytest -v
```

#### Run Tests Matching Pattern
```bash
pytest -k "test_login"
```

#### Run Parallel Tests (faster)
```bash
pip install pytest-xdist
pytest -n auto
```

### Frontend E2E Tests

#### Run All E2E Tests
```bash
cd frontend
npx playwright test
```

#### Run in Specific Browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

#### Run in Headed Mode (see browser)
```bash
npx playwright test --headed
```

#### Run Specific Test File
```bash
npx playwright test auth.spec.ts
```

#### Debug Mode
```bash
npx playwright test --debug
```

#### View Test Report
```bash
npx playwright show-report
```

---

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import MagicMock

@pytest.mark.unit
class TestAuthService:
    @pytest.fixture
    def mock_db_session(self):
        session = MagicMock()
        session.scalar = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_db_session):
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="Test User"
        )

        service = AuthService(mock_db_session)
        user = await service.register(user_data)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.api
class TestNotesAPI:
    @pytest.mark.asyncio
    async def test_create_note(self, client: AsyncClient, authenticated_headers):
        response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Test Note",
                "content": "Test content",
                "subject": "Mathematics"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Note"
```

### E2E Test Example (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('should create a new note', async ({ page }) => {
  await page.goto('/');

  await page.click('button:has-text("Create Note")');
  await page.fill('input[name="title"]', 'Test Note');
  await page.fill('textarea[name="content"]', 'Test content');
  await page.click('button:has-text("Save")');

  await expect(page.locator('text=Note created successfully')).toBeVisible();
});
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e           # E2E test
@pytest.mark.auth          # Authentication related
@pytest.mark.api           # API endpoint test
@pytest.mark.ocr           # OCR related test
@pytest.mark.ai            # AI/LLM related test
@pytest.mark.slow          # Slow running test
```

### Fixtures

#### Using Built-in Fixtures

```python
async def test_with_db(async_db_session: AsyncSession):
    # Use database session
    pass

async def test_with_client(client: AsyncClient):
    # Use HTTP client
    pass

async def test_with_auth(client: AsyncClient, auth_headers):
    headers = await auth_headers()
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
```

#### Creating Custom Fixtures

```python
@pytest.fixture
async def test_note(async_db_session):
    from app.models.note import Note
    note = Note(
        title="Test",
        content="Content",
        subject="Math",
        owner_id=1
    )
    async_db_session.add(note)
    await async_db_session.commit()
    return note
```

---

## Coverage Reports

### Generate Coverage Report

```bash
pytest --cov=app --cov-report=html --cov-report=xml --cov-report=term
```

### View HTML Report

```bash
# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Thresholds

Configure minimum coverage in `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 80.0
```

### Exclude from Coverage

```python
def __repr__(self):  # pragma: no cover
    return f"<User {self.id}>"
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: pytest -m unit --cov

      - name: Run integration tests
        run: pytest -m integration

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest -m unit
        language: system
        pass_filenames: false
```

---

## Best Practices

### 1. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Clear Test Names
```python
# Good
def test_user_cannot_login_with_wrong_password():
    pass

# Bad
def test_login():
    pass
```

### 3. Arrange-Act-Assert Pattern
```python
def test_note_creation():
    # Arrange
    note_data = {"title": "Test", "content": "Content"}

    # Act
    note = create_note(note_data)

    # Assert
    assert note.title == "Test"
```

### 4. Use Descriptive Assertions
```python
# Good
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert user.is_active, "User should be active"

# Less clear
assert response.status_code == 200
```

### 5. Mock External Services
```python
def test_with_mock(mock_deepseek_api):
    mock_deepseek_api.generate_quiz.return_value = {"quiz": "data"}
    # Test without calling real API
```

### 6. Test Edge Cases
```python
def test_note_validation():
    # Test empty title
    # Test very long content
    # Test invalid subject
    # Test special characters
```

### 7. Keep Tests Fast
- Use in-memory database for tests
- Mock external APIs
- Avoid sleep() - use proper async/await
- Run unit tests in parallel

### 8. Maintain Test Data
- Use fixtures for common test data
- Clean up after tests
- Use transaction rollback for database tests

---

## Troubleshooting

### Tests Fail with Import Errors
```bash
# Ensure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Tests Fail
```bash
# Ensure test database exists
createdb test_db
pytest
```

### E2E Tests Timeout
```bash
# Increase timeout
test('slow test', async ({ page }) => {
  test.slow();
  // ... test code
});
```

### Coverage Not Generated
```bash
# Install pytest-cov
pip install pytest-cov
pytest --cov=app
```

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development with Python](https://books.agiliq.com/projects/tdd-with-python/)

---

## Quick Reference

### Common Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific marker
pytest -m unit

# Run verbose
pytest -v

# Stop on first failure
pytest -x

# Run failed tests only
pytest --lf

# Run parallel
pytest -n auto
```

### Test File Template

```python
"""
Tests for [feature].
"""
import pytest

@pytest.mark.unit
class TestFeature:
    @pytest.fixture
    def setup_data(self):
        return {"key": "value"}

    def test_basic_functionality(self, setup_data):
        assert setup_data["key"] == "value"

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        assert True
```

For questions or issues, please refer to the project documentation or create an issue in the repository.
