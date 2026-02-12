"""
Test fixtures and data generators for secure testing.

This module provides secure test data that doesn't leak sensitive patterns.
Uses Faker for generating realistic but fake test data.
"""
import string
from uuid import uuid4
from faker import Faker
import pytest


fake = Faker()


class TestDataGenerator:
    """Generate secure test data that doesn't leak patterns."""

    @staticmethod
    def random_password(min_length: int = 8, max_length: int = 20) -> str:
        """Generate a random password that meets security requirements.

        Args:
            min_length: Minimum password length
            max_length: Maximum password length (max 72 for bcrypt compatibility)

        Returns:
            Random password with letters and digits
        """
        import secrets
        import random

        # Limit max length to 72 for bcrypt compatibility
        max_length = min(max_length, 72)
        length = random.randint(min_length, max_length)

        # Ensure password has at least one of each required character type
        password = [
            secrets.choice(string.ascii_uppercase),  # At least one uppercase
            secrets.choice(string.ascii_lowercase),  # At least one lowercase
            secrets.choice(string.digits),            # At least one digit
        ]

        # Fill rest with random characters from all categories
        all_chars = string.ascii_letters + string.digits
        password.extend(secrets.choice(all_chars) for _ in range(length - 3))

        # Shuffle to avoid predictable pattern
        random.shuffle(password)

        return ''.join(password)

    @staticmethod
    def random_email() -> str:
        """Generate a random email address.

        Returns:
            Random email address
        """
        return fake.email()

    @staticmethod
    def random_full_name() -> str:
        """Generate a random full name.

        Returns:
            Random full name
        """
        return fake.name()

    @staticmethod
    def random_username() -> str:
        """Generate a random username.

        Returns:
            Random username
        """
        return fake.user_name()[:20]  # Limit to 20 characters


# Global test data generator instance
test_data = TestDataGenerator()


@pytest.fixture
def valid_password():
    """Generate a valid password for testing."""
    return test_data.random_password()


@pytest.fixture
def valid_email():
    """Generate a valid email for testing."""
    return test_data.random_email()


@pytest.fixture
def valid_full_name():
    """Generate a valid full name for testing."""
    return test_data.random_full_name()


@pytest.fixture
def valid_username():
    """Generate a valid username for testing."""
    return test_data.random_username()


@pytest.fixture
def test_user_data(valid_email, valid_password, valid_full_name):
    """Generate complete user registration data.

    Returns:
        Dictionary with user registration data
    """
    return {
        "email": valid_email,
        "password": valid_password,
        "full_name": valid_full_name,
    }


@pytest.fixture
def test_login_data(valid_email, valid_password):
    """Generate complete user login data.

    Returns:
        Dictionary with user login data
    """
    return {
        "email": valid_email,
        "password": valid_password,
    }


@pytest.fixture
def multiple_test_users(count: int = 3):
    """Generate multiple test users.

    Args:
        count: Number of users to generate

    Returns:
        List of user data dictionaries
    """
    return [
        {
            "email": test_data.random_email(),
            "username": test_data.random_username(),
            "password": test_data.random_password(),
            "full_name": test_data.random_full_name(),
        }
        for _ in range(count)
    ]


# Keep backward compatibility with old test patterns
# These are deprecated but maintained for existing tests
LEGACY_TEST_PASSWORD = "TestPassword123!"  # Only for backward compatibility
LEGACY_TEST_EMAIL = "test@example.com"
