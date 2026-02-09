"""Basic test to verify project structure"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

print("Checking backend project structure...")

# Check directories
dirs = [
    "app",
    "app/api",
    "app/core",
    "app/models",
    "app/schemas",
    "app/services",
    "app/utils",
    "tests",
    "alembic",
]

for dir_path in dirs:
    full_path = Path(dir_path)
    if full_path.exists() and full_path.is_dir():
        print(f"[OK] {dir_path}/ exists")
    else:
        print(f"[FAIL] {dir_path}/ missing")

# Check key files
files = [
    "app/__init__.py",
    "app/main.py",
    "app/core/config.py",
    "app/core/database.py",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "alembic.ini",
    "pyproject.toml",
]

for file_path in files:
    full_path = Path(file_path)
    if full_path.exists() and full_path.is_file():
        print(f"[OK] {file_path} exists")
    else:
        print(f"[FAIL] {file_path} missing")

print("\nProject structure check complete!")
