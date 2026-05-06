from fastapi import APIRouter, HTTPException, Query

from app.schemas.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    RequirementResponse,
    RequirementListResponse,
)
from app.services.retriever.retriever_service import retrieve_context, get_vector_store
from app.services.evaluation.evaluation_service import evaluate_requirement
from app.services.feedback.feedback_service import generate_feedback

router = APIRouter(tags=["Análisis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analizar un requisito",
    description=(
        "Evalúa un requisito de software en 5 dimensiones (ISO 29148): "
        "verificabilidad, atomicidad, ambigüedad, completitud y trazabilidad. "
        "Genera sugerencias de mejora y una versión optimizada del requisito."
    ),
)
async def analyze_requirement(request: AnalyzeRequest):
    """
    Pipeline completo de análisis:
    1. Recuperar contexto normativo (retriever/pgvector).
    2. Evaluar requisito con LLM (5 dimensiones).
    3. Generar feedback y versión mejorada con LLM.
    """
    try:
        context_docs = retrieve_context(request.text)
        context_texts = [doc.page_content for doc in context_docs]

        evaluation = evaluate_requirement(
            requirement_text=request.text,
            context_docs=context_docs,
        )

        feedback = generate_feedback(
            requirement_text=request.text,
            evaluation=evaluation,
        )

        return AnalyzeResponse(
            original_text=request.text,
            evaluation=evaluation,
            feedback=feedback,
            context_used=context_texts,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analizando el requisito: {str(e)}",
        )


@router.get(
    "/requirements",
    response_model=RequirementListResponse,
    summary="Listar requisitos almacenados",
    description="Retorna los requisitos almacenados en la base de datos, con paginación.",
)
async def list_requirements(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Requisitos por página"),
):
    """Lista paginada de requisitos del vector store."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Requirement
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # Total de requisitos
            total = db.query(func.count(Requirement.id)).scalar() or 0

            # Paginación
            offset = (page - 1) * page_size
            requirements = (
                db.query(Requirement)
                .order_by(Requirement.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return RequirementListResponse(
                total=total,
                page=page,
                page_size=page_size,
                requirements=[
                    RequirementResponse(
                        id=r.id,
                        text=r.text,
                        source=r.source,
                        source_name=r.source_name,
                        metadata=r.metadata_,
                        created_at=r.created_at,
                    )
                    for r in requirements
                ],
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
