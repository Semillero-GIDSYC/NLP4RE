import time
from typing import Optional

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.db.models import Document as DBDocument
from app.db.models import Requirement as DBRequirement

def get_embeddings():
    """
    Retorna el modelo de embeddings según el proveedor configurado.
    """
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    elif settings.LLM_PROVIDER == "local":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.LOCAL_EMBEDDER_MODEL,
            openai_api_base=settings.LOCAL_MODELS_API,
            openai_api_key="lm-studio",
            check_embedding_ctx_length=False
        )
    else:
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )


def retrieve_context(query: str, k: Optional[int] = None) -> list[Document]:
    """
    Recupera los chunks más relevantes de la tabla 'documents' como contexto
    usando similitud del coseno.
    """
    settings = get_settings()
    k = k or settings.RETRIEVER_K

    embeddings_model = get_embeddings()
    query_embedding = embeddings_model.embed_query(query)
    
    db = SessionLocal()
    try:
        # Usando distancia coseno de pgvector:
        results = (
            db.query(DBDocument)
            .order_by(DBDocument.embedding.cosine_distance(query_embedding))
            .limit(k)
            .all()
        )
        
        # Convertir a LangChain Document
        docs = [
            Document(
                page_content=doc.content,
                metadata={
                    **(doc.metadata_ or {}),
                    "id": str(doc.id),
                    "source": doc.source,
                    "page": doc.page,
                    "chunk_index": doc.chunk_index
                }
            )
            for doc in results
        ]
        return docs
    finally:
        db.close()
