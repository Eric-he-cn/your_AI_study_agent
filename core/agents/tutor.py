"""Tutor Agent for learning mode."""
from typing import List
from core.llm.openai_compat import get_llm_client
from core.orchestration.prompts import TUTOR_PROMPT
from backend.schemas import RetrievedChunk


class TutorAgent:
    """Tutor agent for teaching and explaining concepts."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def teach(
        self,
        question: str,
        course_name: str,
        context: str
    ) -> str:
        """Generate teaching response with citations."""
        prompt = TUTOR_PROMPT.format(
            course_name=course_name,
            context=context,
            question=question
        )
        
        messages = [
            {"role": "system", "content": "你是一位专业的大学课程导师。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.7, max_tokens=1500)
        return response
