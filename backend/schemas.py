"""Backend schemas for Course Learning Agent."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class CourseWorkspace(BaseModel):
    """Course workspace configuration."""
    course_name: str
    subject: str  # e.g., "线性代数", "通信原理"
    created_at: datetime = Field(default_factory=datetime.now)
    documents: List[str] = Field(default_factory=list)
    index_path: Optional[str] = None
    notes_path: Optional[str] = None
    mistakes_path: Optional[str] = None
    exams_path: Optional[str] = None


class RetrievedChunk(BaseModel):
    """Retrieved document chunk with citation."""
    text: str
    doc_id: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    score: float


class Plan(BaseModel):
    """Agent orchestration plan."""
    need_rag: bool = True
    allowed_tools: List[str] = Field(default_factory=list)
    task_type: Literal["learn", "practice", "exam", "general"] = "learn"
    style: Literal["step_by_step", "hint_first", "direct"] = "step_by_step"
    output_format: Literal["answer", "quiz", "exam", "report"] = "answer"


class Quiz(BaseModel):
    """Quiz question."""
    question: str
    standard_answer: str
    rubric: str  # Evaluation criteria
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    chapter: Optional[str] = None
    concept: Optional[str] = None


class GradeReport(BaseModel):
    """Grading report for practice."""
    score: float  # 0-100
    feedback: str
    mistake_tags: List[str] = Field(default_factory=list)  # e.g., ["概念性错误", "计算错误"]
    references: List[RetrievedChunk] = Field(default_factory=list)


class ExamReport(BaseModel):
    """Exam performance report."""
    overall_score: float
    weak_topics: List[str]
    recommendations: List[str]
    wrong_questions: List[Dict[str, Any]]


class ChatMessage(BaseModel):
    """Chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    citations: Optional[List[RetrievedChunk]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    """Chat request."""
    course_name: str
    mode: Literal["learn", "practice", "exam"]
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Chat response."""
    message: ChatMessage
    plan: Optional[Plan] = None
