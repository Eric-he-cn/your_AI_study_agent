"""FAISS vector store."""
import os
import pickle
from typing import List, Dict, Any, Tuple
import faiss
import numpy as np
from rag.embed import get_embedding_model


class FAISSStore:
    """FAISS-based vector store."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks = []
    
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        """Add chunks and their embeddings to the store."""
        self.index.add(embeddings.astype('float32'))
        self.chunks.extend(chunks)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar chunks."""
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                # Convert L2 distance to similarity score (inverse)
                score = 1.0 / (1.0 + distances[0][i])
                results.append((self.chunks[idx], score))
        
        return results
    
    def save(self, path: str):
        """Save index and chunks to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump(self.chunks, f)
    
    def load(self, path: str):
        """Load index and chunks from disk."""
        self.index = faiss.read_index(f"{path}.faiss")
        with open(f"{path}.pkl", 'rb') as f:
            self.chunks = pickle.load(f)
    
    @property
    def size(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal


def build_index(chunks: List[Dict[str, Any]]) -> FAISSStore:
    """Build FAISS index from chunks."""
    embedding_model = get_embedding_model()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.embed(texts)
    
    store = FAISSStore(dimension=embeddings.shape[1])
    store.add_chunks(chunks, embeddings)
    
    return store
