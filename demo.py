"""
Demo script showing how to use the Course Learning Agent system.

This script demonstrates:
1. Creating a workspace
2. Ingesting documents
3. Building RAG index
4. Using different modes (Learn, Practice, Exam)
"""
import os
import sys

# Note: This is a demonstration script. To actually run it:
# 1. Install dependencies: pip install -r requirements.txt
# 2. Configure .env with your API key
# 3. Run: python demo.py


def demo_workflow():
    """Demonstrate the complete workflow."""
    
    print("=" * 70)
    print("Course Learning Agent - Demo Workflow")
    print("=" * 70)
    print()
    
    # Step 1: Setup
    print("📋 Step 1: Initial Setup")
    print("-" * 70)
    print("1. Clone the repository")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Configure .env file with your OPENAI_API_KEY")
    print()
    
    # Step 2: Start services
    print("🚀 Step 2: Start Services")
    print("-" * 70)
    print("Terminal 1: python backend/api.py")
    print("Terminal 2: streamlit run frontend/streamlit_app.py")
    print()
    
    # Step 3: Create workspace
    print("📚 Step 3: Create Course Workspace")
    print("-" * 70)
    print("In the Streamlit UI:")
    print("  1. Click '➕ 创建新课程'")
    print("  2. Enter course name: '线性代数'")
    print("  3. Enter subject: '数学'")
    print("  4. Click '创建'")
    print()
    
    # Step 4: Upload documents
    print("📄 Step 4: Upload Course Materials")
    print("-" * 70)
    print("Upload sample documents:")
    print("  - tests/sample_textbook.txt (provided)")
    print("  - Your own PDF/TXT/MD files")
    print()
    print("Then click '🔨 构建索引' to build the RAG index")
    print()
    
    # Step 5: Learn Mode
    print("📖 Step 5: Use Learn Mode")
    print("-" * 70)
    print("Example queries:")
    print("  ✓ '什么是矩阵的秩？'")
    print("  ✓ '解释线性相关和线性无关'")
    print("  ✓ '如何计算矩阵的秩？'")
    print()
    print("Expected output:")
    print("  - Structured answer with definitions")
    print("  - Citations from textbook with page numbers")
    print("  - Key points and common mistakes")
    print()
    
    # Step 6: Practice Mode
    print("✍️ Step 6: Use Practice Mode")
    print("-" * 70)
    print("Example workflow:")
    print("  1. User: '给我出一道关于矩阵秩的中等难度练习题'")
    print("  2. System: [Generates question with rubric]")
    print("  3. User: [Submits answer]")
    print("  4. System: [Provides score, feedback, and mistake analysis]")
    print()
    print("Mistakes are automatically saved to:")
    print("  data/workspaces/<course>/mistakes/mistakes.jsonl")
    print()
    
    # Step 7: Exam Mode
    print("📝 Step 7: Use Exam Mode")
    print("-" * 70)
    print("Example workflow:")
    print("  1. Switch to 'Exam Mode' in sidebar")
    print("  2. User: '开始线性代数第一章测试'")
    print("  3. System: [Generates exam question]")
    print("     Note: WebSearch is disabled in this mode")
    print("  4. User: [Submits answer]")
    print("  5. System: [Provides grade and report]")
    print()
    
    # Step 8: Review
    print("📊 Step 8: Review and Analyze")
    print("-" * 70)
    print("Check your progress:")
    print("  - View mistake log: data/workspaces/<course>/mistakes/")
    print("  - Review notes: data/workspaces/<course>/notes/")
    print("  - Analyze weak topics from exam reports")
    print()
    
    print("=" * 70)
    print("✅ Demo workflow complete!")
    print("=" * 70)
    print()
    print("💡 Tips:")
    print("  - Use specific terminology for better RAG retrieval")
    print("  - Each mode has different tool permissions")
    print("  - All answers include textbook citations")
    print("  - Practice mode builds a mistake log automatically")
    print()


def show_api_examples():
    """Show API usage examples."""
    print()
    print("=" * 70)
    print("API Usage Examples")
    print("=" * 70)
    print()
    
    print("1️⃣ Create Workspace:")
    print("-" * 70)
    print("""
POST http://localhost:8000/workspaces
Content-Type: application/json

{
    "course_name": "线性代数",
    "subject": "数学"
}
""")
    
    print("2️⃣ Upload Document:")
    print("-" * 70)
    print("""
POST http://localhost:8000/workspaces/线性代数/upload
Content-Type: multipart/form-data

file: <your_file.pdf>
""")
    
    print("3️⃣ Build Index:")
    print("-" * 70)
    print("""
POST http://localhost:8000/workspaces/线性代数/build-index
""")
    
    print("4️⃣ Chat (Learn Mode):")
    print("-" * 70)
    print("""
POST http://localhost:8000/chat
Content-Type: application/json

{
    "course_name": "线性代数",
    "mode": "learn",
    "message": "什么是矩阵的秩？",
    "history": []
}

Response:
{
    "message": {
        "role": "assistant",
        "content": "[Structured teaching content]",
        "citations": [
            {
                "text": "矩阵的秩定义为...",
                "doc_id": "sample_textbook.txt",
                "page": null,
                "score": 0.85
            }
        ]
    },
    "plan": {
        "need_rag": true,
        "allowed_tools": ["calculator", "websearch", "filewriter"],
        "task_type": "learn"
    }
}
""")


def show_architecture():
    """Show system architecture."""
    print()
    print("=" * 70)
    print("System Architecture Overview")
    print("=" * 70)
    print()
    print("""
┌─────────────┐
│  Streamlit  │  Frontend UI (port 8501)
│   Frontend  │  - Course selection
└──────┬──────┘  - Mode switching
       │         - Chat interface
       │ HTTP
┌──────▼──────┐
│   FastAPI   │  Backend API (port 8000)
│   Backend   │  - Workspace management
└──────┬──────┘  - Document upload
       │         - Chat endpoint
       │
┌──────▼──────────────────┐
│  Orchestration Runner   │  Core orchestration
│                         │
│  ┌─────────────────┐   │
│  │  Router Agent   │   │  Planning
│  └────────┬────────┘   │
│           │            │
│  ┌────────▼────────┐   │
│  │  Tutor Agent    │   │  Teaching (Learn mode)
│  │  QuizMaster     │   │  Question gen (Practice/Exam)
│  │  Grader Agent   │   │  Evaluation (Practice/Exam)
│  └────────┬────────┘   │
└───────────┼────────────┘
            │
    ┌───────┼───────┐
    │       │       │
┌───▼───┐ ┌─▼──┐ ┌─▼─────┐
│  RAG  │ │MCP │ │Output │
│System │ │Tool│ │Format │
└───────┘ └────┘ └───────┘

Key Components:
- RAG: Document parsing, chunking, embedding, retrieval
- MCP: Calculator, WebSearch, FileWriter tools
- Agents: Router, Tutor, QuizMaster, Grader
- Policy: Tool permission control per mode
""")


if __name__ == "__main__":
    demo_workflow()
    
    if "--api" in sys.argv:
        show_api_examples()
    
    if "--arch" in sys.argv:
        show_architecture()
    
    print()
    print("💻 For detailed documentation, see:")
    print("   - README.md: Overview and quick start")
    print("   - USAGE.md: Detailed usage examples")
    print("   - ARCHITECTURE.md: System design details")
    print()
