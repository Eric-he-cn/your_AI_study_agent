"""Text chunking with overlap."""
import os
from typing import List, Dict, Any


def simple_chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50
) -> List[str]:
    """Simple chunking by character count with overlap."""
    # 防止 overlap >= chunk_size 导致 start 永不前进而死循环
    if chunk_size <= 0:
        chunk_size = 512
    if overlap >= chunk_size:
        overlap = chunk_size // 2

    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        next_start = end - overlap
        if next_start <= start:          # 额外安全兜底
            next_start = start + chunk_size
        start = next_start
        
    return chunks


def chunk_documents(
    pages: List[Dict[str, Any]],
    chunk_size: int = None,
    overlap: int = None
) -> List[Dict[str, Any]]:
    """Chunk documents with metadata preservation."""
    if chunk_size is None:
        chunk_size = int(os.getenv("CHUNK_SIZE", "512"))
    if overlap is None:
        overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    all_chunks = []
    
    for page in pages:
        text = page["text"]
        page_num = page.get("page")
        doc_id = page["doc_id"]
        
        chunks = simple_chunk_text(text, chunk_size, overlap)
        
        for i, chunk_text in enumerate(chunks):
            all_chunks.append({
                "text": chunk_text,
                "doc_id": doc_id,
                "page": page_num,
                "chunk_id": f"{doc_id}_p{page_num}_c{i}" if page_num else f"{doc_id}_c{i}"
            })
    
    return all_chunks
