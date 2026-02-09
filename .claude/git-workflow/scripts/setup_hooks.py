#!/usr/bin/env python3
"""
Setup Git hooks for the project.
Installs commit-msg hook to validate commit message format.
"""

import os
import shutil
from pathlib import Path


def setup_hooks():
    """Setup Git hooks for commit message validation."""

    project_root = Path(__file__).parent.parent.parent
    git_hooks_dir = project_root / '.git' / 'hooks'

    # Ensure hooks directory exists
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy commit-msg hook
    hook_source = project_root / '.git' / 'hooks' / 'commit-msg.py'
    hook_target = git_hooks_dir / 'commit-msg'

    if hook_source.exists():
        shutil.copy(hook_source, hook_target)
        print("[OK] Git hooks installed successfully")
        print("    - Commit message validation enabled")
        print("    - Invalid commits will be rejected")
        return 0
    else:
        print("[ERROR] commit-msg.py not found")
        print("Please ensure the hook file exists")
        return 1


if __name__ == '__main__':
    exit(setup_hooks())
