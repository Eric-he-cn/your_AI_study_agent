# 课程学习助手 (Course Learning Agent)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)

一个基于 AI 的智能课程学习助手，支持 RAG（检索增强生成）、多 Agent 编排和 MCP 工具调用。帮助大学生更高效地学习课程内容。

## ✨ 核心特性

### 🎯 三种学习模式

1. **📖 学习模式 (Learn)**
   - 概念讲解与知识点总结
   - 教材引用与证据溯源
   - 支持计算器、网页搜索、文件写入
   - 每个结论都有教材依据

2. **✍️ 练习模式 (Practice)**
   - 智能出题（支持难度选择）
   - 自动评分与讲评
   - 错题本自动记录
   - 针对性复习建议

3. **📝 考试模式 (Exam)**
   - 模拟真实考试环境
   - 禁用网页搜索（防作弊）
   - 自动组卷与评分
   - 考后分析报告

### 🔧 技术架构

- **RAG 知识库**: PDF/TXT/MD 文档解析 + FAISS 向量检索
- **多 Agent 编排**: Router → Tutor/QuizMaster/Grader
- **MCP 工具集成**: Calculator、WebSearch、FileWriter
- **工具策略控制**: 不同模式限制不同工具访问

## 📋 目录结构

```
course-agent/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python 依赖
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
├── frontend/
│   └── streamlit_app.py        # Streamlit 前端界面
├── backend/
│   ├── api.py                  # FastAPI 后端服务
│   └── schemas.py              # 数据模型定义
├── core/
│   ├── llm/
│   │   └── openai_compat.py    # LLM 客户端
│   ├── orchestration/
│   │   ├── runner.py           # 主编排器
│   │   ├── prompts.py          # 提示词模板
│   │   └── policies.py         # 工具策略
│   └── agents/
│       ├── router.py           # 路由规划 Agent
│       ├── tutor.py            # 教学 Agent
│       ├── quizmaster.py       # 出题 Agent
│       └── grader.py           # 评分 Agent
├── rag/
│   ├── ingest.py               # 文档解析
│   ├── chunk.py                # 文本分块
│   ├── embed.py                # 向量嵌入
│   ├── store_faiss.py          # FAISS 向量库
│   └── retrieve.py             # 检索与引用
├── mcp_tools/
│   └── client.py               # MCP 工具客户端
└── data/
    └── workspaces/             # 课程工作空间
        └── <course_name>/
            ├── uploads/        # 上传的资料
            ├── index/          # 向量索引
            ├── notes/          # 学习笔记
            ├── mistakes/       # 错题本
            └── exams/          # 考试记录
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/Eric-he-cn/your_AI_study_agent.git
cd your_AI_study_agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# OPENAI_API_KEY=your_api_key_here
# OPENAI_BASE_URL=https://api.openai.com/v1
# 或使用 DeepSeek: https://api.deepseek.com/v1
```

### 3. 启动后端服务

```bash
# 启动 FastAPI 后端
python backend/api.py
```

后端服务将在 `http://localhost:8000` 启动

### 4. 启动前端界面

```bash
# 新开一个终端，启动 Streamlit 前端
streamlit run frontend/streamlit_app.py
```

前端界面将在浏览器中自动打开 `http://localhost:8501`

## 📖 使用指南

### 创建课程

1. 在侧边栏点击「创建新课程」
2. 输入课程名称（如"线性代数"）和学科标签
3. 点击「创建」按钮

### 上传教材

1. 选择已创建的课程
2. 在侧边栏上传 PDF、TXT 或 MD 格式的教材文件
3. 点击「构建索引」按钮，等待索引构建完成

### 开始学习

#### 学习模式

```
用户: 什么是矩阵的秩？
助手: [基于教材内容，给出定义、解释和引用]
```

#### 练习模式

```
用户: 给我出一道关于矩阵秩的中等难度练习题
助手: [生成题目]
用户: [提交答案]
助手: [评分和讲评，记录错题]
```

#### 考试模式

```
用户: 线性代数期中考试
助手: [生成考试题目，禁用搜索]
用户: [提交答案]
助手: [评分和考后报告]
```

## 🏗️ 系统架构

### 数据流

```
用户输入 → FastAPI → OrchestrationRunner
                ↓
         Router Agent (规划)
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
  Tutor    QuizMaster    Grader
    ↓           ↓           ↓
   RAG      MCP Tools    结果输出
```

### Agent 职责

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| Router | 任务规划 | 用户请求 + 模式 | Plan（需要 RAG？允许工具？） |
| Tutor | 概念讲解 | 问题 + 教材上下文 | 结构化教学内容 + 引用 |
| QuizMaster | 生成题目 | 主题 + 难度 + 教材 | Quiz（题目 + 答案 + Rubric） |
| Grader | 评分讲评 | 题目 + 学生答案 + Rubric | GradeReport（分数 + 反馈） |

### 工具策略

| 模式 | Calculator | WebSearch | FileWriter |
|------|-----------|-----------|-----------|
| Learn | ✅ | ✅ | ✅ |
| Practice | ✅ | ❌ | ✅ |
| Exam | ✅ | ❌ | ❌ |

## 🔑 核心优势

### 1. 证据优先 (Evidence-First)
- 每个关键结论都有教材引用
- 显示来源文档和页码
- 可追溯、可验证

### 2. 学习闭环
```
学习 → 练习 → 考试 → 复习
  ↑                    ↓
  └────── 反馈优化 ←────┘
```

### 3. 工具可控
- 不同模式限制不同工具
- 考试模式防作弊
- 所有工具调用可观测

### 4. Agent 编排
- 模块化设计，易扩展
- 职责分离，便于维护
- 符合 Agent 应用开发范式

## 🛠️ 技术栈

### 后端
- **FastAPI**: Web 框架
- **Python 3.9+**: 编程语言
- **Pydantic**: 数据验证

### AI & ML
- **OpenAI API**: LLM 接口（兼容 DeepSeek）
- **Sentence Transformers**: 文本嵌入
- **FAISS**: 向量检索

### 文档处理
- **PyMuPDF**: PDF 解析
- **自定义分块算法**: 文本切分

### 前端
- **Streamlit**: 快速原型开发

## 📊 数据模型

### CourseWorkspace
```python
{
    "course_name": "线性代数",
    "subject": "数学",
    "documents": ["教材.pdf", "讲义.pdf"],
    "index_path": "data/workspaces/线性代数/index/faiss_index"
}
```

### Plan
```python
{
    "need_rag": true,
    "allowed_tools": ["calculator", "filewriter"],
    "task_type": "practice",
    "style": "step_by_step",
    "output_format": "quiz"
}
```

### Quiz
```python
{
    "question": "计算矩阵的秩...",
    "standard_answer": "步骤1...",
    "rubric": "得分点：...",
    "difficulty": "medium",
    "chapter": "第2章"
}
```

### GradeReport
```python
{
    "score": 85.0,
    "feedback": "答对了主要步骤...",
    "mistake_tags": ["计算错误"],
    "references": [...]
}
```

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| OPENAI_API_KEY | OpenAI API 密钥 | - |
| OPENAI_BASE_URL | API 基础 URL | https://api.openai.com/v1 |
| DEFAULT_MODEL | 默认模型 | gpt-3.5-turbo |
| EMBEDDING_MODEL | 嵌入模型 | all-MiniLM-L6-v2 |
| CHUNK_SIZE | 分块大小 | 512 |
| CHUNK_OVERLAP | 分块重叠 | 50 |
| TOP_K_RESULTS | 检索数量 | 3 |

## 📝 API 文档

### 创建课程
```http
POST /workspaces
Content-Type: application/json

{
    "course_name": "线性代数",
    "subject": "数学"
}
```

### 上传文档
```http
POST /workspaces/{course_name}/upload
Content-Type: multipart/form-data

file: <file>
```

### 构建索引
```http
POST /workspaces/{course_name}/build-index
```

### 对话
```http
POST /chat
Content-Type: application/json

{
    "course_name": "线性代数",
    "mode": "learn",
    "message": "什么是矩阵的秩？",
    "history": []
}
```

## 🎯 产品价值

### 对比通用 AI 助手

| 特性 | ChatGPT | 本系统 |
|------|---------|--------|
| 课程针对性 | ❌ | ✅ 基于教材 |
| 引用溯源 | ❌ | ✅ 页码 + 文档 |
| 练习闭环 | ❌ | ✅ 出题 + 评分 |
| 错题管理 | ❌ | ✅ 自动记录 |
| 考试模拟 | ❌ | ✅ 可控环境 |
| 工具策略 | ❌ | ✅ 模式限制 |

### 解决的痛点

1. ✅ **资料分散** → 统一知识库管理
2. ✅ **回答不精准** → 基于教材的 RAG
3. ✅ **缺乏练习** → 智能出题与评分
4. ✅ **不可追溯** → 证据引用系统
5. ✅ **工具支持** → MCP 工具集成

## 🔮 未来规划

- [ ] 支持更多文档格式（Word、Excel、PPT）
- [ ] 多轮对话上下文管理
- [ ] 个性化学习路径推荐
- [ ] 团队协作与分享功能
- [ ] 移动端适配
- [ ] 离线模型支持
- [ ] 更丰富的可视化报表

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

Eric He

---

**注意**: 使用前请确保配置了有效的 OpenAI API Key 或兼容的 LLM API。