from sentence_transformers import SentenceTransformer
from testing.models.Rule import Rule
from testing.models.Example import Example
import numpy as np
from testing.embedder.embedder import Embedder


class SentenceTransformerEmbedderImpl(Embedder):
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        dim = self.model.get_sentence_embedding_dimension()
        if dim is None:
            raise ValueError(f"Model '{model_name}' does not report an embedding dimension")
        self._dimension: int = dim

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_rule(self, rule: Rule) -> np.ndarray:
        return self.model.encode(rule.description, normalize_embeddings=True, convert_to_numpy=True)

    def embed_example(self, example: Example) -> np.ndarray:
        return self.model.encode(example.text, normalize_embeddings=True, convert_to_numpy=True)
