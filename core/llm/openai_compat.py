"""Core LLM client with OpenAI-compatible interface."""
import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """OpenAI-compatible LLM client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Send chat completion request."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """带 Function Calling 的对话，支持多轮工具调用直到 LLM 停止请求工具。"""
        import logging
        logger = logging.getLogger("chat_with_tools")
        from mcp_tools.client import MCPTools

        if not tools:
            return self.chat(messages, temperature, max_tokens)

        tool_names = [t["function"]["name"] for t in tools]
        logger.info(f"[Tools] 可用工具: {tool_names}")
        messages = list(messages)
        max_rounds = 6  # 最多 6 轮工具调用，防止死循环

        try:
            for round_idx in range(max_rounds):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                msg = response.choices[0].message

                # LLM 不再调用工具，返回最终答案
                if not msg.tool_calls:
                    logger.info(f"[Tools] 第 {round_idx+1} 轮：LLM 完成回答，未请求更多工具")
                    return msg.content or ""

                logger.info(f"[Tools] 第 {round_idx+1} 轮：LLM 请求调用工具: "
                            f"{[tc.function.name for tc in msg.tool_calls]}")

                # 把 assistant 消息加入历史
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })

                # 执行每个工具并把结果加入历史
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    logger.info(f"[Tools] 执行工具 '{tool_name}'，参数: {tool_args}")
                    tool_result = MCPTools.call_tool(tool_name, **tool_args)
                    logger.info(f"[Tools] 工具 '{tool_name}' 结果: {str(tool_result)[:300]}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

            # 超过最大轮数，做一次不带工具的最终调用
            logger.warning("[Tools] 已达最大工具调用轮数，强制生成最终回答")
            final = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return final.choices[0].message.content or ""

        except Exception as e:
            print(f"[chat_with_tools] 工具调用失败，降级为普通对话: {e}")
            return self.chat(messages, temperature, max_tokens)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ):
        """Send streaming chat completion request."""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error calling LLM: {str(e)}"

    def chat_stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """工具调用（非流式）后，将最终回答流式输出，返回生成器。"""
        import logging
        logger = logging.getLogger("chat_stream_with_tools")
        from mcp_tools.client import MCPTools

        if not tools:
            yield from self.chat_stream(messages, temperature, max_tokens=max_tokens)
            return

        tool_names = [t["function"]["name"] for t in tools]
        logger.info(f"[StreamTools] 可用工具: {tool_names}")
        messages = list(messages)
        max_rounds = 6

        try:
            for round_idx in range(max_rounds):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                msg = response.choices[0].message

                if not msg.tool_calls:
                    logger.info(f"[StreamTools] 第 {round_idx+1} 轮：工具调用完毕，开始流式输出")
                    # 工具调用结束，用当前 messages 做流式最终回答
                    yield from self.chat_stream(messages, temperature, max_tokens=max_tokens)
                    return

                logger.info(f"[StreamTools] 第 {round_idx+1} 轮：调用工具 "
                            f"{[tc.function.name for tc in msg.tool_calls]}")

                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                })

                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    logger.info(f"[StreamTools] 执行工具 '{tool_name}'，参数: {tool_args}")
                    tool_result = MCPTools.call_tool(tool_name, **tool_args)
                    logger.info(f"[StreamTools] 工具 '{tool_name}' 结果: {str(tool_result)[:300]}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

            logger.warning("[StreamTools] 已达最大工具调用轮数，流式输出最终回答")
            yield from self.chat_stream(messages, temperature, max_tokens=max_tokens)

        except Exception as e:
            logger.error(f"[StreamTools] 流式工具调用失败: {e}")
            yield f"（工具调用出错，降级回答）\n"
            yield from self.chat_stream(messages, temperature, max_tokens=max_tokens)


# Global LLM client instance
_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
