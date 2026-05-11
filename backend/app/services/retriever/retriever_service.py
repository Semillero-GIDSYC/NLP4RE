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

def index_documents(
    chunks: list[Document],
    collection_name: str = "iso_standards",
    batch_size: int = 10,
    delay: float = 2.0,
) -> int:
    """
    Indexa una lista de documentos (chunks) en la tabla 'documents' de la base de datos.
    """
    if not chunks:
        return 0

    embeddings_model = get_embeddings()
    total_indexed = 0

    db = SessionLocal()
    try:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.page_content for chunk in batch]
            
            try:
                # Obtener embeddings
                embeddings = embeddings_model.embed_documents(texts)
                
                # Crear instancias de DBDocument
                db_docs = []
                for chunk, emb in zip(batch, embeddings):
                    db_docs.append(
                        DBDocument(
                            content=chunk.page_content,
                            source=chunk.metadata.get("source_file", chunk.metadata.get("source", "unknown")),
                            page=chunk.metadata.get("page"),
                            chunk_index=chunk.metadata.get("chunk_index"),
                            embedding=emb,
                            metadata_=chunk.metadata
                        )
                    )
                
                db.add_all(db_docs)
                db.commit()
                total_indexed += len(batch)
            except Exception as e:
                db.rollback()
                time.sleep(delay * 3)
                try:
                    embeddings = embeddings_model.embed_documents(texts)
                    db_docs = []
                    for chunk, emb in zip(batch, embeddings):
                        db_docs.append(
                            DBDocument(
                                content=chunk.page_content,
                                source=chunk.metadata.get("source_file", chunk.metadata.get("source", "unknown")),
                                page=chunk.metadata.get("page"),
                                chunk_index=chunk.metadata.get("chunk_index"),
                                embedding=emb,
                                metadata_=chunk.metadata
                            )
                        )
                    db.add_all(db_docs)
                    db.commit()
                    total_indexed += len(batch)
                except Exception as e2:
                    db.rollback()
                    print(f"Error fatal indexando batch de chunks: {str(e2)}")
                    continue

            # Rate limiting entre batches
            if i + batch_size < len(chunks):
                time.sleep(delay)
                
    finally:
        db.close()

    return total_indexed


def index_requirements(
    texts: list[str],
    source: str = "manual",
    source_name: Optional[str] = None,
    batch_size: int = 10,
    delay: float = 2.0,
) -> int:
    """
    Indexa una lista de textos como requisitos en la tabla 'requirements'.
    Implementa rate limiting para evitar errores 429.
    """
    if not texts:
        return 0
        
    embeddings_model = get_embeddings()
    
    # Filtrar vacíos
    texts = [text for text in texts if text.strip()]
    if not texts:
        return 0
        
    db = SessionLocal()
    total_indexed = 0
    
    try:
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            try:
                embeddings = embeddings_model.embed_documents(batch)
                
                db_reqs = []
                for text, emb in zip(batch, embeddings):
                    db_reqs.append(
                        DBRequirement(
                            text=text,
                            source=source,
                            source_name=source_name or "unknown",
                            embedding=emb,
                            metadata_={"source": source, "source_name": source_name or "unknown"}
                        )
                    )
                    
                db.add_all(db_reqs)
                db.commit()
                total_indexed += len(db_reqs)
            except Exception as e:
                db.rollback()
                time.sleep(delay * 3)
                try:
                    embeddings = embeddings_model.embed_documents(batch)
                    db_reqs = []
                    for text, emb in zip(batch, embeddings):
                        db_reqs.append(
                            DBRequirement(
                                text=text,
                                source=source,
                                source_name=source_name or "unknown",
                                embedding=emb,
                                metadata_={"source": source, "source_name": source_name or "unknown"}
                            )
                        )
                    db.add_all(db_reqs)
                    db.commit()
                    total_indexed += len(db_reqs)
                except Exception as e2:
                    db.rollback()
                    print(f"Error fatal indexando batch de requisitos: {str(e2)}")
                    continue

            # Rate limiting
            if i + batch_size < len(texts):
                time.sleep(delay)
                
        return total_indexed
    finally:
        db.close()


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
