"""Grader Agent for evaluating answers."""
import json
from typing import List, Optional
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
        student_answer: str,
        course_name: Optional[str] = None,
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
            report = GradeReport(
                score=float(grade_dict.get("score", 0)),
                feedback=grade_dict.get("feedback", ""),
                mistake_tags=grade_dict.get("mistake_tags", []),
                references=[]
            )
            # 写入记忆（course_name 可能为 None，此时跳过）
            if course_name:
                self._save_to_memory(
                    course_name=course_name,
                    question=question,
                    student_answer=student_answer,
                    score=report.score,
                    mistake_tags=report.mistake_tags,
                )
            return report
        except Exception as e:
            print(f"Error parsing grade: {e}")
            return GradeReport(
                score=0.0,
                feedback="评分时出错，请重试。",
                mistake_tags=[],
                references=[]
            )

    def _save_to_memory(
        self,
        course_name: str,
        question: str,
        student_answer: str,
        score: float,
        mistake_tags: List[str],
    ) -> None:
        """将练习结果写入情景记忆（错题重要性=0.9，正确=0.4）。"""
        try:
            from memory.manager import get_memory_manager
            mgr = get_memory_manager()
            is_mistake = score < 60
            importance = 0.9 if is_mistake else 0.4
            content = f"题目: {question[:200]}\n学生答案: {student_answer[:200]}\n得分: {score:.0f}"
            if mistake_tags:
                content += f"\n错误类型: {', '.join(mistake_tags)}"
            event_type = "mistake" if is_mistake else "practice"
            mgr.save_episode(
                course_name=course_name,
                event_type=event_type,
                content=content,
                importance=importance,
                metadata={"score": score, "tags": mistake_tags},
            )
            if mistake_tags and is_mistake:
                mgr.update_weak_points(course_name, mistake_tags)
            mgr.record_practice_result(course_name, score, is_mistake)
        except Exception as e:
            print(f"[Memory] 错题记忆写入失败（不影响评分）: {e}")
