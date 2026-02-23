"""MCP Tools - Calculator, WebSearch (SerpAPI), FileWriter with OpenAI tool schemas."""
import json
import os
import math
import statistics
import requests
from typing import Dict, Any, List


# ── OpenAI Function Calling Schema 定义 ─────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "计算各类数学表达式，以下场景必须调用本工具，不得心算：\n"
                "① 算术/代数：2**10、(3+5)*7、sqrt(2)、abs(-3)\n"
                "② 三角函数：sin(pi/6)、cos(deg2rad(45))、atan2(1,1)、tanh(0.5)\n"
                "③ 对数/指数：log(1000,10)、log2(64)、exp(3)\n"
                "④ 取整/舍入：floor(3.7)、ceil(3.2)、round(3.145,2)、trunc(9.9)\n"
                "⑤ 组合数学：comb(10,3)→C(10,3)=120，perm(5,2)→P(5,2)=20，factorial(10)\n"
                "⑥ 数论：gcd(48,18)、lcm(12,15)\n"
                "⑦ 几何辅助：hypot(3,4)→两点距离，atan2(y,x)→反正切\n"
                "⑧ 统计（传列表）：mean([1,2,3])、median([…])、stdev([…])、variance([…])\n"
                "⑨ 常数：pi、e、tau(=2π)、inf\n"
                "⑩ 角度换算：deg2rad(90)→弧度，rad2deg(pi)→角度\n"
                "只要涉及数值计算，优先调用本工具，不要自己估算。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "合法的 Python 数学表达式字符串。"
                            "示例：'comb(10,3)'、'mean([85,90,78,92])'、"
                            "'sqrt(3**2+4**2)'、'round(log(1024,2),4)'"
                        )
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "websearch",
            "description": "搜索互联网获取最新信息，适合查询时事、补充教材未覆盖的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或问题"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "在用户的历史问答和错题记录中检索相关内容，避免重复讲解，可了解用户薄弱点。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词或问题描述"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "当前课程名称"
                    },
                    "event_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "只检索指定类型：qa/mistake/practice，不传则检索全部"
                    }
                },
                "required": ["query", "course_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mindmap_generator",
            "description": "根据知识点或章节主题，检索教材内容并生成Mermaid思维导图，用于知识点汇总与结构化展示。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "思维导图的主题，例如'第四章 特征值与特征向量'或'矩阵范数与Schur不等式'"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "当前课程名称，用于检索教材内容"
                    },
                    "extra_context": {
                        "type": "string",
                        "description": "可选的补充说明或额外知识点提示"
                    }
                },
                "required": ["topic", "course_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filewriter",
            "description": "将内容写入学习笔记文件，用于保存学习总结、错题记录等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名（不含路径），例如 'note.md'"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "写入模式：write 覆盖，append 追加"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    }
]


def get_tool_schemas(allowed_tools: List[str]) -> List[Dict]:
    """根据允许的工具名列表筛选 schema。"""
    return [s for s in TOOL_SCHEMAS if s["function"]["name"] in allowed_tools]


def _extract_mermaid_code(text: str) -> str:
    """从 LLM 输出中提取第一个 Mermaid 代码块。"""
    import re
    m = re.search(r"```mermaid\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # LLM 有时直接输出 mindmap 语法而不加围栏
    stripped = text.strip()
    if stripped.startswith("mindmap") or stripped.startswith("graph") or stripped.startswith("flowchart"):
        return stripped
    return ""


# ── 工具实现 ─────────────────────────────────────────────────────────────────

class MCPTools:
    """MCP tools implementation with real backends."""

    # 由 runner 在每次调用前注入上下文（如 notes_dir）
    _context: Dict[str, Any] = {}

    @staticmethod
    def calculator(expression: str) -> Dict[str, Any]:
        """安全地计算数学表达式，支持统计、组合数学、三角等扩展函数。"""
        try:
            # 统计函数（接受列表）
            def _mean(data): return statistics.mean(data)
            def _median(data): return statistics.median(data)
            def _stdev(data): return statistics.stdev(data)
            def _variance(data): return statistics.variance(data)
            def _pstdev(data): return statistics.pstdev(data)
            def _pvariance(data): return statistics.pvariance(data)
            def _mode(data): return statistics.mode(data)

            safe_globals = {
                "__builtins__": {},
                # 基础三角
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "asin": math.asin, "acos": math.acos, "atan": math.atan,
                "atan2": math.atan2,
                # 双曲三角
                "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
                "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
                # 角度/弧度互转
                "deg2rad": math.radians, "rad2deg": math.degrees,
                "radians": math.radians, "degrees": math.degrees,
                # 幂/对数/指数
                "sqrt": math.sqrt, "exp": math.exp, "pow": math.pow,
                "log": math.log, "log10": math.log10, "log2": math.log2,
                # 取整/舍入
                "abs": abs, "floor": math.floor, "ceil": math.ceil,
                "round": round, "trunc": math.trunc,
                # 组合数学
                "factorial": math.factorial,
                "comb": math.comb,   # C(n,k) = nCr
                "perm": math.perm,   # P(n,k) = nPr
                "gcd": math.gcd, "lcm": math.lcm,
                # 几何/向量
                "hypot": math.hypot,
                "fmod": math.fmod, "remainder": math.remainder,
                # 统计
                "mean": _mean, "median": _median,
                "stdev": _stdev, "variance": _variance,
                "pstdev": _pstdev, "pvariance": _pvariance,
                "mode": _mode,
                # 常数
                "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
                # 内置集合/聚合
                "sum": sum, "min": min, "max": max, "len": len, "list": list,
            }
            result = eval(expression, safe_globals, {})
            # 浮点数保留合理精度
            if isinstance(result, float):
                display = round(result, 10)
            else:
                display = result
            return {
                "tool": "calculator",
                "expression": expression,
                "result": display,
                "success": True
            }
        except Exception as ex:
            return {
                "tool": "calculator",
                "expression": expression,
                "error": str(ex),
                "success": False
            }

    @staticmethod
    def websearch(query: str) -> Dict[str, Any]:
        """使用 SerpAPI 搜索互联网。"""
        api_key = os.getenv("SERPAPI_API_KEY", "")
        if not api_key:
            return {
                "tool": "websearch",
                "query": query,
                "error": "SERPAPI_API_KEY 未配置",
                "success": False
            }
        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": 5, "hl": "zh-cn"},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("organic_results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })

            return {
                "tool": "websearch",
                "query": query,
                "results": results,
                "success": True
            }
        except Exception as ex:
            return {
                "tool": "websearch",
                "query": query,
                "error": str(ex),
                "success": False
            }

    @staticmethod
    def filewriter(filename: str, content: str, mode: str = "write",
                   notes_dir: str = "./data/notes") -> Dict[str, Any]:
        """将内容写入笔记文件。"""
        try:
            os.makedirs(notes_dir, exist_ok=True)
            # 只取文件名，防止路径穿越
            safe_name = os.path.basename(filename)
            path = os.path.join(notes_dir, safe_name)
            write_mode = "a" if mode == "append" else "w"
            with open(path, write_mode, encoding="utf-8") as f:
                f.write(content)
            return {
                "tool": "filewriter",
                "path": path,
                "mode": mode,
                "success": True
            }
        except Exception as ex:
            return {
                "tool": "filewriter",
                "filename": filename,
                "error": str(ex),
                "success": False
            }

    @staticmethod
    def mindmap_generator(topic: str, course_name: str,
                          extra_context: str = "") -> Dict[str, Any]:
        """检索教材内容，调 LLM 生成 Mermaid 思维导图代码。"""
        try:
            # 1. RAG 检索该主题相关内容
            context = extra_context or ""
            try:
                data_dir = os.getenv("DATA_DIR", "./data/workspaces")
                safe_name = os.path.basename(course_name.strip())
                index_path = os.path.abspath(
                    os.path.join(data_dir, safe_name, "index", "faiss_index")
                )
                if os.path.exists(f"{index_path}.faiss"):
                    from rag.store_faiss import FAISSStore
                    from rag.retrieve import Retriever
                    store = FAISSStore()
                    store.load(index_path)
                    retriever = Retriever(store)
                    chunks = retriever.retrieve(topic, top_k=8)
                    rag_ctx = retriever.format_context(chunks)
                    context = rag_ctx + ("\n" + context if context else "")
            except Exception as rag_err:
                print(f"[Mindmap] RAG 检索失败（继续用空上下文）: {rag_err}")

            # 2. 调 LLM 生成 Mermaid mindmap 代码
            from core.llm.openai_compat import get_llm_client
            llm = get_llm_client()
            ctx_snippet = context[:3000] if context else "（无教材内容，请基于通用知识生成）"
            prompt = (
                f"请根据以下教材内容，为主题「{topic}」生成一个 Mermaid 思维导图。\n\n"
                f"教材参考内容:\n{ctx_snippet}\n\n"
                f"要求：\n"
                f"1. 使用 Mermaid mindmap 语法\n"
                f"2. 根节点格式：root((主题名))\n"
                f"3. 层次清晰，2~4层，每个节点不超过15个字\n"
                f"4. 覆盖该主题核心知识点结构\n"
                f"5. 只输出 Mermaid 代码块，不要任何其他说明\n\n"
                f"输出格式（仅此内容）：\n"
                f"```mermaid\nmindmap\n  root(({topic}))\n    ...\n```"
            )
            messages = [
                {"role": "system", "content": "你是专业的知识图谱生成专家，擅长将知识结构化为思维导图。只输出 Mermaid 代码块。"},
                {"role": "user", "content": prompt},
            ]
            response = llm.chat(messages, temperature=0.3, max_tokens=1200)
            mermaid_code = _extract_mermaid_code(response)
            if not mermaid_code:
                return {"tool": "mindmap_generator", "error": "LLM 未生成有效的 Mermaid 代码", "success": False}

            return {
                "tool": "mindmap_generator",
                "topic": topic,
                "mermaid_code": mermaid_code,
                "success": True,
                "message": (
                    f"已生成「{topic}」的思维导图。"
                    f"请在回复中用 ```mermaid\n{mermaid_code}\n``` 代码块原样展示给用户，"
                    f"不要修改代码内容，然后可以简要说明主要知识点结构。"
                ),
            }
        except Exception as ex:
            return {"tool": "mindmap_generator", "error": str(ex), "success": False}

    @staticmethod
    def memory_search(query: str, course_name: str,
                      event_types: List[str] = None) -> Dict[str, Any]:
        """检索用户历史记忆（情景记忆）。"""
        try:
            from memory.manager import get_memory_manager
            mgr = get_memory_manager()
            episodes = mgr.search_episodes(
                query=query,
                course_name=course_name,
                event_types=event_types,
                top_k=5,
            )
            if not episodes:
                return {
                    "tool": "memory_search",
                    "query": query,
                    "results": [],
                    "message": "未找到相关历史记录",
                    "success": True,
                }
            formatted = []
            for ep in episodes:
                etype = {"qa": "问答", "mistake": "错题", "practice": "练习",
                         "exam": "考试"}.get(ep.get("event_type", ""), ep.get("event_type", ""))
                date_str = ep.get("created_at", "")[:10]
                flag = "⚠️ " if ep.get("importance", 0) >= 0.8 else ""
                formatted.append(f"[{date_str} {etype}] {flag}{ep['content'][:200]}")
            return {
                "tool": "memory_search",
                "query": query,
                "results": formatted,
                "count": len(formatted),
                "success": True,
            }
        except Exception as ex:
            return {"tool": "memory_search", "error": str(ex), "success": False}

    @staticmethod
    def call_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
        """按名称调用工具。"""
        if tool_name == "calculator":
            return MCPTools.calculator(kwargs.get("expression", ""))
        elif tool_name == "websearch":
            return MCPTools.websearch(kwargs.get("query", ""))
        elif tool_name == "memory_search":
            return MCPTools.memory_search(
                query=kwargs.get("query", ""),
                course_name=kwargs.get("course_name", ""),
                event_types=kwargs.get("event_types"),
            )
        elif tool_name == "mindmap_generator":
            return MCPTools.mindmap_generator(
                topic=kwargs.get("topic", ""),
                course_name=kwargs.get("course_name", ""),
                extra_context=kwargs.get("extra_context", ""),
            )
        elif tool_name == "filewriter":
            notes_dir = MCPTools._context.get("notes_dir", "./data/notes")
            return MCPTools.filewriter(
                filename=kwargs.get("filename", "note.md"),
                content=kwargs.get("content", ""),
                mode=kwargs.get("mode", "write"),
                notes_dir=notes_dir
            )
        else:
            return {"tool": tool_name, "error": f"未知工具: {tool_name}", "success": False}
