# StudyNotesManager 数据库Schema总结

## 概览

StudyNotesManager使用PostgreSQL 15+配合pgvector扩展，支持关系型数据和向量相似度搜索。

## 核心表结构

### 1. 用户与认证

#### users (用户表)
- **主键**: UUID
- **核心字段**: email, password_hash, full_name
- **订阅**: subscription_tier, subscription_expires_at
- **OAuth**: oauth_provider, oauth_id
- **状态**: is_active, is_verified, verification_token
- **索引**: email (unique), subscription_tier

### 2. 笔记管理

#### notes (笔记表)
- **主键**: UUID
- **外键**: user_id (CASCADE), category_id
- **内容**: title, content, file_type, file_url, thumbnail_url
- **OCR**: ocr_text, ocr_confidence
- **向量**: embedding VECTOR(1536) - 支持语义搜索
- **索引**:
  - (user_id, created_at DESC)
  - category_id
  - embedding (ivfflat with lists=100)

### 3. 脑图系统

#### mindmaps (脑图表)
- **主键**: UUID
- **外键**: user_id (CASCADE), note_id (CASCADE)
- **结构**: structure (JSONB)
- **类型**: map_type (user_generated, ai_generated, textbook_comparison)
- **AI元数据**: ai_model, ai_generated_at
- **对比**: compared_with_mindmap_id, comparison_result (JSONB)
- **索引**: user_id, note_id, map_type, is_template (partial)

#### mindmap_knowledge_points (知识点表)
- **主键**: UUID
- **外键**: mindmap_id (CASCADE), related_note_id
- **内容**: node_id, knowledge_text, embedding VECTOR(1536)
- **学习数据**: mastery_level (0-1), question_count, mistake_count
- **约束**: (mindmap_id, node_id) UNIQUE
- **索引**:
  - mindmap_id
  - related_note_id
  - embedding (ivfflat with lists=100)

### 4. 测验系统

#### quiz_questions (测验题表)
- **主键**: UUID
- **外键**: knowledge_point_id (CASCADE), note_id
- **内容**: question_text, question_type, options (JSONB)
- **答案**: correct_answer, answer_explanation
- **元数据**: difficulty, ai_generated, ai_model
- **统计**: attempt_count, correct_count
- **索引**: knowledge_point_id, note_id, difficulty

#### user_quiz_records (答题记录)
- **主键**: UUID
- **外键**: user_id (CASCADE), question_id (CASCADE)
- **答案**: user_answer, is_correct
- **时间**: answered_at, time_spent
- **错题定位**: related_note_snippet, related_note_section
- **约束**: (user_id, question_id, answered_at) UNIQUE
- **索引**: (user_id, answered_at DESC), question_id, is_correct (partial for false)

### 5. 错题本系统

#### mistakes (错题表)
- **主键**: UUID
- **外键**: user_id (CASCADE), question_id, category_id, knowledge_point_id, related_note_id
- **快照**: question_text, question_type, options, correct_answer
- **标签**: tags ARRAY
- **统计**: mistake_count, last_mistake_at
- **索引**:
  - (user_id, created_at DESC)
  - tags (GIN)
  - category_id, knowledge_point_id

#### mistake_reviews (复习记录)
- **主键**: UUID
- **外键**: mistake_id (CASCADE), user_id (CASCADE)
- **复习**: is_correct, review_time
- **遗忘曲线**: review_stage (0-6), next_review_at
- **索引**:
  - (mistake_id, reviewed_at DESC)
  - (user_id, next_review_at) partial (next_review_at IS NOT NULL)

### 6. 分类系统

#### categories (分类表)
- **主键**: UUID
- **外键**: user_id (CASCADE), parent_id (self reference)
- **层级**: name, parent_id, level
- **元数据**: color, icon, description
- **统计**: notes_count, children_count
- **约束**: (user_id, name, parent_id) UNIQUE
- **索引**: (user_id, parent_id)

#### category_relations (分类关系表)
- **主键**: UUID
- **外键**: user_id, category_a_id (CASCADE), category_b_id (CASCADE)
- **关系**: relation_type (related, independent), weight
- **约束**: (category_a_id, category_b_id) UNIQUE, category_a_id < category_b_id
- **索引**: user_id, relation_type

### 7. 分享与协作

#### note_shares (笔记分享表)
- **主键**: UUID
- **外键**: note_id (CASCADE), user_id (CASCADE)
- **配置**: share_id (unique), access_type, password_hash
- **权限**: allow_download, allow_merge
- **统计**: view_count, download_count, merge_count
- **过期**: expires_at
- **索引**: note_id, user_id, share_id, expires_at (partial)

### 8. 学习分析

#### study_sessions (学习会话表)
- **主键**: UUID
- **外键**: user_id (CASCADE), related_note_id, related_quiz_id
- **会话**: session_type, duration_seconds
- **统计**: questions_answered, questions_correct, notes_created
- **时间**: started_at, ended_at
- **索引**: (user_id, started_at DESC), session_type

## 向量搜索配置

### pgvector扩展
- 安装: `CREATE EXTENSION vector;`
- 维度: 1536 (OpenAI embeddings)
- 距离函数: cosine (vector_cosine_ops)

### 向量索引
使用IVFFlat索引优化相似度搜索:
```sql
CREATE INDEX idx_notes_embedding
ON notes USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_mindmap_kp_embedding
ON mindmap_knowledge_points USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## 级联删除规则

- **CASCADE**: 删除用户时，删除所有相关数据
  - user_id 在所有表中都是 CASCADE
- **SET NULL**: 删除知识点时，相关题目 knowledge_point_id 设为 NULL
- **保护**: 重要数据（错题快照）不自动删除

## 性能优化

### 索引策略
1. **B-tree索引**: 外键、时间戳、唯一约束
2. **GIN索引**: 数组类型（tags）、JSONB
3. **IVFFlat索引**: 向量相似度搜索
4. **部分索引**: WHERE条件过滤（is_template, next_review_at）

### 查询优化
- 使用复合索引优化常见查询模式
- 时间戳索引支持DESC排序
- 向量索引lists参数根据数据量调整

## 数据完整性

### 约束
- **UNIQUE**: email, (user_id, name, parent_id), (mindmap_id, node_id)
- **CHECK**: category_a_id < category_b_id
- **NOT NULL**: 所有必填字段
- **外键**: 所有关系字段

### 默认值
- UUID: gen_random_uuid()
- 时间戳: NOW()
- JSONB: '{}'
- Boolean: false/true
- Integer: 0

## 扩展性

### JSONB字段
- users.metadata: 用户元数据
- notes.metadata: 笔记元数据
- mindmaps.structure: 脑图结构
- mindmaps.comparison_result: 对比结果
- quiz_questions.options: 题目选项

### 未来可扩展
- 添加更多向量维度支持
- 支持多种embedding模型
- 添加全文搜索（GIN索引）
- 物化视图用于复杂聚合

## 迁移命令

```bash
# 初始化数据库
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "描述"

# 回滚
alembic downgrade -1

# 查看历史
alembic history
```

## 维护建议

1. **定期备份**: 每日自动备份
2. **索引重建**: 根据数据量调整lists参数
3. **VACUUM**: 定期清理死元组
4. **监控**: 慢查询日志、连接数、磁盘使用
5. **更新**: 保持PostgreSQL版本更新

## 文档位置

- 模型定义: `backend/app/models/`
- 迁移脚本: `backend/alembic/versions/`
- 设置指南: `backend/README_DATABASE.md`
- 迁移指南: `backend/README_MIGRATION.md`
- 管理工具: `backend/scripts/db_manage.py`
