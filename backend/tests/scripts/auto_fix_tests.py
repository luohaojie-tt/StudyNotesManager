"""
Automated script to fix security issues in test files.

This script will:
1. Replace hardcoded passwords with fixtures
2. Replace hardcoded emails with fixtures  
3. Fix hardcoded URLs in E2E tests
4. Add necessary imports

Usage:
    python backend/tests/scripts/auto_fix_tests.py
"""
import re
from pathlib import Path


def add_fixture_imports(content: str) -> str:
    """Add necessary fixture imports if not present.
    
    Args:
        content: File content
        
    Returns:
        Updated content with imports
    """
    # Check if imports already exist
    if 'from tests.fixtures.test_data import' in content:
        return content
        
    # Find the import section and add our fixtures
    lines = content.split('\n')
    import_section_end = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_section_end = i + 1
        elif import_section_end > 0 and not (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
            break
            
    # Insert our imports
    fixtures_import = 'from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data'
    
    if import_section_end > 0:
        lines.insert(import_section_end, fixtures_import)
        lines.insert(import_section_end + 1, '')
    else:
        # No existing imports, add at the beginning
        lines.insert(0, fixtures_import)
        lines.insert(1, '')
        
    return '\n'.join(lines)


def fix_test_file(file_path: Path) -> bool:
    """Fix security issues in a test file.
    
    Args:
        file_path: Path to test file
        
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 1. Add necessary imports
        content = add_fixture_imports(content)
        
        # 2. Replace hardcoded passwords in function signatures
        # def test_something(self, valid_password):
        def_pattern = r'def (test_\w+)\(self\):'
        def_replacement = r'\1(self, valid_password):'
        content = re.sub(def_pattern, def_replacement, content)
        
        async_def_pattern = r'async def (test_\w+)\(self, (?:valid_email|valid_password|client)\):'
        async_def_replacement = r'async def \1(self, valid_email, valid_password, client):'
        # Only add if not already has these params
        if 'valid_email' not in content or 'valid_password' not in content:
            content = re.sub(
                r'async def (test_\w+)\(self, client\):',
                async_def_replacement,
                content
            )
        
        # 3. Replace hardcoded password values (with realistic passwords for tests)
        # Keep it simple - replace in data dictionaries
        content = re.sub(
            r'"password":\s*"SecurePass\d+[!]*"[\s,]*',
            f'"password": valid_password, ',
            content
        )
        content = re.sub(
            r"'password':\s*'SecurePass\\d+[!]*'[\s,]*",
            f"'password': valid_password, ",
            content
        )
        
        # 4. Replace hardcoded email values
        content = re.sub(
            r'"email":\s*"test@example\.com"[\s,]*',
            f'"email": valid_email, ',
            content
        )
        content = re.sub(
            r"'email':\s*'test@example\.com'[\s,]*",
            f"'email': valid_email, ",
            content
        )
        
        # 5. Fix assertion comparisons (be careful with these)
        content = re.sub(
            r'assert user\.email == "test@example\.com"',
            'assert user.email == valid_email',
            content
        )
        content = re.sub(
            r'assert user\.email == \'test@example\.com\'',
            "assert user.email == valid_email",
            content
        )
        
        # 6. Replace hardcoded password in get_password_hash calls
        content = re.sub(
            r'get_password_hash\("SecurePass\d+"\)',
            'get_password_hash(valid_password)',
            content
        )
        content = re.sub(
            r"get_password_hash\('SecurePass\\d+'\)",
            'get_password_hash(valid_password)',
            content
        )
        
        # 7. Fix hardcoded URLs in E2E tests
        content = re.sub(
            r'"http://localhost:3000/(\w+)"',
            r'f"{BASE_URL}/\1"',
            content
        )
        content = re.sub(
            r"'http://localhost:3000/(\w+)'",
            r"f'{BASE_URL}/\1'",
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return False


def main():
    """Main function to fix all test files."""
    tests_dir = Path(__file__).parent.parent.parent / "tests"
    
    print("=" * 80)
    print("AUTO FIX TEST SECURITY ISSUES")
    print("=" * 80)
    print()
    
    fixed_files = []
    
    # Find all test files
    for test_file in tests_dir.rglob("test_*.py"):
        if fix_test_file(test_file):
            fixed_files.append(test_file)
            print(f"[OK] Fixed: {test_file.relative_to(tests_dir.parent)}")
        else:
            print(f"[SKIP] {test_file.relative_to(tests_dir.parent)}")
    
    print()
    print("=" * 80)
    print(f"Total files fixed: {len(fixed_files)}")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review the changes")
    print("2. Run tests to verify: pytest tests/")
    print("3. Commit the fixes")


if __name__ == "__main__":
    main()
