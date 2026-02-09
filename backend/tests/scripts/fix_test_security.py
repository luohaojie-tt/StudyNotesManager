"""
Script to identify and fix security issues in test files.

CRITICAL Issues to Fix:
1. Remove hardcoded passwords like "SecurePass123!"
2. Remove hardcoded emails like "test@example.com"
3. Remove hardcoded URLs in E2E tests
4. Ensure test isolation
5. Fix false positive tests

Usage:
    python backend/tests/scripts/fix_test_security.py
"""
import os
import re
from pathlib import Path


# Patterns to find and replace
SECURITY_PATTERNS = {
    # Hardcoded passwords
    r'"SecurePass\d+!"': lambda m: f'valid_password',
    r"'SecurePass\d+!'": lambda m: f"valid_password",
    r'"SecurePass\d+"': lambda m: f'valid_password',
    r"'SecurePass\d+'": lambda m: f"valid_password",
    
    # Hardcoded emails (but keep @example.com for test domains)
    r'"test@example\.com"': lambda m: 'valid_email',
    r"'test@example\.com'": lambda m: "valid_email",
    
    # Hardcoded URLs in E2E tests
    r'"http://localhost:3000/\w+"': lambda m: 'f"{BASE_URL}/page"',
    r"'http://localhost:3000/\w+'": lambda m: "f'{BASE_URL}/page'",
}


def find_security_issues(file_path: Path) -> list:
    """Find security issues in a test file.
    
    Args:
        file_path: Path to test file
        
    Returns:
        List of found issues with line numbers
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # Check for hardcoded passwords
            if 'SecurePass' in line and 'password' in line.lower():
                issues.append({
                    'line': line_num,
                    'type': 'CRITICAL',
                    'issue': 'Hardcoded password pattern',
                    'content': line.strip()
                })
            
            # Check for hardcoded test emails
            if 'test@example.com' in line:
                issues.append({
                    'line': line_num,
                    'type': 'CRITICAL',
                    'issue': 'Hardcoded test email',
                    'content': line.strip()
                })
            
            # Check for hardcoded URLs in E2E tests
            if 'localhost:3000' in line:
                issues.append({
                    'line': line_num,
                    'type': 'CRITICAL',
                    'issue': 'Hardcoded URL in E2E test',
                    'content': line.strip()
                })
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues


def scan_test_directory(test_dir: Path) -> dict:
    """Scan all test files for security issues.
    
    Args:
        test_dir: Path to tests directory
        
    Returns:
        Dictionary mapping file paths to their issues
    """
    all_issues = {}
    
    for test_file in test_dir.rglob("test_*.py"):
        issues = find_security_issues(test_file)
        if issues:
            all_issues[str(test_file)] = issues
            
    return all_issues


def generate_report(issues: dict) -> str:
    """Generate a security issues report.
    
    Args:
        issues: Dictionary of issues found
        
    Returns:
        Formatted report string
    """
    report = ["=" * 80]
    report.append("TEST SECURITY ISSUES REPORT")
    report.append("=" * 80)
    report.append("")
    
    total_files = len(issues)
    total_issues = sum(len(file_issues) for file_issues in issues.values())
    
    report.append(f"Total files with issues: {total_files}")
    report.append(f"Total issues found: {total_issues}")
    report.append("")
    
    for file_path, file_issues in issues.items():
        report.append(f"File: {file_path}")
        report.append("-" * 80)
        
        for issue in file_issues:
            report.append(f"  Line {issue['line']}: [{issue['type']}] {issue['issue']}")
            report.append(f"    {issue['content']}")
            report.append("")
            
    return "\n".join(report)


def main():
    """Main function to scan and report test security issues."""
    # Get the tests directory
    tests_dir = Path(__file__).parent.parent.parent / "tests"
    
    if not tests_dir.exists():
        print(f"Tests directory not found: {tests_dir}")
        return
        
    print(f"Scanning test files in: {tests_dir}")
    print()
    
    # Scan for issues
    issues = scan_test_directory(tests_dir)
    
    # Generate and print report
    report = generate_report(issues)
    print(report)
    
    # Save report to file
    report_file = Path(__file__).parent.parent / "TEST_SECURITY_ISSUES.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\nReport saved to: {report_file}")
    print("\nNext steps:")
    print("1. Review the issues listed above")
    print("2. Update tests to use fixtures from fixtures/test_data.py")
    print("3. Re-run this script to verify fixes")


if __name__ == "__main__":
    main()
