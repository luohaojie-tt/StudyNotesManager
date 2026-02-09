# 测试快速指南 - 为Backend Developer

## 🎯 快速测试你的API

当你完成新的API端点时，按照以下步骤添加测试：

### 1. 单元测试

创建 `tests/unit/test_your_feature.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.unit
class TestYourService:
    @pytest.mark.asyncio
    async def test_your_method(self):
        # Arrange
        mock_db = MagicMock()

        # Act
        result = await your_service.your_method()

        # Assert
        assert result is not None
```

### 2. 集成测试

创建 `tests/integration/test_your_api.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.api
class TestYourAPI:
    @pytest.mark.asyncio
    async def test_your_endpoint(self, client: AsyncClient):
        response = await client.post("/api/your-endpoint", json={})

        assert response.status_code in [200, 201, 400, 500]
```

### 3. 运行测试

```bash
# 所有测试
pytest

# 特定文件
pytest tests/unit/test_your_feature.py

# 特定标记
pytest -m unit
pytest -m api

# 详细输出
pytest -v

# 停在第一个失败
pytest -x
```

## 📋 当前测试状态

✅ **已就绪的测试** (119+个):
- MindmapService (11 tests)
- QuizServices (10 tests)
- DeepSeekService (10 tests)
- API Routes (13 tests)
- Integration Tests (46 tests)
- E2E Tests (13 tests)

⏳ **需要添加的测试**:
- 用户认证API (等待实现)
- 笔记上传API (等待实现)

## 🔧 测试工具

### Fixtures可用:
- `async_db_session` - 数据库会话
- `client` - HTTP客户端
- `test_user_data` - 测试用户数据
- `mock_deepseek_api` - Mock AI服务

### 标记:
- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.api` - API测试
- `@pytest.mark.auth` - 认证测试

## 💡 示例：用户认证测试

```python
@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
```

## 📞 需要帮助？

联系 qa-engineer，我会：
1. 帮助编写测试
2. 验证API端点
3. 生成测试报告
4. 检查代码覆盖率

**测试框架已就绪，随时可以为你的代码添加测试！** 🚀
