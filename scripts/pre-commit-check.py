#!/usr/bin/env python
"""
Pre-commit hook to enforce Git workflow standards.

This hook prevents direct commits to protected branches and ensures
that all development happens on feature branches.

Protected branches:
- develop
- master
- main
- test/*

Usage:
    Copy this script to .git/hooks/pre-commit and make it executable:
    cp scripts/pre-commit-check.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""

import sys
import subprocess


def get_current_branch():
    """Get the current branch name."""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return result
    except subprocess.CalledProcessError:
        return None


def is_protected_branch(branch):
    """Check if the branch is protected."""
    if not branch:
        return True

    protected_branches = ['develop', 'master', 'main']
    protected_patterns = ['test/', 'release/', 'hotfix/']

    # Direct match
    if branch in protected_branches:
        return True

    # Pattern match
    for pattern in protected_patterns:
        if branch.startswith(pattern):
            return True

    return False


def main():
    """Main entry point."""
    branch = get_current_branch()

    # Allow detached HEAD state (rebase, merge, etc.)
    if branch == 'HEAD':
        sys.exit(0)

    # Check if branch is protected
    if is_protected_branch(branch):
        print("=" * 70)
        print("🚫 COMMIT BLOCKED")
        print("=" * 70)
        print()
        print(f"You are trying to commit directly to protected branch: '{branch}'")
        print()
        print("This violates the Git workflow standards!")
        print()
        print("Required workflow:")
        print("  1. Create a feature branch:")
        print(f"       git checkout -b frontend-dev/your-feature-name")
        print(f"     or git checkout -b backend-dev/your-feature-name")
        print()
        print("  2. Make your changes and commit on the feature branch")
        print()
        print("  3. Push to remote:")
        print(f"       git push origin frontend-dev/your-feature-name")
        print()
        print("  4. Create a Pull Request")
        print()
        print("  5. Wait for code review and approval")
        print()
        print("  6. Merge using 'Squash and Merge'")
        print()
        print("For details, see: docs/09-workflow/TEAMMATES_GUIDELINES.md")
        print()
        print("=" * 70)
        print()
        print("If you believe this is an error, contact team-lead.")
        print()
        sys.exit(1)

    # Success - feature branch is OK
    print(f"✓ OK: Committing on feature branch '{branch}'")
    sys.exit(0)


if __name__ == '__main__':
    main()
