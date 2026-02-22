"""Streamlit frontend for Course Learning Agent."""
import re
import streamlit as st
import requests
import json
import os
from datetime import datetime


def fix_latex(text: str) -> str:
    """将 LLM 输出的 LaTeX 定界符转换为 Streamlit KaTeX 可识别的格式。
    \\[...\\]  →  $$...$$  （块公式）
    \\(...\\)  →  $...$    （行内公式）
    """
    if not text:
        return text
    # 块公式：\[ ... \]  →  $$...$$
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'$$\1$$', text, flags=re.DOTALL)
    # 行内公式：\( ... \)  →  $...$
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r'$\1$', text, flags=re.DOTALL)
    return text

# API endpoint
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="课程学习助手",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if "current_course" not in st.session_state:
    st.session_state.current_course = None
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "learn"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "workspaces" not in st.session_state:
    st.session_state.workspaces = []


def load_workspaces():
    """Load available workspaces."""
    try:
        response = requests.get(f"{API_BASE}/workspaces")
        if response.status_code == 200:
            st.session_state.workspaces = response.json()
    except Exception as e:
        st.error(f"加载课程失败: {e}")


def create_workspace(course_name: str, subject: str):
    """Create a new workspace."""
    try:
        response = requests.post(
            f"{API_BASE}/workspaces",
            json={"course_name": course_name, "subject": subject}
        )
        if response.status_code == 200:
            st.success(f"课程 '{course_name}' 创建成功！")
            load_workspaces()
            return True
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text or f"HTTP {response.status_code}"
            st.error(f"创建失败: {detail}")
    except Exception as e:
        st.error(f"创建课程失败: {e}")
    return False


def upload_file(course_name: str, file):
    """Upload a file to workspace."""
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(
            f"{API_BASE}/workspaces/{course_name}/upload",
            files=files
        )
        if response.status_code == 200:
            return True
    except Exception as e:
        st.error(f"上传文件失败: {e}")
    return False


def build_index(course_name: str):
    """Build RAG index for workspace."""
    try:
        response = requests.post(
            f"{API_BASE}/workspaces/{course_name}/build-index",
            timeout=300  # 最长等待5分钟（首次需下载嵌入模型）
        )
        if response.status_code == 200:
            data = response.json()
            st.success(f"索引构建成功！共 {data['num_chunks']} 个文本块")
            return True
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text or f"HTTP {response.status_code}"
            st.error(f"构建失败: {detail}")
    except requests.exceptions.Timeout:
        st.error("构建超时，请检查后端是否在下载嵌入模型，稍后重试")
    except Exception as e:
        st.error(f"构建索引失败: {e}")
    return False


def send_message(course_name: str, mode: str, message: str):
    """Send a chat message with history."""
    try:
        # 取当前消息之前的最多 20 条历史（[-21:-1] 排除最后一条刚 append 的用户消息，避免重复）
        history = st.session_state.chat_history[-21:-1] if st.session_state.chat_history else []
        # 只保留 role 和 content 字段
        history_payload = [{"role": m["role"], "content": m["content"]} for m in history]
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "course_name": course_name,
                "mode": mode,
                "message": message,
                "history": history_payload
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json()
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text or f"HTTP {response.status_code}"
            st.error(f"请求失败: {detail}")
    except requests.exceptions.Timeout:
        st.error("请求超时，请稍后重试")
    except Exception as e:
        st.error(f"发送消息失败: {e}")
    return None


def stream_chat(course_name: str, mode: str, message: str):
    """流式发送消息，返回文本 chunk 生成器（供 st.write_stream 使用）。"""
    import json as _json
    # 取当前消息之前的最多 20 条历史（[-21:-1] 排除最后一条刚 append 的用户消息，避免重复）
    history = st.session_state.chat_history[-21:-1] if st.session_state.chat_history else []
    history_payload = [{"role": m["role"], "content": m["content"]} for m in history]
    payload = {
        "course_name": course_name,
        "mode": mode,
        "message": message,
        "history": history_payload,
    }
    try:
        with requests.post(
            f"{API_BASE}/chat/stream",
            json=payload,
            stream=True,
            timeout=180,
        ) as resp:
            if resp.status_code != 200:
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    detail = resp.text or f"HTTP {resp.status_code}"
                yield f"（请求失败：{detail}）"
                return
            for raw_line in resp.iter_lines():
                if raw_line:
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        # JSON 解码，还原换行符等特殊字符
                        try:
                            yield _json.loads(data)
                        except _json.JSONDecodeError:
                            yield data
    except requests.exceptions.Timeout:
        yield "（请求超时，请稍后重试）"
    except Exception as e:
        yield f"（流式输出失败：{e}）"


# Main UI
st.title("📚 课程学习助手")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ 设置")
    
    # Load workspaces
    if st.button("🔄 刷新课程列表"):
        load_workspaces()
    
    # Create new workspace
    if "expander_open" not in st.session_state:
        st.session_state.expander_open = False
    with st.expander("➕ 创建新课程", expanded=st.session_state.expander_open):
        new_course_name = st.text_input("课程名称", key="new_course_name")
        new_subject = st.text_input("学科标签", key="new_subject", 
                                    placeholder="例如：线性代数、通信原理")
        if st.button("创建"):
            st.session_state.expander_open = True
            if new_course_name and new_subject:
                create_workspace(new_course_name, new_subject)
            else:
                st.warning("请填写课程名称和学科标签")
    
    # Select workspace
    st.markdown("### 📖 选择课程")
    if st.session_state.workspaces:
        course_names = [w["course_name"] for w in st.session_state.workspaces]
        selected = st.selectbox(
            "当前课程",
            course_names,
            key="course_selector"
        )
        if selected != st.session_state.current_course:
            st.session_state.current_course = selected
            st.session_state.chat_history = []
    else:
        st.info("暂无课程，请创建新课程")
    
    # Mode selection
    st.markdown("### 🎯 学习模式")
    mode = st.radio(
        "选择模式",
        ["learn", "practice", "exam"],
        format_func=lambda x: {
            "learn": "📖 学习模式",
            "practice": "✍️ 练习模式",
            "exam": "📝 考试模式"
        }[x],
        key="mode_selector"
    )
    if mode != st.session_state.current_mode:
        st.session_state.current_mode = mode
    
    # Knowledge base management
    if st.session_state.current_course:
        st.markdown("### 📚 知识库管理")
        
        uploaded_file = st.file_uploader(
            "上传资料",
            type=["pdf", "txt", "md", "docx", "pptx", "ppt"],
            key="file_uploader"
        )
        
        if uploaded_file and st.button("上传"):
            if upload_file(st.session_state.current_course, uploaded_file):
                st.success(f"文件 {uploaded_file.name} 上传成功！")
        
        if st.button("🔨 构建索引"):
            with st.spinner("正在构建索引..."):
                build_index(st.session_state.current_course)

# Main content
if st.session_state.current_course:
    # Display current settings
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"**当前课程**: {st.session_state.current_course}")
    with col2:
        mode_names = {
            "learn": "📖 学习模式",
            "practice": "✍️ 练习模式",
            "exam": "📝 考试模式"
        }
        st.info(f"**当前模式**: {mode_names[st.session_state.current_mode]}")
    
    # Mode descriptions
    mode_descriptions = {
        "learn": "💡 **学习模式**: 概念讲解、答疑解惑，所有回答都会引用教材来源",
        "practice": "✍️ **练习模式**: 生成练习题、评分讲评、记录错题",
        "exam": "📝 **考试模式**: 模拟考试环境，禁用网页搜索，独立完成"
    }
    st.markdown(mode_descriptions[st.session_state.current_mode])
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 对话区")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(fix_latex(msg["content"]))
            
            # Display citations if available
            if msg.get("citations"):
                with st.expander(f"📑 查看引用来源（共 {len(msg['citations'])} 条）"):
                    for i, citation in enumerate(msg["citations"]):
                        page_str = f"  第 {citation['page']} 页" if citation.get("page") else ""
                        score_str = f"  相关度 {citation['score']:.2f}" if citation.get("score") is not None else ""
                        st.markdown(
                            f"**[来源{i+1}]** `{citation['doc_id']}`{page_str}{score_str}"
                        )
                        preview = citation["text"][:300].replace("\n", " ").strip()
                        if len(citation["text"]) > 300:
                            preview += "…"
                        st.caption(preview)
                        if i < len(msg["citations"]) - 1:
                            st.divider()
            
            # Display tool calls if available
            if msg.get("tool_calls"):
                with st.expander("🔧 工具调用"):
                    for tool_call in msg["tool_calls"]:
                        st.json(tool_call)
    
    # Chat input
    user_input = st.chat_input("输入你的问题...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 流式输出助手回答
        # 单独收集文本，避免依赖 st.write_stream 返回类型（新版 Streamlit 返回 StreamingOutput 而非 str）
        collected_chunks: list[str] = []

        def _collecting_stream():
            for chunk in stream_chat(
                st.session_state.current_course,
                st.session_state.current_mode,
                user_input,
            ):
                if isinstance(chunk, str):
                    collected_chunks.append(chunk)
                yield chunk

        with st.chat_message("assistant"):
            st.write_stream(_collecting_stream())

        full_response = "".join(collected_chunks)
        
        if full_response:
            # 捕获流式过程中拦截到的 citations
            citations = st.session_state.pop("_pending_citations", None) or None
            # 把完整回答加入对话历史（存储时转换定界符，方便后续重渲染）
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": fix_latex(full_response),
                "citations": citations,
            })
        
        st.rerun()

else:
    st.info("👈 请先在侧边栏选择或创建一个课程")
    
    # Show features
    st.markdown("## ✨ 功能特性")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📖 学习模式")
        st.markdown("""
        - 概念讲解与答疑
        - 教材引用与溯源
        - 知识点总结
        - 支持搜索辅助
        """)
    
    with col2:
        st.markdown("### ✍️ 练习模式")
        st.markdown("""
        - 智能出题
        - 自动评分讲评
        - 错题本记录
        - 针对性建议
        """)
    
    with col3:
        st.markdown("### 📝 考试模式")
        st.markdown("""
        - 模拟考试环境
        - 自动组卷
        - 考后报告
        - 薄弱点分析
        """)
