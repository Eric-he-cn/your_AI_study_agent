"""Tool policy for different modes."""
from typing import List, Literal


class ToolPolicy:
    """Define tool access policy for different modes."""
    
    MODE_POLICIES = {
        "learn":    ["calculator", "websearch", "filewriter", "memory_search"],
        "practice": ["calculator", "filewriter", "memory_search"],
        "exam":     ["calculator"]
    }
    
    @staticmethod
    def get_allowed_tools(mode: Literal["learn", "practice", "exam"]) -> List[str]:
        """Get allowed tools for a mode."""
        return ToolPolicy.MODE_POLICIES.get(mode, [])
    
    @staticmethod
    def is_tool_allowed(tool: str, mode: Literal["learn", "practice", "exam"]) -> bool:
        """Check if a tool is allowed in a mode."""
        return tool in ToolPolicy.get_allowed_tools(mode)
