import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos."""
    pass


class Requirement(Base):
    """
    Modelo para almacenar requisitos con sus embeddings.

    Attributes:
        id: UUID único del requisito.
        text: Texto completo del requisito.
        source: Tipo de fuente ("pdf", "scrape", "manual").
        source_name: Nombre del archivo o URL de origen.
        embedding: Vector de embedding (768 dimensiones para Gemini).
        metadata_: Metadata adicional en formato JSON.
        created_at: Timestamp de creación.
    """

    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, default="manual")
    source_name = Column(String(500), nullable=True)
    embedding = Column(Vector, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Requirement(id={self.id}, source={self.source}, text='{self.text[:50]}...')>"


class Document(Base):
    """
    Modelo para almacenar chunks de documentos de referencia (ISO, etc).
    Estos son los chunks que alimentan el retriever.

    Attributes:
        id: UUID único del chunk.
        content: Contenido textual del chunk.
        source: Nombre del documento de origen.
        page: Número de página (si aplica).
        chunk_index: Índice del chunk dentro del documento.
        embedding: Vector de embedding.
        metadata_: Metadata adicional.
        created_at: Timestamp de creación.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=False)
    page = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    embedding = Column(Vector, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, source={self.source}, content='{self.content[:50]}...')>"
