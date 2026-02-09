#!/bin/bash
# Git Commit Hook - 自动检查Commit Message规范

# 获取commit message
COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Conventional Commits格式检查
PATTERN="^(feat|fix|refactor|docs|test|chore|perf|ci|style|build)(\(.+\))?: .{1,}"

if ! [[ "$COMMIT_MSG" =~ $PATTERN ]]; then
    echo "❌ Commit Message格式错误！"
    echo ""
    echo "请遵循 Conventional Commits 格式："
    echo "  <type>: <description>"
    echo ""
    echo "Type类型："
    echo "  feat     - 新功能"
    echo "  fix      - Bug修复"
    echo "  refactor - 代码重构"
    echo "  docs     - 文档更新"
    echo "  test     - 测试相关"
    echo "  chore    - 构建/工具链"
    echo "  perf     - 性能优化"
    echo "  ci       - CI配置"
    echo ""
    echo "示例："
    echo "  feat: 添加用户注册API"
    echo "  fix: 修复登录验证错误"
    echo "  docs: 更新API文档"
    echo ""
    echo "请重新编写commit message。"
    exit 1
fi

echo "✅ Commit Message格式检查通过"
exit 0
