"""FastAPI backend for Course Learning Agent."""
import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from backend.schemas import (
    CourseWorkspace, ChatRequest, ChatResponse, ChatMessage
)
from rag.ingest import DocumentParser
from rag.chunk import chunk_documents
from rag.store_faiss import build_index
from core.orchestration.runner import OrchestrationRunner

app = FastAPI(title="Course Learning Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global runner
runner = OrchestrationRunner()

# In-memory workspace registry (in production, use database)
workspaces = {}


class CreateWorkspaceRequest(BaseModel):
    course_name: str
    subject: str


class MessageRequest(BaseModel):
    message: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Course Learning Agent API",
        "version": "0.1.0"
    }


@app.post("/workspaces", response_model=CourseWorkspace)
async def create_workspace(request: CreateWorkspaceRequest):
    """Create a new course workspace."""
    if request.course_name in workspaces:
        raise HTTPException(status_code=400, detail="Workspace already exists")
    
    workspace_path = runner.get_workspace_path(request.course_name)
    os.makedirs(workspace_path, exist_ok=True)
    os.makedirs(os.path.join(workspace_path, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(workspace_path, "index"), exist_ok=True)
    os.makedirs(os.path.join(workspace_path, "notes"), exist_ok=True)
    os.makedirs(os.path.join(workspace_path, "mistakes"), exist_ok=True)
    os.makedirs(os.path.join(workspace_path, "exams"), exist_ok=True)
    
    workspace = CourseWorkspace(
        course_name=request.course_name,
        subject=request.subject,
        created_at=datetime.now(),
        index_path=os.path.join(workspace_path, "index", "faiss_index"),
        notes_path=os.path.join(workspace_path, "notes"),
        mistakes_path=os.path.join(workspace_path, "mistakes"),
        exams_path=os.path.join(workspace_path, "exams")
    )
    
    workspaces[request.course_name] = workspace
    return workspace


@app.get("/workspaces", response_model=List[CourseWorkspace])
async def list_workspaces():
    """List all workspaces."""
    return list(workspaces.values())


@app.get("/workspaces/{course_name}", response_model=CourseWorkspace)
async def get_workspace(course_name: str):
    """Get a specific workspace."""
    if course_name not in workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspaces[course_name]


@app.post("/workspaces/{course_name}/upload")
async def upload_document(
    course_name: str,
    file: UploadFile = File(...)
):
    """Upload a document to workspace."""
    if course_name not in workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace = workspaces[course_name]
    workspace_path = runner.get_workspace_path(course_name)
    upload_path = os.path.join(workspace_path, "uploads", file.filename)
    
    # Save file
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Add to workspace documents
    if file.filename not in workspace.documents:
        workspace.documents.append(file.filename)
    
    return {
        "message": f"File {file.filename} uploaded successfully",
        "filename": file.filename
    }


@app.post("/workspaces/{course_name}/build-index")
async def build_workspace_index(course_name: str):
    """Build RAG index for workspace."""
    if course_name not in workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace = workspaces[course_name]
    workspace_path = runner.get_workspace_path(course_name)
    uploads_dir = os.path.join(workspace_path, "uploads")
    
    # Parse all documents
    all_pages = []
    for doc_name in workspace.documents:
        doc_path = os.path.join(uploads_dir, doc_name)
        if os.path.exists(doc_path):
            pages = DocumentParser.parse_document(doc_path)
            all_pages.extend(pages)
    
    if not all_pages:
        raise HTTPException(status_code=400, detail="No documents to index")
    
    # Chunk documents
    chunks = chunk_documents(all_pages)
    
    # Build index
    store = build_index(chunks)
    
    # Save index
    index_path = workspace.index_path
    store.save(index_path)
    
    return {
        "message": "Index built successfully",
        "num_chunks": len(chunks),
        "num_documents": len(workspace.documents)
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    if request.course_name not in workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Run orchestration
    response_message, plan = runner.run(
        course_name=request.course_name,
        mode=request.mode,
        user_message=request.message,
        state={}
    )
    
    return ChatResponse(
        message=response_message,
        plan=plan
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True
    )
