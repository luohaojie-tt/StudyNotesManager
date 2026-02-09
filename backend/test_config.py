"""Test configuration loading"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.config import settings
    print("[OK] Config loaded successfully")
    print(f"  - APP_NAME: {settings.APP_NAME}")
    print(f"  - APP_VERSION: {settings.APP_VERSION}")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - CORS_ORIGINS: {settings.CORS_ORIGINS}")
except Exception as e:
    print(f"[FAIL] Config loading failed: {e}")
    sys.exit(1)
