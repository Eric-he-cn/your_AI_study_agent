"""Router Agent for task planning."""
import json
from typing import Dict, Any
from core.llm.openai_compat import get_llm_client
from core.orchestration.prompts import ROUTER_PROMPT
from core.orchestration.policies import ToolPolicy
from backend.schemas import Plan


class RouterAgent:
    """Router agent for planning task execution."""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    def plan(
        self,
        user_message: str,
        mode: str,
        course_name: str
    ) -> Plan:
        """Generate execution plan."""
        prompt = ROUTER_PROMPT.format(
            mode=mode,
            course_name=course_name,
            user_message=user_message
        )
        
        messages = [
            {"role": "system", "content": "你是一个任务规划助手。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.chat(messages, temperature=0.3)
        
        # Parse response and create plan
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            plan_dict = json.loads(json_str)
            
            # Override with policy if needed
            allowed_tools = ToolPolicy.get_allowed_tools(mode)
            plan_dict["allowed_tools"] = allowed_tools
            plan_dict["task_type"] = mode
            
            return Plan(**plan_dict)
        except Exception as e:
            print(f"Error parsing plan: {e}, using defaults")
            # Return default plan
            return Plan(
                need_rag=True,
                allowed_tools=ToolPolicy.get_allowed_tools(mode),
                task_type=mode,
                style="step_by_step",
                output_format="answer"
            )
