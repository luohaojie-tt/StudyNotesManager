# Scripts - 项目工具脚本

> 🛠️ 项目开发和部署相关的工具脚本

## 📋 脚本列表

### setup-git-hooks.py
**用途**: 自动安装Git hooks，强制检查commit message格式

```bash
python scripts/setup-git-hooks.py
```

**功能**:
- 自动配置`.git/hooks/commit-msg` hook
- 检查commit message是否符合Conventional Commits规范
- 不符合规范的commit将被拒绝

**为什么要用**:
- 确保所有teammates遵守Git规范
- 保持Git历史清晰
- 自动化代码规范检查

### git-setup.sh
**用途**: Git hooks的bash版本（Linux/macOS）

```bash
bash scripts/git-setup.sh
```

---

## 🔧 使用方法

### 初次设置

```bash
# 1. 克隆项目后，立即运行
python scripts/setup-git-hooks.py

# 2. 验证安装
ls .git/hooks/commit-msg

# 3. 测试hook
git commit -m "invalid message"  # 应该被拒绝
git commit -m "feat: add feature"  # 应该通过
```

### teammates启动前

所有teammates在开始工作前，必须：

1. ✅ 阅读文档
2. ✅ 运行`python scripts/setup-git-hooks.py`
3. ✅ 确认Git hooks已安装
4. ✅ 开始工作

---

## 📝 添加新脚本

当添加新的工具脚本时：

1. 将脚本放在`scripts/`目录
2. 在这个README中说明用途
3. 添加使用示例
4. 更新相关文档

---

**最后更新**: 2026-02-09
