# 贡献指南

感谢你对课程学习助手项目的关注！本文档将帮助你了解如何为项目做出贡献。

## 🎯 贡献方式

### 1. 报告 Bug

如果你发现了 Bug，请：

1. 在 GitHub Issues 中搜索是否已有类似问题
2. 如果没有，创建新 Issue，包含：
   - Bug 的详细描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（Python 版本、操作系统等）
   - 如果可能，附上错误日志

### 2. 提出功能建议

如果你有好的想法：

1. 在 Issues 中创建 Feature Request
2. 描述：
   - 要解决什么问题
   - 建议的解决方案
   - 可能的替代方案
   - 对现有功能的影响

### 3. 提交代码

#### 开发流程

1. **Fork 仓库**
   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/YOUR_USERNAME/your_AI_study_agent.git
   cd your_AI_study_agent
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **开发**
   - 遵循代码规范（见下文）
   - 添加必要的注释
   - 更新相关文档

4. **测试**
   ```bash
   python tests/test_basic.py
   ```

5. **提交**
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   # 或
   git commit -m "fix: resolve bug in RAG retrieval"
   ```

6. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   # Then create Pull Request on GitHub
   ```

## 📝 代码规范

### Python 代码风格

遵循 PEP 8 规范：

```python
# Good
def calculate_matrix_rank(matrix: List[List[float]]) -> int:
    """
    Calculate the rank of a matrix.
    
    Args:
        matrix: Input matrix as 2D list
        
    Returns:
        Rank of the matrix
    """
    # Implementation
    pass


# Bad
def calc_rank(m):
    # No docstring, unclear variable names
    pass
```

### 命名约定

- **类名**: PascalCase (e.g., `TutorAgent`, `FAISSStore`)
- **函数/方法**: snake_case (e.g., `build_index`, `retrieve_chunks`)
- **常量**: UPPER_SNAKE_CASE (e.g., `DEFAULT_MODEL`, `CHUNK_SIZE`)
- **私有成员**: 前缀下划线 (e.g., `_internal_method`)

### 文档字符串

每个函数/类都应有清晰的文档字符串：

```python
def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
    """
    Retrieve relevant chunks for a query.
    
    Args:
        query: User query string
        top_k: Number of top results to return
        
    Returns:
        List of retrieved chunks with citations
        
    Raises:
        ValueError: If query is empty
    """
    pass
```

### 类型提示

尽可能使用类型提示：

```python
from typing import List, Dict, Optional

def process_documents(
    files: List[str],
    chunk_size: int = 512,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    pass
```

## 🏗️ 添加新功能

### 添加新 Agent

1. 在 `core/agents/` 创建新文件：

```python
# core/agents/my_agent.py
from core.llm.openai_compat import get_llm_client

class MyAgent:
    """My custom agent."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def process(self, input_data: str) -> str:
        """Process input and return result."""
        # Implementation
        pass
```

2. 在 `core/orchestration/prompts.py` 添加 Prompt：

```python
MY_AGENT_PROMPT = """
You are a helpful assistant for...
Input: {input}
Please...
"""
```

3. 在 `core/orchestration/runner.py` 集成：

```python
from core.agents.my_agent import MyAgent

class OrchestrationRunner:
    def __init__(self):
        # ...
        self.my_agent = MyAgent()
    
    def run_my_mode(self, ...):
        # Use self.my_agent
        pass
```

### 添加新文档格式支持

1. 在 `rag/ingest.py` 添加解析函数：

```python
def parse_myformat(filepath: str) -> List[Dict]:
    """Parse .myext files. Returns list of {text, page}."""
    pages = []
    # ... 解析逻辑 ...
    pages.append({"text": content, "page": i + 1})
    return pages
```

2. 在 `parse_document()` 中注册扩展名：

```python
elif ext == ".myext":
    return parse_myformat(filepath)
```

3. 在 `backend/api.py` 的 `ALLOWED_EXTENSIONS` 中添加：

```python
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".pptx", ".ppt", ".myext"}
```

4. 在 `frontend/streamlit_app.py` 的 `st.file_uploader` 中添加类型：

```python
st.file_uploader(..., type=["pdf","txt","md","docx","pptx","ppt","myext"])
```

5. 如需额外依赖，更新 `requirements.txt` 并在 PR 描述中说明原因。

---

### 添加新工具

在 `mcp_tools/client.py` 添加新方法：

```python
class MCPTools:
    @staticmethod
    def my_tool(param: str) -> Dict[str, Any]:
        """My custom tool."""
        try:
            # Implementation
            result = process(param)
            return {
                "tool": "my_tool",
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "tool": "my_tool",
                "error": str(e),
                "success": False
            }
```

### 添加新模式

1. 在 `backend/schemas.py` 添加到类型：

```python
mode: Literal["learn", "practice", "exam", "my_mode"]
```

2. 在 `core/orchestration/policies.py` 配置策略：

```python
MODE_POLICIES = {
    # ...
    "my_mode": ["calculator", "my_tool"]
}
```

3. 在 `core/orchestration/runner.py` 实现逻辑：

```python
def run_my_mode(self, course_name: str, user_message: str, plan: Plan):
    # Implementation
    pass
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
python tests/test_basic.py

# 测试特定模块
python -c "from tests.test_basic import test_rag_components; test_rag_components()"
```

### 添加测试

在 `tests/` 目录添加测试文件：

```python
def test_my_feature():
    """Test my new feature."""
    from my_module import my_function
    
    result = my_function("test_input")
    assert result == "expected_output"
    
    print("✅ My feature test passed")
    return True
```

## 📚 文档

### 更新文档

如果你的更改影响用户使用方式，请更新：

- `README.md`: 主要功能和快速开始
- `USAGE.md`: 详细使用示例
- `ARCHITECTURE.md`: 系统架构和设计

### 文档风格

- 使用清晰的标题层次
- 提供代码示例
- 包含实际的使用场景
- 中英文混排时注意排版

## 🔍 Code Review 清单

提交 PR 前，请自查：

- [ ] 代码遵循项目风格
- [ ] 添加了必要的注释和文档字符串
- [ ] 通过了所有测试
- [ ] 更新了相关文档
- [ ] Commit 信息清晰明确
- [ ] 没有引入新的依赖（或已说明原因）
- [ ] 考虑了向后兼容性

## 🎨 Commit 信息规范

使用语义化的 commit 信息：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 添加测试
- `chore`: 构建/工具相关

**例子:**
```
feat(rag): add support for Word documents

- Add docx parsing in ingest.py
- Update chunk.py to handle docx format
- Add unit tests

Closes #123
```

## 🤝 社区准则

- 尊重他人
- 建设性地讨论
- 欢迎新手
- 分享知识
- 保持友善

## 📞 联系方式

- GitHub Issues: 用于 bug 报告和功能请求
- Pull Requests: 代码贡献
- Discussions: 一般讨论和问题

## ⭐ 感谢

感谢所有贡献者的付出！每一个 PR、每一个 Issue、每一次讨论都让这个项目变得更好。

---

**祝你编码愉快！** 🚀
