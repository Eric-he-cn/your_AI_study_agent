"""Simple integration tests for the Course Learning Agent."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from backend.schemas import CourseWorkspace, Plan, Quiz
        from core.llm.openai_compat import LLMClient
        from core.agents.router import RouterAgent
        from core.agents.tutor import TutorAgent
        from rag.chunk import chunk_documents
        from rag.store_faiss import FAISSStore
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_schemas():
    """Test data schemas."""
    try:
        from backend.schemas import Plan, Quiz, GradeReport
        from datetime import datetime
        
        # Test Plan
        plan = Plan(
            need_rag=True,
            allowed_tools=["calculator"],
            task_type="learn",
            style="step_by_step",
            output_format="answer"
        )
        assert plan.need_rag == True
        
        # Test Quiz
        quiz = Quiz(
            question="Test question",
            standard_answer="Test answer",
            rubric="Test rubric",
            difficulty="medium"
        )
        assert quiz.difficulty == "medium"
        
        print("✅ Schema tests passed")
        return True
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        return False


def test_rag_components():
    """Test RAG components."""
    try:
        from rag.chunk import simple_chunk_text
        
        text = "This is a test. " * 100
        chunks = simple_chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) > 0
        
        print(f"✅ RAG test passed - generated {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"❌ RAG test error: {e}")
        return False


def test_tool_policy():
    """Test tool policy."""
    try:
        from core.orchestration.policies import ToolPolicy
        
        learn_tools = ToolPolicy.get_allowed_tools("learn")
        assert "calculator" in learn_tools
        assert "websearch" in learn_tools
        
        exam_tools = ToolPolicy.get_allowed_tools("exam")
        assert "calculator" in exam_tools
        assert "websearch" not in exam_tools  # Should be disabled in exam
        
        print("✅ Tool policy tests passed")
        return True
    except Exception as e:
        print(f"❌ Tool policy test error: {e}")
        return False


def test_mcp_tools():
    """Test MCP tools."""
    try:
        from mcp_tools.client import MCPTools
        
        # Test calculator
        result = MCPTools.calculator("2 + 2")
        assert result["success"] == True
        assert result["result"] == 4
        
        # Test websearch
        result = MCPTools.websearch("test query")
        assert result["success"] == True
        
        print("✅ MCP tools tests passed")
        return True
    except Exception as e:
        print(f"❌ MCP tools test error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Course Learning Agent Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Schemas", test_schemas),
        ("RAG Components", test_rag_components),
        ("Tool Policy", test_tool_policy),
        ("MCP Tools", test_mcp_tools),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 60)
        success = test_func()
        results.append((name, success))
        print()
    
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
