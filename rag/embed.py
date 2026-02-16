"""Embedding generation."""
import os
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:
    """Sentence transformer embedding model."""
    
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(model_name)
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        return self.model.encode(texts, show_progress_bar=False)
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query."""
        return self.model.encode([query], show_progress_bar=False)[0]


# Global embedding model
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create global embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
