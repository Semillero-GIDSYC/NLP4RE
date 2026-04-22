from abc import ABC, abstractmethod
import numpy as np
from models.Rule import Rule
from models.Example import Example

class Embedder(ABC):

    @abstractmethod
    def embed_rule(self, rule: Rule) -> np.ndarray:
        pass

    @abstractmethod
    def embed_example(self, example: Example) -> np.ndarray:
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass