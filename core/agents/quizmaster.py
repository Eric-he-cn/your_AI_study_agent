"""QuizMaster Agent for generating questions."""
import json
from core.llm.openai_compat import get_llm_client
from core.orchestration.prompts import QUIZMASTER_PROMPT
from backend.schemas import Quiz


class QuizMasterAgent:
    """QuizMaster agent for generating practice questions."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def generate_quiz(
        self,
        course_name: str,
        topic: str,
        difficulty: str,
        context: str
    ) -> Quiz:
        """Generate a quiz question."""
        prompt = QUIZMASTER_PROMPT.format(
            course_name=course_name,
            topic=topic,
            difficulty=difficulty,
            context=context
        )
        
        messages = [
            {"role": "system", "content": "你是一位出题专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.8, max_tokens=1000)
        
        # Parse response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            quiz_dict = json.loads(json_str)
            return Quiz(**quiz_dict)
        except Exception as e:
            print(f"Error parsing quiz: {e}")
            # Return a default quiz
            return Quiz(
                question="生成题目时出错，请重试。",
                standard_answer="N/A",
                rubric="N/A",
                difficulty=difficulty,
                chapter=topic
            )
