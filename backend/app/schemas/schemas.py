from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

class RequirementCreate(BaseModel):
    """Input para crear un requisito manualmente."""

    text: str = Field(..., min_length=5, description="Texto del requisito")
    source: str = Field(default="manual", description="Fuente: pdf, scrape, manual")
    source_name: Optional[str] = Field(default=None, description="Nombre del archivo o URL")
    metadata_: Optional[dict] = Field(default=None, alias="metadata")


class RequirementResponse(BaseModel):
    """Response de un requisito almacenado (sin embedding)."""

    id: UUID
    text: str
    source: str
    source_name: Optional[str]
    metadata_: Optional[dict] = Field(alias="metadata")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class RequirementListResponse(BaseModel):
    """Response paginada de requisitos."""

    total: int
    page: int
    page_size: int
    requirements: list[RequirementResponse]


class DocumentResponse(BaseModel):
    """Response de un chunk de documento almacenado (sin embedding)."""

    id: UUID
    content: str
    source: str
    page: Optional[int]
    chunk_index: Optional[int]
    metadata_: Optional[dict] = Field(alias="metadata")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentListResponse(BaseModel):
    """Response paginada de documentos."""

    total: int
    page: int
    page_size: int
    documents: list[DocumentResponse]


class EvaluationScore(BaseModel):
    """Puntuación de una dimensión de evaluación."""

    score: int = Field(..., ge=0, le=2, description="Puntuación 0-2")
    explanation: str = Field(..., description="Explicación de la puntuación")


class EvaluationResult(BaseModel):
    """Resultado de la evaluación de un requisito (5 dimensiones)."""

    VERIFIABILITY: EvaluationScore
    ATOMICITY: EvaluationScore
    AMBIGUITY: EvaluationScore
    COMPLETENESS: EvaluationScore
    TRACEABLE: EvaluationScore


class FeedbackResult(BaseModel):
    """Resultado del feedback / sugerencias de mejora."""

    suggestions: list[str] = Field(..., description="Lista de sugerencias concretas")
    improved_requirement: str = Field(..., description="Versión mejorada del requisito")


class AnalyzeRequest(BaseModel):
    """Input para analizar un requisito."""

    text: str = Field(..., min_length=5, description="Texto del requisito a analizar")


class AnalyzeResponse(BaseModel):
    """Response completa del análisis de un requisito."""

    original_text: str
    evaluation: EvaluationResult
    feedback: FeedbackResult
    context_used: list[str] = Field(
        default_factory=list,
        description="Chunks de contexto recuperados del retriever",
    )

class ScrapeRequest(BaseModel):
    """Input para hacer scraping de requisitos."""

    url: str = Field(..., description="URL de la página a scrapear")
    css_selector: Optional[str] = Field(
        default=None,
        description="Selector CSS para los elementos de requisitos (opcional)",
    )


class ScrapeResponse(BaseModel):
    """Resultado del scraping."""

    url: str
    requirements_found: int
    requirements_saved: int
    requirements: list[str] = Field(
        default_factory=list,
        description="Textos de requisitos extraídos",
    )

class UploadResponse(BaseModel):
    """Resultado de la subida de un PDF."""

    filename: str
    chunks_extracted: int
    requirements_indexed: int
    message: str

class ExportRequirement(BaseModel):
    """Requisito para exportación (sin embedding)."""

    id: str
    text: str
    source: str
    source_name: Optional[str]
    metadata: Optional[dict]
    created_at: str


class ExportDocument(BaseModel):
    """Chunk de documento para exportación."""

    id: str
    content: str
    source: str
    page: Optional[int]
    chunk_index: Optional[int]
    metadata: Optional[dict]
    created_at: str
