# 🚨 Backend-dev立即行动指示

**时间**: 2026-02-09 17:25
**来自**: team-lead
**给**: backend-dev

---

## ⚠️ 重要澄清

### Task #15已完成 - 不要再处理

**Task #15: AI Mindmap Generation Feature**
- ✅ 已完成
- ✅ Commit: f19c74e
- ✅ 测试通过
- ✅ **不需要再处理**

---

## 🎯 你的当前任务：Task #56

### 立即开始：Backend HIGH优先级问题 (20个)

**任务编号**: #56
**优先级**: HIGH
**状态**: 🔄 **in_progress** (已分配给你)
**预计时间**: 1小时
**下次报告**: 17:55 (30分钟后)

---

## 📋 必须修复的HIGH问题

### 第1优先级：认证系统增强 (8个) 🚨

**立即开始这些**：

#### 1. Token刷新端点 (最重要)
```python
# backend/app/api/auth.py
@router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """使用refresh token获取新的access token"""
    # 验证refresh token
    # 生成新的access token
    # 返回新token
```

#### 2. 登出/Token撤销
```python
# backend/app/api/auth.py
@router.post("/logout")
async def logout(current_user: tuple = Depends(get_current_active_user)):
    """撤销当前token"""
    # 将token加入黑名单
    # 或从Redis删除
```

#### 3. 密码强度验证
```python
# backend/app/schemas/auth.py
def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 12:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*]', password):
        return False
    return True
```

#### 4. Token过期时间配置化
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=5, le=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
```

#### 5-8. 其他认证HIGH问题
- 密码历史检查
- 账户锁定机制
- 邮件验证
- 密码重置流程

---

### 第2优先级：脑图功能优化 (6个)

9. **修复资源泄漏** (重要)
```python
# backend/app/api/mindmaps.py
# Before:
client = httpx.AsyncClient()
# ... 使用客户端

# After:
async with httpx.AsyncClient() as client:
    # ... 使用客户端
    # 自动关闭，防止泄漏
```

10-14. 其他脑图HIGH问题
- 验证逻辑重复
- AI响应验证
- 缓存机制
- 详细日志
- 错误恢复

---

### 第3优先级：OCR功能增强 (6个)

15. **内存防护** (重要)
```python
# backend/app/api/notes.py
# 使用流式读取
async def read_file_in_chunks(file: UploadFile, chunk_size: int = 8192):
    """流式读取文件，防止内存耗尽"""
    while chunk := await file.read(chunk_size):
        yield chunk
```

16-20. 其他OCR HIGH问题
- Content-Length验证
- CSRF保护
- 文件大小限制
- 上传进度
- 错误重试

---

## 🚀 立即行动计划

### 第1步：阅读任务详情 (5分钟)
- 打开 `docs/09-workflow/BACKEND_FIX_TASKS.md`
- 阅读所有HIGH问题详细说明
- 理解每个问题的修复方案

### 第2步：从认证系统开始 (20分钟)
- 实现Token刷新端点
- 实现登出端点
- 增强密码验证
- 配置化Token过期时间

### 第3步：修复资源泄漏 (10分钟)
- 修复HTTP客户端资源泄漏
- 测试内存使用情况

### 第4步：继续其他HIGH问题 (25分钟)
- 按优先级修复
- 每修复一个测试一次
- 记录进度

### 第5步：30分钟时报告 (17:55)
- 已完成的问题数
- 遇到的困难
- 剩余问题预计时间

---

## ⚠️ 不要混淆

### ❌ 不要做
- 不要再处理Task #15（已完成）
- 不要添加新功能
- 不要修改非HIGH优先级的问题

### ✅ 要做
- 专注Task #56的20个HIGH问题
- 按优先级顺序修复
- 30分钟报告一次
- 遇到阻塞立即报告

---

## 📊 进度跟踪

### 当前 (17:25)
- [ ] Token刷新端点 (0/1)
- [ ] 登出端点 (0/1)
- [ ] 密码验证 (0/1)
- [ ] 资源泄漏修复 (0/1)
- [ ] 其他HIGH问题 (0/16)

### 30分钟后 (17:55)
- 预期完成: 4-8个问题
- 报告进度和困难

### 1小时后 (18:25)
- 预期完成: 所有20个问题
- 准备提交

---

## 🎯 成功标准

Task #56完成需要：
- [ ] Token刷新端点实现并测试
- [ ] 登出端点实现并测试
- [ ] 密码验证增强
- [ ] 资源泄漏修复
- [ ] 至少15/20个HIGH问题处理
- [ ] 测试覆盖率保持>80%

---

## 💬 如有疑问

**如果遇到以下情况，立即报告**：
1. 不理解某个HIGH问题的修复方案
2. 遇到技术阻塞无法继续
3. 估计无法在1小时内完成
4. 发现其他紧急问题

**报告方式**：
- 使用teammate-message发送进度
- 30分钟报告周期必须遵守
- 等待team-lead反馈后再继续

---

**现在立即开始Task #56！不要在Task #15上花时间了！** 🚀

**team-lead**
**17:25**
