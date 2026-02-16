# Course Learning Agent - 项目说明

## 🎯 项目概述

这是一个完整的 **AI 课程学习助手** 项目，专门为大学生课程学习设计。与通用 AI 助手不同，本系统提供：

1. **基于教材的 RAG 系统** - 所有回答都有教材引用
2. **三种学习模式** - 学习、练习、考试
3. **多 Agent 协作** - Router、Tutor、QuizMaster、Grader
4. **工具可控集成** - 不同模式限制不同工具
5. **完整学习闭环** - 从理解到练习到考试

## 📐 系统架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit Frontend                 │
│          (课程选择 | 模式切换 | 对话界面)              │
└────────────────────┬────────────────────────────────┘
                     │ HTTP API
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│          (Workspace管理 | 文件上传 | 对话)            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            Orchestration Runner (编排器)             │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │          Router Agent (规划器)                │  │
│  │   输入: 用户消息 + 模式 + 课程                 │  │
│  │   输出: Plan (need_rag, allowed_tools, ...)   │  │
│  └──────────────────────────────────────────────┘  │
│                     │                                │
│         ┌───────────┼───────────┐                   │
│         ▼           ▼           ▼                   │
│    ┌────────┐ ┌─────────┐ ┌────────┐              │
│    │ Tutor  │ │QuizMstr │ │ Grader │              │
│    │ Agent  │ │ Agent   │ │ Agent  │              │
│    └───┬────┘ └────┬────┘ └───┬────┘              │
│        │           │           │                     │
└────────┼───────────┼───────────┼─────────────────────┘
         │           │           │
    ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐
    │  RAG   │  │  MCP   │  │ Output │
    │ System │  │ Tools  │  │ Format │
    └────────┘  └────────┘  └────────┘
```

### 2. 核心模块说明

#### A. RAG 系统 (rag/)

**功能**: 文档检索增强生成

**流程**:
```
PDF/TXT/MD → 解析 → 分块 → Embedding → FAISS 索引
                                          ↓
用户查询 → Embedding → 相似度检索 → Top-K 结果 → 带引用的上下文
```

**关键文件**:
- `ingest.py`: 文档解析 (支持 PDF, TXT, MD)
- `chunk.py`: 文本分块 (滑窗 + overlap)
- `embed.py`: 向量嵌入 (Sentence Transformers)
- `store_faiss.py`: FAISS 向量存储
- `retrieve.py`: 检索 + 引用生成

#### B. Agent 系统 (core/agents/)

**Router Agent** (router.py)
- 职责: 分析用户请求，制定执行计划
- 输入: 用户消息、模式、课程信息
- 输出: Plan 对象
- 决策: 是否需要 RAG？允许哪些工具？采用什么风格？

**Tutor Agent** (tutor.py)
- 职责: 教学讲解，概念说明
- 输入: 问题 + 教材上下文
- 输出: 结构化教学内容（定义、解释、要点、引用、总结）
- 特点: 证据优先，必须引用教材

**QuizMaster Agent** (quizmaster.py)
- 职责: 生成练习题
- 输入: 课程、主题、难度、教材上下文
- 输出: Quiz 对象（题目、标准答案、评分标准）
- 特点: 基于教材出题，难度可控

**Grader Agent** (grader.py)
- 职责: 评分和讲评
- 输入: 题目、标准答案、评分标准、学生答案
- 输出: GradeReport（分数、反馈、错误分类）
- 特点: 给出建设性反馈，标注错误类型

#### C. MCP 工具 (mcp_tools/)

**工具集**:
1. **Calculator**: 数学表达式计算
2. **WebSearch**: 网页搜索（模拟）
3. **FileWriter**: 文件读写（笔记、错题本）

**工具策略** (policies.py):
```python
MODE_POLICIES = {
    "learn": ["calculator", "websearch", "filewriter"],    # 学习全开
    "practice": ["calculator", "filewriter"],              # 练习禁搜索
    "exam": ["calculator"]                                 # 考试只能算
}
```

### 3. 数据流详解

#### 学习模式流程

```
用户: "什么是矩阵的秩?"
  ↓
FastAPI (/chat endpoint)
  ↓
OrchestrationRunner.run(mode="learn")
  ↓
Router.plan() → Plan(need_rag=True, allowed_tools=[...])
  ↓
Retriever.retrieve("矩阵的秩") → [教材片段1, 片段2, 片段3]
  ↓
Tutor.teach(question, context) → 结构化回答
  ↓
Response → {
    message: "...",
    citations: [...],
    tool_calls: [...]
}
  ↓
Streamlit 显示 (回答 + 引用 + 工具调用)
```

#### 练习模式流程

```
【第一轮：出题】
用户: "给我出一道矩阵秩的题"
  ↓
QuizMaster.generate_quiz() → Quiz 对象
  ↓
显示题目

【第二轮：评分】
用户: "答案是..."
  ↓
Grader.grade() → GradeReport
  ↓
显示评分 + 反馈
  ↓
如果 score < 60 → 保存到错题本 (mistakes.jsonl)
```

## 🎨 前端界面设计

### 布局结构

```
┌────────────────────────────────────────────────────┐
│  课程学习助手 📚                                      │
├─────────────┬──────────────────────────────────────┤
│  侧边栏      │         主内容区                       │
│             │                                        │
│ [课程选择]   │  当前课程: 线性代数                     │
│  线性代数    │  当前模式: 📖 学习模式                  │
│  通信原理    │  ────────────────────────────        │
│  + 新建      │                                        │
│             │  💬 对话区                              │
│ [模式选择]   │  ┌──────────────────────────────┐    │
│  ○ 学习     │  │ User: 什么是矩阵的秩？       │    │
│  ○ 练习     │  └──────────────────────────────┘    │
│  ○ 考试     │  ┌──────────────────────────────┐    │
│             │  │ Assistant: [回答内容]        │    │
│ [知识库]     │  │ 📑 查看引用 ▼                │    │
│  📄 上传     │  │   - 来源1: 教材.pdf, p15     │    │
│  🔨 建索引   │  │   - 来源2: 讲义.txt          │    │
│             │  │ 🔧 工具调用 ▼                │    │
│ [工具调用]   │  │   - Calculator: 2+2=4       │    │
│  ✓ 计算器    │  └──────────────────────────────┘    │
│  ✓ 搜索     │                                        │
│  ✓ 文件     │  [输入框: 输入你的问题...]              │
│             │                                        │
└─────────────┴──────────────────────────────────────┘
```

### 交互特性

1. **实时模式切换**: 切换模式后立即生效
2. **引用折叠**: 点击展开查看详细引用
3. **工具可观测**: 所有工具调用都可查看
4. **历史记录**: 对话历史持久化在 session

## 📊 数据存储结构

```
data/workspaces/
└── 线性代数/
    ├── uploads/                    # 原始文档
    │   ├── 教材第一章.pdf
    │   ├── 教材第二章.pdf
    │   └── 课堂讲义.txt
    ├── index/                      # 向量索引
    │   ├── faiss_index.faiss       # FAISS 索引文件
    │   └── faiss_index.pkl         # 文档块元数据
    ├── notes/                      # 学习笔记
    │   └── 2024-02-16-summary.md
    ├── mistakes/                   # 错题本
    │   └── mistakes.jsonl          # 每行一个错题记录
    └── exams/                      # 考试记录
        └── exam-2024-02-16.json
```

### mistakes.jsonl 格式

```json
{"timestamp": "2024-02-16T10:30:00", "question": "...", "student_answer": "...", "score": 75, "feedback": "...", "mistake_tags": ["计算错误"]}
{"timestamp": "2024-02-16T11:00:00", "question": "...", "student_answer": "...", "score": 60, "feedback": "...", "mistake_tags": ["概念性错误"]}
```

## 🔧 技术实现要点

### 1. RAG 实现

**分块策略**:
```python
chunk_size = 512      # 字符数
overlap = 50          # 重叠字符数
```

**检索策略**:
```python
top_k = 3            # 返回前3个最相关片段
similarity = L2      # 使用 L2 距离
```

### 2. Prompt Engineering

**结构化输出**: 所有 Agent 的 Prompt 都设计为生成结构化输出（JSON 或固定格式）

**证据优先**: Tutor Agent 的 Prompt 强制要求引用教材

**评分客观**: Grader Agent 的 Prompt 包含详细的评分标准

### 3. 错误处理

- LLM 调用失败 → 返回错误消息
- JSON 解析失败 → 使用默认值
- 文件上传失败 → 前端提示
- 索引不存在 → 提示用户先建索引

### 4. 可扩展性设计

**新增 Agent**:
```python
# 1. 在 core/agents/ 创建新 agent 文件
# 2. 在 prompts.py 添加 prompt 模板
# 3. 在 runner.py 添加调用逻辑
```

**新增工具**:
```python
# 在 mcp_tools/client.py 添加新方法
@staticmethod
def new_tool(param):
    # 实现工具逻辑
    return result
```

**新增模式**:
```python
# 1. 在 schemas.py 添加到 Literal 类型
# 2. 在 policies.py 配置工具策略
# 3. 在 runner.py 添加模式处理逻辑
```

## 🎯 核心创新点

### 1. 证据优先架构
- 强制要求引用教材来源
- 显示页码和文档名
- 可追溯、可验证

### 2. 学习闭环设计
```
理解 (Learn) → 练习 (Practice) → 检测 (Exam) → 复习 (错题本)
```

### 3. 工具策略控制
- 不同模式不同策略
- 考试模式防作弊
- 所有调用可观测

### 4. Agent 职责分离
- Router: 规划
- Tutor: 教学
- QuizMaster: 出题
- Grader: 评分

各司其职，便于维护和扩展。

## 🚀 部署建议

### 开发环境
```bash
# 本地开发
python backend/api.py          # 后端: localhost:8000
streamlit run frontend/streamlit_app.py  # 前端: localhost:8501
```

### 生产环境
```bash
# 使用 gunicorn + nginx
gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker
nginx → proxy_pass to 8000
```

### Docker 部署
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "backend/api.py"]
```

## 📈 性能优化

1. **向量检索**: FAISS 使用 GPU 加速
2. **嵌入缓存**: 缓存常见查询的 embedding
3. **模型优化**: 使用量化模型减少显存
4. **异步处理**: FastAPI 异步端点

## 🔒 安全考虑

1. **API Key 保护**: 使用环境变量，不提交到代码库
2. **文件上传限制**: 限制文件大小和类型
3. **表达式执行**: Calculator 使用安全的 eval
4. **数据隔离**: 每个课程独立工作空间

## 📚 学习建议

### 理解顺序

1. **先看数据流**: 从 README.md 的架构图开始
2. **再看 Agent**: 理解每个 Agent 的职责
3. **然后看 RAG**: 理解文档如何变成知识
4. **最后看编排**: 理解如何协调所有组件

### 调试技巧

1. 查看后端日志了解 API 调用
2. 查看 LLM 返回的原始文本
3. 检查 FAISS 索引是否构建成功
4. 验证 .env 配置是否正确

---

## 💡 核心价值总结

本项目不是简单的 "PDF 问答"，而是：

✅ **产品化的学习系统** - 完整的学习闭环  
✅ **可控的 Agent 应用** - 工具策略 + 模式设计  
✅ **可追溯的知识系统** - 证据优先 + 引用标注  
✅ **可扩展的架构** - 模块化 + Agent 编排  

这是一个展示 **Agent 应用开发能力** 的完整项目！
