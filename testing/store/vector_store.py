from abc import ABC, abstractmethod
import numpy as np

class VectorStore(ABC):

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def saveV(self, vector: np.ndarray, metadata: dict) -> None:
        pass

    @abstractmethod
    def searchV(self, vector: np.ndarray, k: int) -> list[tuple[dict, float]]:
        pass

    @abstractmethod
    def listV(self) -> list[dict]:
        pass