# Teammates通信问题记录

> 记录teammates使用中发现的通信问题及解决方案

**创建日期**: 2026-02-09
**状态**: 已识别并解决

---

## 🚨 已知通信问题

### 问题1： teammates将报告写成文件，而不是发送消息

**发现时间**: 2026-02-09
**影响**: 严重 - 导致team-lead无法接收进度报告

#### 问题症状

- ✅ teammates创建了详细的.md文档文件
- ❌ 但没有通过teammate-message发送给team-lead
- ❌ team-lead看不到进度，以为teammates未响应

#### 实际案例

**frontend-dev（5分钟规则测试）**：
- 声称发送了多次报告
- 我完全没有收到
- 实际上他可能只是写了文件

**backend-dev（Task #15）**：
- 声称发送了6份报告
- 我只收到最后1份确认报告
- 前5份他写成了文件（.md）

#### 根本原因

**理解偏差**：
- teammates认为"报告" = 创建文档文件
- team-lead期望"报告" = 发送teammate-message

**为什么test-specialist正常**：
- test-specialist知道要发送消息给我
- 他的报告我都能收到

#### 解决方案

1. **在启动指令中明确说明**：
   ```python
   prompt = f"""你现在是{role}，负责{project}

   ⚠️ 重要：如何正确报告进度

   ✅ 必须通过消息发送报告，不能只写文件！
   ✅ 30分钟时必须主动发送teammate-message给我
   ✅ 报告格式：使用summary字段
   ✅ 包含：已完成、进行中、遇到的问题

   ❌ 不要只创建.md文档文件
   ❌ 不要期望我会自动读取文件

   工作方式：完成工作 → 发送消息给我 → 继续工作
   """
   ```

2. **定期主动询问**：
   - team-lead每30分钟主动询问状态
   - 使用`SendMessage`工具主动联系

3. **强制要求**：
   - 在30分钟时发送强制报告提醒
   - 明确要求"发送消息"，不是"创建文件"

#### 验证方法

**检查teammates是否正确报告**：
- 收到teammate-message ✅
- 看到summary字段 ✅
- 看到详细内容 ✅

**如果teammates没有响应**：
- 立即发送SendMessage询问
- 不要假设他们创建了文件

---

## ✅ 最佳实践

### 正确的teammates沟通方式

1. **team-lead → teammates**
   - 使用`SendMessage`工具
   - 明确的指令和期望
   - 设置明确的时间节点

2. **teammates → team-lead**
   - 必须通过teammate-message发送
   - 不能只写文件
   - 包含summary和详细内容

3. **30分钟报告流程**
   ```
   0分钟：分配任务
   30分钟：强制要求报告（SendMessage提醒）
   收到报告：评估并指导
   未收到：再次强制要求
   ```

---

## 📚 相关文档

- [TEAMMATES_GUIDELINES.md](./TEAMMATES_GUIDELINES.md) - teammates工作规范
- [GIT_WORKFLOW.md](./GIT_WORKFLOW.md) - Git工作流规范
- [时间控制规则测试报告.md](./时间控制规则测试报告.md) - 测试报告

---

**维护者**: team-lead
**最后更新**: 2026-02-09
