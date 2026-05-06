from typing import Any, cast
from testing.store.vector_store import VectorStore
import faiss
import numpy as np

class FaissVectorStoreImpl(VectorStore):
    
    def __init__(self, dimension: int):
        self._dimension = dimension
        self.index = faiss.IndexFlatIP(dimension) 
        self.metadata = {}
        self.next_id = 0

    @property
    def dimension(self) -> int:
        return self._dimension
    
    def saveV(self, vector: np.ndarray, metadata: dict) -> None:
        vec = vector.astype(np.float32).reshape(1, -1)
        cast(Any, self.index).add(vec)
        self.metadata[self.next_id] = metadata
        self.next_id += 1
    
    def searchV(self, vector: np.ndarray, k: int) -> list[tuple[dict, float]]:
        vec = vector.astype(np.float32).reshape(1, -1)
        distances, labels = cast(Any, self.index).search(vec, k)
        
        results = []
        for score, idx in zip(distances[0], labels[0]):
            if idx == -1:
                continue
            results.append((self.metadata[int(idx)], float(score)))
        
        return results
    
    def listV(self) -> list[dict]:
        return list(self.metadata.values())