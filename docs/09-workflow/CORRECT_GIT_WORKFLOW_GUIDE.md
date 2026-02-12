# 正确的Git Workflow流程

**创建时间**: 2026-02-10
**目的**: 确保所有修改遵循规范流程

---

## ❌ 之前的错误做法

```bash
# 错误：直接在master分支修改和commit
git checkout master
# ... 修改代码 ...
git commit -m "fix: something"
git push origin master
```

**问题**:
- ❌ 没有feature分支
- ❌ 没有Pull Request
- ❌ 没有code review
- ❌ 直接修改master分支

---

## ✅ 正确的流程

### 步骤1: 创建feature分支

```bash
git checkout master
git pull origin master
git checkout -b feature/<task-name>

示例:
git checkout -b feature/token-expiry-handling
git checkout -b feature/type-safety-improvements
git checkout -b feature/security-headers
```

### 步骤2: 在feature分支进行修改

```bash
# 在feature分支上工作
git checkout feature/token-expiry-handling
# ... 修改代码 ...
git add .
git commit -m "feat: implement token expiry handling"
```

### 步骤3: Push到remote

```bash
git push -u origin feature/token-expiry-handling
```

### 步骤4: 创建Pull Request

使用GitHub CLI或网页创建PR:

```bash
gh pr create \
  --title "feat: implement token expiry handling" \
  --body "## Summary
- Add 401 response interceptor
- Implement auto logout on token expiry

## Test plan
- [ ] Test token expiry scenario
- [ ] Verify redirect to login
"
```

### 步骤5: Code Review (必须!)

**关键步骤**: 必须经过code-reviewer agent审核

```bash
# 启动code-reviewer agent
# Agent会检查：
- 代码质量
- 安全问题
- 性能问题
- 最佳实践
- 潜在bug
```

### 步骤6: 根据反馈修改

如果review发现issue：

```bash
# 在feature分支上修改
git add .
git commit -m "fix: address code review feedback"
git push origin feature/token-expiry-handling
# PR自动更新
```

### 步骤7: 再次review

修改后需要**再次code review**，直到所有CRITICAL和HIGH问题解决。

### 步骤8: 合并PR

只有满足以下条件才能合并：

- ✅ 所有CRITICAL问题已解决
- ✅ 所有HIGH问题已解决
- ✅ 至少1个reviewer approve
- ✅ CI检查通过
- ✅ 测试通过

```bash
# 使用gh命令合并
gh pr merge --squash --delete-branch
```

---

## 📋 当前任务的Feature分支

| 任务 | Feature分支 | 负责人 | 状态 |
|------|-------------|--------|------|
| Task #4 | feature/token-expiry-handling | frontend-dev | ⏸️ 待开始 |
| Task #1 | feature/type-safety-and-search | frontend-dev-2 | ⏸️ 待开始 |
| Task #3 | feature/security-headers | frontend-dev-3 | ⏸️ 待开始 |

---

## 🚀 执行计划

### 第1轮：Task #4 (frontend-dev)
```bash
cd frontend
git checkout feature/token-expiry-handling
# frontend-dev在这个分支工作
# 完成后push
# 创建PR
# code review
# 合并
```

### 第2轮：Task #1 (frontend-dev-2)
```bash
cd frontend
git checkout feature/type-safety-and-search
# frontend-dev-2在这个分支工作
# ...
```

### 第3轮：Task #3 (frontend-dev-3)
```bash
cd frontend
git checkout feature/security-headers
# frontend-dev-3在这个分支工作
# ...
```

---

## ⚠️ 强制执行机制

### Pre-commit Hook
`scripts/pre-commit-check.py` 会检查：
- ❌ 不能直接commit到master/main分支
- ✅ 必须在feature/xxx分支上工作
- ✅ commit message遵循conventional commits格式

### GitHub Actions (待配置)
```yaml
# .github/workflows/pr-check.yml
name: PR Check
on: pull_request
jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - name: Run code-reviewer
        run: |
          # 自动code review
```

---

## 📝 检查清单

提交任何代码前，确保：

- [ ] 在feature分支上工作
- [ ] 不是master/main分支
- [ ] 代码已测试
- [ ] 创建了Pull Request
- [ ] 经过了code review
- [ ] 所有CRITICAL/HIGH问题已解决
- [ ] 至少1个approve
- [ ] 准备好合并

---

## 🎯 总结

**简单记忆**: FPRC流程
- **F**eature branch (功能分支)
- **P**ush (推送)
- **R**equest (创建PR)
- **C**ode Review (代码审核) ← **最关键！**

---

**创建人**: team-lead
**日期**: 2026-02-10
**原因**: 之前违反了Git workflow规范，需要纠正
