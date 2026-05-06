import time
from typing import Optional

from langchain_core.documents import Document
from langchain_community.vectorstores.pgvector import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.orm import Session

from app.core.config import get_settings

# Colecciones en pgvector
COLLECTION_ISO = "iso_standards"
COLLECTION_REQUIREMENTS = "requirements"


def get_embeddings():
    """
    Retorna el modelo de embeddings según el proveedor configurado.

    Returns:
        Instancia de embeddings (Google o OpenAI).
    """
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
    else:
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )


def get_vector_store(collection_name: str = COLLECTION_ISO) -> PGVector:
    """
    Retorna una instancia de PGVector conectada a la colección indicada.

    Args:
        collection_name: Nombre de la colección en pgvector.

    Returns:
        Instancia de PGVector.
    """
    settings = get_settings()
    embeddings = get_embeddings()

    return PGVector(
        connection_string=settings.database_url,
        embedding_function=embeddings,
        collection_name=collection_name,
    )


def index_documents(
    chunks: list[Document],
    collection_name: str = COLLECTION_ISO,
    batch_size: int = 50,
    delay: float = 2.0,
) -> int:
    """
    Indexa una lista de documentos (chunks) en pgvector.
    Usa batch processing con rate limiting para evitar throttling de la API.

    Args:
        chunks: Lista de Documents de LangChain.
        collection_name: Colección objetivo en pgvector.
        batch_size: Tamaño de cada batch.
        delay: Segundos de espera entre batches.

    Returns:
        Número total de documentos indexados.
    """
    if not chunks:
        return 0

    vector_store = get_vector_store(collection_name)
    total_indexed = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        try:
            vector_store.add_documents(batch)
            total_indexed += len(batch)
        except Exception as e:
            # Retry simple con más delay
            time.sleep(delay * 3)
            try:
                vector_store.add_documents(batch)
                total_indexed += len(batch)
            except Exception as e2:
                continue

        # Rate limiting entre batches
        if i + batch_size < len(chunks):
            time.sleep(delay)

    return total_indexed


def index_requirements(
    texts: list[str],
    source: str = "manual",
    source_name: Optional[str] = None,
) -> int:
    """
    Indexa una lista de textos como requisitos en pgvector.

    Args:
        texts: Lista de textos de requisitos.
        source: Tipo de fuente ("pdf", "scrape", "manual").
        source_name: Nombre del archivo o URL.

    Returns:
        Número de requisitos indexados.
    """
    # Convertir textos a Documents de LangChain
    docs = [
        Document(
            page_content=text,
            metadata={"source": source, "source_name": source_name or "unknown"},
        )
        for text in texts
        if text.strip()
    ]

    return index_documents(docs, collection_name=COLLECTION_REQUIREMENTS)


def retrieve_context(query: str, k: Optional[int] = None) -> list[Document]:
    """
    Recupera los chunks más relevantes del vector store como contexto.
    Busca en la colección de estándares ISO.

    Args:
        query: Texto del requisito a analizar.
        k: Número de resultados a retornar.

    Returns:
        Lista de Documents relevantes.
    """
    settings = get_settings()
    k = k or settings.RETRIEVER_K

    vector_store = get_vector_store(COLLECTION_ISO)
    retriever = vector_store.as_retriever(search_kwargs={"k": k})

    results = retriever.invoke(query)

    return results
