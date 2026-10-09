import time
from typing import Optional

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.orm import Session

from ia_service.core.config import get_settings
from ia_service.db.session import SessionLocal
from ia_service.db.models import Document as DBDocument
from ia_service.db.models import Requirement as DBRequirement


def get_embeddings(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """
    Retorna el modelo de embeddings según el proveedor configurado o solicitado.
    """
    settings = get_settings()
    p = (provider or settings.LLM_PROVIDER or "gemini").lower().strip()

    if p == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=api_key or settings.OPENAI_API_KEY,
        )
    elif p == "local":
        from langchain_openai import OpenAIEmbeddings

        url = base_url or settings.LOCAL_MODELS_API or "http://host.docker.internal:1234/v1"
        if not url.endswith("/v1") and not url.endswith("/v1/"):
            url = f"{url.rstrip('/')}/v1"
        return OpenAIEmbeddings(
            model=settings.LOCAL_EMBEDDER_MODEL,
            openai_api_base=url,
            openai_api_key=api_key or "lm-studio",
            check_embedding_ctx_length=False,
        )
    else:
        # Default: Google Gemini embeddings
        key = api_key or settings.GOOGLE_API_KEY
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=key,
            output_dimensionality=768,
        )


def retrieve_context(
    query: str,
    k: Optional[int] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> list[Document]:
    """
    Recupera los chunks más relevantes de la tabla 'documents' como contexto
    usando similitud del coseno. Robusto ante fallos de conexión.
    """
    settings = get_settings()
    k = k or settings.RETRIEVER_K

    try:
        embeddings_model = get_embeddings(provider=provider, api_key=api_key, base_url=base_url)
        query_embedding = embeddings_model.embed_query(query)
    except Exception:
        if settings.GOOGLE_API_KEY and provider != "gemini":
            try:
                embeddings_model = get_embeddings(provider="gemini", api_key=settings.GOOGLE_API_KEY)
                query_embedding = embeddings_model.embed_query(query)
            except Exception:
                return []
        else:
            return []

    db = SessionLocal()
    try:
        results = (
            db.query(DBDocument)
            .order_by(DBDocument.embedding.cosine_distance(query_embedding))
            .limit(k)
            .all()
        )
        return [
            Document(
                page_content=doc.content,
                metadata={
                    **(doc.metadata_ or {}),
                    "id": str(doc.id),
                    "source": doc.source,
                    "page": doc.page,
                    "chunk_index": doc.chunk_index,
                },
            )
            for doc in results
        ]
    except Exception:
        return []
    finally:
        db.close()


def retrieve_examples(
    query: str,
    k: int = 4,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> list[dict]:
    """
    Recupera los requerimientos de ejemplo más similares de la tabla 'requirements'.
    Robusto ante fallos de conexión.
    """
    settings = get_settings()
    try:
        embeddings_model = get_embeddings(provider=provider, api_key=api_key, base_url=base_url)
        query_embedding = embeddings_model.embed_query(query)
    except Exception:
        if settings.GOOGLE_API_KEY and provider != "gemini":
            try:
                embeddings_model = get_embeddings(provider="gemini", api_key=settings.GOOGLE_API_KEY)
                query_embedding = embeddings_model.embed_query(query)
            except Exception:
                return []
        else:
            return []

    db = SessionLocal()
    try:
        results = (
            db.query(DBRequirement)
            .order_by(DBRequirement.embedding.cosine_distance(query_embedding))
            .limit(k)
            .all()
        )
        examples = []
        for r in results:
            if r.text.strip().lower() == query.strip().lower():
                continue
            examples.append({
                "text": r.text,
                "metadata": r.metadata_ or {},
            })
        return examples[:k]
    except Exception:
        return []
    finally:
        db.close()
