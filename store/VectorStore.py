from abc import ABC, abstractmethod
import numpy as np
from store.impl.FaissVectorStoreImpl import FaissVectorStoreImpl

class VectorStore(ABC):

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @classmethod
    def create(cls, type: str , dimension: int) -> "VectorStore":
        types = {
            'faiss': FaissVectorStoreImpl
        }

        if type not in types:
            raise ValueError(f'Unkonw type: {type}. Options: {list(types.keys())}')
        
        return types[type](dimension)

    @abstractmethod
    def saveV(self, vector: np.ndarray, metadata: dict) -> None:
        pass

    @abstractmethod
    def searchV(self, vector: np.ndarray, k: int) -> list[tuple[dict, float]]:
        pass

    @abstractmethod
    def listV(self) -> list[dict]:
        pass