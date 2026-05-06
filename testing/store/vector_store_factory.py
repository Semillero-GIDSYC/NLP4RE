from testing.store.vector_store import VectorStore
from testing.store.impl.faiss_vector_store_impl import FaissVectorStoreImpl


class VectorStoreFactory:
    _types: dict[str, type[VectorStore]] = {
        'faiss': FaissVectorStoreImpl,
    }

    @classmethod
    def create(cls, type: str, dimension: int) -> VectorStore:
        if type not in cls._types:
            raise ValueError(f'Unknown type: {type}. Options: {list(cls._types.keys())}')
        return cls._types[type](dimension) #type: ignore
