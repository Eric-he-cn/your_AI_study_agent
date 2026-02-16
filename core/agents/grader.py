"""Grader Agent for evaluating answers."""
import json
from typing import List
from core.llm.openai_compat import get_llm_client
from core.orchestration.prompts import GRADER_PROMPT
from backend.schemas import GradeReport, RetrievedChunk


class GraderAgent:
    """Grader agent for evaluating student answers."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def grade(
        self,
        question: str,
        standard_answer: str,
        rubric: str,
        student_answer: str
    ) -> GradeReport:
        """Grade student answer."""
        prompt = GRADER_PROMPT.format(
            question=question,
            standard_answer=standard_answer,
            rubric=rubric,
            student_answer=student_answer
        )
        
        messages = [
            {"role": "system", "content": "你是一位公正的评分专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.3, max_tokens=1000)
        
        # Parse response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            grade_dict = json.loads(json_str)
            
            return GradeReport(
                score=float(grade_dict.get("score", 0)),
                feedback=grade_dict.get("feedback", ""),
                mistake_tags=grade_dict.get("mistake_tags", []),
                references=[]
            )
        except Exception as e:
            print(f"Error parsing grade: {e}")
            return GradeReport(
                score=0.0,
                feedback="评分时出错，请重试。",
                mistake_tags=[],
                references=[]
            )
