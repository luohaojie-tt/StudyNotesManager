"""Boundary condition tests for the backend application."""

import pytest
from app.schemas.auth import UserRegister


class TestBoundaryConditions:
    """边界条件测试"""

    def test_empty_email_raises_error(self):
        """空邮箱应该报错"""
        with pytest.raises(ValueError):
            UserRegister(email="", password="test123")

    def test_max_length_input(self):
        """超长输入应该报错"""
        long_email = "a" * 1000 + "@example.com"
        with pytest.raises(ValueError):
            UserRegister(email=long_email, password="test123")

    def test_special_characters_in_password(self):
        """特殊字符密码应该接受"""
        user = UserRegister(
            email="test@example.com",
            password="P@ssw0rd!#$%",
            full_name="Test User"
        )
        assert user.email == "test@example.com"