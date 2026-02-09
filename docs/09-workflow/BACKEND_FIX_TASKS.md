# Backend Code Review Issues - 修复任务清单

> 📌 **重要提示**: 这些问题来自code-reviewer agents的审查结果

**分配给**: backend-dev
**创建日期**: 2026-02-09
**优先级**: 🔴 CRITICAL > 🟠 HIGH > 🟡 MEDIUM

---

## 🔴 CRITICAL问题（必须立即修复）

### 1. 认证系统 - 认证端点未实现

**文件**: `backend/app/api/auth.py:51-63`
**问题**: `/api/auth/me`端点使用错误的依赖，导致认证绕过
**修复**:
```python
# 错误:
async def get_me(current_user: User = Depends(get_db)):

# 正确:
async def get_me(current_user_tuple: tuple = Depends(get_current_active_user)):
```

### 2. 认证系统 - 调用不存在的方法

**文件**: `backend/app/api/dependencies.py:54`
**问题**: `get_current_user`调用了不存在的`AuthService.get_current_user()`
**修复**: 改为调用`get_user_by_id(UUID(user_id))`

### 3. 认证系统 - 弱JWT密钥

**文件**: `backend/app/core/config.py:35`
**问题**: 硬编码的弱默认密钥
**修复**:
- 移除默认值或使用强随机值
- 添加validator确保生产环境使用32+字符密钥

### 4. 认证系统 - 缺少Rate Limiting

**文件**: `backend/app/api/auth.py`
**问题**: 登录/注册端点无速率限制，可暴力破解
**修复**: 使用slowapi添加速率限制（5次/分钟）

### 5. 脑图功能 - AI Prompt注入

**文件**: `backend/app/services/deepseek_service.py:193-198`
**问题**: 用户输入直接插入AI prompt，可注入恶意指令
**修复**: 实现`_sanitize_for_prompt()`方法过滤注入模式

### 6. 脑图功能 - max_levels参数未验证

**文件**: `backend/app/api/mindmaps.py:16-22`
**问题**: 无验证的参数可导致DoS
**修复**: 添加Pydantic验证（1-10范围）

### 7. OCR功能 - 文件类型验证不足

**文件**: `backend/app/api/notes.py:42-54`
**问题**: 只检查扩展名，不检查文件内容（魔数）
**修复**: 使用python-magic库验证MIME类型

### 8. OCR功能 - 无速率限制

**文件**: `backend/app/api/notes.py:17-106`
**问题**: 上传端点无速率限制
**修复**: 添加10次/分钟限制

### 9. OCR功能 - 路径遍历风险

**文件**: `backend/app/services/oss_service.py:59-62`
**问题**: 使用原始文件名可能导致路径遍历
**修复**: 实现sanitize_filename()清理路径

### 10. OCR功能 - 缺少病毒扫描

**文件**: `backend/app/api/notes.py:30-62`
**问题**: 上传文件不扫描恶意软件
**修复**: 集成ClamAV扫描

---

## 🟠 HIGH问题（应当修复）

### 1. 认证系统 - 缺少Token刷新端点
**文件**: `backend/app/api/auth.py`
**修复**: 实现`POST /api/auth/refresh`端点

### 2. 认证系统 - 缺少登出/Token撤销
**文件**: `backend/app/api/auth.py`
**修复**: 实现Token黑名单或Redis存储

### 3. 认证系统 - 密码强度不够
**文件**: `backend/app/schemas/auth.py:15-22`
**修复**: 要求12+字符，大小写+数字+特殊字符

### 4. 脑图功能 - HTTP客户端资源泄漏
**文件**: `backend/app/api/mindmaps.py:39-45`
**修复**: 使用async with管理客户端

### 5. 脑图功能 - 验证逻辑重复
**文件**: mindmap_service.py和deepseek_service.py
**修复**: 提取到共享validator模块

### 6. 脑图功能 - AI响应验证不足
**文件**: `backend/app/services/deepseek_service.py:266-291`
**修复**: 添加XSS和内容长度检查

### 7. OCR功能 - 内存耗尽风险
**文件**: `backend/app/api/notes.py:31`
**修复**: 使用流式读取，限制内存

### 8. OCR功能 - Content-Length未验证
**文件**: `backend/app/api/notes.py:31-32`
**修复**: 读取前先检查header

---

## 🟡 MEDIUM问题（建议改进）

### 1. 所有模块 - console.log残留
**修复**: 使用logging库或生产环境禁用

### 2. 所有模块 - 缺少审计日志
**修复**: 添加结构化日志记录关键操作

### 3. 所有模块 - 错误消息泄露
**修复**: 使用通用错误消息

### 4. 所有模块 - 缺少输入长度限制
**修复**: 在Pydantic schemas中添加max_length

---

## 📝 修复顺序建议

### 阶段1: 安全关键（今天）
1. 修复所有CRITICAL问题（10个）
2. 添加Rate Limiting到所有公开端点
3. 修复认证绕过漏洞

### 阶段2: 功能完善（本周）
1. 修复所有HIGH问题（8个）
2. 实现Token刷新和撤销
3. 增强密码验证

### 阶段3: 质量提升（下周）
1. 修复MEDIUM问题
2. 添加审计日志
3. 改进错误处理

---

## ✅ 验证标准

修复后的代码必须：
- [ ] 通过所有单元测试
- [ ] 通过所有集成测试
- [ ] code-reviewer agent重新审查通过
- [ ] 测试覆盖率>80%
- [ ] 无CRITICAL问题残留

---

## 📚 参考资料

- Code Review报告: `CODE_REVIEW_VIOLATION_REPORT.md`
- Team规范: `TEAMMATES_GUIDELINES.md`
- Git工作流: `GIT_WORKFLOW.md`

---

**任务分配人**: team-lead
**执行人**: backend-dev
**状态**: 🔴 待开始
