# Testing Guide

## 运行测试

```bash
# 所有测试
pytest

# 带覆盖率
pytest --cov=app --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

## 测试规范

1. **命名**: `test_{feature}_{scenario}_{expected}`
2. **Fixture**: 共享fixture放 `conftest.py`
3. **Mock**: 只mock外部依赖
4. **覆盖率目标**: ≥85%

## 测试数据

使用 `tests/fixtures/test_data.py` 中的 `TestDataGenerator`:

```python
from tests.fixtures.test_data import test_data

user_data = test_data.random_user_data()
note_data = test_data.random_note_data()
```

## 测试辅助工具

使用 `tests/helpers.py` 中的 `TestHelpers`:

```python
from tests.helpers import TestHelpers

# 创建测试用户数据
user_data = TestHelpers.create_user_data(email="test@example.com")

# 创建测试笔记数据
note_data = TestHelpers.create_note_data(title="Test Note")
```

## 测试分类

- **Unit Tests**: `tests/unit/` - 单元测试
- **Integration Tests**: `tests/integration/` - 集成测试
- **API Tests**: `tests/api/` - API测试
- **E2E Tests**: `tests/e2e/` - 端到端测试
- **Performance Tests**: `tests/test_performance.py` - 性能测试
- **Boundary Tests**: `tests/test_boundary.py` - 边界测试
- **Error Scenarios**: `tests/test_error_scenarios.py` - 错误场景测试

## 并行执行

安装 pytest-xdist 后可以并行执行测试:

```bash
pip install pytest-xdist
pytest -n auto
```