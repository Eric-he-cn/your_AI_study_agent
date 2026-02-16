"""Streamlit frontend for Course Learning Agent."""
import streamlit as st
import requests
import json
import os
from datetime import datetime

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
        response = requests.post(f"{API_BASE}/workspaces/{course_name}/build-index")
        if response.status_code == 200:
            data = response.json()
            st.success(f"索引构建成功！共 {data['num_chunks']} 个文本块")
            return True
    except Exception as e:
        st.error(f"构建索引失败: {e}")
    return False


def send_message(course_name: str, mode: str, message: str):
    """Send a chat message."""
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "course_name": course_name,
                "mode": mode,
                "message": message,
                "history": []
            }
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"发送消息失败: {e}")
    return None


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
    with st.expander("➕ 创建新课程"):
        new_course_name = st.text_input("课程名称", key="new_course_name")
        new_subject = st.text_input("学科标签", key="new_subject", 
                                    placeholder="例如：线性代数、通信原理")
        if st.button("创建"):
            if new_course_name and new_subject:
                create_workspace(new_course_name, new_subject)
    
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
            type=["pdf", "txt", "md"],
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
            st.markdown(msg["content"])
            
            # Display citations if available
            if msg.get("citations"):
                with st.expander("📑 查看引用"):
                    for i, citation in enumerate(msg["citations"]):
                        st.markdown(f"**引用 {i+1}**: {citation['doc_id']}")
                        if citation.get("page"):
                            st.markdown(f"页码: {citation['page']}")
                        st.text(citation["text"][:200] + "..." if len(citation["text"]) > 200 else citation["text"])
            
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
        
        # Send message and get response
        with st.spinner("思考中..."):
            response = send_message(
                st.session_state.current_course,
                st.session_state.current_mode,
                user_input
            )
        
        if response:
            message = response["message"]
            
            # Add assistant message to history
            history_msg = {
                "role": "assistant",
                "content": message["content"]
            }
            if message.get("citations"):
                history_msg["citations"] = message["citations"]
            if message.get("tool_calls"):
                history_msg["tool_calls"] = message["tool_calls"]
            
            st.session_state.chat_history.append(history_msg)
            
            # Display assistant message
            with st.chat_message("assistant"):
                st.markdown(message["content"])
                
                # Display citations
                if message.get("citations"):
                    with st.expander("📑 查看引用"):
                        for i, citation in enumerate(message["citations"]):
                            st.markdown(f"**引用 {i+1}**: {citation['doc_id']}")
                            if citation.get("page"):
                                st.markdown(f"页码: {citation['page']}")
                            st.text(citation["text"][:200] + "..." if len(citation["text"]) > 200 else citation["text"])
                
                # Display tool calls
                if message.get("tool_calls"):
                    with st.expander("🔧 工具调用"):
                        for tool_call in message["tool_calls"]:
                            st.json(tool_call)
            
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
