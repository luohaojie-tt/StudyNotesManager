#!/usr/bin/env python3
"""
安装Git Hooks脚本
自动配置commit message检查hook
"""

import os
import shutil
from pathlib import Path

def setup_git_hooks():
    """设置Git hooks"""

    # 获取项目根目录
    root_dir = Path(__file__).parent
    git_hooks_dir = root_dir / '.git' / 'hooks'

    # 确保hooks目录存在
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # 复制commit-msg hook
    hook_source = root_dir / '.git' / 'hooks' / 'commit-msg.py'
    hook_target = git_hooks_dir / 'commit-msg'

    shutil.copy(hook_source, hook_target)

    # 设置执行权限（Unix系统）
    try:
        os.chmod(hook_target, 0o755)
    except:
        pass  # Windows可能不支持

    print("✅ Git Hooks 安装完成！")
    print("   - Commit Message检查已启用")
    print("   - 不符合规范的commit将被拒绝")
    print("")
    print("📖 请阅读 TEAMMATES_GUIDELINES.md 了解完整规范")

if __name__ == '__main__':
    setup_git_hooks()
