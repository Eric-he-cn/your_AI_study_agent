"""Document ingestion and parsing."""
import os
from typing import List, Dict, Any
import fitz  # PyMuPDF


class DocumentParser:
    """Parse documents for RAG."""
    
    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Parse PDF and extract text with page numbers."""
        pages = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    pages.append({
                        "text": text,
                        "page": page_num + 1,
                        "doc_id": os.path.basename(file_path)
                    })
            doc.close()
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
        return pages
    
    @staticmethod
    def parse_txt(file_path: str) -> List[Dict[str, Any]]:
        """Parse text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return [{
                "text": text,
                "page": None,
                "doc_id": os.path.basename(file_path)
            }]
        except Exception as e:
            print(f"Error parsing TXT {file_path}: {e}")
            return []
    
    @staticmethod
    def parse_document(file_path: str) -> List[Dict[str, Any]]:
        """Parse document based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return DocumentParser.parse_pdf(file_path)
        elif ext in ['.txt', '.md']:
            return DocumentParser.parse_txt(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return []
