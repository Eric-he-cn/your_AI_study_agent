"""MCP Tools - Calculator, WebSearch (SerpAPI), FileWriter with OpenAI tool schemas."""
import json
import os
import math
import requests
from typing import Dict, Any, List


# ── OpenAI Function Calling Schema 定义 ─────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，支持加减乘除、幂运算、三角函数、对数等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '2**10'、'sin(3.14/2)'、'log(100, 10)'"
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


# ── 工具实现 ─────────────────────────────────────────────────────────────────

class MCPTools:
    """MCP tools implementation with real backends."""

    # 由 runner 在每次调用前注入上下文（如 notes_dir）
    _context: Dict[str, Any] = {}

    @staticmethod
    def calculator(expression: str) -> Dict[str, Any]:
        """安全地计算数学表达式。"""
        try:
            safe_globals = {
                "__builtins__": {},
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "asin": math.asin, "acos": math.acos, "atan": math.atan,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "log2": math.log2, "exp": math.exp, "abs": abs,
                "pi": math.pi, "e": math.e, "pow": math.pow,
                "floor": math.floor, "ceil": math.ceil, "round": round,
            }
            result = eval(expression, safe_globals, {})
            return {
                "tool": "calculator",
                "expression": expression,
                "result": result,
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
