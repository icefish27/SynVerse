# SynVerse Backend

AI 写作引擎后端，基于 FastAPI + PostgreSQL + Neo4j + DeepSeek。

## 快速启动

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 配置环境变量（复制并编辑）
cp .env.example .env

# 3. 启动
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

## .env 配置项

```env
# DeepSeek API
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# PostgreSQL + pgvector
DATABASE_URL=postgresql+asyncpg://zen:123456@192.168.31.162:5432/synverse

# Redis
REDIS_URL=redis://:123456@192.168.31.162:6379/0

# Neo4j 图数据库
NEO4J_URI=bolt://192.168.31.162:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=synverse123

# MinIO 对象存储
MINIO_ENDPOINT=192.168.31.162:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 嵌入模型（本地运行）
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# Celery 异步任务（可选）
CELERY_BROKER_URL=redis://:123456@192.168.31.162:6379/1
```

## 项目结构

```
backend-fastapi/
├── .env                          # 环境变量（gitignore）
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python 依赖
├── app/
│   ├── main.py                   # 入口：FastAPI app、CORS、路由挂载
│   ├── core/                     # 基础设施层
│   │   ├── config.py             # Pydantic Settings（所有配置项）
│   │   ├── database.py           # 异步 SQLAlchemy engine + session
│   │   ├── redis.py              # 异步 Redis 客户端
│   │   ├── neo4j.py              # Neo4j 异步 driver
│   │   └── minio.py              # MinIO 客户端 + bucket 管理
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── novel.py              # Novel, Chapter, Outline, Character
│   │   ├── knowledge.py          # KnowledgeDocument, KnowledgeChunk, StyleExample
│   │   ├── writing.py            # WritingSession, WritingMessage
│   │   └── rhythm.py             # RhythmAnalysis
│   ├── schemas/                  # Pydantic 请求/响应模型
│   │   ├── novel.py
│   │   ├── knowledge.py
│   │   ├── writing.py
│   │   └── rhythm.py
│   ├── api/                      # 路由层（REST API）
│   │   ├── novels.py             # 小说 CRUD + 封面上传
│   │   ├── chapters.py           # 章节 CRUD（自动编号、字数统计）
│   │   ├── outlines.py           # 大纲 CRUD + SSE 流式生成
│   │   ├── writing.py            # AI 对话 + SSE 流式生成 + 审读
│   │   ├── knowledge.py          # 知识库上传/切片/嵌入/检索
│   │   ├── style_examples.py     # 风格范例管理
│   │   ├── kg.py                 # Neo4j 知识图谱（提取/搜索/图查询）
│   │   └── rhythm.py             # AI 节奏分析（8 维雷达图）
│   ├── services/                 # 业务逻辑层
│   │   ├── ai_service.py         # DeepSeek API 封装（流式+同步/双模型策略）
│   │   ├── embedding_service.py  # bge-small-zh 嵌入生成 + 余弦相似度
│   │   └── rag_service.py        # RAG 管线（检索+拼装 Prompt+上下文构建）
│   └── agents/                   # 智能体 Prompt 定义
│       ├── writer_agent.py       # 写作智能体（写作铁律/反派弧线/AI味红线）
│       └── reader_agent.py       # 读者智能体（7 项反馈清单）
└── tests/                        # 测试（待添加）
```

## 架构原理

### 1. 分层架构

```
┌─────────────────────────────────────────┐
│  api/     路由层：HTTP 端点，参数校验    │
├─────────────────────────────────────────┤
│  services/ 业务层：AI 调用、RAG 管线    │
├─────────────────────────────────────────┤
│  models/   数据层：ORM 模型，表定义      │
├─────────────────────────────────────────┤
│  core/     基础设施：DB、Redis、Neo4j   │
└─────────────────────────────────────────┘
```

### 2. AI 写作管线

```
用户发送写作请求
    │
    ▼
RAG 检索 ────────────── 一致性 KG 查询
│ (pgvector 向量检索)    │ (Neo4j Cypher)
│ 相似段落 Top 5          │ 角色/地点/物品关系
│       ┌────────────────┘
│       ▼
│ 组装 Prompt
│ · 写作智能体 System Prompt（写作铁律）
│ · 固定范例（按场景类型）
│ · 检索参考段落
│ · 上下文（大纲/上一章/角色列表）
│ · 风格规则（禁用词/句长/情绪节奏）
│       │
│       ▼
│ DeepSeek v4-pro（thinking mode）
│ SSE 流式输出
│ ├── event:reasoning → 思考过程
│ ├── event:content   → 正文内容
│ └── event:done      → 章节保存 + 引用来源
│       │
│       ▼
│ 自动保存章节 → 刷新图谱 → 审读（可选）
```

### 3. 双模型策略

| 任务 | 模型 | 原因 |
|------|------|------|
| 写作生成 | `deepseek-v4-pro` | 最强文本质量，thinking mode 思考链 |
| 大纲生成 | `deepseek-v4-pro` | 需要长输出（8000 tokens） |
| 读者审读 | `deepseek-v4-flash` | 轻量任务，便宜 10 倍 |
| 实体提取 | `deepseek-v4-flash` | 分类/提取任务，低延迟 |
| 场景分类 | `deepseek-v4-flash` | 简单分类，不需要深度思考 |

### 4. 嵌入与向量检索

```
上传 txt 文件
    │
    ▼
切片（200-500 字/段，过滤噪声行）
    │
    ▼
bge-small-zh → 512 维向量 → JSONB 存储
    │
    ▼
检索时：query → 嵌入 → 余弦相似度 → Top K 排序
```

不使用 pgvector 扩展（Alpine PostgreSQL 18 兼容性问题），用 JSONB 列 + Python 计算余弦相似度替代。单用户场景下，全量加载 + Python 计算性能足够。

### 5. SSE 流式协议

所有 AI 生成端点统一使用 SSE（Server-Sent Events）：

```
event: start
data: {"session_id": "xxx"}

event: reasoning
data: {"content": "嗯，用户要写第3章..."}

event: content
data: {"content": "陈默站在药铺门口..."}

event: done
data: {"chapter_id": "xxx", "word_count": 2000, "refs": [...]}
```

前端用 `ReadableStream` + `TextDecoder({stream: true})` 解析，分别渲染到思考面板和对话气泡。

### 6. 知识图谱架构

```
章节内容 → DeepSeek Flash 提取实体+关系 → Neo4j 存储
                                              │
                    ┌─────────────────────────┘
                    ▼
            写作时查询：MATCH (c:Character {novel_id})-[r]-(related)
            → 注入 Prompt，防止设定矛盾
```

Neo4j 不可用时静默降级，不影响核心写作功能。

## 数据库表

| 表 | 用途 | 关键字段 |
|----|------|----------|
| novels | 小说项目 | title, type_tags(JSONB), target_chapters |
| chapters | 章节 | novel_id, chapter_number(自增), content, word_count |
| outlines | 大纲 | novel_id(唯一), core_seed, full_outline, version |
| characters | 角色 | novel_id, name, role_type, personality |
| knowledge_documents | 知识库文档 | filename, chunk_count, status |
| knowledge_chunks | 切片+嵌入 | document_id, content, embedding(JSONB 512维), scene_type |
| style_examples | 精选范例 | scene_type, content, quality_rating, is_pinned |
| writing_sessions | AI 对话 | novel_id, chapter_id, title |
| writing_messages | 对话消息 | session_id, role, content, reasoning_content |
| rhythm_analyses | 节奏分析 | chapter_id(唯一), scores(JSONB), suggestions |

## API 总览

| 分组 | 端点 | 方法 |
|------|------|------|
| 健康 | `/api/health` | GET |
| 小说 | `/api/novels` | GET(列表+搜索)/POST |
| | `/api/novels/{id}` | GET/PUT/DELETE |
| | `/api/novels/{id}/cover` | POST(封面上传) |
| 章节 | `/api/novels/{id}/chapters` | GET/POST |
| | `/api/chapters/{id}` | GET/PUT/DELETE |
| 大纲 | `/api/novels/{id}/outline` | GET/PUT |
| | `/api/novels/{id}/outline/generate` | POST(SSE 流式) |
| 写作 | `/api/novels/{id}/sessions` | GET/POST |
| | `/api/sessions/{id}/messages` | GET |
| | `/api/sessions/{id}/generate` | POST(SSE 流式) |
| | `/api/chapters/{id}/review` | POST(SSE 审读) |
| 知识库 | `/api/knowledge/documents` | GET |
| | `/api/knowledge/upload` | POST(上传+切片+嵌入) |
| | `/api/knowledge/documents/{id}` | DELETE |
| | `/api/knowledge/search` | GET(向量检索) |
| 范例 | `/api/style-examples` | GET/POST |
| | `/api/style-examples/{id}` | DELETE |
| 图谱 | `/api/novels/{id}/kg/extract` | POST(AI 提取) |
| | `/api/novels/{id}/kg/search` | GET(搜索实体) |
| | `/api/novels/{id}/kg/graph` | GET(完整图数据) |
| 节奏 | `/api/chapters/{id}/rhythm` | GET/POST(AI 分析) |
| 文件 | `/api/files/{path}` | GET(MinIO 文件服务) |
