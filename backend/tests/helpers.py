"""Test helpers for the backend application."""

from typing import Dict, Any
from tests.fixtures.test_data import test_data


class TestHelpers:
    """Test辅助工具类"""

    @staticmethod
    def create_user_data(**kwargs) -> Dict[str, Any]:
        """创建测试用户数据"""
        data = test_data.random_user_data()
        data.update(kwargs)
        return data

    @staticmethod
    def create_note_data(**kwargs) -> Dict[str, Any]:
        """创建测试笔记数据"""
        data = test_data.random_note_data()
        data.update(kwargs)
        return data