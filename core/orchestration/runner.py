"""Main orchestration runner."""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.schemas import (
    Plan, ChatMessage, RetrievedChunk, Quiz, GradeReport
)
from core.agents.router import RouterAgent
from core.agents.tutor import TutorAgent
from core.agents.quizmaster import QuizMasterAgent
from core.agents.grader import GraderAgent
from rag.retrieve import Retriever
from rag.store_faiss import FAISSStore
from mcp_tools.client import MCPTools


class OrchestrationRunner:
    """Main orchestration runner for the course agent system."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.getenv("DATA_DIR", "./data/workspaces")
        self.data_dir = data_dir
        
        # Initialize agents
        self.router = RouterAgent()
        self.tutor = TutorAgent()
        self.quizmaster = QuizMasterAgent()
        self.grader = GraderAgent()
        self.tools = MCPTools()
    
    def get_workspace_path(self, course_name: str) -> str:
        """Get workspace path for a course."""
        return os.path.join(self.data_dir, course_name)
    
    def load_retriever(self, course_name: str) -> Optional[Retriever]:
        """Load retriever for a course."""
        workspace_path = self.get_workspace_path(course_name)
        index_path = os.path.join(workspace_path, "index", "faiss_index")
        
        if not os.path.exists(f"{index_path}.faiss"):
            return None
        
        store = FAISSStore()
        store.load(index_path)
        return Retriever(store)
    
    def run_learn_mode(
        self,
        course_name: str,
        user_message: str,
        plan: Plan
    ) -> ChatMessage:
        """Execute learn mode."""
        # Retrieve context if needed
        context = ""
        citations = []
        
        if plan.need_rag:
            retriever = self.load_retriever(course_name)
            if retriever:
                chunks = retriever.retrieve(user_message)
                context = retriever.format_context(chunks)
                citations = chunks
            else:
                context = "（未找到相关教材，请先上传课程资料）"
        
        # Generate teaching response
        response_text = self.tutor.teach(user_message, course_name, context)
        
        return ChatMessage(
            role="assistant",
            content=response_text,
            citations=citations if citations else None,
            tool_calls=None
        )
    
    def run_practice_mode(
        self,
        course_name: str,
        user_message: str,
        plan: Plan,
        state: Dict[str, Any] = None
    ) -> ChatMessage:
        """Execute practice mode."""
        if state is None:
            state = {}
        
        # Check if we're generating a quiz or grading an answer
        if "current_quiz" not in state:
            # Generate new quiz
            retriever = self.load_retriever(course_name)
            context = ""
            citations = []
            
            if retriever:
                chunks = retriever.retrieve(user_message)
                context = retriever.format_context(chunks)
                citations = chunks
            
            # Extract topic and difficulty from message
            topic = user_message
            difficulty = "medium"
            if "简单" in user_message or "易" in user_message:
                difficulty = "easy"
            elif "困难" in user_message or "难" in user_message:
                difficulty = "hard"
            
            quiz = self.quizmaster.generate_quiz(course_name, topic, difficulty, context)
            
            response_text = f"""## 练习题目

{quiz.question}

**难度**: {quiz.difficulty}
**章节**: {quiz.chapter or '综合'}

请回答上述问题，我会为你评分并提供反馈。
"""
            
            return ChatMessage(
                role="assistant",
                content=response_text,
                citations=citations if citations else None,
                tool_calls=None
            )
        else:
            # Grade student answer
            quiz = state["current_quiz"]
            student_answer = user_message
            
            grade_report = self.grader.grade(
                quiz.question,
                quiz.standard_answer,
                quiz.rubric,
                student_answer
            )
            
            response_text = f"""## 评分结果

**得分**: {grade_report.score}/100

**反馈**:
{grade_report.feedback}

**错误类型**: {', '.join(grade_report.mistake_tags) if grade_report.mistake_tags else '无明显错误'}

**标准答案**:
{quiz.standard_answer}

---
继续练习请输入新的题目要求。
"""
            
            # Save to mistakes log
            if grade_report.score < 60:
                self._save_mistake(course_name, quiz, student_answer, grade_report)
            
            return ChatMessage(
                role="assistant",
                content=response_text,
                citations=None,
                tool_calls=None
            )
    
    def run_exam_mode(
        self,
        course_name: str,
        user_message: str,
        plan: Plan
    ) -> ChatMessage:
        """Execute exam mode."""
        # Simplified exam mode - generate a single exam question
        retriever = self.load_retriever(course_name)
        context = ""
        
        if retriever:
            chunks = retriever.retrieve(user_message, top_k=5)
            context = retriever.format_context(chunks)
        
        # Generate exam question (harder difficulty)
        quiz = self.quizmaster.generate_quiz(
            course_name,
            user_message,
            "hard",
            context
        )
        
        response_text = f"""## 模拟考试题目

{quiz.question}

**提示**: 这是考试模式，请独立完成。只允许使用计算器工具。

**评分标准**:
{quiz.rubric}

请提交你的答案。
"""
        
        return ChatMessage(
            role="assistant",
            content=response_text,
            citations=None,
            tool_calls=None
        )
    
    def _save_mistake(
        self,
        course_name: str,
        quiz: Quiz,
        student_answer: str,
        grade_report: GradeReport
    ):
        """Save mistake to log."""
        workspace_path = self.get_workspace_path(course_name)
        mistakes_dir = os.path.join(workspace_path, "mistakes")
        os.makedirs(mistakes_dir, exist_ok=True)
        
        mistake_file = os.path.join(mistakes_dir, "mistakes.jsonl")
        
        mistake_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": quiz.question,
            "student_answer": student_answer,
            "standard_answer": quiz.standard_answer,
            "score": grade_report.score,
            "feedback": grade_report.feedback,
            "mistake_tags": grade_report.mistake_tags
        }
        
        with open(mistake_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(mistake_entry, ensure_ascii=False) + '\n')
    
    def run(
        self,
        course_name: str,
        mode: str,
        user_message: str,
        state: Dict[str, Any] = None
    ) -> tuple[ChatMessage, Plan]:
        """Main orchestration entry point."""
        # Generate plan
        plan = self.router.plan(user_message, mode, course_name)
        
        # Execute based on mode
        if mode == "learn":
            response = self.run_learn_mode(course_name, user_message, plan)
        elif mode == "practice":
            response = self.run_practice_mode(course_name, user_message, plan, state)
        elif mode == "exam":
            response = self.run_exam_mode(course_name, user_message, plan)
        else:
            response = ChatMessage(
                role="assistant",
                content=f"未知模式: {mode}",
                citations=None,
                tool_calls=None
            )
        
        return response, plan
